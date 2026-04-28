from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

from patentiq_etl.common.io import ensure_dir, parquet_row_count, write_pylist_parquet, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult


MODEL_SCOPE = "jurisdiction_field_trend_forecast"
FEATURE_TABLE_NAME = "ml_feature_jurisdiction_field_trend_forecast.parquet"
LABEL_TABLE_NAME = "ml_label_jurisdiction_field_trend_future.parquet"
PREDICTION_TABLE_NAME = "ml_prediction_jurisdiction_field_trend_forecast.parquet"
SPLIT_TABLE_NAME = "ml_split_registry.parquet"
PHASE_SPLIT_TABLE_NAME = "ml_split_registry_phase06.parquet"
EXPERIMENT_REGISTRY_NAME = "ml_experiment_registry.parquet"
MODEL_REGISTRY_NAME = "ml_model_registry.parquet"
CALIBRATION_REGISTRY_NAME = "ml_calibration_registry.parquet"
FEATURE_MANIFEST_NAME = "ml_feature_manifest.parquet"
MODEL_CARD_NAME = "model_card_jurisdiction_field_trend_forecast.json"
DIRECTION_CALIBRATION_NAME = "jurisdiction_field_trend_forecast_direction_calibration.json"

TRAINING_HORIZONS = ("3y", "5y")
MIN_ROWS_FOR_BASELINE = {"train": 300, "validation": 100, "test": 100}
BASELINE_PARAMS = {
    "objective": "multiclass",
    "num_class": 3,
    "n_estimators": 500,
    "learning_rate": 0.05,
    "num_leaves": 31,
    "max_depth": 6,
    "min_child_samples": 20,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 0.1,
    "n_jobs": 1,
    "verbosity": -1,
    "random_state": 42,
}
MAJOR_OFFICES = {"EP", "US", "CN", "JP", "KR"}
CATEGORICAL_FEATURES = ["jurisdiction_code", "wipo_industry_code", "segment_heat_state_asof"]
LABEL_TO_INT = {"cooling": 0, "stable": 1, "heating": 2}
INT_TO_LABEL = {value: key for key, value in LABEL_TO_INT.items()}
STRENGTH_RULES = {
    "strong": {"min_top_probability": 0.90, "min_margin": 0.60},
    "moderate": {"min_top_probability": 0.65, "min_margin": 0.40},
    "weak": "fallback",
}
SUPPORT_RULES = {
    "strong": {"min_train_rows": 40, "min_minority_class_share": 0.12},
    "moderate": {"min_train_rows": 15, "min_minority_class_share": 0.05, "major_office_override": True},
    "limited": "fallback",
}
FEATURE_NAMES = [
    "jurisdiction_code",
    "wipo_industry_code",
    "segment_heat_state_asof",
    "field_age_years",
    "local_family_filings_asof",
    "prior_period_local_family_filings",
    "local_growth_rate_asof",
    "local_trend_coefficient_asof",
    "local_growth_rate_lag1",
    "local_growth_rate_lag2",
    "local_family_filings_lag1",
    "local_family_filings_lag2",
    "local_acceleration_1y",
    "local_acceleration_2y",
    "local_volatility_3y",
    "local_volatility_5y",
    "global_family_filings_asof",
    "prior_period_global_family_filings",
    "global_growth_rate_asof",
    "global_trend_coefficient_asof",
    "global_growth_rate_lag1",
    "global_growth_rate_lag2",
    "global_acceleration_1y",
    "global_volatility_3y",
    "local_to_global_share_asof",
    "local_minus_global_growth_spread",
    "local_minus_global_trend_spread",
    "segment_family_count_asof",
    "segment_growth_proxy_asof",
    "is_major_office",
    "is_ep",
    "is_us",
    "is_cn",
    "is_jp",
    "is_kr",
]


def _required_inputs(settings: BuildSettings) -> dict[str, Path]:
    return {
        "local_trends": settings.silver_dir / "silver_local_tech_trends_timeseries.parquet",
        "global_trends": settings.silver_dir / "silver_global_tech_trends_timeseries.parquet",
        "market_summary_pit": settings.gold_dir / "gold_market_summary_pit.parquet",
    }


def _ensure_inputs(required: dict[str, Path]) -> None:
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Phase 06 required inputs missing: {missing}")


def _write_frame_parquet(frame: pd.DataFrame, path: Path) -> None:
    ensure_dir(path.parent)
    con = duckdb.connect()
    con.register("frame_to_write", frame)
    con.execute(f"copy (select * from frame_to_write) to '{path}' (format parquet, compression zstd)")


def _write_scope_rows(path: Path, model_scope: str, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    if not path.exists():
        write_pylist_parquet(rows, path)
        return
    replacement = pd.DataFrame(rows)
    tmp_path = path.with_suffix(".tmp.parquet")
    con = duckdb.connect()
    con.register("replacement_rows", replacement)
    con.execute(
        f"""
        copy (
            select * from read_parquet('{path}') where model_scope <> '{model_scope}'
            union all by name
            select * from replacement_rows
        ) to '{tmp_path}' (format parquet, compression zstd)
        """
    )
    tmp_path.replace(path)


def _required_feature_manifest_rows(feature_table: str, method_version: str) -> list[dict[str, object]]:
    categorical = {"jurisdiction_code", "wipo_industry_code", "segment_heat_state_asof"}
    return [
        {
            "model_scope": MODEL_SCOPE,
            "feature_name": feature_name,
            "feature_table": feature_table,
            "feature_type": "categorical" if feature_name in categorical else "numeric",
            "null_policy": "zero_or_stable_imputed",
            "is_leakage_sensitive": False,
            "introduced_in_version": method_version,
        }
        for feature_name in FEATURE_NAMES
    ]


def _class_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    if len(y_true) == 0:
        return None
    return float(np.mean(np.asarray(y_true, dtype=int) == np.asarray(y_pred, dtype=int)))


def _balanced_accuracy(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(y_pred, dtype=int)
    if len(y) == 0:
        return None
    recalls: list[float] = []
    for klass in sorted(set(y.tolist())):
        mask = y == klass
        if int(mask.sum()) == 0:
            continue
        recalls.append(float(np.mean(p[mask] == klass)))
    if not recalls:
        return None
    return float(np.mean(recalls))


def _macro_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float | None:
    y = np.asarray(y_true, dtype=int)
    p = np.asarray(y_pred, dtype=int)
    if len(y) == 0:
        return None
    f1s: list[float] = []
    for klass in sorted(set(y.tolist()) | set(p.tolist())):
        tp = int(np.sum((y == klass) & (p == klass)))
        fp = int(np.sum((y != klass) & (p == klass)))
        fn = int(np.sum((y == klass) & (p != klass)))
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        if precision + recall == 0:
            f1s.append(0.0)
        else:
            f1s.append(float(2 * precision * recall / (precision + recall)))
    return float(np.mean(f1s)) if f1s else None


def _strength_band(top_prob: np.ndarray, margin: np.ndarray) -> np.ndarray:
    return np.where(
        (top_prob >= STRENGTH_RULES["strong"]["min_top_probability"])
        & (margin >= STRENGTH_RULES["strong"]["min_margin"]),
        "strong",
        np.where(
            (top_prob >= STRENGTH_RULES["moderate"]["min_top_probability"])
            & (margin >= STRENGTH_RULES["moderate"]["min_margin"]),
            "moderate",
            "weak",
        ),
    )


def _support_level(train_rows: np.ndarray, minority_share: np.ndarray, major_office: np.ndarray) -> np.ndarray:
    return np.where(
        (train_rows >= SUPPORT_RULES["strong"]["min_train_rows"])
        & (minority_share >= SUPPORT_RULES["strong"]["min_minority_class_share"]),
        "strong",
        np.where(
            ((train_rows >= SUPPORT_RULES["moderate"]["min_train_rows"])
             & (minority_share >= SUPPORT_RULES["moderate"]["min_minority_class_share"]))
            | ((train_rows >= SUPPORT_RULES["strong"]["min_train_rows"]) & (major_office == 1)),
            "moderate",
            "limited",
        ),
    )


def _prepare_dense_frame(settings: BuildSettings, required: dict[str, Path]) -> pd.DataFrame:
    con = duckdb.connect()
    local = con.execute(
        f"""
        select
            cast(snapshot_year as integer) as as_of_year,
            jurisdiction_code,
            wipo_industry_code,
            cast(local_family_filings as double) as local_family_filings_asof,
            cast(prior_period_local_family_filings as double) as prior_period_local_family_filings,
            cast(local_growth_rate as double) as local_growth_rate_asof,
            cast(local_trend_coefficient as double) as local_trend_coefficient_asof
        from read_parquet('{required["local_trends"]}')
        """
    ).df()
    global_trends = con.execute(
        f"""
        select
            cast(snapshot_year as integer) as as_of_year,
            wipo_industry_code,
            cast(global_family_filings as double) as global_family_filings_asof,
            cast(prior_period_global_family_filings as double) as prior_period_global_family_filings,
            cast(global_growth_rate as double) as global_growth_rate_asof,
            cast(global_trend_coefficient as double) as global_trend_coefficient_asof
        from read_parquet('{required["global_trends"]}')
        """
    ).df()
    market = con.execute(
        f"""
        select
            cast(as_of_year as integer) as as_of_year,
            wipo_industry_code,
            coalesce(segment_heat_state_asof, 'stable') as segment_heat_state_asof,
            cast(
                coalesce(
                    segment_priority_year_family_count_asof,
                    segment_family_count_asof,
                    0.0
                ) as double
            ) as segment_family_count_asof,
            cast(coalesce(segment_growth_index_asof, 0.0) as double) as segment_growth_proxy_asof
        from read_parquet('{required["market_summary_pit"]}')
        """
    ).df()

    min_year = max(settings.year_window_start, int(local["as_of_year"].min()))
    max_year = int(local["as_of_year"].max())
    years = pd.DataFrame({"as_of_year": np.arange(min_year, max_year + 1, dtype=int)})
    segments = local[["jurisdiction_code", "wipo_industry_code"]].drop_duplicates().assign(_key=1)
    dense = segments.merge(years.assign(_key=1), on="_key", how="inner").drop(columns="_key")
    frame = dense.merge(local, on=["jurisdiction_code", "wipo_industry_code", "as_of_year"], how="left")
    frame = frame.merge(global_trends, on=["wipo_industry_code", "as_of_year"], how="left")
    frame = frame.merge(market, on=["wipo_industry_code", "as_of_year"], how="left")

    numeric_fill_zero = [
        "local_family_filings_asof",
        "prior_period_local_family_filings",
        "local_growth_rate_asof",
        "local_trend_coefficient_asof",
        "global_family_filings_asof",
        "prior_period_global_family_filings",
        "global_growth_rate_asof",
        "global_trend_coefficient_asof",
        "segment_family_count_asof",
        "segment_growth_proxy_asof",
    ]
    for col in numeric_fill_zero:
        frame[col] = frame[col].fillna(0.0)
    frame["segment_heat_state_asof"] = frame["segment_heat_state_asof"].fillna("stable")

    frame = frame.sort_values(["jurisdiction_code", "wipo_industry_code", "as_of_year"]).reset_index(drop=True)
    group_keys = ["jurisdiction_code", "wipo_industry_code"]
    grouped = frame.groupby(group_keys, sort=False)

    for lag in (1, 2):
        frame[f"local_growth_rate_lag{lag}"] = grouped["local_growth_rate_asof"].shift(lag).fillna(0.0)
        frame[f"local_family_filings_lag{lag}"] = grouped["local_family_filings_asof"].shift(lag).fillna(0.0)
        frame[f"global_growth_rate_lag{lag}"] = grouped["global_growth_rate_asof"].shift(lag).fillna(0.0)

    frame["local_acceleration_1y"] = frame["local_growth_rate_asof"] - frame["local_growth_rate_lag1"]
    frame["local_acceleration_2y"] = frame["local_growth_rate_lag1"] - frame["local_growth_rate_lag2"]
    frame["global_acceleration_1y"] = frame["global_growth_rate_asof"] - frame["global_growth_rate_lag1"]
    frame["local_volatility_3y"] = (
        grouped["local_growth_rate_asof"].rolling(window=3, min_periods=1).std().reset_index(level=group_keys, drop=True).fillna(0.0)
    )
    frame["local_volatility_5y"] = (
        grouped["local_growth_rate_asof"].rolling(window=5, min_periods=1).std().reset_index(level=group_keys, drop=True).fillna(0.0)
    )
    frame["global_volatility_3y"] = (
        frame.groupby("wipo_industry_code", sort=False)["global_growth_rate_asof"]
        .rolling(window=3, min_periods=1)
        .std()
        .reset_index(level="wipo_industry_code", drop=True)
        .fillna(0.0)
    )

    positive_mask = frame["local_family_filings_asof"] > 0
    first_positive_year = (
        frame.loc[positive_mask, ["jurisdiction_code", "wipo_industry_code", "as_of_year"]]
        .groupby(group_keys, as_index=False)["as_of_year"]
        .min()
        .rename(columns={"as_of_year": "first_positive_year"})
    )
    frame = frame.merge(first_positive_year, on=group_keys, how="left")
    frame["field_age_years"] = np.where(
        frame["first_positive_year"].notna(),
        np.maximum(frame["as_of_year"] - frame["first_positive_year"] + 1, 0),
        0,
    ).astype(float)
    frame = frame.drop(columns=["first_positive_year"])

    frame["local_to_global_share_asof"] = np.where(
        frame["global_family_filings_asof"] > 0,
        frame["local_family_filings_asof"] / frame["global_family_filings_asof"],
        0.0,
    )
    frame["local_minus_global_growth_spread"] = frame["local_growth_rate_asof"] - frame["global_growth_rate_asof"]
    frame["local_minus_global_trend_spread"] = frame["local_trend_coefficient_asof"] - frame["global_trend_coefficient_asof"]

    frame["is_major_office"] = frame["jurisdiction_code"].isin(MAJOR_OFFICES).astype(int)
    frame["is_ep"] = (frame["jurisdiction_code"] == "EP").astype(int)
    frame["is_us"] = (frame["jurisdiction_code"] == "US").astype(int)
    frame["is_cn"] = (frame["jurisdiction_code"] == "CN").astype(int)
    frame["is_jp"] = (frame["jurisdiction_code"] == "JP").astype(int)
    frame["is_kr"] = (frame["jurisdiction_code"] == "KR").astype(int)

    max_year = int(frame["as_of_year"].max())
    for horizon, offset in (("3y", 3), ("5y", 5)):
        future = grouped["local_family_filings_asof"].shift(-offset)
        frame[f"future_local_family_filings_{horizon}"] = future
        frame[f"is_observed_{horizon}"] = frame["as_of_year"] + offset <= max_year
        frame[f"future_local_growth_rate_{horizon}"] = np.where(
            frame[f"is_observed_{horizon}"],
            (frame[f"future_local_family_filings_{horizon}"].fillna(0.0) - frame["local_family_filings_asof"])
            / np.maximum(frame["local_family_filings_asof"], 1.0),
            np.nan,
        )
        future_diff = frame[f"future_local_family_filings_{horizon}"].fillna(0.0) - frame["local_family_filings_asof"]
        frame[f"future_direction_{horizon}"] = np.where(
            ~frame[f"is_observed_{horizon}"],
            None,
            np.where(future_diff > 0, "heating", np.where(future_diff < 0, "cooling", "stable")),
        )

    return frame


def _build_split_frame(frame: pd.DataFrame) -> pd.DataFrame:
    max_year = int(frame["as_of_year"].max())
    max_observed_5y = max_year - 5
    validation_years = {max_observed_5y - 3, max_observed_5y - 2}
    test_years = {max_observed_5y - 1, max_observed_5y}
    cutoff = pd.Timestamp(year=max_observed_5y, month=12, day=31)
    out = frame[["jurisdiction_code", "wipo_industry_code", "as_of_year"]].copy()
    out["entity_id"] = (
        out["jurisdiction_code"].astype(str)
        + "|"
        + out["wipo_industry_code"].astype(str)
        + "|"
        + out["as_of_year"].astype(str)
    )
    out["model_scope"] = MODEL_SCOPE
    out["root_family_id"] = pd.NA
    out["split_strategy"] = "jurisdiction_field_grouped_time_by_as_of_year"
    out["snapshot_cutoff"] = cutoff
    out["primary_wipo_field"] = out["wipo_industry_code"]
    out["time_key_year"] = out["as_of_year"]
    out["split_name"] = np.where(
        out["as_of_year"] > max_observed_5y,
        "unassigned_recent",
        np.where(
            out["as_of_year"].isin(test_years),
            "test",
            np.where(out["as_of_year"].isin(validation_years), "validation", "train"),
        ),
    )
    return out[
        [
            "model_scope",
            "entity_id",
            "root_family_id",
            "split_name",
            "split_strategy",
            "snapshot_cutoff",
            "primary_wipo_field",
            "time_key_year",
        ]
    ]


def _prepare_model_frame(frame: pd.DataFrame) -> pd.DataFrame:
    model_frame = frame.copy()
    for col in CATEGORICAL_FEATURES:
        model_frame[col] = model_frame[col].astype("category")
    return model_frame


def _fit_horizon(
    frame: pd.DataFrame,
    split_frame: pd.DataFrame,
    horizon: str,
    settings: BuildSettings,
) -> tuple[dict[str, object], pd.DataFrame] | None:
    target_col = f"future_local_family_filings_{horizon}"
    target_dir_col = f"future_direction_{horizon}"
    observed_col = f"is_observed_{horizon}"
    work = frame.merge(
        split_frame[["entity_id", "split_name"]],
        on="entity_id",
        how="left",
    )
    observed = work[(work[observed_col]) & (work["split_name"] != "unassigned_recent")].copy()
    split_sizes = {name: int((observed["split_name"] == name).sum()) for name in ("train", "validation", "test")}
    if any(split_sizes[name] < MIN_ROWS_FOR_BASELINE[name] for name in split_sizes):
        return None

    prepared = _prepare_model_frame(observed)
    x_train = prepared.loc[prepared["split_name"] == "train", FEATURE_NAMES]
    x_test = prepared.loc[prepared["split_name"] == "test", FEATURE_NAMES]
    y_train = prepared.loc[prepared["split_name"] == "train", target_dir_col].map(LABEL_TO_INT).to_numpy(dtype=int)
    y_test = prepared.loc[prepared["split_name"] == "test", target_dir_col].map(LABEL_TO_INT).to_numpy(dtype=int)
    y_test_raw = prepared.loc[prepared["split_name"] == "test", target_col].to_numpy(dtype=float)
    current_test = prepared.loc[prepared["split_name"] == "test", "local_family_filings_asof"].to_numpy(dtype=float)

    model = LGBMClassifier(**BASELINE_PARAMS)
    model.fit(
        x_train,
        y_train,
        categorical_feature=CATEGORICAL_FEATURES,
    )

    test_proba = model.predict_proba(x_test)
    test_pred = model.predict(x_test).astype(int)
    top_prob = test_proba.max(axis=1)
    sorted_proba = np.sort(test_proba, axis=1)
    margin = sorted_proba[:, -1] - sorted_proba[:, -2]
    strength = _strength_band(top_prob, margin)

    artifact_path = settings.ml_dir / f"jurisdiction_field_trend_forecast_{horizon}_model.txt"
    bundle_path = settings.ml_dir / f"jurisdiction_field_trend_forecast_{horizon}_bundle.json"
    model.booster_.save_model(str(artifact_path))

    subgroup: dict[str, dict[str, float]] = {}
    subgroup_frame = prepared.loc[prepared["split_name"] == "test", ["wipo_industry_code"]].copy()
    subgroup_frame["actual"] = y_test
    subgroup_frame["predicted"] = test_pred
    for field_name, group in subgroup_frame.groupby("wipo_industry_code", observed=False):
        subgroup[str(field_name)] = {
            "rows": int(len(group)),
            "class_accuracy": float(np.mean(group["actual"] == group["predicted"])),
            "actual_cooling_share": float(np.mean(group["actual"] == LABEL_TO_INT["cooling"])),
            "predicted_cooling_share": float(np.mean(group["predicted"] == LABEL_TO_INT["cooling"])),
        }
    train_support = (
        prepared.loc[prepared["split_name"] == "train", ["jurisdiction_code", "wipo_industry_code", target_dir_col]]
        .assign(row_count=1)
        .groupby(["jurisdiction_code", "wipo_industry_code", target_dir_col], observed=False)["row_count"]
        .sum()
        .reset_index()
    )
    support_pivot = train_support.pivot_table(
        index=["jurisdiction_code", "wipo_industry_code"],
        columns=target_dir_col,
        values="row_count",
        fill_value=0,
    ).reset_index()
    for label in LABEL_TO_INT:
        if label not in support_pivot.columns:
            support_pivot[label] = 0
    support_pivot["train_rows_support"] = support_pivot[list(LABEL_TO_INT.keys())].sum(axis=1)
    support_pivot["minority_class_share"] = support_pivot[list(LABEL_TO_INT.keys())].min(axis=1) / np.maximum(
        support_pivot["train_rows_support"], 1
    )
    calibration_version = f"{settings.release_id}-phase06-direction-calibration-{horizon}"
    bundle = {
        "model_scope": MODEL_SCOPE,
        "horizon": horizon,
        "selected_variant": "direction_baseline",
        "point_forecast_semantics": "direction_band_first",
        "model_artifact": str(artifact_path),
        "feature_columns": FEATURE_NAMES,
        "categorical_features": CATEGORICAL_FEATURES,
        "calibration_method": "confidence_margin_strength_bands",
        "calibration_version": calibration_version,
        "strength_rules": STRENGTH_RULES,
        "prediction_unit": "jurisdiction_code x wipo_industry_code x as_of_year",
    }
    write_text_json(bundle_path, bundle)

    all_rows = _prepare_model_frame(work.copy())
    all_proba = model.predict_proba(all_rows[FEATURE_NAMES])
    all_pred = model.predict(all_rows[FEATURE_NAMES]).astype(int)
    all_top_prob = all_proba.max(axis=1)
    all_sorted_proba = np.sort(all_proba, axis=1)
    all_margin = all_sorted_proba[:, -1] - all_sorted_proba[:, -2]
    prediction_rows = all_rows[
        [
            "jurisdiction_code",
            "wipo_industry_code",
            "as_of_year",
            "local_family_filings_asof",
            "is_major_office",
            target_col,
            target_dir_col,
            observed_col,
            "split_name",
        ]
    ].copy()
    prediction_rows = prediction_rows.merge(
        support_pivot[["jurisdiction_code", "wipo_industry_code", "train_rows_support", "minority_class_share"]],
        on=["jurisdiction_code", "wipo_industry_code"],
        how="left",
    )
    prediction_rows["train_rows_support"] = prediction_rows["train_rows_support"].fillna(0).astype(int)
    prediction_rows["minority_class_share"] = prediction_rows["minority_class_share"].fillna(0.0)
    prediction_rows["model_scope"] = MODEL_SCOPE
    prediction_rows["horizon"] = horizon
    prediction_rows["predicted_direction_band"] = [INT_TO_LABEL[int(v)] for v in all_pred]
    prediction_rows["predicted_direction_probability"] = all_top_prob
    prediction_rows["predicted_margin"] = all_margin
    prediction_rows["trend_strength_band"] = _strength_band(all_top_prob, all_margin)
    prediction_rows["support_level"] = _support_level(
        prediction_rows["train_rows_support"].to_numpy(dtype=float),
        prediction_rows["minority_class_share"].to_numpy(dtype=float),
        prediction_rows["is_major_office"].to_numpy(dtype=float),
    )
    prediction_rows["prob_cooling"] = all_proba[:, LABEL_TO_INT["cooling"]]
    prediction_rows["prob_stable"] = all_proba[:, LABEL_TO_INT["stable"]]
    prediction_rows["prob_heating"] = all_proba[:, LABEL_TO_INT["heating"]]
    prediction_rows["predicted_growth_rate_reference"] = np.select(
        [all_pred == LABEL_TO_INT["heating"], all_pred == LABEL_TO_INT["cooling"]],
        [np.maximum(all_top_prob * 0.25, 0.05), -np.maximum(all_top_prob * 0.25, 0.05)],
        default=0.0,
    )
    prediction_rows["predicted_count_reference"] = np.maximum(
        prediction_rows["local_family_filings_asof"] * (1.0 + prediction_rows["predicted_growth_rate_reference"]),
        0.0,
    )
    prediction_rows["actual_local_family_filings"] = prediction_rows[target_col]
    prediction_rows["actual_direction_band"] = prediction_rows[target_dir_col]
    prediction_rows["is_observed"] = prediction_rows[observed_col]
    prediction_rows = prediction_rows.drop(columns=[target_col, target_dir_col, observed_col, "is_major_office"])

    metrics = {
        "class_accuracy": _class_accuracy(y_test, test_pred),
        "balanced_accuracy": _balanced_accuracy(y_test, test_pred),
        "macro_f1": _macro_f1(y_test, test_pred),
        "direction_accuracy_reference": _class_accuracy(y_test, test_pred),
        "split_sizes": split_sizes,
        "coverage_major_subgroups": subgroup,
        "calibration_version": calibration_version,
        "bundle_path": str(bundle_path),
        "artifact_path": str(artifact_path),
        "predicted_class_distribution": {
            INT_TO_LABEL[idx]: int(count) for idx, count in zip(*np.unique(test_pred, return_counts=True), strict=False)
        },
        "actual_class_distribution": {
            INT_TO_LABEL[idx]: int(count) for idx, count in zip(*np.unique(y_test, return_counts=True), strict=False)
        },
    }
    return metrics, prediction_rows


def build_ml_phase06_jurisdiction_field_trend_forecast(settings: BuildSettings) -> StageResult:
    required = _required_inputs(settings)
    _ensure_inputs(required)
    ensure_dir(settings.ml_dir)

    stage = StageResult(
        stage="ml-phase06-jurisdiction-field-trend-forecast",
        status="success",
        summary="Built Phase 06 jurisdiction-field trend labels, features, split registry, direction-first baseline predictions, and band-calibration metadata.",
        inputs=[str(path) for path in required.values()],
        methods=[
            "Built a dense jurisdiction-field-year grid from local and global trend timeseries.",
            "Derived lag, acceleration, volatility, and market-context features.",
            "Trained LightGBM multiclass direction baselines on horizon-safe grouped time splits.",
            "Assigned direction, strength, and support bands from class probabilities and train-support thresholds.",
        ],
        calculations=[
            "Labels retain raw-count, growth, and direction fields, but the promoted serving semantics are direction-first.",
            "Prediction rows are emitted with direction, strength, and support fields plus secondary count references.",
        ],
        doc_refs=[
            "docs/next-phase-v2/48-patentiq-v2-post-phase-04-prioritization-and-next-execution-path.md",
            "docs/next-phase-v2/49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md",
            "docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md",
        ],
    )

    dense = _prepare_dense_frame(settings, required)
    dense["entity_id"] = (
        dense["jurisdiction_code"].astype(str)
        + "|"
        + dense["wipo_industry_code"].astype(str)
        + "|"
        + dense["as_of_year"].astype(str)
    )

    label_frame = dense[
        [
            "jurisdiction_code",
            "wipo_industry_code",
            "as_of_year",
            "local_family_filings_asof",
            "global_family_filings_asof",
            "local_growth_rate_asof",
            "global_growth_rate_asof",
            "local_trend_coefficient_asof",
            "global_trend_coefficient_asof",
            "future_local_family_filings_3y",
            "future_local_family_filings_5y",
            "future_local_growth_rate_3y",
            "future_local_growth_rate_5y",
            "future_direction_3y",
            "future_direction_5y",
            "is_observed_3y",
            "is_observed_5y",
        ]
    ].copy()
    label_frame["training_snapshot_id"] = settings.release_id
    label_frame["method_version"] = settings.method_version

    feature_frame = dense[
        [
            "jurisdiction_code",
            "wipo_industry_code",
            "as_of_year",
            *FEATURE_NAMES[2:],
        ]
    ].copy()
    feature_frame["training_snapshot_id"] = settings.release_id
    feature_frame["method_version"] = settings.method_version
    feature_frame = feature_frame[["jurisdiction_code", "wipo_industry_code", "as_of_year", *FEATURE_NAMES[2:], "training_snapshot_id", "method_version"]]

    split_frame = _build_split_frame(dense)

    label_path = settings.ml_dir / LABEL_TABLE_NAME
    feature_path = settings.ml_dir / FEATURE_TABLE_NAME
    prediction_path = settings.ml_dir / PREDICTION_TABLE_NAME
    split_path = settings.ml_dir / SPLIT_TABLE_NAME
    phase_split_path = settings.ml_dir / PHASE_SPLIT_TABLE_NAME
    model_card_path = settings.ml_dir / MODEL_CARD_NAME
    direction_calibration_path = settings.ml_dir / DIRECTION_CALIBRATION_NAME

    _write_frame_parquet(label_frame, label_path)
    _write_frame_parquet(feature_frame, feature_path)
    _write_frame_parquet(split_frame, phase_split_path)
    _write_scope_rows(split_path, MODEL_SCOPE, split_frame.to_dict("records"))

    feature_manifest_rows = _required_feature_manifest_rows(FEATURE_TABLE_NAME, settings.method_version)
    _write_scope_rows(settings.ml_dir / FEATURE_MANIFEST_NAME, MODEL_SCOPE, feature_manifest_rows)

    prediction_frames: list[pd.DataFrame] = []
    experiment_rows: list[dict[str, object]] = []
    calibration_rows: list[dict[str, object]] = []
    model_rows: list[dict[str, object]] = []
    direction_calibration_payload: dict[str, object] = {
        "model_scope": MODEL_SCOPE,
        "method_version": settings.method_version,
        "training_snapshot": settings.release_id,
        "serving_semantics": "direction_band_first",
        "strength_band_rules": STRENGTH_RULES,
        "support_level_rules": SUPPORT_RULES,
        "horizons": {},
    }
    model_card_payload: dict[str, object] = {
        "model_scope": MODEL_SCOPE,
        "status": "candidate_trained",
        "prediction_unit": "jurisdiction_code x wipo_industry_code x as_of_year",
        "label_table": str(label_path),
        "feature_table": str(feature_path),
        "prediction_table": str(prediction_path),
        "split_registry": str(phase_split_path),
        "split_registry_shared": str(split_path),
        "method_version": settings.method_version,
        "training_snapshot": settings.release_id,
        "horizons": {},
    }

    for horizon in TRAINING_HORIZONS:
        trained = _fit_horizon(dense, split_frame, horizon, settings)
        if trained is None:
            model_card_payload["horizons"][horizon] = {"status": "insufficient_rows_for_baseline"}
            continue
        metrics, prediction_rows = trained
        prediction_frames.append(prediction_rows)
        experiment_id = f"{settings.release_id}-phase06-baseline-{horizon}"
        experiment_rows.append(
            {
                "experiment_id": experiment_id,
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "algorithm_family": "lightgbm_multiclass_classifier",
                "objective": "multiclass_direction",
                "training_snapshot": settings.release_id,
                "feature_manifest_version": settings.method_version,
                "primary_metric": "macro_f1",
                "primary_metric_value": metrics["macro_f1"],
                "notes": json.dumps(
                    {
                        "predicted_class_distribution": metrics["predicted_class_distribution"],
                        "actual_class_distribution": metrics["actual_class_distribution"],
                    },
                    sort_keys=True,
                ),
                "rmse_log1p": None,
                "interval_coverage_80pct": None,
            }
        )
        calibration_rows.append(
            {
                "experiment_id": experiment_id,
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "calibration_version": metrics["calibration_version"],
                "calibration_method": "direction_strength_support_thresholds",
                "target_coverage": None,
                "coverage_overall": metrics["class_accuracy"],
                "coverage_major_subgroups": json.dumps(metrics["coverage_major_subgroups"], sort_keys=True),
                "status": "calibrated",
            }
        )
        model_rows.append(
            {
                "model_scope": MODEL_SCOPE,
                "model_version": f"{settings.release_id}-phase06-baseline-{horizon}",
                "horizon": horizon,
                "artifact_uri": metrics["bundle_path"],
                "feature_manifest_version": settings.method_version,
                "calibration_version": metrics["calibration_version"],
                "promotion_status": "candidate_trained",
                "rollback_model_version": None,
                "prediction_unit": "jurisdiction_code x wipo_industry_code x as_of_year",
                "training_snapshot": settings.release_id,
            }
        )
        direction_calibration_payload["horizons"][horizon] = {
            "calibration_version": metrics["calibration_version"],
            "predicted_class_distribution": metrics["predicted_class_distribution"],
            "actual_class_distribution": metrics["actual_class_distribution"],
        }
        model_card_payload["horizons"][horizon] = {
            "status": "baseline_trained",
            "selected_variant": "direction_baseline",
            "serving_semantics": "direction_band_first",
            "class_accuracy": metrics["class_accuracy"],
            "balanced_accuracy": metrics["balanced_accuracy"],
            "macro_f1": metrics["macro_f1"],
            "direction_accuracy_reference": metrics["direction_accuracy_reference"],
            "split_sizes": metrics["split_sizes"],
            "artifact_uri": metrics["bundle_path"],
            "calibration_version": metrics["calibration_version"],
            "predicted_class_distribution": metrics["predicted_class_distribution"],
            "actual_class_distribution": metrics["actual_class_distribution"],
        }

    prediction_frame = pd.concat(prediction_frames, ignore_index=True) if prediction_frames else pd.DataFrame()
    if prediction_frames:
        _write_frame_parquet(prediction_frame, prediction_path)
    else:
        write_pylist_parquet([], prediction_path, columns=["model_scope", "horizon"])

    _write_scope_rows(settings.ml_dir / EXPERIMENT_REGISTRY_NAME, MODEL_SCOPE, experiment_rows)
    _write_scope_rows(settings.ml_dir / CALIBRATION_REGISTRY_NAME, MODEL_SCOPE, calibration_rows)
    _write_scope_rows(settings.ml_dir / MODEL_REGISTRY_NAME, MODEL_SCOPE, model_rows)
    write_text_json(direction_calibration_path, direction_calibration_payload)
    write_text_json(model_card_path, model_card_payload)

    stage.outputs.extend(
        [
            str(label_path),
            str(feature_path),
            str(phase_split_path),
            str(prediction_path),
            str(direction_calibration_path),
            str(model_card_path),
        ]
    )
    stage.metrics["label_rows"] = parquet_row_count(label_path)
    stage.metrics["feature_rows"] = parquet_row_count(feature_path)
    stage.metrics["split_rows"] = parquet_row_count(phase_split_path)
    stage.metrics["prediction_rows"] = parquet_row_count(prediction_path)
    for horizon in TRAINING_HORIZONS:
        horizon_metrics = model_card_payload["horizons"].get(horizon, {})
        if "class_accuracy" in horizon_metrics:
            stage.metrics[f"{horizon}_class_accuracy"] = horizon_metrics["class_accuracy"]
        if "balanced_accuracy" in horizon_metrics:
            stage.metrics[f"{horizon}_balanced_accuracy"] = horizon_metrics["balanced_accuracy"]
        if "macro_f1" in horizon_metrics:
            stage.metrics[f"{horizon}_macro_f1"] = horizon_metrics["macro_f1"]
    return stage

from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from lightgbm import Booster, LGBMClassifier

from patentiq_etl.common.io import ensure_dir, parquet_row_count, write_pylist_parquet, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult


MODEL_SCOPE = "publication_or_subfamily_grant_probability"
FEATURE_TABLE_NAME = "ml_feature_pending_grant_pipeline.parquet"
LABEL_TABLE_NAME = "ml_label_pending_grant_event.parquet"
SPLIT_TABLE_NAME = "ml_split_registry.parquet"
PHASE_SPLIT_TABLE_NAME = "ml_split_registry_phase_grant.parquet"
EXPERIMENT_REGISTRY_NAME = "ml_experiment_registry.parquet"
MODEL_REGISTRY_NAME = "ml_model_registry.parquet"
CALIBRATION_REGISTRY_NAME = "ml_calibration_registry.parquet"
FEATURE_MANIFEST_NAME = "ml_feature_manifest.parquet"
MODEL_CARD_NAME = "model_card_pending_grant_pipeline.json"

TRAINING_HORIZONS = ("12m", "24m")
PREDICTION_TABLE_NAME = "ml_prediction_pending_grant_pipeline.parquet"
MIN_ROWS_FOR_BASELINE = {"train": 2_000, "validation": 1_000, "test": 1_000}
MAX_ROWS_FOR_BASELINE = {"train": 400_000, "validation": 120_000, "test": 120_000}
BASELINE_PARAMS = {
    "objective": "binary",
    "n_estimators": 1000,
    "learning_rate": 0.03,
    "num_leaves": 63,
    "max_depth": 8,
    "min_child_samples": 100,
    "subsample": 0.8,
    "subsample_freq": 1,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 0.1,
    "n_jobs": 1,
    "verbosity": -1,
    "random_state": 42,
}
FEATURE_NAMES = [
    "as_of_year",
    "family_priority_year",
    "family_age_years",
    "pending_age_years",
    "primary_wipo_field",
    "family_composite_status_asof",
    "family_size_docdb_asof",
    "family_jurisdiction_count_asof",
    "family_coverage_stability_score_asof",
    "family_tech_breadth_wipo_count_asof",
    "family_blocking_power_score_asof",
    "family_enforceability_score_asof",
    "family_rcf_score_asof",
    "pre_asof_forward_citations_clean",
    "pre_asof_forward_citations_weighted",
    "data_completeness_pct_asof",
    "application_stage_publication_count",
    "grant_stage_publication_count",
    "jurisdiction_field_grant_rate_prior_12m",
    "jurisdiction_field_grant_rate_prior_24m",
    "local_family_filings_asof",
    "prior_period_local_family_filings_asof",
    "local_growth_rate_asof",
    "local_trend_coefficient_asof",
    "jurisdiction_is_ep",
    "jurisdiction_is_us",
    "jurisdiction_is_cn",
    "jurisdiction_is_jp",
    "jurisdiction_is_kr",
    "jurisdiction_is_major_office",
]
BOOLEAN_FEATURES = {
    "jurisdiction_is_ep",
    "jurisdiction_is_us",
    "jurisdiction_is_cn",
    "jurisdiction_is_jp",
    "jurisdiction_is_kr",
    "jurisdiction_is_major_office",
}
PREDICTION_BASE_COLUMNS = [
    "docdb_family_id",
    "jurisdiction_code",
    "as_of_date",
    "as_of_year",
    "family_priority_year",
    "primary_wipo_field",
    "family_age_years",
    "pending_age_years",
    "family_composite_status_asof",
    "family_size_docdb_asof",
    "family_jurisdiction_count_asof",
    "family_coverage_stability_score_asof",
    "family_tech_breadth_wipo_count_asof",
    "family_blocking_power_score_asof",
    "family_enforceability_score_asof",
    "family_rcf_score_asof",
    "pre_asof_forward_citations_clean",
    "pre_asof_forward_citations_weighted",
    "data_completeness_pct_asof",
    "application_stage_publication_count",
    "grant_stage_publication_count",
    "jurisdiction_field_grant_rate_prior_12m",
    "jurisdiction_field_grant_rate_prior_24m",
    "local_family_filings_asof",
    "prior_period_local_family_filings_asof",
    "local_growth_rate_asof",
    "local_trend_coefficient_asof",
    "jurisdiction_is_ep",
    "jurisdiction_is_us",
    "jurisdiction_is_cn",
    "jurisdiction_is_jp",
    "jurisdiction_is_kr",
    "jurisdiction_is_major_office",
]
PREDICTION_PRE_RANK_COLUMNS = PREDICTION_BASE_COLUMNS + [
    "grant_probability_raw_12m",
    "grant_probability_calibrated_12m",
    "grant_probability_raw_24m",
    "grant_probability_calibrated_24m",
    "office_support_level",
]
PREDICTION_OUTPUT_COLUMNS = PREDICTION_PRE_RANK_COLUMNS[:-1] + [
    "pending_grant_rank_within_office_12m",
    "pending_grant_percentile_within_office_12m",
    "pending_grant_priority_tier_12m",
    "pending_grant_rank_within_office_24m",
    "pending_grant_percentile_within_office_24m",
    "pending_grant_priority_tier_24m",
    "office_support_level",
]


def _log_loss_binary(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    if len(y_true) == 0:
        return None
    probs = np.clip(np.asarray(y_prob, dtype=float), 1e-6, 1 - 1e-6)
    y = np.asarray(y_true, dtype=float)
    return float(-np.mean(y * np.log(probs) + (1 - y) * np.log(1 - probs)))


def _brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    if len(y_true) == 0:
        return None
    y = np.asarray(y_true, dtype=float)
    probs = np.asarray(y_prob, dtype=float)
    return float(np.mean((probs - y) ** 2))


def _roc_auc(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    y = np.asarray(y_true, dtype=int)
    scores = np.asarray(y_prob, dtype=float)
    positives = int(y.sum())
    negatives = int(len(y) - positives)
    if len(y) == 0 or positives == 0 or negatives == 0:
        return None
    order = np.argsort(scores)
    ranks = np.empty(len(scores), dtype=float)
    sorted_scores = scores[order]
    n = len(scores)
    i = 0
    while i < n:
        j = i + 1
        while j < n and sorted_scores[j] == sorted_scores[i]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        ranks[order[i:j]] = avg_rank
        i = j
    rank_sum_pos = float(ranks[y == 1].sum())
    return float((rank_sum_pos - positives * (positives + 1) / 2.0) / (positives * negatives))


def _average_precision(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    y = np.asarray(y_true, dtype=int)
    scores = np.asarray(y_prob, dtype=float)
    positives = int(y.sum())
    if len(y) == 0 or positives == 0:
        return None
    order = np.argsort(-scores, kind="mergesort")
    y_sorted = y[order]
    tp = np.cumsum(y_sorted)
    fp = np.cumsum(1 - y_sorted)
    precision = tp / np.maximum(tp + fp, 1)
    recall = tp / positives
    recall_prev = np.concatenate(([0.0], recall[:-1]))
    return float(np.sum((recall - recall_prev) * precision))


def _top_decile_lift(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    y = np.asarray(y_true, dtype=float)
    scores = np.asarray(y_prob, dtype=float)
    if len(y) == 0:
        return None
    base_rate = float(np.mean(y))
    if base_rate <= 0.0:
        return None
    k = max(1, int(np.ceil(len(y) * 0.10)))
    idx = np.argsort(-scores)[:k]
    top_rate = float(np.mean(y[idx])) if len(idx) else 0.0
    return float(top_rate / base_rate)


def _recall_at_top_fraction(y_true: np.ndarray, y_prob: np.ndarray, fraction: float = 0.20) -> float | None:
    y = np.asarray(y_true, dtype=int)
    scores = np.asarray(y_prob, dtype=float)
    positives = int(y.sum())
    if len(y) == 0 or positives == 0:
        return None
    k = max(1, int(np.ceil(len(y) * fraction)))
    idx = np.argsort(-scores)[:k]
    return float(y[idx].sum() / positives)


def _calibration_curve_by_decile(y_true: np.ndarray, y_prob: np.ndarray, bins: int = 10) -> list[dict[str, float]]:
    if len(y_true) == 0:
        return []
    frame = pd.DataFrame({"y_true": np.asarray(y_true, dtype=float), "y_prob": np.asarray(y_prob, dtype=float)})
    frame["bin"] = pd.qcut(frame["y_prob"], q=min(bins, max(1, frame["y_prob"].nunique())), duplicates="drop")
    out: list[dict[str, float]] = []
    for idx, (_, group) in enumerate(frame.groupby("bin", observed=False), start=1):
        out.append(
            {
                "decile": idx,
                "rows": int(len(group)),
                "predicted_rate": float(group["y_prob"].mean()),
                "observed_rate": float(group["y_true"].mean()),
            }
        )
    return out


def _subgroup_probability_summary(
    frame: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray, group_col: str, min_rows: int
) -> dict[str, dict[str, float]]:
    if frame.empty or group_col not in frame.columns:
        return {}
    work = frame[[group_col]].copy()
    work["y_true"] = np.asarray(y_true, dtype=float)
    work["y_prob"] = np.asarray(y_prob, dtype=float)
    out: dict[str, dict[str, float]] = {}
    for group_value, group in work.groupby(group_col, dropna=False):
        if len(group) < min_rows:
            continue
        key = "null" if pd.isna(group_value) else str(group_value)
        out[key] = {
            "rows": int(len(group)),
            "observed_rate": float(group["y_true"].mean()),
            "predicted_rate": float(group["y_prob"].mean()),
            "brier_score": float(np.mean((group["y_prob"] - group["y_true"]) ** 2)),
        }
    return out


def _sigmoid(values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    return 1.0 / (1.0 + np.exp(-np.clip(arr, -35.0, 35.0)))


def _fit_platt_scaler(y_true: np.ndarray, y_prob: np.ndarray, max_iter: int = 50, ridge: float = 1e-6) -> dict[str, float]:
    y = np.asarray(y_true, dtype=float)
    probs = np.clip(np.asarray(y_prob, dtype=float), 1e-6, 1 - 1e-6)
    logits = np.log(probs / (1.0 - probs))
    design = np.column_stack([logits, np.ones_like(logits)])
    beta = np.array([1.0, 0.0], dtype=float)
    ridge_eye = np.eye(2, dtype=float) * ridge
    for _ in range(max_iter):
        pred = _sigmoid(design @ beta)
        weights = np.clip(pred * (1.0 - pred), 1e-6, None)
        hessian = design.T @ (design * weights[:, None]) + ridge_eye
        gradient = design.T @ (pred - y) + ridge * beta
        step = np.linalg.solve(hessian, gradient)
        beta -= step
        if float(np.max(np.abs(step))) < 1e-6:
            break
    return {"a": float(beta[0]), "b": float(beta[1])}


def _apply_platt_scaler(y_prob: np.ndarray, params: dict[str, float]) -> np.ndarray:
    probs = np.clip(np.asarray(y_prob, dtype=float), 1e-6, 1 - 1e-6)
    logits = np.log(probs / (1.0 - probs))
    return _sigmoid(params["a"] * logits + params["b"])


def _fit_isotonic_calibrator(y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, list[float]]:
    probs = np.asarray(y_prob, dtype=float)
    y = np.asarray(y_true, dtype=float)
    order = np.argsort(probs, kind="mergesort")
    x_sorted = probs[order]
    y_sorted = y[order]
    blocks: list[dict[str, float]] = []
    for x_i, y_i in zip(x_sorted, y_sorted, strict=False):
        blocks.append({"sum_y": float(y_i), "count": 1.0, "max_x": float(x_i)})
        while len(blocks) >= 2 and (blocks[-2]["sum_y"] / blocks[-2]["count"]) > (blocks[-1]["sum_y"] / blocks[-1]["count"]):
            right = blocks.pop()
            left = blocks.pop()
            blocks.append(
                {
                    "sum_y": left["sum_y"] + right["sum_y"],
                    "count": left["count"] + right["count"],
                    "max_x": right["max_x"],
                }
            )
    thresholds = [block["max_x"] for block in blocks]
    values = [block["sum_y"] / block["count"] for block in blocks]
    return {"thresholds": thresholds, "values": values}


def _apply_isotonic_calibrator(y_prob: np.ndarray, calibrator: dict[str, list[float]]) -> np.ndarray:
    probs = np.asarray(y_prob, dtype=float)
    thresholds = np.asarray(calibrator["thresholds"], dtype=float)
    values = np.asarray(calibrator["values"], dtype=float)
    if len(thresholds) == 0:
        return np.clip(probs, 0.0, 1.0)
    indices = np.searchsorted(thresholds, probs, side="left")
    indices = np.clip(indices, 0, len(values) - 1)
    return values[indices]


def _apply_calibration(method: str, params: dict[str, object], raw_prob: np.ndarray) -> np.ndarray:
    if method == "identity":
        return np.asarray(raw_prob, dtype=float)
    if method == "platt":
        return _apply_platt_scaler(raw_prob, params)  # type: ignore[arg-type]
    if method == "isotonic":
        return _apply_isotonic_calibrator(raw_prob, params)  # type: ignore[arg-type]
    raise ValueError(f"Unsupported calibration method: {method}")


def _choose_calibration(y_val: np.ndarray, raw_val_prob: np.ndarray) -> tuple[str, dict[str, object], np.ndarray, dict[str, object]]:
    candidates: list[tuple[str, dict[str, object], np.ndarray]] = [("identity", {}, np.asarray(raw_val_prob, dtype=float))]
    platt_params = _fit_platt_scaler(y_val, raw_val_prob)
    candidates.append(("platt", platt_params, _apply_platt_scaler(raw_val_prob, platt_params)))
    isotonic_params = _fit_isotonic_calibrator(y_val, raw_val_prob)
    candidates.append(("isotonic", isotonic_params, _apply_isotonic_calibrator(raw_val_prob, isotonic_params)))

    scored: list[tuple[float, float, str, dict[str, object], np.ndarray]] = []
    for method, params, probs in candidates:
        brier = _brier_score(y_val, probs)
        log_loss = _log_loss_binary(y_val, probs)
        scored.append(
            (
                brier if brier is not None else float("inf"),
                log_loss if log_loss is not None else float("inf"),
                method,
                params,
                probs,
            )
        )
    scored.sort(key=lambda row: (row[0], row[1], row[2]))
    _, _, method, params, val_probs = scored[0]
    return method, params, val_probs, {
        candidate_method: {
            "brier_score": _brier_score(y_val, candidate_probs),
            "log_loss": _log_loss_binary(y_val, candidate_probs),
        }
        for candidate_method, _, candidate_probs in candidates
    }


def _sample_split_frame(
    con: duckdb.DuckDBPyConnection,
    feature_table: Path,
    split_table: Path,
    horizon: str,
    split_name: str,
    max_rows: int,
) -> tuple[pd.DataFrame, int]:
    observed_col = f"observed_{horizon}"
    target_col = f"grant_event_{horizon}"
    count_sql = f"""
        with split_scope as (
            select trajectory_id, as_of_date, as_of_year
            from read_parquet('{split_table}')
            where model_scope = '{MODEL_SCOPE}'
              and split_name = '{split_name}'
        ),
        joined as (
            select
                f.*
            from read_parquet('{feature_table}') f
            inner join split_scope s
              on s.trajectory_id = cast(f.docdb_family_id as varchar) || '|' || f.jurisdiction_code
             and s.as_of_date = f.as_of_date
             and s.as_of_year = f.as_of_year
            where coalesce(f.{observed_col}, false)
        )
        select count(*) from joined
    """
    raw_count = int(con.execute(count_sql).fetchone()[0])
    if raw_count == 0:
        return pd.DataFrame(), 0
    sample_clause = ""
    if raw_count > max_rows:
        sample_clause = f" using sample reservoir({max_rows} rows) repeatable(42)"
    frame = con.execute(
        f"""
        with split_scope as (
            select trajectory_id, as_of_date, as_of_year
            from read_parquet('{split_table}')
            where model_scope = '{MODEL_SCOPE}'
              and split_name = '{split_name}'
        ),
        joined as (
            select
                f.*,
                cast(f.{target_col} as integer) as target_label
            from read_parquet('{feature_table}') f
            inner join split_scope s
              on s.trajectory_id = cast(f.docdb_family_id as varchar) || '|' || f.jurisdiction_code
             and s.as_of_date = f.as_of_date
             and s.as_of_year = f.as_of_year
            where coalesce(f.{observed_col}, false)
        )
        select * from joined{sample_clause}
        """
    ).df()
    return frame, raw_count


def _prepare_pending_grant_matrix(
    feature_frame: pd.DataFrame,
    encoders: dict[str, dict[str, int]] | None = None,
) -> tuple[pd.DataFrame, dict[str, dict[str, int]]]:
    frame = feature_frame.copy()
    encoders = dict(encoders or {})
    categorical_columns = ["family_composite_status_asof", "primary_wipo_field"]
    for column in categorical_columns:
        frame[column] = frame[column].fillna("unknown").astype(str)
        mapping = encoders.get(column)
        if mapping is None:
            values = sorted(frame[column].unique().tolist())
            mapping = {value: idx for idx, value in enumerate(values)}
            encoders[column] = mapping
        frame[f"{column}_code"] = frame[column].map(mapping).fillna(-1).astype(int)
    numeric_columns = [
        feature for feature in FEATURE_NAMES if feature not in {"family_composite_status_asof", "primary_wipo_field"}
    ] + [
        "family_composite_status_asof_code"
    ] + [
        "primary_wipo_field_code"
    ]
    x = frame[numeric_columns].copy()
    for column in BOOLEAN_FEATURES:
        x[column] = x[column].astype(float)
    x = x.apply(pd.to_numeric, errors="coerce")
    medians = x.median(numeric_only=True).fillna(0.0)
    x = x.fillna(medians)
    return x, encoders


def _support_level(rows: int) -> str:
    if rows >= 10_000:
        return "strong"
    if rows >= 2_500:
        return "moderate"
    return "limited"


def _priority_tier(percentile: pd.Series) -> pd.Series:
    return pd.Series(
        pd.cut(
            percentile.fillna(0.0),
            bins=[-1.0, 50.0, 80.0, 95.0, 101.0],
            labels=["monitor", "watch", "high", "top"],
        ),
        index=percentile.index,
        dtype="string",
    ).fillna("monitor")


def _office_support_map(model_card: dict[str, object]) -> dict[str, str]:
    baseline_results = model_card.get("baseline_results", {}) if isinstance(model_card, dict) else {}
    office_rows: dict[str, int] = {}
    if isinstance(baseline_results, dict):
        for horizon_payload in baseline_results.values():
            if not isinstance(horizon_payload, dict):
                continue
            test_metrics = horizon_payload.get("test_metrics", {})
            if not isinstance(test_metrics, dict):
                continue
            subgroups = test_metrics.get("office_subgroups", {})
            if not isinstance(subgroups, dict):
                continue
            for office, summary in subgroups.items():
                if not isinstance(summary, dict):
                    continue
                office_rows[str(office)] = max(office_rows.get(str(office), 0), int(summary.get("rows") or 0))
    return {office: _support_level(rows) for office, rows in office_rows.items()}


def _score_pending_grant_frame(
    feature_frame: pd.DataFrame,
    *,
    booster_12m: Booster,
    booster_24m: Booster,
    calibration_payload: dict[str, object],
    feature_encoders: dict[str, dict[str, int]] | None,
    office_support_map: dict[str, str],
) -> pd.DataFrame:
    if feature_frame.empty:
        empty = feature_frame.copy()
        for column in ("grant_probability_raw_12m", "grant_probability_calibrated_12m", "grant_probability_raw_24m", "grant_probability_calibrated_24m"):
            empty[column] = pd.Series(dtype="float64")
        empty["office_support_level"] = pd.Series(dtype="string")
        return empty

    scored = feature_frame.copy()
    features, _ = _prepare_pending_grant_matrix(scored, feature_encoders)
    raw_12m = booster_12m.predict(features)
    raw_24m = booster_24m.predict(features)
    calibration_12m = calibration_payload.get("horizons", {}).get("12m", {}) if isinstance(calibration_payload, dict) else {}
    calibration_24m = calibration_payload.get("horizons", {}).get("24m", {}) if isinstance(calibration_payload, dict) else {}

    scored["grant_probability_raw_12m"] = raw_12m
    scored["grant_probability_raw_24m"] = raw_24m
    scored["grant_probability_calibrated_12m"] = _apply_calibration(
        str(calibration_12m.get("method", "identity")),
        dict(calibration_12m.get("params") or {}),
        raw_12m,
    )
    scored["grant_probability_calibrated_24m"] = _apply_calibration(
        str(calibration_24m.get("method", "identity")),
        dict(calibration_24m.get("params") or {}),
        raw_24m,
    )
    scored["office_support_level"] = scored["jurisdiction_code"].map(office_support_map).fillna("limited")
    return scored


def _evaluate_probability_metrics(frame: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, object]:
    return {
        "roc_auc": _roc_auc(y_true, y_prob),
        "pr_auc": _average_precision(y_true, y_prob),
        "brier_score": _brier_score(y_true, y_prob),
        "log_loss": _log_loss_binary(y_true, y_prob),
        "top_decile_lift": _top_decile_lift(y_true, y_prob),
        "recall_top_risk_quintile": _recall_at_top_fraction(y_true, y_prob, 0.20),
        "calibration_curve_by_decile": _calibration_curve_by_decile(y_true, y_prob),
        "office_subgroups": _subgroup_probability_summary(frame, y_true, y_prob, "jurisdiction_code", 5_000),
        "field_subgroups": _subgroup_probability_summary(frame, y_true, y_prob, "primary_wipo_field", 5_000),
    }


def _train_pending_grant_baselines(
    settings: BuildSettings,
    feature_table: Path,
    split_table: Path,
    model_registry_path: Path,
    experiment_registry_path: Path,
    calibration_registry_path: Path,
    model_card_path: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object], list[str], dict[str, float]]:
    con = duckdb.connect()
    experiment_rows: list[dict[str, object]] = []
    model_rows: list[dict[str, object]] = []
    calibration_rows: list[dict[str, object]] = []
    outputs: list[str] = []
    summary_metrics: dict[str, float] = {}
    feature_encoders: dict[str, dict[str, int]] | None = None

    model_card_payload = json.loads(model_card_path.read_text(encoding="utf-8"))
    model_card_payload["baseline_results"] = {}
    model_card_payload["training_samples"] = {}
    calibration_payload: dict[str, object] = {"horizons": {}}
    trained_horizons = 0

    for horizon in TRAINING_HORIZONS:
        raw_frames: dict[str, pd.DataFrame] = {}
        raw_counts: dict[str, int] = {}
        for split_name in ("train", "validation", "test"):
            frame, raw_count = _sample_split_frame(
                con=con,
                feature_table=feature_table,
                split_table=split_table,
                horizon=horizon,
                split_name=split_name,
                max_rows=MAX_ROWS_FOR_BASELINE[split_name],
            )
            raw_frames[split_name] = frame
            raw_counts[split_name] = raw_count

        if any(
            raw_counts[name] < MIN_ROWS_FOR_BASELINE[name] or len(raw_frames[name]) < MIN_ROWS_FOR_BASELINE[name]
            for name in MIN_ROWS_FOR_BASELINE
        ):
            experiment_rows.append(
                {
                    "experiment_id": f"{settings.release_id}-phase-grant-baseline-{horizon}",
                    "model_scope": MODEL_SCOPE,
                    "horizon": horizon,
                    "algorithm_family": "lightgbm_classifier",
                    "objective": "binary",
                    "training_snapshot": f"{settings.release_id}-phase-grant",
                    "feature_manifest_version": settings.method_version,
                    "primary_metric": "roc_auc",
                    "primary_metric_value": None,
                    "notes": "insufficient_split_rows",
                }
            )
            model_rows.append(
                {
                    "model_scope": MODEL_SCOPE,
                    "model_version": "pending_real_training",
                    "horizon": horizon,
                    "artifact_uri": None,
                    "feature_manifest_version": settings.method_version,
                    "calibration_version": None,
                    "promotion_status": "not_trained",
                    "rollback_model_version": None,
                    "prediction_unit": "docdb_family_id|jurisdiction_code|as_of_date",
                    "training_snapshot": f"{settings.release_id}-phase-grant",
                }
            )
            calibration_rows.append(
                {
                    "experiment_id": f"{settings.release_id}-phase-grant-baseline-{horizon}",
                    "model_scope": MODEL_SCOPE,
                    "horizon": horizon,
                    "calibration_version": f"{settings.release_id}-phase-grant-calibration-{horizon}",
                    "calibration_method": "not_calibrated",
                    "status": "not_trained",
                }
            )
            model_card_payload["baseline_results"][horizon] = {"status": "insufficient_rows", "raw_counts": raw_counts}
            continue

        x_train, feature_encoders = _prepare_pending_grant_matrix(raw_frames["train"], feature_encoders)
        x_val, _ = _prepare_pending_grant_matrix(raw_frames["validation"], feature_encoders)
        x_test, _ = _prepare_pending_grant_matrix(raw_frames["test"], feature_encoders)
        y_train = raw_frames["train"]["target_label"].to_numpy(dtype=int)
        y_val = raw_frames["validation"]["target_label"].to_numpy(dtype=int)
        y_test = raw_frames["test"]["target_label"].to_numpy(dtype=int)

        positives = int(y_train.sum())
        negatives = int(len(y_train) - positives)
        params = dict(BASELINE_PARAMS)
        params["scale_pos_weight"] = float(negatives / max(positives, 1))
        model = LGBMClassifier(**params)
        model.fit(x_train, y_train)

        raw_val_prob = model.predict_proba(x_val)[:, 1]
        raw_test_prob = model.predict_proba(x_test)[:, 1]
        calibration_method, calibration_params, calibrated_val_prob, candidate_metrics = _choose_calibration(y_val, raw_val_prob)
        calibrated_test_prob = _apply_calibration(calibration_method, calibration_params, raw_test_prob)

        validation_metrics = _evaluate_probability_metrics(raw_frames["validation"], y_val, calibrated_val_prob)
        test_metrics = _evaluate_probability_metrics(raw_frames["test"], y_test, calibrated_test_prob)

        model_path = model_registry_path.parent / f"pending_grant_pipeline_{horizon}_model.txt"
        model.booster_.save_model(str(model_path))
        outputs.append(str(model_path))

        experiment_rows.append(
            {
                "experiment_id": f"{settings.release_id}-phase-grant-baseline-{horizon}",
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "algorithm_family": "lightgbm_classifier",
                "objective": "binary",
                "training_snapshot": f"{settings.release_id}-phase-grant",
                "feature_manifest_version": settings.method_version,
                "primary_metric": "roc_auc",
                "primary_metric_value": test_metrics["roc_auc"],
                "notes": f"baseline_trained_calibration={calibration_method}",
                "roc_auc": test_metrics["roc_auc"],
                "pr_auc": test_metrics["pr_auc"],
                "brier_score": test_metrics["brier_score"],
                "log_loss": test_metrics["log_loss"],
                "top_decile_lift": test_metrics["top_decile_lift"],
                "recall_top_risk_quintile": test_metrics["recall_top_risk_quintile"],
            }
        )
        model_rows.append(
            {
                "model_scope": MODEL_SCOPE,
                "model_version": f"{settings.release_id}-phase-grant-baseline-{horizon}",
                "horizon": horizon,
                "artifact_uri": str(model_path),
                "feature_manifest_version": settings.method_version,
                "calibration_version": f"{settings.release_id}-phase-grant-calibration-{horizon}",
                "promotion_status": "candidate_trained",
                "rollback_model_version": None,
                "prediction_unit": "docdb_family_id|jurisdiction_code|as_of_date",
                "training_snapshot": f"{settings.release_id}-phase-grant",
            }
        )
        calibration_rows.append(
            {
                "experiment_id": f"{settings.release_id}-phase-grant-baseline-{horizon}",
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "calibration_version": f"{settings.release_id}-phase-grant-calibration-{horizon}",
                "calibration_method": calibration_method,
                "status": "calibrated",
                "brier_score": test_metrics["brier_score"],
                "log_loss": test_metrics["log_loss"],
            }
        )

        calibration_payload["horizons"][horizon] = {
            "method": calibration_method,
            "params": calibration_params,
            "validation_candidate_metrics": candidate_metrics,
            "validation_metrics": validation_metrics,
            "test_metrics": test_metrics,
            "raw_counts": raw_counts,
            "sampled_counts": {name: int(len(raw_frames[name])) for name in raw_frames},
            "scale_pos_weight": params["scale_pos_weight"],
        }
        model_card_payload["baseline_results"][horizon] = calibration_payload["horizons"][horizon]
        model_card_payload["training_samples"][horizon] = {
            "raw_counts": raw_counts,
            "sampled_counts": {name: int(len(raw_frames[name])) for name in raw_frames},
        }
        summary_metrics[f"{horizon}_roc_auc"] = float(test_metrics["roc_auc"]) if test_metrics["roc_auc"] is not None else float("nan")
        summary_metrics[f"{horizon}_pr_auc"] = float(test_metrics["pr_auc"]) if test_metrics["pr_auc"] is not None else float("nan")
        summary_metrics[f"{horizon}_brier_score"] = float(test_metrics["brier_score"]) if test_metrics["brier_score"] is not None else float("nan")
        trained_horizons += 1

    calibration_json_path = calibration_registry_path.parent / "pending_grant_pipeline_calibration.json"
    write_text_json(calibration_json_path, calibration_payload)
    outputs.append(str(calibration_json_path))

    if trained_horizons == 0:
        model_card_payload["status"] = "pending_real_training"
        model_card_payload["training_status"] = "insufficient_split_rows"
        model_card_payload["notes"] = [
            "Pending-grant label, feature, and split artifacts are built, but sampled split rows were insufficient for baseline training.",
        ]
    else:
        model_card_payload["status"] = "baseline_trained_candidate"
        model_card_payload["training_status"] = "baseline_lightgbm_trained"
        model_card_payload["notes"] = [
            "Pending-grant baselines are trained on sampled family-jurisdiction pending snapshots.",
            "Probability calibration is selected on validation between identity, Platt, and isotonic variants.",
            "This is the cross-office base model; EP-special procedural features remain a later enhancement.",
            "The current baseline includes primary field encoding, PIT-safe blocking/enforceability context, WIPO breadth, historical jurisdiction-field grant-rate priors, and raw local trend context.",
        ]
    if feature_encoders:
        model_card_payload["feature_encoders"] = feature_encoders
    model_card_payload["promotion_ready"] = False
    return experiment_rows, model_rows, calibration_rows, model_card_payload, outputs, summary_metrics


def _required_inputs(settings: BuildSettings) -> dict[str, Path]:
    return {
        "member_publications": settings.silver_dir / "silver_family_member_publications.parquet",
        "branch_history_dense": settings.silver_dir / "silver_branch_status_history_dense.parquet",
        "family_pit_dense": settings.silver_dir / "silver_family_feature_snapshot_pit_dense.parquet",
        "local_trends": settings.silver_dir / "silver_local_tech_trends_timeseries.parquet",
        "family_summary": settings.gold_dir / "gold_family_summary.parquet",
    }


def _ensure_inputs(required: dict[str, Path]) -> None:
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Pending-grant required inputs missing: {missing}")


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


def _replace_scope_from_parquet(path: Path, model_scope: str, source_path: Path) -> None:
    if not source_path.exists():
        raise FileNotFoundError(f"Pending-grant replacement source missing: {source_path}")
    if not path.exists():
        path.write_bytes(source_path.read_bytes())
        return
    tmp_path = path.with_suffix(".tmp.parquet")
    con = duckdb.connect()
    con.execute(
        f"""
        copy (
            select * from read_parquet('{path}') where model_scope <> '{model_scope}'
            union all by name
            select * from read_parquet('{source_path}')
        ) to '{tmp_path}' (format parquet, compression zstd)
        """
    )
    tmp_path.replace(path)


def _reset_tmp_dir(path: Path) -> Path:
    ensure_dir(path)
    for child in path.glob("*.parquet"):
        child.unlink()
    return path


def _write_empty_pending_grant_prediction_parquet(output_path: Path) -> None:
    ensure_dir(output_path.parent)
    tmp_path = output_path.with_suffix(".tmp.parquet")
    con = duckdb.connect()
    con.execute(
        f"""
        copy (
            select
                cast(null as varchar) as docdb_family_id,
                cast(null as varchar) as jurisdiction_code,
                cast(null as date) as as_of_date,
                cast(null as integer) as as_of_year,
                cast(null as integer) as family_priority_year,
                cast(null as varchar) as primary_wipo_field,
                cast(null as double) as family_age_years,
                cast(null as double) as pending_age_years,
                cast(null as varchar) as family_composite_status_asof,
                cast(null as double) as family_size_docdb_asof,
                cast(null as double) as family_jurisdiction_count_asof,
                cast(null as double) as family_coverage_stability_score_asof,
                cast(null as double) as family_tech_breadth_wipo_count_asof,
                cast(null as double) as family_blocking_power_score_asof,
                cast(null as double) as family_enforceability_score_asof,
                cast(null as double) as family_rcf_score_asof,
                cast(null as double) as pre_asof_forward_citations_clean,
                cast(null as double) as pre_asof_forward_citations_weighted,
                cast(null as double) as data_completeness_pct_asof,
                cast(null as double) as application_stage_publication_count,
                cast(null as double) as grant_stage_publication_count,
                cast(null as double) as jurisdiction_field_grant_rate_prior_12m,
                cast(null as double) as jurisdiction_field_grant_rate_prior_24m,
                cast(null as double) as local_family_filings_asof,
                cast(null as double) as prior_period_local_family_filings_asof,
                cast(null as double) as local_growth_rate_asof,
                cast(null as double) as local_trend_coefficient_asof,
                cast(null as boolean) as jurisdiction_is_ep,
                cast(null as boolean) as jurisdiction_is_us,
                cast(null as boolean) as jurisdiction_is_cn,
                cast(null as boolean) as jurisdiction_is_jp,
                cast(null as boolean) as jurisdiction_is_kr,
                cast(null as boolean) as jurisdiction_is_major_office,
                cast(null as double) as grant_probability_raw_12m,
                cast(null as double) as grant_probability_calibrated_12m,
                cast(null as double) as grant_probability_raw_24m,
                cast(null as double) as grant_probability_calibrated_24m,
                cast(null as bigint) as pending_grant_rank_within_office_12m,
                cast(null as double) as pending_grant_percentile_within_office_12m,
                cast(null as varchar) as pending_grant_priority_tier_12m,
                cast(null as bigint) as pending_grant_rank_within_office_24m,
                cast(null as double) as pending_grant_percentile_within_office_24m,
                cast(null as varchar) as pending_grant_priority_tier_24m,
                cast(null as varchar) as office_support_level
            where false
        ) to '{tmp_path}' (format parquet, compression zstd)
        """
    )
    tmp_path.replace(output_path)


def build_pending_grant_prediction_parquet(
    *,
    feature_path: Path,
    branch_history_path: Path,
    model_card_path: Path,
    calibration_path: Path,
    model_12m_path: Path,
    model_24m_path: Path,
    output_path: Path,
    chunk_row_limit: int = 250_000,
    temp_dir: Path | None = None,
) -> dict[str, int]:
    required_paths = {
        "feature": feature_path,
        "branch_history": branch_history_path,
        "model_card": model_card_path,
        "calibration": calibration_path,
        "model_12m": model_12m_path,
        "model_24m": model_24m_path,
    }
    missing = [name for name, path in required_paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Pending-grant prediction build inputs missing: {missing}")

    model_card = json.loads(model_card_path.read_text(encoding="utf-8"))
    calibration_payload = json.loads(calibration_path.read_text(encoding="utf-8"))
    feature_encoders = model_card.get("feature_encoders", {}) if isinstance(model_card, dict) else {}
    office_support_map = _office_support_map(model_card)
    booster_12m = Booster(model_file=str(model_12m_path))
    booster_24m = Booster(model_file=str(model_24m_path))

    safe_chunk_row_limit = max(10_000, int(chunk_row_limit))
    chunk_dir = _reset_tmp_dir(temp_dir or output_path.parent / "_tmp_pending_grant_prediction_chunks")

    con = duckdb.connect()
    con.execute(
        f"""
        create or replace temp table current_pending_pairs as
        select
            docdb_family_id,
            jurisdiction_code,
            snapshot_date
        from (
            select
                cast(docdb_family_id as varchar) as docdb_family_id,
                jurisdiction_code,
                cast(snapshot_date as date) as snapshot_date,
                snapshot_year,
                coalesce(pending_branch_flag, false) as pending_branch_flag,
                row_number() over (
                    partition by cast(docdb_family_id as varchar), jurisdiction_code
                    order by snapshot_year desc, cast(snapshot_date as date) desc
                ) as rn
            from read_parquet('{branch_history_path}')
        ) ranked
        where rn = 1
          and pending_branch_flag
        """
    )
    current_pending_pair_count = int(con.execute("select count(*) from current_pending_pairs").fetchone()[0])
    if current_pending_pair_count == 0:
        _write_empty_pending_grant_prediction_parquet(output_path)
        return {
            "current_pending_pair_count": 0,
            "scored_row_count": 0,
            "partition_count": 0,
            "chunk_count": 0,
        }

    con.execute(
        f"""
        create or replace temp table current_pending_scoring_scope as
        select
            cast(f.docdb_family_id as varchar) as docdb_family_id,
            f.jurisdiction_code,
            cast(f.as_of_date as date) as as_of_date,
            cast(f.as_of_year as integer) as as_of_year,
            cast(f.family_priority_year as integer) as family_priority_year,
            f.primary_wipo_field,
            cast(f.family_age_years as double) as family_age_years,
            cast(f.pending_age_years as double) as pending_age_years,
            f.family_composite_status_asof,
            cast(f.family_size_docdb_asof as double) as family_size_docdb_asof,
            cast(f.family_jurisdiction_count_asof as double) as family_jurisdiction_count_asof,
            cast(f.family_coverage_stability_score_asof as double) as family_coverage_stability_score_asof,
            cast(f.family_tech_breadth_wipo_count_asof as double) as family_tech_breadth_wipo_count_asof,
            cast(f.family_blocking_power_score_asof as double) as family_blocking_power_score_asof,
            cast(f.family_enforceability_score_asof as double) as family_enforceability_score_asof,
            cast(f.family_rcf_score_asof as double) as family_rcf_score_asof,
            cast(f.pre_asof_forward_citations_clean as double) as pre_asof_forward_citations_clean,
            cast(f.pre_asof_forward_citations_weighted as double) as pre_asof_forward_citations_weighted,
            cast(f.data_completeness_pct_asof as double) as data_completeness_pct_asof,
            cast(f.application_stage_publication_count as double) as application_stage_publication_count,
            cast(f.grant_stage_publication_count as double) as grant_stage_publication_count,
            cast(f.jurisdiction_field_grant_rate_prior_12m as double) as jurisdiction_field_grant_rate_prior_12m,
            cast(f.jurisdiction_field_grant_rate_prior_24m as double) as jurisdiction_field_grant_rate_prior_24m,
            cast(f.local_family_filings_asof as double) as local_family_filings_asof,
            cast(f.prior_period_local_family_filings_asof as double) as prior_period_local_family_filings_asof,
            cast(f.local_growth_rate_asof as double) as local_growth_rate_asof,
            cast(f.local_trend_coefficient_asof as double) as local_trend_coefficient_asof,
            cast(f.jurisdiction_is_ep as boolean) as jurisdiction_is_ep,
            cast(f.jurisdiction_is_us as boolean) as jurisdiction_is_us,
            cast(f.jurisdiction_is_cn as boolean) as jurisdiction_is_cn,
            cast(f.jurisdiction_is_jp as boolean) as jurisdiction_is_jp,
            cast(f.jurisdiction_is_kr as boolean) as jurisdiction_is_kr,
            cast(f.jurisdiction_is_major_office as boolean) as jurisdiction_is_major_office
        from read_parquet('{feature_path}') f
        join current_pending_pairs c
          on cast(f.docdb_family_id as varchar) = c.docdb_family_id
         and f.jurisdiction_code = c.jurisdiction_code
         and cast(f.as_of_date as date) = c.snapshot_date
        """
    )
    scored_row_count = int(con.execute("select count(*) from current_pending_scoring_scope").fetchone()[0])
    if scored_row_count == 0:
        _write_empty_pending_grant_prediction_parquet(output_path)
        return {
            "current_pending_pair_count": current_pending_pair_count,
            "scored_row_count": 0,
            "partition_count": 0,
            "chunk_count": 0,
        }

    partitions = [
        {"as_of_year": int(row[0]), "jurisdiction_code": str(row[1]), "row_count": int(row[2])}
        for row in con.execute(
            """
            select as_of_year, jurisdiction_code, count(*) as row_count
            from current_pending_scoring_scope
            group by 1, 2
            order by 1, 2
            """
        ).fetchall()
    ]

    chunk_paths: list[str] = []
    chunk_count = 0
    for partition in partitions:
        as_of_year = partition["as_of_year"]
        jurisdiction_code = partition["jurisdiction_code"]
        row_count = partition["row_count"]
        for start in range(0, row_count, safe_chunk_row_limit):
            stop = min(start + safe_chunk_row_limit, row_count)
            chunk_frame = con.execute(
                """
                with numbered as (
                    select
                        *,
                        row_number() over (
                            order by cast(docdb_family_id as varchar) asc, cast(as_of_date as date) asc
                        ) as rn
                    from current_pending_scoring_scope
                    where as_of_year = ?
                      and jurisdiction_code = ?
                )
                select * exclude (rn)
                from numbered
                where rn > ?
                  and rn <= ?
                order by rn
                """,
                [as_of_year, jurisdiction_code, start, stop],
            ).df()
            if chunk_frame.empty:
                continue
            scored_chunk = _score_pending_grant_frame(
                chunk_frame,
                booster_12m=booster_12m,
                booster_24m=booster_24m,
                calibration_payload=calibration_payload,
                feature_encoders=feature_encoders if isinstance(feature_encoders, dict) else {},
                office_support_map=office_support_map,
            )
            chunk_path = chunk_dir / f"pending_grant_prediction_chunk_{chunk_count:05d}.parquet"
            scored_chunk[PREDICTION_PRE_RANK_COLUMNS].to_parquet(chunk_path, index=False)
            chunk_paths.append(str(chunk_path))
            chunk_count += 1

    if not chunk_paths:
        _write_empty_pending_grant_prediction_parquet(output_path)
        return {
            "current_pending_pair_count": current_pending_pair_count,
            "scored_row_count": scored_row_count,
            "partition_count": len(partitions),
            "chunk_count": 0,
        }

    sources_sql = ", ".join(repr(path) for path in chunk_paths)
    tmp_output_path = output_path.with_suffix(".tmp.parquet")
    ensure_dir(output_path.parent)
    con.execute(
        f"""
        copy (
            with scored as (
                select * from read_parquet([{sources_sql}])
            ),
            ranked as (
                select
                    *,
                    row_number() over (
                        partition by jurisdiction_code
                        order by grant_probability_calibrated_12m desc, cast(docdb_family_id as varchar) asc, cast(as_of_date as date) asc
                    ) as pending_grant_rank_within_office_12m,
                    row_number() over (
                        partition by jurisdiction_code
                        order by grant_probability_calibrated_24m desc, cast(docdb_family_id as varchar) asc, cast(as_of_date as date) asc
                    ) as pending_grant_rank_within_office_24m,
                    count(*) over (partition by jurisdiction_code) as office_row_count
                from scored
            ),
            percentiled as (
                select
                    *,
                    cast(
                        case
                            when office_row_count <= 1 then 100.0
                            else 100.0 - (cast(pending_grant_rank_within_office_12m - 1 as double) / cast(greatest(office_row_count - 1, 1) as double)) * 100.0
                        end as double
                    ) as pending_grant_percentile_within_office_12m,
                    cast(
                        case
                            when office_row_count <= 1 then 100.0
                            else 100.0 - (cast(pending_grant_rank_within_office_24m - 1 as double) / cast(greatest(office_row_count - 1, 1) as double)) * 100.0
                        end as double
                    ) as pending_grant_percentile_within_office_24m
                from ranked
            )
            select
                docdb_family_id,
                jurisdiction_code,
                as_of_date,
                as_of_year,
                family_priority_year,
                primary_wipo_field,
                family_age_years,
                pending_age_years,
                family_composite_status_asof,
                family_size_docdb_asof,
                family_jurisdiction_count_asof,
                family_coverage_stability_score_asof,
                family_tech_breadth_wipo_count_asof,
                family_blocking_power_score_asof,
                family_enforceability_score_asof,
                family_rcf_score_asof,
                pre_asof_forward_citations_clean,
                pre_asof_forward_citations_weighted,
                data_completeness_pct_asof,
                application_stage_publication_count,
                grant_stage_publication_count,
                jurisdiction_field_grant_rate_prior_12m,
                jurisdiction_field_grant_rate_prior_24m,
                local_family_filings_asof,
                prior_period_local_family_filings_asof,
                local_growth_rate_asof,
                local_trend_coefficient_asof,
                jurisdiction_is_ep,
                jurisdiction_is_us,
                jurisdiction_is_cn,
                jurisdiction_is_jp,
                jurisdiction_is_kr,
                jurisdiction_is_major_office,
                grant_probability_raw_12m,
                grant_probability_calibrated_12m,
                grant_probability_raw_24m,
                grant_probability_calibrated_24m,
                pending_grant_rank_within_office_12m,
                pending_grant_percentile_within_office_12m,
                case
                    when coalesce(pending_grant_percentile_within_office_12m, 0.0) >= 95.0 then 'top'
                    when coalesce(pending_grant_percentile_within_office_12m, 0.0) >= 80.0 then 'high'
                    when coalesce(pending_grant_percentile_within_office_12m, 0.0) >= 50.0 then 'watch'
                    else 'monitor'
                end as pending_grant_priority_tier_12m,
                pending_grant_rank_within_office_24m,
                pending_grant_percentile_within_office_24m,
                case
                    when coalesce(pending_grant_percentile_within_office_24m, 0.0) >= 95.0 then 'top'
                    when coalesce(pending_grant_percentile_within_office_24m, 0.0) >= 80.0 then 'high'
                    when coalesce(pending_grant_percentile_within_office_24m, 0.0) >= 50.0 then 'watch'
                    else 'monitor'
                end as pending_grant_priority_tier_24m,
                office_support_level
            from percentiled
        ) to '{tmp_output_path}' (format parquet, compression zstd)
        """
    )
    tmp_output_path.replace(output_path)

    return {
        "current_pending_pair_count": current_pending_pair_count,
        "scored_row_count": scored_row_count,
        "partition_count": len(partitions),
        "chunk_count": chunk_count,
    }


def build_ml_pending_grant_pipeline(settings: BuildSettings) -> StageResult:
    required = _required_inputs(settings)
    _ensure_inputs(required)

    label_path = settings.ml_dir / LABEL_TABLE_NAME
    feature_path = settings.ml_dir / FEATURE_TABLE_NAME
    split_path = settings.ml_dir / SPLIT_TABLE_NAME
    phase_split_path = settings.ml_dir / PHASE_SPLIT_TABLE_NAME
    experiment_registry_path = settings.ml_dir / EXPERIMENT_REGISTRY_NAME
    model_registry_path = settings.ml_dir / MODEL_REGISTRY_NAME
    calibration_registry_path = settings.ml_dir / CALIBRATION_REGISTRY_NAME
    feature_manifest_path = settings.ml_dir / FEATURE_MANIFEST_NAME
    model_card_path = settings.ml_dir / MODEL_CARD_NAME
    prediction_path = settings.ml_dir / PREDICTION_TABLE_NAME
    label_tmp_dir = _reset_tmp_dir(settings.ml_dir / "_tmp_phase_grant_label_chunks")
    feature_tmp_dir = _reset_tmp_dir(settings.ml_dir / "_tmp_phase_grant_feature_chunks")

    snapshot_year = int(settings.snapshot_date[:4])
    con = duckdb.connect()
    if label_path.exists():
        label_path.unlink()
    if feature_path.exists():
        feature_path.unlink()

    print("[phase_grant] building pending_year_counts", flush=True)
    con.execute(
        f"""
        create or replace temp table pending_year_counts as
        select
            snapshot_year,
            count(*) as pending_row_count
        from read_parquet('{required["branch_history_dense"]}')
        where coalesce(pending_branch_flag, false)
        group by 1
        """
    )
    print("[phase_grant] building pending_family_jurisdiction_pairs", flush=True)
    con.execute(
        f"""
        create or replace temp table pending_family_jurisdiction_pairs as
        select distinct
            docdb_family_id,
            jurisdiction_code
        from read_parquet('{required["branch_history_dense"]}')
        where coalesce(pending_branch_flag, false)
        """
    )
    print("[phase_grant] building first_active_grant_dates", flush=True)
    con.execute(
        f"""
        create or replace temp table first_active_grant_dates as
        select
            a.docdb_family_id,
            a.jurisdiction_code,
            min(cast(a.snapshot_date as date)) as first_active_grant_date
        from read_parquet('{required["branch_history_dense"]}') a
        inner join pending_family_jurisdiction_pairs p
          on p.docdb_family_id = a.docdb_family_id
         and p.jurisdiction_code = a.jurisdiction_code
        where coalesce(a.active_branch_flag, false)
        group by 1,2
        """
    )
    print("[phase_grant] building publication_counts_by_year", flush=True)
    con.execute(
        f"""
        create or replace temp table publication_counts_by_year as
        select
            docdb_family_id,
            publn_auth as jurisdiction_code,
            extract(year from cast(publn_date as date)) as publn_year,
            sum(case when coalesce(is_application_stage, false) then 1 else 0 end) as application_stage_publication_count_year,
            sum(case when coalesce(is_grant_stage, false) then 1 else 0 end) as grant_stage_publication_count_year
        from read_parquet('{required["member_publications"]}')
        where cast(publn_date as date) is not null
        group by 1,2,3
        """
    )
    print("[phase_grant] building local_trend_features_by_year", flush=True)
    con.execute(
        f"""
        create or replace temp table local_trend_features_by_year as
        select
            jurisdiction_code,
            wipo_industry_code as primary_wipo_field,
            snapshot_year as as_of_year,
            cast(local_family_filings as double) as local_family_filings_asof,
            cast(prior_period_local_family_filings as double) as prior_period_local_family_filings_asof,
            cast(local_growth_rate as double) as local_growth_rate_asof,
            cast(local_trend_coefficient as double) as local_trend_coefficient_asof
        from read_parquet('{required["local_trends"]}')
        """
    )

    pending_years = [
        int(row[0])
        for row in con.execute(
            f"""
            select snapshot_year
            from pending_year_counts
            order by snapshot_year
            """
        ).fetchall()
    ]
    print(f"[phase_grant] pending years {pending_years[0]}..{pending_years[-1]} ({len(pending_years)})", flush=True)

    label_chunk_paths: list[str] = []
    feature_chunk_paths: list[str] = []

    for year in pending_years:
        print(f"[phase_grant] label year {year}", flush=True)
        label_chunk = label_tmp_dir / f"pending_grant_labels_{year}.parquet"
        con.execute(
            f"""
            copy (
                with pending_rows as (
                    select
                        b.docdb_family_id,
                        b.jurisdiction_code,
                        cast(b.snapshot_date as date) as as_of_date,
                        b.snapshot_year as as_of_year,
                        cast(b.last_pending_event_date as date) as last_pending_event_date
                    from read_parquet('{required["branch_history_dense"]}') b
                    where coalesce(b.pending_branch_flag, false)
                      and b.snapshot_year = {year}
                ),
                with_family as (
                    select
                        p.docdb_family_id,
                        p.jurisdiction_code,
                        p.as_of_date,
                        p.as_of_year,
                        cast(
                            coalesce(
                                f.first_active_grant_date > p.as_of_date
                                and f.first_active_grant_date <= p.as_of_date + interval 12 months,
                                false
                            ) as integer
                        ) as grant_event_12m,
                        cast(
                            coalesce(
                                f.first_active_grant_date > p.as_of_date
                                and f.first_active_grant_date <= p.as_of_date + interval 24 months,
                                false
                            ) as integer
                        ) as grant_event_24m,
                        cast(p.as_of_date + interval 12 months <= cast('{settings.snapshot_date}' as date) as boolean) as observed_12m,
                        cast(p.as_of_date + interval 24 months <= cast('{settings.snapshot_date}' as date) as boolean) as observed_24m,
                        p.last_pending_event_date,
                        fs.family_priority_year,
                        fs.primary_wipo_field
                    from pending_rows p
                    left join first_active_grant_dates f
                      on f.docdb_family_id = p.docdb_family_id
                     and f.jurisdiction_code = p.jurisdiction_code
                    join read_parquet('{required["family_summary"]}') fs
                      on fs.docdb_family_id = p.docdb_family_id
                )
                select
                    *,
                    cast(date_diff('day', coalesce(last_pending_event_date, as_of_date), as_of_date) / 365.25 as double) as pending_age_years
                from with_family
            ) to '{label_chunk}' (format parquet, compression zstd)
            """
        )
        label_chunk_paths.append(str(label_chunk))

    if not label_chunk_paths:
        raise FileNotFoundError("Pending-grant label chunks were not generated.")

    con.execute(
        f"""
        copy (
            select * from read_parquet([{", ".join(repr(path) for path in label_chunk_paths)}])
        ) to '{label_path}' (format parquet, compression zstd)
        """
    )
    print("[phase_grant] merged label parquet", flush=True)

    for year in pending_years:
        print(f"[phase_grant] feature year {year}", flush=True)
        feature_chunk = feature_tmp_dir / f"pending_grant_features_{year}.parquet"
        con.execute(
            f"""
            copy (
                with prior_jurisdiction_field as (
                    select
                        jurisdiction_code,
                        primary_wipo_field,
                        sum(case when coalesce(observed_12m, false) then 1 else 0 end) as prior_obs_12m_count,
                        sum(case when coalesce(observed_12m, false) then coalesce(grant_event_12m, 0) else 0 end) as prior_pos_12m_count,
                        sum(case when coalesce(observed_24m, false) then 1 else 0 end) as prior_obs_24m_count,
                        sum(case when coalesce(observed_24m, false) then coalesce(grant_event_24m, 0) else 0 end) as prior_pos_24m_count
                    from read_parquet('{label_path}')
                    where as_of_year < {year}
                    group by 1,2
                ),
                prior_jurisdiction as (
                    select
                        jurisdiction_code,
                        sum(case when coalesce(observed_12m, false) then 1 else 0 end) as prior_obs_12m_count,
                        sum(case when coalesce(observed_12m, false) then coalesce(grant_event_12m, 0) else 0 end) as prior_pos_12m_count,
                        sum(case when coalesce(observed_24m, false) then 1 else 0 end) as prior_obs_24m_count,
                        sum(case when coalesce(observed_24m, false) then coalesce(grant_event_24m, 0) else 0 end) as prior_pos_24m_count
                    from read_parquet('{label_path}')
                    where as_of_year < {year}
                    group by 1
                ),
                prior_global as (
                    select
                        sum(case when coalesce(observed_12m, false) then 1 else 0 end) as prior_obs_12m_count,
                        sum(case when coalesce(observed_12m, false) then coalesce(grant_event_12m, 0) else 0 end) as prior_pos_12m_count,
                        sum(case when coalesce(observed_24m, false) then 1 else 0 end) as prior_obs_24m_count,
                        sum(case when coalesce(observed_24m, false) then coalesce(grant_event_24m, 0) else 0 end) as prior_pos_24m_count
                    from read_parquet('{label_path}')
                    where as_of_year < {year}
                )
                select
                    l.docdb_family_id,
                    l.jurisdiction_code,
                    l.as_of_date,
                    l.as_of_year,
                    l.family_priority_year,
                    l.primary_wipo_field,
                    cast(l.as_of_year - l.family_priority_year as double) as family_age_years,
                    l.pending_age_years,
                    p.family_composite_status_asof,
                    p.family_size_docdb_asof,
                    p.family_jurisdiction_count_asof,
                    p.family_coverage_stability_score_asof,
                    p.family_tech_breadth_wipo_count_asof,
                    p.family_blocking_power_score_asof,
                    p.family_enforceability_score_asof,
                    p.family_rcf_score_asof,
                    p.pre_asof_forward_citations_clean,
                    p.pre_asof_forward_citations_weighted,
                    p.data_completeness_pct_asof,
                    coalesce(sum(case when py.publn_year <= l.as_of_year then py.application_stage_publication_count_year else 0 end), 0) as application_stage_publication_count,
                    coalesce(sum(case when py.publn_year <= l.as_of_year then py.grant_stage_publication_count_year else 0 end), 0) as grant_stage_publication_count,
                    case
                        when coalesce(pjf.prior_obs_12m_count, 0) > 0 then
                            (
                                cast(pjf.prior_pos_12m_count as double)
                                + 50.0 * coalesce(
                                    cast(pj.prior_pos_12m_count as double) / nullif(cast(pj.prior_obs_12m_count as double), 0.0),
                                    cast(pg.prior_pos_12m_count as double) / nullif(cast(pg.prior_obs_12m_count as double), 0.0),
                                    0.0
                                )
                            ) / (cast(pjf.prior_obs_12m_count as double) + 50.0)
                        else coalesce(
                            cast(pj.prior_pos_12m_count as double) / nullif(cast(pj.prior_obs_12m_count as double), 0.0),
                            cast(pg.prior_pos_12m_count as double) / nullif(cast(pg.prior_obs_12m_count as double), 0.0),
                            0.0
                        )
                    end as jurisdiction_field_grant_rate_prior_12m,
                    case
                        when coalesce(pjf.prior_obs_24m_count, 0) > 0 then
                            (
                                cast(pjf.prior_pos_24m_count as double)
                                + 50.0 * coalesce(
                                    cast(pj.prior_pos_24m_count as double) / nullif(cast(pj.prior_obs_24m_count as double), 0.0),
                                    cast(pg.prior_pos_24m_count as double) / nullif(cast(pg.prior_obs_24m_count as double), 0.0),
                                    0.0
                                )
                            ) / (cast(pjf.prior_obs_24m_count as double) + 50.0)
                        else coalesce(
                            cast(pj.prior_pos_24m_count as double) / nullif(cast(pj.prior_obs_24m_count as double), 0.0),
                            cast(pg.prior_pos_24m_count as double) / nullif(cast(pg.prior_obs_24m_count as double), 0.0),
                            0.0
                        )
                    end as jurisdiction_field_grant_rate_prior_24m,
                    coalesce(lt.local_family_filings_asof, 0.0) as local_family_filings_asof,
                    coalesce(lt.prior_period_local_family_filings_asof, 0.0) as prior_period_local_family_filings_asof,
                    coalesce(lt.local_growth_rate_asof, 0.0) as local_growth_rate_asof,
                    coalesce(lt.local_trend_coefficient_asof, 0.0) as local_trend_coefficient_asof,
                    cast(l.jurisdiction_code = 'EP' as boolean) as jurisdiction_is_ep,
                    cast(l.jurisdiction_code = 'US' as boolean) as jurisdiction_is_us,
                    cast(l.jurisdiction_code = 'CN' as boolean) as jurisdiction_is_cn,
                    cast(l.jurisdiction_code = 'JP' as boolean) as jurisdiction_is_jp,
                    cast(l.jurisdiction_code = 'KR' as boolean) as jurisdiction_is_kr,
                    cast(l.jurisdiction_code in ('EP', 'US', 'CN', 'JP', 'KR') as boolean) as jurisdiction_is_major_office,
                    l.grant_event_12m,
                    l.grant_event_24m,
                    l.observed_12m,
                    l.observed_24m
                from read_parquet('{label_path}') l
                left join read_parquet('{required["family_pit_dense"]}') p
                  on p.docdb_family_id = l.docdb_family_id
                 and p.as_of_date = l.as_of_date
                left join publication_counts_by_year py
                  on py.docdb_family_id = l.docdb_family_id
                 and py.jurisdiction_code = l.jurisdiction_code
                left join prior_jurisdiction_field pjf
                  on pjf.jurisdiction_code = l.jurisdiction_code
                 and coalesce(pjf.primary_wipo_field, 'unknown') = coalesce(l.primary_wipo_field, 'unknown')
                left join prior_jurisdiction pj
                  on pj.jurisdiction_code = l.jurisdiction_code
                left join local_trend_features_by_year lt
                  on lt.jurisdiction_code = l.jurisdiction_code
                 and coalesce(lt.primary_wipo_field, 'unknown') = coalesce(l.primary_wipo_field, 'unknown')
                 and lt.as_of_year = l.as_of_year
                cross join prior_global pg
                where l.as_of_year = {year}
                group by all
            ) to '{feature_chunk}' (format parquet, compression zstd)
            """
        )
        feature_chunk_paths.append(str(feature_chunk))

    con.execute(
        f"""
        copy (
            select * from read_parquet([{", ".join(repr(path) for path in feature_chunk_paths)}])
        ) to '{feature_path}' (format parquet, compression zstd)
        """
    )
    print("[phase_grant] merged feature parquet", flush=True)

    con.execute(
        f"""
        copy (
            with trajectory_first_year as (
                select
                    cast(docdb_family_id as varchar) || '|' || jurisdiction_code as trajectory_id,
                    min(as_of_year) as first_pending_year
                from read_parquet('{label_path}')
                group by 1
            )
            select
                '{MODEL_SCOPE}' as model_scope,
                l.docdb_family_id,
                l.jurisdiction_code as entity_subkey,
                cast(l.docdb_family_id as varchar) || '|' || l.jurisdiction_code as trajectory_id,
                l.as_of_date,
                l.as_of_year,
                case
                    when t.first_pending_year <= {snapshot_year - 5} then 'train'
                    when t.first_pending_year = {snapshot_year - 4} then 'validation'
                    when t.first_pending_year = {snapshot_year - 3} then 'test'
                    else 'unassigned_recent'
                end as split_name
            from read_parquet('{label_path}') l
            inner join trajectory_first_year t
              on t.trajectory_id = cast(l.docdb_family_id as varchar) || '|' || l.jurisdiction_code
        ) to '{phase_split_path}' (format parquet, compression zstd)
        """
    )
    _replace_scope_from_parquet(split_path, MODEL_SCOPE, phase_split_path)
    print("[phase_grant] wrote split registries", flush=True)

    _write_scope_rows(
        feature_manifest_path,
        MODEL_SCOPE,
        [
            {
                "model_scope": MODEL_SCOPE,
                "feature_table": str(feature_path),
                "feature_name": feature_name,
                "method_version": settings.method_version,
            }
            for feature_name in [
                "primary_wipo_field",
                "family_age_years",
                "pending_age_years",
                "family_composite_status_asof",
                "family_size_docdb_asof",
                "family_jurisdiction_count_asof",
                "family_coverage_stability_score_asof",
                "family_tech_breadth_wipo_count_asof",
                "family_blocking_power_score_asof",
                "family_enforceability_score_asof",
                "family_rcf_score_asof",
                "pre_asof_forward_citations_clean",
                "pre_asof_forward_citations_weighted",
                "application_stage_publication_count",
                "grant_stage_publication_count",
                "jurisdiction_field_grant_rate_prior_12m",
                "jurisdiction_field_grant_rate_prior_24m",
                "local_family_filings_asof",
                "prior_period_local_family_filings_asof",
                "local_growth_rate_asof",
                "local_trend_coefficient_asof",
            ]
        ],
    )

    write_text_json(
        model_card_path,
        {
            "model_scope": MODEL_SCOPE,
            "status": "pending_real_training",
            "native_grain": "family_x_jurisdiction_asof_pending_branch_context",
            "feature_table": str(feature_path),
            "label_table": str(label_path),
            "split_registry": str(phase_split_path),
            "training_horizons": list(TRAINING_HORIZONS),
            "method_version": settings.method_version,
            "release_id": settings.release_id,
            "notes": [
                "This is the first pending-grant pipeline contract scaffold.",
                "Track A should be a cross-office base model.",
                "EP-special procedural features remain a later isolated enhancement.",
                "The current retraining pass enriches the base model with field encoding, PIT-safe blocking/enforceability context, WIPO breadth, train-safe jurisdiction-field priors, and raw local trend context.",
            ],
        },
    )

    (
        experiment_rows,
        model_rows,
        calibration_rows,
        model_card_payload,
        training_outputs,
        summary_metrics,
    ) = _train_pending_grant_baselines(
        settings=settings,
        feature_table=feature_path,
        split_table=phase_split_path,
        model_registry_path=model_registry_path,
        experiment_registry_path=experiment_registry_path,
        calibration_registry_path=calibration_registry_path,
        model_card_path=model_card_path,
    )
    _write_scope_rows(experiment_registry_path, MODEL_SCOPE, experiment_rows)
    _write_scope_rows(model_registry_path, MODEL_SCOPE, model_rows)
    _write_scope_rows(calibration_registry_path, MODEL_SCOPE, calibration_rows)
    write_text_json(model_card_path, model_card_payload)
    print("[phase_grant] wrote registries and model card", flush=True)

    prediction_metrics: dict[str, int] | None = None
    calibration_json_path = calibration_registry_path.parent / "pending_grant_pipeline_calibration.json"
    model_12m_path = model_registry_path.parent / "pending_grant_pipeline_12m_model.txt"
    model_24m_path = model_registry_path.parent / "pending_grant_pipeline_24m_model.txt"
    if all(path.exists() for path in (feature_path, required["branch_history_dense"], model_card_path, calibration_json_path, model_12m_path, model_24m_path)):
        print("[phase_grant] building current pending prediction parquet", flush=True)
        prediction_metrics = build_pending_grant_prediction_parquet(
            feature_path=feature_path,
            branch_history_path=required["branch_history_dense"],
            model_card_path=model_card_path,
            calibration_path=calibration_json_path,
            model_12m_path=model_12m_path,
            model_24m_path=model_24m_path,
            output_path=prediction_path,
            temp_dir=settings.ml_dir / "_tmp_phase_grant_prediction_chunks",
        )
        print("[phase_grant] wrote pending-grant prediction parquet", flush=True)
    else:
        print("[phase_grant] skipped pending-grant prediction parquet; serving artifacts unavailable", flush=True)

    result = StageResult(
        stage="ml-pending-grant-pipeline",
        status="success",
        summary="Materialized pending-grant label, feature, and split artifacts, trained first baseline pending-grant classifiers when split sizes were sufficient, and wrote the current-pending scored serving parquet when scoring artifacts were available.",
        methods=[
            "Built branch-grain pending-grant labels from dense branch history by checking future grant conversion within 12m and 24m horizons.",
            "Joined family PIT-safe context and publication-stage counts to create the first pending-grant feature scaffold.",
            "Sampled split-aligned pending snapshots to train first 12m and 24m LightGBM baseline grant-probability models with validation-time calibration selection.",
            "Scored the latest pending family-jurisdiction rows and materialized the canonical pending-grant serving parquet with office-relative ranks and percentiles when model artifacts were present.",
        ],
        calculations=[
            "Observed-horizon flags require the as-of row to have a fully observable 12m or 24m window by the ETL snapshot date.",
            "Pending-age is measured from the last pending event date when available.",
        ],
        doc_refs=[
            "docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md",
            "docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md",
            "docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md",
        ],
    )
    result.outputs.extend(
        [
            str(label_path),
            str(feature_path),
            str(split_path),
            str(phase_split_path),
            str(experiment_registry_path),
            str(model_registry_path),
            str(calibration_registry_path),
            str(feature_manifest_path),
            str(model_card_path),
        ]
    )
    result.outputs.extend(training_outputs)
    if prediction_path.exists():
        result.outputs.append(str(prediction_path))
    result.metrics["ml_label_pending_grant_event_rows"] = parquet_row_count(label_path)
    result.metrics["ml_feature_pending_grant_pipeline_rows"] = parquet_row_count(feature_path)
    result.metrics["ml_split_registry_phase_grant_rows"] = parquet_row_count(phase_split_path)
    result.metrics["ml_prediction_pending_grant_pipeline_rows"] = parquet_row_count(prediction_path)
    result.metrics["pending_grant_observed_12m_rows"] = int(
        con.execute(f"select count(*) from read_parquet('{label_path}') where coalesce(observed_12m, false)").fetchone()[0]
    )
    result.metrics["pending_grant_observed_24m_rows"] = int(
        con.execute(f"select count(*) from read_parquet('{label_path}') where coalesce(observed_24m, false)").fetchone()[0]
    )
    for metric_name, metric_value in summary_metrics.items():
        result.metrics[f"pending_grant_{metric_name}"] = metric_value
    if prediction_metrics is not None:
        for metric_name, metric_value in prediction_metrics.items():
            result.metrics[f"pending_grant_prediction_{metric_name}"] = metric_value
    return result

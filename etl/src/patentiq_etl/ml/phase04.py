from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

from patentiq_etl.common.io import ensure_dir, parquet_row_count, write_pylist_parquet, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult


MODEL_SCOPE = "family_jurisdiction_lapse_risk"
FEATURE_TABLE_NAME = "ml_feature_family_jurisdiction_lapse_risk.parquet"
LABEL_TABLE_NAME = "ml_label_family_jurisdiction_lapse_risk.parquet"
SPLIT_TABLE_NAME = "ml_split_registry.parquet"
PHASE_SPLIT_TABLE_NAME = "ml_split_registry_phase04.parquet"
EXPERIMENT_REGISTRY_NAME = "ml_experiment_registry.parquet"
MODEL_REGISTRY_NAME = "ml_model_registry.parquet"
CALIBRATION_REGISTRY_NAME = "ml_calibration_registry.parquet"
FEATURE_MANIFEST_NAME = "ml_feature_manifest.parquet"
MODEL_CARD_NAME = "model_card_family_jurisdiction_lapse_risk.json"

TRAINING_HORIZONS = ("12m", "24m")
MIN_ROWS_FOR_BASELINE = {"train": 2_000, "validation": 1_000, "test": 1_000}
MAX_ROWS_FOR_BASELINE = {"train": 400_000, "validation": 120_000, "test": 120_000}
MIN_USABLE_24M_POSITIVES_PER_COHORT = 1_000
CALIBRATION_GROUPS = {
    "office": ("jurisdiction_code", 5_000),
    "primary_wipo_field": ("primary_wipo_field", 5_000),
}
BASELINE_PARAMS = {
    "objective": "binary",
    "n_estimators": 1200,
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
    "branch_state_asof",
    "has_active_grant_asof",
    "years_since_last_grant_event",
    "years_since_last_lapse_event",
    "years_since_last_expiry_event",
    "branch_stage_multiplier_asof",
    "branch_enforceability_contribution_raw_asof",
    "family_composite_status_asof",
    "active_jurisdiction_count_asof",
    "lapsed_jurisdiction_count_asof",
    "family_jurisdiction_count_asof",
    "family_coverage_stability_score_asof",
    "family_overall_legal_enforceability_score_asof",
    "family_blocking_power_score_asof",
    "family_field_contribution_primary_asof",
    "family_tech_breadth_wipo_count_asof",
    "family_size_docdb_asof",
    "family_rcf_score_asof",
    "pre_asof_forward_citations_clean",
    "pre_asof_forward_citations_weighted",
    "pre_asof_unique_citing_family_count",
    "pre_asof_citing_assignee_diversity",
    "pre_asof_attacker_density_score",
    "jurisdiction_is_ep",
    "jurisdiction_is_us",
    "jurisdiction_is_cn",
    "jurisdiction_is_jp",
    "jurisdiction_is_kr",
    "jurisdiction_is_major_office",
    "family_age_years",
]
CATEGORICAL_FEATURES = {"branch_state_asof", "family_composite_status_asof"}
BOOLEAN_FEATURES = {
    "has_active_grant_asof",
    "jurisdiction_is_ep",
    "jurisdiction_is_us",
    "jurisdiction_is_cn",
    "jurisdiction_is_jp",
    "jurisdiction_is_kr",
    "jurisdiction_is_major_office",
}


def _required_inputs(settings: BuildSettings) -> dict[str, Path]:
    return {
        "event_ledger": settings.silver_dir / "silver_legal_status_event_ledger.parquet",
        "branch_history_dense": settings.silver_dir / "silver_branch_status_history_dense.parquet",
        "family_pit_dense": settings.silver_dir / "silver_family_feature_snapshot_pit_dense.parquet",
        "family_summary": settings.gold_dir / "gold_family_summary.parquet",
    }


def _ensure_inputs(required: dict[str, Path]) -> None:
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Phase 04 required inputs missing: {missing}")


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


def _expected_count_error(y_true: np.ndarray, y_prob: np.ndarray) -> float | None:
    if len(y_true) == 0:
        return None
    return float(abs(np.asarray(y_prob, dtype=float).sum() - np.asarray(y_true, dtype=float).sum()))


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


def _subgroup_probability_summary(frame: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray, group_col: str, min_rows: int) -> dict[str, dict[str, float]]:
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


def _sample_split_frame(
    con: duckdb.DuckDBPyConnection,
    feature_table: Path,
    label_table: Path,
    split_table: Path,
    horizon: str,
    split_name: str,
    max_rows: int,
) -> tuple[pd.DataFrame, int]:
    observed_col = f"is_observed_{horizon}"
    target_col = f"lapse_risk_{horizon}_label"
    count_sql = f"""
        with split_scope as (
            select entity_id
            from read_parquet('{split_table}')
            where model_scope = '{MODEL_SCOPE}'
              and split_name = '{split_name}'
        ),
        joined as (
            select
                f.*,
                cast(l.{target_col} as integer) as target_label
            from read_parquet('{feature_table}') f
            inner join read_parquet('{label_table}') l
              on l.docdb_family_id = f.docdb_family_id
             and l.jurisdiction_code = f.jurisdiction_code
             and l.as_of_date = f.as_of_date
             and l.as_of_year = f.as_of_year
            inner join split_scope s
              on s.entity_id = cast(f.docdb_family_id as varchar) || '|' || f.jurisdiction_code
            where l.{observed_col} = true
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
            select entity_id
            from read_parquet('{split_table}')
            where model_scope = '{MODEL_SCOPE}'
              and split_name = '{split_name}'
        ),
        joined as (
            select
                f.*,
                cast(l.{target_col} as integer) as target_label
            from read_parquet('{feature_table}') f
            inner join read_parquet('{label_table}') l
              on l.docdb_family_id = f.docdb_family_id
             and l.jurisdiction_code = f.jurisdiction_code
             and l.as_of_date = f.as_of_date
             and l.as_of_year = f.as_of_year
            inner join split_scope s
              on s.entity_id = cast(f.docdb_family_id as varchar) || '|' || f.jurisdiction_code
            where l.{observed_col} = true
        )
        select * from joined{sample_clause}
        """
    ).df()
    return frame, raw_count


def _prepare_phase04_matrix(
    feature_frame: pd.DataFrame,
    branch_state_mapping: dict[str, int] | None = None,
    family_status_mapping: dict[str, int] | None = None,
) -> tuple[pd.DataFrame, dict[str, int], dict[str, int]]:
    frame = feature_frame.copy()
    frame["branch_state_asof"] = frame["branch_state_asof"].fillna("unknown").astype(str)
    frame["family_composite_status_asof"] = frame["family_composite_status_asof"].fillna("unknown").astype(str)
    if branch_state_mapping is None:
        values = sorted(frame["branch_state_asof"].unique().tolist())
        branch_state_mapping = {value: idx for idx, value in enumerate(values)}
    if family_status_mapping is None:
        values = sorted(frame["family_composite_status_asof"].unique().tolist())
        family_status_mapping = {value: idx for idx, value in enumerate(values)}
    frame["branch_state_asof_code"] = frame["branch_state_asof"].map(branch_state_mapping).fillna(-1).astype(int)
    frame["family_composite_status_asof_code"] = (
        frame["family_composite_status_asof"].map(family_status_mapping).fillna(-1).astype(int)
    )
    numeric_columns = [
        "as_of_year",
        "family_priority_year",
        "family_age_years",
        "has_active_grant_asof",
        "years_since_last_grant_event",
        "years_since_last_lapse_event",
        "years_since_last_expiry_event",
        "branch_stage_multiplier_asof",
        "branch_enforceability_contribution_raw_asof",
        "active_jurisdiction_count_asof",
        "lapsed_jurisdiction_count_asof",
        "family_jurisdiction_count_asof",
        "family_coverage_stability_score_asof",
        "family_overall_legal_enforceability_score_asof",
        "family_blocking_power_score_asof",
        "family_field_contribution_primary_asof",
        "family_tech_breadth_wipo_count_asof",
        "family_size_docdb_asof",
        "family_rcf_score_asof",
        "pre_asof_forward_citations_clean",
        "pre_asof_forward_citations_weighted",
        "pre_asof_unique_citing_family_count",
        "pre_asof_citing_assignee_diversity",
        "pre_asof_attacker_density_score",
        "jurisdiction_is_ep",
        "jurisdiction_is_us",
        "jurisdiction_is_cn",
        "jurisdiction_is_jp",
        "jurisdiction_is_kr",
        "jurisdiction_is_major_office",
        "data_completeness_pct_asof",
        "branch_state_asof_code",
        "family_composite_status_asof_code",
    ]
    x = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
    medians = x.median(numeric_only=True).fillna(0.0)
    x = x.fillna(medians)
    return x, branch_state_mapping, family_status_mapping


def _evaluate_probability_metrics(frame: pd.DataFrame, y_true: np.ndarray, y_prob: np.ndarray) -> dict[str, object]:
    metrics = {
        "roc_auc": _roc_auc(y_true, y_prob),
        "pr_auc": _average_precision(y_true, y_prob),
        "brier_score": _brier_score(y_true, y_prob),
        "log_loss": _log_loss_binary(y_true, y_prob),
        "top_decile_lift": _top_decile_lift(y_true, y_prob),
        "recall_top_risk_quintile": _recall_at_top_fraction(y_true, y_prob, 0.20),
        "expected_lapse_count_error": _expected_count_error(y_true, y_prob),
        "calibration_curve_by_decile": _calibration_curve_by_decile(y_true, y_prob),
    }
    for group_name, (group_col, min_rows) in CALIBRATION_GROUPS.items():
        metrics[f"{group_name}_subgroups"] = _subgroup_probability_summary(frame, y_true, y_prob, group_col, min_rows)
    return metrics


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
        scored.append((brier if brier is not None else float("inf"), log_loss if log_loss is not None else float("inf"), method, params, probs))
    scored.sort(key=lambda row: (row[0], row[1], row[2]))
    _, _, method, params, val_probs = scored[0]
    return method, params, val_probs, {
        candidate_method: {
            "brier_score": _brier_score(y_val, candidate_probs),
            "log_loss": _log_loss_binary(y_val, candidate_probs),
        }
        for candidate_method, _, candidate_probs in candidates
    }


def _apply_calibration(method: str, params: dict[str, object], raw_prob: np.ndarray) -> np.ndarray:
    if method == "identity":
        return np.asarray(raw_prob, dtype=float)
    if method == "platt":
        return _apply_platt_scaler(raw_prob, params)  # type: ignore[arg-type]
    if method == "isotonic":
        return _apply_isotonic_calibrator(raw_prob, params)  # type: ignore[arg-type]
    raise ValueError(f"Unsupported calibration method: {method}")


def _train_phase04_baselines(
    settings: BuildSettings,
    feature_table: Path,
    label_table: Path,
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

    branch_state_mapping: dict[str, int] | None = None
    family_status_mapping: dict[str, int] | None = None
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
                con,
                feature_table=feature_table,
                label_table=label_table,
                split_table=split_table,
                horizon=horizon,
                split_name=split_name,
                max_rows=MAX_ROWS_FOR_BASELINE[split_name],
            )
            raw_frames[split_name] = frame
            raw_counts[split_name] = raw_count

        if any(raw_counts[name] < MIN_ROWS_FOR_BASELINE[name] or len(raw_frames[name]) < MIN_ROWS_FOR_BASELINE[name] for name in MIN_ROWS_FOR_BASELINE):
            experiment_rows.append(
                {
                    "experiment_id": f"{settings.release_id}-phase04-baseline-{horizon}",
                    "model_scope": MODEL_SCOPE,
                    "horizon": horizon,
                    "algorithm_family": "lightgbm_classifier",
                    "objective": "binary",
                    "training_snapshot": f"{settings.release_id}-phase04",
                    "feature_manifest_version": settings.method_version,
                    "primary_metric": "roc_auc",
                    "primary_metric_value": None,
                    "notes": f"baseline_not_trained_insufficient_rows_{raw_counts}",
                }
            )
            model_rows.append(
                {
                    "model_scope": MODEL_SCOPE,
                    "model_version": f"{settings.release_id}-phase04-baseline-{horizon}",
                    "horizon": horizon,
                    "artifact_uri": "",
                    "feature_manifest_version": settings.method_version,
                    "calibration_version": f"{settings.release_id}-phase04-calibration-{horizon}",
                    "promotion_status": "not_trained",
                    "rollback_model_version": None,
                    "prediction_unit": "docdb_family_id|jurisdiction_code|as_of_date",
                    "training_snapshot": f"{settings.release_id}-phase04",
                }
            )
            calibration_rows.append(
                {
                    "experiment_id": f"{settings.release_id}-phase04-baseline-{horizon}",
                    "model_scope": MODEL_SCOPE,
                    "horizon": horizon,
                    "calibration_version": f"{settings.release_id}-phase04-calibration-{horizon}",
                    "calibration_method": "not_calibrated",
                    "target_coverage": None,
                    "coverage_overall": None,
                    "coverage_major_subgroups": "",
                    "status": "not_trained",
                }
            )
            model_card_payload["baseline_results"][horizon] = {"status": "insufficient_rows", "raw_counts": raw_counts}
            continue

        x_train, branch_state_mapping, family_status_mapping = _prepare_phase04_matrix(
            raw_frames["train"], branch_state_mapping, family_status_mapping
        )
        x_val, _, _ = _prepare_phase04_matrix(raw_frames["validation"], branch_state_mapping, family_status_mapping)
        x_test, _, _ = _prepare_phase04_matrix(raw_frames["test"], branch_state_mapping, family_status_mapping)
        y_train = raw_frames["train"]["target_label"].to_numpy(dtype=int)
        y_val = raw_frames["validation"]["target_label"].to_numpy(dtype=int)
        y_test = raw_frames["test"]["target_label"].to_numpy(dtype=int)

        positives = int(y_train.sum())
        negatives = int(len(y_train) - positives)
        scale_pos_weight = float(negatives / max(positives, 1))
        params = dict(BASELINE_PARAMS)
        params["scale_pos_weight"] = scale_pos_weight
        model = LGBMClassifier(**params)
        model.fit(x_train, y_train)

        raw_val_prob = model.predict_proba(x_val)[:, 1]
        raw_test_prob = model.predict_proba(x_test)[:, 1]
        calibration_method, calibration_params, calibrated_val_prob, candidate_metrics = _choose_calibration(y_val, raw_val_prob)
        calibrated_test_prob = _apply_calibration(calibration_method, calibration_params, raw_test_prob)

        validation_metrics = _evaluate_probability_metrics(raw_frames["validation"], y_val, calibrated_val_prob)
        test_metrics = _evaluate_probability_metrics(raw_frames["test"], y_test, calibrated_test_prob)

        model_path = model_registry_path.parent / f"family_jurisdiction_lapse_risk_{horizon}_model.txt"
        model.booster_.save_model(str(model_path))
        outputs.append(str(model_path))

        experiment_rows.append(
            {
                "experiment_id": f"{settings.release_id}-phase04-baseline-{horizon}",
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "algorithm_family": "lightgbm_classifier",
                "objective": "binary",
                "training_snapshot": f"{settings.release_id}-phase04",
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
                "expected_lapse_count_error": test_metrics["expected_lapse_count_error"],
            }
        )
        model_rows.append(
            {
                "model_scope": MODEL_SCOPE,
                "model_version": f"{settings.release_id}-phase04-baseline-{horizon}",
                "horizon": horizon,
                "artifact_uri": str(model_path),
                "feature_manifest_version": settings.method_version,
                "calibration_version": f"{settings.release_id}-phase04-calibration-{horizon}",
                "promotion_status": "candidate_trained",
                "rollback_model_version": None,
                "prediction_unit": "docdb_family_id|jurisdiction_code|as_of_date",
                "training_snapshot": f"{settings.release_id}-phase04",
            }
        )
        calibration_rows.append(
            {
                "experiment_id": f"{settings.release_id}-phase04-baseline-{horizon}",
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "calibration_version": f"{settings.release_id}-phase04-calibration-{horizon}",
                "calibration_method": calibration_method,
                "target_coverage": None,
                "coverage_overall": None,
                "coverage_major_subgroups": json.dumps(test_metrics["office_subgroups"], sort_keys=True),
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
            "scale_pos_weight": scale_pos_weight,
        }
        model_card_payload["baseline_results"][horizon] = calibration_payload["horizons"][horizon]
        model_card_payload["training_samples"][horizon] = {
            "raw_counts": raw_counts,
            "sampled_counts": {name: int(len(raw_frames[name])) for name in raw_frames},
        }
        trained_horizons += 1
        summary_metrics[f"{horizon}_roc_auc"] = float(test_metrics["roc_auc"]) if test_metrics["roc_auc"] is not None else float("nan")
        summary_metrics[f"{horizon}_pr_auc"] = float(test_metrics["pr_auc"]) if test_metrics["pr_auc"] is not None else float("nan")
        summary_metrics[f"{horizon}_brier_score"] = float(test_metrics["brier_score"]) if test_metrics["brier_score"] is not None else float("nan")

    calibration_json_path = calibration_registry_path.parent / "family_jurisdiction_lapse_risk_calibration.json"
    write_text_json(calibration_json_path, calibration_payload)
    outputs.append(str(calibration_json_path))

    if trained_horizons == 0:
        model_card_payload["status"] = "pending_real_training"
        model_card_payload["training_status"] = "insufficient_split_rows"
        model_card_payload["notes"] = [
            "Phase 04 label, feature, and split artifacts are built, but the sampled split rows were insufficient for baseline training.",
        ]
    else:
        model_card_payload["status"] = "baseline_trained_candidate"
        model_card_payload["training_status"] = "baseline_lightgbm_trained"
        model_card_payload["notes"] = [
            "Phase 04 baselines are trained on sampled row-level branch snapshots joined to grouped trajectory splits.",
            "Probability calibration is selected on validation between identity, Platt, and isotonic variants.",
        ]
    model_card_payload["promotion_ready"] = False
    return experiment_rows, model_rows, calibration_rows, model_card_payload, outputs, summary_metrics


def _discover_phase04_years(settings: BuildSettings, branch_history_dense: Path) -> list[int]:
    con = duckdb.connect()
    rows = con.execute(
        f"""
        select distinct cast(snapshot_year as integer) as snapshot_year
        from read_parquet('{branch_history_dense}')
        where active_branch_flag = true
          and replay_branch_state = 'ACTIVE_GRANT'
          and cast(snapshot_date as date) <= date '{settings.snapshot_date}'
          and cast(snapshot_year as integer) >= {settings.year_window_start}
        order by snapshot_year
        """
    ).fetchall()
    return [int(row[0]) for row in rows if row[0] is not None]


def _build_label_chunk(
    con: duckdb.DuckDBPyConnection,
    required: dict[str, Path],
    chunk_path: Path,
    as_of_year: int,
    settings: BuildSettings,
) -> None:
    con.execute(
        f"""
        copy (
            with branch_base as (
                select
                    b.docdb_family_id,
                    b.jurisdiction_code,
                    cast(b.snapshot_date as date) as as_of_date,
                    cast(b.snapshot_year as integer) as as_of_year
                from read_parquet('{required["branch_history_dense"]}') b
                where b.active_branch_flag = true
                  and b.replay_branch_state = 'ACTIVE_GRANT'
                  and cast(b.snapshot_date as date) <= date '{settings.snapshot_date}'
                  and cast(b.snapshot_year as integer) = {as_of_year}
            ),
            negative_events as (
                select
                    docdb_family_id,
                    jurisdiction_code,
                    cast(event_date as date) as event_date
                from read_parquet('{required["event_ledger"]}')
                where cast(event_date as date) is not null
                  and (coalesce(is_lapse_event, false) = true or coalesce(is_expiry_event, false) = true)
            ),
            joined as (
                select
                    bb.docdb_family_id,
                    bb.jurisdiction_code,
                    bb.as_of_date,
                    bb.as_of_year,
                    min(ne.event_date) as event_date_first_negative_after_asof
                from branch_base bb
                left join negative_events ne
                  on ne.docdb_family_id = bb.docdb_family_id
                 and ne.jurisdiction_code = bb.jurisdiction_code
                 and ne.event_date > bb.as_of_date
                group by 1, 2, 3, 4
            )
            select
                docdb_family_id,
                jurisdiction_code,
                as_of_date,
                as_of_year,
                case
                    when as_of_date + interval '12 months' <= date '{settings.snapshot_date}' then true
                    else false
                end as is_observed_12m,
                case
                    when as_of_date + interval '24 months' <= date '{settings.snapshot_date}' then true
                    else false
                end as is_observed_24m,
                case
                    when as_of_date + interval '12 months' <= date '{settings.snapshot_date}'
                     and event_date_first_negative_after_asof is not null
                     and event_date_first_negative_after_asof <= as_of_date + interval '12 months'
                    then 1 else 0
                end as lapse_risk_12m_label,
                case
                    when as_of_date + interval '24 months' <= date '{settings.snapshot_date}'
                     and event_date_first_negative_after_asof is not null
                     and event_date_first_negative_after_asof <= as_of_date + interval '24 months'
                    then 1 else 0
                end as lapse_risk_24m_label,
                event_date_first_negative_after_asof,
                '{settings.release_id}-phase04' as training_snapshot_id,
                '{settings.method_version}' as method_version
            from joined
        ) to '{chunk_path}' (format parquet, compression zstd)
        """
    )


def _build_feature_chunk(
    con: duckdb.DuckDBPyConnection,
    required: dict[str, Path],
    label_chunk_path: Path,
    chunk_path: Path,
    as_of_year: int,
    settings: BuildSettings,
) -> None:
    con.execute(
        f"""
        copy (
            with branch_year as (
                select
                    docdb_family_id,
                    jurisdiction_code,
                    cast(snapshot_date as date) as as_of_date,
                    cast(snapshot_year as integer) as as_of_year,
                    cast(active_branch_flag as boolean) as has_active_grant_asof,
                    replay_branch_state as branch_state_asof,
                    last_grant_event_date,
                    last_lapse_event_date,
                    last_expiry_event_date
                from read_parquet('{required["branch_history_dense"]}')
                where cast(snapshot_year as integer) = {as_of_year}
            ),
            family_pit_year as (
                select *
                from read_parquet('{required["family_pit_dense"]}')
                where as_of_year = {as_of_year}
            )
            select
                l.docdb_family_id,
                l.jurisdiction_code,
                l.as_of_date,
                l.as_of_year,
                g.family_priority_year,
                greatest(
                    0.0,
                    coalesce(date_diff('day', cast(g.family_earliest_priority_date as date), l.as_of_date), 0) / 365.25
                )::double as family_age_years,
                l.training_snapshot_id,
                l.method_version,
                b.branch_state_asof,
                cast(b.has_active_grant_asof as boolean) as has_active_grant_asof,
                case
                    when b.last_grant_event_date is null then null::double
                    else greatest(0.0, date_diff('day', cast(b.last_grant_event_date as date), l.as_of_date) / 365.25)::double
                end as years_since_last_grant_event,
                case
                    when b.last_lapse_event_date is null then null::double
                    else greatest(0.0, date_diff('day', cast(b.last_lapse_event_date as date), l.as_of_date) / 365.25)::double
                end as years_since_last_lapse_event,
                case
                    when b.last_expiry_event_date is null then null::double
                    else greatest(0.0, date_diff('day', cast(b.last_expiry_event_date as date), l.as_of_date) / 365.25)::double
                end as years_since_last_expiry_event,
                1.0::double as branch_stage_multiplier_asof,
                1.0::double as branch_enforceability_contribution_raw_asof,
                p.family_composite_status_asof,
                cast(p.active_jurisdiction_count_asof as double) as active_jurisdiction_count_asof,
                cast(p.lapsed_jurisdiction_count_asof as double) as lapsed_jurisdiction_count_asof,
                cast(p.family_jurisdiction_count_asof as double) as family_jurisdiction_count_asof,
                cast(p.family_coverage_stability_score_asof as double) as family_coverage_stability_score_asof,
                cast(p.family_enforceability_score_asof as double) as family_overall_legal_enforceability_score_asof,
                cast(p.family_blocking_power_score_asof as double) as family_blocking_power_score_asof,
                cast(p.family_field_contribution_primary_asof as double) as family_field_contribution_primary_asof,
                cast(p.family_tech_breadth_wipo_count_asof as double) as family_tech_breadth_wipo_count_asof,
                cast(p.family_size_docdb_asof as double) as family_size_docdb_asof,
                cast(p.family_rcf_score_asof as double) as family_rcf_score_asof,
                cast(p.pre_asof_forward_citations_clean as double) as pre_asof_forward_citations_clean,
                cast(p.pre_asof_forward_citations_weighted as double) as pre_asof_forward_citations_weighted,
                cast(p.pre_asof_unique_citing_family_count as double) as pre_asof_unique_citing_family_count,
                cast(p.pre_asof_citing_assignee_diversity as double) as pre_asof_citing_assignee_diversity,
                cast(p.pre_asof_attacker_density_score as double) as pre_asof_attacker_density_score,
                cast(b.jurisdiction_code = 'EP' as boolean) as jurisdiction_is_ep,
                cast(b.jurisdiction_code = 'US' as boolean) as jurisdiction_is_us,
                cast(b.jurisdiction_code = 'CN' as boolean) as jurisdiction_is_cn,
                cast(b.jurisdiction_code = 'JP' as boolean) as jurisdiction_is_jp,
                cast(b.jurisdiction_code = 'KR' as boolean) as jurisdiction_is_kr,
                cast(b.jurisdiction_code in ('EP', 'US', 'CN', 'JP', 'KR') as boolean) as jurisdiction_is_major_office,
                g.primary_wipo_field,
                cast(p.data_completeness_pct_asof as double) as data_completeness_pct_asof
            from read_parquet('{label_chunk_path}') l
            inner join branch_year b
                on b.docdb_family_id = l.docdb_family_id
               and b.jurisdiction_code = l.jurisdiction_code
               and b.as_of_date = l.as_of_date
            inner join family_pit_year p
                on p.docdb_family_id = l.docdb_family_id
               and p.as_of_year = l.as_of_year
            inner join read_parquet('{required["family_summary"]}') g
                on g.docdb_family_id = l.docdb_family_id
        ) to '{chunk_path}' (format parquet, compression zstd)
        """
    )


def build_ml_phase04_family_jurisdiction_lapse_risk(settings: BuildSettings) -> StageResult:
    required = _required_inputs(settings)
    _ensure_inputs(required)

    label_table = settings.ml_dir / LABEL_TABLE_NAME
    feature_table = settings.ml_dir / FEATURE_TABLE_NAME
    split_table = settings.ml_dir / SPLIT_TABLE_NAME
    phase_split_table = settings.ml_dir / PHASE_SPLIT_TABLE_NAME
    experiment_registry = settings.ml_dir / EXPERIMENT_REGISTRY_NAME
    model_registry = settings.ml_dir / MODEL_REGISTRY_NAME
    calibration_registry = settings.ml_dir / CALIBRATION_REGISTRY_NAME
    feature_manifest = settings.ml_dir / FEATURE_MANIFEST_NAME
    model_card = settings.ml_dir / MODEL_CARD_NAME

    snapshot_date = settings.snapshot_date

    temp_dir = ensure_dir(settings.ml_dir / "_duckdb_tmp_phase04")
    label_chunk_dir = ensure_dir(settings.ml_dir / "_tmp_phase04_label_chunks")
    feature_chunk_dir = ensure_dir(settings.ml_dir / "_tmp_phase04_feature_chunks")

    con = duckdb.connect()
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET threads=4")
    con.execute("SET memory_limit='8GB'")
    con.execute(f"SET temp_directory='{temp_dir}'")

    years = _discover_phase04_years(settings, required["branch_history_dense"])
    label_chunk_paths: list[Path] = []
    feature_chunk_paths: list[Path] = []
    for stale in label_chunk_dir.glob("phase04_label_*.parquet"):
        stale.unlink()
    for stale in feature_chunk_dir.glob("phase04_feature_*.parquet"):
        stale.unlink()

    for as_of_year in years:
        label_chunk_path = label_chunk_dir / f"phase04_label_{int(as_of_year)}.parquet"
        feature_chunk_path = feature_chunk_dir / f"phase04_feature_{int(as_of_year)}.parquet"
        _build_label_chunk(con, required, label_chunk_path, int(as_of_year), settings)
        _build_feature_chunk(con, required, label_chunk_path, feature_chunk_path, int(as_of_year), settings)
        label_chunk_paths.append(label_chunk_path)
        feature_chunk_paths.append(feature_chunk_path)

    if label_table.exists():
        label_table.unlink()
    con.execute(
        f"""
        copy (
            select * from read_parquet('{label_chunk_dir / 'phase04_label_*.parquet'}')
        ) to '{label_table}' (format parquet, compression zstd)
        """
    )

    if feature_table.exists():
        feature_table.unlink()
    con.execute(
        f"""
        copy (
            select * from read_parquet('{feature_chunk_dir / 'phase04_feature_*.parquet'}')
        ) to '{feature_table}' (format parquet, compression zstd)
        """
    )

    latest_usable_test_year_row = con.execute(
        f"""
        with trajectory_years as (
            select
                docdb_family_id,
                jurisdiction_code,
                min(as_of_year) as first_active_grant_year
            from read_parquet('{feature_table}')
            group by 1, 2
        ),
        cohort_quality as (
            select
                t.first_active_grant_year,
                count(*) filter (where l.is_observed_24m) as observed_24m_rows,
                sum(cast(l.lapse_risk_24m_label as bigint)) filter (where l.is_observed_24m) as observed_24m_positive_count
            from trajectory_years t
            inner join read_parquet('{label_table}') l
              on l.docdb_family_id = t.docdb_family_id
             and l.jurisdiction_code = t.jurisdiction_code
            group by 1
        )
        select max(first_active_grant_year) as latest_usable_test_year
        from cohort_quality
        where coalesce(observed_24m_positive_count, 0) >= {MIN_USABLE_24M_POSITIVES_PER_COHORT}
        """
    ).fetchone()
    latest_usable_test_year = (
        int(latest_usable_test_year_row[0]) if latest_usable_test_year_row and latest_usable_test_year_row[0] is not None else None
    )
    if latest_usable_test_year is None:
        fallback_row = con.execute(
            f"""
            select max(as_of_year) as latest_fully_observed_24m_year
            from read_parquet('{label_table}')
            where is_observed_24m = true
            """
        ).fetchone()
        latest_usable_test_year = int(fallback_row[0]) if fallback_row and fallback_row[0] is not None else None
    if latest_usable_test_year is None:
        raise RuntimeError("Phase 04 found no usable or fully observed 24m test cohort after feature materialization.")
    validation_anchor_year = latest_usable_test_year - 1
    train_max_year = latest_usable_test_year - 2

    con.execute(
        f"""
        copy (
            with trajectory_years as (
                select
                    f.docdb_family_id,
                    f.jurisdiction_code,
                    min(f.as_of_year) as first_active_grant_year,
                    max(f.primary_wipo_field) as primary_wipo_field
                from read_parquet('{feature_table}') f
                inner join read_parquet('{label_table}') l
                  on l.docdb_family_id = f.docdb_family_id
                 and l.jurisdiction_code = f.jurisdiction_code
                 and l.as_of_date = f.as_of_date
                group by 1, 2
            )
            select
                '{MODEL_SCOPE}' as model_scope,
                cast(docdb_family_id as varchar) || '|' || jurisdiction_code as entity_id,
                docdb_family_id as root_family_id,
                case
                    when first_active_grant_year is null or first_active_grant_year > {latest_usable_test_year} then 'unassigned_recent'
                    when first_active_grant_year <= {train_max_year} then 'train'
                    when first_active_grant_year = {validation_anchor_year} then 'validation'
                    else 'test'
                end as split_name,
                'family_jurisdiction_grouped_time_by_first_active_grant_year' as split_strategy,
                date '{snapshot_date}' as snapshot_cutoff,
                primary_wipo_field,
                first_active_grant_year as time_key_year
            from trajectory_years
        ) to '{split_table}.phase04.tmp' (format parquet, compression zstd)
        """
    )

    feature_manifest_rows = []
    categorical_features = {"branch_state_asof", "family_composite_status_asof"}
    boolean_features = {
        "has_active_grant_asof",
        "jurisdiction_is_ep",
        "jurisdiction_is_us",
        "jurisdiction_is_cn",
        "jurisdiction_is_jp",
        "jurisdiction_is_kr",
        "jurisdiction_is_major_office",
    }
    for feature_name in FEATURE_NAMES:
        if feature_name in categorical_features:
            feature_type = "categorical"
        elif feature_name in boolean_features:
            feature_type = "boolean"
        else:
            feature_type = "numeric"
        feature_manifest_rows.append(
            {
                "model_scope": MODEL_SCOPE,
                "feature_name": feature_name,
                "feature_table": FEATURE_TABLE_NAME,
                "feature_type": feature_type,
                "null_policy": "explicit_missing_allowed",
                "is_leakage_sensitive": False,
                "introduced_in_version": settings.method_version,
            }
        )

    model_card_payload = {
        "model_scope": MODEL_SCOPE,
        "prediction_unit": "docdb_family_id x jurisdiction_code x as_of_date",
        "status": "pending_real_training",
        "training_status": "label_feature_split_scaffold_ready",
        "horizons": ["12m", "24m"],
        "label_table": str(label_table),
        "feature_table": str(feature_table),
        "split_registry": str(split_table),
        "split_registry_shared": str(split_table),
        "feature_manifest": str(feature_manifest),
        "baseline_model_planned": {
            "algorithm_family": "LightGBMClassifier",
            "objective": "binary",
            "learning_rate": 0.03,
            "num_leaves": 63,
            "max_depth": 8,
            "min_data_in_leaf": 100,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "lambda_l1": 0.1,
            "lambda_l2": 0.1,
        },
        "calibration_method_planned": ["isotonic", "platt"],
        "method_version": settings.method_version,
        "promotion_ready": False,
        "notes": [
            "Phase 04 currently materializes label, feature, and split contracts from branch-history and family PIT inputs.",
            "Model training and probability calibration remain the next implementation step.",
        ],
    }

    experiment_rows = [
        {
            "experiment_id": f"{settings.release_id}-phase04-baseline-{horizon}",
            "model_scope": MODEL_SCOPE,
            "horizon": horizon,
            "algorithm_family": "lightgbm_classifier",
            "objective": "binary",
            "training_snapshot": f"{settings.release_id}-phase04",
            "feature_manifest_version": settings.method_version,
            "primary_metric": "roc_auc",
            "primary_metric_value": None,
            "notes": "planned_baseline_not_trained",
            "rmse_log1p": None,
            "mae_raw": None,
            "precision_at_1pct": None,
            "precision_at_5pct": None,
            "recall_top_decile_impact": None,
            "interval_coverage_80pct": None,
        }
        for horizon in TRAINING_HORIZONS
    ]
    model_registry_rows = [
        {
            "model_scope": MODEL_SCOPE,
            "model_version": f"{settings.release_id}-phase04-baseline-{horizon}",
            "horizon": horizon,
            "artifact_uri": "",
            "feature_manifest_version": settings.method_version,
            "calibration_version": f"{settings.release_id}-phase04-calibration-{horizon}",
            "promotion_status": "planned_scaffold_only",
            "rollback_model_version": None,
            "prediction_unit": "docdb_family_id|jurisdiction_code|as_of_date",
            "training_snapshot": f"{settings.release_id}-phase04",
        }
        for horizon in TRAINING_HORIZONS
    ]
    calibration_rows = [
        {
            "experiment_id": f"{settings.release_id}-phase04-baseline-{horizon}",
            "model_scope": MODEL_SCOPE,
            "horizon": horizon,
            "calibration_version": f"{settings.release_id}-phase04-calibration-{horizon}",
            "calibration_method": "planned_probability_calibration",
            "target_coverage": None,
            "coverage_overall": None,
            "coverage_major_subgroups": "",
            "status": "planned_not_trained",
        }
        for horizon in TRAINING_HORIZONS
    ]

    _write_scope_rows(split_table, MODEL_SCOPE, duckdb.sql(f"select * from read_parquet('{split_table}.phase04.tmp')").df().to_dict("records"))
    Path(f"{split_table}.phase04.tmp").unlink(missing_ok=True)
    con_phase_split = duckdb.connect()
    con_phase_split.execute(
        f"""
        copy (
            select * from read_parquet('{split_table}')
            where model_scope = '{MODEL_SCOPE}'
        ) to '{phase_split_table}' (format parquet, compression zstd)
        """
    )
    _write_scope_rows(feature_manifest, MODEL_SCOPE, feature_manifest_rows)
    model_card_payload["split_registry"] = str(phase_split_table)
    model_card_payload["split_registry_shared"] = str(split_table)
    write_text_json(model_card, model_card_payload)

    (
        experiment_rows,
        model_registry_rows,
        calibration_rows,
        model_card_payload,
        training_outputs,
        training_metrics,
    ) = _train_phase04_baselines(
        settings=settings,
        feature_table=feature_table,
        label_table=label_table,
        split_table=split_table,
        model_registry_path=model_registry,
        experiment_registry_path=experiment_registry,
        calibration_registry_path=calibration_registry,
        model_card_path=model_card,
    )
    _write_scope_rows(experiment_registry, MODEL_SCOPE, experiment_rows)
    _write_scope_rows(model_registry, MODEL_SCOPE, model_registry_rows)
    _write_scope_rows(calibration_registry, MODEL_SCOPE, calibration_rows)
    write_text_json(model_card, model_card_payload)

    result = StageResult(
        stage="ml-phase04-family-jurisdiction-lapse-risk",
        status="success",
        summary="Built Phase 04 branch-aware label, feature, split, and baseline-training artifacts with registry-preserving metadata.",
        methods=[
            "Derived family-jurisdiction lapse labels from dated lapse/expiry events after each yearly active-grant branch snapshot.",
            "Joined dense branch history with dense family PIT metrics to keep first-pass Phase 04 features year-safe.",
            "Assigned one grouped time split per family-jurisdiction trajectory using the latest fully observed 24m year.",
            "Trained sampled LightGBM classifier baselines and selected validation-best probability calibration per horizon.",
        ],
        calculations=[
            "12m and 24m labels are only treated as observed when the horizon closes by the ETL snapshot date.",
            "Branch-level timing features use the lag between as_of_date and last grant/lapse/expiry events.",
            "Current-state-only legal enrichments are intentionally excluded from the initial promotion feature set.",
        ],
        doc_refs=[
            "docs/next-phase-v2/45-patentiq-v2-phase-04-family-jurisdiction-lapse-risk-execution-plan.md",
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
        ],
    )
    result.outputs.extend(
        [
            str(label_table),
            str(feature_table),
            str(split_table),
            str(phase_split_table),
            str(experiment_registry),
            str(model_registry),
            str(calibration_registry),
            str(feature_manifest),
            str(model_card),
        ]
    )
    result.outputs.extend(training_outputs)
    result.metrics["ml_label_family_jurisdiction_lapse_risk_rows"] = parquet_row_count(label_table)
    result.metrics["ml_feature_family_jurisdiction_lapse_risk_rows"] = parquet_row_count(feature_table)
    result.metrics["ml_split_registry_rows"] = parquet_row_count(split_table)
    result.metrics["ml_split_registry_phase04_rows"] = parquet_row_count(phase_split_table)
    result.metrics["ml_experiment_registry_rows"] = parquet_row_count(experiment_registry)
    result.metrics["ml_model_registry_rows"] = parquet_row_count(model_registry)
    result.metrics["ml_calibration_registry_rows"] = parquet_row_count(calibration_registry)
    for metric_name, metric_value in training_metrics.items():
        result.metrics[f"phase04_{metric_name}"] = metric_value
    return result

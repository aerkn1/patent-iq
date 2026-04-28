from __future__ import annotations

import json
from math import sqrt
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, LGBMRegressor

from patentiq_etl.common.io import ensure_dir, parquet_columns, parquet_row_count, write_pylist_parquet, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult


MODEL_SCOPE = "family_future_citation_forecast"
FEATURE_TABLE_NAME = "ml_feature_family_future_citations.parquet"
LABEL_TABLE_NAME = "ml_label_family_future_citations.parquet"
SPLIT_TABLE_NAME = "ml_split_registry.parquet"
PHASE_SPLIT_TABLE_NAME = "ml_split_registry_phase03.parquet"
EXPERIMENT_REGISTRY_NAME = "ml_experiment_registry.parquet"
MODEL_REGISTRY_NAME = "ml_model_registry.parquet"
CALIBRATION_REGISTRY_NAME = "ml_calibration_registry.parquet"
FEATURE_MANIFEST_NAME = "ml_feature_manifest.parquet"
MODEL_CARD_NAME = "model_card_family_future_citation_forecast.json"

FEATURE_COLUMNS: list[tuple[str, str, list[str]]] = [
    ("family_forward_citations_clean", "double", ["family_forward_citations_clean"]),
    ("family_forward_citations_weighted_7y", "double", ["family_forward_citations_weighted_7y", "family_forward_citations_weighted"]),
    ("family_rcf_score", "double", ["family_rcf_score"]),
    ("unique_citing_family_count", "double", ["unique_citing_family_count"]),
    ("citing_assignee_diversity", "double", ["citing_assignee_diversity"]),
    ("attacker_density_score", "double", ["attacker_density_score"]),
    ("family_size_docdb", "double", ["family_size_docdb"]),
    ("active_jurisdiction_count", "double", ["active_jurisdiction_count"]),
    ("family_distinct_owner_count", "double", ["family_distinct_owner_count"]),
    ("family_composite_status", "varchar", ["family_composite_status"]),
    ("branch_enforceability_contribution_raw", "double", ["branch_enforceability_contribution_raw"]),
    ("family_overall_legal_enforceability_score", "double", ["family_overall_legal_enforceability_score"]),
    ("active_grant_branch_count", "double", ["active_grant_branch_count"]),
    ("quality_index_4_percentile", "double", ["quality_index_4_percentile", "family_quality_index_4_score"]),
    ("quality_index_6_percentile", "double", ["quality_index_6_percentile", "family_quality_index_6_score"]),
    ("generality_percentile", "double", ["generality_percentile", "family_generality_percentile"]),
    ("radicalness_percentile", "double", ["radicalness_percentile", "family_radicalness_percentile"]),
    ("science_grounding_percentile", "double", ["science_grounding_percentile", "family_science_grounding_percentile"]),
    ("family_earliest_priority_date", "date", ["family_earliest_priority_date"]),
    ("family_age_years", "double", []),
]

_COMPLETENESS_FEATURES = [
    "family_forward_citations_clean",
    "family_forward_citations_weighted_7y",
    "family_rcf_score",
    "unique_citing_family_count",
    "citing_assignee_diversity",
    "attacker_density_score",
    "family_size_docdb",
    "active_jurisdiction_count",
    "family_distinct_owner_count",
    "branch_enforceability_contribution_raw",
    "family_overall_legal_enforceability_score",
    "active_grant_branch_count",
    "quality_index_4_percentile",
    "quality_index_6_percentile",
    "generality_percentile",
    "radicalness_percentile",
    "science_grounding_percentile",
    "family_age_years",
]

_PIT_REQUIRED_FEATURES: frozenset[str] = frozenset({
    "family_forward_citations_clean",
    "family_forward_citations_weighted_7y",
    "family_rcf_score",
    "unique_citing_family_count",
    "citing_assignee_diversity",
    "attacker_density_score",
    "family_size_docdb",
    "active_jurisdiction_count",
    "active_grant_branch_count",
    "family_composite_status",
    "family_overall_legal_enforceability_score",
    "family_coverage_stability_score",
})

_STILL_LEAKY_WITH_PIT: frozenset[str] = frozenset()

BASELINE_PARAMS = {
    "objective": "regression",
    "n_estimators": 2000,
    "learning_rate": 0.03,
    "num_leaves": 63,
    "max_depth": 8,
    "min_data_in_leaf": 50,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l1": 0.1,
    "lambda_l2": 0.1,
    "n_jobs": 1,
    "verbosity": -1,
    "random_state": 42,
}

BREAKOUT_CLASSIFIER_PARAMS = {
    "objective": "binary",
    "n_estimators": 1200,
    "learning_rate": 0.03,
    "num_leaves": 31,
    "max_depth": 6,
    "min_data_in_leaf": 100,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l1": 0.1,
    "lambda_l2": 0.1,
    "n_jobs": 1,
    "verbosity": -1,
    "random_state": 42,
}

TAIL_REGRESSOR_PARAMS = {
    "objective": "regression",
    "n_estimators": 1200,
    "learning_rate": 0.03,
    "num_leaves": 31,
    "max_depth": 6,
    "min_data_in_leaf": 25,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 1,
    "lambda_l1": 0.1,
    "lambda_l2": 0.1,
    "n_jobs": 1,
    "verbosity": -1,
    "random_state": 42,
}

TRAINING_HORIZONS = ("3y", "5y")
MIN_ROWS_FOR_BASELINE = {"train": 4, "validation": 2, "test": 2}
MAX_ROWS_FOR_BASELINE = {"train": 200_000, "validation": 50_000, "test": 50_000}
TARGET_COVERAGE_BY_HORIZON = {"3y": 0.80, "5y": 0.775}
CALIBRATION_GROUP_COL_BY_HORIZON = {"3y": "primary_wipo_field", "5y": "primary_wipo_field"}
MIN_CALIBRATION_GROUP_ROWS_BY_HORIZON = {"3y": 2_000, "5y": 2_000}
BREAKOUT_QUANTILE_BY_HORIZON = {"3y": 0.95, "5y": 0.95}
MIN_BREAKOUT_ROWS = 500


def _required_inputs(settings: BuildSettings) -> dict[str, Path]:
    return {
        "citation_metrics": settings.silver_dir / "silver_family_citation_metrics.parquet",
        "enriched_network": settings.silver_dir / "silver_enriched_citation_network.parquet",
        "family_oecd": settings.silver_dir / "silver_family_oecd_quality.parquet",
        "coverage_metrics": settings.silver_dir / "silver_family_coverage_metrics.parquet",
        "family_status_pt": settings.silver_dir / "silver_family_status_pt.parquet",
        "family_wipo_fields": settings.silver_dir / "silver_family_wipo_fields.parquet",
        "family_summary": settings.gold_dir / "gold_family_summary.parquet",
    }


def _describe_columns(path: Path) -> set[str]:
    return set(parquet_columns(path))


def _select_expr(source_alias: str, available: set[str], alias: str, sql_type: str, candidates: list[str]) -> str:
    if not candidates:
        if alias == "family_age_years":
            if "family_earliest_priority_date" not in available:
                return f"null::{sql_type} as {alias}"
            return (
                "case when g.family_earliest_priority_date is not null "
                f"then date_diff('year', cast(g.family_earliest_priority_date as date), date '{_SENTINEL_DATE}')::double "
                f"else null::{sql_type} end as {alias}"
            )
        raise ValueError(f"No candidates available for derived field `{alias}`")
    for candidate in candidates:
        if candidate in available:
            if sql_type == "date":
                return f"cast({source_alias}.{candidate} as date) as {alias}"
            return f"cast({source_alias}.{candidate} as {sql_type}) as {alias}"
    return f"null::{sql_type} as {alias}"


_SENTINEL_DATE = "1970-01-01"


def _network_rollup_sql(path: Path, available: set[str]) -> str:
    source = f"read_parquet('{path}')"
    if {"cited_docdb_family_id", "source_docdb_family_id"} <= available:
        out_of_bounds_filter = (
            "coalesce(is_out_of_bounds, false) = false" if "is_out_of_bounds" in available else "true"
        )
        intra_family_filter = (
            "coalesce(is_intra_family_citation, false) = false"
            if "is_intra_family_citation" in available
            else "true"
        )
        assignee_expr = "coalesce(citing_assignee_name, '__unknown__')" if "citing_assignee_name" in available else "'__unknown__'"
        edge_weight_expr = "avg(clean_edge_weight)::double" if "clean_edge_weight" in available else "null::double"
        return f"""
            select
                cited_docdb_family_id as docdb_family_id,
                count(distinct source_docdb_family_id) as unique_citing_family_count,
                case
                    when count(distinct source_docdb_family_id) > 0
                    then count(distinct {assignee_expr})::double
                         / count(distinct source_docdb_family_id)::double
                    else null::double
                end as citing_assignee_diversity,
                {edge_weight_expr} as attacker_density_score
            from {source}
            where {out_of_bounds_filter}
              and {intra_family_filter}
            group by docdb_family_id
        """

    passthrough_fields = {
        "docdb_family_id",
        "unique_citing_family_count",
        "citing_assignee_diversity",
        "attacker_density_score",
    }
    if passthrough_fields <= available:
        return f"""
            select
                docdb_family_id,
                cast(unique_citing_family_count as double) as unique_citing_family_count,
                cast(citing_assignee_diversity as double) as citing_assignee_diversity,
                cast(attacker_density_score as double) as attacker_density_score
            from {source}
        """

    return """
        select
            null::bigint as docdb_family_id,
            null::double as unique_citing_family_count,
            null::double as citing_assignee_diversity,
            null::double as attacker_density_score
        where false
    """


def _label_build_sql(
    settings: BuildSettings,
    family_summary_path: Path,
    citation_metrics_path: Path,
    enriched_network_path: Path,
    citation_cols: set[str],
    network_cols: set[str],
) -> tuple[str, str]:
    explicit_3y = next((name for name in ("future_forward_citations_3y_raw", "y_total_3y") if name in citation_cols), None)
    explicit_5y = next((name for name in ("future_forward_citations_5y_raw", "y_total_5y") if name in citation_cols), None)
    if explicit_3y or explicit_5y:
        select_3y = (
            f"cast(c.{explicit_3y} as double) as future_forward_citations_3y_raw"
            if explicit_3y
            else "null::double as future_forward_citations_3y_raw"
        )
        select_5y = (
            f"cast(c.{explicit_5y} as double) as future_forward_citations_5y_raw"
            if explicit_5y
            else "null::double as future_forward_citations_5y_raw"
        )
        log_3y = (
            f"ln(1 + coalesce(cast(c.{explicit_3y} as double), 0.0)) as future_forward_citations_3y_log1p"
            if explicit_3y
            else "null::double as future_forward_citations_3y_log1p"
        )
        log_5y = (
            f"ln(1 + coalesce(cast(c.{explicit_5y} as double), 0.0)) as future_forward_citations_5y_log1p"
            if explicit_5y
            else "null::double as future_forward_citations_5y_log1p"
        )
        return (
            f"""
            select
                g.docdb_family_id,
                cast(g.family_earliest_priority_date as date) + interval '2 years' as as_of_date,
                extract(year from cast(g.family_earliest_priority_date as date) + interval '2 years')::integer as as_of_year,
                {select_3y},
                {select_5y},
                {log_3y},
                {log_5y},
                cast(cast(g.family_earliest_priority_date as date) + interval '5 years' as date) as label_window_3y_end_date,
                cast(cast(g.family_earliest_priority_date as date) + interval '7 years' as date) as label_window_5y_end_date,
                '{settings.release_id}-phase03' as training_snapshot_id,
                '{settings.method_version}' as method_version
            from read_parquet('{family_summary_path}') g
            left join read_parquet('{citation_metrics_path}') c using (docdb_family_id)
            where coalesce(g.is_main_window_family, true) = true
              and g.family_earliest_priority_date is not null
              and ({'c.' + explicit_3y + ' is not null' if explicit_3y else 'false'}
                   or {'c.' + explicit_5y + ' is not null' if explicit_5y else 'false'})
            """,
            "explicit_label_columns",
        )

    if {"source_docdb_family_id", "cited_docdb_family_id"} <= network_cols and (
        "citation_date" in network_cols or "citation_year" in network_cols
    ):
        citation_date_expr = (
            "cast(citation_date as date)"
            if "citation_date" in network_cols
            else "make_date(citation_year::integer, 12, 31)"
        )
        out_of_bounds_filter = (
            "coalesce(is_out_of_bounds, false) = false" if "is_out_of_bounds" in network_cols else "true"
        )
        intra_family_filter = (
            "coalesce(is_intra_family_citation, false) = false"
            if "is_intra_family_citation" in network_cols
            else "true"
        )
        self_citation_filter = (
            "coalesce(is_self_citation, false) = false" if "is_self_citation" in network_cols else "true"
        )
        return (
            f"""
            with family_anchor as (
                select
                    docdb_family_id,
                    cast(family_earliest_priority_date as date) as family_anchor_date,
                    cast(family_earliest_priority_date as date) + interval '2 years' as as_of_date
                from read_parquet('{family_summary_path}')
                where coalesce(is_main_window_family, true) = true
                  and family_earliest_priority_date is not null
            ),
            first_clean_edge as (
                select
                    cited_docdb_family_id as docdb_family_id,
                    source_docdb_family_id,
                    min({citation_date_expr}) as first_citation_date
                from read_parquet('{enriched_network_path}')
                where {out_of_bounds_filter}
                  and {intra_family_filter}
                  and {self_citation_filter}
                  and {citation_date_expr} is not null
                group by 1, 2
            )
            select
                a.docdb_family_id,
                cast(a.as_of_date as date) as as_of_date,
                extract(year from a.as_of_date)::integer as as_of_year,
                case
                    when cast(a.as_of_date + interval '3 years' as date) <= date '{settings.snapshot_date}'
                    then count(distinct case
                        when e.first_citation_date > cast(a.as_of_date as date)
                         and e.first_citation_date <= cast(a.as_of_date + interval '3 years' as date)
                        then e.source_docdb_family_id end
                    )::double
                    else null::double
                end as future_forward_citations_3y_raw,
                case
                    when cast(a.as_of_date + interval '5 years' as date) <= date '{settings.snapshot_date}'
                    then count(distinct case
                        when e.first_citation_date > cast(a.as_of_date as date)
                         and e.first_citation_date <= cast(a.as_of_date + interval '5 years' as date)
                        then e.source_docdb_family_id end
                    )::double
                    else null::double
                end as future_forward_citations_5y_raw,
                case
                    when cast(a.as_of_date + interval '3 years' as date) <= date '{settings.snapshot_date}'
                    then ln(1 + count(distinct case
                        when e.first_citation_date > cast(a.as_of_date as date)
                         and e.first_citation_date <= cast(a.as_of_date + interval '3 years' as date)
                        then e.source_docdb_family_id end
                    )::double)
                    else null::double
                end as future_forward_citations_3y_log1p,
                case
                    when cast(a.as_of_date + interval '5 years' as date) <= date '{settings.snapshot_date}'
                    then ln(1 + count(distinct case
                        when e.first_citation_date > cast(a.as_of_date as date)
                         and e.first_citation_date <= cast(a.as_of_date + interval '5 years' as date)
                        then e.source_docdb_family_id end
                    )::double)
                    else null::double
                end as future_forward_citations_5y_log1p,
                cast(a.as_of_date + interval '3 years' as date) as label_window_3y_end_date,
                cast(a.as_of_date + interval '5 years' as date) as label_window_5y_end_date,
                '{settings.release_id}-phase03' as training_snapshot_id,
                '{settings.method_version}' as method_version
            from family_anchor a
            left join first_clean_edge e using (docdb_family_id)
            group by 1, 2, 3, 8, 9, 10, 11
            having future_forward_citations_3y_raw is not null or future_forward_citations_5y_raw is not null
            """,
            "derived_from_citation_event_network",
        )

    return (
        """
        select
            null::bigint as docdb_family_id,
            null::date as as_of_date,
            null::integer as as_of_year,
            null::double as future_forward_citations_3y_raw,
            null::double as future_forward_citations_5y_raw,
            null::double as future_forward_citations_3y_log1p,
            null::double as future_forward_citations_5y_log1p,
            null::date as label_window_3y_end_date,
            null::date as label_window_5y_end_date,
            null::varchar as training_snapshot_id,
            null::varchar as method_version
        where false
        """,
        "unavailable",
    )


def _baseline_params_for_rows(train_rows: int) -> dict[str, object]:
    params = dict(BASELINE_PARAMS)
    params["min_data_in_leaf"] = max(1, min(int(params["min_data_in_leaf"]), max(1, train_rows // 4)))
    params["num_leaves"] = max(7, min(int(params["num_leaves"]), max(7, train_rows)))
    return params


def _cap_frame(frame: pd.DataFrame, split_name: str) -> pd.DataFrame:
    limit = MAX_ROWS_FOR_BASELINE.get(split_name)
    if limit is None or len(frame) <= limit:
        return frame
    return frame.sample(n=limit, random_state=42).sort_values("docdb_family_id").reset_index(drop=True)


def _allow_phase03_current_state_fallback(settings: BuildSettings) -> bool:
    return bool((settings.execution or {}).get("phase03_allow_current_state_fallback", False))


def _spearman(y_true: pd.Series, y_pred: np.ndarray) -> float | None:
    if len(y_true) < 2:
        return None
    value = y_true.corr(pd.Series(y_pred, index=y_true.index), method="spearman")
    return None if pd.isna(value) else float(value)


def _rmse(y_true: pd.Series, y_pred: np.ndarray) -> float:
    diff = np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float)
    return float(sqrt(np.mean(np.square(diff))))


def _mae(y_true: pd.Series, y_pred: np.ndarray) -> float:
    diff = np.asarray(y_true, dtype=float) - np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(diff)))


def _tail_mae(actual: pd.Series, predicted: np.ndarray, breakout_threshold: float) -> float | None:
    mask = np.asarray(actual, dtype=float) >= breakout_threshold
    if not np.any(mask):
        return None
    return _mae(actual.loc[mask], np.asarray(predicted, dtype=float)[mask])


def _forecast_metrics(
    actual_raw: pd.Series,
    actual_log: pd.Series,
    predicted_raw: np.ndarray,
    predicted_log: np.ndarray,
    breakout_threshold: float | None = None,
) -> dict[str, float | None]:
    metrics: dict[str, float | None] = {
        "spearman": _spearman(actual_raw.astype(float), predicted_raw),
        "rmse_log1p": _rmse(actual_log.astype(float), predicted_log),
        "mae_raw": _mae(actual_raw.astype(float), predicted_raw),
        "precision_at_1pct": _top_overlap_ratio(actual_raw.astype(float), predicted_raw, 0.01),
        "precision_at_5pct": _top_overlap_ratio(actual_raw.astype(float), predicted_raw, 0.05),
        "recall_top_decile_impact": _top_overlap_ratio(actual_raw.astype(float), predicted_raw, 0.10),
    }
    if breakout_threshold is not None:
        metrics["breakout_tail_mae_raw"] = _tail_mae(actual_raw.astype(float), predicted_raw, breakout_threshold)
    return metrics


def _choose_variant(
    baseline_metrics: dict[str, float | None],
    two_stage_metrics: dict[str, float | None] | None,
) -> str:
    if not two_stage_metrics:
        return "baseline"

    base_spearman = baseline_metrics.get("spearman")
    two_spearman = two_stage_metrics.get("spearman")
    base_p1 = baseline_metrics.get("precision_at_1pct")
    two_p1 = two_stage_metrics.get("precision_at_1pct")
    base_tail_mae = baseline_metrics.get("breakout_tail_mae_raw")
    two_tail_mae = two_stage_metrics.get("breakout_tail_mae_raw")

    spearman_ok = (
        base_spearman is None
        or two_spearman is None
        or two_spearman >= base_spearman - 0.03
    )
    tail_better = (
        base_tail_mae is not None
        and two_tail_mae is not None
        and two_tail_mae <= base_tail_mae * 0.9
    )
    top1_better = (
        base_p1 is not None
        and two_p1 is not None
        and two_p1 >= base_p1 + 0.05
    )
    if spearman_ok and (tail_better or top1_better):
        return "two_stage"
    return "baseline"


def _train_two_stage_candidate(
    horizon: str,
    x_train: pd.DataFrame,
    train_h: pd.DataFrame,
    target_raw: str,
    target_log: str,
) -> dict[str, object] | None:
    train_target_raw = train_h[target_raw].astype(float)
    positive_train = train_target_raw.loc[train_target_raw > 0.0]
    if positive_train.empty:
        return None
    breakout_threshold = float(
        max(1.0, np.quantile(positive_train.to_numpy(dtype=float), BREAKOUT_QUANTILE_BY_HORIZON[horizon]))
    )
    breakout_train = (train_target_raw >= breakout_threshold).astype(int)
    if int(breakout_train.sum()) < MIN_BREAKOUT_ROWS or breakout_train.nunique() < 2:
        return None

    scale_pos_weight = float(max(1.0, (len(breakout_train) - int(breakout_train.sum())) / max(1, int(breakout_train.sum()))))
    clf_params = dict(BREAKOUT_CLASSIFIER_PARAMS)
    clf_params["scale_pos_weight"] = scale_pos_weight
    classifier = LGBMClassifier(**clf_params)
    classifier.fit(x_train, breakout_train)

    tail_train = train_h.loc[breakout_train.astype(bool)].copy()
    if len(tail_train) < MIN_BREAKOUT_ROWS:
        return None
    x_tail_train = x_train.loc[tail_train.index]
    tail_regressor = LGBMRegressor(**TAIL_REGRESSOR_PARAMS)
    tail_regressor.fit(x_tail_train, tail_train[target_log].astype(float))

    return {
        "classifier": classifier,
        "tail_regressor": tail_regressor,
        "breakout_threshold_raw": breakout_threshold,
        "train_breakout_positive_rate": float(breakout_train.mean()),
    }


def _top_overlap_ratio(actual: pd.Series, predicted: np.ndarray, pct: float) -> float | None:
    n = len(actual)
    if n == 0:
        return None
    k = max(1, int(np.ceil(n * pct)))
    actual_top = set(actual.sort_values(ascending=False).head(k).index.tolist())
    pred_top = set(pd.Series(predicted, index=actual.index).sort_values(ascending=False).head(k).index.tolist())
    return float(len(actual_top & pred_top) / k)


def _conformal_qhat(residuals: np.ndarray, target_coverage: float = 0.8) -> float:
    alpha = 1.0 - target_coverage
    q = min(1.0, np.ceil((len(residuals) + 1) * (1 - alpha)) / len(residuals))
    return float(np.quantile(residuals, q, method="higher"))


def _coverage(y_true_log: pd.Series, y_pred_log: np.ndarray, qhat: float) -> float | None:
    if len(y_true_log) == 0:
        return None
    lower = np.asarray(y_pred_log) - qhat
    upper = np.asarray(y_pred_log) + qhat
    values = np.asarray(y_true_log, dtype=float)
    return float(np.mean((values >= lower) & (values <= upper)))


def _group_key(value: object) -> str:
    return "null" if pd.isna(value) else str(value)


def _fit_grouped_conformal_qhats(
    frame: pd.DataFrame,
    y_true_log: pd.Series,
    y_pred_log: np.ndarray,
    target_coverage: float,
    group_col: str | None,
    min_group_rows: int,
) -> tuple[float, dict[str, float]]:
    residuals = np.abs(np.asarray(y_true_log, dtype=float) - np.asarray(y_pred_log, dtype=float))
    global_qhat = _conformal_qhat(residuals, target_coverage=target_coverage)
    if frame.empty or not group_col or group_col not in frame.columns:
        return global_qhat, {}

    work = frame[[group_col]].copy()
    work["residual_abs_log"] = residuals
    qhat_by_group: dict[str, float] = {}
    for group_value, group in work.groupby(group_col, dropna=False):
        if len(group) < min_group_rows:
            continue
        qhat_by_group[_group_key(group_value)] = _conformal_qhat(
            group["residual_abs_log"].to_numpy(dtype=float),
            target_coverage=target_coverage,
        )
    return global_qhat, qhat_by_group


def _resolve_qhat_vector(
    frame: pd.DataFrame,
    default_qhat: float,
    group_col: str | None,
    qhat_by_group: dict[str, float] | None = None,
) -> np.ndarray:
    if frame.empty:
        return np.asarray([], dtype=float)
    if not group_col or group_col not in frame.columns or not qhat_by_group:
        return np.full(len(frame), default_qhat, dtype=float)
    keys = frame[group_col].map(_group_key)
    return keys.map(lambda key: qhat_by_group.get(key, default_qhat)).to_numpy(dtype=float)


def _coverage_with_grouped_qhats(
    frame: pd.DataFrame,
    y_true_log: pd.Series,
    y_pred_log: np.ndarray,
    default_qhat: float,
    group_col: str | None = None,
    qhat_by_group: dict[str, float] | None = None,
) -> float | None:
    if len(y_true_log) == 0:
        return None
    qhat_vector = _resolve_qhat_vector(frame, default_qhat, group_col, qhat_by_group)
    lower = np.asarray(y_pred_log) - qhat_vector
    upper = np.asarray(y_pred_log) + qhat_vector
    values = np.asarray(y_true_log, dtype=float)
    return float(np.mean((values >= lower) & (values <= upper)))


def _subgroup_coverage(frame: pd.DataFrame, y_pred_log: np.ndarray, qhat: float, group_col: str) -> dict[str, float]:
    if frame.empty or group_col not in frame.columns:
        return {}
    work = frame.copy()
    work["pred_log"] = y_pred_log
    out: dict[str, float] = {}
    for group_value, group in work.groupby(group_col, dropna=False):
        if len(group) == 0:
            continue
        key = "null" if pd.isna(group_value) else str(group_value)
        out[key] = float(
            np.mean(
                (group["target_log"].to_numpy(dtype=float) >= group["pred_log"].to_numpy(dtype=float) - qhat)
                & (group["target_log"].to_numpy(dtype=float) <= group["pred_log"].to_numpy(dtype=float) + qhat)
            )
        )
    return out


def _subgroup_coverage_with_grouped_qhats(
    frame: pd.DataFrame,
    y_pred_log: np.ndarray,
    default_qhat: float,
    group_col: str,
    qhat_by_group: dict[str, float] | None = None,
) -> dict[str, float]:
    if frame.empty or group_col not in frame.columns:
        return {}
    work = frame.copy()
    work["pred_log"] = y_pred_log
    work["qhat_abs_log"] = _resolve_qhat_vector(work, default_qhat, group_col, qhat_by_group)
    out: dict[str, float] = {}
    for group_value, group in work.groupby(group_col, dropna=False):
        if len(group) == 0:
            continue
        key = _group_key(group_value)
        out[key] = float(
            np.mean(
                (group["target_log"].to_numpy(dtype=float) >= group["pred_log"].to_numpy(dtype=float) - group["qhat_abs_log"].to_numpy(dtype=float))
                & (group["target_log"].to_numpy(dtype=float) <= group["pred_log"].to_numpy(dtype=float) + group["qhat_abs_log"].to_numpy(dtype=float))
            )
        )
    return out


def _prepare_training_matrix(feature_frame: pd.DataFrame, status_mapping: dict[str, int] | None = None) -> tuple[pd.DataFrame, dict[str, int]]:
    frame = feature_frame.copy()
    frame["family_composite_status"] = frame["family_composite_status"].fillna("unknown").astype(str)
    if status_mapping is None:
        statuses = sorted(frame["family_composite_status"].unique().tolist())
        status_mapping = {status: idx for idx, status in enumerate(statuses)}
    frame["family_composite_status_code"] = frame["family_composite_status"].map(status_mapping).fillna(-1).astype(int)

    numeric_columns = [
        "as_of_year",
        "family_priority_year",
        "family_forward_citations_clean",
        "family_forward_citations_weighted_7y",
        "family_rcf_score",
        "family_size_docdb",
        "active_jurisdiction_count",
        "family_distinct_owner_count",
        "branch_enforceability_contribution_raw",
        "family_overall_legal_enforceability_score",
        "active_grant_branch_count",
        "quality_index_4_percentile",
        "quality_index_6_percentile",
        "generality_percentile",
        "radicalness_percentile",
        "science_grounding_percentile",
        "family_age_years",
        "family_coverage_stability_score",
        "unique_citing_family_count",
        "citing_assignee_diversity",
        "attacker_density_score",
        "data_completeness_pct",
        "family_composite_status_code",
    ]
    x = frame[numeric_columns].apply(pd.to_numeric, errors="coerce")
    medians = x.median(numeric_only=True).fillna(0.0)
    x = x.fillna(medians)
    return x, status_mapping


def _train_baseline_models(
    settings: BuildSettings,
    feature_table: Path,
    label_table: Path,
    split_table: Path,
    model_registry_path: Path,
    experiment_registry_path: Path,
    calibration_registry_path: Path,
    model_card_path: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]], dict[str, object], list[str], dict[str, float]]:
    feature_df = pd.read_parquet(feature_table)
    label_df = pd.read_parquet(label_table)
    label_df = label_df[
        [
            "docdb_family_id",
            "future_forward_citations_3y_raw",
            "future_forward_citations_5y_raw",
            "future_forward_citations_3y_log1p",
            "future_forward_citations_5y_log1p",
        ]
    ].copy()
    split_df = pd.read_parquet(split_table)
    split_df = split_df.loc[split_df["model_scope"] == MODEL_SCOPE, ["entity_id", "split_name", "primary_wipo_field"]].copy()
    split_df["docdb_family_id"] = pd.to_numeric(split_df["entity_id"], errors="coerce").astype("Int64")

    merged = feature_df.merge(label_df, on="docdb_family_id", how="inner").merge(
        split_df[["docdb_family_id", "split_name"]], on="docdb_family_id", how="inner"
    )
    observed_rows_excluded = 0
    if "is_observed_as_of_snapshot" in merged.columns:
        observed_mask = merged["is_observed_as_of_snapshot"].fillna(False).astype(bool)
        observed_rows_excluded = int((~observed_mask).sum())
        merged = merged.loc[observed_mask].copy()
    merged = merged.loc[merged["split_name"].isin(["train", "validation", "test"])].copy()

    split_sizes_raw = {name: int((merged["split_name"] == name).sum()) for name in MIN_ROWS_FOR_BASELINE}
    if any(split_sizes_raw[name] < MIN_ROWS_FOR_BASELINE[name] for name in MIN_ROWS_FOR_BASELINE):
        planned_experiments = [
            {
                "experiment_id": f"{settings.release_id}-phase03-baseline-{horizon}",
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "algorithm_family": "lightgbm_regressor",
                "objective": "regression_log1p",
                "training_snapshot": f"{settings.release_id}-phase03",
                "feature_manifest_version": settings.method_version,
                "primary_metric": "spearman",
                "primary_metric_value": None,
                "notes": f"planned_baseline_not_trained_insufficient_rows_{split_sizes_raw}",
            }
            for horizon in TRAINING_HORIZONS
        ]
        planned_experiments.extend(
            {
                "experiment_id": f"{settings.release_id}-phase03-{objective}-{horizon}",
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "algorithm_family": "lightgbm_regressor",
                "objective": objective,
                "training_snapshot": f"{settings.release_id}-phase03",
                "feature_manifest_version": settings.method_version,
                "primary_metric": "spearman",
                "primary_metric_value": None,
                "notes": "planned_challenger_not_trained",
            }
            for objective in ("poisson", "tweedie")
            for horizon in TRAINING_HORIZONS
        )
        model_rows = [
            {
                "model_scope": MODEL_SCOPE,
                "model_version": f"pending_real_training_{horizon}",
                "horizon": horizon,
                "artifact_uri": None,
                "feature_manifest_version": settings.method_version,
                "calibration_version": None,
                "promotion_status": "not_trained",
                "rollback_model_version": None,
                "prediction_unit": "docdb_family_id",
                "training_snapshot": f"{settings.release_id}-phase03",
            }
            for horizon in TRAINING_HORIZONS
        ]
        calibration_rows = [
            {
                "experiment_id": f"{settings.release_id}-phase03-baseline-{horizon}",
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "calibration_version": None,
                "calibration_method": "conformal_interval_calibration",
                "target_coverage": TARGET_COVERAGE_BY_HORIZON[horizon],
                "coverage_overall": None,
                "coverage_major_subgroups": None,
                "status": "not_calibrated",
            }
            for horizon in TRAINING_HORIZONS
        ]
        model_card_payload = json.loads(model_card_path.read_text(encoding="utf-8"))
        model_card_payload["status"] = "pending_real_training"
        model_card_payload["training_status"] = "insufficient_split_rows"
        model_card_payload["split_sizes"] = split_sizes_raw
        model_card_payload["observed_snapshot_filter_applied"] = "is_observed_as_of_snapshot" in feature_df.columns
        model_card_payload["observed_snapshot_rows_excluded"] = observed_rows_excluded
        return planned_experiments, model_rows, calibration_rows, model_card_payload, [], {}

    train_df = _cap_frame(merged.loc[merged["split_name"] == "train"].copy(), "train")
    validation_df = _cap_frame(merged.loc[merged["split_name"] == "validation"].copy(), "validation")
    test_df = _cap_frame(merged.loc[merged["split_name"] == "test"].copy(), "test")
    split_sizes = {
        "train": int(len(train_df)),
        "validation": int(len(validation_df)),
        "test": int(len(test_df)),
    }

    outputs: list[str] = []
    model_rows: list[dict[str, object]] = []
    calibration_rows: list[dict[str, object]] = []
    experiment_rows: list[dict[str, object]] = []
    evaluation_summary: dict[str, float] = {}
    status_values = sorted(
        pd.concat(
            [
                train_df["family_composite_status"],
                validation_df["family_composite_status"],
                test_df["family_composite_status"],
            ],
            ignore_index=True,
        )
        .fillna("unknown")
        .astype(str)
        .unique()
        .tolist()
    )
    status_mapping = {status: idx for idx, status in enumerate(status_values)}
    calibration_payload: dict[str, object] = {
        "target_coverage_default": 0.8,
        "target_coverage_by_horizon": TARGET_COVERAGE_BY_HORIZON,
        "horizons": {},
        "status_mapping": status_mapping,
    }

    for horizon in TRAINING_HORIZONS:
        target_log = f"future_forward_citations_{horizon}_log1p"
        target_raw = f"future_forward_citations_{horizon}_raw"
        train_h = train_df.loc[train_df[target_log].notna() & train_df[target_raw].notna()].copy()
        validation_h = validation_df.loc[validation_df[target_log].notna() & validation_df[target_raw].notna()].copy()
        test_h = test_df.loc[test_df[target_log].notna() & test_df[target_raw].notna()].copy()
        split_sizes_h = {
            "train": int(len(train_h)),
            "validation": int(len(validation_h)),
            "test": int(len(test_h)),
        }
        if any(split_sizes_h[name] < MIN_ROWS_FOR_BASELINE[name] for name in MIN_ROWS_FOR_BASELINE):
            experiment_rows.append(
                {
                    "experiment_id": f"{settings.release_id}-phase03-baseline-{horizon}",
                    "model_scope": MODEL_SCOPE,
                    "horizon": horizon,
                    "algorithm_family": "lightgbm_regressor",
                    "objective": "regression_log1p",
                    "training_snapshot": f"{settings.release_id}-phase03",
                    "feature_manifest_version": settings.method_version,
                    "primary_metric": "spearman",
                    "primary_metric_value": None,
                    "notes": f"baseline_not_trained_insufficient_horizon_rows_{split_sizes_h}",
                }
            )
            model_rows.append(
                {
                    "model_scope": MODEL_SCOPE,
                    "model_version": f"pending_real_training_{horizon}",
                    "horizon": horizon,
                    "artifact_uri": None,
                    "feature_manifest_version": settings.method_version,
                    "calibration_version": None,
                    "promotion_status": "not_trained",
                    "rollback_model_version": None,
                    "prediction_unit": "docdb_family_id",
                    "training_snapshot": f"{settings.release_id}-phase03",
                }
            )
            calibration_rows.append(
                {
                    "experiment_id": f"{settings.release_id}-phase03-baseline-{horizon}",
                    "model_scope": MODEL_SCOPE,
                    "horizon": horizon,
                    "calibration_version": None,
                    "calibration_method": "conformal_interval_calibration",
                    "target_coverage": TARGET_COVERAGE_BY_HORIZON[horizon],
                    "coverage_overall": None,
                    "coverage_major_subgroups": None,
                    "status": "not_calibrated",
                }
            )
            calibration_payload["horizons"][horizon] = {
                "status": "insufficient_horizon_rows",
                "split_sizes": split_sizes_h,
            }
            continue

        x_train, _ = _prepare_training_matrix(train_h, status_mapping)
        x_val, _ = _prepare_training_matrix(validation_h, status_mapping)
        x_test, _ = _prepare_training_matrix(test_h, status_mapping)
        y_train = train_h[target_log].astype(float)
        y_val = validation_h[target_log].astype(float)
        y_test = test_h[target_log].astype(float)

        params = _baseline_params_for_rows(len(train_h))
        model = LGBMRegressor(**params)
        model.fit(x_train, y_train)

        pred_val_log = model.predict(x_val)
        pred_test_log = model.predict(x_test)
        pred_val_raw = np.expm1(pred_val_log)
        pred_test_raw = np.expm1(pred_test_log)
        baseline_validation_metrics = _forecast_metrics(
            validation_h[target_raw].astype(float),
            y_val,
            pred_val_raw,
            pred_val_log,
        )

        two_stage_models = _train_two_stage_candidate(
            horizon=horizon,
            x_train=x_train,
            train_h=train_h,
            target_raw=target_raw,
            target_log=target_log,
        )
        two_stage_validation_metrics: dict[str, float | None] | None = None
        two_stage_test_metrics: dict[str, float | None] | None = None
        breakout_threshold_raw: float | None = None
        breakout_classifier_path: Path | None = None
        breakout_tail_model_path: Path | None = None
        if two_stage_models:
            breakout_threshold_raw = float(two_stage_models["breakout_threshold_raw"])
            breakout_classifier = two_stage_models["classifier"]
            breakout_tail_regressor = two_stage_models["tail_regressor"]
            p_val = np.clip(breakout_classifier.predict_proba(x_val)[:, 1], 0.0, 1.0)
            p_test = np.clip(breakout_classifier.predict_proba(x_test)[:, 1], 0.0, 1.0)
            tail_val_log = breakout_tail_regressor.predict(x_val)
            tail_test_log = breakout_tail_regressor.predict(x_test)
            tail_val_raw = np.expm1(tail_val_log)
            tail_test_raw = np.expm1(tail_test_log)
            combined_val_raw = pred_val_raw + p_val * np.maximum(0.0, tail_val_raw - pred_val_raw)
            combined_test_raw = pred_test_raw + p_test * np.maximum(0.0, tail_test_raw - pred_test_raw)
            combined_val_log = np.log1p(np.maximum(combined_val_raw, 0.0))
            combined_test_log = np.log1p(np.maximum(combined_test_raw, 0.0))
            two_stage_validation_metrics = _forecast_metrics(
                validation_h[target_raw].astype(float),
                y_val,
                combined_val_raw,
                combined_val_log,
                breakout_threshold=breakout_threshold_raw,
            )
            two_stage_test_metrics = _forecast_metrics(
                test_h[target_raw].astype(float),
                y_test,
                combined_test_raw,
                combined_test_log,
                breakout_threshold=breakout_threshold_raw,
            )
            breakout_classifier_path = model_registry_path.parent / f"family_future_citation_forecast_{horizon}_breakout_classifier.txt"
            breakout_tail_model_path = model_registry_path.parent / f"family_future_citation_forecast_{horizon}_breakout_tail_model.txt"
            breakout_classifier.booster_.save_model(str(breakout_classifier_path))
            breakout_tail_regressor.booster_.save_model(str(breakout_tail_model_path))
            outputs.extend([str(breakout_classifier_path), str(breakout_tail_model_path)])

        selected_variant = _choose_variant(baseline_validation_metrics, two_stage_validation_metrics)
        selected_pred_val_log = pred_val_log
        selected_pred_test_log = pred_test_log
        selected_pred_val_raw = pred_val_raw
        selected_pred_test_raw = pred_test_raw
        if selected_variant == "two_stage" and two_stage_models and two_stage_validation_metrics and two_stage_test_metrics:
            selected_pred_val_raw = combined_val_raw
            selected_pred_test_raw = combined_test_raw
            selected_pred_val_log = combined_val_log
            selected_pred_test_log = combined_test_log

        target_coverage = TARGET_COVERAGE_BY_HORIZON[horizon]
        calibration_group_col = CALIBRATION_GROUP_COL_BY_HORIZON.get(horizon)
        min_group_rows = MIN_CALIBRATION_GROUP_ROWS_BY_HORIZON.get(horizon, 0)
        qhat, qhat_by_group = _fit_grouped_conformal_qhats(
            validation_h,
            y_val,
            selected_pred_val_log,
            target_coverage=target_coverage,
            group_col=calibration_group_col,
            min_group_rows=min_group_rows,
        )
        coverage = _coverage_with_grouped_qhats(
            test_h,
            y_test,
            selected_pred_test_log,
            qhat,
            group_col=calibration_group_col,
            qhat_by_group=qhat_by_group,
        )
        subgroup_cov = _subgroup_coverage_with_grouped_qhats(
            test_h.assign(target_log=y_test.to_numpy(dtype=float)),
            selected_pred_test_log,
            qhat,
            "primary_wipo_field",
            qhat_by_group=qhat_by_group if calibration_group_col == "primary_wipo_field" else None,
        )

        model_path = model_registry_path.parent / f"family_future_citation_forecast_{horizon}_model.txt"
        model.booster_.save_model(str(model_path))
        outputs.append(str(model_path))

        metrics = _forecast_metrics(
            test_h[target_raw].astype(float),
            y_test,
            selected_pred_test_raw,
            selected_pred_test_log,
            breakout_threshold=breakout_threshold_raw if selected_variant == "two_stage" else None,
        )
        metrics["interval_coverage_80pct"] = coverage
        evaluation_summary[f"{horizon}_spearman"] = metrics["spearman"] if metrics["spearman"] is not None else float("nan")
        evaluation_summary[f"{horizon}_interval_coverage_80pct"] = coverage if coverage is not None else float("nan")

        experiment_rows.append(
            {
                "experiment_id": f"{settings.release_id}-phase03-baseline-{horizon}",
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "algorithm_family": "lightgbm_regressor",
                "objective": "regression_log1p",
                "training_snapshot": f"{settings.release_id}-phase03",
                "feature_manifest_version": settings.method_version,
                "primary_metric": "spearman",
                "primary_metric_value": baseline_validation_metrics["spearman"],
                "notes": "baseline_trained",
                "rmse_log1p": baseline_validation_metrics["rmse_log1p"],
                "mae_raw": baseline_validation_metrics["mae_raw"],
                "precision_at_1pct": baseline_validation_metrics["precision_at_1pct"],
                "precision_at_5pct": baseline_validation_metrics["precision_at_5pct"],
                "recall_top_decile_impact": baseline_validation_metrics["recall_top_decile_impact"],
                "breakout_tail_mae_raw": baseline_validation_metrics.get("breakout_tail_mae_raw"),
                "interval_coverage_80pct": coverage,
            }
        )
        if two_stage_validation_metrics is not None:
            experiment_rows.append(
                {
                    "experiment_id": f"{settings.release_id}-phase03-two-stage-{horizon}",
                    "model_scope": MODEL_SCOPE,
                    "horizon": horizon,
                    "algorithm_family": "lightgbm_two_stage",
                    "objective": "breakout_classifier_plus_tail_regressor",
                    "training_snapshot": f"{settings.release_id}-phase03",
                    "feature_manifest_version": settings.method_version,
                    "primary_metric": "spearman",
                    "primary_metric_value": two_stage_validation_metrics["spearman"],
                    "notes": f"two_stage_trained_selected_{selected_variant == 'two_stage'}",
                    "rmse_log1p": two_stage_validation_metrics["rmse_log1p"],
                    "mae_raw": two_stage_validation_metrics["mae_raw"],
                    "precision_at_1pct": two_stage_validation_metrics["precision_at_1pct"],
                    "precision_at_5pct": two_stage_validation_metrics["precision_at_5pct"],
                    "recall_top_decile_impact": two_stage_validation_metrics["recall_top_decile_impact"],
                    "breakout_tail_mae_raw": two_stage_validation_metrics.get("breakout_tail_mae_raw"),
                    "interval_coverage_80pct": None,
                }
            )
        bundle_path = model_registry_path.parent / f"family_future_citation_forecast_{horizon}_bundle.json"
        write_text_json(
            bundle_path,
            {
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "selected_variant": selected_variant,
                "prediction_style": "directional_interval_first",
                "baseline_model_path": str(model_path),
                "breakout_classifier_model_path": str(breakout_classifier_path) if breakout_classifier_path else None,
                "breakout_tail_model_path": str(breakout_tail_model_path) if breakout_tail_model_path else None,
                "breakout_threshold_raw": breakout_threshold_raw,
                "combination_rule": "baseline_plus_breakout_uplift",
                "calibration_version": f"{settings.release_id}-phase03-calibration-{horizon}",
            },
        )
        outputs.append(str(bundle_path))
        model_rows.append(
            {
                "model_scope": MODEL_SCOPE,
                "model_version": f"{settings.release_id}-phase03-{selected_variant}-{horizon}",
                "horizon": horizon,
                "artifact_uri": str(bundle_path),
                "feature_manifest_version": settings.method_version,
                "calibration_version": f"{settings.release_id}-phase03-calibration-{horizon}",
                "promotion_status": "candidate_trained",
                "rollback_model_version": None,
                "prediction_unit": "docdb_family_id",
                "training_snapshot": f"{settings.release_id}-phase03",
            }
        )
        calibration_rows.append(
            {
                "experiment_id": f"{settings.release_id}-phase03-baseline-{horizon}",
                "model_scope": MODEL_SCOPE,
                "horizon": horizon,
                "calibration_version": f"{settings.release_id}-phase03-calibration-{horizon}",
                "calibration_method": (
                    "grouped_conformal_interval_calibration"
                    if qhat_by_group
                    else "conformal_interval_calibration"
                ),
                "target_coverage": target_coverage,
                "coverage_overall": coverage,
                "coverage_major_subgroups": json.dumps(subgroup_cov, sort_keys=True),
                "status": "calibrated",
            }
        )
        calibration_payload["horizons"][horizon] = {
            "qhat_abs_log": qhat,
            "qhat_abs_log_by_group": qhat_by_group,
            "calibration_group_col": calibration_group_col if qhat_by_group else None,
            "calibration_group_min_validation_rows": min_group_rows if qhat_by_group else None,
            "target_coverage": target_coverage,
            "coverage_overall": coverage,
            "coverage_by_primary_wipo_field": subgroup_cov,
            "metrics": metrics,
            "selected_variant": selected_variant,
            "interval_first_serving_recommended": True,
            "baseline_validation_metrics": baseline_validation_metrics,
            "two_stage_validation_metrics": two_stage_validation_metrics,
            "two_stage_test_metrics": two_stage_test_metrics,
            "breakout_threshold_raw": breakout_threshold_raw,
            "breakout_positive_rate_train": (
                two_stage_models["train_breakout_positive_rate"] if two_stage_models else None
            ),
            "train_rows": int(len(train_h)),
            "validation_rows": int(len(validation_h)),
            "test_rows": int(len(test_h)),
        }

    experiment_rows.extend(
        {
            "experiment_id": f"{settings.release_id}-phase03-{objective}-{horizon}",
            "model_scope": MODEL_SCOPE,
            "horizon": horizon,
            "algorithm_family": "lightgbm_regressor",
            "objective": objective,
            "training_snapshot": f"{settings.release_id}-phase03",
            "feature_manifest_version": settings.method_version,
            "primary_metric": "spearman",
            "primary_metric_value": None,
            "notes": "planned_challenger_not_trained",
        }
        for objective in ("poisson", "tweedie")
        for horizon in TRAINING_HORIZONS
    )

    calibration_json_path = calibration_registry_path.parent / "family_future_citation_forecast_calibration.json"
    write_text_json(calibration_json_path, calibration_payload)
    outputs.append(str(calibration_json_path))

    model_card_payload = json.loads(model_card_path.read_text(encoding="utf-8"))
    model_card_payload["status"] = "baseline_trained_candidate"
    model_card_payload["training_status"] = "baseline_lightgbm_trained"
    model_card_payload["split_sizes"] = split_sizes
    model_card_payload["split_sizes_raw"] = split_sizes_raw
    model_card_payload["observed_snapshot_filter_applied"] = "is_observed_as_of_snapshot" in feature_df.columns
    model_card_payload["observed_snapshot_rows_excluded"] = observed_rows_excluded
    model_card_payload["status_mapping"] = status_mapping
    model_card_payload["baseline_results"] = calibration_payload["horizons"]
    model_card_payload["selected_variant_by_horizon"] = {
        horizon: calibration_payload["horizons"].get(horizon, {}).get("selected_variant")
        for horizon in TRAINING_HORIZONS
    }
    model_card_payload["serving_recommendation"] = "interval_first_directional_outlook"
    model_card_payload["notes"] = sorted(
        set(
            list(model_card_payload.get("notes", []))
            + [
                "Phase 03 should be served as interval-first directional outlook, not exact citation count truth.",
                "Two-stage breakout challenger is trained when tail support is sufficient and selected only when it improves tail behavior without materially harming ranking.",
            ]
        )
    )
    evaluation_summary["sampled_training"] = float(any(split_sizes[name] < split_sizes_raw[name] for name in split_sizes))
    for split_name in split_sizes:
        evaluation_summary[f"{split_name}_rows_raw"] = float(split_sizes_raw[split_name])
        evaluation_summary[f"{split_name}_rows_used"] = float(split_sizes[split_name])
    return experiment_rows, model_rows, calibration_rows, model_card_payload, outputs, evaluation_summary


def build_ml_phase03_family_future_citation_forecast(settings: BuildSettings) -> StageResult:
    """Materialize Phase 03 label/feature/split scaffolding and placeholder registries."""
    result = StageResult(
        stage="ml-phase03-family-forecast",
        status="success",
        summary="Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.",
        methods=[
            "Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.",
            "Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.",
            "Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.",
        ],
        calculations=[
            "Future citation labels preserve raw and log1p targets for 3y and 5y horizons.",
            "Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.",
        ],
        doc_refs=[
            "docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md",
            "docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md",
            "docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md",
            "docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md",
        ],
    )

    required = _required_inputs(settings)
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        result.status = "failed"
        result.warnings.append(f"Missing required Phase 03 inputs: {missing}")
        return result

    ml_dir = ensure_dir(settings.ml_dir)
    label_table = ml_dir / LABEL_TABLE_NAME
    feature_table = ml_dir / FEATURE_TABLE_NAME
    split_table = ml_dir / SPLIT_TABLE_NAME
    phase_split_table = ml_dir / PHASE_SPLIT_TABLE_NAME
    experiment_registry = ml_dir / EXPERIMENT_REGISTRY_NAME
    model_registry = ml_dir / MODEL_REGISTRY_NAME
    calibration_registry = ml_dir / CALIBRATION_REGISTRY_NAME
    feature_manifest = ml_dir / FEATURE_MANIFEST_NAME
    model_card = ml_dir / MODEL_CARD_NAME
    feature_base = ml_dir / "_tmp_phase03_feature_base.parquet"

    citation_cols = _describe_columns(required["citation_metrics"])
    network_cols = _describe_columns(required["enriched_network"])
    oecd_cols = _describe_columns(required["family_oecd"])
    coverage_cols = _describe_columns(required["coverage_metrics"])
    status_cols = _describe_columns(required["family_status_pt"])
    wipo_cols = _describe_columns(required["family_wipo_fields"])
    summary_cols = _describe_columns(required["family_summary"])

    snapshot_year = int(settings.snapshot_date[:4])
    family_forecast_cutoff_year = snapshot_year - 6
    split_cutoff = f"{family_forecast_cutoff_year}-12-31"
    global _SENTINEL_DATE
    _SENTINEL_DATE = settings.snapshot_date

    con = duckdb.connect()

    label_sql, label_source = _label_build_sql(
        settings=settings,
        family_summary_path=required["family_summary"],
        citation_metrics_path=required["citation_metrics"],
        enriched_network_path=required["enriched_network"],
        citation_cols=citation_cols,
        network_cols=network_cols,
    )
    if label_source == "unavailable":
        result.warnings.append(
            "Phase 03 could not find explicit future-label columns or enough citation-event fields to derive leakage-safe labels."
        )

    con.execute(
        f"""
        copy (
            {label_sql}
        ) to '{label_table}' (format parquet, compression zstd)
        """
    )

    feature_selects = [
        "g.docdb_family_id",
        f"date '{settings.snapshot_date}' as as_of_date",
        f"{snapshot_year} as as_of_year",
        "true as is_observed_as_of_snapshot",
        "cast(g.family_priority_year as integer) as family_priority_year",
        _select_expr("w", wipo_cols, "primary_wipo_field", "varchar", ["primary_wipo_field", "wipo_field"]),
    ]
    feature_selects.extend(
        [
            _select_expr("c", citation_cols, alias, sql_type, candidates)
            for alias, sql_type, candidates in FEATURE_COLUMNS[:3]
        ]
    )
    feature_selects.extend(
        [
            _select_expr("g", summary_cols, "family_size_docdb", "double", ["family_size_docdb"]),
            _select_expr("g", summary_cols, "active_jurisdiction_count", "double", ["active_jurisdiction_count"]),
            _select_expr("g", summary_cols, "family_distinct_owner_count", "double", ["family_distinct_owner_count"]),
            _select_expr("s", status_cols, "family_composite_status", "varchar", ["family_composite_status"]),
            _select_expr("g", summary_cols, "branch_enforceability_contribution_raw", "double", ["branch_enforceability_contribution_raw"]),
            _select_expr("g", summary_cols, "family_overall_legal_enforceability_score", "double", ["family_overall_legal_enforceability_score"]),
            _select_expr("g", summary_cols, "active_grant_branch_count", "double", ["active_grant_branch_count"]),
            _select_expr("o", oecd_cols, "quality_index_4_percentile", "double", ["quality_index_4_percentile", "family_quality_index_4_score"]),
            _select_expr("o", oecd_cols, "quality_index_6_percentile", "double", ["quality_index_6_percentile", "family_quality_index_6_score"]),
            _select_expr("o", oecd_cols, "generality_percentile", "double", ["generality_percentile", "family_generality_percentile"]),
            _select_expr("o", oecd_cols, "radicalness_percentile", "double", ["radicalness_percentile", "family_radicalness_percentile"]),
            _select_expr("o", oecd_cols, "science_grounding_percentile", "double", ["science_grounding_percentile", "family_science_grounding_percentile"]),
            _select_expr("g", summary_cols, "family_earliest_priority_date", "date", ["family_earliest_priority_date"]),
            _select_expr("g", summary_cols, "family_age_years", "double", []),
            _select_expr("v", coverage_cols, "family_coverage_stability_score", "double", ["family_coverage_stability_score"]),
            "'{settings.release_id}-phase03' as training_snapshot_id".replace("{settings.release_id}", settings.release_id),
            f"'{settings.method_version}' as method_version",
        ]
    )
    feature_selects = [expr for expr in feature_selects if expr]
    network_rollup_sql = _network_rollup_sql(required["enriched_network"], network_cols)

    con.execute(
        f"""
        copy (
            with network_rollup as (
                {network_rollup_sql}
            )
            select
                {", ".join(feature_selects)},
                cast(n.unique_citing_family_count as double) as unique_citing_family_count,
                cast(n.citing_assignee_diversity as double) as citing_assignee_diversity,
                cast(n.attacker_density_score as double) as attacker_density_score
            from read_parquet('{required["family_summary"]}') g
            inner join read_parquet('{label_table}') l using (docdb_family_id)
            left join read_parquet('{required["citation_metrics"]}') c using (docdb_family_id)
            left join network_rollup n using (docdb_family_id)
            left join read_parquet('{required["family_oecd"]}') o using (docdb_family_id)
            left join read_parquet('{required["coverage_metrics"]}') v using (docdb_family_id)
            left join read_parquet('{required["family_status_pt"]}') s using (docdb_family_id)
            left join read_parquet('{required["family_wipo_fields"]}') w using (docdb_family_id)
            where coalesce(g.is_main_window_family, true) = true
        ) to '{feature_base}' (format parquet, compression zstd)
        """
    )

    completeness_sum = " + ".join(f"(case when {col} is not null then 1 else 0 end)" for col in _COMPLETENESS_FEATURES)
    completeness_den = len(_COMPLETENESS_FEATURES)

    pit_table_path = settings.silver_dir / "silver_family_feature_snapshot_pit.parquet"
    pit_applied = pit_table_path.exists()
    allow_current_state_fallback = _allow_phase03_current_state_fallback(settings)

    if label_source == "derived_from_citation_event_network" and not pit_applied and not allow_current_state_fallback:
        result.status = "failed"
        result.warnings.append(
            "Promotion-safe Phase 03 requires `silver_family_feature_snapshot_pit.parquet` whenever labels are derived from citation events. "
            "Run `silver-pit` before `ml-phase03-family-forecast`, or explicitly enable "
            "`execution.phase03_allow_current_state_fallback=true` for exploratory candidate runs only."
        )
        result.outputs.append(str(label_table))
        result.metrics["ml_label_family_future_citations_rows"] = parquet_row_count(label_table)
        return result

    if pit_applied:
        con.execute(
            f"""
            copy (
                with enriched as (
                        select
                            b.docdb_family_id,
                            coalesce(cast(pit.as_of_date as date), cast(b.as_of_date as date))                        as as_of_date,
                            coalesce(extract(year from cast(pit.as_of_date as date))::integer, b.as_of_year)          as as_of_year,
                            coalesce(cast(pit.is_observed_as_of_snapshot as boolean), cast(b.is_observed_as_of_snapshot as boolean)) as is_observed_as_of_snapshot,
                            b.family_priority_year,
                            b.primary_wipo_field,
                            coalesce(pit.pre_asof_forward_citations_clean, b.family_forward_citations_clean)            as family_forward_citations_clean,
                            coalesce(pit.pre_asof_forward_citations_weighted, b.family_forward_citations_weighted_7y)   as family_forward_citations_weighted_7y,
                            coalesce(pit.family_rcf_score_asof, b.family_rcf_score)                                     as family_rcf_score,
                            coalesce(pit.family_size_docdb_asof, b.family_size_docdb)                                   as family_size_docdb,
                            coalesce(pit.active_jurisdiction_count_asof, b.active_jurisdiction_count)                   as active_jurisdiction_count,
                            b.family_distinct_owner_count,
                            coalesce(pit.family_composite_status_asof, b.family_composite_status)                       as family_composite_status,
                            b.branch_enforceability_contribution_raw,
                            coalesce(pit.family_enforceability_score_asof, b.family_overall_legal_enforceability_score) as family_overall_legal_enforceability_score,
                            coalesce(pit.active_grant_branch_count_asof, b.active_grant_branch_count)                   as active_grant_branch_count,
                            b.quality_index_4_percentile,
                            b.quality_index_6_percentile,
                            b.generality_percentile,
                            b.radicalness_percentile,
                            b.science_grounding_percentile,
                            b.family_earliest_priority_date,
                            b.family_age_years,
                            coalesce(pit.family_coverage_stability_score_asof, b.family_coverage_stability_score)        as family_coverage_stability_score,
                            b.training_snapshot_id,
                            b.method_version,
                            coalesce(pit.pre_asof_unique_citing_family_count, b.unique_citing_family_count)             as unique_citing_family_count,
                            coalesce(pit.pre_asof_citing_assignee_diversity, b.citing_assignee_diversity)               as citing_assignee_diversity,
                            coalesce(pit.pre_asof_attacker_density_score, b.attacker_density_score)                     as attacker_density_score
                        from read_parquet('{feature_base}') b
                        left join read_parquet('{pit_table_path}') pit using (docdb_family_id)
                )
                select
                    *,
                    round(({completeness_sum})::double / {completeness_den}, 6) as data_completeness_pct
                from enriched
            ) to '{feature_table}' (format parquet, compression zstd)
            """
        )
        result.methods.append(
                "Applied point-in-time feature enrichment from `silver_family_feature_snapshot_pit`; "
                "replaced leakage-sensitive citation counts, network externalities, and legal-state "
                "columns with pre-as_of_date equivalents; replaced family_rcf_score, family_size_docdb, "
                "and family_coverage_stability_score with PIT-safe variants; recomputed data_completeness_pct from enriched values."
        )
    else:
        con.execute(
            f"""
            copy (
                select
                    *,
                    round(({completeness_sum})::double / {completeness_den}, 6) as data_completeness_pct
                from read_parquet('{feature_base}')
            ) to '{feature_table}' (format parquet, compression zstd)
            """
        )
        if label_source == "derived_from_citation_event_network":
            result.warnings.append(
                "Point-in-time feature table `silver_family_feature_snapshot_pit` not found; "
                "run `silver-pit` stage before `ml-phase03-family-forecast` to remove temporal leakage "
                "from citation counts, network externalities, legal-state features, and PIT-derived structure metrics."
            )
        if allow_current_state_fallback:
            result.warnings.append(
                "Phase 03 is running in exploratory fallback mode with current-state feature substitutions; "
                "this run is not promotion-safe."
            )

    con.execute(
        f"""
        copy (
            with family_base as (
                select
                    docdb_family_id,
                    family_priority_year,
                    coalesce(w.primary_wipo_field, g.primary_wipo_field) as primary_wipo_field
                from read_parquet('{required["family_summary"]}') g
                inner join read_parquet('{label_table}') l using (docdb_family_id)
                left join read_parquet('{required["family_wipo_fields"]}') w using (docdb_family_id)
                where coalesce(g.is_main_window_family, true) = true
            )
            select
                '{MODEL_SCOPE}' as model_scope,
                cast(docdb_family_id as varchar) as entity_id,
                docdb_family_id as root_family_id,
                case
                    when family_priority_year <= {family_forecast_cutoff_year - 4} then 'train'
                    when family_priority_year between {family_forecast_cutoff_year - 3} and {family_forecast_cutoff_year - 2} then 'validation'
                    when family_priority_year between {family_forecast_cutoff_year - 1} and {family_forecast_cutoff_year} then 'test'
                    else 'unassigned_recent'
                end as split_name,
                'family_grouped_time_by_priority_year' as split_strategy,
                date '{split_cutoff}' as snapshot_cutoff,
                primary_wipo_field,
                family_priority_year as time_key_year
            from family_base
        ) to '{split_table}' (format parquet, compression zstd)
        """
    )

    feature_manifest_rows = []
    for alias, sql_type, _ in FEATURE_COLUMNS:
        if alias == "family_earliest_priority_date":
            feature_type = "date"
        elif alias == "family_composite_status":
            feature_type = "categorical"
        else:
            feature_type = "numeric"
        feature_manifest_rows.append(
            {
                "model_scope": MODEL_SCOPE,
                "feature_name": alias,
                "feature_table": FEATURE_TABLE_NAME,
                "feature_type": feature_type,
                "null_policy": "explicit_missing_allowed",
            "is_leakage_sensitive": (
                alias in _STILL_LEAKY_WITH_PIT
                if pit_applied
                else alias in _PIT_REQUIRED_FEATURES
            ),
                "introduced_in_version": settings.method_version,
            }
        )
    feature_manifest_rows.append(
        {
            "model_scope": MODEL_SCOPE,
            "feature_name": "is_observed_as_of_snapshot",
            "feature_table": FEATURE_TABLE_NAME,
            "feature_type": "boolean",
            "null_policy": "derived_non_null",
            "is_leakage_sensitive": False,
            "introduced_in_version": settings.method_version,
        },
    )
    feature_manifest_rows.append(
        {
            "model_scope": MODEL_SCOPE,
            "feature_name": "data_completeness_pct",
            "feature_table": FEATURE_TABLE_NAME,
            "feature_type": "numeric",
            "null_policy": "derived_non_null",
            "is_leakage_sensitive": False,
            "introduced_in_version": settings.method_version,
        }
    )
    write_pylist_parquet(feature_manifest_rows, feature_manifest)

    write_text_json(
        model_card,
        {
            "model_scope": MODEL_SCOPE,
            "prediction_unit": "docdb_family_id",
            "status": "pending_real_training",
            "label_source": label_source,
            "horizons": ["3y", "5y"],
            "feature_table": str(feature_table),
            "label_table": str(label_table),
            "split_registry": str(phase_split_table),
            "split_registry_shared": str(split_table),
            "feature_manifest": str(feature_manifest),
            "calibration_method_planned": "conformal_interval_calibration",
            "baseline_model_planned": {
                "algorithm_family": "LightGBMRegressor",
                "objective": "regression_log1p",
                "learning_rate": 0.03,
                "num_leaves": 63,
                "max_depth": 8,
                "min_data_in_leaf": 50,
                "feature_fraction": 0.8,
                "bagging_fraction": 0.8,
                "lambda_l1": 0.1,
                "lambda_l2": 0.1,
            },
            "method_version": settings.method_version,
            "pit_features_applied": pit_applied,
            "observed_snapshot_filter_applied": pit_applied,
        },
    )

    experiment_rows, model_registry_rows, calibration_rows, model_card_payload, training_outputs, training_metrics = _train_baseline_models(
        settings=settings,
        feature_table=feature_table,
        label_table=label_table,
        split_table=split_table,
        model_registry_path=model_registry,
        experiment_registry_path=experiment_registry,
        calibration_registry_path=calibration_registry,
        model_card_path=model_card,
    )
    write_pylist_parquet(experiment_rows, experiment_registry)
    write_pylist_parquet(model_registry_rows, model_registry)
    write_pylist_parquet(calibration_rows, calibration_registry)
    con = duckdb.connect()
    con.execute(
        f"""
        copy (
            select * from read_parquet('{split_table}')
            where model_scope = '{MODEL_SCOPE}'
        ) to '{phase_split_table}' (format parquet, compression zstd)
        """
    )
    model_card_payload["split_registry"] = str(phase_split_table)
    model_card_payload["split_registry_shared"] = str(split_table)
    write_text_json(model_card, model_card_payload)

    if feature_base.exists():
        feature_base.unlink()

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
    result.metrics["ml_label_family_future_citations_rows"] = parquet_row_count(label_table)
    result.metrics["ml_feature_family_future_citations_rows"] = parquet_row_count(feature_table)
    result.metrics["ml_split_registry_rows"] = parquet_row_count(split_table)
    result.metrics["ml_split_registry_phase03_rows"] = parquet_row_count(phase_split_table)
    result.metrics["ml_experiment_registry_rows"] = parquet_row_count(experiment_registry)
    result.metrics["ml_model_registry_rows"] = parquet_row_count(model_registry)
    result.metrics["ml_calibration_registry_rows"] = parquet_row_count(calibration_registry)
    for metric_name, metric_value in training_metrics.items():
        result.metrics[f"phase03_{metric_name}"] = metric_value
    return result

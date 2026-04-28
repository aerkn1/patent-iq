from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

from patentiq_etl.common.io import ensure_dir, parquet_row_count
from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.silver.build_pit import (
    CLASSIFICATION_DENSE_OUTPUT_TABLE,
    DENSE_OUTPUT_TABLE,
    OUTPUT_TABLE,
)


GOLD_SECTIONS = {
    "family_summary",
    "blocking",
    "blocking_ts",
    "field_ts",
    "field_legacy",
    "attacker",
    "family_citation",
    "family_citation_ts",
    "portfolio_field_ts",
    "portfolio",
    "portfolio_threat",
    "portfolio_citation_summary",
    "portfolio_citation_family_leaderboard",
    "portfolio_citation_ts",
    "portfolio_citation_attacker",
    "portfolio_citation_field",
    "portfolio_citation_jurisdiction",
    "portfolio_filing_timeseries",
    "market_segments",
    "market_timeseries",
    "market_overview",
    "market_citation_trend",
    "market_citation_jurisdiction",
    "market_citation_attacker",
    "semantic",
    "family_heritage",
    "portfolio_heritage",
    "portfolio_forecast",
}

PORTFOLIO_CLASSIFICATION_BUCKET_COUNT = 32
CLASSIFICATION_JURISDICTION_BUCKET_COUNT = 16
PORTFOLIO_CLASSIFICATION_JURISDICTION_BUCKET_COUNT = 8
BLOCKING_MARKET_WEIGHT = 0.65
BLOCKING_CITATION_WEIGHT = 0.35
BLOCKING_PENDING_STAGE_GATE = 0.15
BLOCKING_BREADTH_STEP = 0.05
BLOCKING_BREADTH_MAX_BONUS = 0.15


def _blocking_stage_gate_expr(*, has_active_col: str, status_col: str) -> str:
    return (
        "case "
        f"when coalesce({has_active_col}, false) then 1.0 "
        f"when coalesce({status_col}, '') = 'pending_emerging' then {BLOCKING_PENDING_STAGE_GATE} "
        "else 0.0 "
        "end"
    )


def _blocking_breadth_multiplier_expr(breadth_col: str) -> str:
    return (
        "least("
        f"1.0 + {BLOCKING_BREADTH_MAX_BONUS}, "
        "1.0 + "
        f"(greatest(coalesce(cast({breadth_col} as double), 1.0) - 1.0, 0.0) * {BLOCKING_BREADTH_STEP})"
        ")"
    )


def _blocking_citation_component_expr(citation_raw_col: str) -> str:
    return f"ln(1.0 + greatest(coalesce(cast({citation_raw_col} as double), 0.0), 0.0))"


def _blocking_raw_score_expr(
    *,
    market_col: str,
    citation_raw_col: str,
    has_active_col: str,
    status_col: str,
    breadth_col: str,
) -> str:
    stage_gate = _blocking_stage_gate_expr(has_active_col=has_active_col, status_col=status_col)
    breadth_multiplier = _blocking_breadth_multiplier_expr(breadth_col)
    citation_component = _blocking_citation_component_expr(citation_raw_col)
    return (
        f"({stage_gate}) * (("
        f"greatest(coalesce(cast({market_col} as double), 0.0), 0.0) * {BLOCKING_MARKET_WEIGHT}"
        f") + ({citation_component} * {BLOCKING_CITATION_WEIGHT})) * ({breadth_multiplier})"
    )


def _connect_duckdb_with_temp(settings: BuildSettings) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp" / f"pid_{os.getpid()}")
    con.execute(f"set temp_directory='{temp_dir}'")
    return con


def _model_artifact_paths(settings: BuildSettings) -> dict[str, Path]:
    return {
        "phase03_feature": settings.ml_dir / "ml_feature_family_future_citations.parquet",
        "phase03_bundle_3y": settings.ml_dir / "family_future_citation_forecast_3y_bundle.json",
        "phase03_bundle_5y": settings.ml_dir / "family_future_citation_forecast_5y_bundle.json",
        "phase03_calibration": settings.ml_dir / "family_future_citation_forecast_calibration.json",
        "phase03_model_card": settings.ml_dir / "model_card_family_future_citation_forecast.json",
        "phase04_feature": settings.ml_dir / "ml_feature_family_jurisdiction_lapse_risk.parquet",
        "phase04_calibration": settings.ml_dir / "family_jurisdiction_lapse_risk_calibration.json",
        "phase04_model_12m": settings.ml_dir / "family_jurisdiction_lapse_risk_12m_model.txt",
        "phase04_model_24m": settings.ml_dir / "family_jurisdiction_lapse_risk_24m_model.txt",
        "phase04_release_decision": settings.ml_dir / "family_jurisdiction_lapse_risk_release_decision.json",
        "phase06_prediction": settings.ml_dir / "ml_prediction_jurisdiction_field_trend_forecast.parquet",
        "portfolio_rollup": settings.ml_dir / "ml_portfolio_prediction_rollup.parquet",
        "phase03_prediction": settings.ml_dir / "ml_prediction_family_future_citations.parquet",
        "phase04_prediction": settings.ml_dir / "ml_prediction_family_jurisdiction_lapse_risk.parquet",
    }


def _portfolio_prediction_coverage_status(phase03_cov: pd.Series, phase04_cov: pd.Series) -> pd.Series:
    weakest = pd.concat([phase03_cov.fillna(0.0), phase04_cov.fillna(0.0)], axis=1).min(axis=1)
    return weakest.map(
        lambda value: "high"
        if value >= 0.75
        else ("medium" if value >= 0.50 else "low")
    )


def _coverage_caveat_text(status: str, phase03_cov: float | None, phase04_cov: float | None, phase06_supported: bool) -> str:
    if status == "high" and phase06_supported:
        return "Portfolio-derived prediction coverage is broadly sufficient for MVP interpretation."
    if status == "medium":
        return (
            "Portfolio-derived prediction coverage is partial; interpret aggregates as covered-subset evidence rather than full-portfolio truth."
        )
    if not phase06_supported:
        return (
            "Portfolio-derived prediction coverage is partial and current field-mix support for market overlays is limited outside the current supported slice."
        )
    return (
        "Portfolio-derived prediction coverage is low; use the aggregate as directional evidence only and rely on contributor drill-down before comparison."
    )


def _phase04_support_level_map(release_decision_path: Path) -> dict[str, str]:
    payload = json.loads(release_decision_path.read_text(encoding="utf-8"))
    office_policy = payload.get("office_support_policy", {})
    support_map: dict[str, str] = {}
    for level in ("strong", "moderate", "limited"):
        for office in office_policy.get(level, []):
            support_map[str(office)] = level
    return support_map


def _sql_support_level_case(column_sql: str, support_map: dict[str, str]) -> str:
    clauses: list[str] = []
    for office, level in sorted(support_map.items()):
        safe_office = str(office).replace("'", "''")
        safe_level = str(level).replace("'", "''")
        clauses.append(f"when {column_sql} = '{safe_office}' then '{safe_level}'")
    if not clauses:
        return "cast('limited' as varchar)"
    return f"case {' '.join(clauses)} else 'limited' end"


def _ensure_phase03_prediction_table(settings: BuildSettings, paths: dict[str, Path]) -> Path:
    from lightgbm import Booster

    from patentiq_etl.ml.phase03 import _prepare_training_matrix as _prepare_phase03_matrix
    from patentiq_etl.ml.phase03 import _resolve_qhat_vector

    out_path = paths["phase03_prediction"]
    if out_path.exists():
        out_path.unlink()
    tmp_dir = ensure_dir(settings.ml_dir / "_tmp_phase08_phase03_predictions")

    calibration_payload = json.loads(paths["phase03_calibration"].read_text(encoding="utf-8"))
    model_card_payload = json.loads(paths["phase03_model_card"].read_text(encoding="utf-8"))
    status_mapping = {
        str(key): int(value)
        for key, value in (model_card_payload.get("status_mapping") or {}).items()
    }
    feature_path = paths["phase03_feature"]
    con = duckdb.connect()
    years = [
        int(row[0])
        for row in con.execute(
            f"select distinct as_of_year from read_parquet('{feature_path}') order by as_of_year"
        ).fetchall()
    ]
    chunk_paths: list[str] = []
    for horizon in ("3y", "5y"):
        bundle = json.loads(paths[f"phase03_bundle_{horizon}"].read_text(encoding="utf-8"))
        model = Booster(model_file=str(Path(bundle["baseline_model_path"])))
        calibration = calibration_payload["horizons"][horizon]
        default_qhat = float(calibration["qhat_abs_log"])
        qhat_by_group = calibration.get("qhat_abs_log_by_group") or {}
        group_col = calibration.get("calibration_group_col")

        for year in years:
            frame = con.execute(
                f"""
                select
                    docdb_family_id,
                    as_of_date,
                    as_of_year,
                    primary_wipo_field,
                    data_completeness_pct,
                    family_composite_status,
                    family_priority_year,
                    family_forward_citations_clean,
                    family_forward_citations_weighted_7y,
                    family_rcf_score,
                    family_size_docdb,
                    active_jurisdiction_count,
                    family_distinct_owner_count,
                    branch_enforceability_contribution_raw,
                    family_overall_legal_enforceability_score,
                    active_grant_branch_count,
                    quality_index_4_percentile,
                    quality_index_6_percentile,
                    generality_percentile,
                    radicalness_percentile,
                    science_grounding_percentile,
                    family_age_years,
                    family_coverage_stability_score,
                    unique_citing_family_count,
                    citing_assignee_diversity,
                    attacker_density_score
                from read_parquet('{feature_path}')
                where as_of_year = {year}
                """
            ).df()
            if frame.empty:
                continue
            x, _ = _prepare_phase03_matrix(frame, status_mapping)
            pred_log = model.predict(x)
            pred_raw = np.maximum(0.0, np.expm1(pred_log))
            qhat_vector = _resolve_qhat_vector(frame, default_qhat, group_col, qhat_by_group)
            lower_raw = np.maximum(0.0, np.expm1(pred_log - qhat_vector))
            upper_raw = np.maximum(0.0, np.expm1(pred_log + qhat_vector))
            out = frame[["docdb_family_id", "as_of_date", "as_of_year", "primary_wipo_field", "data_completeness_pct"]].copy()
            out["model_scope"] = "family_future_citation_forecast"
            out["horizon"] = horizon
            out["prediction_style"] = "directional_interval_first"
            out["point_forecast"] = pred_raw
            out["interval_lower"] = lower_raw
            out["interval_upper"] = upper_raw
            out["selected_variant"] = bundle.get("selected_variant")
            chunk_path = tmp_dir / f"phase03_{horizon}_{year}.parquet"
            out.to_parquet(chunk_path, index=False)
            chunk_paths.append(str(chunk_path))

    if not chunk_paths:
        raise FileNotFoundError("Phase 03 prediction chunks were not generated.")
    con.execute(
        f"""
        copy (
            select * from read_parquet([{", ".join(repr(path) for path in chunk_paths)}])
        ) to '{out_path}' (format parquet, compression zstd)
        """
    )
    return out_path


def _ensure_phase04_prediction_table(settings: BuildSettings, paths: dict[str, Path]) -> Path:
    from lightgbm import Booster

    from patentiq_etl.ml.phase04 import _apply_calibration, _prepare_phase04_matrix

    out_path = paths["phase04_prediction"]
    if out_path.exists():
        out_path.unlink()
    tmp_dir = ensure_dir(settings.ml_dir / "_tmp_phase08_phase04_predictions")
    latest_feature_path = settings.ml_dir / "_tmp_phase08_phase04_latest_features.parquet"
    if latest_feature_path.exists():
        latest_feature_path.unlink()

    feature_path = paths["phase04_feature"]
    con = duckdb.connect()
    con.execute(
        f"""
        copy (
            with ranked as (
                select
                    *,
                    row_number() over (
                        partition by docdb_family_id, jurisdiction_code
                        order by as_of_year desc, as_of_date desc
                    ) as rn
                from read_parquet('{feature_path}')
            )
            select * exclude (rn) from ranked where rn = 1
        ) to '{latest_feature_path}' (format parquet, compression zstd)
        """
    )

    branch_values = [
        str(row[0])
        for row in con.execute(
            f"select distinct coalesce(branch_state_asof, 'unknown') from read_parquet('{latest_feature_path}') order by 1"
        ).fetchall()
    ]
    family_values = [
        str(row[0])
        for row in con.execute(
            f"select distinct coalesce(family_composite_status_asof, 'unknown') from read_parquet('{latest_feature_path}') order by 1"
        ).fetchall()
    ]
    branch_mapping = {value: idx for idx, value in enumerate(branch_values)}
    family_mapping = {value: idx for idx, value in enumerate(family_values)}

    calibration_payload = json.loads(paths["phase04_calibration"].read_text(encoding="utf-8"))
    support_map = _phase04_support_level_map(paths["phase04_release_decision"])
    years = [
        int(row[0])
        for row in con.execute(
            f"select distinct as_of_year from read_parquet('{latest_feature_path}') order by as_of_year"
        ).fetchall()
    ]
    chunk_paths: list[str] = []
    for horizon in ("12m", "24m"):
        model = Booster(model_file=str(paths[f"phase04_model_{horizon}"]))
        calibration = calibration_payload["horizons"][horizon]
        calibration_method = str(calibration["method"])
        calibration_params = calibration["params"]
        for year in years:
            frame = con.execute(
                f"""
                select
                    docdb_family_id,
                    jurisdiction_code,
                    as_of_date,
                    as_of_year,
                    primary_wipo_field,
                    data_completeness_pct_asof,
                    branch_state_asof,
                    family_composite_status_asof,
                    has_active_grant_asof,
                    family_priority_year,
                    family_age_years,
                    years_since_last_grant_event,
                    years_since_last_lapse_event,
                    years_since_last_expiry_event,
                    branch_stage_multiplier_asof,
                    branch_enforceability_contribution_raw_asof,
                    active_jurisdiction_count_asof,
                    lapsed_jurisdiction_count_asof,
                    family_jurisdiction_count_asof,
                    family_coverage_stability_score_asof,
                    family_overall_legal_enforceability_score_asof,
                    family_blocking_power_score_asof,
                    family_field_contribution_primary_asof,
                    family_tech_breadth_wipo_count_asof,
                    family_size_docdb_asof,
                    family_rcf_score_asof,
                    pre_asof_forward_citations_clean,
                    pre_asof_forward_citations_weighted,
                    pre_asof_unique_citing_family_count,
                    pre_asof_citing_assignee_diversity,
                    pre_asof_attacker_density_score,
                    jurisdiction_is_ep,
                    jurisdiction_is_us,
                    jurisdiction_is_cn,
                    jurisdiction_is_jp,
                    jurisdiction_is_kr,
                    jurisdiction_is_major_office
                from read_parquet('{latest_feature_path}')
                where as_of_year = {year}
                """
            ).df()
            if frame.empty:
                continue
            x, _, _ = _prepare_phase04_matrix(frame, branch_mapping, family_mapping)
            raw_prob = np.clip(model.predict(x), 0.0, 1.0)
            cal_prob = np.clip(_apply_calibration(calibration_method, calibration_params, raw_prob), 0.0, 1.0)
            out = frame[
                [
                    "docdb_family_id",
                    "jurisdiction_code",
                    "as_of_date",
                    "as_of_year",
                    "primary_wipo_field",
                    "data_completeness_pct_asof",
                ]
            ].copy()
            out["model_scope"] = "family_jurisdiction_lapse_risk"
            out["horizon"] = horizon
            out["risk_score_raw"] = raw_prob
            out["risk_probability_calibrated"] = cal_prob
            out["office_support_level"] = out["jurisdiction_code"].map(lambda code: support_map.get(str(code), "limited"))
            chunk_path = tmp_dir / f"phase04_{horizon}_{year}.parquet"
            out.to_parquet(chunk_path, index=False)
            chunk_paths.append(str(chunk_path))

    if not chunk_paths:
        raise FileNotFoundError("Phase 04 prediction chunks were not generated.")
    con.execute(
        f"""
        copy (
            select * from read_parquet([{", ".join(repr(path) for path in chunk_paths)}])
        ) to '{out_path}' (format parquet, compression zstd)
        """
    )
    return out_path


def _build_portfolio_forecast_from_models(
    settings: BuildSettings,
    *,
    out_portfolio: Path,
    out_portfolio_field_ts: Path,
    out_portfolio_compare_pit: Path,
    out_portfolio_forecast: Path,
    out_portfolio_forecast_segments: Path,
    out_portfolio_forecast_contributors: Path,
    result: StageResult,
) -> list[Path]:
    paths = _model_artifact_paths(settings)
    required = [
        paths["phase03_feature"],
        paths["phase03_bundle_3y"],
        paths["phase03_bundle_5y"],
        paths["phase03_calibration"],
        paths["phase03_model_card"],
        paths["phase04_feature"],
        paths["phase04_calibration"],
        paths["phase04_model_12m"],
        paths["phase04_model_24m"],
        paths["phase04_release_decision"],
        paths["phase06_prediction"],
        out_portfolio,
        out_portfolio_field_ts,
        out_portfolio_compare_pit,
        settings.silver_dir / "silver_family_owner_bridge.parquet",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        result.warnings.append(
            "Portfolio forecast stayed on legacy proxy logic because required sealed model artifacts are missing."
        )
        return []

    phase03_prediction = _ensure_phase03_prediction_table(settings, paths)
    phase04_prediction = _ensure_phase04_prediction_table(settings, paths)

    rollup_path = paths["portfolio_rollup"]
    for path in (rollup_path, out_portfolio_forecast, out_portfolio_forecast_segments, out_portfolio_forecast_contributors):
        if path.exists():
            path.unlink()

    con = duckdb.connect()
    owner_bridge = settings.silver_dir / "silver_family_owner_bridge.parquet"
    latest_phase06_year = con.execute(
        f"select max(as_of_year) from read_parquet('{paths['phase06_prediction']}')"
    ).fetchone()[0]

    con.execute(
        f"""
        copy (
            with owner_denominator as (
                select
                    owner_name_harmonized,
                    max(owner_name_display) as owner_name_display,
                    count(distinct docdb_family_id) as family_denominator_count
                from read_parquet('{owner_bridge}')
                where coalesce(is_primary_owner, false) = true
                group by owner_name_harmonized
            ),
            phase03_rollup as (
                select
                    ob.owner_name_harmonized,
                    p.horizon,
                    count(distinct p.docdb_family_id) as covered_count,
                    sum(p.point_forecast) as expected_total,
                    sum(p.interval_lower) as expected_lower,
                    sum(p.interval_upper) as expected_upper,
                    avg(p.data_completeness_pct) as avg_data_completeness_pct,
                    coalesce(max(p.point_forecast) / nullif(sum(p.point_forecast), 0), 0.0) as top_contributor_dependence_pct
                from read_parquet('{owner_bridge}') ob
                join read_parquet('{phase03_prediction}') p using (docdb_family_id)
                where coalesce(ob.is_primary_owner, false) = true
                group by ob.owner_name_harmonized, p.horizon
            ),
            phase04_rollup as (
                select
                    ob.owner_name_harmonized,
                    p.horizon,
                    count(distinct p.docdb_family_id) as covered_family_count,
                    count(*) as covered_branch_count,
                    sum(p.risk_probability_calibrated) as expected_lapses_count,
                    avg(case when p.office_support_level = 'limited' then 1.0 else 0.0 end) as limited_support_share,
                    avg(p.data_completeness_pct_asof) as avg_data_completeness_pct,
                    avg(branch_counts.branch_count) as avg_scored_jurisdictions_per_covered_family
                from read_parquet('{owner_bridge}') ob
                join read_parquet('{phase04_prediction}') p using (docdb_family_id)
                left join (
                    select docdb_family_id, count(*) as branch_count
                    from read_parquet('{phase04_prediction}')
                    group by docdb_family_id
                ) branch_counts using (docdb_family_id)
                where coalesce(ob.is_primary_owner, false) = true
                group by ob.owner_name_harmonized, p.horizon
            ),
            phase06_field_rollup as (
                with latest as (
                    select *
                    from read_parquet('{paths["phase06_prediction"]}')
                    where as_of_year = {int(latest_phase06_year)}
                ),
                field_weights as (
                    select
                        horizon,
                        wipo_industry_code as wipo_field,
                        sum(case when predicted_direction_band = 'heating' then local_family_filings_asof else 0 end) as heating_weight,
                        sum(case when predicted_direction_band = 'cooling' then local_family_filings_asof else 0 end) as cooling_weight,
                        sum(case when predicted_direction_band = 'stable' then local_family_filings_asof else 0 end) as stable_weight,
                        max(support_level) as support_level,
                        avg(predicted_growth_rate_reference) as predicted_growth_rate_reference,
                        avg(predicted_count_reference) as predicted_count_reference
                    from latest
                    group by horizon, wipo_industry_code
                )
                select
                    horizon,
                    wipo_field,
                    support_level,
                    predicted_growth_rate_reference,
                    predicted_count_reference,
                    case
                        when heating_weight >= cooling_weight and heating_weight >= stable_weight then 'heating'
                        when cooling_weight >= heating_weight and cooling_weight >= stable_weight then 'cooling'
                        else 'stable'
                    end as predicted_direction_band
                from field_weights
            ),
            phase06_owner_rollup as (
                select
                    pf.owner_name_harmonized,
                    fr.horizon,
                    sum(case when fr.predicted_direction_band = 'heating' then pf.active_family_count else 0 end) as heating_exposure_count,
                    sum(case when fr.predicted_direction_band = 'cooling' then pf.active_family_count else 0 end) as cooling_exposure_count,
                    sum(pf.active_family_count) as total_field_active_family_count,
                    avg(case when fr.predicted_direction_band = 'heating' then fr.predicted_growth_rate_reference else null end) as heating_growth_reference,
                    avg(case when fr.predicted_direction_band = 'cooling' then fr.predicted_growth_rate_reference else null end) as cooling_growth_reference
                from read_parquet('{out_portfolio_field_ts}') pf
                left join phase06_field_rollup fr
                  on fr.wipo_field = pf.wipo_field
                group by pf.owner_name_harmonized, fr.horizon
            ),
            phase06_support as (
                select
                    owner_name_harmonized,
                    max(cast(historical_field_mix_supported as integer)) = 1 as phase06_current_field_mix_supported
                from read_parquet('{out_portfolio_compare_pit}')
                where as_of_year = {int(settings.snapshot_date[:4])}
                group by owner_name_harmonized
            )
            select
                p.owner_name_harmonized,
                p.owner_name_display,
                p.snapshot_date,
                'family_bottom_up' as aggregation_scope,
                coalesce(p03_3.covered_count, 0) as phase03_family_covered_count,
                od.family_denominator_count as phase03_family_denominator_count,
                coalesce(p03_3.covered_count * 1.0 / nullif(od.family_denominator_count, 0), 0.0) as phase03_family_coverage_pct,
                coalesce(p04_12.covered_family_count, 0) as phase04_family_covered_count,
                od.family_denominator_count as phase04_family_denominator_count,
                coalesce(p04_12.covered_family_count * 1.0 / nullif(od.family_denominator_count, 0), 0.0) as phase04_family_coverage_pct,
                coalesce(p04_12.avg_scored_jurisdictions_per_covered_family, 0.0) as phase04_avg_scored_jurisdictions_per_covered_family,
                coalesce(p06.phase06_current_field_mix_supported, false) as phase06_current_field_mix_supported,
                case
                    when coalesce(p06.phase06_current_field_mix_supported, false)
                    then 'current portfolio field mix is supported for current-year market-direction overlays'
                    else 'current portfolio field mix support is limited for current-year market-direction overlays'
                end as phase06_current_field_mix_support_reason,
                p03_3.expected_total as portfolio_expected_future_citations_total_3y,
                p03_3.expected_lower as portfolio_expected_future_citations_lower_3y,
                p03_3.expected_upper as portfolio_expected_future_citations_upper_3y,
                p03_5.expected_total as portfolio_expected_future_citations_total_5y,
                p03_5.expected_lower as portfolio_expected_future_citations_lower_5y,
                p03_5.expected_upper as portfolio_expected_future_citations_upper_5y,
                p03_3.expected_total / nullif(p03_3.covered_count, 0) as portfolio_expected_future_citations_per_effective_family_3y,
                p03_5.expected_total / nullif(p03_5.covered_count, 0) as portfolio_expected_future_citations_per_effective_family_5y,
                p03_3.top_contributor_dependence_pct as portfolio_top_contributor_dependence_pct_3y,
                p03_5.top_contributor_dependence_pct as portfolio_top_contributor_dependence_pct_5y,
                coalesce(p03_3.avg_data_completeness_pct, 0.0) as portfolio_phase03_feature_completeness_pct_3y,
                coalesce(p03_5.avg_data_completeness_pct, 0.0) as portfolio_phase03_feature_completeness_pct_5y,
                p04_12.expected_lapses_count as portfolio_expected_lapses_count_12m,
                p04_24.expected_lapses_count as portfolio_expected_lapses_count_24m,
                p04_12.limited_support_share as portfolio_limited_support_share_12m,
                p04_24.limited_support_share as portfolio_limited_support_share_24m,
                coalesce(p04_12.avg_data_completeness_pct, 0.0) as portfolio_phase04_feature_completeness_pct_12m,
                coalesce(p04_24.avg_data_completeness_pct, 0.0) as portfolio_phase04_feature_completeness_pct_24m,
                coalesce(p06r3.heating_exposure_count, 0) as portfolio_heating_market_exposure_count_3y,
                coalesce(p06r3.cooling_exposure_count, 0) as portfolio_cooling_market_exposure_count_3y,
                coalesce(p06r3.heating_exposure_count * 1.0 / nullif(p06r3.total_field_active_family_count, 0), 0.0) as portfolio_hotspot_coverage_pct_3y,
                coalesce(p06r5.heating_exposure_count, 0) as portfolio_heating_market_exposure_count_5y,
                coalesce(p06r5.cooling_exposure_count, 0) as portfolio_cooling_market_exposure_count_5y,
                coalesce(p06r5.heating_exposure_count * 1.0 / nullif(p06r5.total_field_active_family_count, 0), 0.0) as portfolio_hotspot_coverage_pct_5y
            from read_parquet('{out_portfolio}') p
            left join owner_denominator od using (owner_name_harmonized)
            left join phase03_rollup p03_3 on p03_3.owner_name_harmonized = p.owner_name_harmonized and p03_3.horizon = '3y'
            left join phase03_rollup p03_5 on p03_5.owner_name_harmonized = p.owner_name_harmonized and p03_5.horizon = '5y'
            left join phase04_rollup p04_12 on p04_12.owner_name_harmonized = p.owner_name_harmonized and p04_12.horizon = '12m'
            left join phase04_rollup p04_24 on p04_24.owner_name_harmonized = p.owner_name_harmonized and p04_24.horizon = '24m'
            left join phase06_owner_rollup p06r3 on p06r3.owner_name_harmonized = p.owner_name_harmonized and p06r3.horizon = '3y'
            left join phase06_owner_rollup p06r5 on p06r5.owner_name_harmonized = p.owner_name_harmonized and p06r5.horizon = '5y'
            left join phase06_support p06 using (owner_name_harmonized)
        ) to '{rollup_path}' (format parquet, compression zstd)
        """
    )

    rollup_df = pd.read_parquet(rollup_path)
    rollup_df["portfolio_prediction_coverage_status"] = _portfolio_prediction_coverage_status(
        rollup_df["phase03_family_coverage_pct"],
        rollup_df["phase04_family_coverage_pct"],
    )
    rollup_df["coverage_caveat_text"] = [
        _coverage_caveat_text(
            status,
            None if pd.isna(p03_cov) else float(p03_cov),
            None if pd.isna(p04_cov) else float(p04_cov),
            bool(phase06_supported),
        )
        for status, p03_cov, p04_cov, phase06_supported in zip(
            rollup_df["portfolio_prediction_coverage_status"],
            rollup_df["phase03_family_coverage_pct"],
            rollup_df["phase04_family_coverage_pct"],
            rollup_df["phase06_current_field_mix_supported"],
        )
    ]
    rollup_df.to_parquet(rollup_path, index=False)

    rollup_con = duckdb.connect()
    rollup_con.execute(
        f"""
        copy (
            select * from read_parquet('{rollup_path}')
        ) to '{out_portfolio_forecast}' (format parquet, compression zstd)
        """
    )
    rollup_con.execute(
        f"""
        copy (
            with phase06_field_rollup as (
                with latest as (
                    select *
                    from read_parquet('{paths["phase06_prediction"]}')
                    where as_of_year = {int(latest_phase06_year)}
                ),
                field_weights as (
                    select
                        horizon,
                        wipo_industry_code as wipo_field,
                        sum(case when predicted_direction_band = 'heating' then local_family_filings_asof else 0 end) as heating_weight,
                        sum(case when predicted_direction_band = 'cooling' then local_family_filings_asof else 0 end) as cooling_weight,
                        sum(case when predicted_direction_band = 'stable' then local_family_filings_asof else 0 end) as stable_weight,
                        max(support_level) as support_level,
                        avg(predicted_growth_rate_reference) as predicted_growth_rate_reference,
                        avg(predicted_count_reference) as predicted_count_reference
                    from latest
                    group by horizon, wipo_industry_code
                )
                select
                    horizon,
                    wipo_field,
                    support_level,
                    predicted_growth_rate_reference,
                    predicted_count_reference,
                    case
                        when heating_weight >= cooling_weight and heating_weight >= stable_weight then 'heating'
                        when cooling_weight >= heating_weight and cooling_weight >= stable_weight then 'cooling'
                        else 'stable'
                    end as predicted_direction_band
                from field_weights
            )
            select
                pf.owner_name_harmonized,
                pf.snapshot_date,
                fr.horizon,
                pf.wipo_field,
                pf.active_family_count as portfolio_active_family_count_in_field,
                fr.predicted_direction_band,
                fr.support_level,
                fr.predicted_growth_rate_reference,
                fr.predicted_count_reference
            from read_parquet('{out_portfolio_field_ts}') pf
            left join phase06_field_rollup fr
              on fr.wipo_field = pf.wipo_field
        ) to '{out_portfolio_forecast_segments}' (format parquet, compression zstd)
        """
    )
    rollup_con.execute(
        f"""
        copy (
            with phase03_ranked as (
                select
                    ob.owner_name_harmonized,
                    p.horizon,
                    'phase03_future_citations' as contributor_scope,
                    cast(p.docdb_family_id as varchar) as contributor_entity_id,
                    null::varchar as jurisdiction_code,
                    p.point_forecast as contribution_value,
                    p.point_forecast / nullif(sum(p.point_forecast) over (partition by ob.owner_name_harmonized, p.horizon), 0) as contribution_share,
                    row_number() over (
                        partition by ob.owner_name_harmonized, p.horizon
                        order by p.point_forecast desc, p.docdb_family_id
                    ) as contributor_rank
                from read_parquet('{owner_bridge}') ob
                join read_parquet('{phase03_prediction}') p using (docdb_family_id)
                where coalesce(ob.is_primary_owner, false) = true
            ),
            phase04_ranked as (
                select
                    ob.owner_name_harmonized,
                    p.horizon,
                    'phase04_lapse_risk' as contributor_scope,
                    cast(p.docdb_family_id as varchar) as contributor_entity_id,
                    p.jurisdiction_code,
                    p.risk_probability_calibrated as contribution_value,
                    p.risk_probability_calibrated / nullif(sum(p.risk_probability_calibrated) over (partition by ob.owner_name_harmonized, p.horizon), 0) as contribution_share,
                    row_number() over (
                        partition by ob.owner_name_harmonized, p.horizon
                        order by p.risk_probability_calibrated desc, p.docdb_family_id, p.jurisdiction_code
                    ) as contributor_rank
                from read_parquet('{owner_bridge}') ob
                join read_parquet('{phase04_prediction}') p using (docdb_family_id)
                where coalesce(ob.is_primary_owner, false) = true
            )
            select * from phase03_ranked where contributor_rank <= 10
            union all
            select * from phase04_ranked where contributor_rank <= 10
        ) to '{out_portfolio_forecast_contributors}' (format parquet, compression zstd)
        """
    )

    return [rollup_path, out_portfolio_forecast, out_portfolio_forecast_segments, out_portfolio_forecast_contributors]


def _build_gold_selected(
    settings: BuildSettings,
    *,
    stage_name: str,
    summary: str,
    selected_sections: set[str],
) -> StageResult:
    """Build selected Gold marts from the note-aligned Silver contracts."""
    result = StageResult(
        stage=stage_name,
        status="success",
        summary=summary,
        methods=[
            "Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.",
            "Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.",
            "Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.",
        ],
        calculations=[
            "Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.",
            "Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.",
            "Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.",
        ],
        downstream_impacts=[
            "These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.",
            "Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.",
        ],
        doc_refs=[
            "docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md",
            "docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md",
            "docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md",
        ],
    )
    built_outputs: list[Path] = []

    ensure_dir(settings.gold_dir)
    con = duckdb.connect()
    con.execute("set preserve_insertion_order=false")
    con.execute("set threads=6")
    duckdb_temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp" / f"pid_{os.getpid()}")
    con.execute(f"set temp_directory='{duckdb_temp_dir}'")

    family_core = settings.silver_dir / "silver_family_core.parquet"
    owner_primary = settings.silver_dir / "silver_assignee_harmonized.parquet"
    owner_bridge = settings.silver_dir / "silver_family_owner_bridge.parquet"
    fields = settings.silver_dir / "silver_family_wipo_fields.parquet"
    coverage = settings.silver_dir / "silver_family_coverage_metrics.parquet"
    cite = settings.silver_dir / "silver_family_citation_metrics.parquet"
    cite_network = settings.silver_dir / "silver_enriched_citation_network.parquet"
    enforce = settings.silver_dir / "silver_family_enforceability_branches.parquet"
    field_contrib = settings.silver_dir / "silver_family_field_contributions.parquet"
    family_status = settings.silver_dir / "silver_family_status_pt.parquet"
    family_status_history = settings.silver_dir / "silver_family_status_history.parquet"
    branch_history_dense = settings.silver_dir / "silver_branch_status_history_dense.parquet"
    scope_appln_seed = settings.silver_dir / "silver_scope_appln_seed.parquet"
    market_weight = settings.silver_dir / "silver_tiered_market_weighting.parquet"
    local_trend = settings.silver_dir / "silver_local_tech_trends_timeseries.parquet"
    global_trend = settings.silver_dir / "silver_global_tech_trends_timeseries.parquet"
    oecd = settings.silver_dir / "silver_family_oecd_quality.parquet"
    market_seg = settings.silver_dir / "silver_market_intelligence_segments.parquet"
    market_ts = settings.silver_dir / "silver_market_intelligence_timeseries.parquet"
    semantic_rep = settings.silver_dir / "silver_family_text_representative.parquet"
    semantic_elig = settings.silver_dir / "silver_semantic_sampling_eligibility.parquet"
    family_pit_dense = settings.silver_dir / DENSE_OUTPUT_TABLE
    family_pit = family_pit_dense if family_pit_dense.exists() else settings.silver_dir / OUTPUT_TABLE

    out_family_summary = settings.gold_dir / "gold_family_summary.parquet"
    out_blocking = settings.gold_dir / "gold_family_blocking_power.parquet"
    out_blocking_ts = settings.gold_dir / "gold_family_blocking_power_timeseries.parquet"
    out_field_ts = settings.gold_dir / "gold_family_field_contributions_timeseries.parquet"
    out_field_legacy = settings.gold_dir / "gold_family_field_contributions.parquet"
    out_family_citation_summary = settings.gold_dir / "gold_family_citation_summary.parquet"
    out_family_citation_timeseries = settings.gold_dir / "gold_family_citation_timeseries_pit.parquet"
    out_portfolio = settings.gold_dir / "gold_portfolio_summary.parquet"
    out_portfolio_field_ts = settings.gold_dir / "gold_portfolio_field_timeseries.parquet"
    out_portfolio_threat = settings.gold_dir / "gold_portfolio_threat_matrix.parquet"
    out_portfolio_citation_summary = settings.gold_dir / "gold_portfolio_citation_summary.parquet"
    out_portfolio_citation_family_leaderboard = (
        settings.gold_dir / "gold_portfolio_citation_family_leaderboard.parquet"
    )
    out_portfolio_citation_timeseries = settings.gold_dir / "gold_portfolio_citation_timeseries.parquet"
    out_portfolio_citation_attacker = settings.gold_dir / "gold_portfolio_attacker_momentum.parquet"
    out_portfolio_citation_field = settings.gold_dir / "gold_portfolio_citation_pressure_by_field.parquet"
    out_portfolio_citation_jurisdiction = settings.gold_dir / "gold_portfolio_citation_pressure_by_jurisdiction.parquet"
    out_portfolio_filing_timeseries = settings.gold_dir / "gold_portfolio_filing_timeseries.parquet"
    out_market_overview = settings.gold_dir / "gold_market_intelligence_overview.parquet"
    out_market_segments = settings.gold_dir / "gold_market_intelligence_segments.parquet"
    out_market_timeseries = settings.gold_dir / "gold_market_intelligence_timeseries.parquet"
    out_market_citation_trend = settings.gold_dir / "gold_market_citation_trend_pit.parquet"
    out_market_citation_jurisdiction = settings.gold_dir / "gold_market_citation_pressure_by_jurisdiction_pit.parquet"
    out_market_citation_attacker = settings.gold_dir / "gold_market_attacker_leaderboard_pit.parquet"
    out_semantic = settings.gold_dir / "gold_semantic_match_context.parquet"
    out_attacker = settings.gold_dir / "gold_family_attacker_summary.parquet"
    out_portfolio_forecast = settings.gold_dir / "gold_portfolio_forecast_summary.parquet"
    out_portfolio_forecast_segments = settings.gold_dir / "gold_portfolio_forecast_segments.parquet"
    out_portfolio_forecast_contributors = settings.gold_dir / "gold_portfolio_forecast_contributors.parquet"
    out_family_heritage = settings.gold_dir / "gold_family_heritage_summary.parquet"
    out_portfolio_heritage = settings.gold_dir / "gold_portfolio_heritage_summary.parquet"

    snapshot_date = settings.snapshot_date
    snapshot_year = int(settings.snapshot_date[:4])
    history_start_year = settings.heritage_backfill_start
    family_summary_bucket_count = 32
    top_n_crown_jewels = 10
    family_summary_bucket_env = os.getenv("PATENTIQ_GOLD_FAMILY_SUMMARY_BUCKETS", "").strip()
    family_summary_merge_only = os.getenv("PATENTIQ_GOLD_FAMILY_SUMMARY_MERGE_ONLY", "").strip() == "1"
    if family_summary_bucket_env:
        family_summary_buckets = sorted(
            {
                int(token.strip())
                for token in family_summary_bucket_env.split(",")
                if token.strip()
            }
        )
    else:
        family_summary_buckets = list(range(family_summary_bucket_count))
    invalid_family_summary_buckets = [
        bucket
        for bucket in family_summary_buckets
        if bucket < 0 or bucket >= family_summary_bucket_count
    ]
    if invalid_family_summary_buckets:
        raise ValueError(
            f"Invalid family summary bucket ids {invalid_family_summary_buckets}; expected values in 0..{family_summary_bucket_count - 1}."
        )
    history_years = [
        int(row[0])
        for row in con.execute(
            f"""
            select distinct snapshot_year
            from read_parquet('{family_status_history}')
            order by snapshot_year
            """
        ).fetchall()
    ]

    main_families_sql = f"""
        select *
        from read_parquet('{family_core}')
        where coalesce(is_main_window_family, true)
          and not coalesce(is_out_of_bounds_ghost, false)
    """
    owner_identity_sql = f"""
        with ranked_owner_display as (
            select
                owner_name_harmonized,
                owner_name_display,
                count(*) as family_rows,
                row_number() over (
                    partition by owner_name_harmonized
                    order by count(*) desc, owner_name_display asc
                ) as display_rank
            from read_parquet('{owner_bridge}')
            group by owner_name_harmonized, owner_name_display
        )
        select
            owner_name_harmonized,
            owner_name_display
        from ranked_owner_display
        where display_rank = 1
    """
    primary_owner_bridge_sql = f"""
        select distinct
            docdb_family_id,
            owner_name_harmonized
        from read_parquet('{owner_bridge}')
        where coalesce(is_primary_owner, false)
    """
    owner_bridge_scope_sql = f"""
        select distinct
            docdb_family_id,
            owner_name_harmonized
        from read_parquet('{owner_bridge}')
    """
    current_enforce_rollup_sql = f"""
        select
            docdb_family_id,
            sum(branch_enforceability_contribution_raw) as family_market_threat_score_raw,
            sum(branch_enforceability_contribution_raw) as family_overall_legal_enforceability_score
        from read_parquet('{enforce}')
        group by docdb_family_id
    """

    con.execute(f"create or replace temp table gold_main_families as {main_families_sql}")
    if "family_summary" in selected_sections:
        family_summary_tmp_dir = ensure_dir(settings.gold_dir / "_tmp_gold_family_summary")
        if not family_summary_bucket_env and not family_summary_merge_only:
            for tmp in family_summary_tmp_dir.glob("family_summary_*.parquet"):
                tmp.unlink()
        else:
            for bucket in family_summary_buckets:
                part_path = family_summary_tmp_dir / f"family_summary_bucket_{bucket:02d}.parquet"
                if part_path.exists():
                    part_path.unlink()

        if not family_summary_merge_only:
            con.execute(
                f"""
                create or replace temp table gold_owner_primary_summary as
                select
                    o.owner_name_harmonized,
                    o.owner_name_display,
                    o.owner_country,
                    o.owner_scope_appln_count,
                    o.family_distinct_owner_count,
                    o.docdb_family_id
                from read_parquet('{owner_primary}') o
                """
            )
            con.execute(
                f"""
                create or replace temp table gold_fields_summary as
                select
                    f.covered_wipo_fields,
                    f.primary_wipo_field,
                    f.family_tech_breadth_wipo_count,
                    f.docdb_family_id
                from read_parquet('{fields}') f
                """
            )
            con.execute(
                f"""
                create or replace temp table gold_family_status_summary as
                select
                    s.family_composite_status,
                    s.active_jurisdiction_count,
                    s.active_grant_branch_count,
                    s.lapsed_jurisdiction_count,
                    s.opposed_branch_count,
                    s.has_any_active_grant,
                    s.docdb_family_id
                from read_parquet('{family_status}') s
                """
            )
            con.execute(
                f"""
                create or replace temp table gold_coverage_summary as
                select
                    cv.family_market_coverage_weight_raw,
                    cv.family_coverage_stability_score,
                    cv.docdb_family_id
                from read_parquet('{coverage}') cv
                """
            )
            con.execute(
                f"""
                create or replace temp table gold_oecd_summary as
                select
                    q.family_generality_percentile,
                    q.family_originality_percentile,
                    q.family_radicalness_percentile,
                    q.family_fwd_cits5_percentile,
                    q.family_fwd_cits7_percentile,
                    q.family_size_percentile,
                    q.family_grant_lag_speed_percentile,
                    q.family_quality_index_4_score,
                    q.family_quality_index_4_policy,
                    q.family_quality_index_6_score,
                    q.family_quality_index_6_policy,
                    q.oecd_quality_percentile,
                    q.oecd_quality_proxy_score,
                    q.docdb_family_id
                from read_parquet('{oecd}') q
                """
            )
            con.execute(
                f"""
                create or replace temp table gold_semantic_elig_summary as
                select
                    sem.is_semantic_candidate,
                    sem.is_in_vector_sample,
                    sem.docdb_family_id
                from read_parquet('{semantic_elig}') sem
                """
            )
            for bucket in family_summary_buckets:
                part_path = family_summary_tmp_dir / f"family_summary_bucket_{bucket:02d}.parquet"
                con.execute(
                    f"""
                    copy (
                        select
                            c.docdb_family_id,
                            c.family_earliest_priority_date,
                            c.family_priority_year,
                            c.family_size_docdb,
                            c.is_main_window_family,
                            c.is_heritage_backfill_family,
                            o.owner_name_harmonized,
                            o.owner_name_display,
                            o.owner_country,
                            o.owner_scope_appln_count,
                            o.family_distinct_owner_count,
                            f.covered_wipo_fields,
                            f.primary_wipo_field,
                            f.family_tech_breadth_wipo_count,
                            s.family_composite_status,
                            s.active_jurisdiction_count,
                            s.active_grant_branch_count,
                            s.lapsed_jurisdiction_count,
                            s.opposed_branch_count,
                            s.has_any_active_grant,
                            cv.family_market_coverage_weight_raw,
                            cv.family_coverage_stability_score,
                            q.family_generality_percentile,
                            q.family_originality_percentile,
                            q.family_radicalness_percentile,
                            q.family_fwd_cits5_percentile,
                            q.family_fwd_cits7_percentile,
                            q.family_size_percentile,
                            q.family_grant_lag_speed_percentile,
                            q.family_quality_index_4_score,
                            q.family_quality_index_4_policy,
                            q.family_quality_index_6_score,
                            q.family_quality_index_6_policy,
                            q.oecd_quality_percentile,
                            q.oecd_quality_proxy_score,
                            sem.is_semantic_candidate,
                            sem.is_in_vector_sample,
                            '{settings.scope_type}' as scope_type,
                            date '{snapshot_date}' as snapshot_date
                        from gold_main_families c
                        left join gold_owner_primary_summary o using (docdb_family_id)
                        left join gold_fields_summary f using (docdb_family_id)
                        left join gold_family_status_summary s using (docdb_family_id)
                        left join gold_coverage_summary cv using (docdb_family_id)
                        left join gold_oecd_summary q using (docdb_family_id)
                        left join gold_semantic_elig_summary sem using (docdb_family_id)
                        where c.docdb_family_id % {family_summary_bucket_count} = {bucket}
                    ) to '{part_path}' (format parquet, compression uncompressed)
                    """
                )

        available_family_summary_parts = sorted(family_summary_tmp_dir.glob("family_summary_bucket_*.parquet"))
        if len(available_family_summary_parts) == family_summary_bucket_count:
            if out_family_summary.exists():
                if out_family_summary.is_dir():
                    shutil.rmtree(out_family_summary)
                else:
                    out_family_summary.unlink()
            family_summary_tmp_dir.rename(out_family_summary)
            built_outputs.append(out_family_summary)
        elif family_summary_bucket_env or family_summary_merge_only:
            result.warnings.append(
                f"Built partial family summary buckets ({len(available_family_summary_parts)}/{family_summary_bucket_count}); final gold_family_summary merge not written yet."
            )
        else:
            raise RuntimeError(
                f"Expected {family_summary_bucket_count} family summary buckets, found {len(available_family_summary_parts)}."
            )

    if "blocking" in selected_sections:
        current_blocking_raw_score_sql = _blocking_raw_score_expr(
            market_col="family_market_threat_score_raw",
            citation_raw_col="family_blocking_citation_score_raw",
            has_active_col="has_any_active_grant",
            status_col="family_composite_status",
            breadth_col="family_tech_breadth_wipo_count",
        )
        con.execute(
            f"""
            copy (
                with main_families as ({main_families_sql}),
                current_blocking_citation as (
                    select
                        cited_docdb_family_id as docdb_family_id,
                        sum(citation_lethality_score) as family_blocking_citation_score_raw
                    from read_parquet('{cite_network}')
                    where cited_docdb_family_id is not null
                      and (
                          (citation_date is not null and citation_date <= date '{snapshot_date}')
                          or (
                              citation_date is null
                              and citation_year is not null
                              and citation_year <= {snapshot_year}
                          )
                      )
                    group by cited_docdb_family_id
                ),
                current_scores as (
                    select
                        c.docdb_family_id,
                        coalesce(f.primary_wipo_field, '__unknown__') as primary_wipo_field,
                        coalesce(f.family_tech_breadth_wipo_count, 1.0) as family_tech_breadth_wipo_count,
                        coalesce(s.family_composite_status, 'unknown') as family_composite_status,
                        coalesce(s.has_any_active_grant, false) as has_any_active_grant,
                        coalesce(e.family_market_threat_score_raw, 0.0) as family_market_threat_score_raw,
                        coalesce(e.family_overall_legal_enforceability_score, 0.0) as family_overall_legal_enforceability_score,
                        coalesce(x.family_adjusted_citation_score_raw, 0.0) as family_adjusted_citation_score_raw,
                        coalesce(cb.family_blocking_citation_score_raw, 0.0) as family_blocking_citation_score_raw
                    from main_families c
                    left join read_parquet('{fields}') f using (docdb_family_id)
                    left join read_parquet('{family_status}') s using (docdb_family_id)
                    left join ({current_enforce_rollup_sql}) e using (docdb_family_id)
                    left join read_parquet('{cite}') x using (docdb_family_id)
                    left join current_blocking_citation cb using (docdb_family_id)
                )
                select
                    docdb_family_id,
                    family_market_threat_score_raw,
                    family_adjusted_citation_score_raw,
                    family_blocking_citation_score_raw,
                    family_overall_legal_enforceability_score,
                    {current_blocking_raw_score_sql} as family_raw_absolute_blocking_power,
                    percent_rank() over (
                        partition by primary_wipo_field
                        order by {current_blocking_raw_score_sql}
                    ) * 100.0 as family_ui_blocking_power_score
                from current_scores
            ) to '{out_blocking}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_blocking)

    if {"field_ts", "field_legacy"} & selected_sections:
        field_ts_tmp_dir = ensure_dir(settings.gold_dir / "_tmp_gold_field_timeseries")
        for tmp in field_ts_tmp_dir.glob("field_timeseries_*.parquet"):
            tmp.unlink()

        con.execute(
            f"""
            create or replace temp table gold_scope_appln_field_weights as
            with distinct_scope_appln_fields as (
                select distinct
                    docdb_family_id,
                    appln_id,
                    appln_filing_date,
                    wipo_industry_code
                from read_parquet('{scope_appln_seed}')
                where docdb_family_id is not null
                  and appln_id is not null
                  and appln_filing_date is not null
                  and wipo_industry_code is not null
            )
            select
                docdb_family_id,
                appln_id,
                appln_filing_date,
                wipo_industry_code,
                1.0 / cast(count(*) over (partition by docdb_family_id, appln_id) as double) as application_field_weight
            from distinct_scope_appln_fields
            """
        )
        con.execute(
            f"""
            create or replace temp table gold_branch_field_base as
            select
                e.docdb_family_id,
                e.jurisdiction_code,
                e.wipo_industry_code,
                max(e.family_field_fraction) as base_fraction
            from read_parquet('{enforce}') e
            join gold_main_families m using (docdb_family_id)
            group by e.docdb_family_id, e.jurisdiction_code, e.wipo_industry_code
            """
        )
        current_field_path = field_ts_tmp_dir / f"field_timeseries_{snapshot_year}.parquet"
        con.execute(
            f"""
            copy (
                with current_scope_weights as (
                    select *
                    from gold_scope_appln_field_weights
                    where appln_filing_date <= date '{snapshot_date}'
                ),
                current_family_counts as (
                    select
                        docdb_family_id,
                        count(distinct appln_id) as family_application_count_asof
                    from current_scope_weights
                    group by docdb_family_id
                ),
                current_field_share as (
                    select
                        w.docdb_family_id,
                        w.wipo_industry_code,
                        sum(w.application_field_weight) as field_evidence_weight_asof,
                        count(distinct w.appln_id) as field_application_count_asof,
                        max(f.family_application_count_asof) as family_application_count_asof,
                        sum(w.application_field_weight) / cast(max(f.family_application_count_asof) as double) as field_share_asof
                    from current_scope_weights w
                    join current_family_counts f using (docdb_family_id)
                    group by w.docdb_family_id, w.wipo_industry_code
                ),
                current_field_state as (
                    select
                        e.docdb_family_id,
                        e.wipo_industry_code,
                        max(
                            case
                                when e.active_branch_flag then coalesce(e.final_market_multiplier, 0.0)
                                else 0.0
                            end
                        ) as active_market_weight,
                        max(
                            case
                                when e.branch_state_label = 'ACTIVE_OPPOSED_GRANT' then 3
                                when e.branch_state_label = 'ACTIVE_GRANT' then 2
                                when e.branch_state_label = 'PENDING_ONLY' then 1
                                else 0
                            end
                        ) as stage_rank,
                        max(case when e.active_branch_flag then 1 else 0 end) > 0 as is_active_on_snapshot
                    from read_parquet('{enforce}') e
                    join gold_main_families m using (docdb_family_id)
                    group by e.docdb_family_id, e.wipo_industry_code
                )
                select
                    fc.docdb_family_id,
                    {snapshot_year} as snapshot_year,
                    date '{snapshot_date}' as snapshot_date,
                    fc.wipo_industry_code,
                    fc.base_fraction,
                    case
                        when coalesce(fam.family_application_count_asof, 0) > 0 then coalesce(sh.field_share_asof, 0.0)
                        else fc.base_fraction
                    end as field_share_asof,
                    case
                        when coalesce(fam.family_application_count_asof, 0) > 0 then 'appln_weighted_field_share'
                        else 'base_fraction_fallback'
                    end as field_share_method,
                    case
                        when coalesce(fam.family_application_count_asof, 0) > 0 then coalesce(sh.field_evidence_weight_asof, 0.0)
                        else null
                    end as field_evidence_weight_asof,
                    case
                        when coalesce(fam.family_application_count_asof, 0) > 0 then coalesce(sh.field_application_count_asof, 0)
                        else 0
                    end as field_application_count_asof,
                    coalesce(fam.family_application_count_asof, 0) as family_application_count_asof,
                    fc.family_field_enforceability_contribution_score as enforceability_contribution_score,
                    fc.family_field_heritage_contribution_score as heritage_contribution_score,
                    coalesce(s.active_market_weight, 0.0) as active_market_weight,
                    case s.stage_rank
                        when 3 then 'ACTIVE_OPPOSED_GRANT'
                        when 2 then 'ACTIVE_GRANT'
                        when 1 then 'PENDING_ONLY'
                        else 'NO_ACTIVE_STATE'
                    end as max_active_stage,
                    coalesce(s.is_active_on_snapshot, false) as is_active_on_snapshot
                from read_parquet('{field_contrib}') fc
                join gold_main_families m using (docdb_family_id)
                left join current_family_counts fam
                  on fc.docdb_family_id = fam.docdb_family_id
                left join current_field_share sh
                  on fc.docdb_family_id = sh.docdb_family_id
                 and fc.wipo_industry_code = sh.wipo_industry_code
                left join current_field_state s
                  on fc.docdb_family_id = s.docdb_family_id
                 and fc.wipo_industry_code = s.wipo_industry_code
                where fc.snapshot_date = date '{snapshot_date}'
            ) to '{current_field_path}' (format parquet, compression zstd)
            """
        )

        historical_years = [year for year in history_years if history_start_year <= year < snapshot_year]
        for year in historical_years:
            yearly_path = field_ts_tmp_dir / f"field_timeseries_{year}.parquet"
            con.execute(
                f"""
                copy (
                    with cumulative_citation as (
                        select
                            cited_docdb_family_id as docdb_family_id,
                            sum(citation_lethality_score) as cumulative_citation_lethality
                        from read_parquet('{cite_network}')
                        where cited_docdb_family_id is not null
                          and citation_year is not null
                          and citation_year <= {year}
                        group by cited_docdb_family_id
                    ),
                    year_scope_weights as (
                        select *
                        from gold_scope_appln_field_weights
                        where appln_filing_date <= make_date({year}, 12, 31)
                    ),
                    year_family_counts as (
                        select
                            docdb_family_id,
                            count(distinct appln_id) as family_application_count_asof
                        from year_scope_weights
                        group by docdb_family_id
                    ),
                    year_field_share as (
                        select
                            w.docdb_family_id,
                            w.wipo_industry_code,
                            sum(w.application_field_weight) as field_evidence_weight_asof,
                            count(distinct w.appln_id) as field_application_count_asof,
                            max(f.family_application_count_asof) as family_application_count_asof,
                            sum(w.application_field_weight) / cast(max(f.family_application_count_asof) as double) as field_share_asof
                        from year_scope_weights w
                        join year_family_counts f using (docdb_family_id)
                        group by w.docdb_family_id, w.wipo_industry_code
                    )
                    select
                        b.docdb_family_id,
                        {year} as snapshot_year,
                        make_date({year}, 12, 31) as snapshot_date,
                        f.wipo_industry_code,
                        f.base_fraction,
                        case
                            when coalesce(fam.family_application_count_asof, 0) > 0 then coalesce(sh.field_share_asof, 0.0)
                            else f.base_fraction
                        end as field_share_asof,
                        case
                            when coalesce(fam.family_application_count_asof, 0) > 0 then 'appln_weighted_field_share'
                            else 'base_fraction_fallback'
                        end as field_share_method,
                        case
                            when coalesce(fam.family_application_count_asof, 0) > 0 then coalesce(sh.field_evidence_weight_asof, 0.0)
                            else null
                        end as field_evidence_weight_asof,
                        case
                            when coalesce(fam.family_application_count_asof, 0) > 0 then coalesce(sh.field_application_count_asof, 0)
                            else 0
                        end as field_application_count_asof,
                        coalesce(fam.family_application_count_asof, 0) as family_application_count_asof,
                        sum(
                            f.base_fraction
                            * coalesce(w.final_market_multiplier, 0.0)
                            * coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)
                            * case
                                when b.replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1.0
                                when b.replay_branch_state = 'PENDING_ONLY' then 0.2
                                else 0.0
                              end
                        ) as enforceability_contribution_score,
                        f.base_fraction * coalesce(c.cumulative_citation_lethality, 0.0) as heritage_contribution_score,
                        max(
                            case
                                when b.replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then coalesce(w.final_market_multiplier, 0.0)
                                else 0.0
                            end
                        ) as active_market_weight,
                        case max(
                            case
                                when b.replay_branch_state = 'ACTIVE_OPPOSED_GRANT' then 3
                                when b.replay_branch_state = 'ACTIVE_GRANT' then 2
                                when b.replay_branch_state = 'PENDING_ONLY' then 1
                                else 0
                            end
                        )
                            when 3 then 'ACTIVE_OPPOSED_GRANT'
                            when 2 then 'ACTIVE_GRANT'
                            when 1 then 'PENDING_ONLY'
                            else 'NO_ACTIVE_STATE'
                        end as max_active_stage,
                        max(
                            case
                                when b.replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1
                                else 0
                            end
                        ) > 0 as is_active_on_snapshot
                    from read_parquet('{branch_history_dense}') b
                    join gold_branch_field_base f
                      on b.docdb_family_id = f.docdb_family_id
                     and b.jurisdiction_code = f.jurisdiction_code
                    join gold_main_families m
                      on b.docdb_family_id = m.docdb_family_id
                    left join year_family_counts fam
                      on b.docdb_family_id = fam.docdb_family_id
                    left join year_field_share sh
                      on b.docdb_family_id = sh.docdb_family_id
                     and f.wipo_industry_code = sh.wipo_industry_code
                    left join read_parquet('{market_weight}') w
                      on b.jurisdiction_code = w.jurisdiction_code
                     and w.snapshot_year = {year}
                    left join read_parquet('{local_trend}') l
                      on b.jurisdiction_code = l.jurisdiction_code
                     and f.wipo_industry_code = l.wipo_industry_code
                     and l.snapshot_year = {year}
                    left join read_parquet('{global_trend}') g
                      on f.wipo_industry_code = g.wipo_industry_code
                     and g.snapshot_year = {year}
                    left join cumulative_citation c
                      on b.docdb_family_id = c.docdb_family_id
                    where b.snapshot_year = {year}
                    group by
                        b.docdb_family_id,
                        f.wipo_industry_code,
                        f.base_fraction,
                        fam.family_application_count_asof,
                        sh.field_share_asof,
                        sh.field_evidence_weight_asof,
                        sh.field_application_count_asof,
                        c.cumulative_citation_lethality
                ) to '{yearly_path}' (format parquet, compression zstd)
                """
            )

        con.execute(
            f"""
            copy (
                select *
                from read_parquet('{field_ts_tmp_dir / "field_timeseries_*.parquet"}')
            ) to '{out_field_ts}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_field_ts)
        if "field_legacy" in selected_sections:
            con.execute(f"copy (select * from read_parquet('{out_field_ts}')) to '{out_field_legacy}' (format parquet, compression zstd)")
            built_outputs.append(out_field_legacy)

    if "blocking_ts" in selected_sections:
        blocking_ts_tmp_dir = ensure_dir(settings.gold_dir / "_tmp_gold_blocking_timeseries")
        for tmp in blocking_ts_tmp_dir.glob("blocking_timeseries_*.parquet"):
            tmp.unlink()

        historical_years = [year for year in history_years if history_start_year <= year < snapshot_year]
        for year in historical_years:
            historical_blocking_raw_score_sql = _blocking_raw_score_expr(
                market_col="overall_legal_enforceability_score",
                citation_raw_col="blocking_citation_score_raw",
                has_active_col="has_active_grant_asof",
                status_col="family_composite_status_asof",
                breadth_col="family_tech_breadth_wipo_count",
            )
            yearly_path = blocking_ts_tmp_dir / f"blocking_timeseries_{year}.parquet"
            con.execute(
                f"""
                copy (
                    with main_families as ({main_families_sql}),
                    yearly_legal as (
                        select
                            b.docdb_family_id,
                            max(
                                case
                                    when b.replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1
                                    else 0
                                end
                            ) > 0 as has_active_grant_asof,
                            sum(
                                f.base_fraction
                                * coalesce(w.final_market_multiplier, 0.0)
                                * coalesce(l.local_trend_coefficient, g.global_trend_coefficient, 1.0)
                                * case
                                    when b.replay_branch_state in ('ACTIVE_GRANT', 'ACTIVE_OPPOSED_GRANT') then 1.0
                                    when b.replay_branch_state = 'PENDING_ONLY' then 0.2
                                    else 0.0
                                  end
                            ) as overall_legal_enforceability_score
                        from read_parquet('{branch_history_dense}') b
                        join main_families m using (docdb_family_id)
                        join (
                            select
                                docdb_family_id,
                                jurisdiction_code,
                                max(family_field_fraction) as base_fraction,
                                max(wipo_industry_code) as any_field
                            from read_parquet('{enforce}')
                            group by docdb_family_id, jurisdiction_code
                        ) f
                          on b.docdb_family_id = f.docdb_family_id
                         and b.jurisdiction_code = f.jurisdiction_code
                        left join read_parquet('{market_weight}') w
                          on b.jurisdiction_code = w.jurisdiction_code
                         and w.snapshot_year = {year}
                        left join read_parquet('{local_trend}') l
                          on b.jurisdiction_code = l.jurisdiction_code
                         and f.any_field = l.wipo_industry_code
                         and l.snapshot_year = {year}
                        left join read_parquet('{global_trend}') g
                          on f.any_field = g.wipo_industry_code
                         and g.snapshot_year = {year}
                        where b.snapshot_year = {year}
                        group by b.docdb_family_id
                    ),
                    yearly_citation_base as (
                        select
                            cited_docdb_family_id as docdb_family_id,
                            citation_year,
                            sum(citation_lethality_score) as yearly_citation_lethality
                        from read_parquet('{cite_network}')
                        where cited_docdb_family_id is not null
                          and citation_year is not null
                          and citation_year <= {year}
                        group by cited_docdb_family_id, citation_year
                    ),
                    yearly_citation as (
                        select
                            docdb_family_id,
                            sum(yearly_citation_lethality) as adjusted_citation_score_raw
                        from yearly_citation_base
                        group by docdb_family_id
                    ),
                    historical_rows as (
                        select
                            h.docdb_family_id,
                            make_date({year}, 12, 31) as snapshot_date,
                            coalesce(w.primary_wipo_field, '__unknown__') as primary_wipo_field,
                            coalesce(w.family_tech_breadth_wipo_count, 1.0) as family_tech_breadth_wipo_count,
                            coalesce(h.family_composite_status, 'unknown') as family_composite_status_asof,
                            coalesce(l.has_active_grant_asof, false) as has_active_grant_asof,
                            coalesce(l.overall_legal_enforceability_score, 0.0) as overall_legal_enforceability_score,
                            coalesce(y.adjusted_citation_score_raw, 0.0) as adjusted_citation_score_raw,
                            coalesce(y.adjusted_citation_score_raw, 0.0) as blocking_citation_score_raw
                        from read_parquet('{family_status_history}') h
                        join main_families m using (docdb_family_id)
                        left join read_parquet('{fields}') w using (docdb_family_id)
                        left join yearly_legal l using (docdb_family_id)
                        left join yearly_citation y using (docdb_family_id)
                        where h.snapshot_year = {year}
                    ),
                    historical_ranked as (
                        select
                            docdb_family_id,
                            snapshot_date,
                            {historical_blocking_raw_score_sql} as family_raw_absolute_blocking_power,
                            percent_rank() over (
                                partition by primary_wipo_field
                                order by {historical_blocking_raw_score_sql}
                            ) * 100.0 as ui_blocking_power_score,
                            overall_legal_enforceability_score,
                            adjusted_citation_score_raw,
                            blocking_citation_score_raw
                        from historical_rows
                    )
                    select
                        docdb_family_id,
                        snapshot_date,
                        ui_blocking_power_score,
                        overall_legal_enforceability_score,
                        adjusted_citation_score_raw,
                        blocking_citation_score_raw
                    from historical_ranked
                ) to '{yearly_path}' (format parquet, compression zstd)
                """
            )

        current_blocking_path = blocking_ts_tmp_dir / f"blocking_timeseries_{snapshot_year}.parquet"
        con.execute(
            f"""
            copy (
                select
                    b.docdb_family_id,
                    date '{snapshot_date}' as snapshot_date,
                    b.family_ui_blocking_power_score as ui_blocking_power_score,
                    b.family_overall_legal_enforceability_score as overall_legal_enforceability_score,
                    b.family_blocking_citation_score_raw as adjusted_citation_score_raw,
                    b.family_blocking_citation_score_raw as blocking_citation_score_raw
                from read_parquet('{out_blocking}') b
            ) to '{current_blocking_path}' (format parquet, compression zstd)
            """
        )

        con.execute(
            f"""
            copy (
                select *
                from read_parquet('{blocking_ts_tmp_dir / "blocking_timeseries_*.parquet"}')
            ) to '{out_blocking_ts}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_blocking_ts)

    if "attacker" in selected_sections:
        con.execute(
            f"""
            copy (
                with clean_edges as (
                select *
                from read_parquet('{cite_network}')
                where coalesce(clean_edge_weight, 0.0) > 0.0
                  and cited_docdb_family_id is not null
            ),
            main_families as ({main_families_sql})
            select
                e.cited_docdb_family_id as docdb_family_id,
                date '{snapshot_date}' as snapshot_date,
                coalesce(e.citing_assignee_name, 'UNKNOWN_OWNER') as citing_assignee_name,
                count(*) as citation_count,
                sum(e.citation_lethality_score) as citation_lethality_sum
            from clean_edges e
            join main_families m
              on e.cited_docdb_family_id = m.docdb_family_id
                group by
                    e.cited_docdb_family_id,
                    date '{snapshot_date}',
                    coalesce(e.citing_assignee_name, 'UNKNOWN_OWNER')
            ) to '{out_attacker}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_attacker)

    if "family_citation" in selected_sections:
        if family_pit.exists():
            con.execute(
                f"""
                copy (
                    with main_families as ({main_families_sql}),
                    latest_pit as (
                        select *
                        from read_parquet('{family_pit}')
                        qualify row_number() over (
                            partition by docdb_family_id
                            order by as_of_year desc, as_of_date desc nulls last
                        ) = 1
                    ),
                    current_rows as (
                        select
                            m.docdb_family_id,
                            cast(coalesce(cm.family_forward_citations_raw, 0.0) as double) as family_forward_citations_raw,
                            cast(coalesce(cm.family_forward_citations_clean, 0.0) as double) as family_forward_citations_clean,
                            cast(coalesce(cm.family_forward_citations_weighted, 0.0) as double) as family_forward_citations_weighted_raw,
                            cast(coalesce(cm.family_backward_patent_citation_count, 0.0) as double) as family_backward_patent_citation_count,
                            cast(coalesce(cm.family_backward_citations_clean, 0.0) as double) as family_backward_citations_clean,
                            cast(coalesce(cm.family_backward_npl_citation_count, 0.0) as double) as family_backward_npl_citation_count,
                            cast(coalesce(cm.out_of_bounds_citation_share, 0.0) as double) as out_of_bounds_citation_share,
                            cast(coalesce(cm.family_science_grounding_score, 0.0) as double) as family_science_grounding_score,
                            cast(coalesce(cm.family_rcf_score, 0.0) as double) as family_rcf_score,
                            cast(coalesce(lp.pre_asof_citing_assignee_diversity, 0.0) as double) as citing_assignee_diversity,
                            cast(coalesce(lp.data_completeness_pct_asof, 0.0) as double) as citation_data_completeness_pct_asof
                        from main_families m
                        left join read_parquet('{cite}') cm using (docdb_family_id)
                        left join latest_pit lp using (docdb_family_id)
                    )
                    select
                        docdb_family_id,
                        date '{snapshot_date}' as snapshot_date,
                        family_forward_citations_raw,
                        family_forward_citations_clean,
                        family_forward_citations_weighted_raw,
                        family_backward_patent_citation_count,
                        family_backward_citations_clean,
                        family_backward_npl_citation_count,
                        out_of_bounds_citation_share,
                        family_science_grounding_score,
                        family_rcf_score,
                        citing_assignee_diversity,
                        citation_data_completeness_pct_asof,
                        case
                            when citation_data_completeness_pct_asof >= 0.75 then 'high'
                            when citation_data_completeness_pct_asof >= 0.50 then 'medium'
                            else 'low'
                        end as citation_support_level,
                        percent_rank() over (
                            order by family_forward_citations_weighted_raw, docdb_family_id
                        ) * 100.0 as citation_influence_index,
                        percent_rank() over (
                            order by family_forward_citations_clean, docdb_family_id
                        ) * 100.0 as heritage_mass_index,
                        '{settings.method_version}' as method_version
                    from current_rows
                ) to '{out_family_citation_summary}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_family_citation_summary)
        else:
            result.warnings.append(
                f"Skipped gold_family_citation_summary because family PIT input was not found: {family_pit}"
            )

    if "family_citation_ts" in selected_sections:
        if family_pit.exists():
            con.execute(
                f"""
                copy (
                    with main_families as ({main_families_sql})
                        select
                            fs.docdb_family_id,
                            cast(fs.as_of_year as integer) as as_of_year,
                            coalesce(fs.as_of_date, make_date(fs.as_of_year, 12, 31)) as as_of_date,
                            cast(coalesce(fs.pre_asof_forward_citations_clean, 0.0) as double) as pre_asof_forward_citations_clean,
                            cast(coalesce(fs.pre_asof_forward_citations_weighted, 0.0) as double) as pre_asof_forward_citations_weighted,
                            cast(coalesce(fs.pre_asof_unique_citing_family_count, 0.0) as double) as pre_asof_unique_citing_family_count,
                            cast(coalesce(fs.pre_asof_citing_assignee_diversity, 0.0) as double) as pre_asof_citing_assignee_diversity,
                            cast(coalesce(fs.pre_asof_attacker_density_score, 0.0) as double) as pre_asof_attacker_density_score,
                            cast(coalesce(fs.data_completeness_pct_asof, 0.0) as double) as citation_data_completeness_pct_asof,
                            case
                                when coalesce(fs.data_completeness_pct_asof, 0.0) >= 0.75 then 'high'
                                when coalesce(fs.data_completeness_pct_asof, 0.0) >= 0.50 then 'medium'
                                else 'low'
                        end as citation_support_level,
                        percent_rank() over (
                            partition by fs.as_of_year
                            order by coalesce(fs.pre_asof_forward_citations_weighted, 0.0), fs.docdb_family_id
                        ) * 100.0 as citation_influence_index_asof,
                        coalesce(fs.is_observed_as_of_snapshot, false) as historical_citation_safe,
                        '{settings.method_version}' as method_version
                    from read_parquet('{family_pit}') fs
                    join main_families m using (docdb_family_id)
                    where coalesce(fs.is_observed_as_of_snapshot, false)
                ) to '{out_family_citation_timeseries}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_family_citation_timeseries)
        else:
            result.warnings.append(
                f"Skipped gold_family_citation_timeseries_pit because family PIT input was not found: {family_pit}"
            )

    if "portfolio_citation_summary" in selected_sections:
        if out_family_citation_timeseries.exists() and out_family_citation_summary.exists():
            con.execute("set threads=2")
            chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_portfolio_citation_summary")
            for stale in chunk_dir.glob("portfolio_citation_summary_*.parquet"):
                stale.unlink()

            year_rows = con.execute(
                f"""
                select distinct as_of_year
                from read_parquet('{out_family_citation_timeseries}')
                order by 1
                """
            ).fetchall()
            for (as_of_year,) in year_rows:
                chunk_path = chunk_dir / f"portfolio_citation_summary_{int(as_of_year)}.parquet"
                con.execute(
                    f"""
                    copy (
                        with main_families as ({main_families_sql}),
                        primary_owner_bridge as ({primary_owner_bridge_sql}),
                        owner_identity as ({owner_identity_sql}),
                        pit_rows as (
                            select
                                pob.owner_name_harmonized,
                                cast(fcts.as_of_year as integer) as as_of_year,
                                fcts.docdb_family_id,
                                cast(coalesce(fcts.pre_asof_forward_citations_clean, 0.0) as double) as pre_asof_forward_citations_clean,
                                cast(coalesce(fcts.pre_asof_forward_citations_weighted, 0.0) as double) as pre_asof_forward_citations_weighted,
                                cast(coalesce(fcts.pre_asof_unique_citing_family_count, 0.0) as double) as pre_asof_unique_citing_family_count,
                                cast(coalesce(fcts.pre_asof_citing_assignee_diversity, 0.0) as double) as pre_asof_citing_assignee_diversity,
                                cast(coalesce(fcts.pre_asof_attacker_density_score, 0.0) as double) as pre_asof_attacker_density_score,
                                cast(coalesce(fcts.citation_data_completeness_pct_asof, 0.0) as double) as data_completeness_pct_asof
                            from read_parquet('{out_family_citation_timeseries}') fcts
                            join main_families m using (docdb_family_id)
                            join primary_owner_bridge pob using (docdb_family_id)
                            where fcts.as_of_year = {int(as_of_year)}
                        ),
                        current_rows as (
                            select
                                distinct p.owner_name_harmonized,
                                p.docdb_family_id,
                                cast(coalesce(fcs.family_backward_citations_clean, 0.0) as double) as family_backward_citations_clean,
                                cast(coalesce(fcs.family_backward_npl_citation_count, 0.0) as double) as family_backward_npl_citation_count,
                                cast(coalesce(fcs.family_science_grounding_score, 0.0) as double) as family_science_grounding_score,
                                cast(coalesce(fcs.out_of_bounds_citation_share, 0.0) as double) as out_of_bounds_citation_share,
                                cast(coalesce(gfs.family_generality_percentile, 0.0) as double) as family_generality_percentile,
                                cast(coalesce(gfs.family_originality_percentile, 0.0) as double) as family_originality_percentile
                            from pit_rows p
                            left join read_parquet('{out_family_citation_summary}') fcs using (docdb_family_id)
                            left join read_parquet('{out_family_summary}') gfs using (docdb_family_id)
                        ),
                        current_agg as (
                            select
                                owner_name_harmonized,
                                cast(coalesce(sum(family_backward_npl_citation_count), 0.0) as double) as backward_npl_citation_total,
                                cast(coalesce(avg(family_science_grounding_score), 0.0) as double) as avg_science_grounding_score,
                                cast(coalesce(avg(family_generality_percentile), 0.0) as double) as avg_generality_percentile,
                                cast(coalesce(avg(family_originality_percentile), 0.0) as double) as avg_originality_percentile,
                                cast(coalesce(avg(out_of_bounds_citation_share), 0.0) as double) as avg_out_of_bounds_citation_share
                            from current_rows
                            group by owner_name_harmonized
                        ),
                        exact_forward as (
                            select
                                p.owner_name_harmonized,
                                cast(count(*) as double) as forward_citations_clean_total,
                                cast(coalesce(sum(n.clean_edge_weight), 0.0) as double) as forward_citations_weighted_total,
                                count(distinct n.source_docdb_family_id)::bigint as distinct_citing_family_count
                            from pit_rows p
                            join read_parquet('{cite_network}') n
                              on n.cited_docdb_family_id = p.docdb_family_id
                            where not coalesce(n.is_out_of_bounds, false)
                              and not coalesce(n.is_intra_family_citation, false)
                              and not coalesce(n.is_self_citation, false)
                              and cast(coalesce(n.citation_year, 0) as integer) <= p.as_of_year
                            group by p.owner_name_harmonized
                        ),
                        exact_backward as (
                            select
                                p.owner_name_harmonized,
                                cast(count(*) as double) as backward_citations_clean_total,
                                count(distinct n.cited_docdb_family_id)::bigint as distinct_cited_family_count
                            from pit_rows p
                            join read_parquet('{cite_network}') n
                              on n.source_docdb_family_id = p.docdb_family_id
                            where n.cited_docdb_family_id is not null
                              and not coalesce(n.is_out_of_bounds, false)
                              and not coalesce(n.is_intra_family_citation, false)
                              and not coalesce(n.is_self_citation, false)
                              and cast(coalesce(n.citation_year, 0) as integer) <= p.as_of_year
                            group by p.owner_name_harmonized
                        )
                        select
                            p.owner_name_harmonized,
                            oi.owner_name_display,
                            p.as_of_year,
                            date '{snapshot_date}' as current_snapshot_date,
                            count(distinct p.docdb_family_id) as family_count,
                            coalesce(ef.forward_citations_clean_total, 0.0) as forward_citations_clean_total,
                            coalesce(ef.forward_citations_weighted_total, 0.0) as forward_citations_weighted_total,
                            coalesce(ef.distinct_citing_family_count, 0) as distinct_citing_family_count,
                            cast(coalesce(avg(p.pre_asof_unique_citing_family_count), 0.0) as double) as avg_unique_citing_family_count,
                            cast(coalesce(avg(p.pre_asof_citing_assignee_diversity), 0.0) as double) as avg_citing_assignee_diversity,
                            cast(coalesce(avg(p.pre_asof_attacker_density_score), 0.0) as double) as avg_attacker_density_score,
                            cast(coalesce(avg(p.data_completeness_pct_asof), 0.0) as double) as avg_citation_data_completeness_pct,
                            case
                                when avg(p.data_completeness_pct_asof) >= 0.75 then 'high'
                                when avg(p.data_completeness_pct_asof) >= 0.50 then 'medium'
                                else 'low'
                            end as citation_support_level,
                            coalesce(eb.backward_citations_clean_total, 0.0) as backward_citations_clean_total,
                            coalesce(ca.backward_npl_citation_total, 0.0) as backward_npl_citation_total,
                            coalesce(eb.distinct_cited_family_count, 0) as distinct_cited_family_count,
                            coalesce(ca.avg_science_grounding_score, 0.0) as avg_science_grounding_score,
                            coalesce(ca.avg_generality_percentile, 0.0) as avg_generality_percentile,
                            coalesce(ca.avg_originality_percentile, 0.0) as avg_originality_percentile,
                            coalesce(ca.avg_out_of_bounds_citation_share, 0.0) as avg_out_of_bounds_citation_share,
                            '{settings.method_version}' as method_version
                        from pit_rows p
                        left join current_agg ca using (owner_name_harmonized)
                        left join exact_forward ef using (owner_name_harmonized)
                        left join exact_backward eb using (owner_name_harmonized)
                        left join owner_identity oi
                          on p.owner_name_harmonized = oi.owner_name_harmonized
                        group by
                            p.owner_name_harmonized,
                            oi.owner_name_display,
                            p.as_of_year,
                            ef.forward_citations_clean_total,
                            ef.forward_citations_weighted_total,
                            ef.distinct_citing_family_count,
                            eb.backward_citations_clean_total,
                            eb.distinct_cited_family_count,
                            ca.backward_npl_citation_total,
                            ca.avg_science_grounding_score,
                            ca.avg_generality_percentile,
                            ca.avg_originality_percentile,
                            ca.avg_out_of_bounds_citation_share
                    ) to '{chunk_path}' (format parquet, compression zstd)
                    """
                )
            if out_portfolio_citation_summary.exists():
                out_portfolio_citation_summary.unlink()
            con.execute(
                f"""
                copy (
                    select *
                    from read_parquet('{chunk_dir / 'portfolio_citation_summary_*.parquet'}')
                ) to '{out_portfolio_citation_summary}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_portfolio_citation_summary)
        elif family_pit.exists():
            con.execute(
                f"""
                copy (
                    with main_families as ({main_families_sql}),
                    primary_owner_bridge as ({primary_owner_bridge_sql}),
                    owner_identity as ({owner_identity_sql}),
                    pit_rows as (
                        select
                            pob.owner_name_harmonized,
                            cast(fs.as_of_year as integer) as as_of_year,
                            fs.docdb_family_id,
                            cast(coalesce(fs.pre_asof_forward_citations_clean, 0.0) as double) as pre_asof_forward_citations_clean,
                            cast(coalesce(fs.pre_asof_forward_citations_weighted, 0.0) as double) as pre_asof_forward_citations_weighted,
                            cast(coalesce(fs.pre_asof_unique_citing_family_count, 0.0) as double) as pre_asof_unique_citing_family_count,
                            cast(coalesce(fs.pre_asof_citing_assignee_diversity, 0.0) as double) as pre_asof_citing_assignee_diversity,
                            cast(coalesce(fs.pre_asof_attacker_density_score, 0.0) as double) as pre_asof_attacker_density_score,
                            cast(coalesce(fs.data_completeness_pct_asof, 0.0) as double) as data_completeness_pct_asof
                        from read_parquet('{family_pit}') fs
                        join main_families m using (docdb_family_id)
                        join primary_owner_bridge pob using (docdb_family_id)
                        where coalesce(fs.is_observed_as_of_snapshot, false)
                    ),
                    current_rows as (
                        select
                            distinct p.owner_name_harmonized,
                            p.docdb_family_id,
                            cast(coalesce(cm.family_backward_citations_clean, 0.0) as double) as family_backward_citations_clean,
                            cast(coalesce(cm.family_backward_npl_citation_count, 0.0) as double) as family_backward_npl_citation_count,
                            cast(coalesce(cm.family_science_grounding_score, 0.0) as double) as family_science_grounding_score,
                            cast(coalesce(cm.out_of_bounds_citation_share, 0.0) as double) as out_of_bounds_citation_share,
                            cast(coalesce(gs.family_generality_percentile, 0.0) as double) as family_generality_percentile,
                            cast(coalesce(gs.family_originality_percentile, 0.0) as double) as family_originality_percentile
                        from pit_rows p
                        left join read_parquet('{cite}') cm using (docdb_family_id)
                        left join read_parquet('{out_family_summary}') gs using (docdb_family_id)
                    ),
                    current_agg as (
                        select
                            owner_name_harmonized,
                            cast(coalesce(sum(family_backward_npl_citation_count), 0.0) as double) as backward_npl_citation_total,
                            cast(coalesce(avg(family_science_grounding_score), 0.0) as double) as avg_science_grounding_score,
                            cast(coalesce(avg(family_generality_percentile), 0.0) as double) as avg_generality_percentile,
                            cast(coalesce(avg(family_originality_percentile), 0.0) as double) as avg_originality_percentile,
                            cast(coalesce(avg(out_of_bounds_citation_share), 0.0) as double) as avg_out_of_bounds_citation_share
                        from current_rows
                        group by owner_name_harmonized
                    ),
                    exact_forward as (
                        select
                            p.owner_name_harmonized,
                            cast(count(*) as double) as forward_citations_clean_total,
                            cast(coalesce(sum(n.clean_edge_weight), 0.0) as double) as forward_citations_weighted_total,
                            count(distinct n.source_docdb_family_id)::bigint as distinct_citing_family_count
                        from pit_rows p
                        join read_parquet('{cite_network}') n
                          on n.cited_docdb_family_id = p.docdb_family_id
                        where not coalesce(n.is_out_of_bounds, false)
                          and not coalesce(n.is_intra_family_citation, false)
                          and not coalesce(n.is_self_citation, false)
                          and cast(coalesce(n.citation_year, 0) as integer) <= p.as_of_year
                        group by p.owner_name_harmonized
                    ),
                    exact_backward as (
                        select
                            p.owner_name_harmonized,
                            cast(count(*) as double) as backward_citations_clean_total,
                            count(distinct n.cited_docdb_family_id)::bigint as distinct_cited_family_count
                        from pit_rows p
                        join read_parquet('{cite_network}') n
                          on n.source_docdb_family_id = p.docdb_family_id
                        where n.cited_docdb_family_id is not null
                          and not coalesce(n.is_out_of_bounds, false)
                          and not coalesce(n.is_intra_family_citation, false)
                          and not coalesce(n.is_self_citation, false)
                          and cast(coalesce(n.citation_year, 0) as integer) <= p.as_of_year
                        group by p.owner_name_harmonized
                    )
                    select
                        p.owner_name_harmonized,
                        oi.owner_name_display,
                        p.as_of_year,
                        date '{snapshot_date}' as current_snapshot_date,
                        count(distinct p.docdb_family_id) as family_count,
                        coalesce(ef.forward_citations_clean_total, 0.0) as forward_citations_clean_total,
                        coalesce(ef.forward_citations_weighted_total, 0.0) as forward_citations_weighted_total,
                        coalesce(ef.distinct_citing_family_count, 0) as distinct_citing_family_count,
                        cast(coalesce(avg(p.pre_asof_unique_citing_family_count), 0.0) as double) as avg_unique_citing_family_count,
                        cast(coalesce(avg(p.pre_asof_citing_assignee_diversity), 0.0) as double) as avg_citing_assignee_diversity,
                        cast(coalesce(avg(p.pre_asof_attacker_density_score), 0.0) as double) as avg_attacker_density_score,
                        cast(coalesce(avg(p.data_completeness_pct_asof), 0.0) as double) as avg_citation_data_completeness_pct,
                        case
                            when avg(p.data_completeness_pct_asof) >= 0.75 then 'high'
                            when avg(p.data_completeness_pct_asof) >= 0.50 then 'medium'
                            else 'low'
                        end as citation_support_level,
                        coalesce(eb.backward_citations_clean_total, 0.0) as backward_citations_clean_total,
                        coalesce(ca.backward_npl_citation_total, 0.0) as backward_npl_citation_total,
                        coalesce(eb.distinct_cited_family_count, 0) as distinct_cited_family_count,
                        coalesce(ca.avg_science_grounding_score, 0.0) as avg_science_grounding_score,
                        coalesce(ca.avg_generality_percentile, 0.0) as avg_generality_percentile,
                        coalesce(ca.avg_originality_percentile, 0.0) as avg_originality_percentile,
                        coalesce(ca.avg_out_of_bounds_citation_share, 0.0) as avg_out_of_bounds_citation_share,
                        '{settings.method_version}' as method_version
                    from pit_rows p
                    left join current_agg ca using (owner_name_harmonized)
                    left join exact_forward ef using (owner_name_harmonized)
                    left join exact_backward eb using (owner_name_harmonized)
                    left join owner_identity oi
                      on p.owner_name_harmonized = oi.owner_name_harmonized
                    group by
                        p.owner_name_harmonized,
                        oi.owner_name_display,
                        p.as_of_year,
                        ef.forward_citations_clean_total,
                        ef.forward_citations_weighted_total,
                        ef.distinct_citing_family_count,
                        eb.backward_citations_clean_total,
                        eb.distinct_cited_family_count,
                        ca.backward_npl_citation_total,
                        ca.avg_science_grounding_score,
                        ca.avg_generality_percentile,
                        ca.avg_originality_percentile,
                        ca.avg_out_of_bounds_citation_share
                ) to '{out_portfolio_citation_summary}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_portfolio_citation_summary)
        else:
            result.warnings.append(
                f"Skipped gold_portfolio_citation_summary because family PIT input was not found: {family_pit}"
            )

    if "portfolio_citation_family_leaderboard" in selected_sections:
        required_inputs = [out_family_summary, out_family_citation_summary, out_blocking]
        missing_inputs = [str(path) for path in required_inputs if not path.exists()]
        if not missing_inputs:
            temp_out_portfolio_citation_family_leaderboard = settings.gold_dir / (
                f".{out_portfolio_citation_family_leaderboard.name}.tmp"
            )
            if temp_out_portfolio_citation_family_leaderboard.exists():
                temp_out_portfolio_citation_family_leaderboard.unlink()
            latest_citation_source_sql = (
                f"""
                select
                    docdb_family_id,
                    cast(coalesce(pre_asof_unique_citing_family_count, 0.0) as double) as unique_citing_family_count,
                    cast(coalesce(pre_asof_citing_assignee_diversity, 0.0) as double) as pit_citing_assignee_diversity,
                    row_number() over (
                        partition by docdb_family_id
                        order by as_of_year desc
                    ) as citation_rank
                from read_parquet('{out_family_citation_timeseries}')
                """
                if out_family_citation_timeseries.exists()
                else """
                select
                    null::bigint as docdb_family_id,
                    cast(null as double) as unique_citing_family_count,
                    cast(null as double) as pit_citing_assignee_diversity,
                    cast(1 as integer) as citation_rank
                where false
                """
            )
            con.execute(
                f"""
                copy (
                    with main_families as ({main_families_sql}),
                    primary_owner_bridge as ({primary_owner_bridge_sql}),
                    owner_identity as ({owner_identity_sql}),
                    latest_citation_pit as (
                        {latest_citation_source_sql}
                    ),
                    latest_citation as (
                        select
                            docdb_family_id,
                            unique_citing_family_count,
                            pit_citing_assignee_diversity
                        from latest_citation_pit
                        where citation_rank = 1
                    )
                    select
                        pob.owner_name_harmonized,
                        oi.owner_name_display,
                        date '{snapshot_date}' as current_snapshot_date,
                        pob.docdb_family_id,
                        cast(coalesce(fs.family_priority_year, 0) as integer) as family_priority_year,
                        coalesce(fs.primary_wipo_field, 'unknown') as primary_wipo_field,
                        coalesce(fs.family_composite_status, 'unknown') as family_composite_status,
                        cast(coalesce(fcs.family_forward_citations_clean, cm.family_forward_citations_clean, 0.0) as double) as family_forward_citations_clean,
                        cast(coalesce(fcs.family_forward_citations_weighted_raw, cm.family_forward_citations_weighted, 0.0) as double) as family_forward_citations_weighted_raw,
                        cast(coalesce(cm.family_fwd_cits5, 0.0) as double) as family_fwd_cits5,
                        cast(coalesce(cm.family_fwd_cits7, 0.0) as double) as family_fwd_cits7,
                        cast(coalesce(lc.unique_citing_family_count, 0.0) as double) as unique_citing_family_count,
                        cast(coalesce(lc.pit_citing_assignee_diversity, fcs.citing_assignee_diversity, 0.0) as double) as citing_assignee_diversity,
                        cast(coalesce(fb.family_ui_blocking_power_score, 0.0) as double) as family_ui_blocking_power_score,
                        '{settings.method_version}' as method_version
                    from primary_owner_bridge pob
                    join main_families mf using (docdb_family_id)
                    left join read_parquet('{out_family_summary}') fs using (docdb_family_id)
                    left join read_parquet('{out_family_citation_summary}') fcs using (docdb_family_id)
                    left join read_parquet('{cite}') cm using (docdb_family_id)
                    left join read_parquet('{out_blocking}') fb using (docdb_family_id)
                    left join latest_citation lc using (docdb_family_id)
                    left join owner_identity oi
                      on pob.owner_name_harmonized = oi.owner_name_harmonized
                ) to '{temp_out_portfolio_citation_family_leaderboard}' (format parquet, compression zstd)
                """
            )
            temp_out_portfolio_citation_family_leaderboard.replace(
                out_portfolio_citation_family_leaderboard
            )
            built_outputs.append(out_portfolio_citation_family_leaderboard)
        else:
            result.warnings.append(
                "Skipped gold_portfolio_citation_family_leaderboard because required inputs were not found: "
                + ", ".join(missing_inputs)
            )

    if "portfolio_citation_ts" in selected_sections:
        if out_portfolio_citation_summary in built_outputs:
            con.execute(
                f"""
                copy (
                    select
                        owner_name_harmonized,
                        owner_name_display,
                        as_of_year,
                        current_snapshot_date,
                        family_count,
                        forward_citations_clean_total,
                        forward_citations_weighted_total,
                        distinct_citing_family_count,
                        backward_citations_clean_total,
                        distinct_cited_family_count,
                        avg_unique_citing_family_count,
                        avg_citing_assignee_diversity,
                        avg_attacker_density_score,
                        avg_citation_data_completeness_pct,
                        citation_support_level,
                        method_version
                    from read_parquet('{out_portfolio_citation_summary}')
                ) to '{out_portfolio_citation_timeseries}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_portfolio_citation_timeseries)
        else:
            result.warnings.append(
                "Skipped gold_portfolio_citation_timeseries because gold_portfolio_citation_summary was not built."
            )

    if "portfolio_citation_attacker" in selected_sections:
        con.execute(
            f"""
            copy (
                with main_families as ({main_families_sql}),
                primary_owner_bridge as ({primary_owner_bridge_sql}),
                clean_edges as (
                    select *
                    from read_parquet('{cite_network}')
                    where coalesce(clean_edge_weight, 0.0) > 0.0
                      and cited_docdb_family_id is not null
                      and not coalesce(is_intra_family_citation, false)
                      and not coalesce(is_self_citation, false)
                      and not coalesce(is_out_of_bounds, false)
                ),
                base as (
                    select
                        pob.owner_name_harmonized,
                        cast(coalesce(e.citation_year, 0) as integer) as year,
                        coalesce(e.citing_assignee_name, 'UNKNOWN_OWNER') as citing_assignee_name,
                        coalesce(e.citing_primary_wipo_field, '') as wipo_field,
                        coalesce(e.citing_jurisdiction_code, '') as jurisdiction_code,
                        cast(coalesce(e.clean_edge_weight, 0.0) as double) as clean_edge_weight,
                        cast(coalesce(e.citation_lethality_score, 0.0) as double) as citation_lethality_score
                    from clean_edges e
                    join main_families m
                      on e.cited_docdb_family_id = m.docdb_family_id
                    join primary_owner_bridge pob
                      on e.cited_docdb_family_id = pob.docdb_family_id
                ),
                ranked as (
                    select
                        owner_name_harmonized,
                        year,
                        citing_assignee_name,
                        wipo_field,
                        jurisdiction_code,
                        count(*) as citation_event_count,
                        cast(coalesce(sum(clean_edge_weight), 0.0) as double) as clean_citation_count,
                        cast(coalesce(sum(citation_lethality_score), 0.0) as double) as citation_lethality_sum_raw
                    from base
                    group by
                        owner_name_harmonized,
                        year,
                        citing_assignee_name,
                        wipo_field,
                        jurisdiction_code
                )
                select
                    owner_name_harmonized,
                    date '{snapshot_date}' as current_snapshot_date,
                    year,
                    citing_assignee_name,
                    wipo_field,
                    jurisdiction_code,
                    citation_event_count,
                    clean_citation_count,
                    citation_lethality_sum_raw,
                    percent_rank() over (
                        partition by owner_name_harmonized, year
                        order by citation_lethality_sum_raw, citing_assignee_name
                    ) * 100.0 as attacker_pressure_index,
                    case
                        when lag(citation_lethality_sum_raw) over (
                            partition by owner_name_harmonized, citing_assignee_name, wipo_field, jurisdiction_code
                            order by year
                        ) is null then 'flat'
                        when citation_lethality_sum_raw > lag(citation_lethality_sum_raw) over (
                            partition by owner_name_harmonized, citing_assignee_name, wipo_field, jurisdiction_code
                            order by year
                        ) then 'heating'
                        when citation_lethality_sum_raw < lag(citation_lethality_sum_raw) over (
                            partition by owner_name_harmonized, citing_assignee_name, wipo_field, jurisdiction_code
                            order by year
                        ) then 'cooling'
                        else 'flat'
                    end as momentum_direction,
                    '{settings.method_version}' as method_version
                from ranked
            ) to '{out_portfolio_citation_attacker}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_portfolio_citation_attacker)

    if "portfolio_citation_field" in selected_sections:
        if out_portfolio_citation_attacker in built_outputs:
            con.execute(
                f"""
                copy (
                    with ranked as (
                        select
                            owner_name_harmonized,
                            year,
                            wipo_field,
                            count(distinct citing_assignee_name) as citing_assignee_count,
                            sum(citation_event_count) as citation_event_count,
                            cast(coalesce(sum(clean_citation_count), 0.0) as double) as clean_citation_count,
                            cast(coalesce(sum(citation_lethality_sum_raw), 0.0) as double) as citation_lethality_sum_raw
                        from read_parquet('{out_portfolio_citation_attacker}')
                        group by owner_name_harmonized, year, wipo_field
                    )
                    select
                        owner_name_harmonized,
                        date '{snapshot_date}' as current_snapshot_date,
                        year,
                        wipo_field,
                        citing_assignee_count,
                        citation_event_count,
                        clean_citation_count,
                        citation_lethality_sum_raw,
                        percent_rank() over (
                            partition by owner_name_harmonized, year
                            order by citation_lethality_sum_raw, wipo_field
                        ) * 100.0 as citation_pressure_index,
                        '{settings.method_version}' as method_version
                    from ranked
                ) to '{out_portfolio_citation_field}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_portfolio_citation_field)
        else:
            result.warnings.append(
                "Skipped gold_portfolio_citation_pressure_by_field because gold_portfolio_attacker_momentum was not built."
            )

    if "portfolio_citation_jurisdiction" in selected_sections:
        if out_portfolio_citation_attacker in built_outputs:
            con.execute(
                f"""
                copy (
                    with ranked as (
                        select
                            owner_name_harmonized,
                            year,
                            jurisdiction_code,
                            count(distinct citing_assignee_name) as citing_assignee_count,
                            count(distinct wipo_field) as wipo_field_count,
                            sum(citation_event_count) as citation_event_count,
                            cast(coalesce(sum(clean_citation_count), 0.0) as double) as clean_citation_count,
                            cast(coalesce(sum(citation_lethality_sum_raw), 0.0) as double) as citation_lethality_sum_raw
                        from read_parquet('{out_portfolio_citation_attacker}')
                        group by owner_name_harmonized, year, jurisdiction_code
                    )
                    select
                        owner_name_harmonized,
                        date '{snapshot_date}' as current_snapshot_date,
                        year,
                        jurisdiction_code,
                        citing_assignee_count,
                        wipo_field_count,
                        citation_event_count,
                        clean_citation_count,
                        citation_lethality_sum_raw,
                        percent_rank() over (
                            partition by owner_name_harmonized, year
                            order by citation_lethality_sum_raw, jurisdiction_code
                        ) * 100.0 as citation_pressure_index,
                        '{settings.method_version}' as method_version
                    from ranked
                ) to '{out_portfolio_citation_jurisdiction}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_portfolio_citation_jurisdiction)
        else:
            result.warnings.append(
                "Skipped gold_portfolio_citation_pressure_by_jurisdiction because gold_portfolio_attacker_momentum was not built."
            )

    if "portfolio_filing_timeseries" in selected_sections:
        required_inputs = [out_family_summary]
        missing_inputs = [str(path) for path in required_inputs if not path.exists()]
        if not missing_inputs:
            temp_out_portfolio_filing_timeseries = settings.gold_dir / (
                f".{out_portfolio_filing_timeseries.name}.tmp"
            )
            if temp_out_portfolio_filing_timeseries.exists():
                temp_out_portfolio_filing_timeseries.unlink()
            con.execute(
                f"""
                copy (
                    with main_families as ({main_families_sql}),
                    owner_bridge_scope as ({owner_bridge_scope_sql}),
                    owner_identity as ({owner_identity_sql}),
                    yearly as (
                        select
                            obs.owner_name_harmonized,
                            cast(fs.family_priority_year as integer) as filing_year,
                            count(distinct obs.docdb_family_id) as family_filing_count
                        from owner_bridge_scope obs
                        join main_families mf using (docdb_family_id)
                        join read_parquet('{out_family_summary}') fs using (docdb_family_id)
                        where cast(coalesce(fs.family_priority_year, 0) as integer) > 0
                        group by
                            obs.owner_name_harmonized,
                            cast(fs.family_priority_year as integer)
                    ),
                    windows as (
                        select
                            owner_name_harmonized,
                            filing_year,
                            family_filing_count,
                            sum(family_filing_count) over (
                                partition by owner_name_harmonized
                                order by filing_year
                                rows between unbounded preceding and current row
                            ) as cumulative_family_count,
                            sum(family_filing_count) over (
                                partition by owner_name_harmonized
                                order by filing_year
                                rows between 2 preceding and current row
                            ) as rolling_3y_family_filing_count,
                            sum(family_filing_count) over (
                                partition by owner_name_harmonized
                                order by filing_year
                                rows between 5 preceding and 3 preceding
                            ) as prior_3y_family_filing_count
                        from yearly
                    )
                    select
                        w.owner_name_harmonized,
                        oi.owner_name_display,
                        cast(w.filing_year as integer) as filing_year,
                        date '{snapshot_date}' as current_snapshot_date,
                        cast(w.family_filing_count as bigint) as family_filing_count,
                        cast(w.cumulative_family_count as bigint) as cumulative_family_count,
                        cast(w.rolling_3y_family_filing_count as bigint) as rolling_3y_family_filing_count,
                        cast(coalesce(w.prior_3y_family_filing_count, 0) as bigint) as prior_3y_family_filing_count,
                        cast(
                            case
                                when coalesce(w.prior_3y_family_filing_count, 0) <= 0 and w.rolling_3y_family_filing_count > 0 then 1.0
                                when coalesce(w.prior_3y_family_filing_count, 0) <= 0 then 0.0
                                else (w.rolling_3y_family_filing_count - w.prior_3y_family_filing_count) / cast(w.prior_3y_family_filing_count as double)
                            end
                        as double) as rolling_3y_change_pct,
                        case
                            when coalesce(w.prior_3y_family_filing_count, 0) <= 0 and w.rolling_3y_family_filing_count > 0 then 'accelerating'
                            when (
                                case
                                    when coalesce(w.prior_3y_family_filing_count, 0) <= 0 then 0.0
                                    else (w.rolling_3y_family_filing_count - w.prior_3y_family_filing_count) / cast(w.prior_3y_family_filing_count as double)
                                end
                            ) >= 0.20 then 'accelerating'
                            when (
                                case
                                    when coalesce(w.prior_3y_family_filing_count, 0) <= 0 then 0.0
                                    else (w.rolling_3y_family_filing_count - w.prior_3y_family_filing_count) / cast(w.prior_3y_family_filing_count as double)
                                end
                            ) <= -0.20 then 'cooling'
                            else 'stable'
                        end as momentum_direction,
                        '{settings.method_version}' as method_version
                    from windows w
                    left join owner_identity oi
                      on w.owner_name_harmonized = oi.owner_name_harmonized
                ) to '{temp_out_portfolio_filing_timeseries}' (format parquet, compression zstd)
                """
            )
            temp_out_portfolio_filing_timeseries.replace(out_portfolio_filing_timeseries)
            built_outputs.append(out_portfolio_filing_timeseries)
        else:
            result.warnings.append(
                "Skipped gold_portfolio_filing_timeseries because required inputs were not found: "
                + ", ".join(missing_inputs)
            )

    if "portfolio_field_ts" in selected_sections:
        con.execute(
            f"""
            copy (
                with main_families as ({main_families_sql}),
                current_field_rows as (
                select *
                from read_parquet('{out_field_ts}')
                where snapshot_date = date '{snapshot_date}'
            )
            select
                ob.owner_name_harmonized,
                date '{snapshot_date}' as snapshot_date,
                c.wipo_industry_code as wipo_field,
                count(distinct case when c.is_active_on_snapshot then c.docdb_family_id end) as active_family_count,
                sum(coalesce(c.enforceability_contribution_score, 0.0)) as enforceability_score,
                sum(coalesce(c.heritage_contribution_score, 0.0)) as heritage_score
            from current_field_rows c
            join main_families m using (docdb_family_id)
            join read_parquet('{owner_bridge}') ob using (docdb_family_id)
                group by
                    ob.owner_name_harmonized,
                    date '{snapshot_date}',
                    c.wipo_industry_code
            ) to '{out_portfolio_field_ts}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_portfolio_field_ts)

    if "portfolio" in selected_sections:
        con.execute(
            f"""
            copy (
                with main_families as ({main_families_sql}),
                family_current as (
                select
                    s.docdb_family_id,
                    s.owner_name_harmonized,
                    s.owner_name_display,
                    s.has_any_active_grant,
                    s.opposed_branch_count,
                    s.is_semantic_candidate,
                    b.family_market_threat_score_raw,
                    b.family_adjusted_citation_score_raw,
                    b.family_raw_absolute_blocking_power,
                    b.family_ui_blocking_power_score,
                    q.family_grant_publication_count
                from read_parquet('{out_family_summary}') s
                join read_parquet('{out_blocking}') b using (docdb_family_id)
                left join read_parquet('{oecd}') q using (docdb_family_id)
            ),
            owner_identity as ({owner_identity_sql}),
            crown_ranked as (
                select
                    ob.owner_name_harmonized,
                    fc.docdb_family_id,
                    fc.family_raw_absolute_blocking_power,
                    row_number() over (
                        partition by ob.owner_name_harmonized
                        order by fc.family_raw_absolute_blocking_power desc, fc.docdb_family_id
                    ) as family_rank_desc
                from family_current fc
                join read_parquet('{owner_bridge}') ob using (docdb_family_id)
                where coalesce(fc.has_any_active_grant, false)
            )
            select
                ob.owner_name_harmonized,
                oi.owner_name_display,
                date '{snapshot_date}' as snapshot_date,
                count(distinct fc.docdb_family_id) as portfolio_family_count_within_mega_cluster,
                avg(coalesce(fc.family_ui_blocking_power_score, 0.0)) as portfolio_avg_blocking_power_within_mega_cluster,
                count(distinct case when coalesce(fc.has_any_active_grant, false) then fc.docdb_family_id end) as portfolio_active_grant_family_count,
                count(distinct case when coalesce(fc.is_semantic_candidate, false) then fc.docdb_family_id end) as semantic_candidate_family_count,
                sum(case when coalesce(fc.has_any_active_grant, false) then coalesce(fc.family_raw_absolute_blocking_power, 0.0) else 0.0 end) as portfolio_total_mass_score,
                avg(case when coalesce(fc.family_ui_blocking_power_score, 0.0) >= 90.0 then 1.0 else 0.0 end) as portfolio_hit_rate_top_decile,
                sum(case when cr.family_rank_desc <= {top_n_crown_jewels} then cr.family_raw_absolute_blocking_power else 0.0 end) as portfolio_crown_jewel_index,
                avg(
                    case
                        when coalesce(fc.family_grant_publication_count, 0.0) > 0
                        then case when coalesce(fc.opposed_branch_count, 0.0) > 0 then 1.0 else 0.0 end
                        else null
                    end
                ) as portfolio_opposition_rate,
                sum(case when coalesce(fc.has_any_active_grant, false) then coalesce(fc.family_market_threat_score_raw, 0.0) else 0.0 end) as portfolio_current_threat_score,
                sum(coalesce(fc.family_adjusted_citation_score_raw, 0.0)) as portfolio_heritage_score
            from read_parquet('{owner_bridge}') ob
            join family_current fc using (docdb_family_id)
            left join owner_identity oi
              on ob.owner_name_harmonized = oi.owner_name_harmonized
            left join crown_ranked cr
              on ob.owner_name_harmonized = cr.owner_name_harmonized
             and fc.docdb_family_id = cr.docdb_family_id
                group by
                    ob.owner_name_harmonized,
                    oi.owner_name_display,
                    date '{snapshot_date}'
            ) to '{out_portfolio}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_portfolio)

    if "portfolio_threat" in selected_sections:
        con.execute(
            f"""
            copy (
                with current_field_rows as (
                select *
                from read_parquet('{out_field_ts}')
                where snapshot_date = date '{snapshot_date}'
            ),
            clean_edges as (
                select *
                from read_parquet('{cite_network}')
                where coalesce(clean_edge_weight, 0.0) > 0.0
                  and cited_docdb_family_id is not null
            )
            select
                ob.owner_name_harmonized,
                date '{snapshot_date}' as snapshot_date,
                coalesce(e.citing_assignee_name, 'UNKNOWN_OWNER') as citing_assignee_name,
                cf.wipo_industry_code as wipo_field,
                sum(e.citation_lethality_score * coalesce(cf.base_fraction, 0.0)) as citation_lethality_sum,
                count(distinct cf.docdb_family_id) as collided_family_count
            from clean_edges e
            join current_field_rows cf
              on e.cited_docdb_family_id = cf.docdb_family_id
            join read_parquet('{owner_bridge}') ob
              on cf.docdb_family_id = ob.docdb_family_id
                group by
                    ob.owner_name_harmonized,
                    date '{snapshot_date}',
                    coalesce(e.citing_assignee_name, 'UNKNOWN_OWNER'),
                    cf.wipo_industry_code
            ) to '{out_portfolio_threat}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_portfolio_threat)

    if "market_segments" in selected_sections:
        con.execute(f"copy (select * from read_parquet('{market_seg}')) to '{out_market_segments}' (format parquet, compression zstd)")
        built_outputs.append(out_market_segments)
    if "market_timeseries" in selected_sections:
        con.execute(f"copy (select * from read_parquet('{market_ts}')) to '{out_market_timeseries}' (format parquet, compression zstd)")
        built_outputs.append(out_market_timeseries)
    if "market_overview" in selected_sections:
        con.execute(
            f"""
            copy (
                select
                    count(*) as segment_count,
                    sum(case when market_state = 'rising' then 1 else 0 end) as rising_segment_count,
                    sum(case when market_state = 'cooling' then 1 else 0 end) as cooling_segment_count,
                    sum(total_family_count) as total_family_count,
                    avg(total_family_count) as avg_segment_family_count
                from read_parquet('{market_seg}')
            ) to '{out_market_overview}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_market_overview)

    market_citation_sections = {
        "market_citation_trend",
        "market_citation_jurisdiction",
        "market_citation_attacker",
    }
    if market_citation_sections & selected_sections:
        con.execute("set threads=2")
        base_chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_market_citation_base")
        for stale in base_chunk_dir.glob("market_citation_base_*.parquet"):
            stale.unlink()

        year_rows = con.execute(
            f"""
            select distinct cast(citation_year as integer) as citation_year
            from read_parquet('{cite_network}')
            where cited_docdb_family_id is not null
              and coalesce(clean_edge_weight, 0.0) > 0.0
              and cast(coalesce(citation_year, 0) as integer) between 1900 and {snapshot_year}
              and not coalesce(is_out_of_bounds, false)
              and not coalesce(is_intra_family_citation, false)
            order by 1
            """
        ).fetchall()
        for (citation_year,) in year_rows:
            chunk_path = base_chunk_dir / f"market_citation_base_{int(citation_year)}.parquet"
            con.execute(
                f"""
                copy (
                    with field_bridge as (
                        select
                            docdb_family_id,
                            u.wipo_field as wipo_industry_code,
                            cast(
                                coalesce(
                                    family_field_fraction,
                                    case
                                        when coalesce(family_tech_breadth_wipo_count, 0) <= 0 then 1.0
                                        else 1.0 / cast(family_tech_breadth_wipo_count as double)
                                    end
                                ) as double
                            ) as field_fraction
                        from read_parquet('{fields}') f,
                             unnest(f.covered_wipo_fields) as u(wipo_field)
                    )
                    select
                        cast(coalesce(e.citation_year, 0) as integer) as as_of_year,
                        fb.wipo_industry_code,
                        coalesce(e.citing_assignee_name, 'UNKNOWN_OWNER') as citing_assignee_name,
                        coalesce(e.citing_jurisdiction_code, '') as jurisdiction_code,
                        cast(coalesce(e.clean_edge_weight, 0.0) * coalesce(fb.field_fraction, 1.0) as double) as citation_count,
                        cast(coalesce(e.citation_lethality_score, 0.0) * coalesce(fb.field_fraction, 1.0) as double) as citation_lethality_sum_raw,
                        '{settings.method_version}' as method_version
                    from read_parquet('{cite_network}') e
                    join field_bridge fb
                      on e.cited_docdb_family_id = fb.docdb_family_id
                    where cast(coalesce(e.citation_year, 0) as integer) = {int(citation_year)}
                      and cast(coalesce(e.citation_year, 0) as integer) between 1900 and {snapshot_year}
                      and e.cited_docdb_family_id is not null
                      and coalesce(e.clean_edge_weight, 0.0) > 0.0
                      and not coalesce(e.is_out_of_bounds, false)
                      and not coalesce(e.is_intra_family_citation, false)
                ) to '{chunk_path}' (format parquet, compression zstd)
                """
            )

        if "market_citation_trend" in selected_sections:
            trend_chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_market_citation_trend_pit")
            for stale in trend_chunk_dir.glob("market_citation_trend_*.parquet"):
                stale.unlink()
            for (citation_year,) in year_rows:
                base_chunk_path = base_chunk_dir / f"market_citation_base_{int(citation_year)}.parquet"
                trend_chunk_path = trend_chunk_dir / f"market_citation_trend_{int(citation_year)}.parquet"
                con.execute(
                    f"""
                    copy (
                        select
                            as_of_year,
                            wipo_industry_code,
                            count(*) as citation_event_count,
                            cast(coalesce(sum(citation_count), 0.0) as double) as citation_count,
                            cast(coalesce(sum(citation_lethality_sum_raw), 0.0) as double) as citation_lethality_sum_raw,
                            count(distinct case when trim(coalesce(citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED') then citing_assignee_name end) as distinct_citing_assignee_count,
                            count(distinct case when trim(coalesce(jurisdiction_code, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED') then jurisdiction_code end) as distinct_citing_jurisdiction_count,
                            max(method_version) as method_version
                        from read_parquet('{base_chunk_path}')
                        group by as_of_year, wipo_industry_code
                    ) to '{trend_chunk_path}' (format parquet, compression zstd)
                    """
                )
            if out_market_citation_trend.exists():
                out_market_citation_trend.unlink()
            con.execute(
                f"""
                copy (
                    with base as (
                        select *
                        from read_parquet('{trend_chunk_dir / 'market_citation_trend_*.parquet'}')
                    ),
                    lagged as (
                        select
                            b.*,
                            lag(citation_count) over (
                                partition by wipo_industry_code
                                order by as_of_year
                            ) as prior_citation_count
                        from base b
                    )
                    select
                        l.as_of_year,
                        l.wipo_industry_code,
                        l.citation_event_count,
                        l.citation_count,
                        l.citation_lethality_sum_raw,
                        l.distinct_citing_assignee_count,
                        l.distinct_citing_jurisdiction_count,
                        percent_rank() over (
                            partition by l.as_of_year
                            order by l.citation_lethality_sum_raw, l.wipo_industry_code
                        ) * 100.0 as citation_pressure_index,
                        case
                            when l.prior_citation_count is null then
                                coalesce(
                                    case
                                        when coalesce(mts.market_state_ui_safe, false) then mts.market_state
                                        else null
                                    end,
                                    'stable'
                                )
                            when l.prior_citation_count <= 0 and l.citation_count > 0 then 'heating'
                            when l.citation_count > l.prior_citation_count * 1.05 then 'heating'
                            when l.citation_count < l.prior_citation_count * 0.95 then 'cooling'
                            else 'stable'
                        end as market_citation_state,
                        coalesce(
                            case
                                when coalesce(mts.market_state_ui_safe, false) then mts.market_state
                                else null
                            end,
                            'stable'
                        ) as market_state_reference,
                        true as historical_citation_safe,
                        false as historical_classification_truth_supported,
                        l.method_version
                    from lagged l
                    left join read_parquet('{market_ts}') mts
                      on l.as_of_year = cast(mts.family_priority_year as integer)
                     and l.wipo_industry_code = mts.wipo_industry_code
                ) to '{out_market_citation_trend}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_market_citation_trend)

        if "market_citation_jurisdiction" in selected_sections:
            jurisdiction_chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_market_citation_jurisdiction_pit")
            for stale in jurisdiction_chunk_dir.glob("market_citation_jurisdiction_*.parquet"):
                stale.unlink()
            for (citation_year,) in year_rows:
                base_chunk_path = base_chunk_dir / f"market_citation_base_{int(citation_year)}.parquet"
                jurisdiction_chunk_path = jurisdiction_chunk_dir / f"market_citation_jurisdiction_{int(citation_year)}.parquet"
                con.execute(
                    f"""
                    copy (
                        select
                            as_of_year,
                            wipo_industry_code,
                            jurisdiction_code,
                            count(*) as citation_event_count,
                            count(distinct case when trim(coalesce(citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED') then citing_assignee_name end) as distinct_citing_assignee_count,
                            cast(coalesce(sum(citation_count), 0.0) as double) as citation_count,
                            cast(coalesce(sum(citation_lethality_sum_raw), 0.0) as double) as citation_lethality_sum_raw,
                            max(method_version) as method_version
                        from read_parquet('{base_chunk_path}')
                        where trim(coalesce(jurisdiction_code, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                        group by as_of_year, wipo_industry_code, jurisdiction_code
                    ) to '{jurisdiction_chunk_path}' (format parquet, compression zstd)
                    """
                )
            if out_market_citation_jurisdiction.exists():
                out_market_citation_jurisdiction.unlink()
            con.execute(
                f"""
                copy (
                    select
                        as_of_year,
                        wipo_industry_code,
                        jurisdiction_code,
                        citation_event_count,
                        distinct_citing_assignee_count,
                        citation_count,
                        citation_lethality_sum_raw,
                        percent_rank() over (
                            partition by as_of_year, wipo_industry_code
                            order by citation_lethality_sum_raw, jurisdiction_code
                        ) * 100.0 as citation_pressure_index,
                        method_version
                    from read_parquet('{jurisdiction_chunk_dir / 'market_citation_jurisdiction_*.parquet'}')
                ) to '{out_market_citation_jurisdiction}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_market_citation_jurisdiction)

        if "market_citation_attacker" in selected_sections:
            attacker_chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_market_attacker_leaderboard_pit")
            for stale in attacker_chunk_dir.glob("market_citation_attacker_*.parquet"):
                stale.unlink()
            for (citation_year,) in year_rows:
                base_chunk_path = base_chunk_dir / f"market_citation_base_{int(citation_year)}.parquet"
                attacker_chunk_path = attacker_chunk_dir / f"market_citation_attacker_{int(citation_year)}.parquet"
                con.execute(
                    f"""
                    copy (
                        select
                            as_of_year,
                            wipo_industry_code,
                            citing_assignee_name,
                            count(*) as citation_event_count,
                            count(distinct case when trim(coalesce(jurisdiction_code, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED') then jurisdiction_code end) as distinct_citing_jurisdiction_count,
                            cast(coalesce(sum(citation_count), 0.0) as double) as citation_count,
                            cast(coalesce(sum(citation_lethality_sum_raw), 0.0) as double) as citation_lethality_sum_raw,
                            max(method_version) as method_version
                        from read_parquet('{base_chunk_path}')
                        where trim(coalesce(citing_assignee_name, '')) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                        group by as_of_year, wipo_industry_code, citing_assignee_name
                    ) to '{attacker_chunk_path}' (format parquet, compression zstd)
                    """
                )
            if out_market_citation_attacker.exists():
                out_market_citation_attacker.unlink()
            con.execute(
                f"""
                copy (
                    select
                        as_of_year,
                        wipo_industry_code,
                        citing_assignee_name,
                        citation_event_count,
                        distinct_citing_jurisdiction_count,
                        citation_count,
                        citation_lethality_sum_raw,
                        percent_rank() over (
                            partition by as_of_year, wipo_industry_code
                            order by citation_lethality_sum_raw, citing_assignee_name
                        ) * 100.0 as attacker_pressure_index,
                        method_version
                    from read_parquet('{attacker_chunk_dir / 'market_citation_attacker_*.parquet'}')
                ) to '{out_market_citation_attacker}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_market_citation_attacker)

    if "semantic" in selected_sections:
        con.execute(
            f"""
            copy (
                select
                    s.docdb_family_id,
                    fs.owner_name_harmonized,
                    fs.owner_name_display,
                    s.representative_stage,
                    s.representative_source_type,
                    s.text_provenance,
                    s.is_abstract_fallback,
                    e.is_semantic_candidate,
                    e.is_in_vector_sample,
                    f.covered_wipo_fields,
                    b.family_ui_blocking_power_score,
                    q.oecd_quality_percentile
                from read_parquet('{semantic_rep}') s
                join read_parquet('{semantic_elig}') e using (docdb_family_id)
                left join read_parquet('{fields}') f using (docdb_family_id)
                left join read_parquet('{out_family_summary}') fs using (docdb_family_id)
                left join read_parquet('{out_blocking}') b using (docdb_family_id)
                left join read_parquet('{oecd}') q using (docdb_family_id)
            ) to '{out_semantic}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_semantic)

    if "family_heritage" in selected_sections:
        con.execute(
            f"""
            copy (
                with main_families as ({main_families_sql})
                select
                    c.docdb_family_id,
                    c.family_earliest_priority_date,
                    c.family_priority_year,
                    c.is_main_window_family,
                    c.is_heritage_backfill_family,
                    o.owner_name_harmonized,
                    o.owner_name_display,
                    f.covered_wipo_fields,
                    coalesce(x.family_adjusted_citation_score_raw, 0.0) as family_heritage_score,
                    coalesce(x.raw_family_citation_count, 0) as raw_family_citation_count,
                    coalesce(x.out_of_bounds_citation_share, 0.0) as out_of_bounds_citation_share,
                    '{settings.scope_type}' as scope_type,
                    date '{snapshot_date}' as snapshot_date
                from read_parquet('{family_core}') c
                left join read_parquet('{owner_primary}') o using (docdb_family_id)
                left join read_parquet('{fields}') f using (docdb_family_id)
                left join read_parquet('{cite}') x using (docdb_family_id)
                where not coalesce(c.is_out_of_bounds_ghost, false)
            ) to '{out_family_heritage}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_family_heritage)

    if "portfolio_heritage" in selected_sections:
        con.execute(
            f"""
            copy (
                with owner_identity as ({owner_identity_sql})
                select
                    ob.owner_name_harmonized,
                    oi.owner_name_display,
                    date '{snapshot_date}' as snapshot_date,
                    count(distinct fh.docdb_family_id) as portfolio_family_count_heritage_scope,
                    sum(fh.family_heritage_score) as portfolio_total_heritage_score,
                    avg(fh.family_heritage_score) as portfolio_avg_heritage_score,
                    sum(case when coalesce(fh.is_heritage_backfill_family, false) then 1 else 0 end) as heritage_backfill_family_count,
                    sum(case when coalesce(fh.is_main_window_family, false) then 1 else 0 end) as main_window_family_count,
                    '{settings.scope_type}' as scope_type
                from read_parquet('{out_family_heritage}') fh
                join read_parquet('{owner_bridge}') ob using (docdb_family_id)
                left join owner_identity oi
                  on ob.owner_name_harmonized = oi.owner_name_harmonized
                group by
                    ob.owner_name_harmonized,
                    oi.owner_name_display,
                    date '{snapshot_date}'
            ) to '{out_portfolio_heritage}' (format parquet, compression zstd)
            """
        )
        built_outputs.append(out_portfolio_heritage)

    if "portfolio_forecast" in selected_sections:
        derived_outputs = _build_portfolio_forecast_from_models(
            settings,
            out_portfolio=out_portfolio,
            out_portfolio_field_ts=out_portfolio_field_ts,
            out_portfolio_compare_pit=settings.gold_dir / "gold_portfolio_compare_pit.parquet",
            out_portfolio_forecast=out_portfolio_forecast,
            out_portfolio_forecast_segments=out_portfolio_forecast_segments,
            out_portfolio_forecast_contributors=out_portfolio_forecast_contributors,
            result=result,
        )
        if derived_outputs:
            built_outputs.extend(derived_outputs)
        else:
            con.execute(
                f"""
                copy (
                    select
                        owner_name_harmonized,
                        owner_name_display,
                        snapshot_date,
                        portfolio_family_count_within_mega_cluster,
                        portfolio_avg_blocking_power_within_mega_cluster,
                        portfolio_active_grant_family_count,
                        semantic_candidate_family_count,
                        portfolio_total_mass_score,
                        portfolio_hit_rate_top_decile,
                        portfolio_crown_jewel_index,
                        portfolio_opposition_rate,
                        portfolio_current_threat_score,
                        portfolio_heritage_score,
                        portfolio_total_mass_score as forecast_proxy_score
                    from read_parquet('{out_portfolio}')
                ) to '{out_portfolio_forecast}' (format parquet, compression zstd)
                """
            )
            built_outputs.append(out_portfolio_forecast)

    for output in built_outputs:
        result.outputs.append(str(output))
        result.metrics[f"{output.stem}_rows"] = parquet_row_count(output)
    return result


def build_gold_family_core(settings: BuildSettings) -> StageResult:
    return _build_gold_selected(
        settings,
        stage_name="gold-family-core",
        summary="Built Gold family-facing current-state marts from note-aligned Silver contracts.",
        selected_sections={"family_summary", "blocking", "family_heritage", "attacker"},
    )


def build_gold_family_compare_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-family-compare-pit",
        status="success",
        summary="Built the family compare PIT serving mart from the audited family PIT core and current summary metadata.",
        methods=[
            "Used only observed point-in-time family rows for historical compare serving.",
            "Kept current owner, field, and OECD metadata explicitly labeled as current-only side metadata.",
            "Materialized one row per family and observed year with a latest-observed-year flag for compare and report flows.",
        ],
        calculations=[
            "Family active-jurisdiction share is recomputed from point-in-time jurisdiction counts.",
            "Historical-safe metrics come from the PIT core rather than current-state summary marts.",
        ],
        downstream_impacts=[
            "This mart is the safe family-level source for historical compare, time-slice report sections, and year-aware family evidence payloads.",
        ],
        doc_refs=[
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md",
            "docs/next-phase-v2/38-patentiq-v2-report-generation-use-cases-and-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)

    pit_dense = settings.silver_dir / DENSE_OUTPUT_TABLE
    pit = pit_dense if pit_dense.exists() else settings.silver_dir / OUTPUT_TABLE
    family_summary = settings.gold_dir / "gold_family_summary.parquet"
    out_family_compare_pit = settings.gold_dir / "gold_family_compare_pit.parquet"
    tmp_out_family_compare_pit = settings.gold_dir / "tmp_gold_family_compare_pit.parquet"
    if pit == pit_dense:
        result.methods.insert(0, "Consumed the dense family-year PIT layer for multi-year historical compare behavior.")
    else:
        result.warnings.append(
            "Dense family-year PIT layer not found; gold_family_compare_pit fell back to anchored family PIT."
        )

    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_family_compare_pit")
    latest_observed_year_path = chunk_dir / "family_compare_latest_observed_year.parquet"
    latest_observed_year_path.unlink(missing_ok=True)
    con.execute(
        f"""
        copy (
            select
                docdb_family_id,
                max(cast(as_of_year as integer)) as latest_as_of_year
            from read_parquet('{pit}')
            where coalesce(is_observed_as_of_snapshot, false)
            group by 1
        ) to '{latest_observed_year_path}' (format parquet, compression zstd)
        """
    )

    year_rows = con.execute(
        f"""
        select distinct cast(as_of_year as integer) as as_of_year
        from read_parquet('{pit}')
        where coalesce(is_observed_as_of_snapshot, false)
        order by 1
        """
    ).fetchall()
    chunk_paths: list[str] = []
    for (as_of_year,) in year_rows:
        chunk_path = chunk_dir / f"family_compare_pit_{int(as_of_year)}.parquet"
        chunk_path.unlink(missing_ok=True)
        con.execute(
            f"""
            copy (
                with current_family as (
                    select
                        docdb_family_id,
                        owner_name_harmonized as owner_name_harmonized_current,
                        owner_name_display as owner_name_display_current,
                        primary_wipo_field as primary_wipo_field_current,
                        covered_wipo_fields as covered_wipo_fields_current,
                        oecd_quality_percentile as oecd_quality_percentile_current,
                        snapshot_date as current_snapshot_date
                    from read_parquet('{family_summary}')
                )
                select
                    p.docdb_family_id,
                    cast(p.as_of_date as date) as as_of_date,
                    cast(p.as_of_year as integer) as as_of_year,
                    cast(p.is_observed_as_of_snapshot as boolean) as is_observed_as_of_snapshot,
                    cast(cast(p.as_of_year as integer) = loy.latest_as_of_year as boolean) as is_latest_observed_year,
                    cast(cf.current_snapshot_date as date) as current_snapshot_date,
                    cf.owner_name_harmonized_current,
                    cf.owner_name_display_current,
                    cf.primary_wipo_field_current,
                    cf.covered_wipo_fields_current,
                    cast(cf.oecd_quality_percentile_current as double) as oecd_quality_percentile_current,
                    p.family_composite_status_asof,
                    cast(p.active_jurisdiction_count_asof as double) as active_jurisdiction_count_asof,
                    cast(p.active_grant_branch_count_asof as double) as active_grant_branch_count_asof,
                    cast(p.lapsed_jurisdiction_count_asof as double) as lapsed_jurisdiction_count_asof,
                    cast(p.family_jurisdiction_count_asof as double) as family_jurisdiction_count_asof,
                    case
                        when coalesce(p.family_jurisdiction_count_asof, 0) = 0 then 0.0
                        else cast(p.active_jurisdiction_count_asof as double) / cast(p.family_jurisdiction_count_asof as double)
                    end as family_active_jurisdiction_share_asof,
                    cast(p.family_coverage_stability_score_asof as double) as family_coverage_stability_score_asof,
                    cast(p.family_size_docdb_asof as double) as family_size_docdb_asof,
                    cast(p.family_tech_breadth_wipo_count_asof as double) as family_tech_breadth_wipo_count_asof,
                    cast(p.family_blocking_power_score_asof as double) as family_blocking_power_score_asof,
                    cast(p.family_enforceability_score_asof as double) as family_enforceability_score_asof,
                    cast(p.family_field_contribution_primary_asof as double) as family_field_contribution_primary_asof,
                    cast(p.pre_asof_forward_citations_clean as double) as pre_asof_forward_citations_clean,
                    cast(p.pre_asof_forward_citations_weighted as double) as pre_asof_forward_citations_weighted,
                    cast(p.family_rcf_score_asof as double) as family_rcf_score_asof,
                    cast(p.pre_asof_unique_citing_family_count as double) as pre_asof_unique_citing_family_count,
                    cast(p.pre_asof_citing_assignee_diversity as double) as pre_asof_citing_assignee_diversity,
                    cast(p.pre_asof_attacker_density_score as double) as pre_asof_attacker_density_score,
                    cast(p.data_completeness_pct_asof as double) as data_completeness_pct_asof,
                    true as historical_compare_safe,
                    false as historical_oecd_supported,
                    false as historical_owner_truth_supported,
                    true as current_owner_metadata_only
                from read_parquet('{pit}') p
                left join read_parquet('{latest_observed_year_path}') loy using (docdb_family_id)
                left join current_family cf using (docdb_family_id)
                where
                    coalesce(p.is_observed_as_of_snapshot, false)
                    and cast(p.as_of_year as integer) = {int(as_of_year)}
            ) to '{chunk_path}' (format parquet, compression zstd)
            """
        )
        chunk_paths.append(str(chunk_path))

    tmp_out_family_compare_pit.unlink(missing_ok=True)
    out_family_compare_pit.unlink(missing_ok=True)
    con.execute(
        f"""
        copy (
            select * from read_parquet([{", ".join(repr(path) for path in chunk_paths)}], union_by_name=true)
        ) to '{tmp_out_family_compare_pit}' (format parquet, compression zstd)
        """
    )
    tmp_out_family_compare_pit.replace(out_family_compare_pit)
    result.outputs.append(str(out_family_compare_pit))
    result.metrics[f"{out_family_compare_pit.stem}_rows"] = parquet_row_count(out_family_compare_pit)
    return result


def build_gold_family_classification_mix_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-family-classification-mix-pit",
        status="success",
        summary="Built the family classification PIT summary mart from the dense family-year classification backbone.",
        methods=[
            "Started from silver_family_classification_pit_dense so the mart stays aligned with the dense family-year PIT grain.",
            "Kept reusable WIPO and CPC arrays for UI drill-down while materializing summary fields for family cards and compare views.",
            "Made the stable classification replay policy explicit instead of implying dated code-mutation truth.",
        ],
        calculations=[
            "Classification concentration HHI uses equal-share membership across CPC main groups in the first stable-replay implementation.",
            "Classification entropy uses the natural log of the CPC main-group count under the same equal-share assumption.",
            "Classification breadth band is derived from CPC main-group count: unknown, focused, balanced, diversified.",
        ],
        downstream_impacts=[
            "This mart is the family-level classification source for chronological CPC/WIPO UI sections and later portfolio and market classification rollups.",
        ],
        doc_refs=[
            "docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md",
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_family_classification_mix_pit")
    con.execute(f"set temp_directory='{temp_dir}'")

    classification_dense = settings.silver_dir / CLASSIFICATION_DENSE_OUTPUT_TABLE
    out_family_classification_mix_pit = settings.gold_dir / "gold_family_classification_mix_pit.parquet"
    if not classification_dense.exists():
        result.status = "failed"
        result.warnings.append(
            f"Missing required input for gold-family-classification-mix-pit: {classification_dense}"
        )
        return result

    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_family_classification_mix_pit")
    for stale in chunk_dir.glob("family_classification_mix_pit_*.parquet"):
        stale.unlink()

    year_rows = con.execute(
        f"""
        select distinct as_of_year
        from read_parquet('{classification_dense}')
        where coalesce(is_observed_as_of_snapshot, false)
        order by 1
        """
    ).fetchall()
    for (as_of_year,) in year_rows:
        chunk_path = chunk_dir / f"family_classification_mix_pit_{int(as_of_year)}.parquet"
        con.execute(
            f"""
            copy (
                with base as (
                    select *
                    from read_parquet('{classification_dense}')
                    where coalesce(is_observed_as_of_snapshot, false)
                      and as_of_year = {int(as_of_year)}
                )
                select
                    docdb_family_id,
                    cast(as_of_date as date) as as_of_date,
                    cast(as_of_year as integer) as as_of_year,
                    cast(is_observed_as_of_snapshot as boolean) as is_observed_as_of_snapshot,
                    cast(is_partial_snapshot_year as boolean) as is_partial_snapshot_year,
                    covered_wipo_fields_asof,
                    primary_wipo_field_asof,
                    cast(wipo_field_count_asof as double) as wipo_field_count_asof,
                    ipc_subclasses_asof,
                    cpc_sections_asof,
                    cpc_subclasses_asof,
                    cpc_main_groups_asof,
                    cast(ipc_subclass_count_asof as double) as ipc_subclass_count_asof,
                    cast(cpc_section_count_asof as double) as cpc_section_count_asof,
                    cast(cpc_subclass_count_asof as double) as cpc_subclass_count_asof,
                    cast(cpc_main_group_count_asof as double) as cpc_main_group_count_asof,
                    case
                        when coalesce(cpc_main_group_count_asof, 0) <= 0 then null
                        else 1.0 / cast(cpc_main_group_count_asof as double)
                    end as classification_concentration_hhi_asof,
                    case
                        when coalesce(cpc_main_group_count_asof, 0) <= 0 then null
                        else ln(cast(cpc_main_group_count_asof as double))
                    end as classification_entropy_asof,
                    list_extract(cpc_main_groups_asof, 1) as top_cpc_main_group_asof,
                    case
                        when coalesce(cpc_main_group_count_asof, 0) <= 0 then null
                        else 1.0 / cast(cpc_main_group_count_asof as double)
                    end as top_cpc_main_group_share_asof,
                    case
                        when coalesce(cpc_main_group_count_asof, 0) <= 0 then 'unknown'
                        when cpc_main_group_count_asof = 1 then 'focused'
                        when cpc_main_group_count_asof <= 3 then 'balanced'
                        else 'diversified'
                    end as classification_breadth_band_asof,
                    classification_visibility_policy,
                    cast(classification_membership_replayed_to_history as boolean) as classification_membership_replayed_to_history,
                    cast(historical_classification_truth_supported as boolean) as historical_classification_truth_supported,
                    true as historical_compare_safe
                from base
                order by docdb_family_id, as_of_year
            ) to '{chunk_path}' (format parquet, compression zstd)
            """
        )

    if out_family_classification_mix_pit.exists():
        out_family_classification_mix_pit.unlink()
    con.execute(
        f"""
        copy (
            select *
            from read_parquet('{chunk_dir / 'family_classification_mix_pit_*.parquet'}')
        ) to '{out_family_classification_mix_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_family_classification_mix_pit))
    result.metrics[f"{out_family_classification_mix_pit.stem}_rows"] = parquet_row_count(out_family_classification_mix_pit)
    return result


def build_gold_family_classification_jurisdiction_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-family-classification-jurisdiction-pit",
        status="success",
        summary="Built the family WIPO-CPC-jurisdiction PIT mart from classification replay and dense branch history.",
        methods=[
            "Started from the family classification mix PIT and joined dense branch-year replay so technology and jurisdiction slices stay aligned to the same family-year grain.",
            "Exploded WIPO-field and CPC-main-group membership into one row per family, year, field, CPC, and jurisdiction slice.",
            "Kept replay caveats explicit by preserving classification-history support flags instead of implying dated code-mutation truth.",
        ],
        calculations=[
            "Jurisdiction support level reuses the current office support policy map and defaults to limited where no explicit support policy exists.",
            "Active status is read from the branch-history replay for the same family, jurisdiction, and year.",
            "Blocking, enforceability, and pre-as-of citation columns are carried from the family compare PIT for the same family-year.",
        ],
        downstream_impacts=[
            "This mart is the ranking-ready family evidence layer for WIPO x CPC x jurisdiction chronology and downstream portfolio and market slice rollups.",
        ],
        doc_refs=[
            "docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md",
            "docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md",
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_family_classification_jurisdiction_pit")
    con.execute(f"set temp_directory='{temp_dir}'")

    family_classification_mix = settings.gold_dir / "gold_family_classification_mix_pit.parquet"
    family_compare_pit = settings.gold_dir / "gold_family_compare_pit.parquet"
    branch_history_dense = settings.silver_dir / "silver_branch_status_history_dense.parquet"
    out_family_classification_jurisdiction_pit = (
        settings.gold_dir / "gold_family_classification_jurisdiction_pit.parquet"
    )
    if not family_classification_mix.exists() or not family_compare_pit.exists() or not branch_history_dense.exists():
        missing = [
            str(path)
            for path in (family_classification_mix, family_compare_pit, branch_history_dense)
            if not path.exists()
        ]
        result.status = "failed"
        result.warnings.append(
            f"Missing required inputs for gold-family-classification-jurisdiction-pit: {missing}"
        )
        return result

    support_map: dict[str, str] = {}
    release_decision_path = _model_artifact_paths(settings)["phase04_release_decision"]
    if release_decision_path.exists():
        support_map = _phase04_support_level_map(release_decision_path)
    support_case = _sql_support_level_case("b.jurisdiction_code", support_map)

    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_family_classification_jurisdiction_pit")

    year_rows = con.execute(
        f"""
        select distinct as_of_year
        from read_parquet('{family_classification_mix}')
        where coalesce(is_observed_as_of_snapshot, false)
          and coalesce(wipo_field_count_asof, 0) > 0
          and coalesce(cpc_main_group_count_asof, 0) > 0
        order by 1
        """
    ).fetchall()
    for (as_of_year,) in year_rows:
        con.execute(
            f"""
            create or replace temp table gold_family_classification_jur_year_base as
            select
                fcm.docdb_family_id,
                cast(fcm.as_of_date as date) as as_of_date,
                cast(fcm.as_of_year as integer) as as_of_year,
                cast(fcp.current_snapshot_date as date) as current_snapshot_date,
                coalesce(fcp.family_blocking_power_score_asof, 0.0) as family_blocking_power_score_asof,
                coalesce(fcp.family_enforceability_score_asof, 0.0) as family_enforceability_score_asof,
                coalesce(fcp.pre_asof_forward_citations_clean, 0.0) as pre_asof_forward_citations_clean,
                fcm.classification_visibility_policy,
                cast(coalesce(fcm.classification_membership_replayed_to_history, false) as boolean) as classification_membership_replayed_to_history,
                cast(coalesce(fcm.historical_classification_truth_supported, false) as boolean) as historical_classification_truth_supported,
                cast(coalesce(fcm.historical_compare_safe, false) as boolean) as historical_compare_safe,
                fcm.covered_wipo_fields_asof,
                fcm.cpc_main_groups_asof
            from read_parquet('{family_classification_mix}') fcm
            join read_parquet('{family_compare_pit}') fcp
              on fcm.docdb_family_id = fcp.docdb_family_id
             and fcm.as_of_year = fcp.as_of_year
            where coalesce(fcm.is_observed_as_of_snapshot, false)
              and fcm.as_of_year = {int(as_of_year)}
              and coalesce(fcm.wipo_field_count_asof, 0) > 0
              and coalesce(fcm.cpc_main_group_count_asof, 0) > 0
            """
        )
        con.execute(
            f"""
            create or replace temp table gold_family_classification_jur_branch_year as
            select
                b.docdb_family_id,
                b.jurisdiction_code,
                b.source_auth,
                cast(coalesce(b.is_up_unrolled, false) as boolean) as is_up_unrolled,
                cast(coalesce(b.is_classic_validation, false) as boolean) as is_classic_validation,
                cast(coalesce(b.is_global_member, false) as boolean) as is_global_member,
                b.replay_branch_state,
                cast(coalesce(b.active_branch_flag, false) as boolean) as is_active_asof
            from read_parquet('{branch_history_dense}') b
            join (
                select distinct docdb_family_id
                from gold_family_classification_jur_year_base
            ) fy using (docdb_family_id)
            where b.snapshot_year = {int(as_of_year)}
            """
        )
        for bucket_id in range(CLASSIFICATION_JURISDICTION_BUCKET_COUNT):
            chunk_path = (
                chunk_dir
                / f"family_classification_jurisdiction_pit_{int(as_of_year)}_b{bucket_id:02d}.parquet"
            )
            if chunk_path.exists() and chunk_path.stat().st_size > 0:
                try:
                    con.execute(f"select count(*) from read_parquet('{chunk_path}')").fetchone()
                    continue
                except duckdb.Error:
                    chunk_path.unlink(missing_ok=True)
            con.execute(
                f"""
                copy (
                    with base as (
                        select
                            fyb.docdb_family_id,
                            fyb.as_of_date,
                            fyb.as_of_year,
                            fyb.current_snapshot_date,
                            b.jurisdiction_code,
                            b.source_auth,
                            cast(coalesce(b.is_up_unrolled, false) as boolean) as is_up_unrolled,
                            cast(coalesce(b.is_classic_validation, false) as boolean) as is_classic_validation,
                            cast(coalesce(b.is_global_member, false) as boolean) as is_global_member,
                            b.replay_branch_state,
                            cast(coalesce(b.is_active_asof, false) as boolean) as is_active_asof,
                            fyb.family_blocking_power_score_asof,
                            fyb.family_enforceability_score_asof,
                            fyb.pre_asof_forward_citations_clean,
                            {support_case} as classification_jurisdiction_support_level,
                            fyb.classification_visibility_policy,
                            fyb.classification_membership_replayed_to_history,
                            fyb.historical_classification_truth_supported,
                            fyb.historical_compare_safe,
                            w.wipo_field,
                            c.cpc_main_group
                        from gold_family_classification_jur_year_base fyb
                        join gold_family_classification_jur_branch_year b
                          on fyb.docdb_family_id = b.docdb_family_id
                        cross join unnest(fyb.covered_wipo_fields_asof) as w(wipo_field)
                        cross join unnest(fyb.cpc_main_groups_asof) as c(cpc_main_group)
                        where mod(fyb.docdb_family_id, {CLASSIFICATION_JURISDICTION_BUCKET_COUNT}) = {bucket_id}
                    )
                    select
                        docdb_family_id,
                        as_of_date,
                        as_of_year,
                        current_snapshot_date,
                        wipo_field,
                        cpc_main_group,
                        jurisdiction_code,
                        source_auth,
                        is_up_unrolled,
                        is_classic_validation,
                        is_global_member,
                        replay_branch_state,
                        is_active_asof,
                        cast(family_blocking_power_score_asof as double) as family_blocking_power_score_asof,
                        cast(family_enforceability_score_asof as double) as family_enforceability_score_asof,
                        cast(pre_asof_forward_citations_clean as double) as pre_asof_forward_citations_clean,
                        classification_jurisdiction_support_level,
                        classification_visibility_policy,
                        classification_membership_replayed_to_history,
                        historical_classification_truth_supported,
                        historical_compare_safe,
                        '{settings.method_version}' as method_version
                    from base
                    where trim(coalesce(wipo_field, '')) <> ''
                      and trim(coalesce(cpc_main_group, '')) <> ''
                      and trim(coalesce(jurisdiction_code, '')) <> ''
                ) to '{chunk_path}' (format parquet, compression zstd)
                """
            )

    if out_family_classification_jurisdiction_pit.exists():
        out_family_classification_jurisdiction_pit.unlink()
    con.execute(
        f"""
        copy (
            select *
            from read_parquet('{chunk_dir / 'family_classification_jurisdiction_pit_*_b*.parquet'}')
        ) to '{out_family_classification_jurisdiction_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_family_classification_jurisdiction_pit))
    result.metrics[f"{out_family_classification_jurisdiction_pit.stem}_rows"] = parquet_row_count(
        out_family_classification_jurisdiction_pit
    )
    return result


def build_gold_portfolio_classification_mix_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-portfolio-classification-mix-pit",
        status="success",
        summary="Built the portfolio classification PIT mart by aggregating family-year classification membership through the current owner bridge.",
        methods=[
            "Started from the family classification mix PIT and family compare PIT so owner-year classification rows stay aligned with historical-safe family-year context.",
            "Aggregated WIPO-field and CPC-main-group membership separately into one owner-year classification mart.",
            "Kept current-owner replay caveats explicit rather than implying true historical ownership.",
        ],
        calculations=[
            "Portfolio family share within a classification is the fraction of owner-year families carrying that classification membership.",
            "Portfolio active-family share within a classification is measured against owner-year active-family count.",
            "Classification rank within owner-year is ordered by family count, then active-family share, then code.",
        ],
        downstream_impacts=[
            "This mart supports chronological portfolio CPC/WIPO exposure, gain/loss views, and later market-classification rollups.",
        ],
        doc_refs=[
            "docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md",
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_portfolio_classification_mix_pit")
    con.execute(f"set temp_directory='{temp_dir}'")

    family_classification_mix = settings.gold_dir / "gold_family_classification_mix_pit.parquet"
    family_compare_pit = settings.gold_dir / "gold_family_compare_pit.parquet"
    owner_bridge = settings.silver_dir / "silver_family_owner_bridge.parquet"
    out_portfolio_classification_mix_pit = settings.gold_dir / "gold_portfolio_classification_mix_pit.parquet"
    if not family_classification_mix.exists() or not family_compare_pit.exists() or not owner_bridge.exists():
        missing = [
            str(path)
            for path in (family_classification_mix, family_compare_pit, owner_bridge)
            if not path.exists()
        ]
        result.status = "failed"
        result.warnings.append(
            f"Missing required inputs for gold-portfolio-classification-mix-pit: {missing}"
        )
        return result

    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_portfolio_classification_mix_pit")
    # Keep valid bucket files so late-year rebuilds can resume without replaying earlier years.
    # Invalid or zero-byte chunks are overwritten in-place below.

    year_rows = con.execute(
        f"""
        select distinct as_of_year
        from read_parquet('{family_classification_mix}')
        order by 1
        """
    ).fetchall()
    for (as_of_year,) in year_rows:
        year_chunk_paths: list[Path] = []
        for bucket_id in range(PORTFOLIO_CLASSIFICATION_BUCKET_COUNT):
            chunk_path = chunk_dir / f"portfolio_classification_mix_pit_{int(as_of_year)}_b{bucket_id:02d}.parquet"
            year_chunk_paths.append(chunk_path)
            if chunk_path.exists() and chunk_path.stat().st_size > 0:
                try:
                    con.execute(f"select count(*) from read_parquet('{chunk_path}')").fetchone()
                    continue
                except duckdb.Error:
                    chunk_path.unlink(missing_ok=True)
            con.execute(
                f"""
                copy (
                    with owner_identity as (
                        select
                            owner_name_harmonized,
                            owner_name_display
                        from (
                            select
                                owner_name_harmonized,
                                owner_name_display,
                                row_number() over (
                                    partition by owner_name_harmonized
                                    order by count(*) desc, owner_name_display asc
                                ) as display_rank
                            from read_parquet('{owner_bridge}')
                            group by owner_name_harmonized, owner_name_display
                        )
                        where display_rank = 1
                    ),
                    family_base as (
                        select
                            ob.owner_name_harmonized,
                            oi.owner_name_display as owner_name_display_current,
                            fc.docdb_family_id,
                            fc.as_of_year,
                            fc.covered_wipo_fields_asof,
                            fc.cpc_main_groups_asof,
                            fp.current_snapshot_date,
                            cast(coalesce(fp.active_jurisdiction_count_asof, 0.0) > 0 as boolean) as is_active_family_asof,
                            coalesce(fp.family_blocking_power_score_asof, 0.0) as family_blocking_power_score_asof,
                            coalesce(fp.family_enforceability_score_asof, 0.0) as family_enforceability_score_asof
                        from read_parquet('{family_classification_mix}') fc
                        join read_parquet('{owner_bridge}') ob using (docdb_family_id)
                        left join owner_identity oi using (owner_name_harmonized)
                        join read_parquet('{family_compare_pit}') fp
                          on fc.docdb_family_id = fp.docdb_family_id
                         and fc.as_of_year = fp.as_of_year
                        where fc.as_of_year = {int(as_of_year)}
                          and trim(upper(coalesce(ob.owner_name_harmonized, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                          and mod(abs(hash(ob.owner_name_harmonized)), {PORTFOLIO_CLASSIFICATION_BUCKET_COUNT}) = {bucket_id}
                    ),
                    owner_year_totals as (
                        select
                            owner_name_harmonized,
                            owner_name_display_current,
                            as_of_year,
                            max(current_snapshot_date) as current_snapshot_date,
                            count(distinct docdb_family_id) as portfolio_family_count_hist_proxy,
                            count(distinct case when is_active_family_asof then docdb_family_id end) as portfolio_active_family_count_asof
                        from family_base
                        group by owner_name_harmonized, owner_name_display_current, as_of_year
                    ),
                    wipo_rows as (
                        select
                            owner_name_harmonized,
                            owner_name_display_current,
                            as_of_year,
                            current_snapshot_date,
                            docdb_family_id,
                            is_active_family_asof,
                            family_blocking_power_score_asof,
                            family_enforceability_score_asof,
                            'WIPO_FIELD' as classification_type,
                            unnest(covered_wipo_fields_asof) as classification_code
                        from family_base
                    ),
                    cpc_rows as (
                        select
                            owner_name_harmonized,
                            owner_name_display_current,
                            as_of_year,
                            current_snapshot_date,
                            docdb_family_id,
                            is_active_family_asof,
                            family_blocking_power_score_asof,
                            family_enforceability_score_asof,
                            'CPC_MAIN_GROUP' as classification_type,
                            unnest(cpc_main_groups_asof) as classification_code
                        from family_base
                    ),
                    classification_rows as (
                        select * from wipo_rows
                        union all
                        select * from cpc_rows
                    ),
                    aggregated as (
                        select
                            c.owner_name_harmonized,
                            c.owner_name_display_current,
                            c.as_of_year,
                            max(c.current_snapshot_date) as current_snapshot_date,
                            c.classification_type,
                            c.classification_code,
                            c.classification_code as classification_label,
                            count(distinct c.docdb_family_id) as portfolio_family_count_in_classification_asof,
                            count(distinct case when c.is_active_family_asof then c.docdb_family_id end) as portfolio_active_family_count_in_classification_asof,
                            avg(c.family_blocking_power_score_asof) as portfolio_blocking_density_asof,
                            avg(c.family_enforceability_score_asof) as portfolio_enforceability_density_asof
                        from classification_rows c
                        where c.classification_code is not null
                          and c.classification_code <> ''
                        group by
                            c.owner_name_harmonized,
                            c.owner_name_display_current,
                            c.as_of_year,
                            c.classification_type,
                            c.classification_code
                    )
                    select
                        a.owner_name_harmonized,
                        a.owner_name_display_current,
                        a.as_of_year,
                        cast(a.current_snapshot_date as date) as current_snapshot_date,
                        a.classification_type,
                        a.classification_code,
                        a.classification_label,
                        cast(t.portfolio_family_count_hist_proxy as double) as portfolio_family_count_hist_proxy,
                        cast(t.portfolio_active_family_count_asof as double) as portfolio_active_family_count_asof,
                        cast(a.portfolio_family_count_in_classification_asof as double) as portfolio_family_count_in_classification_asof,
                        cast(a.portfolio_active_family_count_in_classification_asof as double) as portfolio_active_family_count_in_classification_asof,
                        case
                            when coalesce(t.portfolio_family_count_hist_proxy, 0) = 0 then null
                            else cast(a.portfolio_family_count_in_classification_asof as double) / cast(t.portfolio_family_count_hist_proxy as double)
                        end as portfolio_family_share_asof,
                        case
                            when coalesce(t.portfolio_active_family_count_asof, 0) = 0 then null
                            else cast(a.portfolio_active_family_count_in_classification_asof as double) / cast(t.portfolio_active_family_count_asof as double)
                        end as portfolio_active_family_share_asof,
                        cast(a.portfolio_blocking_density_asof as double) as portfolio_blocking_density_asof,
                        cast(a.portfolio_enforceability_density_asof as double) as portfolio_enforceability_density_asof,
                        cast(false as boolean) as historical_owner_truth_supported,
                        cast(true as boolean) as current_owner_bridge_replayed_to_history,
                        row_number() over (
                            partition by a.owner_name_harmonized, a.as_of_year, a.classification_type
                            order by a.portfolio_family_count_in_classification_asof desc,
                                     a.portfolio_active_family_count_in_classification_asof desc,
                                     a.classification_code asc
                        ) as classification_rank_within_owner_year
                    from aggregated a
                    join owner_year_totals t
                      on a.owner_name_harmonized = t.owner_name_harmonized
                     and a.as_of_year = t.as_of_year
                    order by
                        a.owner_name_harmonized,
                        a.as_of_year,
                        a.classification_type,
                        classification_rank_within_owner_year
                ) to '{chunk_path}' (format parquet, compression zstd)
                """
            )

    if out_portfolio_classification_mix_pit.exists():
        out_portfolio_classification_mix_pit.unlink()
    con.execute(
        f"""
        copy (
            select *
            from read_parquet('{chunk_dir / 'portfolio_classification_mix_pit_*.parquet'}')
        ) to '{out_portfolio_classification_mix_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_portfolio_classification_mix_pit))
    result.metrics[f"{out_portfolio_classification_mix_pit.stem}_rows"] = parquet_row_count(out_portfolio_classification_mix_pit)
    return result


def build_gold_portfolio_classification_jurisdiction_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-portfolio-classification-jurisdiction-pit",
        status="success",
        summary="Built the portfolio WIPO-CPC-jurisdiction PIT mart by replaying family slice rows through the current owner bridge.",
        methods=[
            "Started from the family classification-jurisdiction PIT mart and aggregated through the family-owner bridge at owner-year slice grain.",
            "Kept owner replay caveats explicit rather than implying native historical owner truth.",
            "Normalized citation pressure inside each owner-year so slice comparisons are readable without pretending cross-owner comparability.",
        ],
        calculations=[
            "Portfolio family share in slice is the owner-year family count in the slice divided by total owner-year family count.",
            "Portfolio citation pressure index scales slice-average pre-as-of forward citations to the strongest slice within the same owner-year.",
            "Slice rank within owner-year is ordered by family count, then active family count, then blocking density, then slice keys.",
        ],
        downstream_impacts=[
            "This mart supports portfolio classification-geography leaderboards, CPC-by-jurisdiction views, and field-cluster evidence tables.",
        ],
        doc_refs=[
            "docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md",
            "docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md",
            "docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_portfolio_classification_jurisdiction_pit")
    con.execute(f"set temp_directory='{temp_dir}'")

    family_classification_jurisdiction_pit = settings.gold_dir / "gold_family_classification_jurisdiction_pit.parquet"
    family_compare_pit = settings.gold_dir / "gold_family_compare_pit.parquet"
    owner_bridge = settings.silver_dir / "silver_family_owner_bridge.parquet"
    out_portfolio_classification_jurisdiction_pit = (
        settings.gold_dir / "gold_portfolio_classification_jurisdiction_pit.parquet"
    )
    if (
        not family_classification_jurisdiction_pit.exists()
        or not family_compare_pit.exists()
        or not owner_bridge.exists()
    ):
        missing = [
            str(path)
            for path in (family_classification_jurisdiction_pit, family_compare_pit, owner_bridge)
            if not path.exists()
        ]
        result.status = "failed"
        result.warnings.append(
            f"Missing required inputs for gold-portfolio-classification-jurisdiction-pit: {missing}"
        )
        return result

    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_portfolio_classification_jurisdiction_pit")

    year_rows = con.execute(
        f"""
        select distinct as_of_year
        from read_parquet('{family_classification_jurisdiction_pit}')
        order by 1
        """
    ).fetchall()
    for (as_of_year,) in year_rows:
        for bucket_id in range(PORTFOLIO_CLASSIFICATION_JURISDICTION_BUCKET_COUNT):
            chunk_path = chunk_dir / f"portfolio_classification_jurisdiction_pit_{int(as_of_year)}_b{bucket_id:02d}.parquet"
            if chunk_path.exists() and chunk_path.stat().st_size > 0:
                try:
                    con.execute(f"select count(*) from read_parquet('{chunk_path}')").fetchone()
                    continue
                except duckdb.Error:
                    chunk_path.unlink(missing_ok=True)
            con.execute(
                f"""
                copy (
                    with owner_identity as (
                        select
                            owner_name_harmonized,
                            owner_name_display
                        from (
                            select
                                owner_name_harmonized,
                                owner_name_display,
                                row_number() over (
                                    partition by owner_name_harmonized
                                    order by count(*) desc, owner_name_display asc
                                ) as display_rank
                            from read_parquet('{owner_bridge}')
                            group by owner_name_harmonized, owner_name_display
                        )
                        where display_rank = 1
                    ),
                    owner_year_totals as (
                        select
                            ob.owner_name_harmonized,
                            oi.owner_name_display as owner_name_display_current,
                            fcp.as_of_year,
                            max(fcp.current_snapshot_date) as current_snapshot_date,
                            count(distinct fcp.docdb_family_id) as portfolio_family_count_hist_proxy,
                            count(
                                distinct case
                                    when coalesce(fcp.active_jurisdiction_count_asof, 0.0) > 0 then fcp.docdb_family_id
                                end
                            ) as portfolio_active_family_count_asof
                        from read_parquet('{family_compare_pit}') fcp
                        join read_parquet('{owner_bridge}') ob using (docdb_family_id)
                        left join owner_identity oi using (owner_name_harmonized)
                        where fcp.as_of_year = {int(as_of_year)}
                          and trim(upper(coalesce(ob.owner_name_harmonized, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                          and mod(abs(hash(ob.owner_name_harmonized)), {PORTFOLIO_CLASSIFICATION_JURISDICTION_BUCKET_COUNT}) = {bucket_id}
                        group by ob.owner_name_harmonized, oi.owner_name_display, fcp.as_of_year
                    ),
                    family_base as (
                        select
                            ob.owner_name_harmonized,
                            oi.owner_name_display as owner_name_display_current,
                            fcj.docdb_family_id,
                            fcj.as_of_year,
                            fcj.current_snapshot_date,
                            fcj.wipo_field,
                            fcj.cpc_main_group,
                            fcj.jurisdiction_code,
                            fcj.is_active_asof,
                            fcj.family_blocking_power_score_asof,
                            fcj.family_enforceability_score_asof,
                            fcj.pre_asof_forward_citations_clean,
                            fcj.classification_jurisdiction_support_level,
                            fcj.classification_membership_replayed_to_history,
                            fcj.historical_classification_truth_supported,
                            fcj.historical_compare_safe
                        from read_parquet('{family_classification_jurisdiction_pit}') fcj
                        join read_parquet('{owner_bridge}') ob using (docdb_family_id)
                        left join owner_identity oi using (owner_name_harmonized)
                        where fcj.as_of_year = {int(as_of_year)}
                          and trim(upper(coalesce(ob.owner_name_harmonized, ''))) not in ('', '_', 'UNKNOWN', 'UNKNOWN_OWNER', 'UNASSIGNED')
                          and mod(abs(hash(ob.owner_name_harmonized)), {PORTFOLIO_CLASSIFICATION_JURISDICTION_BUCKET_COUNT}) = {bucket_id}
                    ),
                    aggregated as (
                        select
                            owner_name_harmonized,
                            owner_name_display_current,
                            as_of_year,
                            max(current_snapshot_date) as current_snapshot_date,
                            wipo_field,
                            cpc_main_group,
                            jurisdiction_code,
                            min(classification_jurisdiction_support_level) as classification_jurisdiction_support_level,
                            count(distinct docdb_family_id) as portfolio_family_count_in_slice_asof,
                            count(distinct case when is_active_asof then docdb_family_id end) as portfolio_active_family_count_in_slice_asof,
                            avg(family_blocking_power_score_asof) as portfolio_blocking_density_asof,
                            avg(family_enforceability_score_asof) as portfolio_enforceability_density_asof,
                            avg(pre_asof_forward_citations_clean) as portfolio_raw_citation_pressure_density_asof,
                            bool_and(coalesce(classification_membership_replayed_to_history, false)) as classification_membership_replayed_to_history,
                            bool_and(coalesce(historical_classification_truth_supported, false)) as historical_classification_truth_supported,
                            bool_and(coalesce(historical_compare_safe, false)) as historical_compare_safe
                        from family_base
                        group by
                            owner_name_harmonized,
                            owner_name_display_current,
                            as_of_year,
                            wipo_field,
                            cpc_main_group,
                            jurisdiction_code
                    )
                    select
                        a.owner_name_harmonized,
                        a.owner_name_display_current,
                        a.as_of_year,
                        cast(a.current_snapshot_date as date) as current_snapshot_date,
                        a.wipo_field,
                        a.cpc_main_group,
                        a.jurisdiction_code,
                        cast(t.portfolio_family_count_hist_proxy as double) as portfolio_family_count_hist_proxy,
                        cast(t.portfolio_active_family_count_asof as double) as portfolio_active_family_count_asof,
                        cast(a.portfolio_family_count_in_slice_asof as double) as portfolio_family_count_in_slice_asof,
                        cast(a.portfolio_active_family_count_in_slice_asof as double) as portfolio_active_family_count_in_slice_asof,
                        case
                            when coalesce(t.portfolio_family_count_hist_proxy, 0) = 0 then null
                            else cast(a.portfolio_family_count_in_slice_asof as double) / cast(t.portfolio_family_count_hist_proxy as double)
                        end as portfolio_family_share_in_slice_asof,
                        cast(a.portfolio_blocking_density_asof as double) as portfolio_blocking_density_asof,
                        cast(a.portfolio_enforceability_density_asof as double) as portfolio_enforceability_density_asof,
                        case
                            when coalesce(
                                max(a.portfolio_raw_citation_pressure_density_asof) over (
                                    partition by a.owner_name_harmonized, a.as_of_year
                                ),
                                0.0
                            ) <= 0 then 0.0
                            else cast(a.portfolio_raw_citation_pressure_density_asof as double)
                                 / max(a.portfolio_raw_citation_pressure_density_asof) over (
                                     partition by a.owner_name_harmonized, a.as_of_year
                                 ) * 100.0
                        end as portfolio_citation_pressure_index_asof,
                        a.classification_jurisdiction_support_level,
                        cast(false as boolean) as historical_owner_truth_supported,
                        cast(true as boolean) as current_owner_bridge_replayed_to_history,
                        cast(a.classification_membership_replayed_to_history as boolean) as classification_membership_replayed_to_history,
                        cast(a.historical_classification_truth_supported as boolean) as historical_classification_truth_supported,
                        cast(a.historical_compare_safe as boolean) as historical_compare_safe,
                        row_number() over (
                            partition by a.owner_name_harmonized, a.as_of_year
                            order by
                                a.portfolio_family_count_in_slice_asof desc,
                                a.portfolio_active_family_count_in_slice_asof desc,
                                a.portfolio_blocking_density_asof desc,
                                a.wipo_field asc,
                                a.cpc_main_group asc,
                                a.jurisdiction_code asc
                        ) as slice_rank_within_owner_year,
                        '{settings.method_version}' as method_version
                    from aggregated a
                    join owner_year_totals t
                      on a.owner_name_harmonized = t.owner_name_harmonized
                     and a.as_of_year = t.as_of_year
                    order by
                        a.owner_name_harmonized,
                        a.as_of_year,
                        slice_rank_within_owner_year
                ) to '{chunk_path}' (format parquet, compression zstd)
                """
            )

    if out_portfolio_classification_jurisdiction_pit.exists():
        out_portfolio_classification_jurisdiction_pit.unlink()
    con.execute(
        f"""
        copy (
            select *
            from read_parquet('{chunk_dir / 'portfolio_classification_jurisdiction_pit_*.parquet'}')
        ) to '{out_portfolio_classification_jurisdiction_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_portfolio_classification_jurisdiction_pit))
    result.metrics[f"{out_portfolio_classification_jurisdiction_pit.stem}_rows"] = parquet_row_count(
        out_portfolio_classification_jurisdiction_pit
    )
    return result


def build_gold_market_cpc_trend_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-market-cpc-trend-pit",
        status="success",
        summary="Built the market CPC trend PIT mart from family-year classification visibility and family compare context.",
        methods=[
            "Started from the family classification mix PIT and grouped visible CPC main groups by primary WIPO field and year.",
            "Avoided inventing a many-to-many CPC-to-WIPO mapping by using the family primary WIPO field as the market segment basis.",
            "Joined market summary PIT only for segment heat-state context, while deriving family-count denominators directly from the family-year basis.",
        ],
        calculations=[
            "CPC family share within segment is measured against the family-year segment basis, not against summed CPC memberships.",
            "CPC growth index uses prior-year family-count change within the same WIPO-field and CPC pair.",
            "CPC heat state is banded from growth: heating above 10 percent, cooling below negative 10 percent, otherwise stable.",
        ],
        downstream_impacts=[
            "This mart powers CPC drill-downs inside market WIPO segments and feeds the global CPC importance PIT layer.",
        ],
        doc_refs=[
            "docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md",
            "docs/next-phase-v2/57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md",
            "docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_market_cpc_trend_pit_v2")
    con.execute(f"set temp_directory='{temp_dir}'")

    family_classification_mix = settings.gold_dir / "gold_family_classification_mix_pit.parquet"
    family_compare_pit = settings.gold_dir / "gold_family_compare_pit.parquet"
    market_summary_pit = settings.gold_dir / "gold_market_summary_pit.parquet"
    out_market_cpc_trend_pit = settings.gold_dir / "gold_market_cpc_trend_pit.parquet"
    if not family_classification_mix.exists() or not family_compare_pit.exists() or not market_summary_pit.exists():
        missing = [
            str(path)
            for path in (family_classification_mix, family_compare_pit, market_summary_pit)
            if not path.exists()
        ]
        result.status = "failed"
        result.warnings.append(
            f"Missing required inputs for gold-market-cpc-trend-pit: {missing}"
        )
        return result

    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_market_cpc_trend_pit_v2")
    for stale in chunk_dir.glob("market_cpc_trend_pit_*.parquet"):
        stale.unlink()

    year_rows = con.execute(
        f"""
        select distinct
            as_of_year
        from read_parquet('{family_classification_mix}')
        where coalesce(is_observed_as_of_snapshot, false)
          and coalesce(cpc_main_group_count_asof, 0) > 0
        order by 1
        """
    ).fetchall()
    for (as_of_year,) in year_rows:
        chunk_path = chunk_dir / f"market_cpc_trend_pit_{int(as_of_year)}.parquet"
        con.execute(
            f"""
            copy (
                with base as (
                    select
                        fcm.docdb_family_id,
                        fcm.as_of_year,
                        fcm.primary_wipo_field_asof as segment_key,
                        fc.current_snapshot_date,
                        cast(coalesce(fc.active_jurisdiction_count_asof, 0.0) > 0 as boolean) as is_active_family_asof,
                        coalesce(fc.family_blocking_power_score_asof, 0.0) as family_blocking_power_score_asof,
                        coalesce(fc.family_enforceability_score_asof, 0.0) as family_enforceability_score_asof,
                        coalesce(fc.pre_asof_forward_citations_clean, 0.0) as pre_asof_forward_citations_clean,
                        coalesce(fc.family_rcf_score_asof, 0.0) as family_rcf_score_asof,
                        fcm.classification_visibility_policy,
                        cast(fcm.historical_classification_truth_supported as boolean) as historical_classification_truth_supported,
                        unnest(fcm.cpc_main_groups_asof) as cpc_main_group
                    from read_parquet('{family_classification_mix}') fcm
                    join read_parquet('{family_compare_pit}') fc
                      on fcm.docdb_family_id = fc.docdb_family_id
                     and fcm.as_of_year = fc.as_of_year
                    where coalesce(fcm.is_observed_as_of_snapshot, false)
                      and fcm.as_of_year = {int(as_of_year)}
                      and fcm.primary_wipo_field_asof is not null
                      and fcm.primary_wipo_field_asof <> ''
                ),
                segment_totals as (
                    select
                        segment_key,
                        as_of_year,
                        count(distinct docdb_family_id) as segment_family_count_classification_basis_asof,
                        count(distinct case when is_active_family_asof then docdb_family_id end) as segment_active_family_count_classification_basis_asof
                    from base
                    group by segment_key, as_of_year
                ),
                aggregated as (
                    select
                        b.segment_key,
                        b.as_of_year,
                        max(b.current_snapshot_date) as current_snapshot_date,
                        b.cpc_main_group,
                        count(distinct b.docdb_family_id) as cpc_family_count_asof,
                        count(distinct case when b.is_active_family_asof then b.docdb_family_id end) as cpc_active_family_count_asof,
                        avg(b.family_blocking_power_score_asof) as cpc_blocking_density_asof,
                        avg(b.family_enforceability_score_asof) as cpc_enforceability_density_asof,
                        avg(b.pre_asof_forward_citations_clean) as cpc_pre_asof_forward_citations_clean_avg_asof,
                        avg(b.family_rcf_score_asof) as cpc_avg_rcf_score_asof,
                        max(b.classification_visibility_policy) as classification_visibility_policy,
                        bool_and(b.historical_classification_truth_supported) as historical_classification_truth_supported
                    from base b
                    where b.cpc_main_group is not null
                      and b.cpc_main_group <> ''
                    group by b.segment_key, b.as_of_year, b.cpc_main_group
                )
                select
                    a.segment_key,
                    a.segment_key as wipo_industry_code,
                    a.as_of_year,
                    cast(a.current_snapshot_date as date) as current_snapshot_date,
                    a.cpc_main_group,
                    a.cpc_main_group as cpc_main_group_label,
                    cast(a.cpc_family_count_asof as double) as cpc_family_count_asof,
                    cast(a.cpc_active_family_count_asof as double) as cpc_active_family_count_asof,
                    cast(st.segment_family_count_classification_basis_asof as double) as segment_family_count_classification_basis_asof,
                    cast(st.segment_active_family_count_classification_basis_asof as double) as segment_active_family_count_classification_basis_asof,
                    case
                        when coalesce(st.segment_family_count_classification_basis_asof, 0) = 0 then null
                        else cast(a.cpc_family_count_asof as double) / cast(st.segment_family_count_classification_basis_asof as double)
                    end as cpc_family_share_within_segment_asof,
                    case
                        when coalesce(st.segment_active_family_count_classification_basis_asof, 0) = 0 then null
                        else cast(a.cpc_active_family_count_asof as double) / cast(st.segment_active_family_count_classification_basis_asof as double)
                    end as cpc_active_family_share_within_segment_asof,
                    cast(a.cpc_blocking_density_asof as double) as cpc_blocking_density_asof,
                    cast(a.cpc_enforceability_density_asof as double) as cpc_enforceability_density_asof,
                    cast(a.cpc_pre_asof_forward_citations_clean_avg_asof as double) as cpc_pre_asof_forward_citations_clean_avg_asof,
                    cast(a.cpc_avg_rcf_score_asof as double) as cpc_avg_rcf_score_asof,
                    ms.segment_heat_state_asof,
                    a.classification_visibility_policy,
                    cast(true as boolean) as classification_membership_replayed_to_history,
                    cast(a.historical_classification_truth_supported as boolean) as historical_classification_truth_supported,
                    cast(true as boolean) as historical_compare_safe
                from aggregated a
                join segment_totals st
                  on a.segment_key = st.segment_key
                 and a.as_of_year = st.as_of_year
                left join read_parquet('{market_summary_pit}') ms
                  on a.segment_key = ms.segment_key
                 and a.as_of_year = ms.as_of_year
                order by a.segment_key, a.as_of_year, a.cpc_family_count_asof desc, a.cpc_main_group asc
            ) to '{chunk_path}' (format parquet, compression zstd)
            """
        )

    if out_market_cpc_trend_pit.exists():
        out_market_cpc_trend_pit.unlink()
    con.execute(
        f"""
        copy (
            with base as (
                select *
                from read_parquet('{chunk_dir / 'market_cpc_trend_pit_*.parquet'}')
            ),
            segment_history as (
                select distinct
                    segment_key,
                    as_of_year,
                    segment_family_count_classification_basis_asof,
                    segment_heat_state_asof
                from base
            ),
            segment_enriched as (
                select
                    sh.*,
                    lag(segment_family_count_classification_basis_asof) over (
                        partition by segment_key
                        order by as_of_year
                    ) as segment_prior_family_count_classification_basis_asof,
                    case
                        when sh.segment_heat_state_asof is not null then sh.segment_heat_state_asof
                        when coalesce(
                            lag(segment_family_count_classification_basis_asof) over (
                                partition by segment_key
                                order by as_of_year
                            ),
                            0
                        ) <= 0 then 'stable'
                        when (
                            (segment_family_count_classification_basis_asof - lag(segment_family_count_classification_basis_asof) over (
                                partition by segment_key
                                order by as_of_year
                            ))
                            / lag(segment_family_count_classification_basis_asof) over (
                                partition by segment_key
                                order by as_of_year
                            )
                        ) > 0.10 then 'heating'
                        when (
                            (segment_family_count_classification_basis_asof - lag(segment_family_count_classification_basis_asof) over (
                                partition by segment_key
                                order by as_of_year
                            ))
                            / lag(segment_family_count_classification_basis_asof) over (
                                partition by segment_key
                                order by as_of_year
                            )
                        ) < -0.10 then 'cooling'
                        else 'stable'
                    end as resolved_segment_heat_state_asof
                from segment_history sh
            ),
            lagged as (
                select
                    *,
                    lag(cpc_family_count_asof) over (
                        partition by segment_key, cpc_main_group
                        order by as_of_year
                    ) as cpc_prior_family_count_asof
                from base
            )
            select
                l.segment_key,
                l.wipo_industry_code,
                l.as_of_year,
                l.current_snapshot_date,
                l.cpc_main_group,
                l.cpc_main_group_label,
                l.cpc_family_count_asof,
                l.cpc_active_family_count_asof,
                l.segment_family_count_classification_basis_asof,
                l.segment_active_family_count_classification_basis_asof,
                l.cpc_family_share_within_segment_asof,
                l.cpc_active_family_share_within_segment_asof,
                l.cpc_blocking_density_asof,
                l.cpc_enforceability_density_asof,
                l.cpc_pre_asof_forward_citations_clean_avg_asof,
                l.cpc_avg_rcf_score_asof,
                se.resolved_segment_heat_state_asof as segment_heat_state_asof,
                l.cpc_prior_family_count_asof,
                case
                    when coalesce(l.cpc_prior_family_count_asof, 0) <= 0 then null
                    else (l.cpc_family_count_asof - l.cpc_prior_family_count_asof) / l.cpc_prior_family_count_asof
                end as cpc_growth_index_asof,
                case
                    when coalesce(l.cpc_prior_family_count_asof, 0) <= 0 then 'stable'
                    when ((l.cpc_family_count_asof - l.cpc_prior_family_count_asof) / l.cpc_prior_family_count_asof) > 0.10 then 'heating'
                    when ((l.cpc_family_count_asof - l.cpc_prior_family_count_asof) / l.cpc_prior_family_count_asof) < -0.10 then 'cooling'
                    else 'stable'
                end as cpc_heat_state_asof,
                row_number() over (
                    partition by l.segment_key, l.as_of_year
                    order by l.cpc_family_count_asof desc, l.cpc_blocking_density_asof desc, l.cpc_main_group asc
                ) as cpc_rank_within_segment_year,
                l.classification_visibility_policy,
                l.classification_membership_replayed_to_history,
                l.historical_classification_truth_supported,
                l.historical_compare_safe
            from lagged l
            left join segment_enriched se
              on l.segment_key = se.segment_key
             and l.as_of_year = se.as_of_year
        ) to '{out_market_cpc_trend_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_market_cpc_trend_pit))
    result.metrics[f"{out_market_cpc_trend_pit.stem}_rows"] = parquet_row_count(out_market_cpc_trend_pit)
    return result


def build_gold_market_cpc_jurisdiction_trend_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-market-cpc-jurisdiction-trend-pit",
        status="success",
        summary="Built the market WIPO-CPC-jurisdiction PIT mart from family slice evidence.",
        methods=[
            "Started from the family classification-jurisdiction PIT mart so market slice rows inherit the same replay-safe family-year semantics.",
            "Aggregated families by WIPO field, CPC main group, jurisdiction, and year, then lagged each slice for year-over-year growth.",
            "Normalized citation pressure inside each year so slice rankings remain readable without pretending absolute comparability across years.",
        ],
        calculations=[
            "Family share within slice basis is measured against the same WIPO-field and jurisdiction basis for the same year.",
            "Growth index compares current slice family count against prior-year family count in the same WIPO-CPC-jurisdiction slice.",
            "Slice rank within year is ordered by family count, then blocking density, then slice keys.",
        ],
        downstream_impacts=[
            "This mart supports market CPC-by-jurisdiction leaderboards, growth views, and future UI drill-downs across field, CPC, and office slices.",
        ],
        doc_refs=[
            "docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md",
            "docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md",
            "docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_market_cpc_jurisdiction_trend_pit")
    con.execute(f"set temp_directory='{temp_dir}'")

    family_classification_jurisdiction_pit = settings.gold_dir / "gold_family_classification_jurisdiction_pit.parquet"
    out_market_cpc_jurisdiction_trend_pit = (
        settings.gold_dir / "gold_market_cpc_jurisdiction_trend_pit.parquet"
    )
    if not family_classification_jurisdiction_pit.exists():
        result.status = "failed"
        result.warnings.append(
            f"Missing required input for gold-market-cpc-jurisdiction-trend-pit: {family_classification_jurisdiction_pit}"
        )
        return result

    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_market_cpc_jurisdiction_trend_pit")
    for stale in chunk_dir.glob("market_cpc_jurisdiction_trend_pit_*.parquet"):
        stale.unlink()

    year_rows = con.execute(
        f"""
        select distinct as_of_year
        from read_parquet('{family_classification_jurisdiction_pit}')
        order by 1
        """
    ).fetchall()
    for (as_of_year,) in year_rows:
        chunk_path = chunk_dir / f"market_cpc_jurisdiction_trend_pit_{int(as_of_year)}.parquet"
        con.execute(
            f"""
            copy (
                with segment_totals as (
                    select
                        as_of_year,
                        wipo_field,
                        jurisdiction_code,
                        count(distinct docdb_family_id) as segment_family_count_basis_asof,
                        count(distinct case when is_active_asof then docdb_family_id end) as segment_active_family_count_basis_asof
                    from read_parquet('{family_classification_jurisdiction_pit}')
                    where as_of_year = {int(as_of_year)}
                    group by as_of_year, wipo_field, jurisdiction_code
                ),
                aggregated as (
                    select
                        as_of_year,
                        max(current_snapshot_date) as current_snapshot_date,
                        wipo_field,
                        cpc_main_group,
                        jurisdiction_code,
                        min(classification_jurisdiction_support_level) as classification_jurisdiction_support_level,
                        count(distinct docdb_family_id) as family_count_asof,
                        count(distinct case when is_active_asof then docdb_family_id end) as active_family_count_asof,
                        avg(family_blocking_power_score_asof) as blocking_density_asof,
                        avg(family_enforceability_score_asof) as enforceability_density_asof,
                        avg(pre_asof_forward_citations_clean) as raw_citation_pressure_density_asof,
                        bool_and(coalesce(classification_membership_replayed_to_history, false)) as classification_membership_replayed_to_history,
                        bool_and(coalesce(historical_classification_truth_supported, false)) as historical_classification_truth_supported,
                        bool_and(coalesce(historical_compare_safe, false)) as historical_compare_safe
                    from read_parquet('{family_classification_jurisdiction_pit}')
                    where as_of_year = {int(as_of_year)}
                    group by as_of_year, wipo_field, cpc_main_group, jurisdiction_code
                )
                select
                    a.as_of_year,
                    cast(a.current_snapshot_date as date) as current_snapshot_date,
                    a.wipo_field,
                    a.cpc_main_group,
                    a.jurisdiction_code,
                    cast(a.family_count_asof as double) as family_count_asof,
                    cast(a.active_family_count_asof as double) as active_family_count_asof,
                    cast(st.segment_family_count_basis_asof as double) as segment_family_count_basis_asof,
                    cast(st.segment_active_family_count_basis_asof as double) as segment_active_family_count_basis_asof,
                    case
                        when coalesce(st.segment_family_count_basis_asof, 0) = 0 then null
                        else cast(a.family_count_asof as double) / cast(st.segment_family_count_basis_asof as double)
                    end as family_share_within_slice_asof,
                    cast(a.blocking_density_asof as double) as blocking_density_asof,
                    cast(a.enforceability_density_asof as double) as enforceability_density_asof,
                    cast(a.raw_citation_pressure_density_asof as double) as raw_citation_pressure_density_asof,
                    a.classification_jurisdiction_support_level,
                    cast(a.classification_membership_replayed_to_history as boolean) as classification_membership_replayed_to_history,
                    cast(a.historical_classification_truth_supported as boolean) as historical_classification_truth_supported,
                    cast(a.historical_compare_safe as boolean) as historical_compare_safe,
                    '{settings.method_version}' as method_version
                from aggregated a
                join segment_totals st
                  on a.as_of_year = st.as_of_year
                 and a.wipo_field = st.wipo_field
                 and a.jurisdiction_code = st.jurisdiction_code
                order by a.as_of_year, a.wipo_field, a.cpc_main_group, a.jurisdiction_code
            ) to '{chunk_path}' (format parquet, compression zstd)
            """
        )

    if out_market_cpc_jurisdiction_trend_pit.exists():
        out_market_cpc_jurisdiction_trend_pit.unlink()
    con.execute(
        f"""
        copy (
            with base as (
                select *
                from read_parquet('{chunk_dir / 'market_cpc_jurisdiction_trend_pit_*.parquet'}')
            ),
            lagged as (
                select
                    *,
                    lag(family_count_asof) over (
                        partition by wipo_field, cpc_main_group, jurisdiction_code
                        order by as_of_year
                    ) as prior_family_count_asof
                from base
            )
            select
                as_of_year,
                current_snapshot_date,
                wipo_field,
                cpc_main_group,
                jurisdiction_code,
                family_count_asof,
                active_family_count_asof,
                segment_family_count_basis_asof,
                segment_active_family_count_basis_asof,
                family_share_within_slice_asof,
                case
                    when coalesce(max(raw_citation_pressure_density_asof) over (partition by as_of_year), 0.0) <= 0 then 0.0
                    else raw_citation_pressure_density_asof
                         / max(raw_citation_pressure_density_asof) over (partition by as_of_year) * 100.0
                end as citation_pressure_index_asof,
                case
                    when coalesce(prior_family_count_asof, 0) <= 0 then null
                    else (family_count_asof - prior_family_count_asof) / prior_family_count_asof
                end as growth_index_asof,
                blocking_density_asof,
                enforceability_density_asof,
                row_number() over (
                    partition by as_of_year
                    order by family_count_asof desc, blocking_density_asof desc, wipo_field asc, cpc_main_group asc, jurisdiction_code asc
                ) as slice_rank_within_year,
                classification_jurisdiction_support_level,
                classification_membership_replayed_to_history,
                historical_classification_truth_supported,
                historical_compare_safe,
                method_version
            from lagged
        ) to '{out_market_cpc_jurisdiction_trend_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_market_cpc_jurisdiction_trend_pit))
    result.metrics[f"{out_market_cpc_jurisdiction_trend_pit.stem}_rows"] = parquet_row_count(
        out_market_cpc_jurisdiction_trend_pit
    )
    return result


def build_gold_cpc_importance_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-cpc-importance-pit",
        status="success",
        summary="Built the CPC importance PIT mart from the market CPC trend layer.",
        methods=[
            "Aggregated CPC presence across WIPO segments into one CPC-year row per main group.",
            "Weighted blocking and enforceability by CPC family count so large segments matter proportionally.",
            "Scored CPC importance from family share, segment breadth, blocking, enforceability, and positive growth contribution.",
        ],
        calculations=[
            "CPC global family share is measured against the total family classification basis across all WIPO segments in the year.",
            "CPC segment presence share is the fraction of WIPO segments where the CPC appears in that year.",
            "Importance band is derived from the composite score: strategic above 0.55, core above 0.30, otherwise emerging.",
        ],
        downstream_impacts=[
            "This mart supports year-slice CPC ranking cards and importance drill-downs in Market Intelligence.",
        ],
        doc_refs=[
            "docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md",
            "docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_cpc_importance_pit")
    con.execute(f"set temp_directory='{temp_dir}'")

    market_cpc_trend_pit = settings.gold_dir / "gold_market_cpc_trend_pit.parquet"
    out_cpc_importance_pit = settings.gold_dir / "gold_cpc_importance_pit.parquet"
    if not market_cpc_trend_pit.exists():
        result.status = "failed"
        result.warnings.append(
            f"Missing required input for gold-cpc-importance-pit: {market_cpc_trend_pit}"
        )
        return result

    if out_cpc_importance_pit.exists():
        out_cpc_importance_pit.unlink()
    con.execute(
        f"""
        copy (
            with base as (
                select *
                from read_parquet('{market_cpc_trend_pit}')
            ),
            year_totals as (
                select
                    as_of_year,
                    sum(segment_family_count_classification_basis_asof) as total_family_basis_asof,
                    count(distinct segment_key) as total_segment_count_asof
                from (
                    select distinct
                        as_of_year,
                        segment_key,
                        segment_family_count_classification_basis_asof
                    from base
                )
                group by as_of_year
            ),
            aggregated as (
                select
                    b.as_of_year,
                    max(b.current_snapshot_date) as current_snapshot_date,
                    b.cpc_main_group,
                    max(b.cpc_main_group_label) as cpc_main_group_label,
                    sum(b.cpc_family_count_asof) as cpc_family_count_asof,
                    count(distinct b.segment_key) as cpc_segment_count_asof,
                    case
                        when sum(b.cpc_family_count_asof) = 0 then null
                        else sum(b.cpc_blocking_density_asof * b.cpc_family_count_asof) / sum(b.cpc_family_count_asof)
                    end as cpc_blocking_density_asof,
                    case
                        when sum(b.cpc_family_count_asof) = 0 then null
                        else sum(b.cpc_enforceability_density_asof * b.cpc_family_count_asof) / sum(b.cpc_family_count_asof)
                    end as cpc_enforceability_density_asof,
                    case
                        when sum(b.cpc_family_count_asof) = 0 then null
                        else sum(b.cpc_pre_asof_forward_citations_clean_avg_asof * b.cpc_family_count_asof) / sum(b.cpc_family_count_asof)
                    end as cpc_pre_asof_forward_citations_clean_avg_asof,
                    case
                        when sum(b.cpc_family_count_asof) = 0 then null
                        else sum(b.cpc_avg_rcf_score_asof * b.cpc_family_count_asof) / sum(b.cpc_family_count_asof)
                    end as cpc_avg_rcf_score_asof
                from base b
                group by b.as_of_year, b.cpc_main_group
            ),
            lagged as (
                select
                    a.*,
                    lag(a.cpc_family_count_asof) over (
                        partition by a.cpc_main_group
                        order by a.as_of_year
                    ) as cpc_prior_family_count_asof
                from aggregated a
            ),
            scored as (
                select
                    l.as_of_year,
                    l.current_snapshot_date,
                    l.cpc_main_group,
                    l.cpc_main_group_label,
                    cast(l.cpc_family_count_asof as double) as cpc_family_count_asof,
                    cast(l.cpc_segment_count_asof as double) as cpc_segment_count_asof,
                    case
                        when coalesce(yt.total_family_basis_asof, 0) = 0 then null
                        else cast(l.cpc_family_count_asof as double) / cast(yt.total_family_basis_asof as double)
                    end as cpc_family_share_global_asof,
                    case
                        when coalesce(yt.total_segment_count_asof, 0) = 0 then null
                        else cast(l.cpc_segment_count_asof as double) / cast(yt.total_segment_count_asof as double)
                    end as cpc_segment_presence_share_asof,
                    cast(l.cpc_blocking_density_asof as double) as cpc_blocking_density_asof,
                    cast(l.cpc_enforceability_density_asof as double) as cpc_enforceability_density_asof,
                    cast(l.cpc_pre_asof_forward_citations_clean_avg_asof as double) as cpc_pre_asof_forward_citations_clean_avg_asof,
                    cast(l.cpc_avg_rcf_score_asof as double) as cpc_avg_rcf_score_asof,
                    cast(l.cpc_prior_family_count_asof as double) as cpc_prior_family_count_asof,
                    case
                        when coalesce(l.cpc_prior_family_count_asof, 0) <= 0 then null
                        else (cast(l.cpc_family_count_asof as double) - cast(l.cpc_prior_family_count_asof as double))
                             / cast(l.cpc_prior_family_count_asof as double)
                    end as cpc_growth_index_asof
                from lagged l
                join year_totals yt using (as_of_year)
            ),
            normalized as (
                select
                    *,
                    cume_dist() over (
                        partition by as_of_year
                        order by coalesce(cpc_family_share_global_asof, 0.0)
                    ) as family_share_strength_asof,
                    cume_dist() over (
                        partition by as_of_year
                        order by coalesce(cpc_segment_presence_share_asof, 0.0)
                    ) as segment_presence_strength_asof,
                    cume_dist() over (
                        partition by as_of_year
                        order by coalesce(cpc_blocking_density_asof, 0.0)
                    ) as blocking_strength_asof,
                    cume_dist() over (
                        partition by as_of_year
                        order by coalesce(cpc_enforceability_density_asof, 0.0)
                    ) as enforceability_strength_asof,
                    cume_dist() over (
                        partition by as_of_year
                        order by least(greatest(coalesce(cpc_growth_index_asof, 0.0), 0.0), 1.0)
                    ) as growth_strength_asof
                from scored
            )
            select
                as_of_year,
                current_snapshot_date,
                cpc_main_group,
                cpc_main_group_label,
                cpc_family_count_asof,
                cpc_segment_count_asof,
                cpc_family_share_global_asof,
                cpc_segment_presence_share_asof,
                cpc_blocking_density_asof,
                cpc_enforceability_density_asof,
                cpc_pre_asof_forward_citations_clean_avg_asof,
                cpc_avg_rcf_score_asof,
                cpc_prior_family_count_asof,
                cpc_growth_index_asof,
                (
                    0.45 * coalesce(family_share_strength_asof, 0.0)
                    + 0.20 * coalesce(segment_presence_strength_asof, 0.0)
                    + 0.20 * coalesce(blocking_strength_asof, 0.0)
                    + 0.10 * coalesce(enforceability_strength_asof, 0.0)
                    + 0.05 * coalesce(growth_strength_asof, 0.0)
                ) as cpc_importance_score_asof,
                case
                    when (
                        0.45 * coalesce(family_share_strength_asof, 0.0)
                        + 0.20 * coalesce(segment_presence_strength_asof, 0.0)
                        + 0.20 * coalesce(blocking_strength_asof, 0.0)
                        + 0.10 * coalesce(enforceability_strength_asof, 0.0)
                        + 0.05 * coalesce(growth_strength_asof, 0.0)
                    ) >= 0.80 then 'strategic'
                    when (
                        0.45 * coalesce(family_share_strength_asof, 0.0)
                        + 0.20 * coalesce(segment_presence_strength_asof, 0.0)
                        + 0.20 * coalesce(blocking_strength_asof, 0.0)
                        + 0.10 * coalesce(enforceability_strength_asof, 0.0)
                        + 0.05 * coalesce(growth_strength_asof, 0.0)
                    ) >= 0.55 then 'core'
                    else 'emerging'
                end as cpc_importance_band_asof,
                row_number() over (
                    partition by as_of_year
                    order by
                        (
                            0.45 * coalesce(family_share_strength_asof, 0.0)
                            + 0.20 * coalesce(segment_presence_strength_asof, 0.0)
                            + 0.20 * coalesce(blocking_strength_asof, 0.0)
                            + 0.10 * coalesce(enforceability_strength_asof, 0.0)
                            + 0.05 * coalesce(growth_strength_asof, 0.0)
                        ) desc,
                        cpc_family_count_asof desc,
                        cpc_main_group asc
                ) as cpc_importance_rank_within_year,
                true as historical_compare_safe,
                false as historical_classification_truth_supported
            from normalized
        ) to '{out_cpc_importance_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_cpc_importance_pit))
    result.metrics[f"{out_cpc_importance_pit.stem}_rows"] = parquet_row_count(out_cpc_importance_pit)
    return result


def build_gold_portfolio_summary_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-portfolio-summary-pit",
        status="success",
        summary="Built the portfolio PIT summary mart by aggregating family compare PIT rows through the current owner bridge with explicit historical caveats.",
        methods=[
            "Aggregated only historical-safe family PIT rows into year-keyed portfolio summaries.",
            "Reused the current owner bridge as a historical membership approximation and labeled that caveat explicitly.",
            "Focused the first release on legal, blocking, coverage, and concentration signals rather than forcing unsupported historical field-mix claims.",
        ],
        calculations=[
            "Portfolio top-family dependence is measured as the maximum family blocking share within each owner-year slice.",
            "Portfolio active-family count is derived from point-in-time active-jurisdiction presence rather than current family status.",
        ],
        downstream_impacts=[
            "This mart is the first safe source for portfolio over-time comparison, historical report sections, and legal-attrition context before Phase 04 predictions arrive.",
        ],
        doc_refs=[
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md",
            "docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_portfolio_pit")
    con.execute(f"set temp_directory='{temp_dir}'")

    family_compare_pit = settings.gold_dir / "gold_family_compare_pit.parquet"
    owner_bridge = settings.silver_dir / "silver_family_owner_bridge.parquet"
    out_portfolio_summary_pit = settings.gold_dir / "gold_portfolio_summary_pit.parquet"
    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_portfolio_summary_pit")
    for stale in chunk_dir.glob("portfolio_summary_pit_*.parquet"):
        stale.unlink()

    year_rows = con.execute(
        f"""
        select distinct as_of_year
        from read_parquet('{family_compare_pit}')
        order by 1
        """
    ).fetchall()
    for (as_of_year,) in year_rows:
        chunk_path = chunk_dir / f"portfolio_summary_pit_{int(as_of_year)}.parquet"
        con.execute(
            f"""
            copy (
                with owner_identity as (
                    select
                        owner_name_harmonized,
                        owner_name_display
                    from (
                        select
                            owner_name_harmonized,
                            owner_name_display,
                            row_number() over (
                                partition by owner_name_harmonized
                                order by count(*) desc, owner_name_display asc
                            ) as display_rank
                        from read_parquet('{owner_bridge}')
                        group by owner_name_harmonized, owner_name_display
                    )
                    where display_rank = 1
                ),
                bridged as (
                    select
                        ob.owner_name_harmonized,
                        oi.owner_name_display as owner_name_display_current,
                        f.docdb_family_id,
                        f.as_of_year,
                        f.current_snapshot_date,
                        f.family_composite_status_asof,
                        f.active_jurisdiction_count_asof,
                        f.lapsed_jurisdiction_count_asof,
                        f.family_blocking_power_score_asof,
                        f.family_enforceability_score_asof,
                        f.family_rcf_score_asof,
                        f.data_completeness_pct_asof
                    from read_parquet('{family_compare_pit}') f
                    join read_parquet('{owner_bridge}') ob using (docdb_family_id)
                    left join owner_identity oi using (owner_name_harmonized)
                    where f.as_of_year = {int(as_of_year)}
                )
                select
                    owner_name_harmonized,
                    owner_name_display_current,
                    as_of_year,
                    current_snapshot_date,
                    count(distinct docdb_family_id) as portfolio_family_count_hist_proxy,
                    count(distinct case when coalesce(active_jurisdiction_count_asof, 0) > 0 then docdb_family_id end) as portfolio_active_family_count_asof,
                    sum(coalesce(active_jurisdiction_count_asof, 0.0)) as portfolio_active_jurisdiction_count_asof,
                    sum(coalesce(lapsed_jurisdiction_count_asof, 0.0)) as portfolio_lapsed_jurisdiction_count_asof,
                    avg(coalesce(family_blocking_power_score_asof, 0.0)) as portfolio_avg_blocking_power_score_asof,
                    sum(coalesce(family_blocking_power_score_asof, 0.0)) as portfolio_total_blocking_power_score_asof,
                    avg(coalesce(family_enforceability_score_asof, 0.0)) as portfolio_avg_enforceability_score_asof,
                    sum(coalesce(family_rcf_score_asof, 0.0)) as portfolio_total_rcf_score_asof,
                    avg(coalesce(data_completeness_pct_asof, 0.0)) as portfolio_data_completeness_pct_asof,
                    case
                        when sum(coalesce(family_blocking_power_score_asof, 0.0)) = 0 then 0.0
                        else max(coalesce(family_blocking_power_score_asof, 0.0)) / sum(coalesce(family_blocking_power_score_asof, 0.0))
                    end as portfolio_top_family_blocking_share_asof,
                    true as historical_compare_safe,
                    false as historical_owner_truth_supported,
                    true as current_owner_bridge_replayed_to_history,
                    false as historical_field_mix_supported
                from bridged
                group by owner_name_harmonized, owner_name_display_current, as_of_year, current_snapshot_date
                order by owner_name_harmonized, as_of_year
            ) to '{chunk_path}' (format parquet, compression zstd)
            """
        )

    if out_portfolio_summary_pit.exists():
        out_portfolio_summary_pit.unlink()
    con.execute(
        f"""
        copy (
            select *
            from read_parquet('{chunk_dir / 'portfolio_summary_pit_*.parquet'}')
        ) to '{out_portfolio_summary_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_portfolio_summary_pit))
    result.metrics[f"{out_portfolio_summary_pit.stem}_rows"] = parquet_row_count(out_portfolio_summary_pit)
    return result


def build_gold_portfolio_compare_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-portfolio-compare-pit",
        status="success",
        summary="Built the portfolio compare PIT mart from dense portfolio PIT summaries and year-safe field-mix support where available.",
        methods=[
            "Started from the dense portfolio summary PIT so legal, blocking, and concentration metrics stay historical-safe.",
            "Joined field-mix metrics only for years actually present in the portfolio field timeseries.",
            "Kept historical owner truth and historical field-mix support explicitly caveated when source coverage is unavailable.",
        ],
        calculations=[
            "Portfolio legal durability index is measured as active-family share within the historical owner-year proxy slice.",
            "Portfolio field breadth is the count of positive active-family fields in the supported field-timeseries year.",
            "Portfolio field concentration is calculated as HHI over active-family field shares, with top-field share surfaced separately.",
        ],
        downstream_impacts=[
            "This mart is the compare-oriented source for portfolio year-slice views, radar overlays, and report compare tables.",
        ],
        doc_refs=[
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)

    portfolio_summary_pit = settings.gold_dir / "gold_portfolio_summary_pit.parquet"
    portfolio_field_ts = settings.gold_dir / "gold_portfolio_field_timeseries.parquet"
    out_portfolio_compare_pit = settings.gold_dir / "gold_portfolio_compare_pit.parquet"

    con.execute(
        f"""
        copy (
            with field_mix_base as (
                select
                    owner_name_harmonized,
                    cast(extract(year from snapshot_date) as integer) as as_of_year,
                    wipo_field,
                    coalesce(active_family_count, 0) as active_family_count
                from read_parquet('{portfolio_field_ts}')
            ),
            field_mix_totals as (
                select
                    owner_name_harmonized,
                    as_of_year,
                    sum(active_family_count) as total_active_family_count
                from field_mix_base
                group by owner_name_harmonized, as_of_year
            ),
            field_mix_shares as (
                select
                    b.owner_name_harmonized,
                    b.as_of_year,
                    b.wipo_field,
                    b.active_family_count,
                    t.total_active_family_count,
                    case
                        when coalesce(t.total_active_family_count, 0) = 0 then null
                        else cast(b.active_family_count as double) / cast(t.total_active_family_count as double)
                    end as active_family_share
                from field_mix_base b
                join field_mix_totals t
                  on b.owner_name_harmonized = t.owner_name_harmonized
                 and b.as_of_year = t.as_of_year
            ),
            field_mix as (
                select
                    s.owner_name_harmonized,
                    s.as_of_year,
                    count(*) filter (where coalesce(active_family_count, 0) > 0) as portfolio_field_breadth_asof,
                    case
                        when max(coalesce(s.total_active_family_count, 0)) = 0 then null
                        else sum(power(coalesce(s.active_family_share, 0.0), 2))
                    end as portfolio_field_concentration_hhi_asof,
                    case
                        when max(coalesce(s.total_active_family_count, 0)) = 0 then null
                        else max(coalesce(s.active_family_share, 0.0))
                    end as portfolio_top_field_share_asof
                from field_mix_shares s
                group by s.owner_name_harmonized, s.as_of_year
            )
            select
                p.owner_name_harmonized,
                p.owner_name_display_current,
                p.as_of_year,
                p.current_snapshot_date,
                p.portfolio_family_count_hist_proxy,
                p.portfolio_active_family_count_asof,
                p.portfolio_active_jurisdiction_count_asof,
                p.portfolio_lapsed_jurisdiction_count_asof,
                p.portfolio_avg_blocking_power_score_asof,
                p.portfolio_total_blocking_power_score_asof,
                p.portfolio_avg_enforceability_score_asof,
                p.portfolio_total_rcf_score_asof,
                p.portfolio_data_completeness_pct_asof,
                p.portfolio_top_family_blocking_share_asof,
                case
                    when coalesce(p.portfolio_family_count_hist_proxy, 0) = 0 then 0.0
                    else cast(p.portfolio_active_family_count_asof as double) / cast(p.portfolio_family_count_hist_proxy as double)
                end as portfolio_legal_durability_index_asof,
                cast(fm.portfolio_field_breadth_asof as double) as portfolio_field_breadth_asof,
                cast(fm.portfolio_field_concentration_hhi_asof as double) as portfolio_field_concentration_hhi_asof,
                cast(fm.portfolio_top_field_share_asof as double) as portfolio_top_field_share_asof,
                p.historical_compare_safe,
                p.historical_owner_truth_supported,
                p.current_owner_bridge_replayed_to_history,
                cast(fm.owner_name_harmonized is not null as boolean) as historical_field_mix_supported
            from read_parquet('{portfolio_summary_pit}') p
            left join field_mix fm
              on p.owner_name_harmonized = fm.owner_name_harmonized
             and p.as_of_year = fm.as_of_year
            order by p.owner_name_harmonized, p.as_of_year
        ) to '{out_portfolio_compare_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_portfolio_compare_pit))
    result.metrics[f"{out_portfolio_compare_pit.stem}_rows"] = parquet_row_count(out_portfolio_compare_pit)
    return result


def build_gold_market_leaderboard_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-market-leaderboard-pit",
        status="success",
        summary="Built the market leaderboard PIT mart for segment-year family and owner rankings with explicit historical owner caveats.",
        methods=[
            "Derived family leaderboard rows from year-safe family field-contribution timeseries joined to dense family compare PIT.",
            "Derived owner leaderboard rows by aggregating current-owner replay across in-segment family-year rows.",
            "Ranked families and owners separately within each segment-year slice and capped each leaderboard to a compact top set.",
        ],
        calculations=[
            "Family leaderboard ranking uses family blocking power first, then weighted field participation as a tiebreaker.",
            "Owner leaderboard share is measured against the segment active-family count from the market summary PIT.",
            "Owner average blocking is computed over the current-owner replay family set inside the segment-year slice.",
        ],
        downstream_impacts=[
            "This mart supports selected-year segment leader tables and owner presence panels without requiring ad hoc ranking logic in the backend.",
        ],
        doc_refs=[
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_market_leaderboard_pit")
    con.execute(f"set temp_directory='{temp_dir}'")

    market_summary_pit = settings.gold_dir / "gold_market_summary_pit.parquet"
    family_compare_pit = settings.gold_dir / "gold_family_compare_pit.parquet"
    family_field_ts = settings.gold_dir / "gold_family_field_contributions_timeseries.parquet"
    out_market_leaderboard_pit = settings.gold_dir / "gold_market_leaderboard_pit.parquet"
    top_k = 20
    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_market_leaderboard_pit")
    for stale in chunk_dir.glob("market_leaderboard_pit_*.parquet"):
        stale.unlink()

    year_segment_rows = con.execute(
        f"""
        select distinct as_of_year, segment_key
        from read_parquet('{market_summary_pit}')
        order by 1, 2
        """
    ).fetchall()
    for as_of_year, segment_key in year_segment_rows:
        safe_segment = (
            str(segment_key)
            .replace("/", "_")
            .replace(" ", "_")
            .replace(",", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("-", "_")
        )
        chunk_path = chunk_dir / f"market_leaderboard_pit_{int(as_of_year)}_{safe_segment}.parquet"
        con.execute(
            f"""
            copy (
                with segment_family_year as (
                    select
                        ff.snapshot_year as as_of_year,
                        ff.wipo_industry_code as segment_key,
                        ff.docdb_family_id,
                        coalesce(ff.base_fraction, 0.0) as base_fraction,
                        coalesce(ff.active_market_weight, 0.0) as active_market_weight,
                        fc.current_snapshot_date,
                        fc.family_composite_status_asof,
                        fc.family_blocking_power_score_asof,
                        fc.family_enforceability_score_asof,
                        fc.family_active_jurisdiction_share_asof,
                        fc.family_rcf_score_asof,
                        fc.owner_name_harmonized_current,
                        fc.owner_name_display_current
                    from read_parquet('{family_field_ts}') ff
                    join read_parquet('{family_compare_pit}') fc
                      on ff.docdb_family_id = fc.docdb_family_id
                     and ff.snapshot_year = fc.as_of_year
                    where coalesce(ff.is_active_on_snapshot, true)
                      and ff.snapshot_year = {int(as_of_year)}
                      and ff.wipo_industry_code = '{str(segment_key).replace("'", "''")}'
                ),
                family_ranked as (
                    select
                        sfy.segment_key,
                        sfy.as_of_year,
                        sfy.current_snapshot_date,
                        'family' as leaderboard_entity_type,
                        row_number() over (
                            partition by sfy.segment_key, sfy.as_of_year
                            order by
                                coalesce(sfy.family_blocking_power_score_asof, 0.0) desc,
                                coalesce(sfy.base_fraction, 0.0) desc,
                                sfy.docdb_family_id asc
                        ) as leaderboard_rank,
                        sfy.docdb_family_id,
                        cast(null as varchar) as owner_name_harmonized,
                        cast(null as varchar) as owner_name_display_current,
                        cast(1 as bigint) as in_segment_family_count_hist_proxy,
                        cast(null as double) as in_segment_family_share_hist_proxy,
                        cast(sfy.family_blocking_power_score_asof as double) as avg_blocking_score_asof,
                        cast(sfy.family_blocking_power_score_asof as double) as total_blocking_score_asof,
                        cast(sfy.base_fraction as double) as field_presence_weight_asof,
                        sfy.family_composite_status_asof,
                        true as historical_compare_safe,
                        false as historical_owner_truth_supported,
                        false as current_owner_bridge_replayed_to_history,
                        true as current_owner_metadata_only
                    from segment_family_year sfy
                ),
                owner_agg as (
                    select
                        sfy.segment_key,
                        sfy.as_of_year,
                        max(sfy.current_snapshot_date) as current_snapshot_date,
                        sfy.owner_name_harmonized_current as owner_name_harmonized,
                        max(sfy.owner_name_display_current) as owner_name_display_current,
                        count(distinct sfy.docdb_family_id) as in_segment_family_count_hist_proxy,
                        avg(coalesce(sfy.family_blocking_power_score_asof, 0.0)) as avg_blocking_score_asof,
                        sum(coalesce(sfy.family_blocking_power_score_asof, 0.0)) as total_blocking_score_asof,
                        avg(coalesce(sfy.base_fraction, 0.0)) as field_presence_weight_asof
                    from segment_family_year sfy
                    group by sfy.segment_key, sfy.as_of_year, sfy.owner_name_harmonized_current
                ),
                owner_ranked as (
                    select
                        oa.segment_key,
                        oa.as_of_year,
                        oa.current_snapshot_date,
                        'owner' as leaderboard_entity_type,
                        row_number() over (
                            partition by oa.segment_key, oa.as_of_year
                            order by
                                oa.in_segment_family_count_hist_proxy desc,
                                coalesce(oa.total_blocking_score_asof, 0.0) desc,
                                oa.owner_name_harmonized asc
                        ) as leaderboard_rank,
                        cast(null as bigint) as docdb_family_id,
                        oa.owner_name_harmonized,
                        oa.owner_name_display_current,
                        oa.in_segment_family_count_hist_proxy,
                        case
                            when coalesce(ms.segment_active_family_count_asof, 0) = 0 then null
                            else cast(oa.in_segment_family_count_hist_proxy as double) / cast(ms.segment_active_family_count_asof as double)
                        end as in_segment_family_share_hist_proxy,
                        cast(oa.avg_blocking_score_asof as double) as avg_blocking_score_asof,
                        cast(oa.total_blocking_score_asof as double) as total_blocking_score_asof,
                        cast(oa.field_presence_weight_asof as double) as field_presence_weight_asof,
                        cast(null as varchar) as family_composite_status_asof,
                        true as historical_compare_safe,
                        false as historical_owner_truth_supported,
                        true as current_owner_bridge_replayed_to_history,
                        true as current_owner_metadata_only
                    from owner_agg oa
                    left join read_parquet('{market_summary_pit}') ms
                      on oa.segment_key = ms.segment_key
                     and oa.as_of_year = ms.as_of_year
                    where oa.as_of_year = {int(as_of_year)}
                      and oa.segment_key = '{str(segment_key).replace("'", "''")}'
                )
                select *
                from (
                    select * from family_ranked where leaderboard_rank <= {top_k}
                    union all
                    select * from owner_ranked where leaderboard_rank <= {top_k}
                )
                order by segment_key, as_of_year, leaderboard_entity_type, leaderboard_rank
            ) to '{chunk_path}' (format parquet, compression zstd)
            """
        )

    if out_market_leaderboard_pit.exists():
        out_market_leaderboard_pit.unlink()
    con.execute(
        f"""
        copy (
            select *
            from read_parquet('{chunk_dir / 'market_leaderboard_pit_*.parquet'}')
        ) to '{out_market_leaderboard_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_market_leaderboard_pit))
    result.metrics[f"{out_market_leaderboard_pit.stem}_rows"] = parquet_row_count(out_market_leaderboard_pit)
    return result


def build_gold_market_summary_pit(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-market-summary-pit",
        status="success",
        summary="Built the market PIT summary mart from year-safe market timeseries, dense family compare PIT, and current-owner caveated family membership.",
        methods=[
            "Started from the year-safe market-intelligence timeseries and retained one row per segment and year.",
            "Joined dense family compare PIT with family field-contribution timeseries to derive blocking and active-family density by segment-year.",
            "Used the current family owner from the family compare PIT as a historical owner proxy and labeled that caveat explicitly.",
        ],
        calculations=[
            "Segment growth index is computed from family-count change versus the prior year when prior-year count exists.",
            "Segment blocking density is a weighted average of family blocking power using field base fractions as segment participation weights.",
            "Segment field balance is the average family allocation share to the segment, higher when families are more concentrated in that field.",
        ],
        downstream_impacts=[
            "This mart is the safe historical source for Market Intelligence year-slice cards, league tables, and segment detail drawers.",
        ],
        doc_refs=[
            "docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md",
            "docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)
    con.execute("set threads=2")
    temp_dir = ensure_dir(settings.gold_dir / "_duckdb_tmp_market_pit")
    con.execute(f"set temp_directory='{temp_dir}'")

    market_ts = settings.gold_dir / "gold_market_intelligence_timeseries.parquet"
    family_compare_pit = settings.gold_dir / "gold_family_compare_pit.parquet"
    family_field_ts = settings.gold_dir / "gold_family_field_contributions_timeseries.parquet"
    out_market_summary_pit = settings.gold_dir / "gold_market_summary_pit.parquet"
    chunk_dir = ensure_dir(settings.gold_dir / "_tmp_gold_market_summary_pit")
    for stale in chunk_dir.glob("market_summary_pit_*.parquet"):
        stale.unlink()

    year_rows = con.execute(
        f"""
        select distinct cast(family_priority_year as integer) as as_of_year
        from read_parquet('{market_ts}')
        order by 1
        """
    ).fetchall()
    for (as_of_year,) in year_rows:
        chunk_path = chunk_dir / f"market_summary_pit_{int(as_of_year)}.parquet"
        con.execute(
            f"""
            copy (
                with segment_family_year_all as (
                    select
                        ff.snapshot_year as as_of_year,
                        ff.wipo_industry_code as segment_key,
                        ff.docdb_family_id as docdb_family_id,
                        coalesce(ff.is_active_on_snapshot, true) as is_active_on_snapshot,
                        coalesce(ff.base_fraction, 0.0) as base_fraction,
                        coalesce(ff.active_market_weight, 0.0) as active_market_weight,
                        fc.current_snapshot_date,
                        fc.family_blocking_power_score_asof,
                        fc.family_enforceability_score_asof,
                        fc.family_active_jurisdiction_share_asof,
                        fc.family_tech_breadth_wipo_count_asof,
                        fc.family_composite_status_asof,
                        fc.owner_name_harmonized_current as owner_name_harmonized
                    from read_parquet('{family_field_ts}') ff
                    join read_parquet('{family_compare_pit}') fc
                      on ff.docdb_family_id = fc.docdb_family_id
                     and ff.snapshot_year = fc.as_of_year
                    where ff.snapshot_year = {int(as_of_year)}
                ),
                segment_family_year as (
                    select *
                    from segment_family_year_all
                    where is_active_on_snapshot
                ),
                segment_stock_counts as (
                    select
                        as_of_year,
                        segment_key,
                        count(distinct docdb_family_id) as segment_family_count_stock_asof
                    from segment_family_year_all
                    group by as_of_year, segment_key
                ),
                owner_counts as (
                    select
                        as_of_year,
                        segment_key,
                        owner_name_harmonized,
                        count(distinct docdb_family_id) as owner_family_count
                    from segment_family_year
                    group by as_of_year, segment_key, owner_name_harmonized
                ),
                segment_rollup as (
                    select
                        sfy.as_of_year,
                        sfy.segment_key,
                        max(sfy.current_snapshot_date) as current_snapshot_date,
                        count(distinct sfy.docdb_family_id) as segment_active_family_count_asof,
                        sum(coalesce(sfy.active_market_weight, 0.0)) as segment_active_weight_asof,
                        avg(coalesce(sfy.family_active_jurisdiction_share_asof, 0.0)) as segment_active_jurisdiction_share_asof,
                        case
                            when sum(coalesce(sfy.base_fraction, 0.0)) = 0 then 0.0
                            else sum(coalesce(sfy.family_blocking_power_score_asof, 0.0) * coalesce(sfy.base_fraction, 0.0))
                                 / sum(coalesce(sfy.base_fraction, 0.0))
                        end as segment_blocking_density_asof,
                        case
                            when sum(coalesce(sfy.base_fraction, 0.0)) = 0 then 0.0
                            else sum(coalesce(sfy.family_enforceability_score_asof, 0.0) * coalesce(sfy.base_fraction, 0.0))
                                 / sum(coalesce(sfy.base_fraction, 0.0))
                        end as segment_enforceability_density_asof,
                        avg(coalesce(sfy.base_fraction, 0.0)) as segment_field_balance_asof,
                        count(distinct sfy.owner_name_harmonized) as segment_owner_count_hist_proxy,
                        case
                            when count(distinct sfy.docdb_family_id) = 0 then 0.0
                            else max(coalesce(oc.owner_family_count, 0)) / count(distinct sfy.docdb_family_id)
                        end as segment_top_owner_share_hist_proxy
                    from segment_family_year sfy
                    left join owner_counts oc
                      on sfy.as_of_year = oc.as_of_year
                     and sfy.segment_key = oc.segment_key
                     and sfy.owner_name_harmonized = oc.owner_name_harmonized
                    group by sfy.as_of_year, sfy.segment_key
                )
                select
                    mts.wipo_industry_code as segment_key,
                    mts.wipo_industry_code,
                    cast(mts.family_priority_year as integer) as as_of_year,
                    sr.current_snapshot_date,
                    case
                        when coalesce(mts.market_state_ui_safe, false) then mts.market_state
                        else null
                    end as segment_heat_state_asof,
                    coalesce(cast(mts.market_state_ui_safe as boolean), false) as segment_market_state_ui_safe_asof,
                    coalesce(cast(mts.is_recent_priority_year_incomplete as boolean), false) as segment_priority_year_incomplete_asof,
                    cast(mts.latest_comparable_year as integer) as segment_latest_comparable_year,
                    coalesce(cast(ssc.segment_family_count_stock_asof as double), 0.0) as segment_family_count_stock_asof,
                    cast(mts.family_count as double) as segment_priority_year_family_count_asof,
                    cast(mts.prior_family_count as double) as segment_prior_priority_year_family_count_asof,
                    case
                        when coalesce(mts.prior_family_count, 0) <= 0 then null
                        else cast(mts.family_count - mts.prior_family_count as double) / cast(mts.prior_family_count as double)
                    end as segment_growth_index_asof,
                    coalesce(sr.segment_owner_count_hist_proxy, 0) as segment_owner_count_hist_proxy_asof,
                    coalesce(sr.segment_blocking_density_asof, 0.0) as segment_blocking_density_asof,
                    coalesce(sr.segment_field_balance_asof, 0.0) as segment_field_balance_asof,
                    coalesce(sr.segment_active_family_count_asof, 0) as segment_active_family_count_asof,
                    coalesce(sr.segment_active_weight_asof, 0.0) as segment_active_weight_asof,
                    coalesce(sr.segment_active_jurisdiction_share_asof, 0.0) as segment_active_jurisdiction_share_asof,
                    coalesce(sr.segment_enforceability_density_asof, 0.0) as segment_enforceability_density_asof,
                    coalesce(sr.segment_top_owner_share_hist_proxy, 0.0) as segment_top_owner_share_hist_proxy,
                    true as historical_compare_safe,
                    false as historical_owner_truth_supported,
                    true as current_owner_bridge_replayed_to_history,
                    false as historical_oecd_supported
                from read_parquet('{market_ts}') mts
                left join segment_rollup sr
                  on mts.wipo_industry_code = sr.segment_key
                 and cast(mts.family_priority_year as integer) = sr.as_of_year
                left join segment_stock_counts ssc
                  on mts.wipo_industry_code = ssc.segment_key
                 and cast(mts.family_priority_year as integer) = ssc.as_of_year
                where cast(mts.family_priority_year as integer) = {int(as_of_year)}
                order by mts.wipo_industry_code, cast(mts.family_priority_year as integer)
            ) to '{chunk_path}' (format parquet, compression zstd)
            """
        )

    if out_market_summary_pit.exists():
        out_market_summary_pit.unlink()
    con.execute(
        f"""
        copy (
            select *
            from read_parquet('{chunk_dir / 'market_summary_pit_*.parquet'}')
        ) to '{out_market_summary_pit}' (format parquet, compression zstd)
        """
    )
    result.outputs.append(str(out_market_summary_pit))
    result.metrics[f"{out_market_summary_pit.stem}_rows"] = parquet_row_count(out_market_summary_pit)
    return result


def build_gold_family_summary(settings: BuildSettings) -> StageResult:
    return _build_gold_selected(
        settings,
        stage_name="gold-family-summary",
        summary="Built the Gold family summary mart from note-aligned Silver family, legal, owner, and OECD contracts.",
        selected_sections={"family_summary"},
    )


def build_gold_family_metrics(settings: BuildSettings) -> StageResult:
    return _build_gold_selected(
        settings,
        stage_name="gold-family-metrics",
        summary="Built Gold family blocking, attacker, and heritage marts from note-aligned Silver legal and citation contracts.",
        selected_sections={"blocking", "family_heritage", "attacker", "family_citation", "family_citation_ts"},
    )


def build_gold_family_citation_chronology(settings: BuildSettings) -> StageResult:
    result = StageResult(
        stage="gold-family-citation-chronology",
        status="success",
        summary="Built a standalone family citation chronology mart directly from the citation event ledger without rebuilding the broader family Gold bundle.",
        methods=[
            "Derived yearly family chronology from the clean citation event ledger rather than sparse PIT feature anchors.",
            "Kept the existing PIT citation-timeseries mart untouched so downstream portfolio readers can migrate separately.",
            "Anchored chronology rows to family priority year, citation years, and the current snapshot year for families with any citation activity.",
        ],
        calculations=[
            "Cumulative forward weighted citations follow the PIT-safe clean-edge-weight definition used in family historical features.",
            "Early-window 5y and 7y counts follow family-level first-citation timing semantics at the citing-family grain.",
        ],
        downstream_impacts=[
            "Family chronology can migrate to this mart immediately without changing portfolio citation aggregation behavior.",
        ],
        doc_refs=[
            "docs/next-phase-v2/81-patentiq-v2-family-citation-chronology-standalone-audit.md",
            "docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md",
        ],
    )
    ensure_dir(settings.gold_dir)
    con = _connect_duckdb_with_temp(settings)

    family_core = settings.silver_dir / "silver_family_core.parquet"
    member_publications = settings.silver_dir / "silver_family_member_publications.parquet"
    cite_network = settings.silver_dir / "silver_enriched_citation_network.parquet"
    out_path = settings.gold_dir / "gold_family_citation_chronology.parquet"
    tmp_out_path = settings.gold_dir / f".{out_path.name}.tmp"

    missing = [str(path) for path in (family_core, member_publications, cite_network) if not path.exists()]
    if missing:
        result.warnings.append(
            "Skipped gold_family_citation_chronology because required sources were not found: " + ", ".join(missing)
        )
        return result

    tmp_out_path.unlink(missing_ok=True)
    placeholder_owner_values = "', '".join(["", "_", "UNKNOWN", "UNKNOWN_OWNER", "UNASSIGNED"])
    snapshot_year = int(settings.snapshot_date[:4])

    con.execute(
        f"""
        copy (
            with main_families as (
                select
                    c.docdb_family_id,
                    cast(
                        coalesce(
                            c.family_priority_year,
                            extract(year from cast(c.family_earliest_priority_date as date)),
                            extract(year from cast(c.snapshot_date as date))
                        ) as integer
                    ) as family_priority_year,
                    cast(
                        coalesce(
                            c.family_earliest_priority_date,
                            make_date(
                                cast(
                                    coalesce(
                                        c.family_priority_year,
                                        extract(year from cast(c.snapshot_date as date))
                                    ) as integer
                                ),
                                1,
                                1
                            )
                        ) as date
                    ) as family_earliest_priority_date,
                    cast(a.family_earliest_publication_date as date) as family_earliest_publication_date,
                    cast(
                        coalesce(
                            a.family_earliest_publication_date,
                            c.family_earliest_priority_date,
                            make_date(
                                cast(
                                    coalesce(
                                        c.family_priority_year,
                                        extract(year from cast(c.snapshot_date as date))
                                    ) as integer
                                ),
                                1,
                                1
                            )
                        ) as date
                    ) as family_citation_anchor_date,
                    cast(c.snapshot_date as date) as snapshot_date
                from read_parquet('{family_core}') c
                left join (
                    select
                        docdb_family_id,
                        min(cast(publn_date as date)) filter (where publn_date is not null) as family_earliest_publication_date
                    from read_parquet('{member_publications}')
                    group by docdb_family_id
                ) a using (docdb_family_id)
                where coalesce(c.is_main_window_family, true)
                  and not coalesce(c.is_out_of_bounds_ghost, false)
            ),
            forward_event_base as (
                select
                    n.cited_docdb_family_id as docdb_family_id,
                    cast(n.citation_date as date) as citation_date,
                    extract(year from cast(n.citation_date as date))::integer as citation_year,
                    cast(n.source_docdb_family_id as bigint) as source_docdb_family_id,
                    trim(cast(coalesce(n.citing_assignee_name, '') as varchar)) as citing_assignee_name,
                    cast(coalesce(n.clean_edge_weight, 0.0) as double) as clean_edge_weight,
                    not coalesce(n.is_out_of_bounds, false)
                      and not coalesce(n.is_intra_family_citation, false)
                      and not coalesce(n.is_self_citation, false) as is_clean
                from read_parquet('{cite_network}') n
                join main_families m
                  on n.cited_docdb_family_id = m.docdb_family_id
                where n.cited_docdb_family_id is not null
                  and n.citation_date is not null
            ),
            backward_event_base as (
                select
                    n.source_docdb_family_id as docdb_family_id,
                    cast(n.citation_date as date) as citation_date,
                    extract(year from cast(n.citation_date as date))::integer as citation_year,
                    cast(n.cited_docdb_family_id as bigint) as cited_docdb_family_id,
                    not coalesce(n.is_out_of_bounds, false)
                      and not coalesce(n.is_intra_family_citation, false)
                      and not coalesce(n.is_self_citation, false) as is_clean
                from read_parquet('{cite_network}') n
                join main_families m
                  on n.source_docdb_family_id = m.docdb_family_id
                where n.source_docdb_family_id is not null
                  and n.citation_date is not null
            ),
            active_families as (
                select distinct docdb_family_id from forward_event_base
                union
                select distinct docdb_family_id from backward_event_base
            ),
            anchor_years as (
                select
                    m.docdb_family_id,
                    m.family_priority_year as as_of_year
                from main_families m
                join active_families a using (docdb_family_id)
                union
                select
                    m.docdb_family_id,
                    extract(year from m.snapshot_date)::integer as as_of_year
                from main_families m
                join active_families a using (docdb_family_id)
                union
                select docdb_family_id, citation_year as as_of_year
                from forward_event_base
                union
                select docdb_family_id, citation_year as as_of_year
                from backward_event_base
            ),
            anchors as (
                select
                    y.docdb_family_id,
                    y.as_of_year,
                    case
                        when y.as_of_year = extract(year from m.snapshot_date)::integer then m.snapshot_date
                        else make_date(y.as_of_year, 12, 31)
                    end as as_of_date,
                    m.family_priority_year,
                    m.family_earliest_priority_date,
                    m.family_citation_anchor_date,
                    m.snapshot_date
                from (
                    select distinct
                        docdb_family_id,
                        as_of_year
                    from anchor_years
                    where as_of_year between {settings.year_window_start} and {snapshot_year}
                ) y
                join main_families m using (docdb_family_id)
            ),
            forward_rollup as (
                select
                    a.docdb_family_id,
                    a.as_of_year,
                    cast(
                        coalesce(sum(case when f.citation_year = a.as_of_year then 1 else 0 end), 0) as bigint
                    ) as forward_citation_event_count_year,
                    cast(
                        coalesce(sum(case when f.citation_date <= a.as_of_date then 1 else 0 end), 0) as bigint
                    ) as pre_asof_forward_citation_event_count,
                    cast(
                        coalesce(sum(case when f.citation_date <= a.as_of_date and f.is_clean then 1 else 0 end), 0) as bigint
                    ) as pre_asof_forward_clean_citation_event_count,
                    cast(
                        coalesce(
                            sum(case when f.citation_date <= a.as_of_date and f.is_clean then f.clean_edge_weight else 0.0 end),
                            0.0
                        ) as double
                    ) as pre_asof_forward_citations_weighted,
                    cast(
                        coalesce(
                            count(
                                distinct case
                                    when f.citation_date <= a.as_of_date
                                     and f.is_clean
                                     and f.source_docdb_family_id is not null
                                    then f.source_docdb_family_id
                                end
                            ),
                            0
                        ) as double
                    ) as pre_asof_unique_citing_family_count,
                    cast(
                        coalesce(
                            count(
                                distinct case
                                    when f.citation_date <= a.as_of_date
                                     and f.is_clean
                                     and trim(upper(coalesce(f.citing_assignee_name, ''))) not in ('{placeholder_owner_values}')
                                    then f.citing_assignee_name
                                end
                            ),
                            0
                        ) as double
                    ) as pre_asof_unique_citing_owner_count,
                    case
                        when count(
                            distinct case
                                when f.citation_date <= a.as_of_date
                                 and f.is_clean
                                 and f.source_docdb_family_id is not null
                                then f.source_docdb_family_id
                            end
                        ) > 0
                        then count(
                            distinct case
                                when f.citation_date <= a.as_of_date
                                 and f.is_clean
                                 and trim(upper(coalesce(f.citing_assignee_name, ''))) not in ('{placeholder_owner_values}')
                                then f.citing_assignee_name
                            end
                        )::double
                        / count(
                            distinct case
                                when f.citation_date <= a.as_of_date
                                 and f.is_clean
                                 and f.source_docdb_family_id is not null
                                then f.source_docdb_family_id
                            end
                        )::double
                        else null::double
                    end as pre_asof_citing_assignee_diversity,
                    avg(
                        case
                            when f.citation_date <= a.as_of_date and f.is_clean then f.clean_edge_weight
                        end
                    )::double as pre_asof_attacker_density_score,
                    min(case when f.citation_date <= a.as_of_date then f.citation_date end) as first_forward_citation_date_asof,
                    max(case when f.citation_date <= a.as_of_date then f.citation_date end) as latest_forward_citation_date_asof,
                    cast(
                        coalesce(
                            count(
                                distinct case
                                    when f.is_clean
                                     and f.source_docdb_family_id is not null
                                     and f.citation_date <= least(a.as_of_date, a.family_citation_anchor_date + interval '5 years')
                                    then f.source_docdb_family_id
                                end
                            ),
                            0
                        ) as double
                    ) as pre_asof_forward_clean_5y,
                    cast(
                        coalesce(
                            count(
                                distinct case
                                    when f.is_clean
                                     and f.source_docdb_family_id is not null
                                     and f.citation_date <= least(a.as_of_date, a.family_citation_anchor_date + interval '7 years')
                                    then f.source_docdb_family_id
                                end
                            ),
                            0
                        ) as double
                    ) as pre_asof_forward_clean_7y
                from anchors a
                left join forward_event_base f
                  on a.docdb_family_id = f.docdb_family_id
                group by a.docdb_family_id, a.as_of_year, a.as_of_date, a.family_earliest_priority_date, a.family_citation_anchor_date
            ),
            backward_rollup as (
                select
                    a.docdb_family_id,
                    a.as_of_year,
                    cast(
                        coalesce(sum(case when b.citation_year = a.as_of_year then 1 else 0 end), 0) as bigint
                    ) as backward_citation_event_count_year,
                    cast(
                        coalesce(sum(case when b.citation_date <= a.as_of_date then 1 else 0 end), 0) as bigint
                    ) as pre_asof_backward_citation_event_count,
                    cast(
                        coalesce(sum(case when b.citation_date <= a.as_of_date and b.is_clean then 1 else 0 end), 0) as bigint
                    ) as pre_asof_backward_clean_citation_event_count,
                    cast(
                        coalesce(
                            count(
                                distinct case
                                    when b.citation_date <= a.as_of_date
                                     and b.is_clean
                                     and b.cited_docdb_family_id is not null
                                    then b.cited_docdb_family_id
                                end
                            ),
                            0
                        ) as bigint
                    ) as pre_asof_distinct_cited_family_count
                from anchors a
                left join backward_event_base b
                  on a.docdb_family_id = b.docdb_family_id
                group by a.docdb_family_id, a.as_of_year, a.as_of_date
            )
            select
                a.docdb_family_id,
                a.as_of_year,
                a.as_of_date,
                true as is_observed_as_of_snapshot,
                f.forward_citation_event_count_year,
                f.pre_asof_forward_citation_event_count,
                f.pre_asof_forward_clean_citation_event_count,
                f.pre_asof_forward_citations_weighted,
                f.pre_asof_unique_citing_family_count,
                f.pre_asof_unique_citing_owner_count,
                b.backward_citation_event_count_year,
                b.pre_asof_backward_citation_event_count,
                b.pre_asof_backward_clean_citation_event_count,
                b.pre_asof_distinct_cited_family_count,
                f.pre_asof_citing_assignee_diversity,
                f.pre_asof_attacker_density_score,
                f.first_forward_citation_date_asof,
                f.latest_forward_citation_date_asof,
                cast(a.as_of_date >= a.family_citation_anchor_date + interval '5 years' as boolean) as window_5y_closed,
                cast(a.as_of_date >= a.family_citation_anchor_date + interval '7 years' as boolean) as window_7y_closed,
                f.pre_asof_forward_clean_5y,
                f.pre_asof_forward_clean_7y,
                null::double as data_completeness_pct_asof,
                true as historical_citation_safe,
                case
                    when coalesce(f.pre_asof_forward_citation_event_count, 0) > 0
                      or coalesce(b.pre_asof_backward_citation_event_count, 0) > 0 then 'high'
                    else 'limited'
                end as chronology_support_level,
                '{settings.method_version}' as method_version
            from anchors a
            left join forward_rollup f
              on a.docdb_family_id = f.docdb_family_id
             and a.as_of_year = f.as_of_year
            left join backward_rollup b
              on a.docdb_family_id = b.docdb_family_id
             and a.as_of_year = b.as_of_year
            order by a.docdb_family_id, a.as_of_year
        ) to '{tmp_out_path}' (format parquet, compression zstd)
        """
    )
    tmp_out_path.replace(out_path)
    result.outputs.append(str(out_path))
    result.metrics[f"{out_path.stem}_rows"] = parquet_row_count(out_path)
    return result


def build_gold_history(settings: BuildSettings) -> StageResult:
    return _build_gold_selected(
        settings,
        stage_name="gold-history",
        summary="Built Gold blocking-power and field-contribution history marts from replay-aligned Silver history sidecars.",
        selected_sections={"field_ts", "field_legacy", "blocking_ts"},
    )


def build_gold_history_fields(settings: BuildSettings) -> StageResult:
    return _build_gold_selected(
        settings,
        stage_name="gold-history-fields",
        summary="Built Gold field-contribution history marts from replay-aligned Silver branch and field history.",
        selected_sections={"field_ts", "field_legacy"},
    )


def build_gold_history_blocking(settings: BuildSettings) -> StageResult:
    return _build_gold_selected(
        settings,
        stage_name="gold-history-blocking",
        summary="Built Gold blocking-power history marts from replay-aligned Silver legal and citation history.",
        selected_sections={"blocking_ts"},
    )


def build_gold_portfolio(settings: BuildSettings) -> StageResult:
    return _build_gold_selected(
        settings,
        stage_name="gold-portfolio",
        summary="Built Gold portfolio marts from the family-owner bridge and Gold family/history contracts.",
        selected_sections={
            "portfolio_field_ts",
            "portfolio",
            "portfolio_threat",
            "portfolio_heritage",
            "portfolio_forecast",
            "portfolio_citation_summary",
            "portfolio_citation_family_leaderboard",
            "portfolio_citation_ts",
            "portfolio_citation_attacker",
            "portfolio_citation_field",
            "portfolio_citation_jurisdiction",
            "portfolio_filing_timeseries",
        },
    )


def build_gold_market_semantic(settings: BuildSettings) -> StageResult:
    return _build_gold_selected(
        settings,
        stage_name="gold-market-semantic",
        summary="Built Gold Market Intelligence and semantic-context marts from note-aligned Silver and Gold family outputs.",
        selected_sections={
            "market_segments",
            "market_timeseries",
            "market_overview",
            "market_citation_trend",
            "market_citation_jurisdiction",
            "market_citation_attacker",
            "semantic",
        },
    )


def build_gold(settings: BuildSettings) -> StageResult:
    """Build the full Gold mart suite by running the sectioned Gold stages in dependency order."""
    subresults = [
        build_gold_family_summary(settings),
        build_gold_family_metrics(settings),
        build_gold_history_fields(settings),
        build_gold_history_blocking(settings),
        build_gold_portfolio(settings),
        build_gold_market_semantic(settings),
    ]
    result = StageResult(
        stage="gold",
        status="success",
        summary="Built the full Gold mart suite from note-aligned Silver contracts via sectioned Gold stages.",
        methods=subresults[0].methods,
        calculations=subresults[0].calculations,
        doc_refs=subresults[0].doc_refs,
        downstream_impacts=subresults[0].downstream_impacts,
    )
    for subresult in subresults:
        result.outputs.extend(subresult.outputs)
        result.warnings.extend(subresult.warnings)
        result.metrics.update(subresult.metrics)
    return result

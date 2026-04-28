from __future__ import annotations

import argparse
from pathlib import Path

import duckdb
import pandas as pd
from lightgbm import Booster

from _bootstrap import bootstrap


ETL_ROOT = bootstrap()
REPO_ROOT = ETL_ROOT.parent

from patentiq_etl.ml.phase_grant import _office_support_map, _priority_tier, _score_pending_grant_frame  # noqa: E402


def _owner_frame(owner_harmonized: str, feature_path: Path, owner_bridge_path: Path, branch_history_path: Path) -> pd.DataFrame:
    con = duckdb.connect()
    try:
        query = f"""
        with owner_families as (
            select distinct cast(docdb_family_id as varchar) as docdb_family_id
            from read_parquet('{owner_bridge_path}')
            where owner_name_harmonized = ?
              and coalesce(is_primary_owner, false) = true
        ),
        current_pending_pairs as (
            select docdb_family_id, jurisdiction_code, snapshot_date
            from (
                select
                    cast(b.docdb_family_id as varchar) as docdb_family_id,
                    b.jurisdiction_code,
                    cast(b.snapshot_date as date) as snapshot_date,
                    coalesce(b.pending_branch_flag, false) as pending_branch_flag,
                    row_number() over (
                        partition by cast(b.docdb_family_id as varchar), b.jurisdiction_code
                        order by b.snapshot_year desc, b.snapshot_date desc
                    ) as rn
                from read_parquet('{branch_history_path}') b
                join owner_families o
                  on cast(b.docdb_family_id as varchar) = o.docdb_family_id
            ) ranked
            where rn = 1
              and pending_branch_flag
        ),
        latest_pending as (
            select f.*
            from read_parquet('{feature_path}') f
            join current_pending_pairs c
              on cast(f.docdb_family_id as varchar) = c.docdb_family_id
             and f.jurisdiction_code = c.jurisdiction_code
             and cast(f.as_of_date as date) = c.snapshot_date
        )
        select
            cast(docdb_family_id as varchar) as docdb_family_id,
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
            jurisdiction_is_major_office
        from latest_pending
        order by jurisdiction_code, docdb_family_id
        """
        return con.execute(query, [owner_harmonized]).df()
    finally:
        con.close()


def build_owner_cache(owner_harmonized: str, output_path: Path) -> None:
    ml_dir = REPO_ROOT / "etl" / "data" / "ml"
    silver_dir = REPO_ROOT / "etl" / "data" / "silver"
    feature_path = ml_dir / "ml_feature_pending_grant_pipeline.parquet"
    owner_bridge_path = silver_dir / "silver_family_owner_bridge.parquet"
    branch_history_path = silver_dir / "silver_branch_status_history_dense.parquet"
    model_card_path = ml_dir / "model_card_pending_grant_pipeline.json"
    calibration_path = ml_dir / "pending_grant_pipeline_calibration.json"
    model_12m_path = ml_dir / "pending_grant_pipeline_12m_model.txt"
    model_24m_path = ml_dir / "pending_grant_pipeline_24m_model.txt"

    import json

    model_card = json.loads(model_card_path.read_text(encoding="utf-8"))
    calibration_payload = json.loads(calibration_path.read_text(encoding="utf-8"))
    office_support_map = _office_support_map(model_card)

    owner_frame = _owner_frame(
        owner_harmonized,
        feature_path=feature_path,
        owner_bridge_path=owner_bridge_path,
        branch_history_path=branch_history_path,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if owner_frame.empty:
        owner_frame = pd.DataFrame(
            columns=[
                "docdb_family_id",
                "jurisdiction_code",
                "primary_wipo_field",
                "grant_probability_calibrated_12m",
                "grant_probability_calibrated_24m",
                "pending_grant_rank_within_office_12m",
                "pending_grant_percentile_within_office_12m",
                "pending_grant_rank_within_office_24m",
                "pending_grant_percentile_within_office_24m",
                "office_support_level",
            ]
        )
        tmp_path = output_path.with_suffix(".tmp.parquet")
        owner_frame.to_parquet(tmp_path, index=False)
        tmp_path.replace(output_path)
        return

    owner_frame = _score_pending_grant_frame(
        owner_frame,
        booster_12m=Booster(model_file=str(model_12m_path)),
        booster_24m=Booster(model_file=str(model_24m_path)),
        calibration_payload=calibration_payload,
        feature_encoders=model_card.get("feature_encoders", {}) if isinstance(model_card, dict) else {},
        office_support_map=office_support_map,
    )

    for horizon in ("12m", "24m"):
        probability_col = f"grant_probability_calibrated_{horizon}"
        rank_col = f"pending_grant_rank_within_office_{horizon}"
        percentile_col = f"pending_grant_percentile_within_office_{horizon}"
        priority_col = f"pending_grant_priority_tier_{horizon}"

        owner_frame[rank_col] = (
            owner_frame.groupby("jurisdiction_code")[probability_col]
            .rank(method="first", ascending=False)
            .astype("int64")
        )
        office_sizes = owner_frame.groupby("jurisdiction_code")[probability_col].transform("count")
        owner_frame[percentile_col] = (
            100.0 - ((owner_frame[rank_col] - 1).astype(float) / office_sizes.clip(lower=1).sub(1).clip(lower=1)) * 100.0
        ).clip(lower=0.0, upper=100.0)
        owner_frame[priority_col] = _priority_tier(owner_frame[percentile_col])

    keep_columns = [
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
        "grant_probability_raw_12m",
        "grant_probability_calibrated_12m",
        "grant_probability_raw_24m",
        "grant_probability_calibrated_24m",
        "pending_grant_rank_within_office_12m",
        "pending_grant_percentile_within_office_12m",
        "pending_grant_priority_tier_12m",
        "pending_grant_rank_within_office_24m",
        "pending_grant_percentile_within_office_24m",
        "pending_grant_priority_tier_24m",
        "office_support_level",
    ]
    tmp_path = output_path.with_suffix(".tmp.parquet")
    owner_frame[keep_columns].to_parquet(tmp_path, index=False)
    tmp_path.replace(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an owner-scoped pending-grant cache parquet.")
    parser.add_argument("--owner-harmonized", required=True, help="Resolved owner_name_harmonized token.")
    parser.add_argument("--output-path", required=True, help="Output parquet path.")
    args = parser.parse_args()

    build_owner_cache(owner_harmonized=str(args.owner_harmonized), output_path=Path(args.output_path))


if __name__ == "__main__":
    main()

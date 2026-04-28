from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, LGBMRegressor

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet, write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.gold.build_gold import (
    _build_gold_selected,
    _build_portfolio_forecast_from_models,
    build_gold,
    build_gold_cpc_importance_pit,
    build_gold_family_citation_chronology,
    build_gold_family_classification_jurisdiction_pit,
    build_gold_family_classification_mix_pit,
    build_gold_market_leaderboard_pit,
    build_gold_market_cpc_jurisdiction_trend_pit,
    build_gold_market_cpc_trend_pit,
    build_gold_family_compare_pit,
    build_gold_market_summary_pit,
    build_gold_portfolio_classification_jurisdiction_pit,
    build_gold_portfolio_compare_pit,
    build_gold_portfolio_classification_mix_pit,
    build_gold_portfolio_summary_pit,
)
from patentiq_etl.gold import run as gold_run
from patentiq_etl.ml.phase03 import _prepare_training_matrix as _prepare_phase03_matrix
from patentiq_etl.ml.phase04 import _prepare_phase04_matrix


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="test-release",
        snapshot_date="2026-03-15",
        year_window_start=2007,
        year_window_end=2026,
        heritage_backfill_start=1996,
        heritage_backfill_end=2006,
        azure_publish_enabled=False,
        vector_sample_pct=1.0,
        active_grant_only_for_semantic=True,
        method_version="test_method_v1",
        semantic_embedding_method="stable_hash_embedding_mvp",
        semantic_ann_method="manifest_only_placeholder",
        patstat_source_mode="local_files",
        register_source_mode="local_files",
        epab_source_mode="local_files",
        uspto_source_mode="local_files",
        refs_source_mode="local_files",
        tip_env="PROD",
        raw_patstat_dir=root / "etl/data/raw/patstat",
        raw_register_dir=root / "etl/data/raw/register",
        raw_uspto_dir=root / "etl/data/raw/uspto",
        raw_epab_dir=root / "etl/data/raw/epab",
        raw_refs_dir=root / "etl/data/raw/refs",
        bounded_patstat_dir=root / "etl/data/raw-bounded/patstat",
        bounded_register_dir=root / "etl/data/raw-bounded/register",
        bounded_uspto_dir=root / "etl/data/raw-bounded/uspto",
        bounded_epab_dir=root / "etl/data/raw-bounded/epab",
        bounded_refs_dir=root / "etl/data/raw-bounded/refs",
        bounded_seed_dir=root / "etl/data/raw-bounded/_seeds",
        bronze_dir=root / "etl/data/bronze",
        silver_dir=root / "etl/data/silver",
        gold_dir=root / "etl/data/gold",
        ml_dir=root / "etl/data/ml",
        vectors_dir=root / "etl/data/vectors",
        releases_dir=root / "etl/data/releases",
        manifests_dir=root / "etl/manifests",
        journal_path=root / "etl/ETL_IMPLEMENTATION_LOG.md",
        ref_techn_field_ipc=root / "etl/data/raw/refs/wipo_techn_field_ipc.csv",
        scope_type="mega_cluster_bounded",
        field_source="wipo_industry_code",
        selected_wipo_fields=["Computer technology"],
        thresholds={},
        azure={},
        execution={},
    )


def test_build_gold_uses_primary_owner_for_family_and_bridge_for_portfolio(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    silver_dir = ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "family_earliest_priority_date": date(2020, 1, 1),
                "family_priority_year": 2020,
                "is_main_window_family": True,
                "is_heritage_backfill_family": False,
                "is_out_of_bounds_ghost": False,
                "family_size_docdb": 2,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            },
            {
                "docdb_family_id": 2,
                "inpadoc_family_id": 22,
                "family_earliest_priority_date": date(2021, 1, 1),
                "family_priority_year": 2021,
                "is_main_window_family": True,
                "is_heritage_backfill_family": False,
                "is_out_of_bounds_ghost": False,
                "family_size_docdb": 1,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            },
        ],
        silver_dir / "silver_family_core.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "owner_country": "US",
                "owner_scope_appln_count": 2,
                "family_distinct_owner_count": 2,
                "primary_owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
            {
                "docdb_family_id": 2,
                "owner_name_harmonized": "GAMMA",
                "owner_name_display": "Gamma",
                "owner_country": "US",
                "owner_scope_appln_count": 1,
                "family_distinct_owner_count": 1,
                "primary_owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
        ],
        silver_dir / "silver_assignee_harmonized.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "owner_country": "US",
                "owner_scope_appln_count": 2,
                "owner_display_variant_count": 1,
                "owner_country_variant_count": 1,
                "family_distinct_owner_count": 2,
                "owner_family_rank": 1,
                "is_primary_owner": True,
                "owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "BETA",
                "owner_name_display": "Beta",
                "owner_country": "GB",
                "owner_scope_appln_count": 1,
                "owner_display_variant_count": 1,
                "owner_country_variant_count": 1,
                "family_distinct_owner_count": 2,
                "owner_family_rank": 2,
                "is_primary_owner": False,
                "owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
            {
                "docdb_family_id": 2,
                "owner_name_harmonized": "GAMMA",
                "owner_name_display": "Gamma",
                "owner_country": "US",
                "owner_scope_appln_count": 1,
                "owner_display_variant_count": 1,
                "owner_country_variant_count": 1,
                "family_distinct_owner_count": 1,
                "owner_family_rank": 1,
                "is_primary_owner": True,
                "owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
        ],
        silver_dir / "silver_family_owner_bridge.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "covered_wipo_fields": ["Computer technology"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 1,
                "family_field_fraction": 1.0,
                "family_earliest_priority_date": date(2020, 1, 1),
                "in_scope_appln_count": 2,
            },
            {
                "docdb_family_id": 2,
                "covered_wipo_fields": ["Computer technology"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 1,
                "family_field_fraction": 1.0,
                "family_earliest_priority_date": date(2021, 1, 1),
                "in_scope_appln_count": 1,
            },
        ],
        silver_dir / "silver_family_wipo_fields.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "raw_family_citation_count": 5,
                "family_backward_patent_citation_count": 1,
                "family_backward_citations_clean": 1,
                "out_of_bounds_citation_count": 0.0,
                "out_of_bounds_citation_share": 0.0,
                "family_forward_citations_raw": 3,
                "family_forward_citations_clean": 3,
                "family_forward_citations_weighted": 3.0,
                "family_fwd_cits5": 2,
                "family_fwd_cits7": 3,
                "family_backward_npl_citation_count": 1,
                "family_science_grounding_score": 0.4,
                "family_rcf_score": 1.0,
                "family_adjusted_citation_score_raw": 10.0,
            },
            {
                "docdb_family_id": 2,
                "raw_family_citation_count": 0,
                "family_backward_patent_citation_count": 0,
                "family_backward_citations_clean": 0,
                "out_of_bounds_citation_count": 0.0,
                "out_of_bounds_citation_share": 0.0,
                "family_forward_citations_raw": 0,
                "family_forward_citations_clean": 0,
                "family_forward_citations_weighted": 0.0,
                "family_fwd_cits5": 0,
                "family_fwd_cits7": 0,
                "family_backward_npl_citation_count": 0,
                "family_science_grounding_score": 0.0,
                "family_rcf_score": 0.0,
                "family_adjusted_citation_score_raw": 0.0,
            },
        ],
        silver_dir / "silver_family_citation_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2025, 12, 31),
                "as_of_year": 2025,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_size_docdb_asof": 2.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 1.0,
                "family_blocking_power_score_asof": 0.7,
                "family_enforceability_score_asof": 1.0,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 2.5,
                "family_rcf_score_asof": 0.8,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.4,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 0.8,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2026, 3, 15),
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_size_docdb_asof": 2.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 1.0,
                "family_blocking_power_score_asof": 0.75,
                "family_enforceability_score_asof": 1.0,
                "pre_asof_forward_citations_clean": 3.0,
                "pre_asof_forward_citations_weighted": 3.5,
                "family_rcf_score_asof": 1.0,
                "pre_asof_unique_citing_family_count": 3.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.25,
                "data_completeness_pct_asof": 0.9,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2025, 12, 31),
                "as_of_year": 2025,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "pending_emerging",
                "active_jurisdiction_count_asof": 0.0,
                "active_grant_branch_count_asof": 0.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_size_docdb_asof": 1.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 0.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 1.0,
                "family_blocking_power_score_asof": 0.0,
                "family_enforceability_score_asof": 0.0,
                "pre_asof_forward_citations_clean": 0.0,
                "pre_asof_forward_citations_weighted": 0.0,
                "family_rcf_score_asof": 0.0,
                "pre_asof_unique_citing_family_count": 0.0,
                "pre_asof_citing_assignee_diversity": 0.0,
                "pre_asof_attacker_density_score": 0.0,
                "data_completeness_pct_asof": 0.3,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2026, 3, 15),
                "as_of_year": 2026,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "pending_emerging",
                "active_jurisdiction_count_asof": 0.0,
                "active_grant_branch_count_asof": 0.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_size_docdb_asof": 1.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 0.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 1.0,
                "family_blocking_power_score_asof": 0.0,
                "family_enforceability_score_asof": 0.0,
                "pre_asof_forward_citations_clean": 0.0,
                "pre_asof_forward_citations_weighted": 0.0,
                "family_rcf_score_asof": 0.0,
                "pre_asof_unique_citing_family_count": 0.0,
                "pre_asof_citing_assignee_diversity": 0.0,
                "pre_asof_attacker_density_score": 0.0,
                "data_completeness_pct_asof": 0.3,
            },
        ],
        silver_dir / "silver_family_feature_snapshot_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "snapshot_date": date(2026, 3, 15),
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "source_auth": "US",
                "is_up_unrolled": False,
                "is_classic_validation": False,
                "is_global_member": False,
                "family_jurisdiction_count": 1,
                "active_jurisdiction_count": 1,
                "family_grant_publication_count": 1,
                "family_field_fraction": 1.0,
                "final_market_multiplier": 1.0,
                "global_family_filings": 10,
                "global_field_trend_coefficient": 1.0,
                "local_family_filings": 5,
                "local_field_trend_coefficient": 1.0,
                "branch_coefficient_mode": "localized",
                "active_branch_flag": True,
                "is_opposed_branch": False,
                "representative_branch_stage": "STANDARD_GRANT",
                "branch_state_label": "ACTIVE_GRANT",
                "branch_stage_multiplier": 1.0,
                "branch_enforceability_contribution_raw": 2.0,
            },
            {
                "docdb_family_id": 2,
                "snapshot_date": date(2026, 3, 15),
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "source_auth": "US",
                "is_up_unrolled": False,
                "is_classic_validation": False,
                "is_global_member": False,
                "family_jurisdiction_count": 1,
                "active_jurisdiction_count": 0,
                "family_grant_publication_count": 0,
                "family_field_fraction": 1.0,
                "final_market_multiplier": 1.0,
                "global_family_filings": 10,
                "global_field_trend_coefficient": 1.0,
                "local_family_filings": 5,
                "local_field_trend_coefficient": 1.0,
                "branch_coefficient_mode": "localized",
                "active_branch_flag": False,
                "is_opposed_branch": False,
                "representative_branch_stage": "PENDING_APPLICATION",
                "branch_state_label": "PENDING_ONLY",
                "branch_stage_multiplier": 0.2,
                "branch_enforceability_contribution_raw": 0.0,
            },
        ],
        silver_dir / "silver_family_enforceability_branches.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "snapshot_date": date(2026, 3, 15),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 1.0,
                "family_field_enforceability_contribution_score": 2.0,
                "family_field_heritage_contribution_score": 10.0,
                "method_version": settings.method_version,
            },
            {
                "docdb_family_id": 2,
                "snapshot_date": date(2026, 3, 15),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 1.0,
                "family_field_enforceability_contribution_score": 0.0,
                "family_field_heritage_contribution_score": 0.0,
                "method_version": settings.method_version,
            },
        ],
        silver_dir / "silver_family_field_contributions.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "fully_active",
                "active_jurisdiction_count": 1,
                "active_grant_branch_count": 1,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": True,
                "is_dead_family": False,
            },
            {
                "docdb_family_id": 2,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "pending_emerging",
                "active_jurisdiction_count": 0,
                "active_grant_branch_count": 0,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": False,
                "is_dead_family": False,
            },
        ],
        silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "snapshot_year": 2025,
                "snapshot_date": date(2025, 12, 31),
                "family_composite_status": "pending_emerging",
                "active_jurisdiction_count": 0,
                "active_grant_branch_count": 0,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": False,
                "is_dead_family": False,
            },
            {
                "docdb_family_id": 1,
                "snapshot_year": 2026,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "fully_active",
                "active_jurisdiction_count": 1,
                "active_grant_branch_count": 1,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": True,
                "is_dead_family": False,
            },
            {
                "docdb_family_id": 2,
                "snapshot_year": 2025,
                "snapshot_date": date(2025, 12, 31),
                "family_composite_status": "pending_emerging",
                "active_jurisdiction_count": 0,
                "active_grant_branch_count": 0,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": False,
                "is_dead_family": False,
            },
            {
                "docdb_family_id": 2,
                "snapshot_year": 2026,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "pending_emerging",
                "active_jurisdiction_count": 0,
                "active_grant_branch_count": 0,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": False,
                "is_dead_family": False,
            },
        ],
        silver_dir / "silver_family_status_history.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2025,
                "snapshot_date": date(2025, 12, 31),
                "source_auth": "US",
                "is_up_unrolled": False,
                "is_classic_validation": False,
                "is_global_member": False,
                "last_grant_event_date": None,
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
                "last_negative_event_date": None,
                "last_opposition_event_date": None,
                "last_pending_event_date": date(2025, 1, 1),
                "replay_branch_state": "PENDING_ONLY",
                "active_branch_flag": False,
                "lapsed_or_expired_flag": False,
                "pending_branch_flag": True,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2026,
                "snapshot_date": date(2026, 3, 15),
                "source_auth": "US",
                "is_up_unrolled": False,
                "is_classic_validation": False,
                "is_global_member": False,
                "last_grant_event_date": date(2026, 1, 1),
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
                "last_negative_event_date": None,
                "last_opposition_event_date": None,
                "last_pending_event_date": date(2025, 1, 1),
                "replay_branch_state": "ACTIVE_GRANT",
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "pending_branch_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "US",
                "snapshot_year": 2025,
                "snapshot_date": date(2025, 12, 31),
                "source_auth": "US",
                "is_up_unrolled": False,
                "is_classic_validation": False,
                "is_global_member": False,
                "last_grant_event_date": None,
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
                "last_negative_event_date": None,
                "last_opposition_event_date": None,
                "last_pending_event_date": date(2025, 2, 1),
                "replay_branch_state": "PENDING_ONLY",
                "active_branch_flag": False,
                "lapsed_or_expired_flag": False,
                "pending_branch_flag": True,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "US",
                "snapshot_year": 2026,
                "snapshot_date": date(2026, 3, 15),
                "source_auth": "US",
                "is_up_unrolled": False,
                "is_classic_validation": False,
                "is_global_member": False,
                "last_grant_event_date": None,
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
                "last_negative_event_date": None,
                "last_opposition_event_date": None,
                "last_pending_event_date": date(2025, 2, 1),
                "replay_branch_state": "PENDING_ONLY",
                "active_branch_flag": False,
                "lapsed_or_expired_flag": False,
                "pending_branch_flag": True,
                "opposed_branch_flag": False,
            },
        ],
        silver_dir / "silver_branch_status_history_dense.parquet",
    )
    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "US",
                "snapshot_year": 2025,
                "gdp_value": 1.0,
                "ip_score": 40.0,
                "gdp_tier_weight": 1.0,
                "final_market_multiplier": 1.0,
            },
            {
                "jurisdiction_code": "US",
                "snapshot_year": 2026,
                "gdp_value": 1.0,
                "ip_score": 40.0,
                "gdp_tier_weight": 1.0,
                "final_market_multiplier": 1.0,
            },
        ],
        silver_dir / "silver_tiered_market_weighting.parquet",
    )
    write_pylist_parquet(
        [
            {
                "snapshot_year": 2025,
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "local_family_filings": 1,
                "prior_period_local_family_filings": 1,
                "local_growth_rate": 0.0,
                "local_trend_coefficient": 1.0,
                "counting_unit": "family_count",
                "family_model": settings.scope_type,
                "method_version": settings.method_version,
            },
            {
                "snapshot_year": 2026,
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "local_family_filings": 1,
                "prior_period_local_family_filings": 1,
                "local_growth_rate": 0.0,
                "local_trend_coefficient": 1.0,
                "counting_unit": "family_count",
                "family_model": settings.scope_type,
                "method_version": settings.method_version,
            },
        ],
        silver_dir / "silver_local_tech_trends_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {
                "snapshot_year": 2025,
                "wipo_industry_code": "Computer technology",
                "global_family_filings": 1,
                "prior_period_global_family_filings": 1,
                "global_growth_rate": 0.0,
                "global_trend_coefficient": 1.0,
                "counting_unit": "family_count",
                "family_model": settings.scope_type,
                "method_version": settings.method_version,
            },
            {
                "snapshot_year": 2026,
                "wipo_industry_code": "Computer technology",
                "global_family_filings": 1,
                "prior_period_global_family_filings": 1,
                "global_growth_rate": 0.0,
                "global_trend_coefficient": 1.0,
                "counting_unit": "family_count",
                "family_model": settings.scope_type,
                "method_version": settings.method_version,
            },
        ],
        silver_dir / "silver_global_tech_trends_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 100,
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "wipo_industry_code": "Computer technology",
                "family_earliest_priority_date": date(2020, 1, 1),
                "appln_filing_date": date(2020, 1, 1),
            },
            {
                "appln_id": 200,
                "docdb_family_id": 2,
                "inpadoc_family_id": 22,
                "wipo_industry_code": "Computer technology",
                "family_earliest_priority_date": date(2021, 1, 1),
                "appln_filing_date": date(2021, 1, 1),
            },
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "priority_year": 2020,
                "primary_wipo_field": "Computer technology",
                "family_adjusted_citation_score_raw": 10.0,
                "family_jurisdiction_count": 1,
                "family_grant_publication_count": 1.0,
                "family_generality_score": 0.5,
                "family_generality_percentile": 80.0,
                "family_originality_score": 0.4,
                "family_originality_percentile": 70.0,
                "family_radicalness_score": 0.3,
                "family_radicalness_percentile": 60.0,
                "family_backward_npl_citation_count": 1,
                "family_backward_npl_citation_percentile": 50.0,
                "family_science_grounding_score": 0.4,
                "family_science_grounding_percentile": 55.0,
                "family_fwd_cits5": 2,
                "family_fwd_cits5_percentile": 80.0,
                "family_fwd_cits7": 3,
                "family_fwd_cits7_percentile": 90.0,
                "family_size_docdb": 2,
                "family_size_percentile": 85.0,
                "family_grant_lag_days": 100.0,
                "family_grant_lag_speed_percentile": 65.0,
                "family_quality_index_4_score": 0.8,
                "family_quality_index_4_policy": "claims_omitted_family_first_variant",
                "family_quality_index_6_score": 0.7,
                "family_quality_index_6_policy": "claims_omitted_family_first_variant",
                "oecd_quality_percentile": 88.0,
                "oecd_quality_proxy_score": 0.8,
            },
            {
                "docdb_family_id": 2,
                "priority_year": 2021,
                "primary_wipo_field": "Computer technology",
                "family_adjusted_citation_score_raw": 0.0,
                "family_jurisdiction_count": 1,
                "family_grant_publication_count": 0.0,
                "family_generality_score": 0.0,
                "family_generality_percentile": 10.0,
                "family_originality_score": 0.0,
                "family_originality_percentile": 10.0,
                "family_radicalness_score": 0.0,
                "family_radicalness_percentile": 10.0,
                "family_backward_npl_citation_count": 0,
                "family_backward_npl_citation_percentile": 10.0,
                "family_science_grounding_score": 0.0,
                "family_science_grounding_percentile": 10.0,
                "family_fwd_cits5": 0,
                "family_fwd_cits5_percentile": 10.0,
                "family_fwd_cits7": 0,
                "family_fwd_cits7_percentile": 10.0,
                "family_size_docdb": 1,
                "family_size_percentile": 20.0,
                "family_grant_lag_days": None,
                "family_grant_lag_speed_percentile": 0.0,
                "family_quality_index_4_score": 0.1,
                "family_quality_index_4_policy": "claims_omitted_family_first_variant",
                "family_quality_index_6_score": None,
                "family_quality_index_6_policy": None,
                "oecd_quality_percentile": 15.0,
                "oecd_quality_proxy_score": 0.1,
            },
        ],
        silver_dir / "silver_family_oecd_quality.parquet",
    )
    write_pylist_parquet(
        [
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 1,
                "is_out_of_bounds": False,
                "citing_pat_publn_id": 100,
                "cited_pat_publn_id": 200,
                "citation_date": date(2025, 6, 1),
                "citation_year": 2025,
                "citing_jurisdiction_code": "US",
                "citing_kind_code": "A1",
                "citing_primary_wipo_field": "Computer technology",
                "citing_assignee_name": "OMEGA",
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "clean_edge_weight": 1.0,
                "citing_stage_multiplier": 0.2,
                "citing_market_multiplier": 1.0,
                "raw_trend_coefficient": 1.0,
                "clipped_trend_coefficient": 1.0,
                "trend_source": "localized",
                "citation_lethality_score": 1.5,
            }
        ],
        silver_dir / "silver_enriched_citation_network.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "family_jurisdiction_count": 1,
                "active_jurisdiction_count": 1.0,
                "active_grant_branch_count": 1.0,
                "lapsed_jurisdiction_count": 0.0,
                "family_grant_publication_count": 1.0,
                "family_application_publication_count": 1.0,
                "family_market_coverage_weight_raw": 1.0,
                "family_coverage_stability_score": 1.0,
            },
            {
                "docdb_family_id": 2,
                "family_jurisdiction_count": 1,
                "active_jurisdiction_count": 0.0,
                "active_grant_branch_count": 0.0,
                "lapsed_jurisdiction_count": 0.0,
                "family_grant_publication_count": 0.0,
                "family_application_publication_count": 1.0,
                "family_market_coverage_weight_raw": 0.0,
                "family_coverage_stability_score": 0.0,
            },
        ],
        silver_dir / "silver_family_coverage_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {"segment_id": "Computer technology", "wipo_industry_code": "Computer technology", "market_state": "rising", "total_family_count": 2.0, "latest_year": 2026},
        ],
        silver_dir / "silver_market_intelligence_segments.parquet",
    )
    write_pylist_parquet(
        [
            {
                "family_priority_year": 2025,
                "wipo_industry_code": "Computer technology",
                "family_count": 1,
                "prior_family_count": 1,
                "market_state": "stable",
                "is_recent_priority_year_incomplete": True,
                "market_state_ui_safe": False,
                "latest_comparable_year": None,
                "snapshot_date": date(2026, 3, 15),
            },
            {
                "family_priority_year": 2026,
                "wipo_industry_code": "Computer technology",
                "family_count": 2,
                "prior_family_count": 1,
                "market_state": "rising",
                "is_recent_priority_year_incomplete": True,
                "market_state_ui_safe": False,
                "latest_comparable_year": None,
                "snapshot_date": date(2026, 3, 15),
            },
        ],
        silver_dir / "silver_market_intelligence_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "representative_appln_id": 1,
                "representative_publn_id": 100,
                "representative_stage": "STANDARD_GRANT",
                "representative_source_type": "EPAB_CLAIM",
                "representative_claim_1_en": "Claim",
                "representative_abstract_en": None,
                "text_provenance": "EPAB",
                "is_abstract_fallback": False,
            }
        ],
        silver_dir / "silver_family_text_representative.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "has_ep_grant": True, "is_semantic_candidate": True, "is_in_vector_sample": True},
            {"docdb_family_id": 2, "has_ep_grant": False, "is_semantic_candidate": False, "is_in_vector_sample": False},
        ],
        silver_dir / "silver_semantic_sampling_eligibility.parquet",
    )

    result = build_gold(settings).finish()

    assert result.status == "success"
    con = duckdb.connect()
    family_rows = con.execute(
        """
        select
            docdb_family_id,
            owner_name_harmonized,
            owner_name_display,
            family_distinct_owner_count,
            oecd_quality_percentile,
            is_semantic_candidate
        from read_parquet(?)
        order by docdb_family_id
        """,
        [str(settings.gold_dir / "gold_family_summary.parquet")],
    ).fetchall()
    assert family_rows == [
        (1, "ALPHA", "Alpha", 2, 88.0, True),
        (2, "GAMMA", "Gamma", 1, 15.0, False),
    ]

    blocking_rows = con.execute(
        """
        select
            docdb_family_id,
            family_market_threat_score_raw,
            family_adjusted_citation_score_raw,
            family_blocking_citation_score_raw,
            round(family_raw_absolute_blocking_power, 6)
        from read_parquet(?)
        order by docdb_family_id
        """,
        [str(settings.gold_dir / "gold_family_blocking_power.parquet")],
    ).fetchall()
    assert blocking_rows[0] == (1, 2.0, 10.0, 1.5, 1.620702)

    blocking_ts_rows = con.execute(
        """
        select
            docdb_family_id,
            snapshot_date,
            ui_blocking_power_score,
            overall_legal_enforceability_score,
            adjusted_citation_score_raw,
            blocking_citation_score_raw
        from read_parquet(?)
        where snapshot_date = date '2026-03-15'
        order by docdb_family_id
        """,
        [str(settings.gold_dir / "gold_family_blocking_power_timeseries.parquet")],
    ).fetchall()
    assert blocking_ts_rows == [
        (1, date(2026, 3, 15), 100.0, 2.0, 1.5, 1.5),
        (2, date(2026, 3, 15), 0.0, 0.0, 0.0, 0.0),
    ]

    portfolio_rows = con.execute(
        """
        select owner_name_harmonized, portfolio_family_count_within_mega_cluster
        from read_parquet(?)
        order by owner_name_harmonized
        """,
        [str(settings.gold_dir / "gold_portfolio_summary.parquet")],
    ).fetchall()
    assert portfolio_rows == [("ALPHA", 1), ("BETA", 1), ("GAMMA", 1)]

    portfolio_field_rows = con.execute(
        """
        select owner_name_harmonized, wipo_field, active_family_count, enforceability_score, heritage_score
        from read_parquet(?)
        order by owner_name_harmonized, wipo_field
        """,
        [str(settings.gold_dir / "gold_portfolio_field_timeseries.parquet")],
    ).fetchall()
    assert portfolio_field_rows == [
        ("ALPHA", "Computer technology", 1, 2.0, 10.0),
        ("BETA", "Computer technology", 1, 2.0, 10.0),
        ("GAMMA", "Computer technology", 0, 0.0, 0.0),
    ]

    attacker_rows = con.execute(
        """
        select docdb_family_id, citing_assignee_name, citation_count, citation_lethality_sum
        from read_parquet(?)
        order by docdb_family_id, citing_assignee_name
        """,
        [str(settings.gold_dir / "gold_family_attacker_summary.parquet")],
    ).fetchall()
    assert attacker_rows == [(1, "OMEGA", 1, 1.5)]

    family_citation_rows = con.execute(
        """
        select
            docdb_family_id,
            family_forward_citations_clean,
            citing_assignee_diversity,
            citation_support_level,
            citation_influence_index
        from read_parquet(?)
        order by docdb_family_id
        """,
        [str(settings.gold_dir / "gold_family_citation_summary.parquet")],
    ).fetchall()
    assert family_citation_rows == [
        (1, 3.0, 0.5, "high", 100.0),
        (2, 0.0, 0.0, "low", 0.0),
    ]

    family_citation_ts_rows = con.execute(
        """
        select
            docdb_family_id,
            as_of_year,
            pre_asof_forward_citations_clean,
            citation_support_level
        from read_parquet(?)
        where docdb_family_id = 1
        order by as_of_year
        """,
        [str(settings.gold_dir / "gold_family_citation_timeseries_pit.parquet")],
    ).fetchall()
    assert family_citation_ts_rows == [
        (1, 2025, 2.0, "high"),
        (1, 2026, 3.0, "high"),
    ]

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "publn_date": date(2020, 6, 1),
            },
            {
                "docdb_family_id": 2,
                "publn_date": date(2021, 6, 1),
            },
        ],
        silver_dir / "silver_family_member_publications.parquet",
    )

    chronology_result = build_gold_family_citation_chronology(settings).finish()
    assert chronology_result.status == "success"

    chronology_rows = con.execute(
        """
        select
            docdb_family_id,
            as_of_year,
            pre_asof_forward_citation_event_count,
            pre_asof_forward_clean_citation_event_count,
            pre_asof_forward_citations_weighted,
            pre_asof_unique_citing_family_count,
            pre_asof_backward_citation_event_count,
            chronology_support_level
        from read_parquet(?)
        where docdb_family_id = 1
        order by as_of_year
        """,
        [str(settings.gold_dir / "gold_family_citation_chronology.parquet")],
    ).fetchall()
    assert chronology_rows == [
        (1, 2020, 0, 0, 0.0, 0.0, 0, "limited"),
        (1, 2025, 1, 1, 1.0, 1.0, 0, "high"),
        (1, 2026, 1, 1, 1.0, 1.0, 0, "high"),
    ]

    portfolio_citation_summary_rows = con.execute(
        """
        select
            owner_name_harmonized,
            as_of_year,
            family_count,
            forward_citations_clean_total,
            backward_citations_clean_total
        from read_parquet(?)
        order by owner_name_harmonized, as_of_year
        """,
        [str(settings.gold_dir / "gold_portfolio_citation_summary.parquet")],
    ).fetchall()
    assert portfolio_citation_summary_rows == [
        ("ALPHA", 2025, 1, 1.0, 0.0),
        ("ALPHA", 2026, 1, 1.0, 0.0),
        ("GAMMA", 2025, 1, 0.0, 0.0),
        ("GAMMA", 2026, 1, 0.0, 0.0),
    ]

    portfolio_citation_attacker_rows = con.execute(
        """
        select
            owner_name_harmonized,
            year,
            citing_assignee_name,
            citation_event_count,
            citation_lethality_sum_raw
        from read_parquet(?)
        order by owner_name_harmonized, year, citing_assignee_name
        """,
        [str(settings.gold_dir / "gold_portfolio_attacker_momentum.parquet")],
    ).fetchall()
    assert portfolio_citation_attacker_rows == [
        ("ALPHA", 2025, "OMEGA", 1, 1.5),
    ]

    portfolio_citation_field_rows = con.execute(
        """
        select
            owner_name_harmonized,
            year,
            wipo_field,
            citation_event_count,
            citing_assignee_count
        from read_parquet(?)
        order by owner_name_harmonized, year, wipo_field
        """,
        [str(settings.gold_dir / "gold_portfolio_citation_pressure_by_field.parquet")],
    ).fetchall()
    assert portfolio_citation_field_rows == [
        ("ALPHA", 2025, "Computer technology", 1, 1),
    ]

    portfolio_citation_jurisdiction_rows = con.execute(
        """
        select
            owner_name_harmonized,
            year,
            jurisdiction_code,
            citation_event_count,
            citing_assignee_count
        from read_parquet(?)
        order by owner_name_harmonized, year, jurisdiction_code
        """,
        [str(settings.gold_dir / "gold_portfolio_citation_pressure_by_jurisdiction.parquet")],
    ).fetchall()
    assert portfolio_citation_jurisdiction_rows == [
        ("ALPHA", 2025, "US", 1, 1),
    ]

    market_citation_trend_rows = con.execute(
        """
        select
            as_of_year,
            wipo_industry_code,
            citation_event_count,
            distinct_citing_assignee_count,
            distinct_citing_jurisdiction_count,
            market_citation_state,
            market_state_reference
        from read_parquet(?)
        order by as_of_year, wipo_industry_code
        """,
        [str(settings.gold_dir / "gold_market_citation_trend_pit.parquet")],
    ).fetchall()
    assert market_citation_trend_rows == [
        (2025, "Computer technology", 1, 1, 1, "stable", "stable"),
    ]

    market_citation_jurisdiction_rows = con.execute(
        """
        select
            as_of_year,
            wipo_industry_code,
            jurisdiction_code,
            citation_event_count,
            distinct_citing_assignee_count
        from read_parquet(?)
        order by as_of_year, wipo_industry_code, jurisdiction_code
        """,
        [str(settings.gold_dir / "gold_market_citation_pressure_by_jurisdiction_pit.parquet")],
    ).fetchall()
    assert market_citation_jurisdiction_rows == [
        (2025, "Computer technology", "US", 1, 1),
    ]

    market_citation_attacker_rows = con.execute(
        """
        select
            as_of_year,
            wipo_industry_code,
            citing_assignee_name,
            citation_event_count,
            distinct_citing_jurisdiction_count
        from read_parquet(?)
        order by as_of_year, wipo_industry_code, citing_assignee_name
        """,
        [str(settings.gold_dir / "gold_market_attacker_leaderboard_pit.parquet")],
    ).fetchall()
    assert market_citation_attacker_rows == [
        (2025, "Computer technology", "OMEGA", 1, 1),
    ]


def test_blocking_power_gates_pending_families_with_extreme_citation_signal(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    silver_dir = ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "family_earliest_priority_date": date(2020, 1, 1),
                "family_priority_year": 2020,
                "is_main_window_family": True,
                "is_heritage_backfill_family": False,
                "is_out_of_bounds_ghost": False,
                "family_size_docdb": 2,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            },
            {
                "docdb_family_id": 2,
                "inpadoc_family_id": 22,
                "family_earliest_priority_date": date(2024, 1, 1),
                "family_priority_year": 2024,
                "is_main_window_family": True,
                "is_heritage_backfill_family": False,
                "is_out_of_bounds_ghost": False,
                "family_size_docdb": 1,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            },
        ],
        silver_dir / "silver_family_core.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "covered_wipo_fields": ["Computer technology"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 1,
                "family_field_fraction": 1.0,
                "family_earliest_priority_date": date(2020, 1, 1),
                "in_scope_appln_count": 1,
            },
            {
                "docdb_family_id": 2,
                "covered_wipo_fields": ["Computer technology"],
                "primary_wipo_field": "Computer technology",
                "family_tech_breadth_wipo_count": 1,
                "family_field_fraction": 1.0,
                "family_earliest_priority_date": date(2024, 1, 1),
                "in_scope_appln_count": 1,
            },
        ],
        silver_dir / "silver_family_wipo_fields.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "raw_family_citation_count": 0,
                "family_backward_patent_citation_count": 0,
                "family_backward_citations_clean": 0,
                "out_of_bounds_citation_count": 0.0,
                "out_of_bounds_citation_share": 0.0,
                "family_forward_citations_raw": 3,
                "family_forward_citations_clean": 3,
                "family_forward_citations_weighted": 3.0,
                "family_fwd_cits5": 2,
                "family_fwd_cits7": 3,
                "family_backward_npl_citation_count": 0,
                "family_science_grounding_score": 0.0,
                "family_rcf_score": 1.0,
                "family_adjusted_citation_score_raw": 5.0,
            },
            {
                "docdb_family_id": 2,
                "raw_family_citation_count": 0,
                "family_backward_patent_citation_count": 0,
                "family_backward_citations_clean": 0,
                "out_of_bounds_citation_count": 0.0,
                "out_of_bounds_citation_share": 0.0,
                "family_forward_citations_raw": 1,
                "family_forward_citations_clean": 1,
                "family_forward_citations_weighted": 0.1,
                "family_fwd_cits5": 1,
                "family_fwd_cits7": 1,
                "family_backward_npl_citation_count": 0,
                "family_science_grounding_score": 0.0,
                "family_rcf_score": 5913.0,
                "family_adjusted_citation_score_raw": 5913.0,
            },
        ],
        silver_dir / "silver_family_citation_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 1,
                "citation_date": date(2025, 6, 1),
                "citation_year": 2025,
                "citation_lethality_score": 1.0,
            },
            {
                "source_docdb_family_id": 11,
                "cited_docdb_family_id": 2,
                "citation_date": date(2025, 7, 1),
                "citation_year": 2025,
                "citation_lethality_score": 5913.0,
            },
        ],
        silver_dir / "silver_enriched_citation_network.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "branch_enforceability_contribution_raw": 2.0},
            {"docdb_family_id": 2, "branch_enforceability_contribution_raw": 0.0},
        ],
        silver_dir / "silver_family_enforceability_branches.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "fully_active",
                "active_jurisdiction_count": 1,
                "active_grant_branch_count": 1,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": True,
                "is_dead_family": False,
            },
            {
                "docdb_family_id": 2,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "pending_emerging",
                "active_jurisdiction_count": 0,
                "active_grant_branch_count": 0,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": False,
                "is_dead_family": False,
            },
        ],
        silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "snapshot_year": 2026,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "fully_active",
                "active_jurisdiction_count": 1,
                "active_grant_branch_count": 1,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": True,
                "is_dead_family": False,
            },
            {
                "docdb_family_id": 2,
                "snapshot_year": 2026,
                "snapshot_date": date(2026, 3, 15),
                "family_composite_status": "pending_emerging",
                "active_jurisdiction_count": 0,
                "active_grant_branch_count": 0,
                "lapsed_jurisdiction_count": 0,
                "opposed_branch_count": 0,
                "has_any_active_grant": False,
                "is_dead_family": False,
            },
        ],
        silver_dir / "silver_family_status_history.parquet",
    )

    result = _build_gold_selected(
        settings,
        stage_name="gold-blocking-test",
        summary="blocking-only test build",
        selected_sections={"blocking"},
    ).finish()

    assert result.status == "success"
    con = duckdb.connect()
    rows = con.execute(
        """
        select
            docdb_family_id,
            family_adjusted_citation_score_raw,
            family_blocking_citation_score_raw,
            round(family_raw_absolute_blocking_power, 6) as raw_blocking,
            round(family_ui_blocking_power_score, 6) as ui_score
        from read_parquet(?)
        order by docdb_family_id
        """,
        [str(settings.gold_dir / "gold_family_blocking_power.parquet")],
    ).fetchall()

    assert rows[0] == (1, 5.0, 1.0, 1.542602, 100.0)
    assert rows[0][3] > rows[1][3]
    assert rows[1][4] == 0.0
    assert rows[1][3] < 1.0


def test_build_gold_field_timeseries_uses_application_weighted_field_share_asof(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    silver_dir = ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "family_earliest_priority_date": date(2024, 1, 10),
                "family_priority_year": 2024,
                "is_main_window_family": True,
                "is_heritage_backfill_family": False,
                "is_out_of_bounds_ghost": False,
                "family_size_docdb": 4,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_family_core.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "snapshot_year": 2024},
            {"docdb_family_id": 1, "snapshot_year": 2025},
        ],
        silver_dir / "silver_family_status_history.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "family_field_fraction": 0.5,
                "active_branch_flag": True,
                "final_market_multiplier": 1.0,
                "branch_state_label": "ACTIVE_GRANT",
            },
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "wipo_industry_code": "Digital communication",
                "family_field_fraction": 0.5,
                "active_branch_flag": True,
                "final_market_multiplier": 1.0,
                "branch_state_label": "ACTIVE_GRANT",
            },
        ],
        silver_dir / "silver_family_enforceability_branches.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "snapshot_date": date(2026, 3, 15),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 0.5,
                "family_field_enforceability_contribution_score": 0.8,
                "family_field_heritage_contribution_score": 0.4,
                "method_version": settings.method_version,
            },
            {
                "docdb_family_id": 1,
                "snapshot_date": date(2026, 3, 15),
                "wipo_industry_code": "Digital communication",
                "base_fraction": 0.5,
                "family_field_enforceability_contribution_score": 0.6,
                "family_field_heritage_contribution_score": 0.3,
                "method_version": settings.method_version,
            },
        ],
        silver_dir / "silver_family_field_contributions.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2024,
                "replay_branch_state": "ACTIVE_GRANT",
            },
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2025,
                "replay_branch_state": "ACTIVE_GRANT",
            },
        ],
        silver_dir / "silver_branch_status_history_dense.parquet",
    )
    write_pylist_parquet(
        [
            {"jurisdiction_code": "US", "snapshot_year": 2024, "final_market_multiplier": 1.0},
            {"jurisdiction_code": "US", "snapshot_year": 2025, "final_market_multiplier": 1.0},
        ],
        silver_dir / "silver_tiered_market_weighting.parquet",
    )
    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "snapshot_year": 2024,
                "local_trend_coefficient": 1.0,
            },
            {
                "jurisdiction_code": "US",
                "wipo_industry_code": "Digital communication",
                "snapshot_year": 2024,
                "local_trend_coefficient": 1.0,
            },
            {
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "snapshot_year": 2025,
                "local_trend_coefficient": 1.0,
            },
            {
                "jurisdiction_code": "US",
                "wipo_industry_code": "Digital communication",
                "snapshot_year": 2025,
                "local_trend_coefficient": 1.0,
            },
        ],
        silver_dir / "silver_local_tech_trends_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {
                "wipo_industry_code": "Computer technology",
                "snapshot_year": 2024,
                "global_trend_coefficient": 1.0,
            },
            {
                "wipo_industry_code": "Digital communication",
                "snapshot_year": 2024,
                "global_trend_coefficient": 1.0,
            },
            {
                "wipo_industry_code": "Computer technology",
                "snapshot_year": 2025,
                "global_trend_coefficient": 1.0,
            },
            {
                "wipo_industry_code": "Digital communication",
                "snapshot_year": 2025,
                "global_trend_coefficient": 1.0,
            },
        ],
        silver_dir / "silver_global_tech_trends_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {"cited_docdb_family_id": 1, "citation_year": 2024, "citation_lethality_score": 1.0},
            {"cited_docdb_family_id": 1, "citation_year": 2025, "citation_lethality_score": 1.0},
        ],
        silver_dir / "silver_enriched_citation_network.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 100,
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "wipo_industry_code": "Computer technology",
                "family_earliest_priority_date": date(2024, 1, 10),
                "appln_filing_date": date(2024, 1, 10),
                "appln_auth": "US",
                "appln_kind": "A",
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            },
            {
                "appln_id": 101,
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "wipo_industry_code": "Computer technology",
                "family_earliest_priority_date": date(2024, 1, 10),
                "appln_filing_date": date(2024, 5, 20),
                "appln_auth": "US",
                "appln_kind": "A",
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            },
            {
                "appln_id": 102,
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "wipo_industry_code": "Computer technology",
                "family_earliest_priority_date": date(2024, 1, 10),
                "appln_filing_date": date(2025, 2, 15),
                "appln_auth": "US",
                "appln_kind": "A",
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            },
            {
                "appln_id": 102,
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "wipo_industry_code": "Digital communication",
                "family_earliest_priority_date": date(2024, 1, 10),
                "appln_filing_date": date(2025, 2, 15),
                "appln_auth": "US",
                "appln_kind": "A",
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            },
            {
                "appln_id": 103,
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "wipo_industry_code": "Digital communication",
                "family_earliest_priority_date": date(2024, 1, 10),
                "appln_filing_date": date(2025, 3, 10),
                "appln_auth": "US",
                "appln_kind": "A",
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            },
        ],
        silver_dir / "silver_scope_appln_seed.parquet",
    )

    result = _build_gold_selected(
        settings,
        stage_name="gold-field-timeseries-test",
        summary="field-timeseries test build",
        selected_sections={"field_ts", "field_legacy"},
    ).finish()

    assert result.status == "success"
    con = duckdb.connect()
    rows = con.execute(
        """
        select
            snapshot_year,
            wipo_industry_code,
            round(base_fraction, 6) as base_fraction,
            round(field_share_asof, 6) as field_share_asof,
            field_share_method,
            round(coalesce(field_evidence_weight_asof, 0.0), 6) as field_evidence_weight_asof,
            field_application_count_asof,
            family_application_count_asof
        from read_parquet(?)
        order by snapshot_year, wipo_industry_code
        """,
        [str(settings.gold_dir / "gold_family_field_contributions_timeseries.parquet")],
    ).fetchall()

    assert rows == [
        (2024, "Computer technology", 0.5, 1.0, "appln_weighted_field_share", 2.0, 2, 2),
        (2024, "Digital communication", 0.5, 0.0, "appln_weighted_field_share", 0.0, 0, 2),
        (2025, "Computer technology", 0.5, 0.625, "appln_weighted_field_share", 2.5, 3, 4),
        (2025, "Digital communication", 0.5, 0.375, "appln_weighted_field_share", 1.5, 2, 4),
        (2026, "Computer technology", 0.5, 0.625, "appln_weighted_field_share", 2.5, 3, 4),
        (2026, "Digital communication", 0.5, 0.375, "appln_weighted_field_share", 1.5, 2, 4),
    ]


def test_build_gold_family_compare_pit_materializes_observed_family_history_for_compare(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "primary_wipo_field": "Computer technology",
                "covered_wipo_fields": ["Computer technology", "Digital communication"],
                "oecd_quality_percentile": 88.0,
                "snapshot_date": date(2026, 3, 15),
            }
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 1, 1),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 4.0,
                "active_grant_branch_count_asof": 2.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 4.0,
                "family_coverage_stability_score_asof": 0.75,
                "family_size_docdb_asof": 3.0,
                "family_tech_breadth_wipo_count_asof": 2.0,
                "family_blocking_power_score_asof": 0.6,
                "family_enforceability_score_asof": 0.7,
                "family_field_contribution_primary_asof": 0.8,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 1.5,
                "family_rcf_score_asof": 0.3,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.25,
                "data_completeness_pct_asof": 0.9,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 1, 1),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 3.0,
                "active_grant_branch_count_asof": 2.0,
                "lapsed_jurisdiction_count_asof": 1.0,
                "family_jurisdiction_count_asof": 4.0,
                "family_coverage_stability_score_asof": 0.7,
                "family_size_docdb_asof": 3.0,
                "family_tech_breadth_wipo_count_asof": 2.0,
                "family_blocking_power_score_asof": 0.65,
                "family_enforceability_score_asof": 0.68,
                "family_field_contribution_primary_asof": 0.82,
                "pre_asof_forward_citations_clean": 3.0,
                "pre_asof_forward_citations_weighted": 2.5,
                "family_rcf_score_asof": 0.35,
                "pre_asof_unique_citing_family_count": 3.0,
                "pre_asof_citing_assignee_diversity": 0.55,
                "pre_asof_attacker_density_score": 0.3,
                "data_completeness_pct_asof": 0.92,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2027, 1, 1),
                "as_of_year": 2027,
                "is_observed_as_of_snapshot": False,
                "family_composite_status_asof": "pending_emerging",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 0.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 0.2,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.1,
                "family_enforceability_score_asof": 0.1,
                "family_field_contribution_primary_asof": 0.2,
                "pre_asof_forward_citations_clean": 0.0,
                "pre_asof_forward_citations_weighted": 0.0,
                "family_rcf_score_asof": 0.05,
                "pre_asof_unique_citing_family_count": 0.0,
                "pre_asof_citing_assignee_diversity": 0.0,
                "pre_asof_attacker_density_score": 0.0,
                "data_completeness_pct_asof": 0.5,
            },
        ],
        settings.silver_dir / "silver_family_feature_snapshot_pit.parquet",
    )

    result = build_gold_family_compare_pit(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select
            docdb_family_id,
            as_of_year,
            is_latest_observed_year,
            owner_name_harmonized_current,
            primary_wipo_field_current,
            family_active_jurisdiction_share_asof,
            historical_compare_safe,
            historical_oecd_supported,
            current_owner_metadata_only
        from read_parquet(?)
        order by docdb_family_id, as_of_year
        """,
        [str(settings.gold_dir / "gold_family_compare_pit.parquet")],
    ).fetchall()
    assert rows == [
        (1, 2021, False, "ALPHA", "Computer technology", 1.0, True, False, True),
        (1, 2022, True, "ALPHA", "Computer technology", 0.75, True, False, True),
    ]


def test_build_gold_family_compare_pit_prefers_dense_family_year_pit_when_present(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "primary_wipo_field": "Computer technology",
                "covered_wipo_fields": ["Computer technology"],
                "oecd_quality_percentile": 88.0,
                "snapshot_date": date(2026, 3, 15),
            }
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 4.0,
                "active_grant_branch_count_asof": 2.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_size_docdb_asof": 3.0,
                "family_jurisdiction_count_asof": 4.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 0.8,
                "family_blocking_power_score_asof": 0.6,
                "family_enforceability_score_asof": 0.7,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 1.5,
                "family_rcf_score_asof": 0.3,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.25,
                "data_completeness_pct_asof": 0.9,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 3.0,
                "active_grant_branch_count_asof": 2.0,
                "lapsed_jurisdiction_count_asof": 1.0,
                "family_size_docdb_asof": 3.0,
                "family_jurisdiction_count_asof": 4.0,
                "family_coverage_stability_score_asof": 0.75,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 0.82,
                "family_blocking_power_score_asof": 0.65,
                "family_enforceability_score_asof": 0.68,
                "pre_asof_forward_citations_clean": 3.0,
                "pre_asof_forward_citations_weighted": 2.5,
                "family_rcf_score_asof": 0.35,
                "pre_asof_unique_citing_family_count": 3.0,
                "pre_asof_citing_assignee_diversity": 0.55,
                "pre_asof_attacker_density_score": 0.3,
                "data_completeness_pct_asof": 0.92,
            },
        ],
        settings.silver_dir / "silver_family_feature_snapshot_pit_dense.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 1, 1),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_size_docdb_asof": 1.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 0.2,
                "family_blocking_power_score_asof": 0.2,
                "family_enforceability_score_asof": 0.2,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 1.0,
                "family_rcf_score_asof": 0.1,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.2,
                "pre_asof_attacker_density_score": 0.1,
                "data_completeness_pct_asof": 0.5,
            }
        ],
        settings.silver_dir / "silver_family_feature_snapshot_pit.parquet",
    )

    result = build_gold_family_compare_pit(settings).finish()
    assert result.status == "success"
    assert "Dense family-year PIT layer not found" not in " ".join(result.warnings)

    con = duckdb.connect()
    rows = con.execute(
        """
        select docdb_family_id, as_of_year, family_blocking_power_score_asof
        from read_parquet(?)
        order by docdb_family_id, as_of_year
        """,
        [str(settings.gold_dir / "gold_family_compare_pit.parquet")],
    ).fetchall()
    assert rows == [
        (1, 2021, 0.6),
        (1, 2022, 0.65),
    ]


def test_build_gold_portfolio_summary_pit_aggregates_family_compare_rows_with_owner_bridge_caveat(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "owner_country": "US",
                "owner_scope_appln_count": 2,
                "owner_display_variant_count": 1,
                "owner_country_variant_count": 1,
                "family_distinct_owner_count": 1,
                "owner_family_rank": 1,
                "is_primary_owner": True,
                "owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
            {
                "docdb_family_id": 2,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "owner_country": "US",
                "owner_scope_appln_count": 2,
                "owner_display_variant_count": 1,
                "owner_country_variant_count": 1,
                "family_distinct_owner_count": 1,
                "owner_family_rank": 1,
                "is_primary_owner": True,
                "owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
        ],
        settings.silver_dir / "silver_family_owner_bridge.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 1, 1),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": True,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 88.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 4.0,
                "active_grant_branch_count_asof": 2.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 4.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 0.8,
                "family_size_docdb_asof": 3.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 10.0,
                "family_enforceability_score_asof": 0.7,
                "family_field_contribution_primary_asof": 0.8,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 1.5,
                "family_rcf_score_asof": 0.3,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.25,
                "data_completeness_pct_asof": 0.9,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2021, 1, 1),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": True,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Digital communication",
                "covered_wipo_fields_current": ["Digital communication"],
                "oecd_quality_percentile_current": 70.0,
                "family_composite_status_asof": "partially_lapsed",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 1.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 0.5,
                "family_coverage_stability_score_asof": 0.6,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 30.0,
                "family_enforceability_score_asof": 0.4,
                "family_field_contribution_primary_asof": 0.6,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.8,
                "family_rcf_score_asof": 0.2,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.3,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 0.8,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
        ],
        settings.gold_dir / "gold_family_compare_pit.parquet",
    )

    result = build_gold_portfolio_summary_pit(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select
            owner_name_harmonized,
            as_of_year,
            portfolio_family_count_hist_proxy,
            portfolio_active_family_count_asof,
            portfolio_active_jurisdiction_count_asof,
            portfolio_avg_blocking_power_score_asof,
            portfolio_top_family_blocking_share_asof,
            historical_owner_truth_supported,
            current_owner_bridge_replayed_to_history
        from read_parquet(?)
        order by owner_name_harmonized, as_of_year
        """,
        [str(settings.gold_dir / "gold_portfolio_summary_pit.parquet")],
    ).fetchall()
    assert rows == [
        ("ALPHA", 2021, 2, 2, 5.0, 20.0, 0.75, False, True),
    ]


def test_build_gold_family_classification_mix_pit_materializes_family_year_summary(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology", "Digital communication"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 2,
                "ipc_subclasses_asof": ["H04L"],
                "cpc_sections_asof": ["H"],
                "cpc_subclasses_asof": ["H04L", "H04W"],
                "cpc_main_groups_asof": ["H04L45/00", "H04W4/00"],
                "ipc_subclass_count_asof": 1,
                "cpc_section_count_asof": 1,
                "cpc_subclass_count_asof": 2,
                "cpc_main_group_count_asof": 2,
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology", "Digital communication"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 2,
                "ipc_subclasses_asof": ["H04L"],
                "cpc_sections_asof": ["H"],
                "cpc_subclasses_asof": ["H04L", "H04W"],
                "cpc_main_groups_asof": ["H04L45/00", "H04W4/00"],
                "ipc_subclass_count_asof": 1,
                "cpc_section_count_asof": 1,
                "cpc_subclass_count_asof": 2,
                "cpc_main_group_count_asof": 2,
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Semiconductors"],
                "primary_wipo_field_asof": "Semiconductors",
                "wipo_field_count_asof": 1,
                "ipc_subclasses_asof": ["H01L"],
                "cpc_sections_asof": ["H"],
                "cpc_subclasses_asof": ["H01L"],
                "cpc_main_groups_asof": ["H01L21/00"],
                "ipc_subclass_count_asof": 1,
                "cpc_section_count_asof": 1,
                "cpc_subclass_count_asof": 1,
                "cpc_main_group_count_asof": 1,
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
            },
        ],
        settings.silver_dir / "silver_family_classification_pit_dense.parquet",
    )

    result = build_gold_family_classification_mix_pit(settings).finish()
    assert result.status == "success", result.warnings

    con = duckdb.connect()
    rows = con.execute(
        """
        select
            docdb_family_id,
            as_of_year,
            cpc_main_group_count_asof,
            classification_concentration_hhi_asof,
            top_cpc_main_group_asof,
            top_cpc_main_group_share_asof,
            classification_breadth_band_asof,
            classification_visibility_policy,
            classification_membership_replayed_to_history,
            historical_classification_truth_supported,
            historical_compare_safe
        from read_parquet(?)
        order by docdb_family_id, as_of_year
        """,
        [str(settings.gold_dir / "gold_family_classification_mix_pit.parquet")],
    ).fetchall()
    assert rows == [
        (1, 2021, 2.0, 0.5, "H04L45/00", 0.5, "balanced", "stable_family_classification_replay", True, False, True),
        (1, 2022, 2.0, 0.5, "H04L45/00", 0.5, "balanced", "stable_family_classification_replay", True, False, True),
        (2, 2021, 1.0, 1.0, "H01L21/00", 1.0, "focused", "stable_family_classification_replay", True, False, True),
    ]


def test_build_gold_portfolio_classification_mix_pit_aggregates_owner_year_rows(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology", "Digital communication"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 2.0,
                "ipc_subclasses_asof": ["H04L"],
                "cpc_sections_asof": ["H"],
                "cpc_subclasses_asof": ["H04L", "H04W"],
                "cpc_main_groups_asof": ["H04L45/00", "H04W4/00"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 2.0,
                "cpc_main_group_count_asof": 2.0,
                "classification_concentration_hhi_asof": 0.5,
                "classification_entropy_asof": 0.693147,
                "top_cpc_main_group_asof": "H04L45/00",
                "top_cpc_main_group_share_asof": 0.5,
                "classification_breadth_band_asof": "balanced",
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["G06F"],
                "cpc_sections_asof": ["G"],
                "cpc_subclasses_asof": ["G06F"],
                "cpc_main_groups_asof": ["G06F3/00"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 1.0,
                "classification_concentration_hhi_asof": 1.0,
                "classification_entropy_asof": 0.0,
                "top_cpc_main_group_asof": "G06F3/00",
                "top_cpc_main_group_share_asof": 1.0,
                "classification_breadth_band_asof": "focused",
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
        ],
        settings.gold_dir / "gold_family_classification_mix_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology", "Digital communication"],
                "oecd_quality_percentile_current": 80.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 2.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 2.0,
                "family_blocking_power_score_asof": 0.6,
                "family_enforceability_score_asof": 0.8,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 1.5,
                "family_rcf_score_asof": 0.4,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.4,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 0.9,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 75.0,
                "family_composite_status_asof": "pending_emerging",
                "active_jurisdiction_count_asof": 0.0,
                "active_grant_branch_count_asof": 0.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 0.0,
                "family_coverage_stability_score_asof": 0.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.2,
                "family_enforceability_score_asof": 0.3,
                "family_field_contribution_primary_asof": 0.4,
                "pre_asof_forward_citations_clean": 0.0,
                "pre_asof_forward_citations_weighted": 0.0,
                "family_rcf_score_asof": 0.0,
                "pre_asof_unique_citing_family_count": 0.0,
                "pre_asof_citing_assignee_diversity": None,
                "pre_asof_attacker_density_score": None,
                "data_completeness_pct_asof": 0.7,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
        ],
        settings.gold_dir / "gold_family_compare_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "owner_country": "US",
                "owner_scope_appln_count": 2,
                "owner_display_variant_count": 1,
                "owner_country_variant_count": 1,
                "family_distinct_owner_count": 1,
                "owner_family_rank": 1,
                "is_primary_owner": True,
                "owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
            {
                "docdb_family_id": 2,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "owner_country": "US",
                "owner_scope_appln_count": 1,
                "owner_display_variant_count": 1,
                "owner_country_variant_count": 1,
                "family_distinct_owner_count": 1,
                "owner_family_rank": 1,
                "is_primary_owner": True,
                "owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
        ],
        settings.silver_dir / "silver_family_owner_bridge.parquet",
    )

    result = build_gold_portfolio_classification_mix_pit(settings).finish()
    assert result.status == "success", result.warnings

    con = duckdb.connect()
    rows = con.execute(
        """
        select
            owner_name_harmonized,
            as_of_year,
            classification_type,
            classification_code,
            portfolio_family_count_hist_proxy,
            portfolio_active_family_count_asof,
            portfolio_family_count_in_classification_asof,
            portfolio_active_family_count_in_classification_asof,
            round(portfolio_family_share_asof, 6),
            round(portfolio_active_family_share_asof, 6),
            round(portfolio_blocking_density_asof, 6),
            round(portfolio_enforceability_density_asof, 6),
            historical_owner_truth_supported,
            current_owner_bridge_replayed_to_history,
            classification_rank_within_owner_year
        from read_parquet(?)
        order by classification_type, classification_rank_within_owner_year, classification_code
        """,
        [str(settings.gold_dir / "gold_portfolio_classification_mix_pit.parquet")],
    ).fetchall()
    assert rows == [
        ("ALPHA", 2021, "CPC_MAIN_GROUP", "H04L45/00", 2.0, 1.0, 1.0, 1.0, 0.5, 1.0, 0.6, 0.8, False, True, 1),
        ("ALPHA", 2021, "CPC_MAIN_GROUP", "H04W4/00", 2.0, 1.0, 1.0, 1.0, 0.5, 1.0, 0.6, 0.8, False, True, 2),
        ("ALPHA", 2021, "CPC_MAIN_GROUP", "G06F3/00", 2.0, 1.0, 1.0, 0.0, 0.5, 0.0, 0.2, 0.3, False, True, 3),
        ("ALPHA", 2021, "WIPO_FIELD", "Computer technology", 2.0, 1.0, 2.0, 1.0, 1.0, 1.0, 0.4, 0.55, False, True, 1),
        ("ALPHA", 2021, "WIPO_FIELD", "Digital communication", 2.0, 1.0, 1.0, 1.0, 0.5, 1.0, 0.6, 0.8, False, True, 2),
    ]


def test_build_gold_classification_jurisdiction_pit_materializes_family_portfolio_and_market_slices(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["H04L"],
                "cpc_sections_asof": ["H"],
                "cpc_subclasses_asof": ["H04L"],
                "cpc_main_groups_asof": ["H04L45/00"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 1.0,
                "classification_concentration_hhi_asof": 1.0,
                "classification_entropy_asof": 0.0,
                "top_cpc_main_group_asof": "H04L45/00",
                "top_cpc_main_group_share_asof": 1.0,
                "classification_breadth_band_asof": "focused",
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["H04L"],
                "cpc_sections_asof": ["H"],
                "cpc_subclasses_asof": ["H04L"],
                "cpc_main_groups_asof": ["H04L45/00"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 1.0,
                "classification_concentration_hhi_asof": 1.0,
                "classification_entropy_asof": 0.0,
                "top_cpc_main_group_asof": "H04L45/00",
                "top_cpc_main_group_share_asof": 1.0,
                "classification_breadth_band_asof": "focused",
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["G06F"],
                "cpc_sections_asof": ["G"],
                "cpc_subclasses_asof": ["G06F"],
                "cpc_main_groups_asof": ["G06F3/00"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 1.0,
                "classification_concentration_hhi_asof": 1.0,
                "classification_entropy_asof": 0.0,
                "top_cpc_main_group_asof": "G06F3/00",
                "top_cpc_main_group_share_asof": 1.0,
                "classification_breadth_band_asof": "focused",
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "docdb_family_id": 3,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["G06F"],
                "cpc_sections_asof": ["G"],
                "cpc_subclasses_asof": ["G06F"],
                "cpc_main_groups_asof": ["G06F3/00"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 1.0,
                "classification_concentration_hhi_asof": 1.0,
                "classification_entropy_asof": 0.0,
                "top_cpc_main_group_asof": "G06F3/00",
                "top_cpc_main_group_share_asof": 1.0,
                "classification_breadth_band_asof": "focused",
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "docdb_family_id": 3,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["G06F"],
                "cpc_sections_asof": ["G"],
                "cpc_subclasses_asof": ["G06F"],
                "cpc_main_groups_asof": ["G06F3/00"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 1.0,
                "classification_concentration_hhi_asof": 1.0,
                "classification_entropy_asof": 0.0,
                "top_cpc_main_group_asof": "G06F3/00",
                "top_cpc_main_group_share_asof": 1.0,
                "classification_breadth_band_asof": "focused",
                "classification_visibility_policy": "stable_family_classification_replay",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
        ],
        settings.gold_dir / "gold_family_classification_mix_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 80.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.8,
                "family_enforceability_score_asof": 0.7,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 3.0,
                "pre_asof_forward_citations_weighted": 2.5,
                "family_rcf_score_asof": 0.5,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.4,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 0.9,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 85.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.9,
                "family_enforceability_score_asof": 0.75,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 4.0,
                "pre_asof_forward_citations_weighted": 3.2,
                "family_rcf_score_asof": 0.6,
                "pre_asof_unique_citing_family_count": 3.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.25,
                "data_completeness_pct_asof": 0.92,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 45.0,
                "family_composite_status_asof": "pending_emerging",
                "active_jurisdiction_count_asof": 0.0,
                "active_grant_branch_count_asof": 0.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 0.0,
                "family_coverage_stability_score_asof": 0.4,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.2,
                "family_enforceability_score_asof": 0.1,
                "family_field_contribution_primary_asof": 0.3,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.5,
                "family_rcf_score_asof": 0.1,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.2,
                "pre_asof_attacker_density_score": 0.05,
                "data_completeness_pct_asof": 0.75,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 3,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "BETA",
                "owner_name_display_current": "Beta",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 70.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.5,
                "family_enforceability_score_asof": 0.6,
                "family_field_contribution_primary_asof": 0.8,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 1.5,
                "family_rcf_score_asof": 0.3,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.3,
                "pre_asof_attacker_density_score": 0.1,
                "data_completeness_pct_asof": 0.88,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 3,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "BETA",
                "owner_name_display_current": "Beta",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 72.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.6,
                "family_enforceability_score_asof": 0.65,
                "family_field_contribution_primary_asof": 0.85,
                "pre_asof_forward_citations_clean": 2.5,
                "pre_asof_forward_citations_weighted": 1.8,
                "family_rcf_score_asof": 0.35,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.35,
                "pre_asof_attacker_density_score": 0.12,
                "data_completeness_pct_asof": 0.89,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
        ],
        settings.gold_dir / "gold_family_compare_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2021,
                "snapshot_date": date(2021, 12, 31),
                "source_auth": "US",
                "is_up_unrolled": False,
                "is_classic_validation": False,
                "is_global_member": False,
                "last_grant_event_date": date(2021, 1, 15),
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
                "last_negative_event_date": None,
                "last_opposition_event_date": None,
                "last_pending_event_date": date(2020, 1, 1),
                "replay_branch_state": "ACTIVE_GRANT",
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "pending_branch_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2022,
                "snapshot_date": date(2022, 12, 31),
                "source_auth": "US",
                "is_up_unrolled": False,
                "is_classic_validation": False,
                "is_global_member": False,
                "last_grant_event_date": date(2021, 1, 15),
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
                "last_negative_event_date": None,
                "last_opposition_event_date": None,
                "last_pending_event_date": date(2020, 1, 1),
                "replay_branch_state": "ACTIVE_GRANT",
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "pending_branch_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "EP",
                "snapshot_year": 2022,
                "snapshot_date": date(2022, 12, 31),
                "source_auth": "EP",
                "is_up_unrolled": False,
                "is_classic_validation": True,
                "is_global_member": False,
                "last_grant_event_date": None,
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
                "last_negative_event_date": None,
                "last_opposition_event_date": None,
                "last_pending_event_date": date(2022, 2, 1),
                "replay_branch_state": "PENDING_ONLY",
                "active_branch_flag": False,
                "lapsed_or_expired_flag": False,
                "pending_branch_flag": True,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 3,
                "jurisdiction_code": "EP",
                "snapshot_year": 2021,
                "snapshot_date": date(2021, 12, 31),
                "source_auth": "EP",
                "is_up_unrolled": False,
                "is_classic_validation": True,
                "is_global_member": False,
                "last_grant_event_date": date(2021, 4, 5),
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
                "last_negative_event_date": None,
                "last_opposition_event_date": None,
                "last_pending_event_date": date(2020, 2, 1),
                "replay_branch_state": "ACTIVE_GRANT",
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "pending_branch_flag": False,
                "opposed_branch_flag": False,
            },
            {
                "docdb_family_id": 3,
                "jurisdiction_code": "EP",
                "snapshot_year": 2022,
                "snapshot_date": date(2022, 12, 31),
                "source_auth": "EP",
                "is_up_unrolled": False,
                "is_classic_validation": True,
                "is_global_member": False,
                "last_grant_event_date": date(2021, 4, 5),
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
                "last_negative_event_date": None,
                "last_opposition_event_date": None,
                "last_pending_event_date": date(2020, 2, 1),
                "replay_branch_state": "ACTIVE_GRANT",
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "pending_branch_flag": False,
                "opposed_branch_flag": False,
            },
        ],
        settings.silver_dir / "silver_branch_status_history_dense.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "ALPHA", "owner_name_display": "Alpha"},
            {"docdb_family_id": 2, "owner_name_harmonized": "ALPHA", "owner_name_display": "Alpha"},
            {"docdb_family_id": 3, "owner_name_harmonized": "BETA", "owner_name_display": "Beta"},
            {"docdb_family_id": 3, "owner_name_harmonized": "UNKNOWN_OWNER", "owner_name_display": "Unknown Owner"},
        ],
        settings.silver_dir / "silver_family_owner_bridge.parquet",
    )
    write_text_json(
        settings.ml_dir / "family_jurisdiction_lapse_risk_release_decision.json",
        {
            "office_support_policy": {
                "strong": ["US"],
                "moderate": ["EP"],
                "limited": [],
            }
        },
    )

    family_result = build_gold_family_classification_jurisdiction_pit(settings).finish()
    portfolio_result = build_gold_portfolio_classification_jurisdiction_pit(settings).finish()
    market_result = build_gold_market_cpc_jurisdiction_trend_pit(settings).finish()

    assert family_result.status == "success", family_result.warnings
    assert portfolio_result.status == "success", portfolio_result.warnings
    assert market_result.status == "success", market_result.warnings

    con = duckdb.connect()
    family_rows = con.execute(
        """
        select
            docdb_family_id,
            as_of_year,
            wipo_field,
            cpc_main_group,
            jurisdiction_code,
            is_active_asof,
            round(family_blocking_power_score_asof, 6),
            round(pre_asof_forward_citations_clean, 6),
            classification_jurisdiction_support_level
        from read_parquet(?)
        order by docdb_family_id, as_of_year
        """,
        [str(settings.gold_dir / "gold_family_classification_jurisdiction_pit.parquet")],
    ).fetchall()
    assert family_rows == [
        (1, 2021, "Computer technology", "H04L45/00", "US", True, 0.8, 3.0, "strong"),
        (1, 2022, "Computer technology", "H04L45/00", "US", True, 0.9, 4.0, "strong"),
        (2, 2022, "Computer technology", "G06F3/00", "EP", False, 0.2, 1.0, "moderate"),
        (3, 2021, "Computer technology", "G06F3/00", "EP", True, 0.5, 2.0, "moderate"),
        (3, 2022, "Computer technology", "G06F3/00", "EP", True, 0.6, 2.5, "moderate"),
    ]

    portfolio_rows = con.execute(
        """
        select
            owner_name_harmonized,
            as_of_year,
            wipo_field,
            cpc_main_group,
            jurisdiction_code,
            portfolio_family_count_in_slice_asof,
            portfolio_active_family_count_in_slice_asof,
            round(portfolio_family_share_in_slice_asof, 6),
            round(portfolio_blocking_density_asof, 6),
            round(portfolio_citation_pressure_index_asof, 6),
            slice_rank_within_owner_year
        from read_parquet(?)
        where owner_name_harmonized = 'ALPHA'
          and as_of_year = 2022
        order by slice_rank_within_owner_year
        """,
        [str(settings.gold_dir / "gold_portfolio_classification_jurisdiction_pit.parquet")],
    ).fetchall()
    assert portfolio_rows == [
        ("ALPHA", 2022, "Computer technology", "H04L45/00", "US", 1.0, 1.0, 0.5, 0.9, 100.0, 1),
        ("ALPHA", 2022, "Computer technology", "G06F3/00", "EP", 1.0, 0.0, 0.5, 0.2, 25.0, 2),
    ]
    unknown_owner_rows = con.execute(
        """
        select count(*)
        from read_parquet(?)
        where owner_name_harmonized = 'UNKNOWN_OWNER'
        """,
        [str(settings.gold_dir / "gold_portfolio_classification_jurisdiction_pit.parquet")],
    ).fetchone()[0]
    assert unknown_owner_rows == 0

    market_rows = con.execute(
        """
        select
            as_of_year,
            wipo_field,
            cpc_main_group,
            jurisdiction_code,
            family_count_asof,
            active_family_count_asof,
            round(family_share_within_slice_asof, 6),
            round(citation_pressure_index_asof, 6),
            round(growth_index_asof, 6),
            slice_rank_within_year
        from read_parquet(?)
        where as_of_year = 2022
        order by slice_rank_within_year
        """,
        [str(settings.gold_dir / "gold_market_cpc_jurisdiction_trend_pit.parquet")],
    ).fetchall()
    assert market_rows == [
        (2022, "Computer technology", "G06F3/00", "EP", 2.0, 1.0, 1.0, 43.75, 1.0, 1),
        (2022, "Computer technology", "H04L45/00", "US", 1.0, 1.0, 1.0, 100.0, 0.0, 2),
    ]


def test_build_gold_market_summary_pit_materializes_year_safe_segment_rollups(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "family_priority_year": 2021,
                "wipo_industry_code": "Computer technology",
                "family_count": 2,
                "prior_family_count": 1,
                "market_state": "rising",
                "is_recent_priority_year_incomplete": False,
                "market_state_ui_safe": True,
                "latest_comparable_year": 2022,
                "snapshot_date": date(2026, 3, 15),
            },
            {
                "family_priority_year": 2022,
                "wipo_industry_code": "Computer technology",
                "family_count": 3,
                "prior_family_count": 2,
                "market_state": "rising",
                "is_recent_priority_year_incomplete": False,
                "market_state_ui_safe": True,
                "latest_comparable_year": 2022,
                "snapshot_date": date(2026, 3, 15),
            },
            {
                "family_priority_year": 2025,
                "wipo_industry_code": "Computer technology",
                "family_count": 1,
                "prior_family_count": 3,
                "market_state": "cooling",
                "is_recent_priority_year_incomplete": True,
                "market_state_ui_safe": False,
                "latest_comparable_year": 2022,
                "snapshot_date": date(2026, 3, 15),
            },
        ],
        settings.gold_dir / "gold_market_intelligence_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 80.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 2.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.6,
                "family_enforceability_score_asof": 0.8,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 1.5,
                "family_rcf_score_asof": 0.4,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.4,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 0.9,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "BETA",
                "owner_name_display_current": "Beta",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology", "Digital communication"],
                "oecd_quality_percentile_current": 50.0,
                "family_composite_status_asof": "pending_emerging",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 0.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 0.5,
                "family_coverage_stability_score_asof": 0.5,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 2.0,
                "family_blocking_power_score_asof": 0.2,
                "family_enforceability_score_asof": 0.4,
                "family_field_contribution_primary_asof": 0.5,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.5,
                "family_rcf_score_asof": 0.2,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.2,
                "pre_asof_attacker_density_score": 0.1,
                "data_completeness_pct_asof": 0.8,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 80.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 2.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.7,
                "family_enforceability_score_asof": 0.85,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 3.0,
                "pre_asof_forward_citations_weighted": 2.5,
                "family_rcf_score_asof": 0.5,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 0.92,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "BETA",
                "owner_name_display_current": "Beta",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology", "Digital communication"],
                "oecd_quality_percentile_current": 50.0,
                "family_composite_status_asof": "pending_emerging",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 0.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 0.5,
                "family_coverage_stability_score_asof": 0.5,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 2.0,
                "family_blocking_power_score_asof": 0.3,
                "family_enforceability_score_asof": 0.45,
                "family_field_contribution_primary_asof": 0.5,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.5,
                "family_rcf_score_asof": 0.2,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.2,
                "pre_asof_attacker_density_score": 0.1,
                "data_completeness_pct_asof": 0.82,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 3,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 60.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.9,
                "family_enforceability_score_asof": 0.9,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 4.0,
                "pre_asof_forward_citations_weighted": 3.0,
                "family_rcf_score_asof": 0.6,
                "pre_asof_unique_citing_family_count": 3.0,
                "pre_asof_citing_assignee_diversity": 0.6,
                "pre_asof_attacker_density_score": 0.25,
                "data_completeness_pct_asof": 0.95,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
        ],
        settings.gold_dir / "gold_family_compare_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "snapshot_year": 2021,
                "snapshot_date": date(2021, 12, 31),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 1.0,
                "enforceability_contribution_score": 0.8,
                "heritage_contribution_score": 0.4,
                "active_market_weight": 1.0,
                "max_active_stage": "STANDARD_GRANT",
                "is_active_on_snapshot": True,
            },
            {
                "docdb_family_id": 2,
                "snapshot_year": 2021,
                "snapshot_date": date(2021, 12, 31),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 0.5,
                "enforceability_contribution_score": 0.4,
                "heritage_contribution_score": 0.2,
                "active_market_weight": 0.5,
                "max_active_stage": "STANDARD_APPLICATION",
                "is_active_on_snapshot": True,
            },
            {
                "docdb_family_id": 1,
                "snapshot_year": 2022,
                "snapshot_date": date(2022, 12, 31),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 1.0,
                "enforceability_contribution_score": 0.85,
                "heritage_contribution_score": 0.5,
                "active_market_weight": 1.0,
                "max_active_stage": "STANDARD_GRANT",
                "is_active_on_snapshot": True,
            },
            {
                "docdb_family_id": 2,
                "snapshot_year": 2022,
                "snapshot_date": date(2022, 12, 31),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 0.5,
                "enforceability_contribution_score": 0.45,
                "heritage_contribution_score": 0.2,
                "active_market_weight": 0.5,
                "max_active_stage": "STANDARD_APPLICATION",
                "is_active_on_snapshot": True,
            },
            {
                "docdb_family_id": 3,
                "snapshot_year": 2022,
                "snapshot_date": date(2022, 12, 31),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 1.0,
                "enforceability_contribution_score": 0.9,
                "heritage_contribution_score": 0.6,
                "active_market_weight": 1.0,
                "max_active_stage": "STANDARD_GRANT",
                "is_active_on_snapshot": True,
            },
        ],
        settings.gold_dir / "gold_family_field_contributions_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 1, "owner_name_harmonized": "ALPHA", "owner_name_display": "Alpha"},
            {"docdb_family_id": 2, "owner_name_harmonized": "BETA", "owner_name_display": "Beta"},
            {"docdb_family_id": 3, "owner_name_harmonized": "ALPHA", "owner_name_display": "Alpha"},
        ],
        settings.silver_dir / "silver_family_owner_bridge.parquet",
    )

    result = build_gold_market_summary_pit(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select
            segment_key,
            as_of_year,
            segment_heat_state_asof,
            segment_market_state_ui_safe_asof,
            segment_priority_year_incomplete_asof,
            segment_latest_comparable_year,
            segment_family_count_stock_asof,
            segment_priority_year_family_count_asof,
            segment_prior_priority_year_family_count_asof,
            round(segment_growth_index_asof, 6),
            segment_owner_count_hist_proxy_asof,
            round(segment_blocking_density_asof, 6),
            round(segment_field_balance_asof, 6),
            segment_active_family_count_asof,
            round(segment_top_owner_share_hist_proxy, 6),
            current_owner_bridge_replayed_to_history,
            historical_owner_truth_supported
        from read_parquet(?)
        order by as_of_year
        """,
        [str(settings.gold_dir / "gold_market_summary_pit.parquet")],
    ).fetchall()
    assert rows == [
        ("Computer technology", 2021, "rising", True, False, 2022, 2.0, 2.0, 1.0, 1.0, 2, 0.466667, 0.75, 2, 0.5, True, False),
        ("Computer technology", 2022, "rising", True, False, 2022, 3.0, 3.0, 2.0, 0.5, 2, 0.7, 0.833333, 3, 0.666667, True, False),
        ("Computer technology", 2025, None, False, True, 2022, 0.0, 1.0, 3.0, -0.666667, 0, 0.0, 0.0, 0, 0.0, True, False),
    ]


def test_build_gold_market_leaderboard_pit_materializes_family_and_owner_rows(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "segment_key": "Computer technology",
                "wipo_industry_code": "Computer technology",
                "as_of_year": 2022,
                "current_snapshot_date": date(2026, 3, 15),
                "segment_heat_state_asof": "rising",
                "segment_market_state_ui_safe_asof": True,
                "segment_priority_year_incomplete_asof": False,
                "segment_latest_comparable_year": 2022,
                "segment_family_count_stock_asof": 3.0,
                "segment_priority_year_family_count_asof": 3.0,
                "segment_prior_priority_year_family_count_asof": 2.0,
                "segment_growth_index_asof": 0.5,
                "segment_owner_count_hist_proxy_asof": 2,
                "segment_blocking_density_asof": 0.7,
                "segment_field_balance_asof": 0.8,
                "segment_active_family_count_asof": 3,
                "segment_active_weight_asof": 2.5,
                "segment_active_jurisdiction_share_asof": 0.75,
                "segment_enforceability_density_asof": 0.6,
                "segment_top_owner_share_hist_proxy": 0.666667,
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_bridge_replayed_to_history": True,
                "historical_oecd_supported": False,
            }
        ],
        settings.gold_dir / "gold_market_summary_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 80.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 2.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.9,
                "family_enforceability_score_asof": 0.85,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 3.0,
                "pre_asof_forward_citations_weighted": 2.5,
                "family_rcf_score_asof": 0.5,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 0.92,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "BETA",
                "owner_name_display_current": "Beta",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 60.0,
                "family_composite_status_asof": "pending_emerging",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 0.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 0.5,
                "family_coverage_stability_score_asof": 0.5,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.4,
                "family_enforceability_score_asof": 0.5,
                "family_field_contribution_primary_asof": 0.6,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.7,
                "family_rcf_score_asof": 0.2,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.2,
                "pre_asof_attacker_density_score": 0.1,
                "data_completeness_pct_asof": 0.8,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 3,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 75.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.8,
                "family_enforceability_score_asof": 0.8,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 1.8,
                "family_rcf_score_asof": 0.4,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.4,
                "pre_asof_attacker_density_score": 0.15,
                "data_completeness_pct_asof": 0.9,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
        ],
        settings.gold_dir / "gold_family_compare_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "snapshot_year": 2022,
                "snapshot_date": date(2022, 12, 31),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 1.0,
                "enforceability_contribution_score": 0.8,
                "heritage_contribution_score": 0.4,
                "active_market_weight": 1.0,
                "max_active_stage": "STANDARD_GRANT",
                "is_active_on_snapshot": True,
            },
            {
                "docdb_family_id": 2,
                "snapshot_year": 2022,
                "snapshot_date": date(2022, 12, 31),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 0.5,
                "enforceability_contribution_score": 0.5,
                "heritage_contribution_score": 0.2,
                "active_market_weight": 0.5,
                "max_active_stage": "STANDARD_APPLICATION",
                "is_active_on_snapshot": True,
            },
            {
                "docdb_family_id": 3,
                "snapshot_year": 2022,
                "snapshot_date": date(2022, 12, 31),
                "wipo_industry_code": "Computer technology",
                "base_fraction": 1.0,
                "enforceability_contribution_score": 0.8,
                "heritage_contribution_score": 0.3,
                "active_market_weight": 1.0,
                "max_active_stage": "STANDARD_GRANT",
                "is_active_on_snapshot": True,
            },
        ],
        settings.gold_dir / "gold_family_field_contributions_timeseries.parquet",
    )

    result = build_gold_market_leaderboard_pit(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select
            leaderboard_entity_type,
            leaderboard_rank,
            docdb_family_id,
            owner_name_harmonized,
            in_segment_family_count_hist_proxy,
            round(in_segment_family_share_hist_proxy, 6),
            round(avg_blocking_score_asof, 6),
            round(total_blocking_score_asof, 6),
            family_composite_status_asof,
            current_owner_bridge_replayed_to_history
        from read_parquet(?)
        order by leaderboard_entity_type, leaderboard_rank
        """,
        [str(settings.gold_dir / "gold_market_leaderboard_pit.parquet")],
    ).fetchall()
    assert rows == [
        ("family", 1, 1, None, 1, None, 0.9, 0.9, "fully_active", False),
        ("family", 2, 3, None, 1, None, 0.8, 0.8, "fully_active", False),
        ("family", 3, 2, None, 1, None, 0.4, 0.4, "pending_emerging", False),
        ("owner", 1, None, "ALPHA", 2, 0.666667, 0.85, 1.7, None, True),
        ("owner", 2, None, "BETA", 1, 0.333333, 0.4, 0.4, None, True),
    ]


def test_build_gold_market_cpc_trend_pit_materializes_segment_cpc_year_rows(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "segment_key": "Computer technology",
                "wipo_industry_code": "Computer technology",
                "as_of_year": 2021,
                "current_snapshot_date": date(2026, 3, 15),
                "segment_heat_state_asof": "rising",
                "segment_market_state_ui_safe_asof": True,
                "segment_priority_year_incomplete_asof": False,
                "segment_latest_comparable_year": 2022,
                "segment_family_count_stock_asof": 2.0,
                "segment_priority_year_family_count_asof": 2.0,
                "segment_prior_priority_year_family_count_asof": 1.0,
                "segment_growth_index_asof": 1.0,
                "segment_owner_count_hist_proxy_asof": 2,
                "segment_blocking_density_asof": 0.5,
                "segment_field_balance_asof": 1.0,
                "segment_active_family_count_asof": 2,
                "segment_active_weight_asof": 2.0,
                "segment_active_jurisdiction_share_asof": 1.0,
                "segment_enforceability_density_asof": 0.65,
                "segment_top_owner_share_hist_proxy": 0.5,
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_bridge_replayed_to_history": True,
                "historical_oecd_supported": False,
            },
            {
                "segment_key": "Computer technology",
                "wipo_industry_code": "Computer technology",
                "as_of_year": 2022,
                "current_snapshot_date": date(2026, 3, 15),
                "segment_heat_state_asof": "rising",
                "segment_market_state_ui_safe_asof": True,
                "segment_priority_year_incomplete_asof": False,
                "segment_latest_comparable_year": 2022,
                "segment_family_count_stock_asof": 3.0,
                "segment_priority_year_family_count_asof": 3.0,
                "segment_prior_priority_year_family_count_asof": 2.0,
                "segment_growth_index_asof": 0.5,
                "segment_owner_count_hist_proxy_asof": 2,
                "segment_blocking_density_asof": 0.566667,
                "segment_field_balance_asof": 1.0,
                "segment_active_family_count_asof": 3,
                "segment_active_weight_asof": 3.0,
                "segment_active_jurisdiction_share_asof": 1.0,
                "segment_enforceability_density_asof": 0.7,
                "segment_top_owner_share_hist_proxy": 0.666667,
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_bridge_replayed_to_history": True,
                "historical_oecd_supported": False,
            },
        ],
        settings.gold_dir / "gold_market_summary_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["A01"],
                "cpc_sections_asof": ["A"],
                "cpc_subclasses_asof": ["A01B"],
                "cpc_main_groups_asof": ["A01", "B01"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 2.0,
                "classification_concentration_hhi_asof": 0.5,
                "classification_entropy_asof": 0.693147,
                "top_cpc_main_group_asof": "A01",
                "top_cpc_main_group_share_asof": 0.5,
                "classification_breadth_band_asof": "balanced",
                "classification_visibility_policy": "first_seen_classification_visibility",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["A01"],
                "cpc_sections_asof": ["A"],
                "cpc_subclasses_asof": ["A01B"],
                "cpc_main_groups_asof": ["A01"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 1.0,
                "classification_concentration_hhi_asof": 1.0,
                "classification_entropy_asof": 0.0,
                "top_cpc_main_group_asof": "A01",
                "top_cpc_main_group_share_asof": 1.0,
                "classification_breadth_band_asof": "focused",
                "classification_visibility_policy": "first_seen_classification_visibility",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["A01"],
                "cpc_sections_asof": ["A"],
                "cpc_subclasses_asof": ["A01B"],
                "cpc_main_groups_asof": ["A01", "B01"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 2.0,
                "classification_concentration_hhi_asof": 0.5,
                "classification_entropy_asof": 0.693147,
                "top_cpc_main_group_asof": "A01",
                "top_cpc_main_group_share_asof": 0.5,
                "classification_breadth_band_asof": "balanced",
                "classification_visibility_policy": "first_seen_classification_visibility",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["A01"],
                "cpc_sections_asof": ["A"],
                "cpc_subclasses_asof": ["A01B"],
                "cpc_main_groups_asof": ["A01"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 1.0,
                "classification_concentration_hhi_asof": 1.0,
                "classification_entropy_asof": 0.0,
                "top_cpc_main_group_asof": "A01",
                "top_cpc_main_group_share_asof": 1.0,
                "classification_breadth_band_asof": "focused",
                "classification_visibility_policy": "first_seen_classification_visibility",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "docdb_family_id": 3,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_partial_snapshot_year": False,
                "covered_wipo_fields_asof": ["Computer technology"],
                "primary_wipo_field_asof": "Computer technology",
                "wipo_field_count_asof": 1.0,
                "ipc_subclasses_asof": ["B01"],
                "cpc_sections_asof": ["B"],
                "cpc_subclasses_asof": ["B01C"],
                "cpc_main_groups_asof": ["B01"],
                "ipc_subclass_count_asof": 1.0,
                "cpc_section_count_asof": 1.0,
                "cpc_subclass_count_asof": 1.0,
                "cpc_main_group_count_asof": 1.0,
                "classification_concentration_hhi_asof": 1.0,
                "classification_entropy_asof": 0.0,
                "top_cpc_main_group_asof": "B01",
                "top_cpc_main_group_share_asof": 1.0,
                "classification_breadth_band_asof": "focused",
                "classification_visibility_policy": "first_seen_classification_visibility",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
        ],
        settings.gold_dir / "gold_family_classification_mix_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 80.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 2.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.8,
                "family_enforceability_score_asof": 0.9,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 3.0,
                "pre_asof_forward_citations_weighted": 2.0,
                "family_rcf_score_asof": 0.7,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.3,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 0.9,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2021, 12, 31),
                "as_of_year": 2021,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "BETA",
                "owner_name_display_current": "Beta",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 70.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.2,
                "family_enforceability_score_asof": 0.4,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.8,
                "family_rcf_score_asof": 0.2,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.2,
                "pre_asof_attacker_density_score": 0.1,
                "data_completeness_pct_asof": 0.9,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 80.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 2.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 2.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.8,
                "family_enforceability_score_asof": 0.9,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 4.0,
                "pre_asof_forward_citations_weighted": 3.0,
                "family_rcf_score_asof": 0.8,
                "pre_asof_unique_citing_family_count": 3.0,
                "pre_asof_citing_assignee_diversity": 0.4,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 0.92,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "BETA",
                "owner_name_display_current": "Beta",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 70.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.2,
                "family_enforceability_score_asof": 0.4,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.8,
                "family_rcf_score_asof": 0.2,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.2,
                "pre_asof_attacker_density_score": 0.1,
                "data_completeness_pct_asof": 0.9,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
            {
                "docdb_family_id": 3,
                "as_of_date": date(2022, 12, 31),
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "is_latest_observed_year": False,
                "current_snapshot_date": date(2026, 3, 15),
                "owner_name_harmonized_current": "ALPHA",
                "owner_name_display_current": "Alpha",
                "primary_wipo_field_current": "Computer technology",
                "covered_wipo_fields_current": ["Computer technology"],
                "oecd_quality_percentile_current": 75.0,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_coverage_stability_score_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_blocking_power_score_asof": 0.7,
                "family_enforceability_score_asof": 0.8,
                "family_field_contribution_primary_asof": 1.0,
                "pre_asof_forward_citations_clean": 2.0,
                "pre_asof_forward_citations_weighted": 1.5,
                "family_rcf_score_asof": 0.6,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.3,
                "pre_asof_attacker_density_score": 0.15,
                "data_completeness_pct_asof": 0.9,
                "historical_compare_safe": True,
                "historical_oecd_supported": False,
                "historical_owner_truth_supported": False,
                "current_owner_metadata_only": True,
            },
        ],
        settings.gold_dir / "gold_family_compare_pit.parquet",
    )

    result = build_gold_market_cpc_trend_pit(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select
            as_of_year,
            cpc_main_group,
            cpc_family_count_asof,
            round(cpc_family_share_within_segment_asof, 6),
            cpc_prior_family_count_asof,
            round(cpc_growth_index_asof, 6),
            cpc_heat_state_asof,
            cpc_rank_within_segment_year,
            segment_heat_state_asof,
            classification_visibility_policy
        from read_parquet(?)
        order by as_of_year, cpc_main_group
        """,
        [str(settings.gold_dir / "gold_market_cpc_trend_pit.parquet")],
    ).fetchall()
    assert rows == [
        (2021, "A01", 2.0, 1.0, None, None, "stable", 1, "rising", "first_seen_classification_visibility"),
        (2021, "B01", 1.0, 0.5, None, None, "stable", 2, "rising", "first_seen_classification_visibility"),
        (2022, "A01", 2.0, 0.666667, 2.0, 0.0, "stable", 2, "rising", "first_seen_classification_visibility"),
        (2022, "B01", 2.0, 0.666667, 1.0, 1.0, "heating", 1, "rising", "first_seen_classification_visibility"),
    ]


def test_build_gold_cpc_importance_pit_ranks_cpcs_within_year(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "segment_key": "Computer technology",
                "wipo_industry_code": "Computer technology",
                "as_of_year": 2021,
                "current_snapshot_date": date(2026, 3, 15),
                "cpc_main_group": "A01",
                "cpc_main_group_label": "A01",
                "cpc_family_count_asof": 2.0,
                "cpc_active_family_count_asof": 2.0,
                "segment_family_count_classification_basis_asof": 2.0,
                "segment_active_family_count_classification_basis_asof": 2.0,
                "cpc_family_share_within_segment_asof": 1.0,
                "cpc_active_family_share_within_segment_asof": 1.0,
                "cpc_blocking_density_asof": 0.5,
                "cpc_enforceability_density_asof": 0.65,
                "cpc_pre_asof_forward_citations_clean_avg_asof": 2.0,
                "cpc_avg_rcf_score_asof": 0.45,
                "segment_heat_state_asof": "rising",
                "cpc_prior_family_count_asof": None,
                "cpc_growth_index_asof": None,
                "cpc_heat_state_asof": "stable",
                "cpc_rank_within_segment_year": 1,
                "classification_visibility_policy": "first_seen_classification_visibility",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "segment_key": "Computer technology",
                "wipo_industry_code": "Computer technology",
                "as_of_year": 2021,
                "current_snapshot_date": date(2026, 3, 15),
                "cpc_main_group": "B01",
                "cpc_main_group_label": "B01",
                "cpc_family_count_asof": 1.0,
                "cpc_active_family_count_asof": 1.0,
                "segment_family_count_classification_basis_asof": 2.0,
                "segment_active_family_count_classification_basis_asof": 2.0,
                "cpc_family_share_within_segment_asof": 0.5,
                "cpc_active_family_share_within_segment_asof": 0.5,
                "cpc_blocking_density_asof": 0.8,
                "cpc_enforceability_density_asof": 0.9,
                "cpc_pre_asof_forward_citations_clean_avg_asof": 3.0,
                "cpc_avg_rcf_score_asof": 0.7,
                "segment_heat_state_asof": "rising",
                "cpc_prior_family_count_asof": None,
                "cpc_growth_index_asof": None,
                "cpc_heat_state_asof": "stable",
                "cpc_rank_within_segment_year": 2,
                "classification_visibility_policy": "first_seen_classification_visibility",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "segment_key": "Computer technology",
                "wipo_industry_code": "Computer technology",
                "as_of_year": 2022,
                "current_snapshot_date": date(2026, 3, 15),
                "cpc_main_group": "A01",
                "cpc_main_group_label": "A01",
                "cpc_family_count_asof": 2.0,
                "cpc_active_family_count_asof": 2.0,
                "segment_family_count_classification_basis_asof": 3.0,
                "segment_active_family_count_classification_basis_asof": 3.0,
                "cpc_family_share_within_segment_asof": 0.666667,
                "cpc_active_family_share_within_segment_asof": 0.666667,
                "cpc_blocking_density_asof": 0.5,
                "cpc_enforceability_density_asof": 0.65,
                "cpc_pre_asof_forward_citations_clean_avg_asof": 2.5,
                "cpc_avg_rcf_score_asof": 0.5,
                "segment_heat_state_asof": "rising",
                "cpc_prior_family_count_asof": 2.0,
                "cpc_growth_index_asof": 0.0,
                "cpc_heat_state_asof": "stable",
                "cpc_rank_within_segment_year": 2,
                "classification_visibility_policy": "first_seen_classification_visibility",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
            {
                "segment_key": "Computer technology",
                "wipo_industry_code": "Computer technology",
                "as_of_year": 2022,
                "current_snapshot_date": date(2026, 3, 15),
                "cpc_main_group": "B01",
                "cpc_main_group_label": "B01",
                "cpc_family_count_asof": 2.0,
                "cpc_active_family_count_asof": 2.0,
                "segment_family_count_classification_basis_asof": 3.0,
                "segment_active_family_count_classification_basis_asof": 3.0,
                "cpc_family_share_within_segment_asof": 0.666667,
                "cpc_active_family_share_within_segment_asof": 0.666667,
                "cpc_blocking_density_asof": 0.75,
                "cpc_enforceability_density_asof": 0.85,
                "cpc_pre_asof_forward_citations_clean_avg_asof": 3.0,
                "cpc_avg_rcf_score_asof": 0.65,
                "segment_heat_state_asof": "rising",
                "cpc_prior_family_count_asof": 1.0,
                "cpc_growth_index_asof": 1.0,
                "cpc_heat_state_asof": "heating",
                "cpc_rank_within_segment_year": 1,
                "classification_visibility_policy": "first_seen_classification_visibility",
                "classification_membership_replayed_to_history": True,
                "historical_classification_truth_supported": False,
                "historical_compare_safe": True,
            },
        ],
        settings.gold_dir / "gold_market_cpc_trend_pit.parquet",
    )

    result = build_gold_cpc_importance_pit(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select
            as_of_year,
            cpc_main_group,
            round(cpc_family_share_global_asof, 6),
            round(cpc_growth_index_asof, 6),
            cpc_importance_band_asof,
            cpc_importance_rank_within_year
        from read_parquet(?)
        order by as_of_year, cpc_importance_rank_within_year
        """,
        [str(settings.gold_dir / "gold_cpc_importance_pit.parquet")],
    ).fetchall()
    assert rows == [
        (2021, "A01", 1.0, None, "strategic", 1),
        (2021, "B01", 0.5, None, "core", 2),
        (2022, "B01", 0.666667, 1.0, "strategic", 1),
        (2022, "A01", 0.666667, 0.0, "strategic", 2),
    ]


def test_build_gold_portfolio_compare_pit_caveats_field_mix_to_supported_years(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "ALPHA",
                "owner_name_display_current": "Alpha",
                "as_of_year": 2025,
                "current_snapshot_date": date(2026, 3, 15),
                "portfolio_family_count_hist_proxy": 4,
                "portfolio_active_family_count_asof": 2,
                "portfolio_active_jurisdiction_count_asof": 5.0,
                "portfolio_lapsed_jurisdiction_count_asof": 1.0,
                "portfolio_avg_blocking_power_score_asof": 10.0,
                "portfolio_total_blocking_power_score_asof": 40.0,
                "portfolio_avg_enforceability_score_asof": 0.5,
                "portfolio_total_rcf_score_asof": 1.5,
                "portfolio_data_completeness_pct_asof": 0.8,
                "portfolio_top_family_blocking_share_asof": 0.4,
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_bridge_replayed_to_history": True,
                "historical_field_mix_supported": False,
            },
            {
                "owner_name_harmonized": "ALPHA",
                "owner_name_display_current": "Alpha",
                "as_of_year": 2026,
                "current_snapshot_date": date(2026, 3, 15),
                "portfolio_family_count_hist_proxy": 5,
                "portfolio_active_family_count_asof": 3,
                "portfolio_active_jurisdiction_count_asof": 7.0,
                "portfolio_lapsed_jurisdiction_count_asof": 1.0,
                "portfolio_avg_blocking_power_score_asof": 12.0,
                "portfolio_total_blocking_power_score_asof": 60.0,
                "portfolio_avg_enforceability_score_asof": 0.6,
                "portfolio_total_rcf_score_asof": 2.0,
                "portfolio_data_completeness_pct_asof": 0.9,
                "portfolio_top_family_blocking_share_asof": 0.5,
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_bridge_replayed_to_history": True,
                "historical_field_mix_supported": False,
            },
        ],
        settings.gold_dir / "gold_portfolio_summary_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "ALPHA",
                "snapshot_date": date(2026, 3, 15),
                "wipo_field": "Computer technology",
                "active_family_count": 2,
                "enforceability_score": 0.4,
                "heritage_score": 1.0,
            },
            {
                "owner_name_harmonized": "ALPHA",
                "snapshot_date": date(2026, 3, 15),
                "wipo_field": "Digital communication",
                "active_family_count": 1,
                "enforceability_score": 0.2,
                "heritage_score": 0.5,
            },
            {
                "owner_name_harmonized": "ALPHA",
                "snapshot_date": date(2026, 3, 15),
                "wipo_field": "Semiconductors",
                "active_family_count": 0,
                "enforceability_score": 0.0,
                "heritage_score": 0.0,
            },
        ],
        settings.gold_dir / "gold_portfolio_field_timeseries.parquet",
    )

    result = build_gold_portfolio_compare_pit(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    rows = con.execute(
        """
        select
            owner_name_harmonized,
            as_of_year,
            round(portfolio_legal_durability_index_asof, 6),
            portfolio_field_breadth_asof,
            round(portfolio_field_concentration_hhi_asof, 6),
            round(portfolio_top_field_share_asof, 6),
            historical_field_mix_supported,
            current_owner_bridge_replayed_to_history
        from read_parquet(?)
        order by as_of_year
        """,
        [str(settings.gold_dir / "gold_portfolio_compare_pit.parquet")],
    ).fetchall()
    assert rows == [
        ("ALPHA", 2025, 0.5, None, None, None, False, True),
        ("ALPHA", 2026, 0.6, 2.0, 0.555556, 0.666667, True, True),
    ]


def test_run_gold_exposes_sectioned_stage_functions() -> None:
    assert callable(gold_run.run_gold)
    assert callable(gold_run.run_gold_family_summary)
    assert callable(gold_run.run_gold_family_metrics)
    assert callable(gold_run.run_gold_family_citation_chronology)
    assert callable(gold_run.run_gold_family_core)
    assert callable(gold_run.run_gold_family_compare_pit)
    assert callable(gold_run.run_gold_family_classification_mix_pit)
    assert callable(gold_run.run_gold_family_classification_jurisdiction_pit)
    assert callable(gold_run.run_gold_portfolio_summary_pit)
    assert callable(gold_run.run_gold_portfolio_classification_mix_pit)
    assert callable(gold_run.run_gold_portfolio_classification_jurisdiction_pit)
    assert callable(gold_run.run_gold_market_summary_pit)
    assert callable(gold_run.run_gold_market_cpc_trend_pit)
    assert callable(gold_run.run_gold_market_cpc_jurisdiction_trend_pit)
    assert callable(gold_run.run_gold_cpc_importance_pit)
    assert callable(gold_run.run_gold_market_leaderboard_pit)
    assert callable(gold_run.run_gold_portfolio_compare_pit)
    assert callable(gold_run.run_gold_history)
    assert callable(gold_run.run_gold_history_fields)
    assert callable(gold_run.run_gold_history_blocking)
    assert callable(gold_run.run_gold_portfolio)
    assert callable(gold_run.run_gold_market_semantic)


def test_build_portfolio_forecast_from_models_writes_coverage_fields(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.ml_dir)

    owner_bridge = settings.silver_dir / "silver_family_owner_bridge.parquet"
    out_portfolio = settings.gold_dir / "gold_portfolio_summary.parquet"
    out_portfolio_field_ts = settings.gold_dir / "gold_portfolio_field_timeseries.parquet"
    out_portfolio_compare_pit = settings.gold_dir / "gold_portfolio_compare_pit.parquet"
    out_summary = settings.gold_dir / "gold_portfolio_forecast_summary.parquet"
    out_segments = settings.gold_dir / "gold_portfolio_forecast_segments.parquet"
    out_contributors = settings.gold_dir / "gold_portfolio_forecast_contributors.parquet"

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "owner_country": "US",
                "owner_scope_appln_count": 2,
                "owner_display_variant_count": 1,
                "owner_country_variant_count": 1,
                "family_distinct_owner_count": 1,
                "owner_family_rank": 1,
                "is_primary_owner": True,
                "owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
            {
                "docdb_family_id": 2,
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "owner_country": "US",
                "owner_scope_appln_count": 2,
                "owner_display_variant_count": 1,
                "owner_country_variant_count": 1,
                "family_distinct_owner_count": 1,
                "owner_family_rank": 1,
                "is_primary_owner": True,
                "owner_selection_method": "scope_appln_count_desc_then_owner_name",
            },
        ],
        owner_bridge,
    )
    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "ALPHA",
                "owner_name_display": "Alpha",
                "snapshot_date": date(2026, 3, 15),
                "portfolio_family_count_within_mega_cluster": 2,
                "portfolio_avg_blocking_power_within_mega_cluster": 10.0,
                "portfolio_active_grant_family_count": 2,
                "semantic_candidate_family_count": 2,
                "portfolio_total_mass_score": 5.0,
                "portfolio_hit_rate_top_decile": 0.5,
                "portfolio_crown_jewel_index": 1.5,
                "portfolio_opposition_rate": 0.0,
                "portfolio_current_threat_score": 0.2,
                "portfolio_heritage_score": 0.3,
            }
        ],
        out_portfolio,
    )
    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "ALPHA",
                "snapshot_date": date(2026, 3, 15),
                "wipo_field": "Computer technology",
                "active_family_count": 2,
                "enforceability_score": 1.0,
                "heritage_score": 0.1,
            }
        ],
        out_portfolio_field_ts,
    )
    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "ALPHA",
                "owner_name_display_current": "Alpha",
                "as_of_year": 2026,
                "current_snapshot_date": date(2026, 3, 15),
                "portfolio_family_count_hist_proxy": 2,
                "portfolio_active_family_count_asof": 2,
                "portfolio_active_jurisdiction_count_asof": 2.0,
                "portfolio_lapsed_jurisdiction_count_asof": 0.0,
                "portfolio_avg_blocking_power_score_asof": 5.0,
                "portfolio_total_blocking_power_score_asof": 10.0,
                "portfolio_avg_enforceability_score_asof": 0.5,
                "portfolio_total_rcf_score_asof": 2.0,
                "portfolio_data_completeness_pct_asof": 1.0,
                "portfolio_top_family_blocking_share_asof": 0.5,
                "portfolio_legal_durability_index_asof": 1.0,
                "portfolio_field_breadth_asof": 1.0,
                "portfolio_field_concentration_hhi_asof": 1.0,
                "portfolio_top_field_share_asof": 1.0,
                "historical_compare_safe": True,
                "historical_owner_truth_supported": False,
                "current_owner_bridge_replayed_to_history": True,
                "historical_field_mix_supported": True,
            }
        ],
        out_portfolio_compare_pit,
    )

    phase03_features = pd.DataFrame(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": date(2022, 1, 1),
                "as_of_year": 2022,
                "primary_wipo_field": "Computer technology",
                "family_composite_status": "fully_active",
                "family_priority_year": 2020,
                "family_forward_citations_clean": 3.0,
                "family_forward_citations_weighted_7y": 3.0,
                "family_rcf_score": 1.0,
                "family_size_docdb": 2.0,
                "active_jurisdiction_count": 1.0,
                "family_distinct_owner_count": 1.0,
                "branch_enforceability_contribution_raw": 1.5,
                "family_overall_legal_enforceability_score": 0.7,
                "active_grant_branch_count": 1.0,
                "quality_index_4_percentile": 0.5,
                "quality_index_6_percentile": 0.6,
                "generality_percentile": 0.3,
                "radicalness_percentile": 0.4,
                "science_grounding_percentile": 0.2,
                "family_age_years": 2.0,
                "family_coverage_stability_score": 0.8,
                "unique_citing_family_count": 2.0,
                "citing_assignee_diversity": 0.5,
                "attacker_density_score": 0.2,
                "data_completeness_pct": 1.0,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": date(2023, 1, 1),
                "as_of_year": 2023,
                "primary_wipo_field": "Computer technology",
                "family_composite_status": "pending_emerging",
                "family_priority_year": 2021,
                "family_forward_citations_clean": 1.0,
                "family_forward_citations_weighted_7y": 1.2,
                "family_rcf_score": 0.5,
                "family_size_docdb": 1.0,
                "active_jurisdiction_count": 1.0,
                "family_distinct_owner_count": 1.0,
                "branch_enforceability_contribution_raw": 0.8,
                "family_overall_legal_enforceability_score": 0.4,
                "active_grant_branch_count": 1.0,
                "quality_index_4_percentile": 0.3,
                "quality_index_6_percentile": 0.2,
                "generality_percentile": 0.2,
                "radicalness_percentile": 0.1,
                "science_grounding_percentile": 0.1,
                "family_age_years": 2.0,
                "family_coverage_stability_score": 0.6,
                "unique_citing_family_count": 1.0,
                "citing_assignee_diversity": 0.2,
                "attacker_density_score": 0.1,
                "data_completeness_pct": 1.0,
            },
        ]
    )
    phase03_feature_path = settings.ml_dir / "ml_feature_family_future_citations.parquet"
    phase03_features.to_parquet(phase03_feature_path, index=False)
    status_mapping = {"fully_active": 0, "pending_emerging": 1}
    x_phase03, _ = _prepare_phase03_matrix(phase03_features, status_mapping)
    y3 = np.log1p(np.array([4.0, 1.0]))
    y5 = np.log1p(np.array([5.0, 2.0]))
    reg3 = LGBMRegressor(objective="regression", n_estimators=10, learning_rate=0.1, num_leaves=7, n_jobs=1, verbosity=-1, random_state=42)
    reg5 = LGBMRegressor(objective="regression", n_estimators=10, learning_rate=0.1, num_leaves=7, n_jobs=1, verbosity=-1, random_state=42)
    reg3.fit(x_phase03, y3)
    reg5.fit(x_phase03, y5)
    reg3.booster_.save_model(str(settings.ml_dir / "family_future_citation_forecast_3y_model.txt"))
    reg5.booster_.save_model(str(settings.ml_dir / "family_future_citation_forecast_5y_model.txt"))
    write_text_json(
        settings.ml_dir / "family_future_citation_forecast_3y_bundle.json",
        {
            "baseline_model_path": str(settings.ml_dir / "family_future_citation_forecast_3y_model.txt"),
            "breakout_classifier_model_path": None,
            "breakout_tail_model_path": None,
            "breakout_threshold_raw": 4.0,
            "calibration_version": "test-phase03-calibration-3y",
            "combination_rule": "baseline_plus_breakout_uplift",
            "horizon": "3y",
            "model_scope": "family_future_citation_forecast",
            "prediction_style": "directional_interval_first",
            "selected_variant": "baseline",
        },
    )
    write_text_json(
        settings.ml_dir / "family_future_citation_forecast_5y_bundle.json",
        {
            "baseline_model_path": str(settings.ml_dir / "family_future_citation_forecast_5y_model.txt"),
            "breakout_classifier_model_path": None,
            "breakout_tail_model_path": None,
            "breakout_threshold_raw": 5.0,
            "calibration_version": "test-phase03-calibration-5y",
            "combination_rule": "baseline_plus_breakout_uplift",
            "horizon": "5y",
            "model_scope": "family_future_citation_forecast",
            "prediction_style": "directional_interval_first",
            "selected_variant": "baseline",
        },
    )
    write_text_json(
        settings.ml_dir / "family_future_citation_forecast_calibration.json",
        {
            "horizons": {
                "3y": {"qhat_abs_log": 0.1, "qhat_abs_log_by_group": {}, "calibration_group_col": None},
                "5y": {"qhat_abs_log": 0.1, "qhat_abs_log_by_group": {}, "calibration_group_col": None},
            }
        },
    )
    write_text_json(settings.ml_dir / "model_card_family_future_citation_forecast.json", {"status_mapping": status_mapping})

    phase04_features = pd.DataFrame(
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "as_of_date": date(2026, 3, 15),
                "as_of_year": 2026,
                "family_priority_year": 2020,
                "family_age_years": 6.0,
                "training_snapshot_id": "test",
                "method_version": settings.method_version,
                "branch_state_asof": "ACTIVE_GRANT",
                "has_active_grant_asof": True,
                "years_since_last_grant_event": 1.0,
                "years_since_last_lapse_event": 10.0,
                "years_since_last_expiry_event": 10.0,
                "branch_stage_multiplier_asof": 1.0,
                "branch_enforceability_contribution_raw_asof": 1.2,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 0.8,
                "family_overall_legal_enforceability_score_asof": 0.7,
                "family_blocking_power_score_asof": 0.6,
                "family_field_contribution_primary_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_size_docdb_asof": 2.0,
                "family_rcf_score_asof": 1.0,
                "pre_asof_forward_citations_clean": 3.0,
                "pre_asof_forward_citations_weighted": 3.0,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.5,
                "pre_asof_attacker_density_score": 0.2,
                "jurisdiction_is_ep": False,
                "jurisdiction_is_us": True,
                "jurisdiction_is_cn": False,
                "jurisdiction_is_jp": False,
                "jurisdiction_is_kr": False,
                "jurisdiction_is_major_office": True,
                "primary_wipo_field": "Computer technology",
                "data_completeness_pct_asof": 1.0,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "US",
                "as_of_date": date(2026, 3, 15),
                "as_of_year": 2026,
                "family_priority_year": 2021,
                "family_age_years": 5.0,
                "training_snapshot_id": "test",
                "method_version": settings.method_version,
                "branch_state_asof": "ACTIVE_GRANT",
                "has_active_grant_asof": True,
                "years_since_last_grant_event": 2.0,
                "years_since_last_lapse_event": 10.0,
                "years_since_last_expiry_event": 10.0,
                "branch_stage_multiplier_asof": 1.0,
                "branch_enforceability_contribution_raw_asof": 0.8,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 0.7,
                "family_overall_legal_enforceability_score_asof": 0.5,
                "family_blocking_power_score_asof": 0.4,
                "family_field_contribution_primary_asof": 1.0,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_size_docdb_asof": 1.0,
                "family_rcf_score_asof": 0.5,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 1.2,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.2,
                "pre_asof_attacker_density_score": 0.1,
                "jurisdiction_is_ep": False,
                "jurisdiction_is_us": True,
                "jurisdiction_is_cn": False,
                "jurisdiction_is_jp": False,
                "jurisdiction_is_kr": False,
                "jurisdiction_is_major_office": True,
                "primary_wipo_field": "Computer technology",
                "data_completeness_pct_asof": 1.0,
            },
        ]
    )
    phase04_features.to_parquet(settings.ml_dir / "ml_feature_family_jurisdiction_lapse_risk.parquet", index=False)
    x_phase04, _, _ = _prepare_phase04_matrix(phase04_features)
    y12 = np.array([1, 0], dtype=int)
    y24 = np.array([1, 0], dtype=int)
    clf12 = LGBMClassifier(objective="binary", n_estimators=10, learning_rate=0.1, num_leaves=7, n_jobs=1, verbosity=-1, random_state=42)
    clf24 = LGBMClassifier(objective="binary", n_estimators=10, learning_rate=0.1, num_leaves=7, n_jobs=1, verbosity=-1, random_state=42)
    clf12.fit(x_phase04, y12)
    clf24.fit(x_phase04, y24)
    clf12.booster_.save_model(str(settings.ml_dir / "family_jurisdiction_lapse_risk_12m_model.txt"))
    clf24.booster_.save_model(str(settings.ml_dir / "family_jurisdiction_lapse_risk_24m_model.txt"))
    write_text_json(
        settings.ml_dir / "family_jurisdiction_lapse_risk_calibration.json",
        {"horizons": {"12m": {"method": "identity", "params": {}}, "24m": {"method": "identity", "params": {}}}},
    )
    write_text_json(
        settings.ml_dir / "family_jurisdiction_lapse_risk_release_decision.json",
        {"office_support_policy": {"strong": [], "moderate": ["US"], "limited": []}},
    )

    write_pylist_parquet(
        [
            {
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "as_of_year": 2025,
                "local_family_filings_asof": 10.0,
                "split_name": "test",
                "train_rows_support": 20,
                "minority_class_share": 0.2,
                "model_scope": "jurisdiction_field_trend_forecast",
                "horizon": "3y",
                "predicted_direction_band": "heating",
                "predicted_direction_probability": 0.8,
                "predicted_margin": 0.6,
                "trend_strength_band": "moderate",
                "support_level": "limited",
                "prob_cooling": 0.1,
                "prob_stable": 0.1,
                "prob_heating": 0.8,
                "predicted_growth_rate_reference": 0.2,
                "predicted_count_reference": 12.0,
                "actual_local_family_filings": 11.0,
                "actual_direction_band": "heating",
                "is_observed": True,
            },
            {
                "jurisdiction_code": "US",
                "wipo_industry_code": "Computer technology",
                "as_of_year": 2025,
                "local_family_filings_asof": 10.0,
                "split_name": "test",
                "train_rows_support": 20,
                "minority_class_share": 0.2,
                "model_scope": "jurisdiction_field_trend_forecast",
                "horizon": "5y",
                "predicted_direction_band": "cooling",
                "predicted_direction_probability": 0.8,
                "predicted_margin": 0.6,
                "trend_strength_band": "moderate",
                "support_level": "limited",
                "prob_cooling": 0.8,
                "prob_stable": 0.1,
                "prob_heating": 0.1,
                "predicted_growth_rate_reference": -0.2,
                "predicted_count_reference": 8.0,
                "actual_local_family_filings": 7.0,
                "actual_direction_band": "cooling",
                "is_observed": True,
            },
        ],
        settings.ml_dir / "ml_prediction_jurisdiction_field_trend_forecast.parquet",
    )

    stage_result = StageResult(stage="gold-portfolio-forecast", status="success", summary="test")
    outputs = _build_portfolio_forecast_from_models(
        settings,
        out_portfolio=out_portfolio,
        out_portfolio_field_ts=out_portfolio_field_ts,
        out_portfolio_compare_pit=out_portfolio_compare_pit,
        out_portfolio_forecast=out_summary,
        out_portfolio_forecast_segments=out_segments,
        out_portfolio_forecast_contributors=out_contributors,
        result=stage_result,
    )

    assert str(settings.ml_dir / "ml_portfolio_prediction_rollup.parquet") in [str(path) for path in outputs]
    assert out_summary.exists()
    assert out_segments.exists()
    assert out_contributors.exists()

    con = duckdb.connect()
    summary = con.execute(
        """
        select
            phase03_family_coverage_pct,
            phase04_family_coverage_pct,
            phase06_current_field_mix_supported,
            portfolio_prediction_coverage_status,
            portfolio_expected_future_citations_total_3y is not null as has_phase03_3y,
            portfolio_expected_lapses_count_12m is not null as has_phase04_12m
        from read_parquet(?)
        """,
        [str(out_summary)],
    ).fetchone()
    assert summary == (1.0, 1.0, True, "high", True, True)

    segment_row = con.execute(
        """
        select predicted_direction_band, support_level
        from read_parquet(?)
        where horizon = '3y'
        """,
        [str(out_segments)],
    ).fetchone()
    assert segment_row == ("heating", "limited")

    contributor_count = con.execute(
        "select count(*) from read_parquet(?)",
        [str(out_contributors)],
    ).fetchone()[0]
    assert contributor_count > 0


def test_family_citation_chronology_uses_publication_anchor_for_7y_window(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    silver_dir = ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "inpadoc_family_id": 11,
                "family_earliest_priority_date": date(2018, 1, 1),
                "family_priority_year": 2018,
                "is_main_window_family": True,
                "is_heritage_backfill_family": False,
                "is_out_of_bounds_ghost": False,
                "family_size_docdb": 1,
                "scope_type": settings.scope_type,
                "method_version": settings.method_version,
                "snapshot_date": settings.snapshot_date,
            }
        ],
        silver_dir / "silver_family_core.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "appln_id": 1001,
                "pat_publn_id": 2001,
                "jurisdiction_code": "US",
                "publn_kind": "A1",
                "publn_date": date(2019, 6, 1),
                "is_application_stage": True,
                "is_grant_stage": False,
                "publication_number_full": "US-TEST-1",
            }
        ],
        silver_dir / "silver_family_member_publications.parquet",
    )
    write_pylist_parquet(
        [
            {
                "source_docdb_family_id": 10,
                "cited_docdb_family_id": 1,
                "citation_date": date(2025, 6, 1),
                "citing_assignee_name": "OMEGA",
                "is_out_of_bounds": False,
                "is_intra_family_citation": False,
                "is_self_citation": False,
                "clean_edge_weight": 1.0,
            }
        ],
        silver_dir / "silver_enriched_citation_network.parquet",
    )

    chronology_result = build_gold_family_citation_chronology(settings).finish()
    assert chronology_result.status == "success"

    con = duckdb.connect()
    chronology_row = con.execute(
        """
        select
            pre_asof_forward_clean_7y,
            window_7y_closed
        from read_parquet(?)
        where docdb_family_id = 1
          and as_of_year = 2026
        """,
        [str(settings.gold_dir / "gold_family_citation_chronology.parquet")],
    ).fetchone()
    assert chronology_row == (1.0, False)

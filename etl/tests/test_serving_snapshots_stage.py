from __future__ import annotations

import json
from pathlib import Path

import duckdb
import pytest

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.serving.run import build_serving_snapshots, run_serving_snapshots


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


def _prepare_gold_inputs(settings: BuildSettings) -> None:
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.bronze_dir)
    ensure_dir(settings.ml_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 101,
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "primary_wipo_field": "Computer technology",
                "family_priority_year": 2018,
                "family_composite_status": "fully_active",
                "family_size_docdb": 3,
                "family_tech_breadth_wipo_count": 2,
                "active_jurisdiction_count": 2.0,
                "active_grant_branch_count": 2.0,
                "lapsed_jurisdiction_count": 0.0,
                "opposed_branch_count": 0.0,
                "has_any_active_grant": True,
                "family_fwd_cits7_percentile": 0.81,
                "family_quality_index_6_score": 0.72,
                "oecd_quality_percentile": 0.75,
                "oecd_quality_proxy_score": 0.74,
            },
            {
                "docdb_family_id": 202,
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "primary_wipo_field": "Computer technology",
                "family_priority_year": 2018,
                "family_composite_status": "fully_active",
                "family_size_docdb": 2,
                "family_tech_breadth_wipo_count": 1,
                "active_jurisdiction_count": 1.0,
                "active_grant_branch_count": 1.0,
                "lapsed_jurisdiction_count": 0.0,
                "opposed_branch_count": 0.0,
                "has_any_active_grant": True,
                "family_fwd_cits7_percentile": 0.44,
                "family_quality_index_6_score": 0.41,
                "oecd_quality_percentile": 0.48,
                "oecd_quality_proxy_score": 0.46,
            },
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 101,
                "family_ui_blocking_power_score": 91.0,
                "family_overall_legal_enforceability_score": 4.2,
                "family_market_threat_score_raw": 0.8,
            },
            {
                "docdb_family_id": 202,
                "family_ui_blocking_power_score": 63.0,
                "family_overall_legal_enforceability_score": 2.4,
                "family_market_threat_score_raw": 0.4,
            },
        ],
        settings.gold_dir / "gold_family_blocking_power.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 101,
                "is_latest_observed_year": True,
                "primary_wipo_field_current": "Computer technology",
                "family_composite_status_asof": "fully_active",
                "family_enforceability_score_asof": 4.2,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_jurisdiction_count_asof": 2.0,
                "pre_asof_forward_citations_weighted": 16.5,
                "data_completeness_pct_asof": 1.0,
                "historical_compare_safe": True,
                "historical_oecd_supported": True,
                "current_owner_metadata_only": False,
            },
            {
                "docdb_family_id": 202,
                "is_latest_observed_year": True,
                "primary_wipo_field_current": "Computer technology",
                "family_composite_status_asof": "fully_active",
                "family_enforceability_score_asof": 2.4,
                "family_active_jurisdiction_share_asof": 1.0,
                "family_jurisdiction_count_asof": 1.0,
                "pre_asof_forward_citations_weighted": 7.0,
                "data_completeness_pct_asof": 1.0,
                "historical_compare_safe": True,
                "historical_oecd_supported": True,
                "current_owner_metadata_only": False,
            },
        ],
        settings.gold_dir / "gold_family_compare_pit.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 101, "heritage_mass": 12.0}],
        settings.gold_dir / "gold_family_heritage_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "snapshot_date": "2026-03-15",
                "portfolio_family_count_within_mega_cluster": 2,
                "portfolio_total_mass_score": 80.0,
                "portfolio_current_threat_score": 30.0,
                "portfolio_heritage_score": 50.0,
                "portfolio_avg_blocking_power_within_mega_cluster": 75.0,
                "portfolio_hit_rate_top_decile": 0.6,
                "portfolio_crown_jewel_index": 12.0,
            },
            {
                "owner_name_harmonized": "BETA",
                "owner_name_display": "Beta",
                "snapshot_date": "2026-03-15",
                "portfolio_family_count_within_mega_cluster": 2,
                "portfolio_total_mass_score": 40.0,
                "portfolio_current_threat_score": 10.0,
                "portfolio_heritage_score": 20.0,
                "portfolio_avg_blocking_power_within_mega_cluster": 35.0,
                "portfolio_hit_rate_top_decile": 0.2,
                "portfolio_crown_jewel_index": 5.0,
            },
        ],
        settings.gold_dir / "gold_portfolio_summary.parquet",
    )
    write_pylist_parquet(
        [{"owner_name_harmonized": "APPLE", "citation_forecast_3y_total": 10.0}],
        settings.gold_dir / "gold_portfolio_forecast_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display_current": "Apple",
                "as_of_year": 2024,
                "classification_type": "WIPO_FIELD",
                "classification_code": "Computer technology",
                "classification_label": "Computer technology",
                "classification_rank_within_owner_year": 1,
                "portfolio_family_share_asof": 0.6,
                "portfolio_family_count_in_classification_asof": 2,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display_current": "Apple",
                "as_of_year": 2024,
                "classification_type": "WIPO_FIELD",
                "classification_code": "Digital communication",
                "classification_label": "Digital communication",
                "classification_rank_within_owner_year": 2,
                "portfolio_family_share_asof": 0.4,
                "portfolio_family_count_in_classification_asof": 1,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display_current": "Apple",
                "as_of_year": 2025,
                "classification_type": "WIPO_FIELD",
                "classification_code": "Computer technology",
                "classification_label": "Computer technology",
                "classification_rank_within_owner_year": 1,
                "portfolio_family_share_asof": 0.7,
                "portfolio_family_count_in_classification_asof": 2,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display_current": "Apple",
                "as_of_year": 2025,
                "classification_type": "WIPO_FIELD",
                "classification_code": "Digital communication",
                "classification_label": "Digital communication",
                "classification_rank_within_owner_year": 2,
                "portfolio_family_share_asof": 0.3,
                "portfolio_family_count_in_classification_asof": 1,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display_current": "Apple",
                "as_of_year": 2024,
                "classification_type": "CPC_MAIN_GROUP",
                "classification_code": "H04L",
                "classification_label": "H04L",
                "classification_rank_within_owner_year": 1,
                "portfolio_family_share_asof": 0.5,
                "portfolio_family_count_in_classification_asof": 1,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display_current": "Apple",
                "as_of_year": 2024,
                "classification_type": "CPC_MAIN_GROUP",
                "classification_code": "G06F",
                "classification_label": "G06F",
                "classification_rank_within_owner_year": 2,
                "portfolio_family_share_asof": 0.5,
                "portfolio_family_count_in_classification_asof": 1,
            },
            {
                "owner_name_harmonized": "APPLE",
                "owner_name_display_current": "Apple",
                "as_of_year": 2025,
                "classification_type": "CPC_MAIN_GROUP",
                "classification_code": "H04L",
                "classification_label": "H04L",
                "classification_rank_within_owner_year": 1,
                "portfolio_family_share_asof": 1.0,
                "portfolio_family_count_in_classification_asof": 2,
            },
        ],
        settings.gold_dir / "gold_portfolio_classification_mix_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 101,
                "as_of_year": 2024,
                "primary_wipo_field_asof": "Computer technology",
                "cpc_main_groups_asof": ["H04L"],
            },
            {
                "docdb_family_id": 202,
                "as_of_year": 2024,
                "primary_wipo_field_asof": "Computer technology",
                "cpc_main_groups_asof": ["G06F"],
            },
            {
                "docdb_family_id": 101,
                "as_of_year": 2025,
                "primary_wipo_field_asof": "Computer technology",
                "cpc_main_groups_asof": ["H04L"],
            },
            {
                "docdb_family_id": 202,
                "as_of_year": 2025,
                "primary_wipo_field_asof": "Computer technology",
                "cpc_main_groups_asof": ["H04L", "G06F"],
            },
        ],
        settings.gold_dir / "gold_family_classification_mix_pit.parquet",
    )
    write_pylist_parquet(
        [{"owner_name_harmonized": "APPLE", "horizon": "3y", "wipo_field": "Computer technology"}],
        settings.gold_dir / "gold_portfolio_forecast_segments.parquet",
    )
    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "APPLE",
                "contributor_scope": "phase03_future_citations",
                "horizon": "3y",
                "contributor_entity_id": "101",
                "contribution_share": 0.7,
                "contribution_value": 2.5,
            }
        ],
        settings.gold_dir / "gold_portfolio_forecast_contributors.parquet",
    )
    write_pylist_parquet(
        [{"owner_name_harmonized": "APPLE", "heritage_mass": 8.0}],
        settings.gold_dir / "gold_portfolio_heritage_summary.parquet",
    )
    write_pylist_parquet(
        [{"owner_name_harmonized": "APPLE", "wipo_field": "Computer technology", "threat_exposure": 0.4}],
        settings.gold_dir / "gold_portfolio_threat_matrix.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 101,
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "is_primary_owner": True,
            },
            {
                "docdb_family_id": 202,
                "owner_name_harmonized": "APPLE",
                "owner_name_display": "Apple",
                "is_primary_owner": True,
            },
        ],
        settings.silver_dir / "silver_family_owner_bridge.parquet",
    )
    write_pylist_parquet(
        [
            {
                "pat_publn_id": 26064061,
                "appln_id": 11223344,
                "docdb_family_id": 101,
                "publn_auth": "EP",
                "publn_nr": "2606406",
                "publn_kind": "A1",
                "publn_date": "2013-07-10",
                "publication_number_full": "EP2606406A1",
                "is_application_stage": True,
                "is_grant_stage": False,
                "is_modifier_stage": False,
                "scope_type": "mega_cluster_bounded",
                "snapshot_date": "2026-03-15",
            },
            {
                "pat_publn_id": 26064062,
                "appln_id": 11223344,
                "docdb_family_id": 101,
                "publn_auth": "EP",
                "publn_nr": "2606406",
                "publn_kind": "B1",
                "publn_date": "2018-11-14",
                "publication_number_full": "EP2606406B1",
                "is_application_stage": False,
                "is_grant_stage": True,
                "is_modifier_stage": False,
                "scope_type": "mega_cluster_bounded",
                "snapshot_date": "2026-03-15",
            },
        ],
        settings.silver_dir / "silver_family_member_publications.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 11223344,
                "appln_filing_date": "2012-12-19",
            }
        ],
        settings.bronze_dir / "bronze_patstat_appln.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 11223344,
                "appln_title_lg": "en",
                "appln_title": "Signal routing for adaptive network switching",
            }
        ],
        settings.bronze_dir / "bronze_patstat_appln_title.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 11223344,
                "appln_abstract_lg": "en",
                "appln_abstract": "An adaptive routing system for network traffic.",
            }
        ],
        settings.bronze_dir / "bronze_patstat_appln_abstr.parquet",
    )
    write_pylist_parquet(
        [
            {
                "epab_doc_id": "epab-1",
                "publication_number_full": "EP2606406A1",
                "publication_authority": "EP",
                "publication_number": "2606406",
                "publication_kind": "A1",
                "publication_date": "2013-07-10",
                "language_code": "en",
            }
        ],
        settings.bronze_dir / "bronze_epab_publication.parquet",
    )
    write_pylist_parquet(
        [
            {
                "epab_doc_id": "epab-1",
                "claim_sequence_no": 1,
                "language_code": "en",
                "claim_text_plain": "A routing apparatus comprising an adaptive signal controller.",
            }
        ],
        settings.bronze_dir / "bronze_epab_claims.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 11223344,
                "docdb_family_id": 101,
                "reg101_id": 77,
                "register_record_present": True,
                "ep_registered_license_flag": True,
                "ep_licensee_names": "Acme Licensing GmbH",
                "register_snapshot_date": "2026-03-15",
            },
            {
                "appln_id": 11223344,
                "docdb_family_id": 101,
                "reg101_id": 12,
                "register_record_present": False,
                "ep_registered_license_flag": False,
                "ep_licensee_names": None,
                "register_snapshot_date": "2025-12-01",
            }
        ],
        settings.silver_dir / "silver_ep_register_core.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 11223344,
                "docdb_family_id": 101,
                "snapshot_date": "2026-03-15",
                "ep_display_status_text": "pending_examination",
                "status_source": "REGISTER_CORE",
            }
        ],
        settings.silver_dir / "silver_ep_register_display_ledger.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 11223344,
                "ep_proc_step_maturity_score": 0.81,
                "ep_search_report_mailed_date": "2014-01-12",
                "ep_latest_proc_phase_code": "EXAM",
                "ep_latest_proc_result_code": "PENDING",
                "ep_proc_time_limit_days": 120,
            }
        ],
        settings.silver_dir / "silver_ep_register_proc_step_features.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 11223344,
                "ep_register_is_unitary_patent": False,
                "ep_register_up_status_code": None,
                "ep_register_up_status_text": None,
                "ep_register_up_event_latest_date": None,
            }
        ],
        settings.silver_dir / "silver_ep_register_up_status.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 11223344,
                "ep_opposition_active": True,
                "ep_opposition_status_text": "ADMISSIBLE",
                "ep_opponent_names": "Challenger GmbH",
                "ep_opponent_agent_names": None,
                "ep_appeal_active": False,
                "ep_appeal_result_text": None,
            },
            {
                "appln_id": 11223344,
                "ep_opposition_active": False,
                "ep_opposition_status_text": None,
                "ep_opponent_names": None,
                "ep_opponent_agent_names": None,
                "ep_appeal_active": False,
                "ep_appeal_result_text": None,
            }
        ],
        settings.silver_dir / "silver_ep_register_current_opposition.parquet",
    )
    write_pylist_parquet(
        [
            {
                "appln_id": 11223344,
                "ep_register_lead_agent_name": "Meyer IP",
                "ep_register_lead_agent_country": "DE",
                "ep_register_agent_customer_id": 991,
            }
        ],
        settings.silver_dir / "silver_ep_register_agent_summary.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 101, "text_scope": "abstract", "semantic_summary": "test"}],
        settings.gold_dir / "gold_semantic_match_context.parquet",
    )
    write_pylist_parquet(
        [{"as_of_year": 2025, "primary_wipo_field": "Computer technology", "family_count": 100}],
        settings.gold_dir / "gold_market_intelligence_overview.parquet",
    )
    write_pylist_parquet(
        [{"as_of_year": 2025, "primary_wipo_field": "Computer technology", "segment_rank": 1}],
        settings.gold_dir / "gold_market_intelligence_segments.parquet",
    )
    write_pylist_parquet(
        [{"as_of_year": 2025, "primary_wipo_field": "Computer technology", "filing_count": 100}],
        settings.gold_dir / "gold_market_intelligence_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 101,
                "snapshot_year": 2025,
                "snapshot_date": "2026-03-15",
                "family_composite_status": "under_fire",
            }
        ],
        settings.silver_dir / "silver_family_status_history.parquet",
    )
    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "APPLE",
                "snapshot_date": "2026-03-15",
                "wipo_field": "Computer technology",
                "active_family_count": 2,
                "enforceability_score": 0.75,
                "heritage_score": 0.81,
            }
        ],
        settings.gold_dir / "gold_portfolio_field_timeseries.parquet",
    )
    write_pylist_parquet(
        [
            {
                "owner_name_harmonized": "APPLE",
                "as_of_year": 2025,
                "historical_compare_safe": True,
                "portfolio_avg_enforceability_score_asof": 0.8,
            }
        ],
        settings.gold_dir / "gold_portfolio_compare_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "as_of_year": 2025,
                "wipo_industry_code": "Computer technology",
                "segment_family_count_stock_asof": 100,
            }
        ],
        settings.gold_dir / "gold_market_summary_pit.parquet",
    )
    write_pylist_parquet(
        [
            {
                "segment_key": "Computer technology",
                "leaderboard_entity_type": "owner",
                "as_of_year": 2025,
                "leaderboard_rank": 1,
                "owner_name_harmonized": "APPLE",
                "owner_name_display_current": "Apple",
            }
        ],
        settings.gold_dir / "gold_market_leaderboard_pit.parquet",
    )


def test_serving_snapshots_stage_is_exposed() -> None:
    assert callable(build_serving_snapshots)
    assert callable(run_serving_snapshots)


def test_build_serving_snapshots_materializes_duckdb_and_manifest_contracts(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    settings.execution = {
        "serving_snapshot_threads": 1,
        "serving_publication_chunk_target_rows": 1,
        "serving_publication_chunk_max_count": 8,
    }
    _prepare_gold_inputs(settings)

    result = build_serving_snapshots(settings)

    serving_dir = settings.repo_root / "etl" / "data" / "serving"
    core_path = serving_dir / "core_serving.duckdb"
    analytics_path = serving_dir / "analytics_serving.duckdb"
    semantic_path = serving_dir / "semantic_serving.duckdb"
    market_path = serving_dir / "market_serving.duckdb"
    publication_path = serving_dir / "publication_serving"
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    audit_path = serving_dir / "serving_snapshot_audit.json"

    assert result.status == "success"
    assert core_path.exists()
    assert analytics_path.exists()
    assert semantic_path.exists()
    assert market_path.exists()
    assert publication_path.exists()
    assert manifest_path.exists()
    assert audit_path.exists()
    assert not (serving_dir / "_duckdb_tmp").exists()
    assert not (serving_dir / "_tmp_publication_evidence").exists()
    assert not (serving_dir / "_publication_application_support").exists()

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["snapshots"]["core"]["filename"] == "core_serving.duckdb"
    assert manifest["snapshots"]["analytics"]["filename"] == "analytics_serving.duckdb"
    assert "family_compare_current_serving" in manifest["snapshots"]["core"]["tables"]
    assert "portfolio_compare_current_serving" in manifest["snapshots"]["core"]["tables"]
    assert "portfolio_classification_current_serving" in manifest["snapshots"]["core"]["tables"]
    assert "family_status_history" in manifest["snapshots"]["analytics"]["tables"]
    assert "portfolio_field_timeseries" in manifest["snapshots"]["analytics"]["tables"]
    assert "portfolio_compare_pit" in manifest["snapshots"]["analytics"]["tables"]
    assert "market_summary_pit" in manifest["snapshots"]["analytics"]["tables"]
    assert "publication_evidence_serving" not in manifest["snapshots"]["core"]["tables"]
    assert manifest["snapshots"]["publication"]["filename"] == "publication_serving"
    assert "publication_member_by_number" in manifest["snapshots"]["publication"]["tables"]
    assert "application_evidence_by_appln" in manifest["snapshots"]["publication"]["tables"]
    assert "publication_claim_by_number" in manifest["snapshots"]["publication"]["tables"]
    assert "family_publications_by_family" in manifest["snapshots"]["publication"]["tables"]

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["snapshots"]["core"]["table_stats"]["family_compare_current_serving"]["rows"] == 2
    assert audit["snapshots"]["analytics"]["table_stats"]["family_status_history"]["rows"] == 1
    assert audit["snapshots"]["analytics"]["table_stats"]["portfolio_field_timeseries"]["rows"] == 1
    assert audit["snapshots"]["analytics"]["table_stats"]["portfolio_compare_pit"]["rows"] == 1
    assert audit["snapshots"]["core"]["table_stats"]["portfolio_compare_current_serving"]["rows"] == 2
    assert audit["snapshots"]["core"]["table_stats"]["portfolio_classification_current_serving"]["rows"] == 3
    assert audit["snapshots"]["publication"]["table_stats"]["publication_member_by_number"]["rows"] == 2
    assert audit["snapshots"]["publication"]["table_stats"]["application_evidence_by_appln"]["rows"] == 1
    assert audit["snapshots"]["publication"]["table_stats"]["publication_claim_by_number"]["rows"] == 1
    assert audit["snapshots"]["publication"]["table_stats"]["family_publications_by_family"]["rows"] == 2
    for dataset_name in [
        "publication_member_by_number",
        "application_evidence_by_appln",
        "publication_claim_by_number",
        "family_publications_by_family",
    ]:
        partition_dirs = sorted(path for path in (publication_path / dataset_name).iterdir() if path.is_dir())
        assert partition_dirs
        assert all((partition_dir / "data.parquet").exists() for partition_dir in partition_dirs)
        assert all(len(list(partition_dir.glob("*.parquet"))) == 1 for partition_dir in partition_dirs)

    con = duckdb.connect(str(core_path))
    tables = {
        row[0]
        for row in con.execute(
            "select table_name from information_schema.tables where table_schema = 'main'"
        ).fetchall()
    }
    assert "family_summary" in tables
    assert "family_compare_current_serving" in tables
    assert "portfolio_compare_current_serving" in tables
    assert "portfolio_classification_current_serving" in tables
    assert "publication_evidence_serving" not in tables
    compare_rows = con.execute(
        """
        select
            docdb_family_id,
            family_composite_status,
            family_composite_status_asof,
            opposition_overlay_active,
            family_ui_blocking_power_score,
            legal_durability_percentile,
            citation_heritage_percentile
        from family_compare_current_serving
        order by docdb_family_id
        """
    ).fetchall()
    family_summary_rows = con.execute(
        """
        select
            docdb_family_id,
            mart_family_composite_status,
            family_composite_status,
            active_opposition_application_count,
            opposition_overlay_active,
            mart_opposed_branch_count,
            opposed_branch_count
        from family_summary
        order by docdb_family_id
        """
    ).fetchall()
    portfolio_compare_rows = con.execute(
        """
        select owner_name_harmonized, peer_bucket, portfolio_total_mass_score_percentile
        from portfolio_compare_current_serving
        order by owner_name_harmonized
        """
    ).fetchall()
    classification_rows = con.execute(
        """
        select
            owner_name_harmonized,
            classification_type,
            segment,
            classification_label,
            rank,
            family_share,
            trajectory
        from portfolio_classification_current_serving
        order by classification_type, rank
        """
    ).fetchall()
    con.close()

    publication_con = duckdb.connect()
    publication_rows = publication_con.execute(
        """
        select
            publication_number_full,
            family_composite_status,
            active_opposition_application_count,
            opposition_overlay_active
        from read_parquet(?, hive_partitioning=true)
        order by publication_number_full
        """,
        [str(publication_path / "publication_member_by_number" / "*/*.parquet")],
    ).fetchall()
    application_rows = publication_con.execute(
        """
        select
            appln_id,
            title_text,
            abstract_text,
            appln_filing_date,
            register_record_present,
            ep_register_lead_agent_name
        from read_parquet(?, hive_partitioning=true)
        order by appln_id
        """,
        [str(publication_path / "application_evidence_by_appln" / "*/*.parquet")],
    ).fetchall()
    application_contract = publication_con.execute(
        """
        select
            count(*) as row_count,
            count(distinct appln_id) as distinct_appln_id_count
        from read_parquet(?, hive_partitioning=true)
        """,
        [str(publication_path / "application_evidence_by_appln" / "*/*.parquet")],
    ).fetchone()
    claim_rows = publication_con.execute(
        """
        select
            publication_number_full,
            claim_1_text
        from read_parquet(?, hive_partitioning=true)
        order by publication_number_full
        """,
        [str(publication_path / "publication_claim_by_number" / "*/*.parquet")],
    ).fetchall()
    claim_contract = publication_con.execute(
        """
        select
            count(*) as row_count,
            count(distinct publication_number_full) as distinct_publication_count
        from read_parquet(?, hive_partitioning=true)
        """,
        [str(publication_path / "publication_claim_by_number" / "*/*.parquet")],
    ).fetchone()
    family_publication_rows = publication_con.execute(
        """
        select
            docdb_family_id,
            publication_number_full,
            publn_kind,
            publn_date,
            is_application_stage,
            is_grant_stage
        from read_parquet(?, hive_partitioning=true)
        order by publication_number_full
        """,
        [str(publication_path / "family_publications_by_family" / "*/*.parquet")],
    ).fetchall()
    publication_con.close()

    assert family_summary_rows[0] == (101, "fully_active", "under_fire", 1, True, 0.0, 1.0)
    assert family_summary_rows[1] == (202, "fully_active", "fully_active", 0, False, 0.0, 0.0)
    assert compare_rows[0][0] == 101
    assert compare_rows[0][1] == "under_fire"
    assert compare_rows[0][2] == "under_fire"
    assert compare_rows[0][3] is True
    assert compare_rows[0][4] == 91.0
    assert compare_rows[0][5] == 0.0
    assert compare_rows[0][6] == 100.0
    assert compare_rows[1][0] == 202
    assert compare_rows[1][5] == 0.0
    assert compare_rows[1][6] == 0.0
    assert portfolio_compare_rows[0] == ("APPLE", "2_5", 100.0)
    assert portfolio_compare_rows[1] == ("BETA", "2_5", 0.0)
    assert classification_rows[0] == ("APPLE", "CPC_MAIN_GROUP", "H04L", "H04L", 1, 1.0, 0.5)
    assert classification_rows[1][:6] == ("APPLE", "WIPO_FIELD", "Computer technology", "Computer technology", 1, 0.7)
    assert classification_rows[1][6] == pytest.approx(0.1)
    assert classification_rows[2][:6] == ("APPLE", "WIPO_FIELD", "Digital communication", "Digital communication", 2, 0.3)
    assert classification_rows[2][6] == pytest.approx(-0.1)
    assert publication_rows[0] == ("EP2606406A1", "under_fire", 1, True)
    assert publication_rows[1] == ("EP2606406B1", "under_fire", 1, True)
    assert application_contract == (1, 1)
    assert application_rows[0][0] == 11223344
    assert application_rows[0][1] == "Signal routing for adaptive network switching"
    assert application_rows[0][2] == "An adaptive routing system for network traffic."
    assert str(application_rows[0][3]) == "2012-12-19"
    assert application_rows[0][4] is True
    assert application_rows[0][5] == "Meyer IP"
    assert claim_contract == (1, 1)
    assert claim_rows[0] == ("EP2606406A1", "A routing apparatus comprising an adaptive signal controller.")
    assert family_publication_rows[0][0] == 101
    assert family_publication_rows[0][1] == "EP2606406A1"
    assert family_publication_rows[1][1] == "EP2606406B1"

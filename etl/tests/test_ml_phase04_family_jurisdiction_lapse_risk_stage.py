from __future__ import annotations

import json
from pathlib import Path

import duckdb
import numpy as np

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.ml.phase04 import build_ml_phase04_family_jurisdiction_lapse_risk
from patentiq_etl.ml.phase04 import _apply_isotonic_calibrator
from patentiq_etl.ml.phase04 import _apply_platt_scaler
from patentiq_etl.ml.phase04 import _average_precision
from patentiq_etl.ml.phase04 import _fit_isotonic_calibrator
from patentiq_etl.ml.phase04 import _fit_platt_scaler
from patentiq_etl.ml.phase04 import _roc_auc
from patentiq_etl.ml.run import run_ml_phase04_family_jurisdiction_lapse_risk


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


def test_ml_phase04_family_jurisdiction_lapse_risk_stage_is_exposed() -> None:
    assert callable(build_ml_phase04_family_jurisdiction_lapse_risk)
    assert callable(run_ml_phase04_family_jurisdiction_lapse_risk)


def test_phase04_probability_helpers_behave_sensibly() -> None:
    y_true = np.array([0, 0, 1, 1], dtype=int)
    perfect = np.array([0.1, 0.2, 0.8, 0.9], dtype=float)
    assert _roc_auc(y_true, perfect) == 1.0
    assert _average_precision(y_true, perfect) == 1.0

    platt = _fit_platt_scaler(y_true, perfect)
    platt_probs = _apply_platt_scaler(perfect, platt)
    assert np.all(platt_probs >= 0.0)
    assert np.all(platt_probs <= 1.0)

    isotonic = _fit_isotonic_calibrator(y_true, perfect)
    isotonic_probs = _apply_isotonic_calibrator(perfect, isotonic)
    assert np.all(isotonic_probs[:-1] <= isotonic_probs[1:])


def test_build_ml_phase04_family_jurisdiction_lapse_risk_materializes_contracts(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)
    ensure_dir(settings.ml_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "family_priority_year": 2018,
                "family_earliest_priority_date": "2018-05-01",
                "primary_wipo_field": "Computer technology",
                "is_main_window_family": True,
            },
            {
                "docdb_family_id": 2,
                "family_priority_year": 2021,
                "family_earliest_priority_date": "2021-02-10",
                "primary_wipo_field": "Digital communication",
                "is_main_window_family": True,
            },
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2022,
                "snapshot_date": "2022-12-31",
                "replay_branch_state": "ACTIVE_GRANT",
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "last_grant_event_date": "2020-06-01",
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
            },
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "snapshot_year": 2023,
                "snapshot_date": "2023-12-31",
                "replay_branch_state": "ACTIVE_GRANT",
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "last_grant_event_date": "2020-06-01",
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "EP",
                "snapshot_year": 2024,
                "snapshot_date": "2024-12-31",
                "replay_branch_state": "ACTIVE_GRANT",
                "active_branch_flag": True,
                "lapsed_or_expired_flag": False,
                "last_grant_event_date": "2023-04-15",
                "last_lapse_event_date": None,
                "last_expiry_event_date": None,
            },
        ],
        settings.silver_dir / "silver_branch_status_history_dense.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "jurisdiction_code": "US",
                "event_date": "2023-06-30",
                "is_lapse_event": True,
                "is_expiry_event": False,
            },
            {
                "docdb_family_id": 2,
                "jurisdiction_code": "EP",
                "event_date": "2027-01-10",
                "is_lapse_event": False,
                "is_expiry_event": True,
            },
        ],
        settings.silver_dir / "silver_legal_status_event_ledger.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 1,
                "as_of_date": "2022-12-31",
                "as_of_year": 2022,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 2.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_size_docdb_asof": 3.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_coverage_stability_score_asof": 0.8,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 0.6,
                "family_blocking_power_score_asof": 0.7,
                "family_enforceability_score_asof": 0.9,
                "pre_asof_forward_citations_clean": 4.0,
                "pre_asof_forward_citations_weighted": 3.5,
                "family_rcf_score_asof": 0.5,
                "pre_asof_unique_citing_family_count": 2.0,
                "pre_asof_citing_assignee_diversity": 0.4,
                "pre_asof_attacker_density_score": 0.2,
                "data_completeness_pct_asof": 1.0,
            },
            {
                "docdb_family_id": 1,
                "as_of_date": "2023-12-31",
                "as_of_year": 2023,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_size_docdb_asof": 3.0,
                "family_jurisdiction_count_asof": 2.0,
                "family_coverage_stability_score_asof": 0.75,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 0.58,
                "family_blocking_power_score_asof": 0.68,
                "family_enforceability_score_asof": 0.88,
                "pre_asof_forward_citations_clean": 5.0,
                "pre_asof_forward_citations_weighted": 4.3,
                "family_rcf_score_asof": 0.49,
                "pre_asof_unique_citing_family_count": 3.0,
                "pre_asof_citing_assignee_diversity": 0.45,
                "pre_asof_attacker_density_score": 0.22,
                "data_completeness_pct_asof": 1.0,
            },
            {
                "docdb_family_id": 2,
                "as_of_date": "2024-12-31",
                "as_of_year": 2024,
                "is_observed_as_of_snapshot": True,
                "family_composite_status_asof": "fully_active",
                "active_jurisdiction_count_asof": 1.0,
                "active_grant_branch_count_asof": 1.0,
                "lapsed_jurisdiction_count_asof": 0.0,
                "family_size_docdb_asof": 2.0,
                "family_jurisdiction_count_asof": 1.0,
                "family_coverage_stability_score_asof": 0.9,
                "family_tech_breadth_wipo_count_asof": 1.0,
                "family_field_contribution_primary_asof": 0.7,
                "family_blocking_power_score_asof": 0.6,
                "family_enforceability_score_asof": 0.85,
                "pre_asof_forward_citations_clean": 1.0,
                "pre_asof_forward_citations_weighted": 0.8,
                "family_rcf_score_asof": 0.3,
                "pre_asof_unique_citing_family_count": 1.0,
                "pre_asof_citing_assignee_diversity": 0.2,
                "pre_asof_attacker_density_score": 0.1,
                "data_completeness_pct_asof": 1.0,
            },
        ],
        settings.silver_dir / "silver_family_feature_snapshot_pit_dense.parquet",
    )
    write_pylist_parquet(
        [
            {
                "model_scope": "family_future_citation_forecast",
                "entity_id": "100",
                "root_family_id": 100,
                "split_name": "train",
                "split_strategy": "family_grouped_time_by_priority_year",
                "snapshot_cutoff": "2020-12-31",
                "primary_wipo_field": "Computer technology",
                "time_key_year": 2015,
            }
        ],
        settings.ml_dir / "ml_split_registry.parquet",
    )
    write_pylist_parquet(
        [
            {
                "model_scope": "family_future_citation_forecast",
                "feature_name": "family_rcf_score",
                "feature_table": "ml_feature_family_future_citations.parquet",
                "feature_type": "numeric",
                "null_policy": "explicit_missing_allowed",
                "is_leakage_sensitive": False,
                "introduced_in_version": "legacy",
            }
        ],
        settings.ml_dir / "ml_feature_manifest.parquet",
    )

    result = build_ml_phase04_family_jurisdiction_lapse_risk(settings)
    assert result.status == "success"

    label_table = settings.ml_dir / "ml_label_family_jurisdiction_lapse_risk.parquet"
    feature_table = settings.ml_dir / "ml_feature_family_jurisdiction_lapse_risk.parquet"
    split_table = settings.ml_dir / "ml_split_registry.parquet"
    phase_split_table = settings.ml_dir / "ml_split_registry_phase04.parquet"
    model_card = settings.ml_dir / "model_card_family_jurisdiction_lapse_risk.json"

    labels = duckdb.sql(f"select * from read_parquet('{label_table}') order by docdb_family_id, as_of_year").df()
    assert labels.shape[0] == 3
    family1_2022 = labels[(labels.docdb_family_id == 1) & (labels.as_of_year == 2022)].iloc[0]
    assert family1_2022["lapse_risk_12m_label"] == 1
    assert family1_2022["lapse_risk_24m_label"] == 1
    family1_2023 = labels[(labels.docdb_family_id == 1) & (labels.as_of_year == 2023)].iloc[0]
    assert family1_2023["lapse_risk_12m_label"] == 0
    assert family1_2023["lapse_risk_24m_label"] == 0
    assert bool(family1_2023["is_observed_24m"]) is True
    family2_2024 = labels[(labels.docdb_family_id == 2) & (labels.as_of_year == 2024)].iloc[0]
    assert bool(family2_2024["is_observed_24m"]) is False

    features = duckdb.sql(f"select * from read_parquet('{feature_table}') order by docdb_family_id, as_of_year").df()
    assert "jurisdiction_is_us" in features.columns
    assert "family_blocking_power_score_asof" in features.columns
    assert features.shape[0] == 3

    split_registry = duckdb.sql(
        f"""
        select * from read_parquet('{split_table}')
        where model_scope = 'family_jurisdiction_lapse_risk'
        order by entity_id
        """
    ).df()
    assert split_registry.shape[0] == 2
    assert set(split_registry["split_name"]) <= {"train", "validation", "test", "unassigned_recent"}
    phase_split_registry = duckdb.sql(
        f"""
        select * from read_parquet('{phase_split_table}')
        order by entity_id
        """
    ).df()
    assert phase_split_registry.shape[0] == 2
    assert set(phase_split_registry["split_name"]) <= {"train", "validation", "test", "unassigned_recent"}

    legacy_split = duckdb.sql(
        f"""
        select count(*) as c from read_parquet('{split_table}')
        where model_scope = 'family_future_citation_forecast'
        """
    ).df()["c"][0]
    assert legacy_split == 1

    feature_manifest = duckdb.sql(
        f"""
        select * from read_parquet('{settings.ml_dir / "ml_feature_manifest.parquet"}')
        where model_scope = 'family_jurisdiction_lapse_risk'
        """
    ).df()
    assert "branch_state_asof" in set(feature_manifest["feature_name"])

    model_card_payload = json.loads(model_card.read_text(encoding="utf-8"))
    assert model_card_payload["training_status"] == "insufficient_split_rows"
    assert model_card_payload["split_registry"] == str(phase_split_table)
    assert model_card_payload["split_registry_shared"] == str(split_table)

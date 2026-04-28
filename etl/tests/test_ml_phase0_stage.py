from __future__ import annotations

import json
from pathlib import Path

import duckdb

from patentiq_etl.common.io import ensure_dir, write_pylist_parquet
from patentiq_etl.common.types import BuildSettings
from patentiq_etl.ml.phase0 import build_ml_phase0_foundation
from patentiq_etl.ml.run import run_ml_phase0_foundation


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


def test_ml_phase0_stage_is_exposed() -> None:
    assert callable(build_ml_phase0_foundation)
    assert callable(run_ml_phase0_foundation)


def test_build_ml_phase0_foundation_materializes_split_and_fixture_artifacts(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    ensure_dir(settings.silver_dir)
    ensure_dir(settings.gold_dir)

    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "family_priority_year": 2012,
                "is_main_window_family": True,
                "primary_wipo_field": "Computer technology",
                "family_composite_status": "fully_active",
            },
            {
                "docdb_family_id": 200,
                "family_priority_year": 2017,
                "is_main_window_family": True,
                "primary_wipo_field": "Computer technology",
                "family_composite_status": "dead",
            },
            {
                "docdb_family_id": 300,
                "family_priority_year": 2020,
                "is_main_window_family": True,
                "primary_wipo_field": "Digital communication",
                "family_composite_status": "pending_emerging",
            },
            {
                "docdb_family_id": 400,
                "family_priority_year": 2023,
                "is_main_window_family": True,
                "primary_wipo_field": "Digital communication",
                "family_composite_status": "partially_lapsed",
            },
        ],
        settings.gold_dir / "gold_family_summary.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "owner_name_harmonized": "ACME",
                "representative_stage": "STANDARD_GRANT",
                "representative_source_type": "EPAB_CLAIM",
                "text_provenance": "EPAB_EP1B1",
                "is_abstract_fallback": False,
                "is_semantic_candidate": True,
                "is_in_vector_sample": True,
                "covered_wipo_fields": ["Computer technology"],
                "family_ui_blocking_power_score": 82.0,
                "oecd_quality_percentile": 0.91,
            },
            {
                "docdb_family_id": 200,
                "owner_name_harmonized": "BETA",
                "representative_stage": "STANDARD_GRANT",
                "representative_source_type": "PATSTAT_ABSTRACT",
                "text_provenance": "PATSTAT_ABSTRACT",
                "is_abstract_fallback": True,
                "is_semantic_candidate": True,
                "is_in_vector_sample": True,
                "covered_wipo_fields": ["Computer technology"],
                "family_ui_blocking_power_score": 10.0,
                "oecd_quality_percentile": 0.11,
            },
            {
                "docdb_family_id": 300,
                "owner_name_harmonized": "GAMMA",
                "representative_stage": "PATSTAT_ABSTRACT_FALLBACK",
                "representative_source_type": "PATSTAT_ABSTRACT",
                "text_provenance": "PATSTAT_ABSTRACT",
                "is_abstract_fallback": True,
                "is_semantic_candidate": True,
                "is_in_vector_sample": True,
                "covered_wipo_fields": ["Digital communication"],
                "family_ui_blocking_power_score": 25.0,
                "oecd_quality_percentile": 0.25,
            },
            {
                "docdb_family_id": 400,
                "owner_name_harmonized": "DELTA",
                "representative_stage": "STANDARD_GRANT",
                "representative_source_type": "PATSTAT_ABSTRACT",
                "text_provenance": "PATSTAT_ABSTRACT",
                "is_abstract_fallback": True,
                "is_semantic_candidate": True,
                "is_in_vector_sample": True,
                "covered_wipo_fields": ["Digital communication"],
                "family_ui_blocking_power_score": 31.0,
                "oecd_quality_percentile": 0.41,
            },
        ],
        settings.gold_dir / "gold_semantic_match_context.parquet",
    )
    write_pylist_parquet(
        [
            {
                "docdb_family_id": 100,
                "representative_appln_id": 10,
                "representative_publn_id": 1000,
                "representative_claim_1_en": "claim text alpha",
                "representative_abstract_en": None,
                "representative_source_type": "EPAB_CLAIM",
                "text_provenance": "EPAB_EP1B1",
                "is_abstract_fallback": False,
            },
            {
                "docdb_family_id": 200,
                "representative_appln_id": 20,
                "representative_publn_id": 2000,
                "representative_claim_1_en": None,
                "representative_abstract_en": "abstract beta",
                "representative_source_type": "PATSTAT_ABSTRACT",
                "text_provenance": "PATSTAT_ABSTRACT",
                "is_abstract_fallback": True,
            },
            {
                "docdb_family_id": 300,
                "representative_appln_id": 30,
                "representative_publn_id": 3000,
                "representative_claim_1_en": None,
                "representative_abstract_en": "abstract gamma",
                "representative_source_type": "PATSTAT_ABSTRACT",
                "text_provenance": "PATSTAT_ABSTRACT",
                "is_abstract_fallback": True,
            },
            {
                "docdb_family_id": 400,
                "representative_appln_id": 40,
                "representative_publn_id": 4000,
                "representative_claim_1_en": None,
                "representative_abstract_en": "abstract delta",
                "representative_source_type": "PATSTAT_ABSTRACT",
                "text_provenance": "PATSTAT_ABSTRACT",
                "is_abstract_fallback": True,
            },
        ],
        settings.silver_dir / "silver_family_text_representative.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100}],
        settings.silver_dir / "silver_family_citation_metrics.parquet",
    )
    write_pylist_parquet(
        [
            {"docdb_family_id": 100, "family_composite_status": "fully_active"},
            {"docdb_family_id": 200, "family_composite_status": "dead"},
            {"docdb_family_id": 300, "family_composite_status": "pending_emerging"},
            {"docdb_family_id": 400, "family_composite_status": "partially_lapsed"},
        ],
        settings.silver_dir / "silver_family_status_pt.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100}],
        settings.silver_dir / "silver_family_status_history.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100}],
        settings.silver_dir / "silver_family_oecd_quality.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100}],
        settings.silver_dir / "silver_family_coverage_metrics.parquet",
    )
    write_pylist_parquet(
        [{"docdb_family_id": 100}],
        settings.silver_dir / "silver_family_enforceability_branches.parquet",
    )

    result = build_ml_phase0_foundation(settings).finish()
    assert result.status == "success"

    con = duckdb.connect()
    split_rows = con.execute(
        "select model_scope, entity_id, split_name from read_parquet(?) order by entity_id",
        [str(settings.ml_dir / "ml_split_registry.parquet")],
    ).fetchall()
    assert split_rows == [
        ("family_future_citation_forecast", "100", "train"),
        ("family_future_citation_forecast", "200", "validation"),
        ("family_future_citation_forecast", "300", "test"),
        ("family_future_citation_forecast", "400", "unassigned_recent"),
    ]

    fixture_groups = con.execute(
        "select fixture_group, count(*) from read_parquet(?) group by 1 order by 1",
        [str(settings.ml_dir / "semantic_eval_fixture_registry.parquet")],
    ).fetchall()
    assert fixture_groups == [
        ("claim_active_discovery", 1),
        ("dead_family_suppression", 1),
        ("partially_lapsed_watch", 1),
        ("pending_family_watch", 1),
    ]

    manifest = json.loads((settings.ml_dir / "training_snapshot_manifest.json").read_text(encoding="utf-8"))
    assert manifest["training_snapshot_id"] == "test-release-2026-03-15-phase0"
    assert len(manifest["source_tables"]) == 9

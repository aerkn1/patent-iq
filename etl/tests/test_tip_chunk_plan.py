from __future__ import annotations

import json
from pathlib import Path

from patentiq_etl.common.types import BuildSettings
from patentiq_etl.prebronze.plan import plan_tip_chunked_export, plan_tip_heritage_chunked_export


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="test-release",
        snapshot_date="2026-03-16",
        year_window_start=2018,
        year_window_end=2023,
        heritage_backfill_start=1996,
        heritage_backfill_end=2006,
        azure_publish_enabled=False,
        vector_sample_pct=0.1,
        active_grant_only_for_semantic=True,
        method_version="test",
        semantic_embedding_method="hash",
        semantic_ann_method="placeholder",
        patstat_source_mode="tip",
        register_source_mode="tip",
        epab_source_mode="tip",
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
        selected_wipo_fields=["Computer technology", "Digital communication"],
        thresholds={},
        azure={"container": "patentiq-data"},
        execution={
            "tip_chunked_export_enabled": True,
            "blob_intermediate_enabled": True,
            "upload_after_chunk": True,
            "cleanup_after_upload": True,
            "chunk_year_span": 3,
            "table_families": ["core", "citations"],
            "max_workers": {"core": 2, "citations": 1},
        },
    )


def test_tip_chunk_plan_writes_manifest(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    result = plan_tip_chunked_export(settings).finish()

    manifest_path = settings.manifests_dir / "chunks" / "tip_chunk_plan.json"
    assert result.status == "success"
    assert manifest_path.exists()

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["chunk_year_span"] == 3
    assert payload["table_families"] == ["core", "citations"]
    assert len(payload["chunks"]) == 8
    assert payload["chunks"][0]["chunk_id"].startswith("computer-technology__2018_2020__")
    assert payload["chunks"][-1]["chunk_id"].startswith("digital-communication__2021_2023__")


def test_tip_heritage_chunk_plan_writes_manifest(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    result = plan_tip_heritage_chunked_export(settings).finish()

    manifest_path = settings.manifests_dir / "chunks" / "tip_heritage_chunk_plan.json"
    assert result.status == "success"
    assert manifest_path.exists()

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["horizon_label"] == "heritage"
    assert payload["year_window_start"] == 1996
    assert payload["year_window_end"] == 2006
    assert payload["table_families"] == ["core", "publications", "citations"]
    assert payload["chunks"][0]["chunk_id"].startswith("heritage__computer-technology__1996_1998__")

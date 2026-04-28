from __future__ import annotations

import json
from pathlib import Path

import pytest

from patentiq_etl.common.types import BuildSettings
from patentiq_etl.publish.run import publish_release


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="demo-release",
        snapshot_date="2026-03-15",
        year_window_start=2007,
        year_window_end=2026,
        heritage_backfill_start=1996,
        heritage_backfill_end=2006,
        azure_publish_enabled=False,
        vector_sample_pct=0.1,
        active_grant_only_for_semantic=True,
        method_version="test",
        semantic_embedding_method="test",
        semantic_ann_method="test",
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
        ref_techn_field_ipc=root / "data/ipc.csv",
        scope_type="mvp",
        field_source="wipo",
        selected_wipo_fields=["Computer technology"],
        thresholds={},
        azure={
            "account_url": "https://example.blob.core.windows.net",
            "container": "patentiq-data",
            "connection_string_env": "AZURE_STORAGE_CONNECTION_STRING",
            "active_release_manifest_blob": "manifests/active_release.json",
        },
        execution={},
    )


def _write_text(path: Path, value: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def test_publish_release_stages_serving_and_nested_vector_artifacts(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    _write_text(settings.bronze_dir / "bronze_a.parquet", "bronze")
    _write_text(settings.silver_dir / "silver_a.parquet", "silver")
    _write_text(settings.gold_dir / "gold_a.parquet", "gold")
    _write_text(settings.ml_dir / "model_card_pending_grant_pipeline.json", '{"name":"pending"}')
    _write_text(settings.ml_dir / "training_snapshot_manifest.json", '{"training_snapshot_id":"ml-123"}')
    _write_text(settings.vectors_dir / "vec_embedding_manifest.json", '{"release_id":"vec-123","abstract_model_id":"a","claim_model_id":"b"}')
    _write_text(settings.vectors_dir / "vec_family_embeddings_abstracts.parquet", "abstracts")
    _write_text(settings.vectors_dir / "vec_family_embeddings_claims.parquet", "claims")
    _write_text(settings.vectors_dir / "vec_query_registry.parquet", "registry")
    _write_text(settings.vectors_dir / "vec_ann_index_manifest.json", '{"ann_method":"hnsw"}')
    _write_text(settings.vectors_dir / "ann" / "vec_ann_claims_hnsw.bin", "ann")
    _write_text(
        settings.repo_root / "etl/data/serving/serving_snapshot_manifest.json",
        json.dumps(
            {
                "serving_release": "serving-123",
                "snapshots": {
                    "core": {"filename": "core_serving.duckdb", "bytes": 10, "tables": ["family_summary"]},
                    "publication": {"filename": "publication_serving", "bytes": 20, "tables": ["publication_member_by_number"]},
                },
            }
        ),
    )
    _write_text(settings.repo_root / "etl/data/serving/serving_snapshot_audit.json", '{"status":"ok"}')
    _write_text(settings.repo_root / "etl/data/serving/core_serving.duckdb", "core")
    _write_text(settings.repo_root / "etl/data/serving/semantic_serving.duckdb", "semantic")
    _write_text(settings.repo_root / "etl/data/serving/market_serving.duckdb", "market")
    _write_text(settings.repo_root / "etl/data/serving/publication_serving/publication_member_by_number/part-000.parquet", "pub")

    [result] = publish_release(settings)

    release_dir = settings.releases_dir / settings.release_id
    release_manifest = json.loads((release_dir / "release-manifest.json").read_text(encoding="utf-8"))
    active_release = json.loads((settings.repo_root / "etl/manifests/releases/active_release.json").read_text(encoding="utf-8"))

    assert result.status == "success"
    assert (release_dir / "serving/core_serving.duckdb").exists()
    assert (release_dir / "serving/publication_serving/publication_member_by_number/part-000.parquet").exists()
    assert (release_dir / "vectors/ann/vec_ann_claims_hnsw.bin").exists()
    assert release_manifest["artifacts"]["serving"]["blob_prefix"] == "releases/demo-release/serving"
    assert release_manifest["serving_release"] == "serving-123"
    assert release_manifest["semantic_model_dependencies"]["abstract"]["repo_id"] == "a"
    assert release_manifest["semantic_model_dependencies"]["abstract"]["packaged_in_release"] is False
    assert release_manifest["semantic_model_dependencies"]["claims"]["repo_id"] == "b"
    assert release_manifest["runtime_profiles"]["full"]["items"][-1]["path"] == "vectors/ann"
    assert active_release["release_manifest_blob"] == "releases/demo-release/release-manifest.json"


def test_publish_release_refuses_to_overwrite_existing_release_by_default(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    existing_release = settings.releases_dir / settings.release_id
    _write_text(existing_release / "stale.txt", "stale")

    with pytest.raises(RuntimeError, match="overwrite is disabled"):
        publish_release(settings)

from __future__ import annotations

import json
from pathlib import Path

from patentiq_etl.common.types import BuildSettings
from patentiq_etl.publish.runtime_release import prepare_runtime_release_manifest


def _settings(tmp_path: Path) -> BuildSettings:
    root = tmp_path / "repo"
    return BuildSettings(
        repo_root=root,
        release_id="runtime-demo",
        snapshot_date="2026-04-25",
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


def test_prepare_runtime_release_manifest_generates_release_and_upload_plan(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    serving_dir = settings.repo_root / "etl/data/serving"
    _write_text(
        serving_dir / "serving_snapshot_manifest.json",
        json.dumps(
            {
                "serving_release": "2026-04-25-serving",
                "snapshots": {
                    "core": {"filename": "core_serving.duckdb", "bytes": 10},
                    "publication": {"filename": "publication_serving", "bytes": 20},
                },
            }
        ),
    )
    _write_text(serving_dir / "serving_snapshot_audit.json", '{"status":"ok"}')
    _write_text(serving_dir / "core_serving.duckdb", "core")
    _write_text(serving_dir / "market_serving.duckdb", "market")
    _write_text(serving_dir / "semantic_serving.duckdb", "semantic")
    _write_text(serving_dir / "analytics_serving.duckdb", "analytics")
    _write_text(serving_dir / "publication_serving" / "application_evidence_by_appln" / "part-000.parquet", "pub")
    _write_text(serving_dir / ".DS_Store", "junk")

    _write_text(
        settings.vectors_dir / "vec_embedding_manifest.json",
        '{"release_id":"vec-123","abstract_model_id":"repo/a","claim_model_id":"repo/b"}',
    )
    _write_text(settings.vectors_dir / "vec_family_embeddings_abstracts.parquet", "abstracts")
    _write_text(settings.vectors_dir / "vec_family_embeddings_claims.parquet", "claims")
    _write_text(settings.vectors_dir / "vec_query_registry.parquet", "registry")
    _write_text(settings.vectors_dir / "vec_ann_index_manifest.json", '{"ann_method":"hnsw"}')
    _write_text(settings.vectors_dir / "vec_ann_exact_vs_ann_audit.json", '{"status":"ok"}')
    _write_text(settings.vectors_dir / "ann" / "vec_ann_claims_hnsw.bin", "ann")

    _write_text(settings.ml_dir / "training_snapshot_manifest.json", '{"training_snapshot_id":"ml-123"}')
    _write_text(settings.ml_dir / "model_card_pending_grant_pipeline.json", '{"name":"pending"}')
    _write_text(settings.ml_dir / "_tmp_phase08_phase04_latest_features.parquet", "tmp")

    outputs = prepare_runtime_release_manifest(settings)

    release_manifest = json.loads(outputs["release_manifest_path"].read_text(encoding="utf-8"))
    active_release = json.loads(outputs["active_release_path"].read_text(encoding="utf-8"))
    upload_plan = json.loads(outputs["upload_plan_path"].read_text(encoding="utf-8"))

    assert release_manifest["release_id"] == "runtime-demo"
    assert release_manifest["artifacts"]["serving"]["blob_prefix"] == "releases/runtime-demo/serving"
    assert release_manifest["serving_release"] == "2026-04-25-serving"
    assert release_manifest["training_snapshot_id"] == "ml-123"
    assert release_manifest["semantic_model_dependencies"]["abstract"]["repo_id"] == "repo/a"
    assert active_release["release_manifest_blob"] == "releases/runtime-demo/release-manifest.json"

    blob_paths = {entry["blob_path"] for entry in upload_plan["uploads"] if entry["type"] == "file"}
    assert "releases/runtime-demo/serving/core_serving.duckdb" in blob_paths
    assert (
        "releases/runtime-demo/serving/publication_serving/application_evidence_by_appln/part-000.parquet"
        in blob_paths
    )
    assert "releases/runtime-demo/models/model_card_pending_grant_pipeline.json" in blob_paths
    assert "releases/runtime-demo/models/_tmp_phase08_phase04_latest_features.parquet" in blob_paths
    assert "manifests/active_release.json" in blob_paths
    assert all(".DS_Store" not in blob_path for blob_path in blob_paths)

import json
from pathlib import Path

from config.settings import get_settings
from infrastructure.artifacts import ArtifactLocator


def test_artifact_locator_resolves_core_snapshot_from_local_manifest(tmp_path: Path, monkeypatch) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    core_path = serving_dir / "core_serving.duckdb"
    core_path.write_bytes(b"duckdb-placeholder")
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "serving_release": "test-serving",
                "contract_version": "1",
                "snapshots": {
                    "core": {
                        "filename": "core_serving.duckdb",
                        "tables": ["family_compare_current_serving"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    get_settings.cache_clear()

    locator = ArtifactLocator()
    assert locator.resolve_core_serving_duckdb() == core_path

    get_settings.cache_clear()


def test_artifact_locator_materializes_core_snapshot_from_file_url(tmp_path: Path, monkeypatch) -> None:
    remote_dir = tmp_path / "remote"
    remote_dir.mkdir(parents=True)
    core_path = remote_dir / "core_serving.duckdb"
    core_path.write_bytes(b"duckdb-placeholder")
    manifest_path = remote_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "serving_release": "test-serving",
                "contract_version": "1",
                "snapshots": {
                    "core": {
                        "filename": "core_serving.duckdb",
                        "uri": core_path.resolve().as_uri(),
                        "tables": ["family_compare_current_serving"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    cache_dir = tmp_path / "cache"

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "azure_blob_cached")
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_URL", manifest_path.resolve().as_uri())
    monkeypatch.setenv("PATENTIQ_V2_CACHE_DIR", str(cache_dir))
    get_settings.cache_clear()

    locator = ArtifactLocator()
    resolved = locator.resolve_core_serving_duckdb()
    assert resolved is not None
    assert resolved.exists()
    assert resolved != core_path
    assert resolved.parent == cache_dir
    assert resolved.read_bytes() == b"duckdb-placeholder"

    get_settings.cache_clear()


def test_artifact_locator_resolves_semantic_snapshot_from_local_manifest(tmp_path: Path, monkeypatch) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    semantic_path = serving_dir / "semantic_serving.duckdb"
    semantic_path.write_bytes(b"semantic-placeholder")
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "serving_release": "test-serving",
                "contract_version": "1",
                "snapshots": {
                    "semantic": {
                        "filename": "semantic_serving.duckdb",
                        "tables": ["semantic_match_context"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    get_settings.cache_clear()

    locator = ArtifactLocator()
    assert locator.resolve_semantic_serving_duckdb() == semantic_path

    get_settings.cache_clear()


def test_artifact_locator_resolves_market_snapshot_from_local_manifest(tmp_path: Path, monkeypatch) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    market_path = serving_dir / "market_serving.duckdb"
    market_path.write_bytes(b"market-placeholder")
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "serving_release": "test-serving",
                "contract_version": "1",
                "snapshots": {
                    "market": {
                        "filename": "market_serving.duckdb",
                        "tables": ["market_intelligence_overview"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    get_settings.cache_clear()

    locator = ArtifactLocator()
    assert locator.resolve_market_serving_duckdb() == market_path

    get_settings.cache_clear()


def test_artifact_locator_resolves_analytics_snapshot_from_local_manifest(tmp_path: Path, monkeypatch) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    analytics_path = serving_dir / "analytics_serving.duckdb"
    analytics_path.write_bytes(b"analytics-placeholder")
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "serving_release": "test-serving",
                "contract_version": "1",
                "snapshots": {
                    "analytics": {
                        "filename": "analytics_serving.duckdb",
                        "tables": ["family_status_history"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    get_settings.cache_clear()

    locator = ArtifactLocator()
    assert locator.resolve_analytics_serving_duckdb() == analytics_path

    get_settings.cache_clear()


def test_artifact_locator_resolves_publication_snapshot_from_local_manifest(tmp_path: Path, monkeypatch) -> None:
    serving_dir = tmp_path / "serving"
    serving_dir.mkdir(parents=True)
    publication_path = serving_dir / "publication_serving"
    publication_path.mkdir(parents=True)
    manifest_path = serving_dir / "serving_snapshot_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "serving_release": "test-serving",
                "contract_version": "1",
                "snapshots": {
                    "publication": {
                        "filename": "publication_serving",
                        "tables": ["publication_member_by_number"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("PATENTIQ_V2_ARTIFACT_MODE", "local_fs")
    monkeypatch.setenv("PATENTIQ_V2_LOCAL_ARTIFACT_ROOT", str(serving_dir))
    monkeypatch.setenv("PATENTIQ_V2_SERVING_MANIFEST_PATH", str(manifest_path))
    get_settings.cache_clear()

    locator = ArtifactLocator()
    assert locator.resolve_publication_serving_duckdb() == publication_path

    get_settings.cache_clear()

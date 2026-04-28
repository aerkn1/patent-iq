from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import types
import pytest


def _write_text(path: Path, value: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _load_bootstrap_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_runtime_artifacts.py"
    spec = importlib.util.spec_from_file_location("bootstrap_runtime_artifacts", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bootstrap_runtime_artifacts_materializes_local_release_into_mount_safe_layout(tmp_path: Path) -> None:
    release_dir = tmp_path / "release"
    target_root = tmp_path / "runtime"
    manifest_path = release_dir / "release-manifest.json"
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "bootstrap_runtime_artifacts.py"

    _write_text(release_dir / "serving" / "core_serving.duckdb", "core")
    _write_text(release_dir / "models" / "training_snapshot_manifest.json", '{"training_snapshot_id":"ml-123"}')

    manifest = {
        "release_id": "demo-release",
        "runtime_profiles": {
            "default": {
                "items": [
                    {"path": "serving/core_serving.duckdb", "type": "file"},
                    {"path": "models", "type": "directory"},
                ]
            }
        },
        "vector_manifest": {"model_ids": {"abstract": "a", "claims": "b"}},
    }
    _write_text(manifest_path, json.dumps(manifest))

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--source-mode",
            "local_release",
            "--release-manifest-path",
            str(manifest_path),
            "--target-root",
            str(target_root),
            "--profile",
            "default",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert (target_root / "releases/demo-release/serving/core_serving.duckdb").exists()
    assert (target_root / "releases/demo-release/ml/training_snapshot_manifest.json").exists()
    assert (target_root / "current").is_symlink()
    assert (target_root / "current").resolve() == (target_root / "releases/demo-release").resolve()
    assert "Materializing item" in result.stderr


def test_prefetch_hf_models_downloads_declared_dependencies_into_shared_cache(tmp_path: Path, monkeypatch) -> None:
    module = _load_bootstrap_module()
    hf_home = tmp_path / "hf-home"
    logger = module._configure_logger(None)
    download_calls: list[dict[str, object]] = []

    def fake_snapshot_download(
        *,
        repo_id: str,
        revision: str | None,
        cache_dir: str,
        local_dir: str,
        local_dir_use_symlinks: bool,
        token: str | None,
    ) -> str:
        download_calls.append(
            {
                "repo_id": repo_id,
                "revision": revision,
                "cache_dir": cache_dir,
                "local_dir": local_dir,
                "local_dir_use_symlinks": local_dir_use_symlinks,
                "token": token,
            }
        )
        snapshot_dir = Path(local_dir)
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        (snapshot_dir / "config.json").write_text("{}", encoding="utf-8")
        return str(snapshot_dir)

    monkeypatch.setitem(sys.modules, "huggingface_hub", types.SimpleNamespace(snapshot_download=fake_snapshot_download))
    monkeypatch.setenv("HF_TOKEN", "secret-token")

    module._prefetch_hf_models(
        {
            "semantic_model_dependencies": {
                "abstract": {
                    "repo_id": "BAAI/bge-m3",
                    "revision": "rev-123",
                },
                "claims": {
                    "repo_id": "AI-Growth-Lab/PatentSBERTa",
                    "revision": "rev-456",
                },
            }
        },
        hf_home=hf_home,
        allow_unpinned=False,
        token_env="HF_TOKEN",
        logger=logger,
    )

    assert len(download_calls) == 2
    assert download_calls[0]["cache_dir"] == str(hf_home / "hub")
    assert download_calls[0]["local_dir"] == str(hf_home / "models" / "BAAI--bge-m3")
    assert download_calls[0]["local_dir_use_symlinks"] is False
    assert download_calls[0]["token"] == "secret-token"
    assert (hf_home / "models" / "BAAI--bge-m3" / "config.json").exists()
    assert (hf_home / "models" / "AI-Growth-Lab--PatentSBERTa" / "config.json").exists()


def test_download_blob_to_path_rejects_size_mismatch(tmp_path: Path, monkeypatch) -> None:
    module = _load_bootstrap_module()
    logger = module._configure_logger(None)
    target_path = tmp_path / "artifact.bin"

    class FakeDownload:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def readall(self) -> bytes:
            return self._payload

    class FakeBlobClient:
        def get_blob_properties(self):
            return types.SimpleNamespace(size=4)

        def download_blob(self, *, offset: int, length: int, max_concurrency: int):
            assert offset == 0
            assert length == 4
            assert max_concurrency == 1
            return FakeDownload(b"abcde")

    class FakeContainer:
        def get_blob_client(self, blob_name: str):
            assert blob_name == "artifact.bin"
            return FakeBlobClient()

    monkeypatch.setenv("PATENTIQ_BOOTSTRAP_BLOB_CHUNK_SIZE_MB", "1")

    with pytest.raises(RuntimeError, match="Downloaded blob size mismatch"):
        module._download_blob_to_path(FakeContainer(), "artifact.bin", target_path, logger)

    assert not target_path.exists()
    assert not (tmp_path / ".artifact.bin.partial").exists()

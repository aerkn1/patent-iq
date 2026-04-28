from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from patentiq_etl.common.types import BuildSettings


def load_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def runtime_profiles() -> dict[str, Any]:
    default_items = [
        {"path": "serving/core_serving.duckdb", "type": "file"},
        {"path": "serving/market_serving.duckdb", "type": "file"},
        {"path": "serving/semantic_serving.duckdb", "type": "file"},
        {"path": "serving/publication_serving", "type": "directory"},
        {"path": "serving/serving_snapshot_manifest.json", "type": "file"},
        {"path": "serving/serving_snapshot_audit.json", "type": "file"},
        {"path": "vectors/vec_embedding_manifest.json", "type": "file"},
        {"path": "vectors/vec_family_embeddings_abstracts.parquet", "type": "file"},
        {"path": "vectors/vec_family_embeddings_claims.parquet", "type": "file"},
        {"path": "vectors/vec_query_registry.parquet", "type": "file"},
        {"path": "models", "type": "directory"},
    ]
    full_items = [
        *default_items,
        {"path": "serving/analytics_serving.duckdb", "type": "file"},
        {"path": "vectors/vec_ann_index_manifest.json", "type": "file"},
        {"path": "vectors/vec_ann_exact_vs_ann_audit.json", "type": "file"},
        {"path": "vectors/ann", "type": "directory"},
    ]
    return {
        "default": {
            "description": (
                "Base local/remote runtime profile with serving snapshots, vector payloads, and the full ML directory. "
                "Analytics serving stays excluded to keep local bootstrap lighter."
            ),
            "items": default_items,
        },
        "full": {
            "description": (
                "Full parity runtime profile including analytics serving and ANN payloads for every endpoint family."
            ),
            "items": full_items,
        },
    }


def semantic_model_dependencies(vector_manifest: dict[str, Any]) -> dict[str, Any]:
    dependencies: dict[str, Any] = {}
    model_specs = {
        "abstract": {
            "repo_id": vector_manifest.get("abstract_model_id"),
            "revision": vector_manifest.get("abstract_model_revision"),
            "version_hint": vector_manifest.get("abstract_model_version"),
        },
        "claims": {
            "repo_id": vector_manifest.get("claim_model_id"),
            "revision": vector_manifest.get("claim_model_revision"),
            "version_hint": vector_manifest.get("claim_model_version"),
        },
    }
    for space, spec in model_specs.items():
        repo_id = str(spec.get("repo_id") or "").strip()
        if not repo_id:
            continue
        revision = str(spec.get("revision") or "").strip() or None
        version_hint = str(spec.get("version_hint") or "").strip() or None
        dependencies[space] = {
            "provider": "huggingface",
            "repo_id": repo_id,
            "revision": revision,
            "version_hint": version_hint,
            "cache_scope": "hf_hub",
            "packaged_in_release": False,
            "bootstrap_required": True,
            "required_for_profiles": ["default", "full"],
        }
    return dependencies


def build_release_manifest(
    settings: BuildSettings,
    *,
    release_dir: Path,
    release_root_prefix: str,
    copied_artifacts: dict[str, dict[str, Any]],
    built_at: str,
    serving_dir: Path | None = None,
    vectors_dir: Path | None = None,
    models_dir: Path | None = None,
) -> dict[str, Any]:
    resolved_serving_dir = serving_dir or (release_dir / "serving")
    resolved_vectors_dir = vectors_dir or (release_dir / "vectors")
    resolved_models_dir = models_dir or (release_dir / "models")

    serving_manifest = load_json_if_exists(resolved_serving_dir / "serving_snapshot_manifest.json")
    vector_manifest = load_json_if_exists(resolved_vectors_dir / "vec_embedding_manifest.json")
    ann_manifest = load_json_if_exists(resolved_vectors_dir / "vec_ann_index_manifest.json")
    training_manifest = load_json_if_exists(resolved_models_dir / "training_snapshot_manifest.json")
    hf_dependencies = semantic_model_dependencies(vector_manifest)

    return {
        "release_id": settings.release_id,
        "built_at": built_at,
        "snapshot_date": settings.snapshot_date,
        "scope_type": settings.scope_type,
        "selected_wipo_fields": settings.selected_wipo_fields,
        "artifact_root": release_root_prefix,
        "artifacts": copied_artifacts,
        "serving_release": serving_manifest.get("serving_release"),
        "serving_snapshots": serving_manifest.get("snapshots", {}),
        "vector_release": vector_manifest.get("release_id"),
        "vector_manifest": {
            "path": f"{release_root_prefix}/vectors/vec_embedding_manifest.json",
            "model_ids": {
                "abstract": vector_manifest.get("abstract_model_id"),
                "claims": vector_manifest.get("claim_model_id"),
            },
        },
        "semantic_model_dependencies": hf_dependencies,
        "ann_manifest": {
            "path": f"{release_root_prefix}/vectors/vec_ann_index_manifest.json",
            "method": ann_manifest.get("ann_method"),
        },
        "training_snapshot_id": training_manifest.get("training_snapshot_id"),
        "training_snapshot_manifest": f"{release_root_prefix}/models/training_snapshot_manifest.json",
        "runtime_profiles": runtime_profiles(),
    }

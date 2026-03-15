from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from azure.storage.blob import BlobServiceClient

from patentiq_etl.common.io import write_text_json
from patentiq_etl.common.types import BuildSettings, StageResult


def publish_release(settings: BuildSettings) -> list[StageResult]:
    """Assemble a release directory and optionally upload it to the Azure artifact store."""
    result = StageResult(
        stage="publish",
        status="success",
        summary="Prepared release manifests and published the local release to the configured artifact target.",
        methods=[
            "Packaged the release into a deterministic directory structure before any optional Azure upload.",
            "Updated active manifest pointers only after release metadata had been written.",
        ],
        calculations=[
            "The publish target is one authoritative artifact store for application and Data Room consumption.",
        ],
        doc_refs=[
            "docs/next-phase-v2/21-patentiq-v2-azure-runtime-and-storage-architecture.md",
            "docs/next-phase-v2/20-patentiq-v2-data-room-architecture-and-contract.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
        ],
    )

    release_dir = settings.releases_dir / settings.release_id
    release_dir.mkdir(parents=True, exist_ok=True)
    result.outputs.append(str(release_dir))

    for folder_name, source_dir in [
        ("bronze", settings.bronze_dir),
        ("silver", settings.silver_dir),
        ("gold", settings.gold_dir),
        ("models", settings.ml_dir),
        ("vectors", settings.vectors_dir),
    ]:
        target_dir = release_dir / folder_name
        target_dir.mkdir(parents=True, exist_ok=True)
        for artifact in source_dir.glob("*"):
            if artifact.is_file():
                shutil.copy2(artifact, target_dir / artifact.name)

    release_manifest = {
        "release_id": settings.release_id,
        "snapshot_date": settings.snapshot_date,
        "scope_type": settings.scope_type,
        "selected_wipo_fields": settings.selected_wipo_fields,
    }
    manifest_path = release_dir / "manifest.json"
    write_text_json(manifest_path, release_manifest)
    result.outputs.append(str(manifest_path))

    active_release_path = settings.repo_root / "etl" / "manifests" / "releases" / "active_release.json"
    write_text_json(active_release_path, {"release_id": settings.release_id, "manifest_path": str(manifest_path)})
    result.outputs.append(str(active_release_path))

    if settings.azure_publish_enabled:
        connection_string = os.environ.get(settings.azure["connection_string_env"])
        if not connection_string:
            result.status = "degraded"
            result.warnings.append("Azure publish was enabled but no connection string environment variable was present.")
            return [result]
        blob_service = BlobServiceClient.from_connection_string(connection_string)
        container = blob_service.get_container_client(settings.azure["container"])
        for file_path in release_dir.rglob("*"):
            if not file_path.is_file():
                continue
            blob_name = f"releases/{settings.release_id}/{file_path.relative_to(release_dir).as_posix()}"
            with file_path.open("rb") as handle:
                container.upload_blob(blob_name, handle, overwrite=True)
        result.outputs.append(f"azure://{settings.azure['container']}/releases/{settings.release_id}")
    else:
        result.warnings.append("Azure publish is disabled in build config. Release was staged locally only.")

    return [result]

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from patentiq_etl.common.io import append_jsonl, ensure_dir, write_text_json
from patentiq_etl.common.logging_utils import configure_logger
from patentiq_etl.common.types import BuildSettings, StageResult, utc_now_iso
from patentiq_etl.publish.runtime_contract import build_release_manifest


def _stage_log_path(settings: BuildSettings) -> Path:
    return settings.manifests_dir / "stages" / "publish.log"


def _stage_event_path(settings: BuildSettings) -> Path:
    return settings.manifests_dir / "stages" / "publish.events.jsonl"


def _emit_event(settings: BuildSettings, event_name: str, **payload: Any) -> None:
    append_jsonl(
        _stage_event_path(settings),
        {
            "event": event_name,
            "timestamp": utc_now_iso(),
            **payload,
        },
    )


def _release_sources(settings: BuildSettings) -> list[tuple[str, Path]]:
    return [
        ("bronze", settings.bronze_dir),
        ("silver", settings.silver_dir),
        ("gold", settings.gold_dir),
        ("models", settings.ml_dir),
        ("vectors", settings.vectors_dir),
        ("serving", settings.repo_root / "etl" / "data" / "serving"),
    ]


def _count_tree(root: Path) -> tuple[int, int]:
    file_count = 0
    total_bytes = 0
    if not root.exists():
        return file_count, total_bytes
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        file_count += 1
        total_bytes += path.stat().st_size
    return file_count, total_bytes


def _copy_tree(source_dir: Path, target_dir: Path) -> tuple[int, int]:
    ensure_dir(target_dir)
    copied_files = 0
    copied_bytes = 0
    for source_path in sorted(source_dir.rglob("*")):
        relative_path = source_path.relative_to(source_dir)
        target_path = target_dir / relative_path
        if source_path.is_dir():
            ensure_dir(target_path)
            continue
        ensure_dir(target_path.parent)
        shutil.copy2(source_path, target_path)
        copied_files += 1
        copied_bytes += source_path.stat().st_size
    return copied_files, copied_bytes


def _release_manifest(
    settings: BuildSettings,
    *,
    release_dir: Path,
    release_root_prefix: str,
    copied_artifacts: dict[str, dict[str, Any]],
    built_at: str,
) -> dict[str, Any]:
    return build_release_manifest(
        settings,
        release_dir=release_dir,
        release_root_prefix=release_root_prefix,
        copied_artifacts=copied_artifacts,
        built_at=built_at,
    )


def _stage_release_locally(
    settings: BuildSettings,
    result: StageResult,
    *,
    stage_logger,
    built_at: str,
) -> tuple[Path, Path, dict[str, dict[str, Any]]]:
    release_dir = settings.releases_dir / settings.release_id
    temp_release_dir = settings.releases_dir / f".{settings.release_id}.tmp"

    _emit_event(
        settings,
        "local_stage_started",
        release_dir=str(release_dir),
        overwrite_enabled=settings.release_overwrite_enabled,
    )
    stage_logger.info(
        "Staging release locally release_id=%s release_dir=%s overwrite_enabled=%s",
        settings.release_id,
        release_dir,
        settings.release_overwrite_enabled,
    )

    if release_dir.exists() and any(release_dir.iterdir()) and not settings.release_overwrite_enabled:
        raise RuntimeError(
            f"Local release directory already exists and overwrite is disabled: {release_dir}"
        )

    if temp_release_dir.exists():
        stage_logger.warning("Removing leftover temporary release directory path=%s", temp_release_dir)
        shutil.rmtree(temp_release_dir)

    ensure_dir(temp_release_dir)
    copied_artifacts: dict[str, dict[str, Any]] = {}
    release_root_prefix = f"releases/{settings.release_id}"

    for folder_name, source_dir in _release_sources(settings):
        target_dir = temp_release_dir / folder_name
        if not source_dir.exists():
            stage_logger.warning("Skipping missing release source folder=%s source_dir=%s", folder_name, source_dir)
            result.warnings.append(f"Release source directory missing for `{folder_name}`: {source_dir}")
            _emit_event(settings, "release_source_missing", folder=folder_name, source_dir=str(source_dir))
            continue
        stage_logger.info("Copying release source folder=%s source_dir=%s target_dir=%s", folder_name, source_dir, target_dir)
        _emit_event(
            settings,
            "release_source_copy_started",
            folder=folder_name,
            source_dir=str(source_dir),
            target_dir=str(target_dir),
        )
        copied_files, copied_bytes = _copy_tree(source_dir, target_dir)
        copied_artifacts[folder_name] = {
            "blob_prefix": f"{release_root_prefix}/{folder_name}",
            "local_path": str(target_dir),
            "file_count": copied_files,
            "bytes": copied_bytes,
        }
        stage_logger.info(
            "Copied release source folder=%s file_count=%s bytes=%s",
            folder_name,
            copied_files,
            copied_bytes,
        )
        _emit_event(
            settings,
            "release_source_copy_finished",
            folder=folder_name,
            file_count=copied_files,
            bytes=copied_bytes,
        )

    release_manifest = _release_manifest(
        settings,
        release_dir=temp_release_dir,
        release_root_prefix=release_root_prefix,
        copied_artifacts=copied_artifacts,
        built_at=built_at,
    )
    release_manifest_path = temp_release_dir / "release-manifest.json"
    write_text_json(release_manifest_path, release_manifest)
    write_text_json(
        temp_release_dir / "manifest.json",
        {
            "release_id": settings.release_id,
            "release_manifest_path": str(release_manifest_path),
            "snapshot_date": settings.snapshot_date,
            "scope_type": settings.scope_type,
            "selected_wipo_fields": settings.selected_wipo_fields,
        },
    )

    if release_dir.exists() and settings.release_overwrite_enabled:
        stage_logger.warning("Removing existing local release directory before promote path=%s", release_dir)
        shutil.rmtree(release_dir)

    temp_release_dir.rename(release_dir)
    _emit_event(settings, "local_stage_finished", release_dir=str(release_dir))
    stage_logger.info("Promoted staged release into place release_dir=%s", release_dir)
    result.outputs.append(str(release_dir))
    result.outputs.append(str(release_dir / "release-manifest.json"))
    return release_dir, release_dir / "release-manifest.json", copied_artifacts


def _write_active_release_pointer(
    settings: BuildSettings,
    *,
    release_manifest_path: Path,
    release_root_prefix: str,
    built_at: str,
) -> Path:
    active_release_path = settings.repo_root / "etl" / "manifests" / "releases" / "active_release.json"
    write_text_json(
        active_release_path,
        {
            "release_id": settings.release_id,
            "built_at": built_at,
            "artifact_root": release_root_prefix,
            "release_manifest_path": str(release_manifest_path),
            "release_manifest_blob": f"{release_root_prefix}/release-manifest.json",
        },
    )
    return active_release_path


def _upload_release_to_azure(
    settings: BuildSettings,
    result: StageResult,
    *,
    release_dir: Path,
    release_manifest_path: Path,
    stage_logger,
    built_at: str,
) -> None:
    from azure.storage.blob import BlobServiceClient

    connection_string = os.environ.get(settings.azure["connection_string_env"])
    if not connection_string:
        raise RuntimeError(
            f"Azure publish is enabled but environment variable `{settings.azure['connection_string_env']}` is not set."
        )

    blob_service = BlobServiceClient.from_connection_string(connection_string)
    container = blob_service.get_container_client(settings.azure["container"])
    release_root_prefix = f"releases/{settings.release_id}"

    if not settings.azure_release_overwrite_enabled:
        existing = next(iter(container.list_blobs(name_starts_with=f"{release_root_prefix}/")), None)
        if existing is not None:
            raise RuntimeError(
                f"Azure release prefix already exists and overwrite is disabled: azure://{settings.azure['container']}/{release_root_prefix}"
            )

    _emit_event(
        settings,
        "azure_upload_started",
        container=settings.azure["container"],
        prefix=release_root_prefix,
        overwrite_enabled=settings.azure_release_overwrite_enabled,
    )
    stage_logger.info(
        "Uploading staged release to Azure container=%s prefix=%s overwrite_enabled=%s",
        settings.azure["container"],
        release_root_prefix,
        settings.azure_release_overwrite_enabled,
    )

    uploaded_files = 0
    uploaded_bytes = 0
    for file_path in sorted(release_dir.rglob("*")):
        if not file_path.is_file():
            continue
        blob_name = f"{release_root_prefix}/{file_path.relative_to(release_dir).as_posix()}"
        with file_path.open("rb") as handle:
            container.upload_blob(blob_name, handle, overwrite=settings.azure_release_overwrite_enabled)
        uploaded_files += 1
        uploaded_bytes += file_path.stat().st_size
        stage_logger.info("Uploaded blob blob_name=%s size_bytes=%s", blob_name, file_path.stat().st_size)

    active_release_payload = {
        "release_id": settings.release_id,
        "built_at": built_at,
        "artifact_root": release_root_prefix,
        "release_manifest_blob": f"{release_root_prefix}/release-manifest.json",
    }
    active_blob_name = settings.azure.get("active_release_manifest_blob", "manifests/active_release.json")
    container.upload_blob(
        active_blob_name,
        json.dumps(active_release_payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8"),
        overwrite=True,
    )

    result.outputs.append(f"azure://{settings.azure['container']}/{release_root_prefix}")
    result.outputs.append(f"azure://{settings.azure['container']}/{active_blob_name}")
    result.metrics["azure_uploaded_file_count"] = uploaded_files
    result.metrics["azure_uploaded_bytes"] = uploaded_bytes
    _emit_event(
        settings,
        "azure_upload_finished",
        container=settings.azure["container"],
        prefix=release_root_prefix,
        uploaded_file_count=uploaded_files,
        uploaded_bytes=uploaded_bytes,
        active_release_blob=active_blob_name,
    )
    stage_logger.info(
        "Azure upload finished uploaded_file_count=%s uploaded_bytes=%s active_release_blob=%s release_manifest_path=%s",
        uploaded_files,
        uploaded_bytes,
        active_blob_name,
        release_manifest_path,
    )


def publish_release(settings: BuildSettings) -> list[StageResult]:
    """Assemble a release directory and optionally upload it to the Azure artifact store."""
    stage_logger = configure_logger("publish", _stage_log_path(settings))
    built_at = utc_now_iso()
    result = StageResult(
        stage="publish",
        status="success",
        summary="Prepared a logged, manifest-driven release directory and optionally published it to Azure Blob.",
        methods=[
            "Stages the release into a temporary directory before promoting it into place locally.",
            "Refuses to overwrite an existing local or remote release unless overwrite flags are explicitly enabled.",
            "Publishes a richer release-manifest that pins serving, vector, ANN, and ML artifact paths together.",
            "Writes structured stage events so local and CI operators can trace copy and upload progress in detail.",
        ],
        calculations=[
            "The release payload is rooted at releases/<release_id> and keeps serving, vectors, and models under stable prefixes.",
            "Default and full runtime profiles are serialized into the release-manifest so bootstrap tooling can hydrate only what is needed.",
        ],
        doc_refs=[
            "docs/next-phase-v2/21-patentiq-v2-azure-runtime-and-storage-architecture.md",
            "docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md",
            "docs/next-phase-v2/36-patentiq-v2-azure-deployment-and-release-blueprint.md",
            "docs/next-phase-v2/41-patentiq-v2-etl-serving-snapshots-packaging-contract.md",
        ],
    )

    stage_logger.info(
        "Publish stage started release_id=%s local_overwrite_enabled=%s azure_publish_enabled=%s azure_overwrite_enabled=%s",
        settings.release_id,
        settings.release_overwrite_enabled,
        settings.azure_publish_enabled,
        settings.azure_release_overwrite_enabled,
    )
    _emit_event(
        settings,
        "stage_started",
        release_id=settings.release_id,
        azure_publish_enabled=settings.azure_publish_enabled,
    )

    try:
        release_dir, release_manifest_path, copied_artifacts = _stage_release_locally(
            settings,
            result,
            stage_logger=stage_logger,
            built_at=built_at,
        )
        release_root_prefix = f"releases/{settings.release_id}"
        active_release_path = _write_active_release_pointer(
            settings,
            release_manifest_path=release_manifest_path,
            release_root_prefix=release_root_prefix,
            built_at=built_at,
        )
        result.outputs.append(str(active_release_path))

        local_files, local_bytes = _count_tree(release_dir)
        result.metrics["local_release_file_count"] = local_files
        result.metrics["local_release_bytes"] = local_bytes
        result.artifacts["copied_artifacts"] = copied_artifacts

        if settings.azure_publish_enabled:
            _upload_release_to_azure(
                settings,
                result,
                release_dir=release_dir,
                release_manifest_path=release_manifest_path,
                stage_logger=stage_logger,
                built_at=built_at,
            )
        else:
            result.warnings.append("Azure publish is disabled in build config. Release was staged locally only.")
            stage_logger.info("Azure publish disabled; release staged locally only.")

        stage_logger.info(
            "Publish stage finished release_dir=%s local_release_file_count=%s local_release_bytes=%s",
            release_dir,
            local_files,
            local_bytes,
        )
        _emit_event(
            settings,
            "stage_finished",
            status=result.status,
            release_dir=str(release_dir),
            local_release_file_count=local_files,
            local_release_bytes=local_bytes,
        )
    except Exception as exc:
        result.status = "failure"
        result.warnings.append(str(exc))
        stage_logger.exception("Publish stage failed release_id=%s", settings.release_id)
        _emit_event(settings, "stage_failed", error=str(exc))
        raise

    return [result.finish()]

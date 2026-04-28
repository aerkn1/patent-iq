#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import errno
import json
import logging
import os
import shutil
from pathlib import Path
import time
from typing import Any


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize one published PatentIQ release into a runtime-ready filesystem layout for local Docker "
            "or Azure Container Apps mounts."
        )
    )
    parser.add_argument("--source-mode", choices=("local_release", "azure_blob"), required=True)
    parser.add_argument("--target-root", required=True, help="Root directory that will hold releases/ and current/.")
    parser.add_argument("--profile", choices=("default", "full"), default="default")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing target release directory.")
    parser.add_argument("--log-path", help="Optional file path for bootstrap logs.")
    parser.add_argument("--prefetch-hf-models", action="store_true", help="Download required Hugging Face model snapshots into a shared cache.")
    parser.add_argument("--allow-unpinned-hf-models", action="store_true", help="Allow downloading Hugging Face models when the release-manifest does not pin a revision.")
    parser.add_argument("--hf-home", help="Root path for the Hugging Face cache. Defaults to <target-root>/hf-home.")
    parser.add_argument(
        "--hf-token-env",
        default="HF_TOKEN",
        help="Environment variable carrying an optional Hugging Face token for gated models.",
    )

    parser.add_argument("--release-manifest-path", help="Local release-manifest.json path for local_release mode.")
    parser.add_argument("--active-release-path", help="Local active_release.json path for local_release mode.")

    parser.add_argument("--account-url", help="Azure Blob account URL for azure_blob mode.")
    parser.add_argument("--container", help="Azure Blob container name for azure_blob mode.")
    parser.add_argument("--active-release-blob", help="Blob path to active_release.json.")
    parser.add_argument("--release-manifest-blob", help="Blob path to release-manifest.json.")
    parser.add_argument(
        "--connection-string-env",
        default="AZURE_STORAGE_CONNECTION_STRING",
        help="Environment variable carrying an Azure Storage connection string.",
    )
    return parser.parse_args()


def _configure_logger(log_path: str | None) -> logging.Logger:
    logger = logging.getLogger("patentiq_runtime_bootstrap")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if log_path:
        file_path = Path(log_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default


def _copy_file(source: Path, target: Path, logger: logging.Logger) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    size_bytes = source.stat().st_size
    logger.info("Copied file source=%s target=%s size_bytes=%s", source, target, size_bytes)
    return size_bytes


def _copy_directory(source: Path, target: Path, logger: logging.Logger) -> tuple[int, int]:
    file_count = 0
    total_bytes = 0
    for source_path in sorted(source.rglob("*")):
        relative_path = source_path.relative_to(source)
        target_path = target / relative_path
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        total_bytes += _copy_file(source_path, target_path, logger)
        file_count += 1
    return file_count, total_bytes


def _count_directory(root: Path) -> tuple[int, int]:
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


def _runtime_relative_path(release_relative_path: str) -> Path:
    release_path = Path(release_relative_path)
    if release_path.parts and release_path.parts[0] == "models":
        return Path("ml", *release_path.parts[1:])
    return release_path


def _required_items(manifest: dict[str, Any], profile: str) -> list[dict[str, Any]]:
    runtime_profiles = manifest.get("runtime_profiles", {})
    selected = runtime_profiles.get(profile)
    if not isinstance(selected, dict):
        raise RuntimeError(f"Profile `{profile}` was not found in release-manifest.")
    items = selected.get("items")
    if not isinstance(items, list) or not items:
        raise RuntimeError(f"Profile `{profile}` in release-manifest does not define any materialization items.")
    return items


def _semantic_model_dependencies(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    payload = manifest.get("semantic_model_dependencies")
    if not isinstance(payload, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            normalized[str(key)] = dict(value)
    return normalized


def _prefetched_model_dir(hf_home: Path, repo_id: str) -> Path:
    return hf_home / "models" / repo_id.replace("/", "--")


def _prefetch_hf_models(
    manifest: dict[str, Any],
    *,
    hf_home: Path,
    allow_unpinned: bool,
    token_env: str,
    logger: logging.Logger,
) -> None:
    dependencies = _semantic_model_dependencies(manifest)
    if not dependencies:
        logger.info("Release-manifest declares no semantic Hugging Face model dependencies.")
        return

    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError(
            "Hugging Face model prefetch was requested but `huggingface_hub` is not installed in the bootstrap environment."
        ) from exc

    hub_cache = hf_home / "hub"
    model_root = hf_home / "models"
    hub_cache.mkdir(parents=True, exist_ok=True)
    model_root.mkdir(parents=True, exist_ok=True)
    token = os.environ.get(token_env)
    logger.info(
        "Prefetching Hugging Face models dependency_count=%s hf_home=%s hub_cache=%s model_root=%s token_env_present=%s",
        len(dependencies),
        hf_home,
        hub_cache,
        model_root,
        bool(token),
    )

    for dependency_name, dependency in sorted(dependencies.items()):
        repo_id = str(dependency.get("repo_id") or "").strip()
        if not repo_id:
            logger.warning("Skipping malformed semantic model dependency name=%s reason=missing_repo_id", dependency_name)
            continue
        revision = str(dependency.get("revision") or "").strip() or None
        if revision is None and not allow_unpinned:
            raise RuntimeError(
                f"Semantic model dependency `{dependency_name}` is unpinned and --allow-unpinned-hf-models was not set."
            )
        if revision is None:
            logger.warning(
                "Semantic model dependency is not pinned to a Hugging Face revision name=%s repo_id=%s version_hint=%s",
                dependency_name,
                repo_id,
                dependency.get("version_hint"),
            )

        logger.info(
            "Starting Hugging Face snapshot download name=%s repo_id=%s revision=%s local_dir=%s cache_dir=%s",
            dependency_name,
            repo_id,
            revision or "<default>",
            _prefetched_model_dir(hf_home, repo_id),
            hub_cache,
        )
        local_model_dir = _prefetched_model_dir(hf_home, repo_id)
        snapshot_path = Path(
            snapshot_download(
                repo_id=repo_id,
                revision=revision,
                cache_dir=str(hub_cache),
                local_dir=str(local_model_dir),
                local_dir_use_symlinks=False,
                token=token,
            )
        )
        file_count, total_bytes = _count_directory(snapshot_path)
        logger.info(
            "Finished Hugging Face snapshot download name=%s repo_id=%s revision=%s snapshot_path=%s file_count=%s bytes=%s",
            dependency_name,
            repo_id,
            revision or "<default>",
            snapshot_path,
            file_count,
            total_bytes,
        )


def _get_container_client(args: argparse.Namespace):
    from azure.storage.blob import BlobServiceClient

    connection_string = os.environ.get(args.connection_string_env)
    if connection_string:
        service = BlobServiceClient.from_connection_string(connection_string)
        return service.get_container_client(args.container)
    if not args.account_url:
        raise RuntimeError(
            f"Azure bootstrap requires either `{args.connection_string_env}` or --account-url with managed identity credentials."
        )
    from azure.identity import DefaultAzureCredential

    credential = DefaultAzureCredential()
    service = BlobServiceClient(account_url=args.account_url, credential=credential)
    return service.get_container_client(args.container)


def _download_blob_json(container, blob_name: str) -> dict[str, Any]:
    payload = container.download_blob(blob_name).readall()
    return json.loads(payload.decode("utf-8"))


def _resolve_azure_manifest(args: argparse.Namespace, logger: logging.Logger) -> tuple[dict[str, Any], str]:
    if not args.container:
        raise RuntimeError("Azure bootstrap requires --container.")
    container = _get_container_client(args)

    manifest_blob = args.release_manifest_blob
    if not manifest_blob:
        if not args.active_release_blob:
            raise RuntimeError("Azure bootstrap requires either --release-manifest-blob or --active-release-blob.")
        logger.info("Downloading active release pointer blob=%s", args.active_release_blob)
        active_payload = _download_blob_json(container, args.active_release_blob)
        manifest_blob = str(active_payload.get("release_manifest_blob") or "").strip()
        if not manifest_blob:
            release_id = str(active_payload.get("release_id") or "").strip()
            if not release_id:
                raise RuntimeError("Active release pointer is missing both `release_manifest_blob` and `release_id`.")
            manifest_blob = f"releases/{release_id}/release-manifest.json"

    logger.info("Downloading release manifest blob=%s", manifest_blob)
    manifest = _download_blob_json(container, manifest_blob)
    return manifest, manifest_blob


def _resolve_local_manifest(args: argparse.Namespace, logger: logging.Logger) -> tuple[dict[str, Any], Path]:
    manifest_path: Path | None = None
    if args.release_manifest_path:
        manifest_path = Path(args.release_manifest_path).resolve()
    elif args.active_release_path:
        active_release_path = Path(args.active_release_path).resolve()
        if not active_release_path.exists():
            raise RuntimeError(f"Active release path does not exist: {active_release_path}")
        logger.info("Loading local active release pointer path=%s", active_release_path)
        active_release = _read_json(active_release_path)
        release_manifest_path = str(active_release.get("release_manifest_path") or "").strip()
        if release_manifest_path:
            manifest_path = Path(release_manifest_path).resolve()
        else:
            release_id = str(active_release.get("release_id") or "").strip()
            if not release_id:
                raise RuntimeError("Active release pointer is missing both `release_manifest_path` and `release_id`.")
            manifest_path = active_release_path.parents[2] / "data" / "releases" / release_id / "release-manifest.json"
    if manifest_path is None:
        raise RuntimeError("Local release bootstrap requires --release-manifest-path or --active-release-path.")
    if not manifest_path.exists():
        raise RuntimeError(f"Release manifest path does not exist: {manifest_path}")
    logger.info("Loading local release manifest path=%s", manifest_path)
    return _read_json(manifest_path), manifest_path


def _ensure_existing_release_compatible(
    final_release_dir: Path,
    release_id: str,
    profile: str,
    logger: logging.Logger,
) -> bool:
    state_path = final_release_dir / ".bootstrap-state.json"
    if not state_path.exists():
        return False
    try:
        payload = _read_json(state_path)
    except Exception:
        return False
    if payload.get("release_id") != release_id or payload.get("profile") != profile:
        return False
    logger.info(
        "Existing runtime release is already materialized release_id=%s profile=%s release_dir=%s",
        release_id,
        profile,
        final_release_dir,
    )
    return True


def _promote_current_symlink(target_root: Path, final_release_dir: Path, logger: logging.Logger) -> None:
    current_link = target_root / "current"
    temp_link = target_root / ".current.tmp"
    marker_path = target_root / ".current-release.json"
    if temp_link.is_symlink() or temp_link.is_file():
        temp_link.unlink()
    elif temp_link.exists():
        shutil.rmtree(temp_link)
    if current_link.is_symlink() or current_link.is_file():
        current_link.unlink()
    elif current_link.exists():
        shutil.rmtree(current_link)
    try:
        temp_link.symlink_to(final_release_dir, target_is_directory=True)
        temp_link.replace(current_link)
        if marker_path.exists():
            marker_path.unlink()
        logger.info("Updated current runtime symlink current=%s target=%s", current_link, final_release_dir)
    except OSError as exc:
        if exc.errno not in {errno.EOPNOTSUPP, errno.ENOTSUP, errno.EPERM, errno.EACCES, 95}:
            raise
        _write_json(
            marker_path,
            {
                "release_path": str(final_release_dir),
                "release_id": final_release_dir.name,
                "updated_at": _utc_now_iso(),
                "reason": "symlink_not_supported",
            },
        )
        logger.warning(
            "Runtime symlink is not supported on this filesystem; wrote release marker instead "
            "current=%s target=%s marker=%s error=%s",
            current_link,
            final_release_dir,
            marker_path,
            exc,
        )


def _stage_local_release(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    target_root: Path,
    profile: str,
    overwrite: bool,
    logger: logging.Logger,
) -> Path:
    release_id = str(manifest.get("release_id") or "").strip()
    if not release_id:
        raise RuntimeError("Release manifest is missing `release_id`.")

    release_root = manifest_path.parent
    items = _required_items(manifest, profile)
    target_root.mkdir(parents=True, exist_ok=True)
    final_release_dir = target_root / "releases" / release_id
    staging_dir = target_root / ".staging" / f"{release_id}-{profile}"

    if final_release_dir.exists() and _ensure_existing_release_compatible(final_release_dir, release_id, profile, logger):
        _promote_current_symlink(target_root, final_release_dir, logger)
        return final_release_dir

    if final_release_dir.exists() and not overwrite:
        raise RuntimeError(f"Target runtime release already exists and overwrite is disabled: {final_release_dir}")

    if staging_dir.exists():
        logger.warning("Removing leftover runtime staging directory path=%s", staging_dir)
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Materializing local release release_id=%s profile=%s target_root=%s", release_id, profile, target_root)
    copied_files = 0
    copied_bytes = 0
    for item in items:
        relative_path = str(item["path"])
        source_path = release_root / relative_path
        dest_path = staging_dir / _runtime_relative_path(relative_path)
        item_type = str(item.get("type") or "file")
        logger.info("Materializing item source=%s dest=%s type=%s", source_path, dest_path, item_type)
        if item_type == "directory":
            if not source_path.exists():
                raise RuntimeError(f"Expected release directory is missing: {source_path}")
            file_count, total_bytes = _copy_directory(source_path, dest_path, logger)
            copied_files += file_count
            copied_bytes += total_bytes
        else:
            if not source_path.exists():
                raise RuntimeError(f"Expected release file is missing: {source_path}")
            copied_bytes += _copy_file(source_path, dest_path, logger)
            copied_files += 1

    _copy_file(manifest_path, staging_dir / "release-manifest.json", logger)
    _write_json(
        staging_dir / ".bootstrap-state.json",
        {
            "release_id": release_id,
            "profile": profile,
            "source_mode": "local_release",
            "materialized_at": _utc_now_iso(),
            "copied_file_count": copied_files,
            "copied_bytes": copied_bytes,
        },
    )

    if final_release_dir.exists():
        logger.warning("Removing previous runtime release path=%s", final_release_dir)
        shutil.rmtree(final_release_dir)
    final_release_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir.rename(final_release_dir)
    _promote_current_symlink(target_root, final_release_dir, logger)
    logger.info(
        "Finished local release materialization release_id=%s profile=%s copied_file_count=%s copied_bytes=%s",
        release_id,
        profile,
        copied_files,
        copied_bytes,
    )
    return final_release_dir


def _download_blob_to_path(container, blob_name: str, target_path: Path, logger: logging.Logger) -> int:
    from azure.core.exceptions import ServiceRequestError, ServiceResponseError, ServiceResponseTimeoutError

    blob_client = container.get_blob_client(blob_name)
    blob_properties = blob_client.get_blob_properties()
    expected_size = int(getattr(blob_properties, "size", 0) or 0)
    chunk_size = max(1, _env_int("PATENTIQ_BOOTSTRAP_BLOB_CHUNK_SIZE_MB", 64)) * 1024 * 1024
    retry_limit = max(1, _env_int("PATENTIQ_BOOTSTRAP_BLOB_RETRY_LIMIT", 5))
    retry_backoff_sec = max(0.1, _env_float("PATENTIQ_BOOTSTRAP_BLOB_RETRY_BACKOFF_SEC", 2.0))
    progress_interval = max(1, _env_int("PATENTIQ_BOOTSTRAP_BLOB_PROGRESS_INTERVAL_MB", 512)) * 1024 * 1024

    target_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = target_path.parent / f".{target_path.name}.partial"

    if target_path.exists() and not partial_path.exists():
        target_size = target_path.stat().st_size
        if expected_size and target_size > expected_size:
            logger.warning(
                "Existing blob target is larger than source; restarting download blob_name=%s target=%s existing_size=%s expected_size=%s",
                blob_name,
                target_path,
                target_size,
                expected_size,
            )
            target_path.unlink()
        elif expected_size and target_size == expected_size:
            logger.info("Blob already downloaded blob_name=%s target=%s size_bytes=%s", blob_name, target_path, expected_size)
            return expected_size
        else:
            logger.warning(
                "Existing blob target is incomplete; resuming via partial file blob_name=%s target=%s existing_size=%s expected_size=%s",
                blob_name,
                target_path,
                target_size,
                expected_size,
            )
            target_path.replace(partial_path)

    existing_size = partial_path.stat().st_size if partial_path.exists() else 0
    if expected_size and existing_size > expected_size:
        logger.warning(
            "Existing blob partial target is larger than source; restarting download blob_name=%s target=%s partial_path=%s existing_size=%s expected_size=%s",
            blob_name,
            target_path,
            partial_path,
            existing_size,
            expected_size,
        )
        partial_path.unlink()
        existing_size = 0

    bytes_written = existing_size
    last_logged = (bytes_written // progress_interval) * progress_interval if progress_interval else 0
    file_mode = "r+b" if partial_path.exists() else "wb"
    with partial_path.open(file_mode) as handle:
        if bytes_written:
            handle.seek(bytes_written)
        while bytes_written < expected_size:
            requested_length = min(chunk_size, expected_size - bytes_written)
            payload: bytes | None = None
            for attempt in range(1, retry_limit + 1):
                try:
                    payload = blob_client.download_blob(
                        offset=bytes_written,
                        length=requested_length,
                        max_concurrency=1,
                    ).readall()
                    break
                except (
                    ServiceResponseTimeoutError,
                    ServiceRequestError,
                    ServiceResponseError,
                    TimeoutError,
                    ConnectionError,
                    OSError,
                ) as exc:
                    if attempt >= retry_limit:
                        raise
                    sleep_seconds = retry_backoff_sec * attempt
                    logger.warning(
                        "Retrying blob chunk blob_name=%s offset=%s length=%s attempt=%s/%s sleep_sec=%.1f error=%s",
                        blob_name,
                        bytes_written,
                        requested_length,
                        attempt,
                        retry_limit,
                        sleep_seconds,
                        exc,
                    )
                    time.sleep(sleep_seconds)

            if payload is None:
                raise RuntimeError(f"Failed to download blob chunk: {blob_name} offset={bytes_written} length={requested_length}")
            if requested_length and not payload:
                raise RuntimeError(f"Downloaded empty blob chunk: {blob_name} offset={bytes_written} length={requested_length}")

            handle.write(payload)
            handle.flush()
            bytes_written += len(payload)

            if bytes_written - last_logged >= progress_interval or bytes_written == expected_size:
                logger.info(
                    "Blob download progress blob_name=%s target=%s bytes_written=%s expected_size=%s",
                    blob_name,
                    target_path,
                    bytes_written,
                    expected_size,
                )
                last_logged = bytes_written

    actual_size = partial_path.stat().st_size
    if expected_size and actual_size != expected_size:
        logger.error(
            "Downloaded blob size mismatch blob_name=%s target=%s partial_path=%s actual_size=%s expected_size=%s; removing corrupt partial",
            blob_name,
            target_path,
            partial_path,
            actual_size,
            expected_size,
        )
        partial_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Downloaded blob size mismatch: {blob_name} actual={actual_size} expected={expected_size} target={target_path}"
        )

    if target_path.exists():
        target_path.unlink()
    partial_path.replace(target_path)

    logger.info("Downloaded blob blob_name=%s target=%s size_bytes=%s", blob_name, target_path, actual_size)
    return actual_size


def _download_prefix(
    container,
    prefix: str,
    target_dir: Path,
    logger: logging.Logger,
) -> tuple[int, int]:
    blobs = list(container.list_blobs(name_starts_with=prefix.rstrip("/") + "/"))
    if not blobs:
        raise RuntimeError(f"Expected blob prefix is empty: {prefix}")
    file_count = 0
    total_bytes = 0
    for blob in blobs:
        suffix = blob.name[len(prefix.rstrip("/") + "/") :]
        if not suffix:
            continue
        total_bytes += _download_blob_to_path(container, blob.name, target_dir / suffix, logger)
        file_count += 1
    return file_count, total_bytes


def _stage_azure_release(
    *,
    manifest: dict[str, Any],
    manifest_blob: str,
    args: argparse.Namespace,
    target_root: Path,
    profile: str,
    overwrite: bool,
    logger: logging.Logger,
) -> Path:
    release_id = str(manifest.get("release_id") or "").strip()
    if not release_id:
        raise RuntimeError("Release manifest is missing `release_id`.")

    container = _get_container_client(args)
    artifact_root = str(manifest.get("artifact_root") or f"releases/{release_id}").strip().rstrip("/")
    items = _required_items(manifest, profile)
    target_root.mkdir(parents=True, exist_ok=True)
    final_release_dir = target_root / "releases" / release_id
    staging_dir = target_root / ".staging" / f"{release_id}-{profile}"

    if final_release_dir.exists() and _ensure_existing_release_compatible(final_release_dir, release_id, profile, logger):
        _promote_current_symlink(target_root, final_release_dir, logger)
        return final_release_dir

    if final_release_dir.exists() and not overwrite:
        raise RuntimeError(f"Target runtime release already exists and overwrite is disabled: {final_release_dir}")

    if staging_dir.exists():
        logger.warning("Reusing existing runtime staging directory path=%s", staging_dir)
    else:
        staging_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Materializing Azure release release_id=%s profile=%s container=%s artifact_root=%s target_root=%s",
        release_id,
        profile,
        args.container,
        artifact_root,
        target_root,
    )

    copied_files = 0
    copied_bytes = 0
    for item in items:
        relative_path = str(item["path"])
        blob_prefix = f"{artifact_root}/{relative_path}".replace("\\", "/")
        dest_path = staging_dir / _runtime_relative_path(relative_path)
        item_type = str(item.get("type") or "file")
        logger.info("Materializing blob item blob_prefix=%s dest=%s type=%s", blob_prefix, dest_path, item_type)
        if item_type == "directory":
            file_count, total_bytes = _download_prefix(container, blob_prefix, dest_path, logger)
            copied_files += file_count
            copied_bytes += total_bytes
        else:
            copied_bytes += _download_blob_to_path(container, blob_prefix, dest_path, logger)
            copied_files += 1

    _download_blob_to_path(container, manifest_blob, staging_dir / "release-manifest.json", logger)
    _write_json(
        staging_dir / ".bootstrap-state.json",
        {
            "release_id": release_id,
            "profile": profile,
            "source_mode": "azure_blob",
            "materialized_at": _utc_now_iso(),
            "copied_file_count": copied_files,
            "copied_bytes": copied_bytes,
            "manifest_blob": manifest_blob,
        },
    )

    if final_release_dir.exists():
        logger.warning("Removing previous runtime release path=%s", final_release_dir)
        shutil.rmtree(final_release_dir)
    final_release_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir.rename(final_release_dir)
    _promote_current_symlink(target_root, final_release_dir, logger)
    logger.info(
        "Finished Azure release materialization release_id=%s profile=%s copied_file_count=%s copied_bytes=%s",
        release_id,
        profile,
        copied_files,
        copied_bytes,
    )
    return final_release_dir


def main() -> int:
    args = _parse_args()
    logger = _configure_logger(args.log_path)
    target_root = Path(args.target_root).resolve()
    hf_home = Path(args.hf_home).resolve() if args.hf_home else (target_root / "hf-home")
    logger.info(
        "Bootstrap started source_mode=%s profile=%s target_root=%s overwrite=%s hf_home=%s prefetch_hf_models=%s",
        args.source_mode,
        args.profile,
        target_root,
        args.overwrite,
        hf_home,
        args.prefetch_hf_models,
    )

    if args.source_mode == "local_release":
        manifest, manifest_path = _resolve_local_manifest(args, logger)
        final_release_dir = _stage_local_release(
            manifest=manifest,
            manifest_path=manifest_path,
            target_root=target_root,
            profile=args.profile,
            overwrite=args.overwrite,
            logger=logger,
        )
    else:
        manifest, manifest_blob = _resolve_azure_manifest(args, logger)
        final_release_dir = _stage_azure_release(
            manifest=manifest,
            manifest_blob=manifest_blob,
            args=args,
            target_root=target_root,
            profile=args.profile,
            overwrite=args.overwrite,
            logger=logger,
        )

    semantic_model_dependencies = _semantic_model_dependencies(manifest)
    if semantic_model_dependencies and args.prefetch_hf_models:
        _prefetch_hf_models(
            manifest,
            hf_home=hf_home,
            allow_unpinned=args.allow_unpinned_hf_models,
            token_env=args.hf_token_env,
            logger=logger,
        )
    elif semantic_model_dependencies:
        logger.warning(
            "Release-manifest declares semantic Hugging Face model dependencies but prefetch is disabled. "
            "The backend must mount a prewarmed cache at runtime. dependencies=%s",
            semantic_model_dependencies,
        )
    else:
        logger.info("No semantic Hugging Face model dependencies declared in release-manifest.")

    logger.info(
        "Bootstrap finished final_release_dir=%s current_symlink=%s hf_home=%s",
        final_release_dir,
        target_root / "current",
        hf_home,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

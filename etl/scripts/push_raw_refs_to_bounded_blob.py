#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = REPO_ROOT / "etl" / "data" / "raw" / "refs"
DEFAULT_CONFIG_PATH = REPO_ROOT / "etl" / "conf" / "azure.yaml"
DEFAULT_REPORT_DIR = REPO_ROOT / "etl" / "manifests" / "migrations"
DEFAULT_TARGET_PREFIX = "raw-bounded/refs"
DEFAULT_SKIP_PREFIXES = ("tmp_", ".")


@dataclass(frozen=True)
class UploadCandidate:
    path: Path
    blob_name: str
    size_bytes: int
    sha256: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_azure_config(path: Path) -> dict[str, str]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    azure = payload.get("azure") or {}
    return {
        "container": str(azure.get("container") or "").strip(),
        "connection_string_env": str(azure.get("connection_string_env") or "AZURE_STORAGE_CONNECTION_STRING").strip(),
    }


def _configure_logger(log_path: Path | None) -> logging.Logger:
    logger = logging.getLogger("push_raw_refs_to_bounded_blob")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%Y-%m-%d %H:%M:%S")

    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_source_files(source_dir: Path, include_temp: bool) -> Iterable[Path]:
    for path in sorted(source_dir.iterdir()):
        if not path.is_file():
            continue
        if not include_temp and path.name.startswith(DEFAULT_SKIP_PREFIXES):
            continue
        yield path


def _collect_candidates(source_dir: Path, target_prefix: str, include_temp: bool) -> list[UploadCandidate]:
    candidates: list[UploadCandidate] = []
    normalized_prefix = target_prefix.strip("/").rstrip("/")
    for path in _iter_source_files(source_dir, include_temp):
        candidates.append(
            UploadCandidate(
                path=path,
                blob_name=f"{normalized_prefix}/{path.name}",
                size_bytes=path.stat().st_size,
                sha256=_sha256(path),
            )
        )
    return candidates


def _write_report(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Upload local etl/data/raw/refs files into the Azure Blob raw-bounded/refs prefix with "
            "safety checks and a migration report."
        )
    )
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--azure-config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--container", help="Override Azure Blob container name from etl/conf/azure.yaml.")
    parser.add_argument("--connection-string-env", help="Override connection-string env var from etl/conf/azure.yaml.")
    parser.add_argument("--target-prefix", default=DEFAULT_TARGET_PREFIX)
    parser.add_argument("--report-path", type=Path, help="Optional explicit migration report path.")
    parser.add_argument("--log-path", type=Path, help="Optional explicit log path.")
    parser.add_argument("--overwrite", action="store_true", help="Allow overwriting existing blobs.")
    parser.add_argument(
        "--resume-existing",
        action="store_true",
        help="Skip already-existing candidate blobs under the target prefix instead of blocking the whole run.",
    )
    parser.add_argument("--include-temp", action="store_true", help="Include temp or dot-prefixed files such as tmp_*.")
    parser.add_argument("--dry-run", action="store_true", help="Plan the upload and write a report without touching Azure.")
    parser.add_argument(
        "--max-block-size-mib",
        type=int,
        default=100,
        help="Azure block upload chunk size in MiB. Default: 100.",
    )
    parser.add_argument(
        "--max-single-put-size-mib",
        type=int,
        default=100,
        help="Single-request upload threshold in MiB. Default: 100.",
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=4,
        help="Maximum parallel connections for large uploads. Default: 4.",
    )
    parser.add_argument(
        "--connection-timeout",
        type=int,
        default=600,
        help="Azure request connection timeout in seconds. Default: 600.",
    )
    parser.add_argument(
        "--read-timeout",
        type=int,
        default=600,
        help="Azure request read timeout in seconds. Default: 600.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    source_dir = args.source_dir.resolve()
    if not source_dir.exists():
        raise SystemExit(f"Source directory does not exist: {source_dir}")

    azure_cfg = _load_azure_config(args.azure_config.resolve())
    container_name = args.container or azure_cfg["container"]
    connection_string_env = args.connection_string_env or azure_cfg["connection_string_env"]
    if not container_name:
        raise SystemExit("Azure container name is missing.")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = (args.report_path or (DEFAULT_REPORT_DIR / f"raw_refs_to_raw_bounded_refs_{timestamp}.json")).resolve()
    log_path = args.log_path.resolve() if args.log_path else report_path.with_suffix(".log")
    logger = _configure_logger(log_path)

    logger.info("Starting raw/refs blob migration source_dir=%s target_prefix=%s dry_run=%s", source_dir, args.target_prefix, args.dry_run)
    candidates = _collect_candidates(source_dir, args.target_prefix, args.include_temp)
    if not candidates:
        raise SystemExit(f"No upload candidates found in {source_dir}")

    payload: dict[str, object] = {
        "started_at": _utc_now_iso(),
        "source_dir": str(source_dir),
        "container": container_name,
        "target_prefix": args.target_prefix.strip("/"),
        "overwrite": bool(args.overwrite),
        "resume_existing": bool(args.resume_existing),
        "include_temp": bool(args.include_temp),
        "dry_run": bool(args.dry_run),
        "transfer": {
            "max_block_size_mib": int(args.max_block_size_mib),
            "max_single_put_size_mib": int(args.max_single_put_size_mib),
            "max_concurrency": int(args.max_concurrency),
            "connection_timeout": int(args.connection_timeout),
            "read_timeout": int(args.read_timeout),
        },
        "files": [
            {
                "name": candidate.path.name,
                "path": str(candidate.path),
                "blob_name": candidate.blob_name,
                "size_bytes": candidate.size_bytes,
                "sha256": candidate.sha256,
            }
            for candidate in candidates
        ],
        "planned_file_count": len(candidates),
        "planned_bytes": sum(candidate.size_bytes for candidate in candidates),
    }

    for candidate in candidates:
        logger.info("Prepared upload candidate file=%s blob=%s size_bytes=%s", candidate.path.name, candidate.blob_name, candidate.size_bytes)

    if args.dry_run:
        payload["status"] = "dry_run"
        payload["finished_at"] = _utc_now_iso()
        _write_report(report_path, payload)
        logger.info("Dry run finished report_path=%s planned_file_count=%s planned_bytes=%s", report_path, payload["planned_file_count"], payload["planned_bytes"])
        return 0

    connection_string = os.environ.get(connection_string_env)
    if not connection_string:
        raise SystemExit(
            f"Azure upload requires environment variable `{connection_string_env}` to be set."
        )

    from azure.storage.blob import BlobServiceClient

    service = BlobServiceClient.from_connection_string(
        connection_string,
        max_block_size=int(args.max_block_size_mib) * 1024 * 1024,
        max_single_put_size=int(args.max_single_put_size_mib) * 1024 * 1024,
        connection_timeout=int(args.connection_timeout),
        read_timeout=int(args.read_timeout),
    )
    container = service.get_container_client(container_name)

    prefix = args.target_prefix.strip("/").rstrip("/") + "/"
    existing_blobs = list(container.list_blobs(name_starts_with=prefix))
    payload["existing_blob_count_under_prefix"] = len(existing_blobs)
    existing_blob_names = {blob.name for blob in existing_blobs}
    existing_blob_sizes = {blob.name: int(getattr(blob, "size", 0) or 0) for blob in existing_blobs}
    if existing_blobs and not args.overwrite and not args.resume_existing:
        sample = [blob.name for blob in existing_blobs[:10]]
        payload["status"] = "blocked_existing_prefix"
        payload["existing_blob_sample"] = sample
        payload["finished_at"] = _utc_now_iso()
        _write_report(report_path, payload)
        raise SystemExit(
            f"Target prefix already contains {len(existing_blobs)} blobs and overwrite is disabled: "
            f"azure://{container_name}/{prefix}"
        )

    candidate_blob_names = {candidate.blob_name for candidate in candidates}
    unexpected_existing = sorted(existing_blob_names - candidate_blob_names)
    payload["unexpected_existing_blobs"] = unexpected_existing
    if unexpected_existing and not args.overwrite:
        payload["status"] = "blocked_unexpected_existing_blobs"
        payload["finished_at"] = _utc_now_iso()
        _write_report(report_path, payload)
        raise SystemExit(
            f"Target prefix contains unexpected existing blobs outside the planned candidate set: "
            f"azure://{container_name}/{prefix}"
        )

    skipped_existing: list[dict[str, object]] = []
    mismatched_existing: list[dict[str, object]] = []
    pending_candidates = candidates
    if args.resume_existing and not args.overwrite:
        pending_candidates = []
        for candidate in candidates:
            if candidate.blob_name in existing_blob_names:
                existing_size = existing_blob_sizes.get(candidate.blob_name, -1)
                if existing_size != candidate.size_bytes:
                    mismatched_existing.append(
                        {
                            "name": candidate.path.name,
                            "blob_name": candidate.blob_name,
                            "existing_size_bytes": existing_size,
                            "candidate_size_bytes": candidate.size_bytes,
                        }
                    )
                    logger.info(
                        "Existing blob size mismatch; reuploading file=%s blob=%s existing_size_bytes=%s candidate_size_bytes=%s",
                        candidate.path.name,
                        candidate.blob_name,
                        existing_size,
                        candidate.size_bytes,
                    )
                    pending_candidates.append(candidate)
                    continue
                skipped_existing.append(
                    {
                        "name": candidate.path.name,
                        "blob_name": candidate.blob_name,
                        "size_bytes": candidate.size_bytes,
                        "sha256": candidate.sha256,
                    }
                )
                logger.info("Skipping already-existing blob file=%s blob=%s", candidate.path.name, candidate.blob_name)
                continue
            pending_candidates.append(candidate)
    payload["skipped_existing"] = skipped_existing
    payload["skipped_existing_count"] = len(skipped_existing)
    payload["mismatched_existing"] = mismatched_existing
    payload["mismatched_existing_count"] = len(mismatched_existing)
    payload["pending_file_count"] = len(pending_candidates)
    payload["pending_bytes"] = sum(candidate.size_bytes for candidate in pending_candidates)

    uploaded: list[dict[str, object]] = []
    effective_overwrite = bool(args.overwrite or args.resume_existing)
    for candidate in pending_candidates:
        logger.info(
            "Uploading blob file=%s blob=%s overwrite=%s max_block_size_mib=%s max_single_put_size_mib=%s max_concurrency=%s",
            candidate.path.name,
            candidate.blob_name,
            effective_overwrite,
            args.max_block_size_mib,
            args.max_single_put_size_mib,
            args.max_concurrency,
        )
        with candidate.path.open("rb") as handle:
            container.upload_blob(
                candidate.blob_name,
                handle,
                overwrite=effective_overwrite,
                max_concurrency=int(args.max_concurrency),
                connection_timeout=int(args.connection_timeout),
                read_timeout=int(args.read_timeout),
            )
        properties = container.get_blob_client(candidate.blob_name).get_blob_properties()
        uploaded.append(
            {
                "name": candidate.path.name,
                "blob_name": candidate.blob_name,
                "size_bytes": candidate.size_bytes,
                "sha256": candidate.sha256,
                "etag": str(properties.etag),
                "last_modified": properties.last_modified.isoformat() if properties.last_modified else None,
            }
        )
        logger.info("Uploaded blob file=%s blob=%s etag=%s", candidate.path.name, candidate.blob_name, properties.etag)

    payload["status"] = "uploaded"
    payload["uploaded"] = uploaded
    payload["uploaded_file_count"] = len(uploaded)
    payload["uploaded_bytes"] = sum(int(item["size_bytes"]) for item in uploaded)
    payload["finished_at"] = _utc_now_iso()
    _write_report(report_path, payload)
    logger.info(
        "Upload finished report_path=%s uploaded_file_count=%s uploaded_bytes=%s",
        report_path,
        payload["uploaded_file_count"],
        payload["uploaded_bytes"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

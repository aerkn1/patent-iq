from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Any

from patentiq_etl.common.config import load_settings
from patentiq_etl.common.io import ensure_dir, write_text_json
from patentiq_etl.common.types import BuildSettings, utc_now_iso
from patentiq_etl.publish.runtime_contract import build_release_manifest, runtime_profiles


_IGNORED_FILENAMES = {".DS_Store"}


def _iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path for path in root.rglob("*") if path.is_file() and path.name not in _IGNORED_FILENAMES
    )


def _count_tree(root: Path) -> tuple[int, int]:
    file_count = 0
    total_bytes = 0
    for path in _iter_files(root):
        file_count += 1
        total_bytes += path.stat().st_size
    return file_count, total_bytes


def _source_root_for_release_path(settings: BuildSettings, release_relative_path: str) -> Path:
    first_part = Path(release_relative_path).parts[0]
    if first_part == "serving":
        return settings.repo_root / "etl" / "data" / "serving"
    if first_part == "vectors":
        return settings.vectors_dir
    if first_part == "models":
        return settings.ml_dir
    raise RuntimeError(f"Unsupported runtime release path root `{first_part}`.")


def _artifact_summary(settings: BuildSettings, release_root_prefix: str) -> dict[str, dict[str, Any]]:
    sources = {
        "serving": settings.repo_root / "etl" / "data" / "serving",
        "vectors": settings.vectors_dir,
        "models": settings.ml_dir,
    }
    summary: dict[str, dict[str, Any]] = {}
    for name, root in sources.items():
        file_count, total_bytes = _count_tree(root)
        summary[name] = {
            "blob_prefix": f"{release_root_prefix}/{name}",
            "local_path": str(root),
            "file_count": file_count,
            "bytes": total_bytes,
        }
    return summary


def _active_release_payload(
    settings: BuildSettings,
    *,
    release_manifest_path: Path,
    release_root_prefix: str,
    built_at: str,
) -> dict[str, Any]:
    return {
        "release_id": settings.release_id,
        "built_at": built_at,
        "artifact_root": release_root_prefix,
        "release_manifest_path": str(release_manifest_path),
        "release_manifest_blob": f"{release_root_prefix}/release-manifest.json",
    }


def _upload_entries(
    settings: BuildSettings,
    *,
    release_root_prefix: str,
    release_manifest_path: Path,
    active_release_path: Path,
) -> list[dict[str, Any]]:
    profiles = runtime_profiles()
    profile_map: dict[str, set[str]] = {}
    type_map: dict[str, str] = {}
    for profile_name, payload in profiles.items():
        for item in payload.get("items", []):
            path = str(item["path"])
            profile_map.setdefault(path, set()).add(profile_name)
            type_map[path] = str(item["type"])

    uploads: list[dict[str, Any]] = []
    for release_relative_path, profile_names in sorted(profile_map.items()):
        source_root = _source_root_for_release_path(settings, release_relative_path)
        relative_path = Path(release_relative_path).relative_to(Path(release_relative_path).parts[0])
        source_path = source_root / relative_path
        item_type = type_map[release_relative_path]
        if item_type == "file":
            if not source_path.exists():
                raise RuntimeError(f"Missing runtime release source file: {source_path}")
            uploads.append(
                {
                    "profiles": sorted(profile_names),
                    "type": "file",
                    "source_path": str(source_path),
                    "blob_path": f"{release_root_prefix}/{release_relative_path}",
                    "bytes": source_path.stat().st_size,
                }
            )
            continue
        if item_type != "directory":
            raise RuntimeError(f"Unsupported runtime release item type `{item_type}` for `{release_relative_path}`.")
        if not source_path.exists():
            raise RuntimeError(f"Missing runtime release source directory: {source_path}")
        directory_files = _iter_files(source_path)
        uploads.append(
            {
                "profiles": sorted(profile_names),
                "type": "directory",
                "source_path": str(source_path),
                "blob_prefix": f"{release_root_prefix}/{release_relative_path}",
                "file_count": len(directory_files),
                "bytes": sum(path.stat().st_size for path in directory_files),
            }
        )
        for file_path in directory_files:
            uploads.append(
                {
                    "profiles": sorted(profile_names),
                    "type": "file",
                    "source_path": str(file_path),
                    "blob_path": f"{release_root_prefix}/{release_relative_path}/{file_path.relative_to(source_path).as_posix()}",
                    "bytes": file_path.stat().st_size,
                }
            )

    uploads.append(
        {
            "profiles": ["default", "full"],
            "type": "file",
            "source_path": str(release_manifest_path),
            "blob_path": f"{release_root_prefix}/release-manifest.json",
            "bytes": release_manifest_path.stat().st_size,
            "generated": True,
        }
    )
    uploads.append(
        {
            "profiles": ["default", "full"],
            "type": "file",
            "source_path": str(active_release_path),
            "blob_path": settings.azure.get("active_release_manifest_blob", "manifests/active_release.json"),
            "bytes": active_release_path.stat().st_size,
            "generated": True,
            "activation_step": True,
        }
    )
    return uploads


def prepare_runtime_release_manifest(
    settings: BuildSettings,
    *,
    output_dir: Path | None = None,
    activate_local_pointer: bool = False,
) -> dict[str, Path]:
    built_at = utc_now_iso()
    release_root_prefix = f"releases/{settings.release_id}"
    target_dir = output_dir or (settings.manifests_dir / "releases" / settings.release_id)
    ensure_dir(target_dir)

    artifacts = _artifact_summary(settings, release_root_prefix)
    release_manifest = build_release_manifest(
        settings,
        release_dir=settings.releases_dir / settings.release_id,
        release_root_prefix=release_root_prefix,
        copied_artifacts=artifacts,
        built_at=built_at,
        serving_dir=settings.repo_root / "etl" / "data" / "serving",
        vectors_dir=settings.vectors_dir,
        models_dir=settings.ml_dir,
    )
    release_manifest_path = target_dir / "release-manifest.json"
    write_text_json(release_manifest_path, release_manifest)

    active_release_payload = _active_release_payload(
        settings,
        release_manifest_path=release_manifest_path,
        release_root_prefix=release_root_prefix,
        built_at=built_at,
    )
    generated_active_release_path = target_dir / "active_release.json"
    write_text_json(generated_active_release_path, active_release_payload)

    if activate_local_pointer:
        canonical_active_release = settings.manifests_dir / "releases" / "active_release.json"
        write_text_json(canonical_active_release, active_release_payload)

    upload_plan_path = target_dir / "runtime-upload-plan.json"
    upload_entries = _upload_entries(
        settings,
        release_root_prefix=release_root_prefix,
        release_manifest_path=release_manifest_path,
        active_release_path=generated_active_release_path,
    )
    write_text_json(
        upload_plan_path,
        {
            "release_id": settings.release_id,
            "built_at": built_at,
            "blob_container": settings.azure.get("container"),
            "release_root_prefix": release_root_prefix,
            "profiles": runtime_profiles(),
            "uploads": upload_entries,
        },
    )

    return {
        "release_manifest_path": release_manifest_path,
        "active_release_path": generated_active_release_path,
        "upload_plan_path": upload_plan_path,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a runtime-only release manifest, active pointer, and upload plan without staging a full local release."
    )
    parser.add_argument(
        "--etl-root",
        default=str((Path(__file__).resolve().parents[3] / "etl")),
        help="Path to the repo etl/ directory.",
    )
    parser.add_argument("--release-id", help="Optional runtime release id override.")
    parser.add_argument("--output-dir", help="Optional output directory for generated manifest files.")
    parser.add_argument(
        "--activate-local-pointer",
        action="store_true",
        help="Also write etl/manifests/releases/active_release.json to the generated release.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    etl_root = Path(args.etl_root).resolve()
    settings = load_settings(etl_root)
    if args.release_id:
        settings = replace(settings, release_id=args.release_id)
    output_dir = Path(args.output_dir).resolve() if args.output_dir else None
    outputs = prepare_runtime_release_manifest(
        settings,
        output_dir=output_dir,
        activate_local_pointer=args.activate_local_pointer,
    )
    for key, value in outputs.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

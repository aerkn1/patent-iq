from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class LayerPlan:
    name: str
    local_path: Path
    blob_prefix: str
    file_count: int
    bytes: int


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name == ".DS_Store":
            continue
        yield path


def _build_layer_plan(layer_name: str, layer_root: Path, archive_id: str) -> tuple[LayerPlan, list[dict[str, object]]]:
    files = list(_iter_files(layer_root))
    blob_prefix = f"{layer_name}/{archive_id}"
    uploads = []
    total_bytes = 0
    for path in files:
        rel = path.relative_to(layer_root).as_posix()
        size = path.stat().st_size
        total_bytes += size
        uploads.append(
            {
                "type": "file",
                "layer": layer_name,
                "blob_path": f"{blob_prefix}/{rel}",
                "source_path": str(path.resolve()),
                "bytes": size,
            }
        )
    layer_plan = LayerPlan(
        name=layer_name,
        local_path=layer_root.resolve(),
        blob_prefix=blob_prefix,
        file_count=len(files),
        bytes=total_bytes,
    )
    return layer_plan, uploads


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an archive upload plan for bronze/silver/gold layers.")
    parser.add_argument("--etl-root", default="etl", help="ETL root directory. Defaults to ./etl")
    parser.add_argument("--archive-id", required=True, help="Archive identifier used in blob prefixes.")
    parser.add_argument("--blob-container", default="patentiq-data", help="Target blob container name.")
    args = parser.parse_args()

    etl_root = Path(args.etl_root).resolve()
    data_root = etl_root / "data"
    archive_dir = etl_root / "manifests" / "archives" / args.archive_id
    archive_dir.mkdir(parents=True, exist_ok=True)

    layers: dict[str, dict[str, object]] = {}
    uploads: list[dict[str, object]] = []
    total_files = 0
    total_bytes = 0

    for layer_name in ("bronze", "silver", "gold"):
        layer_root = data_root / layer_name
        if not layer_root.is_dir():
            raise SystemExit(f"Layer directory does not exist: {layer_root}")
        layer_plan, layer_uploads = _build_layer_plan(layer_name, layer_root, args.archive_id)
        layers[layer_name] = {
            "blob_prefix": layer_plan.blob_prefix,
            "bytes": layer_plan.bytes,
            "file_count": layer_plan.file_count,
            "local_path": str(layer_plan.local_path),
        }
        uploads.extend(layer_uploads)
        total_files += layer_plan.file_count
        total_bytes += layer_plan.bytes

    payload = {
        "archive_id": args.archive_id,
        "blob_container": args.blob_container,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "layers": layers,
        "summary": {
            "file_count": total_files,
            "bytes": total_bytes,
        },
        "uploads": uploads,
    }

    output_path = archive_dir / "archive-upload-plan.json"
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True))

    summary_path = archive_dir / "archive-summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "archive_id": args.archive_id,
                "blob_container": args.blob_container,
                "layers": layers,
                "summary": payload["summary"],
            },
            indent=2,
            sort_keys=True,
        )
    )

    print(f"Wrote archive upload plan: {output_path}")
    print(f"Wrote archive summary: {summary_path}")


if __name__ == "__main__":
    main()

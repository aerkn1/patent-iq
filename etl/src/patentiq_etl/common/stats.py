from __future__ import annotations

from pathlib import Path
from typing import Any

from patentiq_etl.common.io import parquet_columns, parquet_row_count
from patentiq_etl.common.manifest import sha256_file, write_json
from patentiq_etl.common.types import StageResult


def _output_profile(path: Path) -> dict[str, Any]:
    """Build a lightweight profile for one stage output artifact."""
    profile: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
    }
    if not path.exists():
        return profile

    if path.is_dir():
        profile["type"] = "directory"
        profile["entry_count"] = sum(1 for _ in path.iterdir())
        return profile

    profile["type"] = "file"
    profile["size_bytes"] = path.stat().st_size
    profile["sha256"] = sha256_file(path)
    if path.suffix == ".parquet":
        profile["row_count"] = parquet_row_count(path)
        profile["column_count"] = len(parquet_columns(path))
    return profile


def write_stage_stats(path: Path, result: StageResult) -> Path:
    """Persist a stage-level stats snapshot with metrics and output artifact profiles."""
    payload = {
        "stage": result.stage,
        "status": result.status,
        "summary": result.summary,
        "started_at": result.started_at,
        "finished_at": result.finished_at,
        "metrics": result.metrics,
        "warnings": result.warnings,
        "downstream_impacts": result.downstream_impacts,
        "output_profiles": [_output_profile(Path(output)) for output in result.outputs],
    }
    write_json(path, payload)
    return path

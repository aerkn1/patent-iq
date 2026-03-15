from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from patentiq_etl.common.types import StageResult


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file on disk."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a JSON payload to disk with stable formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_stage_manifest(path: Path, result: StageResult) -> None:
    """Persist one ETL stage result as a JSON manifest."""
    write_json(path, result.finish().to_dict())

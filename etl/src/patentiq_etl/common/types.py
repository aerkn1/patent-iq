from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    """Return the current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class StageResult:
    """Structured record of one ETL stage execution for manifests, logs, and journals."""
    stage: str
    status: str
    summary: str
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    methods: list[str] = field(default_factory=list)
    calculations: list[str] = field(default_factory=list)
    doc_refs: list[str] = field(default_factory=list)
    downstream_impacts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    artifacts: dict[str, Any] = field(default_factory=dict)
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str | None = None

    def finish(self) -> "StageResult":
        """Stamp completion time and return the same result object."""
        self.finished_at = utc_now_iso()
        return self

    def to_dict(self) -> dict[str, Any]:
        """Serialize the stage result for JSON manifest output."""
        return asdict(self)


@dataclass
class BuildSettings:
    """Resolved configuration bundle shared across all ETL stages."""
    repo_root: Path
    release_id: str
    snapshot_date: str
    year_window_start: int
    year_window_end: int
    azure_publish_enabled: bool
    vector_sample_pct: float
    active_grant_only_for_semantic: bool
    method_version: str
    semantic_embedding_method: str
    semantic_ann_method: str
    patstat_source_mode: str
    register_source_mode: str
    epab_source_mode: str
    uspto_source_mode: str
    refs_source_mode: str
    tip_env: str
    raw_patstat_dir: Path
    raw_register_dir: Path
    raw_uspto_dir: Path
    raw_epab_dir: Path
    raw_refs_dir: Path
    bounded_patstat_dir: Path
    bounded_register_dir: Path
    bounded_uspto_dir: Path
    bounded_epab_dir: Path
    bounded_refs_dir: Path
    bounded_seed_dir: Path
    bronze_dir: Path
    silver_dir: Path
    gold_dir: Path
    ml_dir: Path
    vectors_dir: Path
    releases_dir: Path
    manifests_dir: Path
    journal_path: Path
    ref_techn_field_ipc: Path
    scope_type: str
    field_source: str
    selected_wipo_fields: list[str]
    thresholds: dict[str, Any]
    azure: dict[str, Any]

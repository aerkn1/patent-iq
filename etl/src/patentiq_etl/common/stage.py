from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging

from patentiq_etl.common.types import BuildSettings


@dataclass
class StageContext:
    """Runtime context bundle for stage-specific execution helpers."""
    settings: BuildSettings
    logger: logging.Logger
    stage_name: str
    manifest_path: Path

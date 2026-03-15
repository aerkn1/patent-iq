from __future__ import annotations

from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.prebronze.extract import extract_bounded_raw


def run_prebronze(settings: BuildSettings) -> list[StageResult]:
    """Run the bounded raw extraction stage group before Bronze landing."""
    return [extract_bounded_raw(settings)]

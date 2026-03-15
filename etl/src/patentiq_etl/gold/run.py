from __future__ import annotations

from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.gold.build_gold import build_gold


def run_gold(settings: BuildSettings) -> list[StageResult]:
    """Run the Gold mart build stage."""
    return [build_gold(settings)]

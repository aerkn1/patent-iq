from __future__ import annotations

from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.silver.build_core import build_core_silver, build_scope_seed
from patentiq_etl.silver.build_enrichment import build_enrichment_silver


def run_scope(settings: BuildSettings) -> list[StageResult]:
    """Run the scope-seeding Silver substage."""
    return [build_scope_seed(settings)]


def run_silver(settings: BuildSettings) -> list[StageResult]:
    """Run the full Silver stage group after bounded scope seeds exist."""
    return [build_core_silver(settings), *build_enrichment_silver(settings)]

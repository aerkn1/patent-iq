from __future__ import annotations

from patentiq_etl.bronze.ingest_epab_fulltext import ingest_epab_fulltext
from patentiq_etl.bronze.ingest_structured import ingest_structured_bronze
from patentiq_etl.bronze.ingest_uspto_fulltext import ingest_uspto_fulltext
from patentiq_etl.common.types import BuildSettings, StageResult


def run_bronze(settings: BuildSettings) -> list[StageResult]:
    """Execute the full Bronze stage group in dependency-safe order."""
    return [
        ingest_structured_bronze(settings),
        ingest_uspto_fulltext(settings),
        ingest_epab_fulltext(settings),
    ]

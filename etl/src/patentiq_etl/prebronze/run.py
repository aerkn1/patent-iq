from __future__ import annotations

from dataclasses import replace

from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.prebronze.chunked import run_tip_chunked_export, run_tip_heritage_chunked_export
from patentiq_etl.prebronze.extract import extract_bounded_raw
from patentiq_etl.prebronze.plan import plan_tip_chunked_export, plan_tip_heritage_chunked_export
from patentiq_etl.prebronze.uspto_odp import extract_uspto_odp_to_bronze


def run_prebronze(settings: BuildSettings) -> list[StageResult]:
    """Run the bounded raw extraction stage group before Bronze landing."""
    if settings.execution.get("tip_chunked_export_enabled", False) and settings.patstat_source_mode == "tip":
        return [run_tip_chunked_export(settings)]
    return [extract_bounded_raw(settings)]


def run_prebronze_heritage(settings: BuildSettings) -> list[StageResult]:
    """Run the historical heritage-backfill bounded raw extraction stage group."""
    if settings.execution.get("tip_chunked_export_enabled", False) and settings.patstat_source_mode == "tip":
        return [run_tip_heritage_chunked_export(settings)]
    heritage_settings = replace(
        settings,
        year_window_start=settings.heritage_backfill_start,
        year_window_end=settings.heritage_backfill_end,
    )
    result = extract_bounded_raw(heritage_settings)
    result.stage = "pre-bronze-heritage-extraction"
    result.summary = "Extracted the older heritage-backfill bounded raw slice for mega-cluster historical support."
    return [result]


def run_tip_chunk_plan(settings: BuildSettings) -> list[StageResult]:
    """Generate the TIP chunked-export plan used for Blob-first full-scope runs."""
    return [plan_tip_chunked_export(settings)]


def run_tip_heritage_chunk_plan(settings: BuildSettings) -> list[StageResult]:
    """Generate the TIP chunked-export plan used for heritage backfill runs."""
    return [plan_tip_heritage_chunked_export(settings)]


def run_prebronze_uspto_odp(settings: BuildSettings) -> list[StageResult]:
    """Run the local USPTO ODP stream worker using an existing U.S. publication seed."""
    result = StageResult(
        stage="pre-bronze-uspto-odp-stream",
        status="success",
        summary="Downloaded bounded USPTO APPXML from ODP, wrote direct Bronze parquet outputs, and cleaned temp ZIP/XML artifacts.",
        methods=[
            "Used the bounded `seed_us_publication_numbers` universe to limit weekly ODP ZIP processing.",
            "Downloaded one weekly APPXML ZIP at a time, extracted the XML payload, and stream-parsed publication documents.",
            "Wrote direct USPTO Bronze parquet outputs and recorded per-file extraction stats before deleting temp artifacts.",
        ],
        calculations=[
            "USPTO processing is restricted to the main operating window and to the bounded in-scope U.S. publication seed.",
            "Only matched publications are persisted; unmatched publications in the same weekly payload are discarded during parse.",
        ],
        downstream_impacts=[
            "These direct Bronze outputs feed semantic representative text selection without requiring retained bounded USPTO XML.",
            "Download or parse failures here degrade U.S. claim-space coverage while leaving PATSTAT abstract fallback available.",
        ],
        doc_refs=[
            "docs/data/uspto-odp-stream-extraction-pipeline.md",
            "docs/data/uspto-full-text-schema.md",
            "docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md",
        ],
    )
    extract_uspto_odp_to_bronze(settings, settings.bounded_seed_dir / "seed_us_publication_numbers.parquet", result)
    return [result]

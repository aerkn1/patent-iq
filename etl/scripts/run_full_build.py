from __future__ import annotations

from _bootstrap import bootstrap

etl_root = bootstrap()

from patentiq_etl.common.config import load_settings
from patentiq_etl.common.journal import append_stage_entry
from patentiq_etl.common.logging_utils import configure_logger
from patentiq_etl.common.manifest import write_stage_manifest
from patentiq_etl.common.stats import write_stage_stats
from patentiq_etl.common.types import StageResult
from patentiq_etl.bronze.certify import certify_sources, certify_release
from patentiq_etl.prebronze.run import (
    run_prebronze,
    run_prebronze_heritage,
    run_prebronze_uspto_odp,
    run_tip_chunk_plan,
    run_tip_heritage_chunk_plan,
)
from patentiq_etl.bronze.run import run_bronze
from patentiq_etl.silver.run import run_scope, run_silver
from patentiq_etl.gold.run import run_gold
from patentiq_etl.ml.run import run_ml
from patentiq_etl.semantic.run import run_semantic
from patentiq_etl.publish.run import publish_release


def _persist(settings, result: StageResult) -> None:
    """Persist one stage result to the standard ETL audit outputs."""
    logger = configure_logger(result.stage, settings.manifests_dir / "stages" / f"{result.stage}.log")
    logger.info("Persisting stage `%s` with status=%s", result.stage, result.status)
    stats_path = settings.manifests_dir / "stats" / f"{result.stage}.json"
    write_stage_stats(stats_path, result)
    result.artifacts["stats_snapshot"] = str(stats_path)
    write_stage_manifest(settings.manifests_dir / "stages" / f"{result.stage}.json", result)
    append_stage_entry(settings.journal_path, result)


def _execute_stage(settings, stage_name: str, fn) -> list[StageResult]:
    """Run one stage group with runner-level logging and return its results."""
    logger = configure_logger(f"runner-{stage_name}", settings.manifests_dir / "stages" / f"runner-{stage_name}.log")
    logger.info("Starting stage group `%s`", stage_name)
    results = fn(settings)
    for result in results:
        logger.info("Finished stage `%s` status=%s outputs=%s", result.stage, result.status, len(result.outputs))
    return results


def main() -> None:
    """Execute the full local PatentIQ ETL pipeline in the canonical order."""
    settings = load_settings(etl_root)
    ordered_results = []
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "source-certification", lambda s: [certify_sources(s)])])
    if settings.execution.get("tip_chunked_export_enabled", False):
        ordered_results.extend([result.finish() for result in _execute_stage(settings, "tip-chunk-plan", run_tip_chunk_plan)])
        if settings.execution.get("heritage_backfill_enabled", False):
            ordered_results.extend([result.finish() for result in _execute_stage(settings, "tip-heritage-chunk-plan", run_tip_heritage_chunk_plan)])
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "prebronze", run_prebronze)])
    if settings.execution.get("heritage_backfill_enabled", False):
        ordered_results.extend([result.finish() for result in _execute_stage(settings, "prebronze-heritage", run_prebronze_heritage)])
    if settings.uspto_source_mode == "odp_api":
        ordered_results.extend([result.finish() for result in _execute_stage(settings, "prebronze-uspto-odp", run_prebronze_uspto_odp)])
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "bronze", run_bronze)])
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "scope", run_scope)])
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "silver", run_silver)])
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "gold", run_gold)])
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "ml", run_ml)])
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "semantic", run_semantic)])
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "release-certification", lambda s: [certify_release(s)])])
    ordered_results.extend([result.finish() for result in _execute_stage(settings, "publish", publish_release)])
    for result in ordered_results:
        _persist(settings, result)


if __name__ == "__main__":
    main()

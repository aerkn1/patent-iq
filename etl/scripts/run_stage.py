from __future__ import annotations

import sys
from collections.abc import Callable

from _bootstrap import bootstrap

etl_root = bootstrap()

from patentiq_etl.bronze.certify import certify_release, certify_sources
from patentiq_etl.bronze.run import run_bronze
from patentiq_etl.common.config import load_settings
from patentiq_etl.common.journal import append_stage_entry
from patentiq_etl.common.logging_utils import configure_logger
from patentiq_etl.common.manifest import write_stage_manifest
from patentiq_etl.common.stats import write_stage_stats
from patentiq_etl.common.types import StageResult
from patentiq_etl.gold.run import run_gold
from patentiq_etl.ml.run import run_ml
from patentiq_etl.prebronze.run import run_prebronze
from patentiq_etl.semantic.run import run_semantic
from patentiq_etl.silver.run import run_scope, run_silver


STAGES: dict[str, Callable] = {
    "certify": lambda settings: [certify_sources(settings)],
    "source-certification": lambda settings: [certify_sources(settings)],
    "prebronze": run_prebronze,
    "bronze": run_bronze,
    "scope": run_scope,
    "silver": run_silver,
    "gold": run_gold,
    "ml": run_ml,
    "semantic": run_semantic,
    "certify-release": lambda settings: [certify_release(settings)],
    "release-certification": lambda settings: [certify_release(settings)],
    "publish": lambda settings: __import__("patentiq_etl.publish.run", fromlist=["publish_release"]).publish_release(settings),
}


def _record(settings, result: StageResult) -> None:
    """Persist one finished stage result to logs, JSON manifest, and markdown journal."""
    logger = configure_logger(result.stage, settings.manifests_dir / "stages" / f"{result.stage}.log")
    logger.info("Recording stage result status=%s", result.status)
    stats_path = settings.manifests_dir / "stats" / f"{result.stage}.json"
    write_stage_stats(stats_path, result)
    result.artifacts["stats_snapshot"] = str(stats_path)
    manifest_path = settings.manifests_dir / "stages" / f"{result.stage}.json"
    write_stage_manifest(manifest_path, result)
    append_stage_entry(settings.journal_path, result)


def main(stage_name: str) -> None:
    """Execute one named ETL stage group from the command line."""
    settings = load_settings(etl_root)
    if stage_name not in STAGES:
        raise SystemExit(f"Unknown stage: {stage_name}")
    logger = configure_logger(f"runner-{stage_name}", settings.manifests_dir / "stages" / f"runner-{stage_name}.log")
    logger.info("Starting requested stage group `%s`", stage_name)
    results = STAGES[stage_name](settings)
    for result in results:
        logger.info("Stage `%s` completed with status=%s", result.stage, result.status)
        _record(settings, result.finish())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/run_stage.py <stage>")
    main(sys.argv[1])

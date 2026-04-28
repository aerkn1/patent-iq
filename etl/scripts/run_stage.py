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
from patentiq_etl.gold.run import (
    run_gold,
    run_gold_family_citation_chronology,
    run_gold_cpc_importance_pit,
    run_gold_family_compare_pit,
    run_gold_family_classification_jurisdiction_pit,
    run_gold_family_classification_mix_pit,
    run_gold_family_core,
    run_gold_family_metrics,
    run_gold_family_summary,
    run_gold_market_cpc_jurisdiction_trend_pit,
    run_gold_history,
    run_gold_history_blocking,
    run_gold_history_fields,
    run_gold_market_cpc_trend_pit,
    run_gold_market_leaderboard_pit,
    run_gold_market_semantic,
    run_gold_market_summary_pit,
    run_gold_portfolio_compare_pit,
    run_gold_portfolio_classification_jurisdiction_pit,
    run_gold_portfolio_classification_mix_pit,
    run_gold_portfolio,
    run_gold_portfolio_summary_pit,
)
from patentiq_etl.ml.run import run_ml
from patentiq_etl.ml.run import run_ml_phase0_foundation
from patentiq_etl.ml.run import run_ml_pending_grant_pipeline
from patentiq_etl.ml.run import run_ml_phase03_family_forecast
from patentiq_etl.ml.run import run_ml_phase04_family_jurisdiction_lapse_risk
from patentiq_etl.ml.run import run_ml_phase06_jurisdiction_field_trend_forecast
from patentiq_etl.prebronze.run import (
    run_build_oecd_indicator_bronze_projection,
    run_build_oecd_indicator_cohort_stats,
    run_build_oecd_indicator_longform,
    run_build_oecd_indicator_seed,
    run_consolidate_before_bronze,
    run_normalize_kind_code,
    run_prebronze,
    run_prebronze_heritage,
    run_prebronze_uspto_odp,
    run_repair_epab_for_semantic,
    run_tip_derived_seed_backfill,
    run_tip_blob_recovery,
    run_tip_chunk_plan,
    run_tip_heritage_chunk_plan,
)
from patentiq_etl.semantic.run import (
    run_semantic_ann,
    run_semantic,
    run_semantic_abstract_phase,
    run_semantic_claim_phase,
    run_semantic_merge,
)
from patentiq_etl.serving.run import run_serving_snapshots
from patentiq_etl.silver.run import (
    run_scope,
    run_silver,
    run_silver_history_refresh,
    run_silver_kind_legal_refresh,
    run_silver_kind_refresh,
    run_silver_legal_status_refresh,
    run_silver_owner_refresh,
    run_silver_oecd_refresh,
    run_silver_pit_classification_dense,
    run_silver_pit_classification_visibility,
    run_silver_pit,
    run_silver_pit_dense,
)


STAGES: dict[str, Callable] = {
    "certify": lambda settings: [certify_sources(settings)],
    "source-certification": lambda settings: [certify_sources(settings)],
    "plan-tip-export": run_tip_chunk_plan,
    "tip-chunk-plan": run_tip_chunk_plan,
    "plan-tip-heritage-export": run_tip_heritage_chunk_plan,
    "tip-heritage-chunk-plan": run_tip_heritage_chunk_plan,
    "recover-tip-blob-uploads": run_tip_blob_recovery,
    "tip-blob-recovery": run_tip_blob_recovery,
    "backfill-tip-derived-seeds": run_tip_derived_seed_backfill,
    "tip-derived-seed-backfill": run_tip_derived_seed_backfill,
    "consolidate-before-bronze": run_consolidate_before_bronze,
    "consolidate_before_bronze": run_consolidate_before_bronze,
    "repair-epab-for-semantic": run_repair_epab_for_semantic,
    "repair_epab_for_semantic": run_repair_epab_for_semantic,
    "normalize-kind-code": run_normalize_kind_code,
    "normalize_kind_code": run_normalize_kind_code,
    "build-oecd-indicator-seed": run_build_oecd_indicator_seed,
    "build_oecd_indicator_seed": run_build_oecd_indicator_seed,
    "build-oecd-indicator-cohort-stats": run_build_oecd_indicator_cohort_stats,
    "build_oecd_indicator_cohort_stats": run_build_oecd_indicator_cohort_stats,
    "build-oecd-indicator-longform": run_build_oecd_indicator_longform,
    "build_oecd_indicator_longform": run_build_oecd_indicator_longform,
    "build-oecd-indicator-bronze-projection": run_build_oecd_indicator_bronze_projection,
    "build_oecd_indicator_bronze_projection": run_build_oecd_indicator_bronze_projection,
    "prebronze": run_prebronze,
    "prebronze-heritage": run_prebronze_heritage,
    "prebronze-uspto-odp": run_prebronze_uspto_odp,
    "bronze": run_bronze,
    "scope": run_scope,
    "silver": run_silver,
    "silver-kind-refresh": run_silver_kind_refresh,
    "silver_kind_refresh": run_silver_kind_refresh,
    "silver-kind-legal-refresh": run_silver_kind_legal_refresh,
    "silver_kind_legal_refresh": run_silver_kind_legal_refresh,
    "silver-legal-status-refresh": run_silver_legal_status_refresh,
    "silver_legal_status_refresh": run_silver_legal_status_refresh,
    "silver-owner-refresh": run_silver_owner_refresh,
    "silver_owner_refresh": run_silver_owner_refresh,
    "silver-oecd-refresh": run_silver_oecd_refresh,
    "silver_oecd_refresh": run_silver_oecd_refresh,
    "silver-history-refresh": run_silver_history_refresh,
    "silver_history_refresh": run_silver_history_refresh,
    "silver-pit": run_silver_pit,
    "silver_pit": run_silver_pit,
    "silver-pit-dense": run_silver_pit_dense,
    "silver_pit_dense": run_silver_pit_dense,
    "silver-pit-classification-visibility": run_silver_pit_classification_visibility,
    "silver_pit_classification_visibility": run_silver_pit_classification_visibility,
    "silver-pit-classification-dense": run_silver_pit_classification_dense,
    "silver_pit_classification_dense": run_silver_pit_classification_dense,
    "gold": run_gold,
    "gold-family-summary": run_gold_family_summary,
    "gold_family_summary": run_gold_family_summary,
    "gold-family-metrics": run_gold_family_metrics,
    "gold_family_metrics": run_gold_family_metrics,
    "gold-family-citation-chronology": run_gold_family_citation_chronology,
    "gold_family_citation_chronology": run_gold_family_citation_chronology,
    "gold-family-core": run_gold_family_core,
    "gold_family_core": run_gold_family_core,
    "gold-family-compare-pit": run_gold_family_compare_pit,
    "gold_family_compare_pit": run_gold_family_compare_pit,
    "gold-family-classification-mix-pit": run_gold_family_classification_mix_pit,
    "gold_family_classification_mix_pit": run_gold_family_classification_mix_pit,
    "gold-family-classification-jurisdiction-pit": run_gold_family_classification_jurisdiction_pit,
    "gold_family_classification_jurisdiction_pit": run_gold_family_classification_jurisdiction_pit,
    "gold-portfolio-summary-pit": run_gold_portfolio_summary_pit,
    "gold_portfolio_summary_pit": run_gold_portfolio_summary_pit,
    "gold-portfolio-classification-mix-pit": run_gold_portfolio_classification_mix_pit,
    "gold_portfolio_classification_mix_pit": run_gold_portfolio_classification_mix_pit,
    "gold-portfolio-classification-jurisdiction-pit": run_gold_portfolio_classification_jurisdiction_pit,
    "gold_portfolio_classification_jurisdiction_pit": run_gold_portfolio_classification_jurisdiction_pit,
    "gold-portfolio-compare-pit": run_gold_portfolio_compare_pit,
    "gold_portfolio_compare_pit": run_gold_portfolio_compare_pit,
    "gold-market-summary-pit": run_gold_market_summary_pit,
    "gold_market_summary_pit": run_gold_market_summary_pit,
    "gold-market-cpc-trend-pit": run_gold_market_cpc_trend_pit,
    "gold_market_cpc_trend_pit": run_gold_market_cpc_trend_pit,
    "gold-market-cpc-jurisdiction-trend-pit": run_gold_market_cpc_jurisdiction_trend_pit,
    "gold_market_cpc_jurisdiction_trend_pit": run_gold_market_cpc_jurisdiction_trend_pit,
    "gold-cpc-importance-pit": run_gold_cpc_importance_pit,
    "gold_cpc_importance_pit": run_gold_cpc_importance_pit,
    "gold-market-leaderboard-pit": run_gold_market_leaderboard_pit,
    "gold_market_leaderboard_pit": run_gold_market_leaderboard_pit,
    "gold-history": run_gold_history,
    "gold_history": run_gold_history,
    "gold-history-fields": run_gold_history_fields,
    "gold_history_fields": run_gold_history_fields,
    "gold-history-blocking": run_gold_history_blocking,
    "gold_history_blocking": run_gold_history_blocking,
    "gold-portfolio": run_gold_portfolio,
    "gold_portfolio": run_gold_portfolio,
    "gold-market-semantic": run_gold_market_semantic,
    "gold_market_semantic": run_gold_market_semantic,
    "ml": run_ml,
    "ml-phase0-foundation": run_ml_phase0_foundation,
    "ml_phase0_foundation": run_ml_phase0_foundation,
    "ml-pending-grant-pipeline": run_ml_pending_grant_pipeline,
    "ml_pending_grant_pipeline": run_ml_pending_grant_pipeline,
    "ml-phase03-family-forecast": run_ml_phase03_family_forecast,
    "ml_phase03_family_forecast": run_ml_phase03_family_forecast,
    "ml-phase04-family-jurisdiction-lapse-risk": run_ml_phase04_family_jurisdiction_lapse_risk,
    "ml_phase04_family_jurisdiction_lapse_risk": run_ml_phase04_family_jurisdiction_lapse_risk,
    "ml-phase06-jurisdiction-field-trend-forecast": run_ml_phase06_jurisdiction_field_trend_forecast,
    "ml_phase06_jurisdiction_field_trend_forecast": run_ml_phase06_jurisdiction_field_trend_forecast,
    "semantic": run_semantic,
    "semantic-abstract-phase": run_semantic_abstract_phase,
    "semantic_abstract_phase": run_semantic_abstract_phase,
    "semantic-claim-phase": run_semantic_claim_phase,
    "semantic_claim_phase": run_semantic_claim_phase,
    "semantic-merge": run_semantic_merge,
    "semantic_merge": run_semantic_merge,
    "semantic-ann": run_semantic_ann,
    "semantic_ann": run_semantic_ann,
    "serving-snapshots": run_serving_snapshots,
    "serving_snapshots": run_serving_snapshots,
    "backend-serving-artifacts": run_serving_snapshots,
    "backend_serving_artifacts": run_serving_snapshots,
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

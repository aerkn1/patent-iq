from __future__ import annotations

from patentiq_etl.common.types import BuildSettings, StageResult
from patentiq_etl.gold.build_gold import (
    build_gold,
    build_gold_cpc_importance_pit,
    build_gold_family_citation_chronology,
    build_gold_family_classification_jurisdiction_pit,
    build_gold_family_classification_mix_pit,
    build_gold_family_compare_pit,
    build_gold_family_core,
    build_gold_family_metrics,
    build_gold_market_cpc_jurisdiction_trend_pit,
    build_gold_market_cpc_trend_pit,
    build_gold_market_leaderboard_pit,
    build_gold_portfolio_classification_jurisdiction_pit,
    build_gold_portfolio_compare_pit,
    build_gold_portfolio_classification_mix_pit,
    build_gold_market_summary_pit,
    build_gold_family_summary,
    build_gold_history,
    build_gold_history_blocking,
    build_gold_history_fields,
    build_gold_market_semantic,
    build_gold_portfolio,
    build_gold_portfolio_summary_pit,
)


def run_gold(settings: BuildSettings) -> list[StageResult]:
    """Run the full Gold mart build as ordered sub-stages."""
    return [
        build_gold_family_summary(settings),
        build_gold_family_metrics(settings),
        build_gold_history(settings),
        build_gold_portfolio(settings),
        build_gold_market_semantic(settings),
    ]


def run_gold_family_summary(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_family_summary(settings)]


def run_gold_family_metrics(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_family_metrics(settings)]


def run_gold_family_citation_chronology(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_family_citation_chronology(settings)]


def run_gold_family_core(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_family_core(settings)]


def run_gold_family_compare_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_family_compare_pit(settings)]


def run_gold_family_classification_mix_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_family_classification_mix_pit(settings)]


def run_gold_family_classification_jurisdiction_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_family_classification_jurisdiction_pit(settings)]


def run_gold_portfolio_summary_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_portfolio_summary_pit(settings)]


def run_gold_portfolio_classification_mix_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_portfolio_classification_mix_pit(settings)]


def run_gold_portfolio_classification_jurisdiction_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_portfolio_classification_jurisdiction_pit(settings)]


def run_gold_portfolio_compare_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_portfolio_compare_pit(settings)]


def run_gold_market_summary_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_market_summary_pit(settings)]


def run_gold_market_cpc_trend_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_market_cpc_trend_pit(settings)]


def run_gold_market_cpc_jurisdiction_trend_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_market_cpc_jurisdiction_trend_pit(settings)]


def run_gold_cpc_importance_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_cpc_importance_pit(settings)]


def run_gold_market_leaderboard_pit(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_market_leaderboard_pit(settings)]


def run_gold_history(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_history(settings)]


def run_gold_history_fields(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_history_fields(settings)]


def run_gold_history_blocking(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_history_blocking(settings)]


def run_gold_portfolio(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_portfolio(settings)]


def run_gold_market_semantic(settings: BuildSettings) -> list[StageResult]:
    return [build_gold_market_semantic(settings)]

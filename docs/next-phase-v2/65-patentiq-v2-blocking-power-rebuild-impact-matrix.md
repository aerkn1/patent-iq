# PatentIQ V2 Blocking-Power Rebuild Impact Matrix

## Purpose

This note defines which Gold marts must be rebuilt after the planned family blocking-power and citation-normalization correction, which marts are logically safe to keep, and which outputs are only conditionally rebuild-dependent.

The current on-disk audit state for this matrix is recorded in [66-patentiq-v2-blocking-power-current-state-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/66-patentiq-v2-blocking-power-current-state-audit.md).

The first real family-layer rebuild after the formula correction is recorded in [68-patentiq-v2-family-blocking-power-rebuild-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/68-patentiq-v2-family-blocking-power-rebuild-audit.md).

The core rule is:

1. any mart that carries or aggregates `family_ui_blocking_power_score`,
2. any mart that carries or aggregates `family_blocking_power_score_asof`,
3. any mart that carries or aggregates `family_enforceability_score_asof`,
4. any mart that uses `family_adjusted_citation_score_raw` for UI or portfolio-facing heritage-style metrics,

must be rebuilt after the corrected Gold family scoring contract is in place.

---

## Metric Fields That Trigger Rebuild

### Family-level corrected metrics

1. `family_adjusted_citation_score_raw`
2. `family_market_threat_score_raw`
3. `family_raw_absolute_blocking_power`
4. `family_ui_blocking_power_score`
5. `family_blocking_power_score_asof`
6. `family_enforceability_score_asof`

### Portfolio-level dependent metrics

1. `portfolio_avg_blocking_power_within_mega_cluster`
2. `portfolio_hit_rate_top_decile`
3. `portfolio_crown_jewel_index`
4. `portfolio_current_threat_score`
5. `portfolio_heritage_score`
6. `portfolio_avg_blocking_power_score_asof`
7. `portfolio_total_blocking_power_score_asof`
8. `portfolio_avg_enforceability_score_asof`
9. `portfolio_top_family_blocking_share_asof`
10. `portfolio_blocking_density_asof`
11. `portfolio_enforceability_density_asof`

### Market-level dependent metrics

1. `blocking_density_asof`
2. `enforceability_density_asof`
3. `cpc_blocking_density_asof`
4. any leaderboard rank that orders on blocking or enforceability density

---

## Must Rebuild

These marts are not trustworthy to keep unchanged after the blocking-power refactor.

### Family Gold

1. `gold_family_summary.parquet`
   Stage: `gold-family-summary`
   Why: current family-facing summary output carries the current blocking and legal-strength semantics.
2. `gold_family_blocking_power.parquet`
   Stage: `gold-family-metrics`
   Why: this is the direct family blocking-power output.
3. `gold_family_heritage_summary.parquet`
   Stage: `gold-family-metrics`
   Why: it uses `family_adjusted_citation_score_raw` as a serving metric.
4. `gold_family_blocking_power_timeseries.parquet`
   Stage: `gold-history-blocking`
   Why: PIT blocking history inherits the same family blocking logic.
5. `gold_family_compare_pit.parquet`
   Stage: `gold-family-compare-pit`
   Why: it carries `family_blocking_power_score_asof` and `family_enforceability_score_asof`.
6. `gold_family_classification_jurisdiction_pit.parquet`
   Stage: `gold-family-classification-jurisdiction-pit`
   Why: it carries `family_blocking_power_score_asof` and `family_enforceability_score_asof`.
7. `gold_semantic_match_context.parquet`
   Stage: `gold-market-semantic`
   Why: it explicitly joins `family_ui_blocking_power_score`.

### Portfolio Gold

1. `gold_portfolio_summary.parquet`
   Stage: `gold-portfolio`
   Why: executive metrics inherit the current family blocking and heritage logic.
2. `gold_portfolio_field_timeseries.parquet`
   Stage: `gold-portfolio`
   Why: it aggregates enforceability and heritage contribution scores.
3. `gold_portfolio_heritage_summary.parquet`
   Stage: `gold-portfolio`
   Why: it aggregates `family_heritage_score`.
4. `gold_portfolio_forecast_summary.parquet`
   Stage: `gold-portfolio`
   Why: the portfolio forecast aggregation consumes current portfolio outputs and should be regenerated after those change, even if the underlying ML predictions are not retrained.
5. `gold_portfolio_forecast_segments.parquet`
   Stage: `gold-portfolio`
   Why: same dependency as forecast summary.
6. `gold_portfolio_forecast_contributors.parquet`
   Stage: `gold-portfolio`
   Why: same dependency as forecast summary.
7. `gold_portfolio_summary_pit.parquet`
   Stage: `gold-portfolio-summary-pit`
   Why: it aggregates family blocking and enforceability over owner-year.
8. `gold_portfolio_compare_pit.parquet`
   Stage: `gold-portfolio-compare-pit`
   Why: it carries portfolio blocking and enforceability PIT metrics.
9. `gold_portfolio_classification_mix_pit.parquet`
   Stage: `gold-portfolio-classification-mix-pit`
   Why: it contains `portfolio_blocking_density_asof` and `portfolio_enforceability_density_asof`.
10. `gold_portfolio_classification_jurisdiction_pit.parquet`
    Stage: `gold-portfolio-classification-jurisdiction-pit`
    Why: it contains `portfolio_blocking_density_asof` and `portfolio_enforceability_density_asof`.

### Market Gold

1. `gold_market_summary_pit.parquet`
   Stage: `gold-market-summary-pit`
   Why: it aggregates family blocking and enforceability into year/segment market summaries.
2. `gold_market_cpc_trend_pit.parquet`
   Stage: `gold-market-cpc-trend-pit`
   Why: it contains `cpc_blocking_density_asof`.
3. `gold_market_cpc_jurisdiction_trend_pit.parquet`
   Stage: `gold-market-cpc-jurisdiction-trend-pit`
   Why: it contains `blocking_density_asof` and `enforceability_density_asof`.
4. `gold_cpc_importance_pit.parquet`
   Stage: `gold-cpc-importance-pit`
   Why: it inherits CPC blocking density from the CPC trend mart.
5. `gold_market_leaderboard_pit.parquet`
   Stage: `gold-market-leaderboard-pit`
   Why: ranking order and density fields inherit the family blocking foundation.

---

## Logically Safe To Keep

These marts are primarily raw-evidence, classification-membership, or citation-count outputs and do not need recalculation solely because blocking power changes.

### Classification-only or replay-only

1. `gold_family_classification_mix_pit.parquet`
   Stage: `gold-family-classification-mix-pit`
   Reason: classification breadth, CPC arrays, WIPO arrays, and replay policy only.

### Citation raw-count or evidence-first Gold

1. `gold_family_citation_summary.parquet`
   Stage: `gold-family-metrics`
2. `gold_family_citation_timeseries_pit.parquet`
   Stage: `gold-family-metrics`
3. `gold_portfolio_citation_summary.parquet`
   Stage: `gold-portfolio`
4. `gold_portfolio_citation_timeseries.parquet`
   Stage: `gold-portfolio`
5. `gold_portfolio_attacker_momentum.parquet`
   Stage: `gold-portfolio`
6. `gold_portfolio_citation_pressure_by_field.parquet`
   Stage: `gold-portfolio`
7. `gold_portfolio_citation_pressure_by_jurisdiction.parquet`
   Stage: `gold-portfolio`
8. `gold_market_citation_trend_pit.parquet`
   Stage: `gold-market-semantic`
9. `gold_market_citation_pressure_by_jurisdiction_pit.parquet`
   Stage: `gold-market-semantic`
10. `gold_market_attacker_leaderboard_pit.parquet`
    Stage: `gold-market-semantic`
11. `gold_portfolio_threat_matrix.parquet`
    Stage: `gold-portfolio`
12. `gold_family_attacker_summary.parquet`
    Stage: `gold-family-metrics`

### Likely safe if the upstream market state source is unchanged

1. `gold_market_intelligence_segments.parquet`
   Stage: `gold-market-semantic`
2. `gold_market_intelligence_timeseries.parquet`
   Stage: `gold-market-semantic`
3. `gold_market_intelligence_overview.parquet`
   Stage: `gold-market-semantic`

These are copied or lightly summarized from the current market-state source and are not directly derived from family blocking power in the current implementation.

---

## Conditional Or Retrain-Dependent

These do not need rebuild purely because blocking power changes unless their own feature inputs or model outputs are intentionally refreshed.

1. `ml_prediction_family_future_citation_3y.parquet`
2. `ml_prediction_family_future_citation_5y.parquet`
3. `ml_prediction_family_jurisdiction_lapse_risk.parquet`
4. pending-grant model outputs when that pipeline is sealed for serving

Important distinction:

1. model prediction parquets do not automatically need retraining for a blocking-power refactor,
2. but portfolio forecast aggregation parquets do need rebuild because they consume changed Gold portfolio inputs.

---

## Recommended Rebuild Order

This is the minimal practical order after the blocking-power correction is implemented.

1. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-family-summary`
2. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-family-metrics`
3. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-history-blocking`
4. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-family-compare-pit`
5. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-family-classification-jurisdiction-pit`
6. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-portfolio-summary-pit`
7. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-portfolio-classification-mix-pit`
8. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-portfolio-classification-jurisdiction-pit`
9. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-portfolio-compare-pit`
10. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-portfolio`
11. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-market-summary-pit`
12. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-market-cpc-trend-pit`
13. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-market-cpc-jurisdiction-trend-pit`
14. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-cpc-importance-pit`
15. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-market-leaderboard-pit`
16. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-market-semantic`

---

## Stage-Granularity Caveat

The stage groups are coarser than the logical rebuild dependency graph.

Examples:

1. `gold-portfolio` will rebuild safe citation outputs together with required portfolio summary, heritage, and forecast outputs.
2. `gold-market-semantic` will rebuild safe market citation outputs together with the required `gold_semantic_match_context.parquet`.
3. `gold-family-metrics` will rebuild safe family citation outputs together with required blocking and heritage outputs.

So the correct reading is:

1. the `Must Rebuild` list is the logical dependency set,
2. the stage commands are the operational execution set,
3. some logically safe marts will still be regenerated incidentally because of stage grouping.

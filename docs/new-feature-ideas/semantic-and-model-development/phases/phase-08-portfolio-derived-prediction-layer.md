# Phase 08: Portfolio-Derived Prediction Layer

## Goal

Aggregate validated micro predictions into portfolio forecasts and contributor views.

## Input Data

1. micro prediction outputs from Phases 03-06
2. [silver_family_owner_bridge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet)
3. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
4. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)

## Actual Metrics Used

1. expected future citations
2. expected likely grants
3. expected lapse counts and reach loss
4. friction risk share
5. hotspot gap counts
6. top contributor dependence
7. future impact concentration HHI
8. coverage and completeness rates

## Config And Policy

1. never build executive KPIs from raw uncalibrated probabilities
2. ownership weighting is applied before aggregation
3. confidence intervals are not naive averages of family confidence
4. unsupported segments are caveated or suppressed

## Generation Logic

1. join micro prediction tables to family-owner bridge
2. apply owner weights
3. aggregate by portfolio
4. compute concentration and fragility diagnostics
5. generate summary, segment, and contributor marts

## Expected Outputs

1. `ml_portfolio_prediction_rollup.parquet`
2. refreshed [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
3. `gold_portfolio_forecast_segments.parquet`
4. `gold_portfolio_forecast_contributors.parquet`

## Where Outputs Are Consumed

1. portfolio forecast API
2. executive portfolio forecast cards
3. contributor drilldowns
4. compare workspace

## Quality Gates

1. prediction completeness `>= 90%` of effective families
2. if completeness `< 90%`, output must be caveated or suppressed
3. top-contributor dependence `> 35%` requires fragility caveat
4. unsupported-segment share `> 20%` suppresses segment rollups
5. `0` executive KPIs built from raw, uncalibrated probabilities

## Stop Conditions

1. family and application units are mixed silently
2. ownership weighting skipped
3. segments mainly driven by fallback slices
4. portfolio intervals built from naive confidence averaging

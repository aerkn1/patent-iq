# PatentIQ V2 Portfolio-Derived Prediction Layer Implementation And Serving Contract

## Goal

Record the first implemented portfolio-derived prediction layer built from the sealed lower-level model artifacts:

1. Phase 03 family future-citation forecast
2. Phase 04 family-jurisdiction lapse risk
3. Phase 06 jurisdiction-field trend forecast

This note fixes the artifact set, the output semantics, the explicit coverage policy, and the backend/UI serving expectations for the current MVP candidate release.

## Implemented Artifacts

The current portfolio-derived layer is now materialized as:

1. [ml_portfolio_prediction_rollup.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_portfolio_prediction_rollup.parquet)
2. [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
3. [gold_portfolio_forecast_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet)
4. [gold_portfolio_forecast_contributors.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_contributors.parquet)

The producing stage is:

1. [gold-portfolio.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stages/gold-portfolio.json)

The lower-level scored inputs used by this layer are:

1. [ml_prediction_family_future_citations.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_family_future_citations.parquet)
2. [ml_prediction_family_jurisdiction_lapse_risk.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_family_jurisdiction_lapse_risk.parquet)
3. [ml_prediction_jurisdiction_field_trend_forecast.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_jurisdiction_field_trend_forecast.parquet)

## Current Audit

Current live row counts:

1. summary rows: `3,034,400`
2. segment rows: `11,040,482`
3. contributor rows: `17,866,740`
4. rollup rows: `3,034,400`

Current portfolio-wide average coverage:

1. average `Phase 03` family coverage: `0.454608`
2. average `Phase 04` family coverage: `0.469497`
3. `Phase 06` current field-mix support: `3,034,400 / 3,034,400`

Current overall coverage status distribution:

1. `high`: `785,459`
2. `medium`: `239,016`
3. `low`: `2,009,925`

This confirms the same core product rule established earlier:

1. portfolio-derived outputs are usable
2. they are not safe to present without explicit coverage disclosure

## Summary Output Contract

The summary mart is the portfolio-level forecast headline payload.

It must include:

1. `aggregation_scope = family_bottom_up`
2. `phase03_family_covered_count`
3. `phase03_family_denominator_count`
4. `phase03_family_coverage_pct`
5. `phase04_family_covered_count`
6. `phase04_family_denominator_count`
7. `phase04_family_coverage_pct`
8. `phase04_avg_scored_jurisdictions_per_covered_family`
9. `phase06_current_field_mix_supported`
10. `phase06_current_field_mix_support_reason`
11. `portfolio_prediction_coverage_status`
12. `coverage_caveat_text`

Current Phase 03 portfolio outputs:

1. `portfolio_expected_future_citations_total_3y`
2. `portfolio_expected_future_citations_lower_3y`
3. `portfolio_expected_future_citations_upper_3y`
4. `portfolio_expected_future_citations_total_5y`
5. `portfolio_expected_future_citations_lower_5y`
6. `portfolio_expected_future_citations_upper_5y`
7. `portfolio_expected_future_citations_per_effective_family_3y`
8. `portfolio_expected_future_citations_per_effective_family_5y`
9. `portfolio_top_contributor_dependence_pct_3y`
10. `portfolio_top_contributor_dependence_pct_5y`

Current Phase 04 portfolio outputs:

1. `portfolio_expected_lapses_count_12m`
2. `portfolio_expected_lapses_count_24m`
3. `portfolio_limited_support_share_12m`
4. `portfolio_limited_support_share_24m`

Current Phase 06 portfolio outputs:

1. `portfolio_heating_market_exposure_count_3y`
2. `portfolio_cooling_market_exposure_count_3y`
3. `portfolio_hotspot_coverage_pct_3y`
4. `portfolio_heating_market_exposure_count_5y`
5. `portfolio_cooling_market_exposure_count_5y`
6. `portfolio_hotspot_coverage_pct_5y`

## Segment Output Contract

[gold_portfolio_forecast_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet) is the portfolio x field x horizon market-direction overlay.

It must be used for:

1. portfolio field hotspot cards
2. heating/cooling field tables
3. portfolio market-exposure drawers

Current key fields:

1. `owner_name_harmonized`
2. `snapshot_date`
3. `horizon`
4. `wipo_field`
5. `portfolio_active_family_count_in_field`
6. `predicted_direction_band`
7. `support_level`
8. `predicted_growth_rate_reference`
9. `predicted_count_reference`

Serving rule:

1. `predicted_direction_band` is the primary product output
2. `predicted_count_reference` is secondary only

## Contributor Output Contract

[gold_portfolio_forecast_contributors.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_contributors.parquet) is the drill-down evidence mart.

It must support:

1. top future-citation contributor families
2. top lapse-risk contributor family-jurisdiction rows
3. contributor dependence and concentration UI

Current key fields:

1. `contributor_scope`
2. `horizon`
3. `contributor_entity_id`
4. `jurisdiction_code`
5. `contribution_value`
6. `contribution_share`
7. `contributor_rank`

Current supported scopes:

1. `phase03_future_citations`
2. `phase04_lapse_risk`
3. pending-grant is not yet part of the current canonical contributor mart because the lower-level model remains candidate-only

## Product Rules

The lower-level serving rules still apply after portfolio aggregation.

### Phase 03

1. portfolio citation outlook is `interval-first`
2. exact totals must not be shown without interval context
3. copy must remain directional, not literal count-certainty

### Phase 04

1. portfolio lapse risk is `risk-band-first`
2. probability-heavy interpretation must be downgraded as limited-support share rises
3. branch-level contributor drill-down must remain available

### Phase 06

1. market direction is the real output
2. raw filing-count references are secondary only
3. current field-mix support caveat must remain visible

### Pending-grant candidate

1. pending-grant is not yet part of the canonical MVP portfolio forecast mart
2. if exposed internally, it must be `rank/percentile-first`
3. raw `12m/24m` probabilities are subordinate detail only
4. exact expected likely-grant counts must remain suppressed until the lower-level model is sealed

## Coverage Policy

Current policy is:

1. `high` when the weaker of Phase 03 and Phase 04 coverage is `>= 0.75`
2. `medium` when the weaker coverage is `>= 0.50` and `< 0.75`
3. `low` when the weaker coverage is `< 0.50`

Backend must always return:

1. `portfolio_prediction_coverage_status`
2. `coverage_caveat_text`

Frontend must always:

1. render coverage status beside the headline aggregate
2. visually downgrade `low` coverage summaries
3. avoid strong portfolio-to-portfolio comparisons without visible coverage context

## Current MVP Status

This portfolio-derived layer is now:

1. implemented
2. audited
3. acceptable for MVP/backend wiring

It is not yet full historical owner-truth forecasting.

The known caveats remain:

1. coverage is partial for many portfolios
2. owner history is still replay-based outside the known supported slices
3. Phase 06 remains direction-band-first rather than count-truth-first
4. pending-grant remains candidate-only and is not yet part of the public Phase 08 serving contract

## Next Use

This layer is now the correct backend-facing source for:

1. portfolio forecast overview cards
2. contributor drilldowns
3. portfolio heating/cooling exposure panels
4. portfolio prediction export/download payloads

The next step after this layer is no longer ETL design uncertainty.

The next step is backend V2 contract implementation against these sealed and aggregated artifacts.

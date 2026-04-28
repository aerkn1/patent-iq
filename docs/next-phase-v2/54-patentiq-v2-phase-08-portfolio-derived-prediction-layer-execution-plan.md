# PatentIQ V2 Phase 08 Portfolio-Derived Prediction Layer Execution Plan

## Goal

Define the full standalone execution plan for `Phase 08` as the portfolio-level aggregation layer built on validated lower-level prediction scopes.

This note is broader than the already-implemented precursor layer.

It defines:

1. the intended complete Phase 08 scope
2. what input coverage is actually available now
3. what is already implemented
4. what is still blocked
5. the recommended promotion path from current precursor to fuller standalone Phase 08
6. the current scope decision to exclude the friction branch and prioritize pending-grant incorporation next

## Phase 08 Purpose

Phase 08 is not a direct top-level company model.

It is the portfolio-level prediction layer that must aggregate lower-level outputs into:

1. portfolio future citation outlook
2. portfolio legal attrition outlook
3. portfolio pending-grant pipeline outlook
4. portfolio market-direction exposure
5. contributor concentration and fragility diagnostics
6. portfolio-level confidence, support, and coverage disclosure

The product must continue to treat this layer as:

1. `family_bottom_up`
2. `branch_bottom_up` where jurisdiction-level legal predictions participate
3. explicitly coverage-qualified

## Intended Full Input Stack

The intended full Phase 08 stack from the original phase note and forecast semantics is:

1. `Phase 03` family future-citation forecasts
2. publication or branch-level pending-grant forecasts
3. `Phase 04` family x jurisdiction lapse-risk forecasts
4. `Phase 06` jurisdiction x field trend forecasts
6. [silver_family_owner_bridge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet)
7. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
8. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)
9. [gold_portfolio_compare_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_compare_pit.parquet) where historical/current support caveats matter

The original broader concept also mentioned friction.

Current planning decision:

1. do `not` treat friction as part of the planned near-term Phase 08 target
2. keep friction out until a later explicit product decision reintroduces it
3. prioritize `pending-grant` as the next Phase 08 extension branch instead

## Current Input Availability Audit

### Present now

The following current Phase 08 inputs exist on disk and are usable:

1. [ml_prediction_family_future_citations.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_family_future_citations.parquet)
2. [ml_prediction_family_jurisdiction_lapse_risk.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_family_jurisdiction_lapse_risk.parquet)
3. [ml_prediction_jurisdiction_field_trend_forecast.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_jurisdiction_field_trend_forecast.parquet)
4. [silver_family_owner_bridge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet)
5. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
6. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)
7. [gold_portfolio_compare_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_compare_pit.parquet)

### Missing now

The following planned next-step Phase 08 input is not yet available:

1. a sealed pending-grant prediction artifact

So the current truthful position is:

1. `citation outlook`: available
2. `coverage attrition outlook`: available
3. `market-direction exposure`: available in narrowed form
4. `grant pipeline`: unavailable
5. `friction exposure`: intentionally excluded from the current planned Phase 08 target

Important update:

1. the lower-level pending-grant artifact now exists as a trained `candidate`,
2. but it is still not sealed strongly enough to promote into the current executable Phase 08 product contract,
3. so Phase 08 should still treat grant-pipeline as `not yet executable honestly` for public-serving use.

## Current Coverage Reality

The already-implemented precursor layer gives the best current full-population read.

From [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet):

1. owner rows: `3,034,400`
2. average `Phase 03` family coverage: `0.454608`
3. average `Phase 04` family coverage: `0.469497`
4. `Phase 03` non-zero coverage share: `0.505226`
5. `Phase 04` non-zero coverage share: `0.541640`
6. `Phase 06` current field-mix support: `3,034,400 / 3,034,400`

Coverage status distribution:

1. `high`: `785,459`
2. `medium`: `239,016`
3. `low`: `2,009,925`

Coverage-band counts by lower-level scope:

`Phase 03`
1. `high`: `1,272,255`
2. `medium`: `156,508`
3. `low`: `1,605,637`

`Phase 04`
1. `high`: `1,266,649`
2. `medium`: `248,300`
3. `low`: `1,519,451`

So the full standalone Phase 08 plan must assume:

1. partial family coverage is a structural fact, not an edge case
2. full-portfolio interpretation is unsafe without coverage metadata
3. Phase 06 support is current-slice-safe, not all-years-safe

## What Is Already Implemented

The current precursor layer is materially real:

1. [ml_portfolio_prediction_rollup.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_portfolio_prediction_rollup.parquet)
2. [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
3. [gold_portfolio_forecast_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet)
4. [gold_portfolio_forecast_contributors.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_contributors.parquet)

These already cover:

1. Phase 03 portfolio future-citation intervals and contributor dependence
2. Phase 04 expected lapse counts and limited-support share
3. Phase 06 field-direction overlays and current hotspot exposure
4. phase-specific coverage fields
5. coverage caveats and combined coverage status

This current layer is documented in:

1. [53-patentiq-v2-portfolio-derived-prediction-layer-implementation-and-serving-contract.md](./53-patentiq-v2-portfolio-derived-prediction-layer-implementation-and-serving-contract.md)

## Intended Full Standalone Phase 08 Outputs

Once Phase 08 is treated as a full standalone layer, it should own:

1. `ml_portfolio_prediction_rollup.parquet`
2. [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
3. [gold_portfolio_forecast_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet)
4. [gold_portfolio_forecast_contributors.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_contributors.parquet)
5. later:
   - `gold_portfolio_grant_pipeline_forecast.parquet`
   once the lower-level grant-pipeline artifact exists honestly

## Full Metric Contract

### Already executable now

#### Citation outlook

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

#### Coverage attrition outlook

1. `portfolio_expected_lapses_count_12m`
2. `portfolio_expected_lapses_count_24m`
3. `portfolio_limited_support_share_12m`
4. `portfolio_limited_support_share_24m`

#### Market-direction exposure

1. `portfolio_heating_market_exposure_count_3y`
2. `portfolio_cooling_market_exposure_count_3y`
3. `portfolio_hotspot_coverage_pct_3y`
4. `portfolio_heating_market_exposure_count_5y`
5. `portfolio_cooling_market_exposure_count_5y`
6. `portfolio_hotspot_coverage_pct_5y`

### Not executable honestly yet

#### Pending grant pipeline

Still blocked for honest product serving because no sealed pending-grant artifact exists yet.

Do not expose yet:

1. `portfolio_expected_likely_grants_count`
2. `portfolio_expected_likely_grants_by_jurisdiction`
3. `portfolio_expected_likely_grants_by_field`
4. `portfolio_grant_pipeline_density`

If internal or exploratory use is needed before sealing, the only acceptable candidate-only alternatives are:

1. `portfolio_pending_pipeline_percentile`
2. `portfolio_pending_pipeline_rank_within_peer_set`
3. `portfolio_top_pending_branch_shortlist`
4. `portfolio_pending_pipeline_priority_tier`

Do **not** headline:

1. exact expected likely-grant counts,
2. exact pending-branch grant probabilities,
3. executive-facing portfolio conversion totals

until the pending-grant lower-level model is sealed.

## Coverage And Confidence Contract

Standalone Phase 08 must continue to require:

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

Recommended continuation of the current coverage policy:

1. `high` when the weaker of `Phase 03` and `Phase 04` coverage is `>= 0.75`
2. `medium` when the weaker coverage is `>= 0.50` and `< 0.75`
3. `low` when the weaker coverage is `< 0.50`

## Guardrails

Standalone Phase 08 must keep these rules:

1. never imply one direct company model if the output is bottom-up aggregation
2. never show Phase 03 totals without interval context
3. never show Phase 04 as pure exact-probability truth when limited-support share is large
4. never present Phase 06 as exact future filing-count truth
5. never expose grant-pipeline metrics until a real grant model exists
6. never expose friction metrics until a real proxy or model artifact exists
7. never hide coverage metadata

## Quality Gates

To treat standalone Phase 08 as fully plan-complete, require:

1. all current precursor marts build reproducibly
2. coverage fields are present and non-null
3. contributor drill-down rows exist for every non-null aggregate family/branch scope
4. portfolio-to-portfolio comparison can be coverage-qualified
5. blocked metric groups are either absent or explicitly marked unsupported

To expand Phase 08 beyond the current precursor, additionally require:

1. a sealed pending-grant lower-level artifact

## Execution Path

### Current implemented path

1. score Phase 03 family predictions
2. score Phase 04 family-jurisdiction predictions
3. join current Phase 06 direction outputs
4. aggregate to portfolio summary, segment, and contributor marts
5. compute phase-specific coverage and caveats

### Full standalone completion path

1. freeze current precursor as `Phase 08 core`
2. add a pending-grant lower-level input when such a model exists
3. extend contributor and segment marts for grant-pipeline scope
4. only then declare the planned Phase 08 target complete

## Current Project Status

The correct current label is:

1. `Phase 08 core implemented`
2. `planned full Phase 08 target not yet complete`

Meaning:

1. the standalone portfolio-derived prediction layer is now real and backend-usable
2. but its current honest scope is limited to `03 + 04 + 06`
3. the pending-grant branch remains the main missing planned extension
4. the friction branch is intentionally excluded from the current near-term plan

## Bottom Line

The current warehouse and model stack are sufficient for a real standalone Phase 08 core.

They are not yet sufficient for the planned next Phase 08 extension because the pending-grant lower-level model does not exist.

So the honest planning stance is:

1. `Phase 08 core`: ready and implemented
2. `Phase 08 next extension`: pending-grant pipeline
3. `Phase 08 friction branch`: intentionally out of the current plan

The standalone upstream plan for the next extension is:

1. [55-patentiq-v2-pending-grant-pipeline-execution-plan.md](./55-patentiq-v2-pending-grant-pipeline-execution-plan.md)

# PatentIQ V2 Post-Phase-04 Prioritization And Next Execution Path

## Goal

Lock the recommended next path after sealing:

1. Phase 03 family future-citation forecast
2. Phase 04 family-jurisdiction lapse risk
3. dense family and Gold PIT product layer

This note clarifies what should be executed next, what should be deferred, and why.

## Current Position

The following are now materially complete for MVP-candidate scope:

1. semantic family search and comparison runtime
2. Phase 03 sealed citation forecast candidate
3. Phase 04 sealed lapse-risk candidate
4. family, portfolio, and market PIT serving marts

The next execution target should therefore maximize:

1. real added product value
2. training honesty
3. reuse of existing Silver and Gold timeseries
4. downstream leverage for portfolio and market surfaces

## Why Phase 05 Is Not The Best Immediate Next Model

Phase 05 remains useful as a product concept, but it is not the strongest next supervised model.

Current live evidence:

1. [silver_legal_status_event_ledger.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet) contains `0` materialized `is_opposition_event` positives
2. EP chronology is likely reconstructible from:
   - [bronze_reg130_opponent.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg130_opponent.parquet)
   - [bronze_reg125_appeal.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg125_appeal.parquet)
   - [silver_ep_register_core.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet)
3. non-EP dated friction chronology is not currently present in a defensible form

So a full supervised `family_friction_risk` model would currently be:

1. too EP-skewed if forced
2. weaker than the next available alternatives
3. less useful than a transparent evidence-weighted proxy

## Recommended Next Order

The next execution order should be:

1. `Phase 06` jurisdiction-field trend forecast
2. `Phase 08 precursor` portfolio-derived rollups from sealed Phase 03 and Phase 04 outputs, with explicit model coverage disclosure
3. `Phase 05 Track A` friction proxy
4. `EP chronology` as descriptive legal intelligence and future Track B preparation

## Why Phase 06 Is The Best Next Model

Phase 06 is better supported by the current warehouse than Phase 05.

Strong current inputs:

1. [silver_local_tech_trends_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet)
2. [silver_global_tech_trends_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet)
3. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)
4. [gold_market_summary_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet)

Why it is stronger:

1. the underlying chronology is already explicit
2. the target is naturally time-series-like and observed
3. the model output has immediate product value in Market Intelligence and portfolio hotspot views
4. it also becomes a direct upstream for the later portfolio-derived prediction layer

## Product Value Ranking

Highest-value next deliverables from existing data are:

1. `Phase 06 trend forecast`
   - jurisdiction-field hotspots
   - cooling/heating segment forecast
   - future market overlays
2. `portfolio-derived prediction layer`
   - expected portfolio citation mass
   - lapse-risk exposure
   - top forecast contributors
   - fragility and gap overlays
3. `friction proxy`
   - attacker pressure
   - EP opposition badge where available
   - challenge susceptibility evidence
4. `EP chronology`
   - opposition and appeal drilldowns
   - descriptive legal intelligence

## Immediate Execution Path

Execute in this order:

1. document the reprioritization and Phase 06 execution contract
2. scaffold the ETL-side `Phase 06` label / feature / split stage
3. run the first live Phase 06 baseline
4. seal or caveat Phase 06 depending on reliability
5. then build the first `Phase 08 precursor` rollups from sealed 03 / 04 / 06 outputs
6. every portfolio-derived rollup must carry phase-specific coverage fields and caveats

## Execution Status

This path is now materially executed.

Completed:

1. `Phase 06` was built, reframed to direction-band-first, and sealed as an MVP candidate
2. the first `Phase 08 precursor` portfolio-derived layer was built from sealed `03 / 04 / 06` outputs
3. explicit portfolio coverage fields are now live in:
   - [ml_portfolio_prediction_rollup.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_portfolio_prediction_rollup.parquet)
   - [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
4. segment and contributor drilldowns are now live in:
   - [gold_portfolio_forecast_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet)
   - [gold_portfolio_forecast_contributors.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_contributors.parquet)

Current live audit:

1. summary rows: `3,034,400`
2. average `Phase 03` portfolio coverage: `0.454608`
3. average `Phase 04` portfolio coverage: `0.469497`
4. coverage status distribution:
   - `high`: `785,459`
   - `medium`: `239,016`
   - `low`: `2,009,925`

The dedicated implementation note is:

1. [53-patentiq-v2-portfolio-derived-prediction-layer-implementation-and-serving-contract.md](./53-patentiq-v2-portfolio-derived-prediction-layer-implementation-and-serving-contract.md)

## Explicit Deferrals

Defer for now:

1. supervised global Phase 05 friction-risk model
2. broad historical OECD backprojection work
3. true historical owner-membership reconstruction
4. backend/UI implementation beyond contract alignment for these new model outputs

## What Still Belongs In Scope

This reprioritization does not remove Phase 05 from scope.

It changes the order:

1. proxy first
2. chronology build second
3. supervised predictive Phase 05 only after dated friction labels exist

## Resulting Program Stance

PatentIQ V2 should now treat the near-term post-Phase-04 roadmap as:

1. `Phase 06` as the next real model
2. `Phase 08 precursor` as the next high-value aggregation layer
3. `Phase 05 proxy + EP chronology` as the honest friction path

This is the most data-supported and product-useful route from the current warehouse state.

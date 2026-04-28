# PatentIQ V2 Phase 03 Seal Decision And Accepted Caveats

## Goal

Record the explicit decision for the current `Phase 03` family future-citation forecast artifacts so the project can move forward without pretending the models are fully production-promoted.

This note seals the current artifacts as:

1. `accepted MVP candidate release`
2. `usable for backend and product planning`
3. `not yet fully promoted production under the strict subgroup gate`

## Decision

Phase 03 is accepted as a sealed candidate release for MVP and demo use.

Decision label:

1. `sealed_candidate_accepted_for_mvp`

This is not the same as:

1. `fully promoted production`

## Why The Decision Is Acceptable

The current live artifact set now satisfies the hard methodological requirements that mattered most:

1. point-in-time family feature enrichment is applied
2. observed-snapshot filtering is explicit
3. leakage-sensitive features in the Phase 03 manifest are `0`
4. both horizons train successfully on the live corpus
5. both horizons now have acceptable overall interval calibration

## Current Accepted Metrics

Current live metrics from the sealed run are approximately:

1. `3y Spearman ≈ 0.454`
2. `3y interval_coverage_80pct ≈ 0.793`
3. `5y Spearman ≈ 0.614`
4. `5y interval_coverage_80pct ≈ 0.801`

These are strong enough to support:

1. MVP family forecast demonstrations
2. backend contract design
3. portfolio bottom-up aggregation planning
4. report and explanation planning

## Why It Is Not Fully Promoted Production

The remaining blocker is subgroup reliability by `primary_wipo_field`.

Current live subgroup ranges are still too wide:

1. `3y` field coverage is roughly `0.634 .. 0.862`
2. `5y` field coverage is roughly `0.667 .. 0.870`

So the strict promotion gate from [42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md) is still not fully satisfied.

## Accepted Caveats

These caveats must travel with the sealed Phase 03 release:

1. treat the models as `accepted candidate`, not final production authority
2. always return confidence/caveat metadata in serving responses
3. do not suppress legal-status context beside the forecast
4. do not claim field-uniform reliability
5. do not treat the point estimate as literal exact-count truth
6. do not use the current artifact as the sole basis for irreversible strategic automation

## Serving Rules

The backend and product should use the Phase 03 release under these rules:

1. prediction unit remains `docdb_family_id`
2. model outputs must include:
   - point forecast
   - interval
   - feature completeness
   - legal/status context
   - model version
   - calibration method
   - caveats
3. UI emphasis should be:
   - interval
   - directional outlook
   - rank/relative strength
   before exact raw count
4. portfolio forecasts should aggregate these family outputs bottom-up
5. UI copy should frame the result as:
   - `future citation outlook`
   - not `guaranteed value`

## Artifact Set Covered By This Decision

The sealed candidate decision covers:

1. [family_future_citation_forecast_3y_model.txt](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt)
2. [family_future_citation_forecast_5y_model.txt](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt)
3. [family_future_citation_forecast_3y_bundle.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_bundle.json)
4. [family_future_citation_forecast_5y_bundle.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_bundle.json)
5. [family_future_citation_forecast_calibration.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json)
6. [model_card_family_future_citation_forecast.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json)
7. [ml_model_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet)
8. [ml_experiment_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet)
9. [ml_calibration_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet)

## What Happens Next

Because Phase 03 is now sealed for MVP, the next work should move in parallel tracks:

1. continue product-scope PIT generation beyond the family core
2. plan Phase 04 family x jurisdiction lapse risk

Do not spend more time on Phase 03 subgroup tightening unless one of these happens:

1. a later serving test shows clearly harmful field bias
2. Phase 08 aggregation exposes unacceptable downstream instability
3. a final production promotion pass is required after the rest of the modeling stack is complete

## Bottom Line

The correct project label for Phase 03 is:

1. `sealed candidate`
2. `accepted for MVP`
3. `not yet final promoted production`

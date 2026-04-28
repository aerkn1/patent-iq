# PatentIQ V2 Phase 06 Seal Decision And Serving Contract

## Goal

Record the explicit decision for the current `Phase 06` jurisdiction-field trend artifacts so backend and UI can consume them consistently without overstating reliability.

This note seals the current artifacts as:

1. `accepted MVP candidate release`
2. `usable for backend and product wiring`
3. `not yet fully promoted production trend authority`

## Decision

Phase 06 is accepted as a sealed candidate release for MVP and demo use.

Decision label:

1. `sealed_candidate_accepted_for_mvp`

This is not the same as:

1. `fully promoted production`

## Why The Decision Is Acceptable

The current live artifact set is good enough for MVP under a narrowed contract:

1. the model is now explicitly `direction-band-first`
2. train, validation, and test splits are materialized and reproducible
3. naive carry-forward and growth-first alternatives were tested and did not beat the current direction-first framing
4. the prediction artifacts already carry:
   - `predicted_direction_band`
   - `trend_strength_band`
   - `support_level`
   - probability references
   - count references
5. the product can use the outputs as market-direction evidence rather than exact filing-count truth

## Current Accepted Metrics

Current live metrics from [model_card_jurisdiction_field_trend_forecast.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_jurisdiction_field_trend_forecast.json):

1. `3y class_accuracy ≈ 0.542`
2. `3y balanced_accuracy ≈ 0.626`
3. `3y macro_f1 ≈ 0.542`
4. `5y class_accuracy ≈ 0.727`
5. `5y balanced_accuracy ≈ 0.863`
6. `5y macro_f1 ≈ 0.587`

These are strong enough to support:

1. direction-oriented market storytelling
2. hotspot / cooling-segment overlays
3. portfolio context and narrative layers
4. backend contract and UI state design

## Why It Is Not Fully Promoted Production

The remaining blockers are support calibration and class-imbalance stability.

Current live audit from [phase06_direction_first_audit.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/phase06_direction_first_audit.json) shows:

1. `3y strong` band is not more reliable than `moderate`
2. `5y` test behavior is helped by a cooling-heavy class mix
3. the current support policy resolves to `limited` across the held-out slice
4. raw count remains unsuitable as the primary promised output

So the strict production interpretation gate is still not satisfied.

## Accepted Caveats

These caveats must travel with the sealed Phase 06 release:

1. treat the models as `accepted candidate`, not final production authority
2. use the outputs primarily as `direction + state` rather than exact market-size truth
3. keep `trend_strength_band` secondary and caveated
4. default `support_level` to `limited` unless later evidence materially improves support policy
5. do not use the current artifact as the sole basis for irreversible investment or strategy automation

## Backend Serving Rules

The backend should return a horizon-explicit trend response with:

1. `jurisdiction_code`
2. `wipo_industry_code`
3. `as_of_year`
4. `horizon`
5. `predicted_direction_band`
6. `trend_strength_band`
7. `support_level`
8. `predicted_direction_probability`
9. `predicted_margin`
10. `predicted_growth_rate_reference`
11. `predicted_count_reference`
12. `actual_direction_band` when present in audit/debug mode only
13. `model_version`
14. `calibration_method`
15. `caveats`

### Direction-band-first rule

All product-facing consumers should emphasize:

1. `heating / stable / cooling`
2. the supporting explanation for why
3. a caveat-aware support label

Do not make raw future filing count the primary visual or API promise.

### Strength-band rule

Use `trend_strength_band` only as a secondary qualifier:

1. it may be shown
2. it must never outrank `predicted_direction_band`
3. it should be visually downgraded when `support_level = limited`

### Support-level rule

For the current sealed version:

1. backend should allow `support_level`
2. UI should assume most rows are `limited`
3. stronger support labels should not be implied unless a later recalibration explicitly changes the policy

## UI Rules

### Market Intelligence pages

Show:

1. `predicted_direction_band` as the primary chip or badge
2. `trend_strength_band` as secondary text or subdued chip
3. `support_level` badge with explicit caveat language
4. optional `predicted_growth_rate_reference`

Do not:

1. headline the segment with a predicted raw filing count
2. imply strong confidence when `support_level = limited`
3. present this as a deterministic hotspot authority

### Portfolio context

Portfolio and compare pages may aggregate:

1. count of heating segments
2. count of cooling segments
3. share of portfolio exposure in heating vs cooling areas
4. top directional contributors

But they must include:

1. share of rows with `limited` support
2. clear caveat that the signal is direction-first, not exact-count-first

## Artifact Set Covered By This Decision

The sealed candidate decision covers:

1. [jurisdiction_field_trend_forecast_3y_model.txt](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/jurisdiction_field_trend_forecast_3y_model.txt)
2. [jurisdiction_field_trend_forecast_5y_model.txt](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/jurisdiction_field_trend_forecast_5y_model.txt)
3. [jurisdiction_field_trend_forecast_3y_bundle.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/jurisdiction_field_trend_forecast_3y_bundle.json)
4. [jurisdiction_field_trend_forecast_5y_bundle.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/jurisdiction_field_trend_forecast_5y_bundle.json)
5. [jurisdiction_field_trend_forecast_direction_calibration.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/jurisdiction_field_trend_forecast_direction_calibration.json)
6. [phase06_direction_first_audit.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/phase06_direction_first_audit.json)
7. [model_card_jurisdiction_field_trend_forecast.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_jurisdiction_field_trend_forecast.json)
8. [ml_model_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet)
9. [ml_experiment_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet)
10. [ml_calibration_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet)

## What Happens Next

Because Phase 06 is now sealed for MVP, the next work should be:

1. use these outputs in backend V2 contracts as `direction-band-first`
2. wire Market Intelligence and portfolio context UIs against the narrowed serving rules
3. treat `trend_strength_band` as a soft qualifier, not an authority signal
4. revisit support-policy and balanced-class reliability later if final production promotion is required

## Bottom Line

The correct project label for Phase 06 is:

1. `sealed candidate`
2. `accepted for MVP`
3. `direction-band-first`
4. `not yet final promoted production`

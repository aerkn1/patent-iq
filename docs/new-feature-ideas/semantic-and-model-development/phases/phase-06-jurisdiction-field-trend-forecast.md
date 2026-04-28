# Phase 06: Jurisdiction-Field Trend Forecast

## Goal

Forecast short-horizon market momentum at jurisdiction-by-field level.

## Input Data

1. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)
2. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)
3. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)

## Actual Metrics Used

1. historical filing velocity
2. historical grant velocity
3. multi-year acceleration
4. field and jurisdiction anchors
5. fragmentation and concentration metrics when available

## Config And Policy

1. prediction unit is `jurisdiction_code x wipo_field x year`
2. use rolling-origin evaluation
3. horizon limited to `3y` or `5y`
4. forecasts must respect non-negativity

## Training Logic

1. build trend labels from time series
2. materialize lag and acceleration features
3. train bounded time-series or tabular forecast model
4. calibrate intervals
5. surface hotspots, cooling zones, and portfolio gap overlays

## Expected Outputs

1. `ml_label_jurisdiction_field_trend_future.parquet`
2. `ml_feature_jurisdiction_field_trend_forecast.parquet`
3. `ml_prediction_jurisdiction_field_trend_forecast.parquet`

## Where Outputs Are Consumed

1. portfolio hotspot and gap views
2. market intelligence overlays
3. future segment prioritization

## Quality Gates

1. non-negativity violation rate `0`
2. sign-of-acceleration accuracy `>= 0.65`
3. 80% interval coverage between `76%` and `84%`
4. MAPE `<= 25%` on stable cohorts
5. MAPE `<= 35%` on volatile cohorts

## Stop Conditions

1. rolling-origin performance collapses versus random split
2. unsupported sparse segments dominate released hotspot outputs
3. model predicts negative volumes

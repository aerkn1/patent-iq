# PatentIQ V2 Phase 06 Jurisdiction-Field Trend Forecast Execution Plan

## Goal

Build the first practical execution contract for `Phase 06`:

1. prediction grain
2. label table
3. feature table
4. split policy
5. baseline model family
6. output artifacts
7. quality gates

The purpose of Phase 06 is to forecast short-horizon market momentum at the:

1. `jurisdiction_code x wipo_industry_code x as_of_year`

level.

## Why Phase 06 Is The Next Model

Phase 06 is the strongest next supervised model after sealed Phases 03 and 04 because the source chronology already exists in compact timeseries form.

Current live inputs:

1. [silver_local_tech_trends_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet)
   - `21,488` rows
   - `1956..2025`
2. [silver_global_tech_trends_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet)
   - `504` rows
   - `1956..2025`
3. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)
4. [gold_market_summary_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet)

## Current Status

Phase 06 is now `implemented and sealed as a narrowed MVP candidate`, but it is not fully promoted production.

What is already strong enough:

1. local jurisdiction-field filing history
2. global field history
3. market heat-state context
4. compact segment-year cardinality suitable for fast iteration

What is now built:

1. Phase 06 label parquet
2. Phase 06 feature parquet
3. Phase 06 split registry
4. Phase 06 model artifacts
5. Phase 06 prediction parquet

Live first-pass outputs now exist at:

1. [ml_label_jurisdiction_field_trend_future.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_jurisdiction_field_trend_future.parquet)
2. [ml_feature_jurisdiction_field_trend_forecast.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_jurisdiction_field_trend_forecast.parquet)
3. [ml_split_registry_phase06.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase06.parquet)
4. [ml_prediction_jurisdiction_field_trend_forecast.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_jurisdiction_field_trend_forecast.parquet)
5. [model_card_jurisdiction_field_trend_forecast.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_jurisdiction_field_trend_forecast.json)

Current live read:

1. rows:
   - labels: `16,435`
   - features: `16,435`
   - predictions: `32,870`
2. split sizes per horizon:
   - train: `8,650`
   - validation: `1,730`
   - test: `1,730`
3. current baseline metrics:
   - `3y` direction accuracy: `0.4272`
   - `3y` interval coverage: `0.7277`
   - `3y` MAPE: `13.83`
   - `5y` direction accuracy: `0.7000`
   - `5y` interval coverage: `0.7682`
   - `5y` MAPE: `189.47`

So Phase 06 is currently:

1. structurally implemented
2. useful as a live contract and artifact lane
3. sealed only under a conservative `direction-band-first` serving contract
4. not yet good enough for full production promotion

## Native Grain

The native prediction row should be:

1. `jurisdiction_code`
2. `wipo_industry_code`
3. `as_of_year`

Recommended model scope name:

1. `jurisdiction_field_trend_forecast`

## Prediction Targets

After the first live baseline and comparison audit, the recommended promoted targets are now:

1. `future_direction_3y`
2. `future_direction_5y`

Raw-count and growth labels should remain as supporting fields:

1. `future_local_family_filings_3y`
2. `future_local_family_filings_5y`
3. `future_local_growth_rate_3y`
4. `future_local_growth_rate_5y`

The primary Phase 06 product contract should optimize for:

1. `trend_direction_band`
2. `trend_strength_band`
3. `support_level`

not literal raw count as the main promise.

## Label Table

Expected first label artifact:

1. `ml_label_jurisdiction_field_trend_future.parquet`

Recommended columns:

### Identity

1. `jurisdiction_code`
2. `wipo_industry_code`
3. `as_of_year`
4. `training_snapshot_id`
5. `method_version`

### Current observed state

1. `local_family_filings_asof`
2. `global_family_filings_asof`
3. `local_growth_rate_asof`
4. `global_growth_rate_asof`
5. `local_trend_coefficient_asof`
6. `global_trend_coefficient_asof`

### Future labels

1. `future_local_family_filings_3y`
2. `future_local_family_filings_5y`
3. `future_local_growth_rate_3y`
4. `future_local_growth_rate_5y`
5. `future_direction_3y`
6. `future_direction_5y`
7. `is_observed_3y`
8. `is_observed_5y`

## Feature Table

Expected first feature artifact:

1. `ml_feature_jurisdiction_field_trend_forecast.parquet`

Recommended feature families:

### Identity and anchors

1. `jurisdiction_code`
2. `wipo_industry_code`
3. `as_of_year`
4. `field_age_years`
5. `method_version`

### Local trend state

1. `local_family_filings_asof`
2. `prior_period_local_family_filings`
3. `local_growth_rate_asof`
4. `local_trend_coefficient_asof`
5. `local_growth_rate_lag1`
6. `local_growth_rate_lag2`
7. `local_family_filings_lag1`
8. `local_family_filings_lag2`
9. `local_acceleration_1y`
10. `local_acceleration_2y`
11. `local_volatility_3y`
12. `local_volatility_5y`

### Global field context

1. `global_family_filings_asof`
2. `prior_period_global_family_filings`
3. `global_growth_rate_asof`
4. `global_trend_coefficient_asof`
5. `global_growth_rate_lag1`
6. `global_growth_rate_lag2`
7. `global_acceleration_1y`
8. `global_volatility_3y`

### Relative positioning

1. `local_to_global_share_asof`
2. `local_minus_global_growth_spread`
3. `local_minus_global_trend_spread`
4. `is_major_office`
5. `is_ep`
6. `is_us`
7. `is_cn`
8. `is_jp`
9. `is_kr`

### Market-state overlays

1. `segment_heat_state_asof`
2. `segment_family_count_asof`
3. `segment_growth_proxy_asof`

The first baseline should stay compact and tabular. It should not depend on a complex sequence model.

## Split Policy

Use a grouped time split by `as_of_year`.

Recommended first policy:

1. train: older fully observed cohorts
2. validation: next contiguous year block
3. test: latest fully observed year block
4. unassigned_recent: rows whose forecast horizon is not fully closed

First practical horizon-safe policy:

1. `3y`
   - train: `<= 2016`
   - validation: `2017..2018`
   - test: `2019..2020`
   - unassigned_recent: `>= 2021`
2. `5y`
   - same shared split registry, but evaluation only on rows with `is_observed_5y = true`

Expected split artifact:

1. `ml_split_registry_phase06.parquet`

## Baseline Model Family

The first live raw-count baseline was useful for diagnosis, but it should not remain the promoted Phase 06 core.

Recommended promoted baseline:

1. `LightGBMClassifier`
2. multiclass target:
   - `cooling`
   - `stable`
   - `heating`

Why:

1. direction-first materially matches the observed product value better
2. it is more stable than raw count under heavy-tail and drift
3. it maps directly to hotspot and cooling surfaces
4. it gives a natural route to confidence and strength bands

Recommended first hyperparameters:

1. `objective = multiclass`
2. `num_class = 3`
3. `n_estimators = 500`
4. `learning_rate = 0.05`
5. `num_leaves = 31`
6. `max_depth = 6`
7. `min_child_samples = 20`
8. `subsample = 0.8`
9. `subsample_freq = 1`
10. `colsample_bytree = 0.8`
11. `reg_alpha = 0.1`
12. `reg_lambda = 0.1`
13. `random_state = 42`

## Challenger Options

Only after the baseline is live:

1. simple horizon-specific linear baseline for calibration sanity
2. Poisson-style count regressor
3. field-specific residual correction layer

Do not start with:

1. deep sequence models
2. multi-output transformer forecasting
3. complex hierarchical Bayesian stacks

## Intervals And Calibration

Serve Phase 06 as direction-first and band-first.

Recommended first calibration:

1. class-probability calibration where useful
2. confidence-margin thresholds for `trend_strength_band`
3. support thresholds for `support_level`

Outputs should include:

1. `trend_direction_band`
2. `trend_strength_band`
3. `support_level`
4. optional `predicted_growth_rate`
5. optional caveated count reference

## Expected Outputs

First-pass Phase 06 outputs should be:

1. `ml_label_jurisdiction_field_trend_future.parquet`
2. `ml_feature_jurisdiction_field_trend_forecast.parquet`
3. `ml_split_registry_phase06.parquet`
4. `jurisdiction_field_trend_forecast_3y_model.txt`
5. `jurisdiction_field_trend_forecast_5y_model.txt`
6. `jurisdiction_field_trend_forecast_direction_calibration.json`
7. `ml_prediction_jurisdiction_field_trend_forecast.parquet`
8. `model_card_jurisdiction_field_trend_forecast.json`

## Serving Role

Phase 06 should feed:

1. market hotspot / cooling overlays
2. portfolio gap and opportunity views
3. future segment prioritization
4. report-generation narrative inputs

## Quality Gates

First-pass release gates:

1. direction performance must beat naive carry-forward materially
2. balanced-class or macro-F1 must be acceptable on the held-out split
3. sparse and imbalanced slices must be flagged as limited support
4. strength-band assignment must be stable and interpretable

## Stop Conditions

Stop or keep in candidate-only state if:

1. direction model collapses to majority-class behavior
2. performance is mostly driven by class imbalance
3. sparse segments dominate false hotspot calls
4. support labeling is not defensible

## First Execution Order

Implement in this order:

1. tests for Phase 06 label / feature / split contracts
2. ETL scaffold in `etl/src/patentiq_etl/ml/phase06.py`
3. stage wiring in [run.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/ml/run.py) and [run_stage.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/scripts/run_stage.py)
4. first live label / feature / split materialization
5. baseline training and calibration
6. first reliability audit

## Immediate Recommendation

Proceed with:

1. Phase 06 documentation
2. Phase 06 ETL TDD scaffold
3. first live baseline run
4. follow-up error analysis and target redesign
5. direction-first pivot and balanced-class audit

After the first live run, the next technical adjustment should be:

1. compare the baseline against a naive carry-forward predictor
2. switch Phase 06 to direction-first framing
3. keep raw count only as a secondary explanatory field
4. keep Phase 06 in `sealed_candidate_accepted_for_mvp` state until a later production-promotion pass improves support reliability

This is the most defensible next model from the current warehouse state.

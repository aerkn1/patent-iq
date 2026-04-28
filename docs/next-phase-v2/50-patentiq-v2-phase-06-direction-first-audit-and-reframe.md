# PatentIQ V2 Phase 06 Direction-First Audit And Reframe

## Goal

Record the first strategy-comparison audit for Phase 06 and formalize the recommended pivot from:

1. raw future filing count first

to:

1. direction-first
2. band-first
3. support-aware serving

## Audited Artifact

The comparison audit was run on the persisted Phase 06 test split and saved at:

1. [phase06_strategy_comparison.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/phase06_strategy_comparison.json)

It compares:

1. current raw-count baseline
2. naive carry-forward
3. direction-first multiclass classifier
4. growth-first log-delta regressor

## Data Read

Current Phase 06 training data is structurally usable:

1. [ml_label_jurisdiction_field_trend_future.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_jurisdiction_field_trend_future.parquet) has `16,435` rows
2. years span `2007..2025`
3. observed-horizon coverage is acceptable for experimentation
4. direction labels are present and non-trivial

But the target distribution is extremely heavy-tailed:

1. `3y` median future count `12`, p99 `33,039.7`
2. `5y` median future count `10`, p99 `34,855.7`

So the main weakness is not corrupt data. It is the mismatch between:

1. a highly skewed raw-count target
2. a small jurisdiction-field panel
3. strong time drift

## Test-Split Comparison

### `3y`

Raw-count baseline:

1. RMSE log1p `1.726`
2. MAPE `13.826`
3. direction accuracy `0.427`

Naive carry-forward:

1. RMSE log1p `1.670`
2. MAPE `15.231`
3. direction accuracy `0.279`

Direction-first classifier:

1. class accuracy `0.542`

Growth-first regressor:

1. RMSE log1p `1.794`
2. MAPE `15.093`
3. direction accuracy `0.451`

### `5y`

Raw-count baseline:

1. RMSE log1p `3.217`
2. MAPE `189.472`
3. direction accuracy `0.700`

Naive carry-forward:

1. RMSE log1p `3.513`
2. MAPE `220.185`
3. direction accuracy `0.279`

Direction-first classifier:

1. class accuracy `0.727`

Growth-first regressor:

1. RMSE log1p `3.236`
2. MAPE `195.590`
3. direction accuracy `0.701`

## Important Interpretation

The comparison implies:

1. naive carry-forward is not sufficient
2. growth-first does not materially fix raw-count instability
3. direction-first is the cleanest useful product framing

Important caveat:

1. `5y` direction accuracy is inflated by class imbalance
2. the held-out `5y` test slice is dominated by `cooling`
3. so direction-first looks promising, but still needs balanced-class auditing before sealing

## Recommended Output Contract

Phase 06 should pivot to these primary outputs:

1. `trend_direction_band`
   - `heating`
   - `stable`
   - `cooling`
2. `trend_strength_band`
   - `strong`
   - `moderate`
   - `weak`
3. `support_level`
   - `strong`
   - `moderate`
   - `limited`

Secondary outputs may remain:

1. `predicted_growth_rate`
2. `predicted_count_reference`
3. optional count interval

But these should be secondary and caveated, not the core promise.

## Strength-Band Policy

Recommended first policy:

1. compute class probabilities from the direction model
2. set `trend_direction_band` from the top class
3. set `trend_strength_band` from margin / confidence

Suggested first rules:

1. `strong`
   - top-class probability high and margin over runner-up high
2. `moderate`
   - top-class probability or margin mid-range
3. `weak`
   - probabilities close together or segment unstable

## Support-Level Policy

Support should be based on:

1. cohort row support
2. class-balance support
3. office-field recurrence
4. volatility / sparsity profile

Recommended labels:

1. `strong`
   - enough training support and balanced recent observation
2. `moderate`
   - usable but uneven support
3. `limited`
   - sparse or highly imbalanced slice

## Product Implication

The Market Intelligence and portfolio-gap product should say:

1. `this segment is heating / stable / cooling`
2. `movement looks strong / moderate / weak`
3. `support is strong / moderate / limited`

Not:

1. `this segment will have exactly N future filings`

## Resulting Recommendation

Phase 06 should remain:

1. `direction-first`
2. `band-first`
3. `sealed_candidate_accepted_for_mvp`
4. `not final promoted production`

This recommendation is now implemented in the live artifacts and formalized in:

1. [51-patentiq-v2-phase-06-seal-decision-and-serving-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/51-patentiq-v2-phase-06-seal-decision-and-serving-contract.md)

Remaining follow-up is optional later work:

1. balanced-class refinement for stronger support policy
2. strength-band recalibration if production promotion is needed
3. subgroup-aware reliability review before any stronger support claims

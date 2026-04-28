# Phase 04: Family-Jurisdiction Lapse Risk

## Goal

Forecast lapse and renewal-loss risk at the family-jurisdiction branch level.

## Input Data

1. [silver_branch_status_history_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history_dense.parquet)
2. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
3. [silver_family_enforceability_branches.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet)
4. [silver_family_coverage_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet)
5. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
6. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)

## Actual Metrics Used

1. branch active tenure
2. branch age
3. branch enforceability contribution
4. family coverage stability
5. citation momentum
6. OECD quality and science-grounding context
7. local jurisdiction and field context

## Config And Policy

1. prediction unit is `docdb_family_id x jurisdiction_code`
2. use jurisdiction-aware survival modeling
3. evaluate `12m` and `24m` outlooks
4. aggregate to expected reach-loss only after calibration

## Training Logic

1. build lapse-event labels from replayed branch history
2. align features to pre-event state only
3. train survival or equivalent time-to-event models
4. calibrate horizon-specific event probabilities
5. compute expected reach-loss by multiplying branch lapse probability by branch market weight

## Expected Outputs

1. `ml_label_family_jurisdiction_lapse_event.parquet`
2. `ml_feature_family_jurisdiction_lapse_risk.parquet`
3. `ml_prediction_family_jurisdiction_lapse_risk.parquet`

## Where Outputs Are Consumed

1. portfolio lapse exposure KPIs
2. branch watchlists
3. coverage-loss and single-point-of-failure alerts

## Quality Gates

1. C-index `>= 0.68` overall
2. major-jurisdiction C-index `>= 0.62`
3. 12-month Brier score `<= 0.16`
4. 24-month Brier score `<= 0.18`
5. 80% coverage by horizon between `76%` and `84%`
6. no negative expected reach-loss values

## Stop Conditions

1. regimes with different renewal behavior are mixed carelessly
2. survival calibration poor in major offices
3. executive KPIs built from raw, uncalibrated branch hazards

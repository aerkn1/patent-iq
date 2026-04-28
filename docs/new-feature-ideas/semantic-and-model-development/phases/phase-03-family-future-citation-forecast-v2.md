# Phase 03: Family Future Citation Forecast V2

## Goal

Replace the old appln-level citation forecast path with a family-first model.

## Input Data

1. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
2. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
3. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
4. [silver_family_coverage_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet)
5. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
6. [silver_family_wipo_fields.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet)
7. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)

## Actual Metrics Used

### Core candidate features

1. `family_forward_citations_clean`
2. `family_forward_citations_weighted_7y` or equivalent weighted forward influence
3. `family_rcf_score`
4. `fwd_cits5_raw`
5. `fwd_cits7_raw`
6. `branch_enforceability_contribution_raw`
7. `family_coverage_stability_score`
8. `quality_index_4_percentile`
9. `quality_index_6_percentile`
10. `generality_percentile`
11. `radicalness_percentile`
12. `science_grounding_percentile`
13. family status and family age

## Config And Policy

1. native prediction unit is `docdb_family_id`
2. use time-aware and family-grouped splits
3. train `3y` and `5y` horizons separately
4. raw model score, calibrated score, and interval outputs must remain separate

## Training Logic

1. build leakage-safe labels after `as_of_date`
2. materialize deterministic feature table
3. train baseline LightGBM on `log1p(y)`
4. evaluate challenger only after baseline is reproducible
5. calibrate prediction intervals on validation data
6. store feature manifest, model card, calibration registry, and split registry

## Expected Outputs

1. `ml_label_family_future_citations.parquet`
2. `ml_feature_family_future_citations.parquet`
3. promoted model artifacts for `3y` and `5y`
4. `ml_model_registry.parquet`
5. `ml_calibration_registry.parquet`
6. `model_card_family_future_citation_forecast.json`

## Where Outputs Are Consumed

1. backend family forecast API
2. portfolio forecast aggregation
3. contributor ranking in forecast views
4. later future-influence model extensions

## Quality Gates

1. `3y` Spearman `>= 0.33`
2. `5y` Spearman `>= 0.33`
3. `80%` interval coverage overall between `78%` and `82%`
4. subgroup interval coverage between `76%` and `84%` for major slices
5. Precision@1% improved over old baseline or clearly justified by better calibration
6. top-10 contributor stability Jaccard `>= 0.80` on held-out portfolios

## Stop Conditions

1. model still depends on appln-level inference contract
2. calibration breaks in major offices or fields
3. post-outcome leakage detected

# PatentIQ V2 Phase 03 Family Future Citation Forecast Execution Plan

## Purpose

Define the concrete execution plan for Phase 03 so the team is explicit about:

1. what the model is trying to predict,
2. what the first promoted feature table should contain,
3. how train/validation/test splits should work,
4. which baseline and challenger models should be trained,
5. which hyperparameters should be used first,
6. which outputs should be produced,
7. which scores and gates decide promotion.

This note operationalizes:

1. [phase-03-family-future-citation-forecast-v2.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md)
2. [08-citation-forecast-model-v2-retraining-report.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md)
3. [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md)
4. [15-patentiq-v2-prediction-training-flow-and-guardrails.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md)

---

## 1. What We Are Aiming For

Phase 03 should produce the first `family-first` forecast layer that is good enough to replace the old appln-level citation forecast path.

The promoted product behavior should answer:

1. which families are likely to gain future influence,
2. whether that influence is nearer-term (`3y`) or more strategic (`5y`),
3. how uncertain the forecast is,
4. which factors are pushing the family up or down,
5. whether portfolio future influence is concentrated or diversified once these family forecasts are aggregated later.

This is not a general “AI value score.”

It is specifically:

1. a `family_future_citation_forecast_3y`,
2. a `family_future_citation_forecast_5y`,
3. trained at `docdb_family_id` grain,
4. calibrated and explainable,
5. safe to consume later in portfolio rollups.

---

## 2. What We Expect To Produce

At the end of Phase 03 we should have:

1. leakage-safe label table
2. deterministic feature table
3. split registry
4. experiment registry entries
5. promoted model artifacts for `3y` and `5y`
6. calibration artifacts
7. model card
8. explainability payload contract

Expected artifact set:

1. `ml_label_family_future_citations.parquet`
2. `ml_feature_family_future_citations.parquet`
3. `ml_split_registry.parquet`
4. `ml_experiment_registry.parquet`
5. `ml_model_registry.parquet`
6. `ml_calibration_registry.parquet`
7. `model_card_family_future_citation_forecast.json`
8. model binaries for `3y` and `5y`
9. feature manifest for serving
10. evaluation report with subgroup reliability

---

## 3. Native Prediction Unit

The only promoted primary grain for Phase 03 should be:

1. `docdb_family_id`

Why:

1. it matches V2 family-first product semantics,
2. it removes duplicate-family overrepresentation,
3. it simplifies later portfolio aggregation,
4. it aligns with Gold family summary and later serving contracts.

Fallback grain should not be used unless blocked:

1. no appln-level promoted model for V2,
2. appln-level artifacts would only be acceptable as temporary research checks, not release outputs.

---

## 4. Label Definition

The Phase 03 target is future forward citations after the `as_of_date`.

Recommended label rules:

1. `as_of_date` must be leakage-safe and explicit in metadata,
2. all features must be observable at or before `as_of_date`,
3. all targets must occur strictly after `as_of_date`,
4. train one target for `3y`,
5. train one target for `5y`.

Recommended target columns:

1. `docdb_family_id`
2. `as_of_date`
3. `as_of_year`
4. `future_forward_citations_3y_raw`
5. `future_forward_citations_5y_raw`
6. `future_forward_citations_3y_log1p`
7. `future_forward_citations_5y_log1p`
8. `label_window_3y_end_date`
9. `label_window_5y_end_date`
10. `training_snapshot_id`

Recommended label table:

1. `ml_label_family_future_citations.parquet`

---

## 5. First Promoted Feature Table

The first promoted Phase 03 feature table should stay strong but disciplined.

Do not jump directly to a bloated 40+ feature design if it weakens reproducibility.

The first promoted table should be:

1. rich enough to materially beat the old 10-feature path,
2. interpretable,
3. fully observable at `as_of_date`,
4. stable enough for subgroup calibration.

## 5.1 Feature Sources

Use these source marts:

1. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
2. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
3. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
4. [silver_family_coverage_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet)
5. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
6. [silver_family_wipo_fields.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet)
7. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)

## 5.2 Recommended Release-Candidate Columns

The first release-candidate table should contain these columns.

### Identity and freeze controls

1. `docdb_family_id`
2. `as_of_date`
3. `as_of_year`
4. `family_priority_year`
5. `primary_wipo_field`
6. `training_snapshot_id`
7. `data_completeness_pct`

### Citation history and externality

1. `family_forward_citations_clean`
2. `family_forward_citations_weighted_7y`
3. `family_rcf_score`
4. `unique_citing_family_count` if derivable cleanly from the enriched network
5. `citing_assignee_diversity` or similar network diversity feature if stable
6. `attacker_density_score` from the enriched citation network if deterministic

### Family structure and coverage

1. `family_size_docdb`
2. `active_jurisdiction_count`
3. `family_coverage_stability_score`
4. `family_cpc_subclass_count` or family tech breadth metric
5. `family_distinct_owner_count`

### Legal durability

1. `family_composite_status`
2. `branch_enforceability_contribution_raw`
3. `family_overall_legal_enforceability_score` or proxy
4. `active_grant_branch_count`

### OECD quality

1. `quality_index_4_percentile`
2. `quality_index_6_percentile`
3. `generality_percentile`
4. `radicalness_percentile`
5. `science_grounding_percentile`

### Temporal and cohort controls

1. `family_age_years`
2. `family_earliest_priority_date`
3. `many_field_overlap_flag` if available and stable

This gives a promoted first-pass feature family of roughly:

1. `20-30` usable columns

That is a better first release than:

1. keeping the old 10 features,
2. or jumping to an ungoverned 40+ feature table immediately.

Current implementation note:

1. `fwd_cits5_raw`
2. `fwd_cits7_raw`

were intentionally removed from the promotion feature set because they were not point-in-time safe for the current `as_of_date = priority + 2 years` training contract.

`family_rcf_score` remains in scope, but it is expected to come from the PIT layer as `family_rcf_score_asof`, not from the current-state citation summary mart.

## 5.3 Null Policy

Every feature must declare its null policy.

Recommended rules:

1. `do not silently cast all missing numerics to 0.0`
2. keep explicit nulls during feature assembly
3. impute only through declared policy
4. add completeness controls where needed

Recommended null policy by class:

1. counts and stable absence-style fields:
   - zero-fill only if true zero is semantically correct
2. percentiles and quality metrics:
   - leave null until imputation rule is approved
   - optionally cohort-median impute with missingness flag
3. categorical status fields:
   - explicit `unknown` category if needed
4. network-derived features:
   - null if unavailable, not silent zero, unless the extraction logic proves zero is real

---

## 6. Split Registry

Phase 03 should use a time-aware and family-grouped split registry.

Recommended split strategy:

1. split unit: `docdb_family_id`
2. split method: grouped time split
3. keep a locked test set
4. avoid any family leakage across splits

Recommended split columns:

1. `model_scope`
2. `docdb_family_id`
3. `split_name`
4. `split_strategy`
5. `snapshot_cutoff`
6. `family_priority_year`
7. `primary_wipo_field`

Recommended first split pattern:

1. `train`: oldest eligible cohorts
2. `validation`: next contiguous cohorts
3. `test`: most recent eligible cohorts still label-complete

Suggested ratio:

1. `70 / 15 / 15`

If cohort boundaries produce cleaner evaluation, prefer time windows over exact ratios.

Hard rules:

1. one family cannot appear in more than one split
2. recent cohorts must be represented in validation or test
3. no repeated tuning on the locked test set

---

## 7. Baseline Model

The promoted baseline should be:

1. `LightGBMRegressor` on `log1p(y)`

Train one model for:

1. `future_forward_citations_3y_log1p`
2. `future_forward_citations_5y_log1p`

Why this baseline is correct:

1. already endorsed by the phase docs,
2. interpretable enough,
3. fast to train and serve,
4. easy to calibrate,
5. lower implementation risk than more exotic count models.

## 7.1 Baseline Hyperparameters

Use a conservative starting configuration first, then tune only if justified.

Recommended initial baseline config:

```yaml
objective: regression
metric:
  - rmse
boosting_type: gbdt
n_estimators: 2000
learning_rate: 0.03
num_leaves: 63
max_depth: 8
min_data_in_leaf: 50
feature_fraction: 0.8
bagging_fraction: 0.8
bagging_freq: 1
lambda_l1: 0.1
lambda_l2: 0.1
min_gain_to_split: 0.0
verbosity: -1
seed: 42
```

Why these values:

1. they are close to the current documented production-style LightGBM regime,
2. they are conservative enough for stability,
3. they keep trees explainable,
4. they are a good baseline before objective tuning.

Do not over-tune first.

The first goal is:

1. deterministic reproducibility,
2. better rank quality than the old path,
3. acceptable calibration.

---

## 8. Challenger Models

Only train challengers after the baseline is reproducible and fully evaluated.

Recommended challengers:

1. `LightGBM` with `Poisson`
2. `LightGBM` with `Tweedie`
3. optional `two_stage_hurdle_model`
4. `two_stage_breakout_classifier_plus_tail_regressor`

## 8.1 Poisson Challenger

Use when:

1. count realism improves,
2. tail behavior is better,
3. rank quality does not regress.

Recommended starting config:

```yaml
objective: poisson
metric:
  - poisson
n_estimators: 2000
learning_rate: 0.05
num_leaves: 31
max_depth: 8
min_data_in_leaf: 20
feature_fraction: 0.8
bagging_fraction: 0.8
bagging_freq: 1
lambda_l1: 0.1
lambda_l2: 0.1
verbosity: -1
seed: 42
```

## 8.2 Tweedie Challenger

Use when:

1. the target has a heavy zero mass and skew,
2. Poisson underfits the tail,
3. overall rank quality stays competitive.

Recommended starting config:

```yaml
objective: tweedie
tweedie_variance_power: 1.3
metric:
  - rmse
n_estimators: 2000
learning_rate: 0.05
num_leaves: 31
max_depth: 8
min_data_in_leaf: 20
feature_fraction: 0.8
bagging_fraction: 0.8
bagging_freq: 1
lambda_l1: 0.1
lambda_l2: 0.1
verbosity: -1
seed: 42
```

## 8.3 Optional Hurdle Challenger

Only run this if the zero-vs-positive regime is clearly hurting baseline quality.

Structure:

1. stage 1:
   - binary classifier for `any_future_citations`
2. stage 2:
   - regressor for positive-count families only

This is useful only if:

1. it materially improves ranking or top-bucket usefulness,
2. it does not create a messy serving contract.

For MVP, do not promote the hurdle model unless it wins clearly.

---

## 9. Calibration

Phase 03 should keep:

1. raw model output,
2. calibrated score,
3. interval output

as distinct outputs.

Recommended first calibration method:

1. `conformal_interval_calibration` on validation-only data

Recommended stored calibration outputs:

1. `target_coverage`
2. `coverage_overall`
3. coverage by:
   - filing-year cohort
   - primary WIPO field
   - major office family slice
4. prediction-bucket residual bias
5. calibration method version

If probability-style side outputs are introduced later, allowed methods remain:

1. `isotonic_regression`
2. `platt_scaling`
3. `beta_calibration`

But the main Phase 03 path should focus on interval calibration for count forecasts.

---

## 10. Explainability

The promoted Phase 03 serving contract must be more informative than the current raw `features_used` echo.

Minimum explanation payload:

1. top positive drivers
2. top negative drivers
3. feature completeness
4. main caveats
5. model metadata:
   - `model_version`
   - `feature_manifest_version`
   - `training_snapshot`
   - `calibration_version`
   - `prediction_unit`

Preferred implementation:

1. SHAP or stable gain-based fallback offline
2. compact top-driver extraction for serving

Do not block promotion on a full SHAP platform if:

1. stable top-driver extraction can be shipped first,
2. the explanation payload is still consistent and legible.

---

## 11. Expected Outputs

## 11.1 Training Tables

1. `ml_label_family_future_citations.parquet`
2. `ml_feature_family_future_citations.parquet`
3. `ml_split_registry.parquet`

## 11.2 Registries

1. `ml_experiment_registry.parquet`
2. `ml_model_registry.parquet`
3. `ml_calibration_registry.parquet`
4. `ml_feature_manifest.parquet`

## 11.3 Model Artifacts

1. `family_future_citation_forecast_3y_model.txt` or equivalent
2. `family_future_citation_forecast_5y_model.txt` or equivalent
3. `family_future_citation_forecast_calibration.json`
4. `model_card_family_future_citation_forecast.json`

## 11.4 Serving-Ready Outputs

1. family forecast inference contract
2. batch inference outputs for portfolio aggregation
3. driver-summary payload contract

Later serving tables may include:

1. `ml_prediction_family_future_citations.parquet`
2. family forecast summary sidecar for serving snapshots

---

## 12. Promotion Metrics

Primary ranking metrics:

1. `Spearman`
2. `Precision_at_1pct`
3. `Precision_at_5pct`
4. `Recall_top_decile_impact`

Error metrics:

1. `RMSE_log1p`
2. `MAE_raw`

Reliability metrics:

1. `interval_coverage_80pct`
2. subgroup coverage by:
   - filing-year cohort
   - primary WIPO field
   - major office family slices
3. `prediction_bucket_residual_bias`

Portfolio-oriented stability metric:

1. top-10 contributor stability Jaccard on held-out portfolios

---

## 13. Ship Gates

Phase 03 is safe for MVP only if:

1. `3y Spearman >= 0.33`
2. `5y Spearman >= 0.33`
3. `interval_coverage_80pct` stays within `78%-82%` overall
4. major subgroup coverage stays within `76%-84%`
5. `Precision@1%` improves over the old baseline or a weaker gain is justified by much better calibration and family-first correctness
6. top-10 contributor stability Jaccard on held-out portfolios is `>= 0.80`
7. explanation payloads are stable and legible

Phase 03 is unsafe for MVP if:

1. the model still depends on appln-level inference semantics
2. performance is driven by family duplication leakage
3. calibration breaks in major offices or major fields
4. rank quality collapses in important demo slices
5. output is dominated by one noisy feature such as raw family size

Current implementation status:

1. the live Phase 03 feature manifest now has `0` leakage-sensitive features after PIT enrichment
2. the baseline stage trains successfully on the live corpus
3. the current live candidate uses grouped conformal interval calibration by `primary_wipo_field` with a global fallback for smaller validation groups
4. the latest live PIT-backed candidate metrics are currently around:
   - `3y Spearman ≈ 0.454`
   - `3y interval_coverage_80pct ≈ 0.793`
   - `5y Spearman ≈ 0.614`
   - `5y interval_coverage_80pct ≈ 0.801`
5. overall coverage is now inside the target band for both horizons
6. major subgroup coverage is still too wide for full promotion:
   - `3y` primary-WIPO-field coverage is still roughly `0.634 .. 0.862`
   - `5y` primary-WIPO-field coverage is still roughly `0.667 .. 0.870`
7. a two-stage breakout challenger now trains successfully on the live corpus for both horizons
8. the two-stage challenger is not currently selected:
   - validation rank quality remains slightly weaker than the baseline
   - tail uplift does not compensate enough to justify promotion
9. the correct current status is still `baseline_trained_candidate`, not fully promoted production
10. the serving contract should now be treated as `interval-first directional outlook`, not exact-count-first

---

## 14. Practical Execution Sequence

1. freeze training snapshot and source hashes
2. build `ml_label_family_future_citations`
3. build `ml_feature_family_future_citations`
4. build `ml_split_registry`
5. train baseline `LightGBMRegressor log1p` for `3y`
6. train baseline `LightGBMRegressor log1p` for `5y`
7. calibrate baseline intervals on validation data
8. evaluate overall and subgroup metrics
9. run Poisson challenger
10. run Tweedie challenger
11. optionally run hurdle or two-stage breakout challenger only if clearly justified
12. compare rank quality, calibration, subgroup stability, tail behavior, and explanation quality
13. promote the simplest model that wins on the right criteria
14. write model card, bundle artifacts, and registries

---

## 15. Final Recommendation

Phase 03 should be executed as:

1. a `family-first`,
2. `two-horizon`,
3. `LightGBM baseline first`,
4. `calibration-aware`,
5. `reproducible`,
6. `explainable` forecast rebuild.

The current live conclusion is:

1. keep the baseline as the selected variant
2. retain the two-stage challenger artifacts for future tail-model work
3. present forecasts primarily as interval-backed directional outlooks rather than literal exact citation claims

The right first promoted model is not the most exotic one.

It is:

1. the simplest model that clears rank-quality and calibration gates,
2. uses a disciplined `20-30` feature table,
3. produces a serving contract that backend and UI can trust later.

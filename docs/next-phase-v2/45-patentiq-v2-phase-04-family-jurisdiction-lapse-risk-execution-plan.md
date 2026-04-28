# PatentIQ V2 Phase 04 Family-Jurisdiction Lapse Risk Execution Plan

## Goal

Define the first practical execution plan for `Phase 04`:

1. prediction scope
2. feature table
3. split policy
4. baseline model family
5. evaluation metrics
6. expected outputs

Phase 04 should produce a calibrated `family x jurisdiction` lapse-risk layer that can support:

1. family legal-risk drilldowns
2. portfolio coverage-attrition outlook
3. report-generation evidence blocks
4. later Phase 08 portfolio aggregation

## Current Status

Phase 04 is now implemented as a live trained baseline candidate with:

1. chunked label and feature generation on the live corpus
2. grouped time splits by `family x jurisdiction` trajectory
3. calibrated `12m` and `24m` baseline LightGBM classifiers
4. larger held-out reliability audit

The current artifact set is sealed for MVP under:

1. [46-patentiq-v2-phase-04-seal-decision-and-serving-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/46-patentiq-v2-phase-04-seal-decision-and-serving-contract.md)

This means:

1. acceptable for backend and UI integration
2. acceptable for demo and MVP usage
3. not yet universal office-level promoted production

## Prediction Unit

The primary prediction unit should be:

1. `docdb_family_id`
2. `jurisdiction_code`
3. `as_of_date`

This is not a family-only model.

The model must forecast the legal-coverage loss risk for each family-jurisdiction branch context.

## First Release Horizons

The first release should predict:

1. `lapse_risk_12m`
2. `lapse_risk_24m`

Why:

1. both are already aligned with the portfolio outputs defined in [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md)
2. they are short enough to remain operationally meaningful
3. they are easier to evaluate than a very long legal-survival horizon

## Label Definition

### Positive event

For a given `family x jurisdiction x as_of_date` row:

1. `12m` label = `1` if a lapse or expiry event is observed within the next `12` months
2. `24m` label = `1` if a lapse or expiry event is observed within the next `24` months

### Negative event

Label = `0` when:

1. the branch remains legally active beyond the horizon, or
2. no lapse/expiry event is observed within the horizon and the horizon is fully observed

### Exclusions

Exclude rows where:

1. the branch is already not active at `as_of_date`
2. the branch is not meaningfully in-force or renewal-bearing in that jurisdiction
3. the horizon is not fully observed by snapshot date

## Upstream Data Foundations

Primary sources already available:

1. [silver_legal_status_event_ledger.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet)
2. [silver_branch_status_history_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history_dense.parquet)
3. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
4. [silver_family_feature_snapshot_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit.parquet)
5. [gold_family_blocking_power_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet)
6. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)

These are strong enough to start Phase 04 without inventing a new legal-history foundation.

## Feature Table Design

The first feature table should be branch-aware but still compact.

Recommended table:

1. `ml_feature_family_jurisdiction_lapse_risk.parquet`

Recommended columns:

### Identity and anchor

1. `docdb_family_id`
2. `jurisdiction_code`
3. `as_of_date`
4. `as_of_year`
5. `family_priority_year`
6. `family_age_years`
7. `training_snapshot_id`
8. `method_version`

### Current legal branch state at as_of_date

1. `branch_state_asof`
2. `has_active_grant_asof`
3. `years_since_last_grant_event`
4. `years_since_last_lapse_event`
5. `years_since_last_expiry_event`
6. `branch_stage_multiplier_asof`
7. `branch_enforceability_contribution_raw_asof`

### Family legal context at as_of_date

1. `family_composite_status_asof`
2. `active_jurisdiction_count_asof`
3. `lapsed_jurisdiction_count_asof`
4. `family_jurisdiction_count_asof`
5. `family_coverage_stability_score_asof`
6. `family_overall_legal_enforceability_score_asof`

### Family strategic strength at as_of_date

1. `family_blocking_power_score_asof`
2. `family_field_contribution_primary_asof`
3. `family_tech_breadth_wipo_count_asof`
4. `family_size_docdb_asof`
5. `family_rcf_score_asof`

### Citation / pressure context at as_of_date

1. `pre_asof_forward_citations_clean`
2. `pre_asof_forward_citations_weighted`
3. `pre_asof_unique_citing_family_count`
4. `pre_asof_citing_assignee_diversity`
5. `pre_asof_attacker_density_score`

### Optional first-pass office context

1. `jurisdiction_is_ep`
2. `jurisdiction_is_us`
3. `jurisdiction_is_cn`
4. `jurisdiction_is_jp`
5. `jurisdiction_is_kr`
6. `jurisdiction_is_major_office`

## Target Table

Recommended label table:

1. `ml_label_family_jurisdiction_lapse_risk.parquet`

Columns:

1. `docdb_family_id`
2. `jurisdiction_code`
3. `as_of_date`
4. `as_of_year`
5. `lapse_risk_12m_label`
6. `lapse_risk_24m_label`
7. `is_observed_12m`
8. `is_observed_24m`
9. `event_date_first_negative_after_asof`

## Split Policy

Use a grouped time split.

Split keys:

1. group by `docdb_family_id + jurisdiction_code`
2. time anchor by `as_of_year`

Recommended policy:

1. train on older observed cohorts
2. validation on later observed cohorts
3. test on the latest still-fully-observed cohorts
4. keep recent unresolved rows as `unassigned_recent`

Guardrails:

1. never let the same family-jurisdiction trajectory appear in both train and test
2. never evaluate on rows without fully observed `12m` / `24m` horizons
3. preserve jurisdiction diversity in each split where possible

## Baseline Model Choice

Use a binary classifier baseline first.

Recommended baseline:

1. `LightGBMClassifier`

Rationale:

1. handles mixed sparse/dense tabular features well
2. strong baseline for calibrated risk scoring
3. easy SHAP / feature-importance interpretation
4. practical for horizon-specific models

## First-Pass Hyperparameters

### Shared baseline

1. `objective = binary`
2. `n_estimators = 1200`
3. `learning_rate = 0.03`
4. `num_leaves = 63`
5. `max_depth = 8`
6. `min_data_in_leaf = 100`
7. `feature_fraction = 0.8`
8. `bagging_fraction = 0.8`
9. `bagging_freq = 1`
10. `lambda_l1 = 0.1`
11. `lambda_l2 = 0.1`
12. `random_state = 42`

### Class imbalance handling

Use one of:

1. `scale_pos_weight`
2. per-row class weighting

Prefer:

1. `scale_pos_weight` computed separately for `12m` and `24m`

## Calibration Plan

Lapse risk is probability output, so calibration matters directly.

Recommended first pass:

1. train raw LightGBM classifier
2. calibrate probabilities on validation
3. compare:
   - isotonic
   - Platt / logistic calibration
4. keep the better-calibrated variant per horizon

Unlike Phase 03, this is not interval calibration.

This is:

1. probability calibration
2. reliability curve alignment
3. expected-rate stability by subgroup

## Evaluation Metrics

### Primary metrics

1. ROC AUC
2. PR AUC
3. Brier score
4. log loss

### Calibration metrics

1. calibration curve by decile
2. observed vs predicted lapse rate by decile
3. subgroup calibration by major office
4. subgroup calibration by major WIPO field

### Practical business metrics

1. top-decile lift
2. recall in top risk quintile
3. expected lapse count error after calibration
4. weighted-reach-loss ranking stability

## Suggested Promotion Gates

The first realistic gates should be:

1. `ROC AUC >= 0.72` on major supported jurisdictions
2. `PR AUC` materially above base-rate baseline
3. Brier score stable across validation and test
4. calibration error acceptable on major offices
5. no severe failure in the largest WIPO-field slices

Because legal-event distributions vary strongly by office, office-level subgroup reliability matters more here than in Phase 03.

## Expected Outputs

Phase 04 should emit:

1. `ml_label_family_jurisdiction_lapse_risk.parquet`
2. `ml_feature_family_jurisdiction_lapse_risk.parquet`
3. `ml_split_registry.parquet` rows for Phase 04 scope
4. `family_jurisdiction_lapse_risk_12m_model.txt`
5. `family_jurisdiction_lapse_risk_24m_model.txt`
6. `family_jurisdiction_lapse_risk_calibration.json`
7. `ml_model_registry.parquet` rows for Phase 04
8. `ml_experiment_registry.parquet` rows for Phase 04
9. `ml_calibration_registry.parquet` rows for Phase 04
10. `model_card_family_jurisdiction_lapse_risk.json`

## Product Outputs Unlocked

Once Phase 04 exists, the product can legitimately show:

1. family-level high-risk jurisdictions
2. expected active-coverage loss in `12m`
3. expected active-coverage loss in `24m`
4. portfolio expected lapse counts
5. portfolio expected weighted reach loss
6. report sections describing legal attrition risk

## Immediate Execution Sequence

1. define label contract from legal-status event ledger
2. build branch-aware PIT-safe feature table
3. build grouped time split
4. train LightGBM baseline for `12m`
5. train LightGBM baseline for `24m`
6. calibrate probabilities
7. audit office and field subgroup reliability
8. decide whether to seal as candidate or promote

## Recommendation

Phase 04 is the right next ML phase because:

1. its upstream legal-history data is already strong
2. it unlocks real portfolio attrition outputs
3. it complements Phase 03 without depending on semantic maturity

## Implementation Status

The first ETL scaffold for Phase 04 is now implemented in code:

1. label table contract
2. branch-aware feature table contract
3. grouped trajectory split contract
4. registry-preserving scaffold metadata

Current practical boundary:

1. the scaffold is test-validated
2. the live label and feature artifacts are now built with chunked execution
3. baseline model training and probability calibration are still the next step

Observed live sizing from the current dense branch history:

1. in-scope label rows (`2007..2026`): about `151.9M`
2. in-scope feature rows (`2007..2026`): about `97.3M`
3. fully observed `12m` rows: about `121.7M`
4. fully observed `24m` rows: about `107.3M`
5. distinct in-scope family-jurisdiction trajectories: about `12.7M`

Current live split policy implementation:

1. grouped by `docdb_family_id + jurisdiction_code`
2. trajectory anchor = `first_active_grant_year`
3. the latest test cohort is chosen from the latest `24m`-observed anchor year with a meaningful positive count
4. current live split:
   - `train` through `2019`
   - `validation` on `2020`
   - `test` on `2021`
   - `unassigned_recent` for trajectories first observed in `2022..2025`

## Current Baseline Status

Phase 04 now has live baseline candidate models and calibration artifacts:

1. `family_jurisdiction_lapse_risk_12m_model.txt`
2. `family_jurisdiction_lapse_risk_24m_model.txt`
3. `family_jurisdiction_lapse_risk_calibration.json`

Current live sampled-training profile:

1. `train`: `400k` rows per horizon
2. `validation`: `120k` rows per horizon
3. `test`: `120k` rows per horizon

Current live held-out metrics:

1. `12m`
   - ROC AUC: about `0.985`
   - PR AUC: about `0.120`
   - Brier score: about `0.00257`
   - log loss: about `0.0102`
2. `24m`
   - ROC AUC: about `0.971`
   - PR AUC: about `0.116`
   - Brier score: about `0.00529`
   - log loss: about `0.0207`

Current calibration choice:

1. `isotonic` beat both raw probabilities and Platt on validation for `12m`
2. `isotonic` beat both raw probabilities and Platt on validation for `24m`

So the next implementation step is:

1. audit whether the current Phase 04 baselines are strong enough to seal as accepted MVP candidates
2. document subgroup caveats and decide promotion gates
3. then move to the next ML phase

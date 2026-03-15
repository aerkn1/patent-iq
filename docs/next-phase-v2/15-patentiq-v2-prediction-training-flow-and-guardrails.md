# PatentIQ V2 Prediction Training Flow And Guardrails

## Purpose

Define the safest end-to-end training, validation, calibration, and release flow for every PatentIQ V2 prediction scope so that:

1. prediction targets are defined at the correct grain,
2. training feature tables are generated from the correct Bronze and Silver dependencies,
3. model families are chosen by problem type rather than convenience,
4. calibration and reliability are validated before serving,
5. every prediction surface has explicit MVP-safe usage conditions,
6. every model has a documented downstream blast radius if it is wrong.

This document is the operational companion to:

1. [08-citation-forecast-model-v2-retraining-report.md](./08-citation-forecast-model-v2-retraining-report.md)
2. [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](./09-forecast-v2-mvp-use-cases-and-feature-semantics.md)
3. [10-patentiq-v2-bronze-silver-gold-knowledge-tree.md](./10-patentiq-v2-bronze-silver-gold-knowledge-tree.md)
4. [11-patentiq-v2-metric-lineage-catalog.md](./11-patentiq-v2-metric-lineage-catalog.md)
5. [14-patentiq-v2-metrics-generation-flow-and-guardrails.md](./14-patentiq-v2-metrics-generation-flow-and-guardrails.md)

## Prediction Scope Inventory

PatentIQ V2 should support these prediction scopes:

1. `family_future_citation_forecast`
2. `publication_or_subfamily_grant_probability`
3. `family_jurisdiction_lapse_risk`
4. `family_friction_risk`
5. `jurisdiction_field_trend_forecast`
6. `ep_special_publication_grant_probability`

## Portfolio Prediction Layer

Portfolio prediction in V2 must be treated as a derived aggregation layer, not as a primary monolithic training scope.

The portfolio layer must aggregate:

1. `family_future_citation_forecast`
2. `publication_or_subfamily_grant_probability`
3. `family_jurisdiction_lapse_risk`
4. `family_friction_risk`
5. `jurisdiction_field_trend_forecast`

Recommended derived serving tables:

1. `ml_portfolio_prediction_rollup`
2. `gold_portfolio_forecast_summary`
3. `gold_portfolio_forecast_segments`
4. `gold_portfolio_forecast_contributors`

Core rule:
- portfolio forecasts must remain drillable to family, branch, and segment inputs
- no direct portfolio model should ship in MVP unless it is validated separately and clearly labeled

## Shared Model Governance Contract

Every model scope must satisfy these rules:

1. training and serving grain must be explicitly declared,
2. all features must obey the same `as_of_date` boundary as the label,
3. no post-outcome information may enter training features,
4. raw score, calibrated score, and confidence or interval outputs must be distinguishable,
5. no model may be promoted without subgroup reliability checks,
6. fallback heuristics must exist when data volume is too low or drift is too high,
7. every serving artifact must be tied to:
   - `model_version`
   - `feature_manifest_version`
   - `training_snapshot`
   - `calibration_version`
   - `prediction_unit`
   - `method_version`
8. PATSTAT Register features may be used only inside `ep_special_publication_grant_probability` and must not leak into non-EP scoring or percentile-ranking marts.

## Shared Training Artifacts

The prediction layer should use these training-side tables and registries:

### `ml_feature_manifest`

Purpose:
- canonical list of features allowed for each model scope

Required columns:
- `model_scope`
- `feature_name`
- `feature_table`
- `feature_type`
- `null_policy`
- `is_leakage_sensitive`
- `introduced_in_version`

### `ml_split_registry`

Purpose:
- freeze train/validation/test assignment

Required columns:
- `model_scope`
- `entity_id`
- `split_name`
- `split_strategy`
- `snapshot_cutoff`

### `ml_experiment_registry`

Purpose:
- capture every training run and challenger comparison

Required columns:
- `experiment_id`
- `model_scope`
- `algorithm_family`
- `objective`
- `training_snapshot`
- `feature_manifest_version`
- `primary_metric`
- `primary_metric_value`
- `notes`

### `ml_calibration_registry`

Purpose:
- record calibration method and diagnostics

Required columns:
- `experiment_id`
- `calibration_version`
- `calibration_method`
- `target_coverage`
- `coverage_overall`
- `coverage_major_subgroups`

### `ml_model_registry`

Purpose:
- promote only gate-passing artifacts to serving

Required columns:
- `model_scope`
- `model_version`
- `artifact_uri`
- `feature_manifest_version`
- `calibration_version`
- `promotion_status`
- `rollback_model_version`

## Shared Training Flow

## Stage P0: Freeze Training Snapshot

### Goal

Freeze the exact upstream data snapshot used for model training.

### Inputs

1. all Bronze and Silver tables required by the target model scope
2. reference tables and external weighting inputs

### Outputs

1. `training_snapshot_id`
2. `snapshot_cutoff_date`
3. immutable manifest of source table row counts and hashes

### Guardrails

1. no model should train on mutable live tables,
2. Bronze/Silver row counts must be logged before feature building,
3. snapshot date must be later than the latest allowed feature observation but earlier than label windows.

### Stop Conditions

Stop if:

1. snapshot reproducibility cannot be guaranteed,
2. major upstream tables fail validation from the metrics-generation runbook,
3. row counts drift unexpectedly from the approved snapshot.

### Downstream Blast Radius

If wrong here, all model comparisons become non-reproducible and promotion decisions are not defensible.

## Stage P1: Build Target Labels

### Goal

Create leakage-safe labels for each prediction scope.

### Required label tables

1. `ml_label_family_future_citations`
2. `ml_label_publication_grant_outcome`
3. `ml_label_family_jurisdiction_lapse_event`
4. `ml_label_family_friction_event`
5. `ml_label_jurisdiction_field_trend_future`

### Guardrails

1. labels must be generated after defining the `as_of_date`,
2. labels must exclude information observable only after the cutoff,
3. label windows must be versioned,
4. right-censoring and left-truncation rules must be documented where relevant.

### Stop Conditions

Stop if:

1. the label logic requires future features,
2. positive event counts are too small for the intended model family,
3. censoring assumptions are inconsistent across jurisdictions.

### Downstream Blast Radius

Wrong labels invalidate model metrics, calibration, and every product forecast derived from them.

## Stage P2: Materialize Feature Tables

### Goal

Build deterministic, scope-specific feature tables from validated Silver metrics.

### Required feature tables

1. `ml_feature_family_future_citations`
2. `ml_feature_publication_grant_probability`
3. `ml_feature_family_jurisdiction_lapse_risk`
4. `ml_feature_family_friction_risk`
5. `ml_feature_jurisdiction_field_trend_forecast`
6. `ml_feature_ep_special_grant_probability`

### Shared Guardrails

1. no feature may depend on a Gold presentation-only metric unless explicitly approved,
2. null handling must be explicit per feature,
3. raw and normalized variants must remain distinguishable,
4. every feature must declare whether it is:
   - point-in-time state
   - cumulative history
   - cohort-normalized value
   - contextual trend feature
5. family-first collapse rules must already have run where required.

### Stop Conditions

Stop if:

1. feature coverage is materially lower than expected,
2. missingness becomes correlated with target in an unexplained way,
3. upstream metric validation is stale or failed.

### Downstream Blast Radius

Wrong feature tables corrupt every model scope that consumes them and invalidate all later calibration work.

## Stage P3: Split Registry And Evaluation Design

### Goal

Create robust train/validation/test splits aligned to each model’s failure modes.

### Shared Guardrails

1. use time-aware splits by default,
2. group by family where duplicate application members can leak,
3. use office-aware splits where regulatory regimes differ materially,
4. keep a final locked test set untouched until model selection is complete.

### Recommended split strategies

1. `family_future_citation_forecast`
   - grouped by `docdb_family_id`
   - time-based by `as_of_year` or `family_priority_year`
2. `publication_or_subfamily_grant_probability`
   - grouped by family
   - stratified by jurisdiction and field
3. `family_jurisdiction_lapse_risk`
   - jurisdiction-specific
   - time-based survival split
4. `family_friction_risk`
   - grouped by family
   - time-based with class-balance monitoring
5. `jurisdiction_field_trend_forecast`
   - rolling-origin evaluation

### Stop Conditions

Stop if:

1. leakage between train and test is detected,
2. subgroup representation in test is too sparse for the intended release claim,
3. the selected split strategy overstates performance versus a realistic rolling split.

## Stage P4: Baseline Training

### Goal

Train the simplest interpretable baseline for each scope before challengers.

### Rule

No challenger model should be evaluated until the baseline is reproducible and fully scored.

## Stage P5: Challenger Training

### Goal

Train stronger models only if they can beat the baseline on the right metrics without damaging interpretability or calibration.

### Guardrails

1. challengers must use the exact same split registry as the baseline,
2. any feature additions must be versioned in `ml_feature_manifest`,
3. no challenger can ship solely on one metric if it regresses calibration or subgroup stability materially.

## Stage P6: Calibration

### Goal

Convert raw model outputs into usable probabilities, risks, or intervals.

### Allowed calibration methods

1. `isotonic_regression`
2. `platt_scaling`
3. `beta_calibration`
4. `conformal_interval_calibration`
5. `survival_probability_calibration`

### Guardrails

1. calibration must run on validation-only data,
2. calibration diagnostics must be stored in `ml_calibration_registry`,
3. calibrated outputs must be checked overall and by subgroup.

## Stage P7: Reliability Evaluation

### Goal

Prove the model is accurate enough and safe enough for MVP use.

### Shared evaluation families

1. discrimination / ranking
2. calibration / coverage
3. subgroup stability
4. drift sensitivity
5. explanation sanity

### Shared stop conditions

Stop promotion if:

1. calibration is globally good but materially broken in key offices or fields,
2. ranking quality is acceptable overall but collapses in the most important MVP slices,
3. explanation outputs are inconsistent with known domain relationships,
4. error is dominated by one bad subgroup that the UI cannot safely caveat.

## Stage P8: Fine-Tuning And Feature Hygiene

### Goal

Improve performance safely, not by overfitting.

### Allowed tuning areas

1. objective selection,
2. monotonic constraints where domain-defensible,
3. feature pruning,
4. regularization,
5. resampling or class-weighting,
6. survival horizon design,
7. interval construction method.

### Forbidden tuning shortcuts

1. using post-outcome signals,
2. tuning repeatedly on the locked test set,
3. adding opaque features with no provenance,
4. hiding unstable subgroups under aggregate metrics.

## Stage P9: Promotion To MVP Serving

### Goal

Ship only models that are accurate, calibrated, explainable, and bounded by clear usage rules.

### Promotion outputs

1. model artifact
2. calibration artifact
3. feature manifest
4. model card
5. rollout note with safe-use conditions
6. rollback target

## Stage P10: Portfolio Aggregation And Reliability

### Goal

Build portfolio-level forecast surfaces from validated micro-level model outputs.

### Inputs

1. family-level citation forecast outputs
2. branch-level grant probability outputs
   - including `EP-special` grant outputs where available
3. family x jurisdiction lapse-risk outputs
4. family friction-risk outputs
5. jurisdiction x field trend forecasts
6. ownership and family membership mappings

### Outputs

1. `ml_portfolio_prediction_rollup`
2. `gold_portfolio_forecast_summary`
3. `gold_portfolio_forecast_segments`
4. `gold_portfolio_forecast_contributors`

### Generated Portfolio Metrics

1. `portfolio_expected_future_citations_total`
2. `portfolio_expected_future_citations_per_effective_family`
3. `portfolio_expected_likely_grants_count`
4. `portfolio_expected_lapses_count_12m`
5. `portfolio_expected_lapses_count_24m`
6. `portfolio_expected_weighted_reach_loss_12m`
7. `portfolio_expected_weighted_reach_loss_24m`
8. `portfolio_high_friction_family_count`
9. `portfolio_high_friction_family_share`
10. `portfolio_hotspot_gap_count`
11. `portfolio_top_contributor_dependence_pct`
12. `portfolio_future_impact_concentration_hhi`

### Aggregation Logic

1. future citation totals:
   - sum family-level expected citations using ownership weights where needed
2. likely grants:
   - sum calibrated branch grant probabilities to expected-count space
3. lapse outlook:
   - sum calibrated family x jurisdiction lapse probabilities by horizon
   - compute weighted reach loss by multiplying branch lapse probability by current branch market weight
4. friction exposure:
   - count families above the agreed high-risk threshold
   - compute weighted mass using importance weights where enabled
5. hotspot exposure:
   - join future jurisdiction x field trend forecasts to current portfolio coverage
   - flag high-growth uncovered slices

### Guardrails

1. never sum raw uncalibrated probabilities in executive-facing KPIs,
2. never average family confidence scores and call the result a portfolio interval,
3. never hide concentration when a few families dominate expected value,
4. never mix family and application units in the same aggregate without explicit labeling,
5. ownership weighting must be applied before aggregation,
6. unsupported slices must be excluded or explicitly labeled as fallback,
7. segment rollups must be suppressed where subgroup reliability is below release thresholds,
8. EP-special grant outputs must remain labeled as EP-enhanced rather than universal office-quality upgrades.

### Reliability Checks

1. contributor concentration:
   - check top 1, top 5, and top 10 family contribution shares
2. aggregation completeness:
   - check fraction of in-scope portfolio assets with valid model outputs
3. portfolio calibration proxy:
   - compare expected aggregate counts versus realized counts on held-out portfolios where feasible
4. segment stability:
   - check whether field and jurisdiction rollups are dominated by sparse unsupported cohorts
5. sensitivity:
   - recompute totals with top contributor removed to measure fragility

### Stop Conditions

Stop portfolio forecast release if:

1. more than the approved share of the portfolio lacks valid micro-level predictions,
2. top-contributor dependence exceeds the approved concentration threshold without a UI caveat,
3. segment rollups are mostly driven by unsupported or fallback slices,
4. aggregate expected counts are built from uncalibrated or incomparable micro outputs.

### Downstream Blast Radius

Wrong here corrupts:

1. executive portfolio forecast cards,
2. compare views using predicted upside or risk,
3. pruning and resource-allocation decisions,
4. diligence narratives about company-level future position.

## Model Scope A: Family Future Citation Forecast

### Product Role

Predict expected future forward citation impact for the canonical family at `3y` and `5y` horizons.

### Native Grain

`docdb_family_id`

### Label Table

`ml_label_family_future_citations`

### Feature Table

`ml_feature_family_future_citations`

### Feature Dependencies

From Silver:

1. `silver_family_core`
2. `silver_family_status_pt`
3. `silver_family_coverage_metrics`
4. `silver_family_wipo_fields`
5. `silver_family_citation_metrics`
6. `silver_enriched_citation_network`
7. `silver_family_oecd_quality`
8. `silver_local_tech_trends_timeseries`
9. `silver_global_tech_trends_timeseries`
10. `silver_assignee_harmonized`
11. `silver_family_enforceability_branches`

### Core Features

1. `pre_asof_forward_citations_clean`
2. `pre_asof_forward_citations_weighted`
3. `citation_velocity_1y`
4. `citation_acceleration_2y`
5. `unique_citing_families`
6. `unique_citing_assignees`
7. `external_citation_share`
8. `family_size_docdb`
9. `family_raw_breadth_jurisdiction_count`
10. `family_weighted_market_reach_score`
11. `active_grant_branch_count`
12. `family_tech_breadth_wipo_count`
13. `family_generality_score`
14. `family_originality_score`
15. `family_science_grounding_score`
16. `assignee_family_count`
17. `local_field_trend_coefficient_primary`
18. `global_field_trend_coefficient_primary`
19. `family_overall_legal_enforceability_proxy`
20. `data_completeness_pct`

### Model Families

Baseline:

1. `LightGBMRegressor` on `log1p(y)`

Challengers:

1. `LightGBM` with `Poisson`
2. `LightGBM` with `Tweedie`
3. `two_stage_hurdle_model`
   - stage 1: any-future-citations classifier
   - stage 2: positive-count regressor

### Recommended Configuration

1. grouped time split by family
2. target horizons:
   - `future_forward_citations_3y`
   - `future_forward_citations_5y`
3. train one model per horizon
4. limit feature set to variables observable at `as_of_date`

### Primary Metrics

1. `Spearman`
2. `RMSE_log1p`
3. `MAE_raw`
4. `Precision_at_1pct`
5. `Precision_at_5pct`
6. `Recall_top_decile_impact`

### Calibration / Reliability Metrics

1. `interval_coverage_80pct`
2. coverage by:
   - filing-year cohort
   - primary WIPO field
   - major office family slices
3. `prediction_bucket_residual_bias`

### Fine-Tuning Priorities

1. choose the objective that best preserves rank quality and interval coverage,
2. prune weak ownership or quality features that add instability,
3. test monotonic constraints only where defensible:
   - more clean forward citations should not lower future expectation

### Guardrails

1. no application-grain duplication leakage,
2. no backward NPL blended into impact target,
3. no post-window citation features,
4. no cohort with too few samples should drive public ranking claims.

### Safe For MVP If

1. `Spearman >= 0.33` on both 3y and 5y or a justified alternative target is approved,
2. `interval_coverage_80pct` stays within `78%-82%` overall,
3. major subgroup coverage stays within `76%-84%`,
4. top-decile ranking is materially better than heuristic baseline,
5. explanation payloads are stable and legible.

### Unsafe For MVP If

1. rank quality collapses in the main demo fields,
2. calibration fails badly for recent cohorts,
3. output is dominated by one noisy feature such as raw family size,
4. test performance depends on duplicated family members.

### Downstream Blast Radius

Wrong here corrupts:

1. family forecast cards,
2. portfolio future-impact rollups,
3. hidden-gems prioritization,
4. acquisition-watchlist logic.

## Model Scope B: Publication Or Subfamily Grant Probability

### Product Role

Estimate the probability that a pending publication or branch converts to grant within the defined horizon.

### Native Grain

`appln_id` or `family x jurisdiction x pending branch`

### Label Table

`ml_label_publication_grant_outcome`

### Feature Table

`ml_feature_publication_grant_probability`

### Feature Dependencies

From Silver:

1. `silver_family_member_publications`
2. `silver_family_core`
3. `silver_family_wipo_fields`
4. `silver_assignee_harmonized`
5. `silver_family_status_pt`
6. `silver_family_coverage_metrics`
7. `silver_local_tech_trends_timeseries`
8. `silver_family_oecd_quality`

Register-specific extension:
- PATSTAT Register features are not allowed in this cross-office base scope
- EP applications with Register enrichment should be handled through the separate EP-special scope below

### Core Features

1. `jurisdiction_code`
2. `pending_age_months`
3. `family_priority_year`
4. `family_size_docdb`
5. `family_raw_breadth_jurisdiction_count`
6. `family_tech_breadth_wipo_count`
7. `assignee_historical_grant_rate`
8. `assignee_pending_volume_same_field`
9. `field_grant_rate_jurisdiction`
10. `office_pending_backlog_proxy`
11. `major_office_family_presence`
12. `family_generality_score` where leakage-safe
13. `data_completeness_pct`

### Model Families

Baseline:

1. `LightGBMClassifier`

Challengers:

1. `XGBoostClassifier`
2. `regularized_logistic_regression`

### Recommended Configuration

1. separate major-office models where behavior differs materially:
   - `USPTO`
   - `EPO`
   - optional `CNIPA`, `JPO`, `KIPO` if sample is sufficient
2. group split by family to reduce branch leakage
3. calibrate probabilities after training

### Primary Metrics

1. `PR_AUC`
2. `Brier_score`
3. `LogLoss`
4. `Precision_top_decile`
5. `Recall_positive_class`

### Calibration / Reliability Metrics

1. calibration curve slope and intercept
2. `ECE` or expected calibration error
3. reliability by office, field, and pending-age bucket

### Fine-Tuning Priorities

1. jurisdiction-specific feature interactions,
2. class weighting if grant/non-grant is imbalanced,
3. simplify if office-specific challengers overfit.

### Guardrails

1. no post-grant signals in features,
2. no future citations after grant decision in features,
3. calibration is mandatory before UI display,
4. unsupported offices must fall back to heuristic or no-score mode.

### Safe For MVP If

1. `PR_AUC` exceeds heuristic baseline materially,
2. `Brier_score` is stable across major offices,
3. calibration error is acceptable on `USPTO` and `EPO`,
4. unsupported offices are hidden or explicitly labeled heuristic-only.

### Unsafe For MVP If

1. office mixing produces unstable probabilities,
2. model is accurate overall but badly calibrated in EPO or USPTO,
3. pending-age leakage is suspected.

### Downstream Blast Radius

Wrong here corrupts:

1. pending threat cards,
2. acquisition diligence on shadow portfolios,
3. portfolio likely-grant counts,
4. assignee future grant-pressure views.

## Model Scope B2: EP-Special Publication Grant Probability

### Product Role

Estimate EP grant probability using PATSTAT Register procedural milestones for EP applications only.

### Native Grain

`appln_id`

### Label Table

`ml_label_publication_grant_outcome`

### Feature Table

`ml_feature_ep_special_grant_probability`

### Feature Dependencies

From Silver:

1. `silver_family_member_publications`
2. `silver_family_core`
3. `silver_family_wipo_fields`
4. `silver_assignee_harmonized`
5. `silver_ep_register_proc_step_features`
6. `silver_ep_register_display_ledger`
7. `silver_ep_register_up_status`

### Core Features

1. `jurisdiction_code = 'EP'`
2. `pending_age_months`
3. `family_priority_year`
4. `family_size_docdb`
5. `field_grant_rate_jurisdiction`
6. `assignee_historical_grant_rate`
7. `ep_proc_step_maturity_score`
8. `ep_search_report_mailed_date`
9. `ep_latest_proc_phase_code`
10. `ep_latest_proc_result_code`
11. `ep_proc_time_limit_days`
12. `register_record_present`

### Model Families

Baseline:

1. `XGBoostClassifier`

Challengers:

1. `LightGBMClassifier`
2. `regularized_logistic_regression`

### Recommended Configuration

1. train only on EP applications with Register coverage,
2. keep separate from the cross-office base grant model,
3. calibrate independently from non-EP models,
4. serve with explicit `EP-special` model metadata.

### Primary Metrics

1. `PR_AUC`
2. `Brier_score`
3. `LogLoss`
4. `Precision_top_decile`
5. `Recall_positive_class`

### Calibration / Reliability Metrics

1. `ECE`
2. calibration slope and intercept
3. reliability by pending-age bucket
4. reliability by WIPO field

### Fine-Tuning Priorities

1. procedural-step sequence encoding,
2. time-since-search-report features,
3. null-safe handling for sparse Register fields.

### Guardrails

1. this model must never score non-EP applications,
2. Register features must never be backported into the cross-office base model without a separate comparability review,
3. outputs must be labeled `EP-special`,
4. the model may improve pending-threat forecast accuracy but must not alter global blocking-power or portfolio percentile math.

### Safe For MVP If

1. it materially outperforms the base EP slice of the cross-office model,
2. calibration is stable within EP pending-age and field buckets,
3. missing Register coverage is handled by a clear fallback path.

### Unsafe For MVP If

1. Register coverage is too sparse or inconsistent for reproducible training,
2. the model is accurate overall but poorly calibrated on common EP pending cohorts,
3. the pipeline accidentally routes EP-special features into non-EP predictions.

### Downstream Blast Radius

Wrong here corrupts:

1. EP pending-threat cards,
2. EP acquisition diligence on shadow portfolios,
3. portfolio likely-grant totals where EP-special outputs are aggregated,
4. trust in EP procedural explainability.

## Model Scope C: Family Jurisdiction Lapse Risk

### Product Role

Estimate the probability that a granted family branch lapses within the next prediction window.

### Native Grain

`docdb_family_id x jurisdiction_code`

### Label Table

`ml_label_family_jurisdiction_lapse_event`

### Feature Table

`ml_feature_family_jurisdiction_lapse_risk`

### Feature Dependencies

From Silver:

1. `silver_legal_status_event_ledger`
2. `silver_family_status_pt`
3. `silver_family_coverage_metrics`
4. `silver_tiered_market_weighting`
5. `silver_local_tech_trends_timeseries`
6. `silver_family_citation_metrics`
7. `silver_family_oecd_quality`
8. `silver_family_enforceability_branches`

### Core Features

1. `branch_age_years`
2. `jurisdiction_code`
3. `stage_multiplier_current`
4. `final_market_multiplier`
5. `local_field_trend_coefficient`
6. `family_weighted_market_reach_score`
7. `family_coverage_stability_score`
8. `pre_asof_forward_citations_weighted`
9. `family_overall_legal_enforceability_proxy`
10. `up_single_point_failure_flag`
11. `renewal_milestone_bucket`
12. `assignee_branch_retention_rate_same_jurisdiction`

### Model Families

Baseline:

1. `Cox_Proportional_Hazards`

Challengers:

1. `Random_Survival_Forest`
2. `discrete_time_hazard_model`

### Recommended Configuration

1. train separate jurisdiction families where renewal regimes differ strongly,
2. at minimum separate:
   - `USPTO`
   - `EPO/EP branch`
   - `CNIPA`
   - `JPO/KIPO` if enough data
3. model outputs:
   - `lapse_risk_12m`
   - `lapse_risk_24m`

### Primary Metrics

1. `C_index`
2. `Integrated_Brier_Score`
3. time-dependent AUC at 12m and 24m

### Calibration / Reliability Metrics

1. observed vs predicted lapse probability at 12m / 24m
2. calibration by jurisdiction
3. calibration by branch-age bucket

### Fine-Tuning Priorities

1. survival horizon design,
2. branch-age treatment,
3. renewal-milestone features,
4. jurisdiction-specific baseline hazards.

### Guardrails

1. do not train one global lapse model across incompatible fee regimes,
2. left-truncation must be handled for already-aged patents entering the window,
3. dead branches must not appear as active-risk candidates.

### Safe For MVP If

1. `C_index` beats heuristic branch-age baseline,
2. probability calibration at 12m and 24m is stable in supported jurisdictions,
3. unsupported jurisdictions are not scored or are explicitly heuristic.

### Unsafe For MVP If

1. lapse curves are obviously wrong at key renewal milestones,
2. one jurisdiction dominates the pooled model,
3. survival outputs cannot be explained in simple branch terms.

### Downstream Blast Radius

Wrong here corrupts:

1. strategic-retreat predictions,
2. coverage stability future views,
3. whitespace and patent-cliff insights,
4. pruning recommendations.

## Model Scope D: Family Friction Risk

### Product Role

Estimate the probability that a recently granted family becomes an opposition or litigation target.

### Native Grain

`docdb_family_id`

### Label Table

`ml_label_family_friction_event`

### Feature Table

`ml_feature_family_friction_risk`

### Feature Dependencies

From Silver:

1. `silver_enriched_citation_network`
2. `silver_family_citation_metrics`
3. `silver_family_oecd_quality`
4. `silver_family_status_pt`
5. `silver_family_enforceability_branches`
6. `silver_family_wipo_fields`
7. `silver_assignee_harmonized`

### Core Features

1. `post_grant_citation_velocity_12m`
2. `citation_lethality_sum_12m`
3. `unique_major_attacker_count`
4. `attacker_concentration_hhi`
5. `family_generality_score`
6. `family_radicalness_score`
7. `family_overall_legal_enforceability_proxy`
8. `top_jurisdiction_market_weight`
9. `opposition_survivor_peer_density`
10. `field_collision_density`

### Model Families

Baseline:

1. `LightGBMClassifier` with class weights

Challengers:

1. `LightGBM` with focal loss
2. `regularized_logistic_regression`

Not recommended as primary MVP model:

1. `IsolationForest`

Reason:
- anomaly detection is harder to calibrate and explain in a contest setting

### Recommended Configuration

1. define positive class narrowly and consistently:
   - opposition filed
   - post-grant review filed
   - litigation initiated
2. build a post-grant observation window
3. evaluate heavily on rare-event metrics

### Primary Metrics

1. `PR_AUC`
2. `Recall_at_top_5pct`
3. `Precision_at_top_5pct`
4. `lift_over_base_rate`

### Calibration / Reliability Metrics

1. `Brier_score`
2. reliability by primary field
3. reliability by grant-age bucket

### Fine-Tuning Priorities

1. positive-class weighting,
2. attacker concentration features,
3. citation lethality windows,
4. simplification if rare-event instability is high.

### Guardrails

1. class imbalance handling is mandatory,
2. PR-based evaluation is mandatory,
3. no friction score should be shown if positive-class data is too sparse in the claimed domain,
4. if the model is unstable, revert to rules-based risk tiers built from the same features.

### Safe For MVP If

1. `PR_AUC` materially exceeds random and heuristic baselines,
2. top-risk bucket has credible lift,
3. the positive-class sample is adequate in the exposed MVP slices,
4. high-risk predictions can be explained using attacker/collision evidence.

### Unsafe For MVP If

1. the model only predicts negatives,
2. the top bucket is not materially enriched,
3. explanations rely on opaque anomaly scores.

### Downstream Blast Radius

Wrong here corrupts:

1. high-friction badges,
2. litigation-warning messaging,
3. attacker escalation views,
4. portfolio “under fire” summaries.

## Model Scope E: Jurisdiction-Field Trend Forecast

### Product Role

Forecast short-horizon filing momentum for `jurisdiction x WIPO field` slices.

### Native Grain

`snapshot_year x jurisdiction_code x wipo_field`

### Label Table

`ml_label_jurisdiction_field_trend_future`

### Feature Table

`ml_feature_jurisdiction_field_trend_forecast`

### Feature Dependencies

From Silver:

1. `silver_local_tech_trends_timeseries`
2. `silver_global_tech_trends_timeseries`
3. optional macro references if approved

### Core Features

1. `local_family_filings_t_minus_1`
2. `local_family_filings_t_minus_2`
3. `local_growth_rate_t_minus_1`
4. `local_growth_rate_t_minus_2`
5. `global_field_growth_rate_t_minus_1`
6. `relative_hotspot_index`
7. `rolling_mean_3y`
8. `rolling_std_3y`

### Model Families

Baseline:

1. `ARIMA_or_ETS`

Challengers:

1. `Prophet`
2. `gradient_boosted_tabular_forecast` on lagged features

### Recommended Configuration

1. rolling-origin backtesting
2. short horizon only:
   - `1y`
   - `3y`
   - at most `5y` with strong caveats
3. no long-range 2040-style forecasting

### Primary Metrics

1. `sMAPE`
2. `WAPE`
3. `directional_accuracy`

### Calibration / Reliability Metrics

1. interval coverage
2. bias by jurisdiction tier
3. bias by high-volume vs low-volume fields

### Fine-Tuning Priorities

1. lag depth,
2. trend smoothing,
3. zero-bound handling,
4. fallback to global trend if local history is sparse.

### Guardrails

1. no negative filing-volume forecasts,
2. sparse slices must fall back or stay unforecasted,
3. forecast outputs must be visually distinguished from historical data.

### Safe For MVP If

1. directional accuracy is materially above naive baseline,
2. interval coverage is acceptable on core slices,
3. sparse low-volume slices are suppressed or explicitly fallback-labeled.

### Unsafe For MVP If

1. forecasts oscillate wildly in low-volume slices,
2. many negative or implausible values require manual clipping,
3. the UI cannot communicate historical vs forecast clearly.

### Downstream Blast Radius

Wrong here corrupts:

1. hotspot forecasting,
2. whitespace timing calls,
3. local trend coefficients used in valuation overlays if future values are reused.

## Shared Reliability Dashboard

Every promoted model should publish a compact validation dashboard with:

1. dataset size
2. positive-event rate if classification
3. split strategy
4. primary metric
5. calibration metric
6. subgroup worst-case metric
7. model version
8. fallback / unsupported slice list

## MVP Safe-Use Summary

Prediction models are safe to expose in MVP only when:

1. training snapshot is reproducible,
2. leakage checks are clean,
3. the model beats a simple baseline on the correct metric family,
4. calibration or interval coverage is within approved tolerances,
5. subgroup behavior is not materially broken in the slices shown publicly,
6. unsupported slices are hidden, suppressed, or explicitly labeled heuristic/fallback.

## MVP Unsafe-Use Summary

Do not expose a model as a contest-visible forecast if:

1. aggregate metrics look fine but subgroup reliability is broken in major fields or jurisdictions,
2. the model lacks explanation support,
3. calibration is missing or clearly poor,
4. the effective training sample is too small for the claimed scope,
5. the fallback behavior is undefined.

## Minimal Release Order

If the team needs the safest release order:

1. `family_future_citation_forecast`
2. `publication_or_subfamily_grant_probability`
3. `family_jurisdiction_lapse_risk`
4. `family_friction_risk`
5. `jurisdiction_field_trend_forecast`

The first two are the most defensible to ship early because:

1. they align directly with existing V2 product narratives,
2. they are easier to explain,
3. they have clearer evaluation metrics and artifact structure.

# PatentIQ V2 Phase 05 Family Friction Risk Execution Plan

## Goal

Define the first practical execution plan for `Phase 05`:

1. prediction scope
2. label feasibility
3. feature table
4. split policy
5. baseline model family
6. fallback MVP path if supervised labels are not yet defensible

Phase 05 is intended to support:

1. family high-friction watchlists
2. portfolio "under fire" summaries
3. attacker-escalation evidence blocks
4. legal-intelligence drilldowns

## Current Status

Phase 05 is `planned`, but not yet trainable as a clean supervised production-style model.

What is available now:

1. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
2. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
3. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
4. [silver_family_feature_snapshot_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense.parquet)
5. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
6. [silver_legal_status_event_ledger.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet)
7. [silver_ep_register_current_opposition.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet)
8. [gold_family_attacker_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet)

What is missing:

1. dated opposition chronology in the current Silver layer
2. dated litigation chronology in the current Silver layer
3. a defensible time-anchored positive label source for "future friction event"

## Why Phase 05 Is Not Yet Trainable As A Full Supervised Model

The main blocker is label chronology.

Current live checks:

1. [silver_legal_status_event_ledger.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet) has `176,704,214` total rows but `0` rows with `is_opposition_event = true`
2. the same ledger does contain `17,290,197` grant-event rows across `13,283,424` distinct families
3. [silver_ep_register_current_opposition.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet) has `5,564` currently active EP opposition rows out of `1,090,998` applications

This means:

1. we have `current EP opposition state`
2. we do `not` yet have `dated friction-event history` suitable for future-event labeling

So a true Phase 05 predictive model should `not` be trained yet against the current artifact set without inventing chronology that is not really present.

## Recommended MVP Shape

Phase 05 should be split into two tracks.

## Track A: MVP Friction Proxy

Ship a `rules-based / evidence-weighted friction proxy` first.

This is acceptable because:

1. attacker and collision evidence is already real
2. current EP opposition state is already real
3. family PIT features are already real
4. the product can benefit from a friction signal before the supervised label is mature

Recommended output:

1. `silver_family_friction_proxy.parquet`

Recommended fields:

1. `docdb_family_id`
2. `snapshot_date`
3. `friction_risk_proxy_pct`
4. `friction_risk_band`
5. `ep_opposition_active_badge`
6. `ep_appeal_active_badge`
7. `attacker_density_score`
8. `unique_major_attacker_count`
9. `attacker_concentration_hhi`
10. `citation_lethality_sum`
11. `field_collision_density`
12. `support_reason`
13. `method_version`

Recommended use:

1. family watchlists
2. portfolio high-friction summaries
3. report evidence blocks

This proxy must be labeled as:

1. `heuristic_evidence_weighted`
2. not `future-event calibrated probability`

## Track B: True Predictive Phase 05 Model

Only start the supervised model when one of these becomes available:

1. dated EP opposition chronology
2. dated appeal chronology
3. dated litigation or comparable contestation feed

Then Phase 05 can become a proper predictive model scope.

## Product Role

Until Track B is real, the product role should be:

1. `friction exposure proxy`
2. `challenge susceptibility summary`
3. `attacker / contestation pressure lens`

Not:

1. guaranteed future opposition prediction
2. litigation-probability authority

## Native Grain

When Track B becomes trainable, the native grain should remain:

1. `docdb_family_id`
2. optional `as_of_date`

This should remain family-first, with jurisdiction-aware evidence in the explanation payloads.

## Target Label Design For Future Track B

When chronology exists, define:

1. `friction_event_12m`
2. `friction_event_24m`

Positive event should mean one of:

1. opposition filed
2. appeal filed after opposition pathway
3. litigation or contestation initiated

Negative event should mean:

1. fully observed horizon
2. no friction event in that horizon

Exclusions:

1. families without a meaningful post-grant state
2. families whose observation horizon is not fully closed
3. slices where positive support is too sparse for the claimed domain

## Upstream Data Foundations

Strong current sources:

1. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
2. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
3. [silver_family_feature_snapshot_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense.parquet)
4. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
5. [silver_ep_register_current_opposition.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet)
6. [gold_family_attacker_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet)

Weak current source for supervised labeling:

1. [silver_legal_status_event_ledger.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet)

Reason:

1. no opposition-event positives are currently materialized there

## Feature Table Design

The future supervised table should be:

1. `ml_feature_family_friction_risk.parquet`

Recommended columns:

### Identity and anchor

1. `docdb_family_id`
2. `as_of_date`
3. `as_of_year`
4. `family_priority_year`
5. `family_age_years`
6. `training_snapshot_id`
7. `method_version`

### Citation-pressure features

1. `post_grant_citation_velocity_12m`
2. `post_grant_citation_velocity_24m`
3. `citation_lethality_sum_12m`
4. `citation_lethality_sum_24m`
5. `pre_asof_forward_citations_clean`
6. `pre_asof_forward_citations_weighted`

### Attacker features

1. `unique_major_attacker_count`
2. `attacker_concentration_hhi`
3. `pre_asof_unique_citing_family_count`
4. `pre_asof_citing_assignee_diversity`
5. `pre_asof_attacker_density_score`

### Legal and quality context

1. `family_composite_status_asof`
2. `active_jurisdiction_count_asof`
3. `family_jurisdiction_count_asof`
4. `family_coverage_stability_score_asof`
5. `family_overall_legal_enforceability_score_asof`
6. `family_blocking_power_score_asof`
7. `family_rcf_score_asof`
8. `family_generality_score`
9. `family_radicalness_score`
10. `quality_index_4_percentile`
11. `quality_index_6_percentile`

### EP-specific friction evidence

1. `ep_register_record_present`
2. `ep_opposition_active_current`
3. `ep_appeal_active_current`
4. `ep_opposition_peer_density`

These should remain:

1. explanation features for MVP proxy mode
2. optional features for a future EP-special model
3. not a cross-office base-model crutch unless chronology is real

### Field and collision context

1. `primary_wipo_field`
2. `field_collision_density`
3. `family_field_contribution_primary_asof`
4. `family_tech_breadth_wipo_count_asof`

## Split Policy For Future Track B

Use a grouped time split.

Split keys:

1. group by `docdb_family_id`
2. time anchor by `as_of_year`

Policy:

1. train on older fully observed cohorts
2. validation on later fully observed cohorts
3. test on latest still-fully-observed cohorts
4. keep recent unresolved rows as `unassigned_recent`

Guardrails:

1. no same-family leakage across train and test
2. no evaluation on unresolved horizons
3. no claimed slice if positives are too sparse

## Baseline Model Choice For Future Track B

Recommended baseline:

1. `LightGBMClassifier` with class weighting

Challengers:

1. regularized logistic regression
2. LightGBM with focal-loss-style weighting if needed

Not recommended as MVP primary:

1. anomaly detection
2. opaque unsupervised risk score as the only output

## Primary Metrics

Mandatory:

1. `PR_AUC`
2. `Precision_at_top_5pct`
3. `Recall_at_top_5pct`
4. `lift_over_base_rate`

Secondary:

1. `Brier_score`
2. calibration by primary field
3. calibration by grant-age bucket

## Quality Gates

Future supervised Track B should require:

1. `PR_AUC >= 3x` base-rate baseline
2. top-5% bucket precision `>= 2x` prevalence
3. calibration error `<= 0.06`
4. risk bucket ordering stable across reruns
5. explanation payload can show attacker and collision evidence clearly

## Stop Conditions

Do not train or ship the supervised model if:

1. positive labels come from current-state snapshots without dated chronology
2. the model only predicts negatives
3. the top bucket is not materially enriched
4. explanations rely on opaque anomaly scores

## Immediate Implementation Recommendation

The next practical move should be:

1. do `not` start a supervised Phase 05 trainer yet
2. build `silver_family_friction_proxy.parquet`
3. wire the proxy into backend/UI as a clearly labeled evidence-weighted signal
4. separately investigate whether Register chronology can be expanded into dated opposition-event labels

## Expected Outputs

Immediate MVP-safe output:

1. `silver_family_friction_proxy.parquet`

Future supervised outputs:

1. `ml_label_family_friction_event.parquet`
2. `ml_feature_family_friction_risk.parquet`
3. `family_friction_risk_12m_model.txt`
4. `family_friction_risk_24m_model.txt`
5. `family_friction_risk_calibration.json`
6. `model_card_family_friction_risk.json`

## Bottom Line

Phase 05 should now be treated as:

1. `ready for explicit planning`
2. `ready for MVP proxy implementation`
3. `not yet ready for honest supervised model training`

The reason is simple:

1. the feature side is largely ready
2. the label chronology side is not


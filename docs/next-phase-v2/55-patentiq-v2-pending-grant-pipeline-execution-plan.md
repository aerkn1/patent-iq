# PatentIQ V2 Pending-Grant Pipeline Execution Plan

## Goal

Define the standalone upstream prediction scope required to extend `Phase 08` with a real pending-grant pipeline branch.

This phase should produce calibrated micro-level grant probabilities that can later be aggregated into:

1. portfolio expected likely grants
2. likely grants by jurisdiction
3. likely grants by field
4. grant-pipeline density and contributor drilldowns

## Why This Is The Right Next Extension

The current `Phase 08 core` already uses:

1. `Phase 03` citation outlook
2. `Phase 04` lapse risk
3. `Phase 06` market-direction overlays

The next missing planned branch is `pending-grant pipeline`, not friction.

That is the correct next extension because:

1. it is explicitly required by the forecast semantics in [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md)
2. the lower-level micro-grain requirement is already documented in [predictive-signals-and-interpretable-forecasting-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/predictive-signals-and-interpretable-forecasting-requirements.md)
3. the current warehouse already contains enough publication and branch chronology to build a first defensible base model

## Current Implementation Status

The first ETL contract scaffold for this phase is now implemented in code:

1. [phase_grant.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/ml/phase_grant.py)
2. [test_ml_pending_grant_pipeline_stage.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/tests/test_ml_pending_grant_pipeline_stage.py)

Current live outputs:

1. `ml_label_pending_grant_event.parquet`
2. `ml_feature_pending_grant_pipeline.parquet`
3. `ml_split_registry_phase_grant.parquet`
4. `pending_grant_pipeline_12m_model.txt`
5. `pending_grant_pipeline_24m_model.txt`
6. `pending_grant_pipeline_calibration.json`
7. [model_card_pending_grant_pipeline.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_pending_grant_pipeline.json)

Current status is:

1. contract scaffold implemented
2. targeted tests passing
3. first live full-corpus build completed
4. first baseline `12m/24m` models trained as `candidate` only
5. not sealed yet

### Current portfolio-serving status

As of `2026-04-10`, the portfolio page no longer treats pending-grant as a pure warning-only placeholder.

Current serving path is:

1. preferred path:
   - read [ml_prediction_pending_grant_pipeline.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_pending_grant_pipeline.parquet) when a global serving mart exists
2. current local fallback:
   - build an owner-scoped cache parquet on demand from the sealed candidate artifacts via [build_pending_grant_owner_cache.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/scripts/build_pending_grant_owner_cache.py)
   - cache location: `backend_v2/.cache/pending_grant/{owner_name_harmonized}.parquet`
3. portfolio UI contract:
   - summary row
   - jurisdiction split
   - field split
   - top pending branch shortlist

Important caveat:

1. this is still `candidate_only`
2. when the global prediction mart is absent, the current fallback rank/percentile values are computed from the owner's current pending office slice rather than a full global office mart
3. exact expected likely-grant totals remain directional planning aids, not sealed product truth

Current live read:

1. label / feature / split rows: `93,347,403`
2. observed horizon rows:
   - `12m`: `74,015,905`
   - `24m`: `64,881,761`
3. enriched held-out sampled baseline metrics:
   - `12m`: ROC AUC `0.6395`, PR AUC `0.1670`, Brier `0.0887`
   - `24m`: ROC AUC `0.6600`, PR AUC `0.3201`, Brier `0.1569`
4. calibration method selected:
   - `12m`: `isotonic`
   - `24m`: `isotonic`
5. current verdict:
   - still `candidate_only`
   - local-trend enrichment improved feature realism, but did not materially improve reliability
   - `12m` changed only marginally
   - `24m` degraded versus the prior enriched baseline, so the model remains unsealable

### Real-entity audit status

A dedicated real-entity audit is now also persisted at:

1. [pending_grant_real_entity_audit.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_real_entity_audit.json)

This audit uses actual observed `test` rows across major offices and scores them with the current retrained models.

Current read from that audit:

1. audited real-row slice:
   - `3,943,446` major-office `test` rows across `CN`, `US`, `JP`, `EP`, `KR`
   - `2,134,154` observed `12m` rows
   - `1,134,103` observed `24m` rows
2. audited-slice metrics:
   - `12m`: ROC AUC `0.5886`, PR AUC `0.1699`, Brier `0.0995`
   - `24m`: ROC AUC `0.6148`, PR AUC `0.3242`, Brier `0.1751`
3. strongest real-office behavior in that slice is `JP`
4. `CN` and `US` still show material overprediction
5. primary-owner coverage in the audit slice is `99.85%`
6. current-owner portfolio rollups are usable for sensibility review, but still carry the owner-history replay caveat

So the real-entity audit confirms the same conclusion as the aggregate holdout metrics:

1. useful candidate ranking signal
2. more defensible for shortlist / percentile use than raw probability use
3. not yet strong enough to seal as an exact public-facing grant-likelihood model

## Current Serving Recommendation

The current pending-grant models should **not** be treated as sealed raw-probability outputs.

They are better interpreted as:

1. a `ranking` signal first,
2. a `percentile` or `office-relative rank` signal second,
3. an optional `likelihood tier` only after rank-based ordering is established.

### Recommended current output shape

For current internal or caveated product use, prefer:

1. `pending_grant_rank_within_office_horizon`
2. `pending_grant_percentile_within_office_horizon`
3. `pending_grant_priority_tier`
4. `pending_grant_support_level`

Optional secondary fields:

1. `pending_grant_probability_12m`
2. `pending_grant_probability_24m`

but only as:

1. subordinate detail,
2. caveated candidate output,
3. never the headline user-facing truth.

### Why this is the safer contract

Current discrimination is good enough to rank pending branches better than random, especially on `24m`, but not strong enough to present exact probabilities as a trusted product promise.

So the current contract should be:

1. `rank / percentile first`
2. `tier second`
3. `raw probability optional and caveated`

not:

1. `exact grant likelihood truth`

### Current portfolio contract that is now implemented

The portfolio pending-grant panel should currently expose:

1. `pending_pipeline_percentile`
2. `pending_pipeline_priority_tier`
3. `pending_pipeline_support_level`
4. `pending_pipeline_top_jurisdiction`
5. `pending_pipeline_top_field`
6. top pending branch shortlist with:
   - `rank_within_office_horizon`
   - `percentile_within_office_horizon`
   - `priority_tier`
   - `office_support_level`

The portfolio pending-grant panel should currently suppress as headlines:

1. raw `12m` / `24m` branch probabilities
2. exact portfolio conversion promises
3. unqualified expected-likely-grant totals without candidate caveat language

## Current Trained Feature Set Vs Planned Feature Set

The current live pending-grant models are trained from a narrower implemented feature set than the broader target feature inventory below.

So the correct reading is:

1. the current trained models do use the note-aligned `core` direction,
2. but they do **not** yet use the full planned enriched feature set,
3. the note below should therefore be read as `target scope`, not `already fully implemented scope`.

### Features used in the current live trained models

The current Track A base models are now trained from [phase_grant.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/ml/phase_grant.py) with the enriched feature vector below:

1. `as_of_year`
2. `family_priority_year`
3. `family_age_years`
4. `pending_age_years`
5. `primary_wipo_field`
6. `family_composite_status_asof`
7. `family_size_docdb_asof`
8. `family_jurisdiction_count_asof`
9. `family_coverage_stability_score_asof`
10. `family_tech_breadth_wipo_count_asof`
11. `family_blocking_power_score_asof`
12. `family_enforceability_score_asof`
13. `family_rcf_score_asof`
14. `pre_asof_forward_citations_clean`
15. `pre_asof_forward_citations_weighted`
16. `data_completeness_pct_asof`
17. `application_stage_publication_count`
18. `grant_stage_publication_count`
19. `jurisdiction_field_grant_rate_prior_12m`
20. `jurisdiction_field_grant_rate_prior_24m`
21. `local_family_filings_asof`
22. `prior_period_local_family_filings_asof`
23. `local_growth_rate_asof`
24. `local_trend_coefficient_asof`
25. `jurisdiction_is_ep`
26. `jurisdiction_is_us`
27. `jurisdiction_is_cn`
28. `jurisdiction_is_jp`
29. `jurisdiction_is_kr`
30. `jurisdiction_is_major_office`

### Planned but not yet used in the current live models

The following items are still planned / candidate enrichments rather than currently-trained features:

1. market-direction / trend-context features derived safely from the Phase 06 lane
2. richer CPC/WIPO breadth refinements
3. assignee / owner historical grant-rate priors
4. any later `EP-special` Register procedural features

## Agreed Pending-Grant Enrichment Pass

The agreed next improvement pass for pending-grant is:

1. enrich the current base model before any sealing decision,
2. prefer PIT-safe family / field / office context first,
3. avoid direct leakage-prone reuse of prediction outputs from other phases.

### Highest-priority enrichments

These additions are now implemented in the current enriched baseline:

1. explicit `primary_wipo_field` encoding
2. `family_blocking_power_score_asof`
3. `family_enforceability_score_asof`
4. `family_tech_breadth_wipo_count_asof`
5. smoothed `jurisdiction-field prior grant rates`
6. raw local trend context from `silver_local_tech_trends_timeseries.parquet`

Current conclusion on this enrichment pass:

1. it improved the model contract and feature realism
2. it did not improve the candidate enough to justify sealing
3. `12m` changed only marginally after local-trend enrichment
4. `24m` degraded versus the prior enriched baseline
5. it is therefore still a useful candidate iteration, but not a sealing event

### Conditional later enrichments

These remain valid, but require tighter design or PIT rules before use:

1. broader Phase 06-safe trend-context features beyond the current raw local trend inputs
2. CPC refinement beyond the current WIPO-field layer
3. assignee historical grant-rate priors
4. `EP-special` procedural features in an isolated Track B model

### Explicit guardrail for the enrichment pass

Do **not**:

1. use direct `Phase 06` prediction outputs as training features without a train-safe out-of-fold design,
2. mix `EP-special` features into the cross-office base model,
3. treat the current note’s broader target feature list as already implemented.

Important implementation note:

1. the first apparently excellent training pass was invalidated and replaced because it still had leakage
2. the corrected current baseline uses:
   - grouped trajectory-aware split assignment
   - row-exact split joins
   - publication-stage / grant-stage counts capped at `as_of_year`
   - explicit field encoding
   - PIT-safe blocking / enforceability / WIPO breadth
   - train-safe historical jurisdiction-field priors
   - raw local trend context at `jurisdiction x primary_wipo_field x as_of_year`
3. the current metrics above are the only ones that should be treated as valid

## Native Grain

The primary model grain should be:

1. `family x jurisdiction x as_of_date` branch context for a first cross-office base grant model

Optional later extension:

1. `EP-special` pending branch or application grain using Register procedural features

This matches the existing guidance:

1. micro-level predictive tables must preserve native grain
2. portfolio pending-threat counts must aggregate those micro-level outputs bottom-up

## Product Role

This phase should answer:

1. which pending branches are most likely to convert to grant soon
2. how much of a portfolio’s current pending pipeline is likely to grant
3. which jurisdictions and fields drive the likely-grant pipeline
4. which portfolios have thin, strong, or aging pending pipelines

In the current candidate state, the strongest honest answer is:

1. which pending branches rank highest for likely near-term conversion,
2. which portfolios have relatively stronger or weaker pending pipelines,
3. which offices and fields dominate the likely-converter shortlist,
4. not exact probability truth at branch or portfolio level.

## Current Input Availability Audit

### Strongly available now

The following inputs already exist and are sufficient to start a base grant model:

1. [silver_family_member_publications.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet)
   - rows: `42,692,835`
   - application-stage rows: `24,565,247`
   - grant-stage rows: `11,151,715`
2. [silver_branch_status_history_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history_dense.parquet)
   - rows: `386,481,639`
   - pending-branch rows: `176,880,958`
   - active-grant rows: `157,525,345`
3. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
4. [silver_family_owner_bridge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet)
5. [silver_family_wipo_fields.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet)
6. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
7. [silver_family_enforceability_branches.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet)

These counts show the scope is not data-starved.

There is enough pending-branch and publication-stage volume to train a first cross-office base model.

### EP-special enhancement inputs also available

The following Register inputs already exist for a later EP-special enhancement:

1. [silver_ep_register_core.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet)
   - rows: `1,090,998`
2. [silver_ep_register_proc_step_features.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_proc_step_features.parquet)
   - rows: `1,006,327`
3. [silver_ep_register_display_ledger.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_display_ledger.parquet)
4. [silver_ep_register_up_status.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_up_status.parquet)

This supports a clean two-layer strategy:

1. global/cross-office base grant model first
2. optional `EP-special` overlay second

## Recommended Phase Structure

### Track A: Cross-office base pending-grant model

This is the required first implementation.

Predict:

1. `grant_event_12m`
2. `grant_event_24m`

for pending branch contexts that are still unresolved at `as_of_date`.

### Track B: EP-special pending-grant model

This is optional after Track A.

It should:

1. use Register procedural features
2. stay isolated from the global base model
3. be labeled `EP-special`
4. never be treated as a hidden quality booster for all offices

## First Target Definition

For Track A, the target should be:

1. `grant_event_12m = 1`
   - a pending branch converts to grant within `12 months` after `as_of_date`
2. `grant_event_24m = 1`
   - a pending branch converts to grant within `24 months` after `as_of_date`

Negative label:

1. no grant conversion observed in the horizon while the branch remains observed enough for that horizon

Observed-horizon rule:

1. exclude recent unresolved branches that do not yet have a fully observed horizon

## First Feature Set

### Core branch state features

1. `jurisdiction_code`
2. `family_priority_year`
3. `family_age_years`
4. `years_since_last_pending_event`
5. `years_since_last_grant_event`
6. `pending_branch_flag`
7. `active_branch_flag`
8. `replay_branch_state`

### Family structure features

1. `family_size_docdb`
2. `family_jurisdiction_count`
3. `active_jurisdiction_count`
4. `family_composite_status`
5. `family_coverage_stability_score`

### Field and quality features

1. `primary_wipo_field`
2. `family_tech_breadth_wipo_count`
3. `family_rcf_score`
4. `pre_asof_forward_citations_clean` or safe branch/family analogs where appropriate

### Office / maturity features

1. `jurisdiction_is_major_office`
2. pending-age buckets
3. jurisdiction-field historical grant-rate priors
4. assignee historical grant-rate priors if they can be built without leakage

### EP-special features for Track B only

1. `ep_proc_step_maturity_score`
2. `ep_search_report_mailed_date`
3. `ep_latest_proc_phase_code`
4. `ep_latest_proc_result_code`
5. `ep_proc_time_limit_days`
6. `register_record_present`

## Split Policy

The first split policy should be:

1. grouped, time-aware split by branch trajectory
2. training on older pending cohorts
3. validation on the next cohort year
4. test on the next clean observed cohort year
5. unresolved recent cohorts in `unassigned_recent`

Do not mix branches from the same branch trajectory across train/validation/test if that creates outcome leakage.

## Model Families

### Track A base model

Baseline:

1. `LightGBMClassifier`

Challengers:

1. `XGBoostClassifier`
2. `regularized_logistic_regression`

### Track B EP-special model

Baseline:

1. `XGBoostClassifier`

Challengers:

1. `LightGBMClassifier`
2. `regularized_logistic_regression`

## Calibration

Pending-grant outputs are probability outputs.

So they must be calibrated with:

1. isotonic regression
2. or Platt scaling if sample behavior is better

Required calibration checks:

1. overall calibration
2. reliability by pending-age bucket
3. reliability by major office
4. reliability by WIPO field

For `EP-special`, calibration must remain separate from the global base model.

## Expected Outputs

Track A should emit:

1. `ml_label_pending_grant_event.parquet`
2. `ml_feature_pending_grant_pipeline.parquet`
3. `ml_split_registry_phase_grant.parquet`
4. `pending_grant_pipeline_12m_model.txt`
5. `pending_grant_pipeline_24m_model.txt`
6. `pending_grant_pipeline_calibration.json`
7. `model_card_pending_grant_pipeline.json`
8. `ml_prediction_pending_grant_pipeline.parquet`
9. `pending_grant_pipeline_release_decision.json`

Track B later may emit:

1. `ep_pending_grant_pipeline_12m_model.txt`
2. `ep_pending_grant_pipeline_24m_model.txt`
3. `ep_pending_grant_pipeline_calibration.json`
4. `ml_prediction_pending_grant_pipeline_ep_special.parquet`

## Downstream Use In Phase 08

Once Track A exists, Phase 08 can truthfully extend with:

1. `portfolio_expected_likely_grants_count`
2. `portfolio_expected_likely_grants_by_jurisdiction`
3. `portfolio_expected_likely_grants_by_field`
4. `portfolio_grant_pipeline_density`

Contributor drilldowns must remain available to:

1. exact branch rows
2. family ids
3. jurisdictions
4. pending-age cohorts

## Quality Gates

The first release should require:

1. calibrated probability outputs
2. acceptable PR-AUC above naive class prevalence
3. acceptable Brier score and log loss
4. reliability that is sensible by pending-age bucket
5. no post-outcome leakage

Portfolio-aggregation-specific readiness requires:

1. `0` executive KPIs built from raw uncalibrated probabilities
2. enough scored pending rows to cover a material share of current pending portfolios
3. contributor drill-down rows for portfolio pending totals

## Guardrails

1. do not mix this branch-grain model with family-grain metrics silently
2. do not let `EP-special` features leak into the cross-office base model
3. do not treat predicted grants as current legal truth
4. do not aggregate unresolved sparse slices without support/caveat metadata
5. keep native micro-grain outputs for traceability

## Recommended Execution Order

1. write the standalone pending-grant plan
2. audit the exact pending-branch label-building logic
3. scaffold the ETL phase test-first
4. build Track A base pending-grant model first
5. audit reliability and only then wire it into Phase 08
6. treat Track B `EP-special` as later enhancement, not a blocker

## Bottom Line

This scope is feasible now.

Why:

1. there is ample pending/application-stage volume
2. there is dense branch history
3. there is a clean future Phase 08 use case waiting for it

So the correct next missing upstream phase for Phase 08 is:

1. `pending-grant pipeline`

not friction.

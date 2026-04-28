# Enriched Semantic And Model Implementation Runbook Backlog

## Purpose

Turn the roadmap in:

- [enriched-semantic-and-model-roadmap-from-2026-sciencedirect-findings.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-roadmap-from-2026-sciencedirect-findings.md)

into an execution backlog with:

1. implementation phases,
2. exact upstream data dependencies,
3. expected ETL and serving outputs,
4. validation rules,
5. quality thresholds and release gates,
6. suggested backlog order.

This runbook is additive to:

- [semantic-similarity-and-vector-layer-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md)
- [predictive-signals-and-interpretable-forecasting-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/predictive-signals-and-interpretable-forecasting-requirements.md)
- [15-patentiq-v2-prediction-training-flow-and-guardrails.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md)
- [16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md)

## Scope

This runbook covers:

1. semantic retrieval and semantic comparison runtime,
2. family-first predictive models,
3. portfolio-derived predictive rollups,
4. graph-aware and structured-semantic enrichments,
5. release-quality gates.

It does not cover:

1. a broad legal-opinion engine,
2. universal infringement matching,
3. claim-complete corpus expansion,
4. direct monolithic portfolio model serving as primary truth.

## Current Data Base

## Semantic Data Available Now

### Core input marts

1. [silver_family_text_representative.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet)
2. [silver_semantic_sampling_eligibility.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet)
3. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
4. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
5. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
6. [silver_branch_status_history_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history_dense.parquet)
7. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
8. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)

### Current known corpus condition

1. semantic candidates are broad at family level,
2. claim-grade coverage is narrow relative to abstract coverage,
3. legal and chronology overlays are now strong enough for post-retrieval gating,
4. vector runtime artifacts are not yet promoted.

## Predictive Data Available Now

### Core input marts

1. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
2. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
3. [silver_family_enforceability_branches.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet)
4. [silver_family_field_contributions.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_field_contributions.parquet)
5. [silver_family_coverage_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet)
6. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
7. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
8. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
9. [silver_branch_status_history_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history_dense.parquet)
10. [silver_family_owner_bridge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet)
11. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
12. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
13. [gold_family_blocking_power_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet)
14. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)

### Current known corpus condition

1. feature richness is now substantially ahead of the current deployed model-serving path,
2. the main gap is model pipeline and serving alignment,
3. family-first prediction is now technically supportable,
4. portfolio rollups can now be built from micro-level predictions and real owner membership.

## Shared Governance

Every new semantic or model deliverable must declare:

1. `method_version`
2. `training_snapshot`
3. `feature_manifest_version`
4. `embedding_model_version` or `model_version`
5. `prediction_unit`
6. `text_provenance_policy` where applicable
7. `sampling_policy_version` where applicable
8. `release_status`

Every release candidate must have:

1. row-count audit,
2. coverage audit,
3. leakage audit where predictive,
4. calibration or reliability audit,
5. rollback target.

## Implementation Phases

## Phase 0: Freeze Inputs And Evaluation Fixtures

### Goal

Create stable training and evaluation inputs before any promoted runtime or model work.

### Data used

1. canonical Silver and Gold marts listed above
2. current semantic candidate family set
3. curated semantic evaluation fixtures
4. held-out forecast evaluation cohorts

### Implementation work

1. materialize `training_snapshot_id`
2. create semantic fixture set:
   - discovery queries
   - family-to-family similarity fixtures
   - known false-current-threat fixtures
   - portfolio overlap fixtures
3. create model split registries:
   - time-aware
   - family-grouped
   - office-aware where needed

### Expected outputs

1. `ml_split_registry`
2. `semantic_eval_fixture_registry`
3. `training_snapshot_manifest`

### Expected quality

1. `100%` of promoted artifacts trace to one frozen snapshot
2. `0` detected train/test family leakage
3. fixture set covers major workflows, not only one search flavor

### Stop conditions

1. snapshot row counts drift unexpectedly
2. family leakage appears in grouped splits
3. semantic fixtures lack major workflow coverage

## Phase 1: Promote Semantic Runtime Foundation

### Goal

Replace placeholder semantic runtime with a real promoted vector layer.

### Data used

1. [silver_family_text_representative.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet)
2. [silver_semantic_sampling_eligibility.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet)
3. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
4. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
5. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)

### Implementation work

1. replace `stable_hash_embedding` with a patent-specialized embedding model
2. materialize real vector artifacts:
   - `vec_family_embeddings_claims`
   - `vec_family_embeddings_abstracts`
3. build ANN indexes:
   - claim space
   - abstract space
4. expose a backend retrieval service using family-deduped results
5. attach deterministic context overlays from Gold and Silver

### Expected outputs

1. `vec_family_embeddings_claims.parquet`
2. `vec_family_embeddings_abstracts.parquet`
3. `vec_embedding_manifest.json`
4. `vec_ann_index_manifest.json`
5. `vec_query_registry`
6. backend retrieval endpoint or repository contract

### Expected quality

#### Required hard rules

1. `vector_claims` and `vector_abstract` remain separate
2. results dedupe to `docdb_family_id`
3. representative provenance is preserved
4. legal and chronology context is joinable for every strategic display

#### Release metrics

Existing note metrics:

1. `Recall_at_10`
2. `MRR`
3. `nDCG_at_10`
4. `duplicate_family_rate`
5. exact-vs-ANN recall agreement

Proposed release thresholds:

1. `duplicate_family_rate <= 1.0%`
2. exact-vs-ANN recall agreement at top-20 `>= 0.95`
3. legal-status join completeness `>= 99.0%`
4. chronology join completeness `>= 99.0%`
5. blocking-power context completeness `>= 95.0%`
6. family-to-family overlap stability Jaccard at top-20 `>= 0.85`
7. portfolio overlap stability Jaccard at top-50 `>= 0.80`
8. false-current-threat rate on curated fixtures `<= 2.0%`

### Stop conditions

1. duplicate-family rate remains high
2. claim and abstract spaces are blended in one unlabeled score
3. chronology or legal joins are incomplete
4. claim-space retrieval is marketed beyond its real coverage
5. ranking stability is weak across reruns

## Phase 2: Semantic Reranking And Structured Summaries

### Goal

Turn vector neighbors into explainable strategic outputs.

### Data used

1. vector artifacts from Phase 1
2. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
3. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
4. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
5. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)

### Implementation work

1. add deterministic reranker combining:
   - similarity
   - legal state
   - chronology
   - blocking
   - OECD percentile context
2. build structured family-level semantic summaries
3. expose workflow-specific result payloads:
   - discovery
   - comparison
   - collision
   - whitespace
4. add abstention lane for low-confidence or thin-coverage cases

### Expected outputs

1. `vec_raw_match_results`
2. `vec_semantic_comparison_rollup`
3. `semantic_summary_family`
4. `semantic_abstention_registry`

### Expected quality

1. `>= 95%` of returned results have explicit provenance and legal context
2. `>= 95%` of comparison rows are fully labeled by vector space
3. `0` unlabeled claim-vs-abstract blended scores in exposed APIs
4. sampled whitespace zones always carry sampled flag

### Validation tests

1. family compare shows claim and abstract overlap separately
2. current threat displays suppress dead or non-active-only matches correctly
3. whitespace excludes high active legal density slices
4. abstention triggers on claim-oriented workflows without claim coverage

## Phase 3: Family Future Citation Forecast V2

### Goal

Replace the old appln-level forecast serving path with a family-first model.

### Data used

1. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
2. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
3. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
4. [silver_family_coverage_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet)
5. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
6. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
7. semantic-topology features from later phases when ready

### Implementation work

1. build `ml_label_family_future_citations`
2. build `ml_feature_family_future_citations`
3. train baseline LightGBM on `log1p(y)` for `3y` and `5y`
4. calibrate intervals
5. build explainability payload
6. migrate backend serving from appln-level to family-level

### Expected outputs

1. `ml_label_family_future_citations.parquet`
2. `ml_feature_family_future_citations.parquet`
3. `ml_model_registry.parquet`
4. `ml_calibration_registry.parquet`
5. `model_card_family_future_citation_forecast.json`
6. backend family-forecast serving contract

### Expected quality

Existing note targets:

1. `3y` Spearman `>= 0.33`
2. `5y` Spearman `>= 0.33`
3. `80%` interval coverage overall between `78%` and `82%`
4. major subgroup interval coverage within `76%` to `84%`
5. Precision@1% improved versus current baseline or justified by much better calibration

Additional proposed gates:

1. explanation completeness `>= 99%` for served families
2. top contributor rank stability on held-out portfolios `>= 0.80` Jaccard at top-10
3. no office or field slice with calibration error materially worse than agreed subgroup tolerance

### Stop conditions

1. model still depends on appln-level serving grain
2. calibration breaks in major offices or fields
3. family duplicates leak across splits
4. explanation outputs contradict known domain relationships

## Phase 4: Family-Jurisdiction Lapse Risk

### Goal

Use repaired legal replay and yearly history to estimate lapse and reach-loss risk.

### Data used

1. [silver_branch_status_history_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history_dense.parquet)
2. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
3. [silver_family_enforceability_branches.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet)
4. [silver_family_coverage_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet)
5. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
6. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)

### Implementation work

1. build `ml_label_family_jurisdiction_lapse_event`
2. build `ml_feature_family_jurisdiction_lapse_risk`
3. train jurisdiction-aware survival models
4. calibrate `12m` and `24m` horizons
5. build expected reach-loss rollups

### Expected outputs

1. `ml_label_family_jurisdiction_lapse_event.parquet`
2. `ml_feature_family_jurisdiction_lapse_risk.parquet`
3. `ml_prediction_family_jurisdiction_lapse_risk.parquet`
4. `gold_portfolio_forecast_summary` lapse-related fields fed from micro predictions

### Expected quality

Proposed release thresholds:

1. C-index `>= 0.68` overall
2. major-jurisdiction C-index `>= 0.62`
3. 12-month Brier score `<= 0.16`
4. 24-month Brier score `<= 0.18`
5. 80% event-probability coverage by horizon between `76%` and `84%`
6. no negative expected reach-loss values

### Stop conditions

1. jurisdictions are mixed despite materially different renewal regimes
2. survival calibration is poor in major offices
3. reach-loss rollups are produced from uncalibrated probabilities

## Phase 5: Family Friction Risk

### Goal

Predict high-friction exposure at family level.

### Data used

1. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
2. EP register overlay marts
3. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
4. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
5. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)

### Implementation work

1. define `ml_label_family_friction_event`
2. build `ml_feature_family_friction_risk`
3. train imbalance-aware classifier
4. calibrate probabilities
5. expose top-risk families and friction-weighted mass

### Expected outputs

1. `ml_label_family_friction_event.parquet`
2. `ml_feature_family_friction_risk.parquet`
3. `ml_prediction_family_friction_risk.parquet`
4. `gold_portfolio_forecast_segments` friction-related slices

### Expected quality

Proposed release thresholds:

1. PR-AUC at least `3x` positive-rate baseline
2. precision at top-5% risk bucket `>= 2x` baseline prevalence
3. probability calibration error `<= 0.06`
4. high-risk family share and weighted mass remain stable across reruns

### Stop conditions

1. model is judged mainly by ROC-AUC only
2. positive labels are too sparse in key subgroups to justify broad claims
3. explanations cannot distinguish attack-density versus legal fragility drivers

## Phase 6: Jurisdiction-Field Trend Forecast

### Goal

Build a bounded macro environment forecast consumed by family and portfolio views.

### Data used

1. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)
2. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)
3. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
4. field fragmentation and concentration features when built

### Implementation work

1. build `ml_label_jurisdiction_field_trend_future`
2. build `ml_feature_jurisdiction_field_trend_forecast`
3. train bounded short-horizon forecasting model
4. expose hotspot, cooling, and gap overlays

### Expected outputs

1. `ml_label_jurisdiction_field_trend_future.parquet`
2. `ml_feature_jurisdiction_field_trend_forecast.parquet`
3. `ml_prediction_jurisdiction_field_trend_forecast.parquet`
4. `gold_portfolio_forecast_segments` hotspot fields

### Expected quality

Proposed release thresholds:

1. forecast horizon capped to `3y` or `5y`
2. non-negativity violation rate `0`
3. sign-of-acceleration accuracy `>= 0.65`
4. 80% interval coverage between `76%` and `84%`
5. MAPE `<= 25%` on stable cohorts and `<= 35%` on volatile cohorts

### Stop conditions

1. negative filing or grant volumes appear
2. rolling-origin evaluation collapses versus random split
3. unsupported sparse segments dominate hotspot outputs

## Phase 7: Semantic Topology And Structured Intelligence

### Goal

Promote graph-aware semantic signals and reusable semantic summaries.

### Data used

1. real vector artifacts from Phase 1
2. semantic raw match graph
3. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
4. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
5. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)

### Implementation work

1. build semantic graph features:
   - degree
   - bridge score
   - local density
   - cluster assignment
2. build structured family semantic summary
3. add semantic cluster trajectory views using history marts
4. feed graph features into future-influence and contributor models

### Expected outputs

1. `vec_semantic_graph_features.parquet`
2. `semantic_summary_family.parquet`
3. `semantic_cluster_history.parquet`
4. optional `ml_feature_family_future_influence.parquet`

### Expected quality

Proposed thresholds:

1. graph build covers `>= 95%` of embedded families
2. cluster rerun stability NMI `>= 0.80`
3. semantic summary generation success `>= 98%` for embedded families
4. summary provenance completeness `100%`

### Stop conditions

1. graph features cover only a weak minority of embedded families
2. cluster assignments drift excessively between same-snapshot reruns
3. summaries lose grounding to source family evidence

## Phase 8: Portfolio-Derived Prediction Layer

### Goal

Aggregate validated micro predictions into portfolio intelligence.

### Data used

1. micro prediction tables from Phases 3-6
2. [silver_family_owner_bridge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet)
3. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
4. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)

### Implementation work

1. build `ml_portfolio_prediction_rollup`
2. refresh portfolio forecast Gold marts from calibrated micro outputs
3. add contributor fragility and concentration diagnostics
4. add coverage and completeness flags

### Expected outputs

1. `ml_portfolio_prediction_rollup.parquet`
2. refreshed [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
3. `gold_portfolio_forecast_segments.parquet`
4. `gold_portfolio_forecast_contributors.parquet`

### Expected quality

Existing note-aligned checks:

1. top contributor dependence
2. aggregation completeness
3. portfolio calibration proxy
4. segment stability
5. sensitivity to top contributor removal

Proposed release thresholds:

1. prediction completeness `>= 90%` of effective families for broad portfolio release
2. if completeness is `< 90%`, portfolio output must be caveated or suppressed
3. top-contributor dependence above `35%` requires explicit fragility caveat
4. unsupported segment share above `20%` suppresses segment rollups
5. no executive KPI built from raw uncalibrated probabilities

### Stop conditions

1. family and application units are mixed silently
2. ownership weighting is skipped
3. segment rollups are mostly fallback slices
4. confidence intervals are naive averages of family confidence

## Phase 9: Optional Expansion Tracks

These are justified by the article findings but should ship later.

### Track A: Portfolio Path Dependence Risk

Inputs:

1. semantic cluster history
2. family history
3. owner bridge
4. field contribution timeseries

Outputs:

1. `portfolio_path_dependence_risk`
2. `portfolio_semantic_diversification_score`
3. `portfolio_path_shift_momentum`

### Track B: Segment Fragmentation And Crowding

Inputs:

1. market timeseries
2. owner concentration
3. field and semantic cluster density

Outputs:

1. `segment_fragmentation_score`
2. `segment_crowding_score`
3. `segment_top_owner_expectation`

### Track C: Document Quality Assurance

Inputs:

1. patent specification text
2. claims
3. abstract
4. figure references where available

Outputs:

1. `document_quality_assurance_score`
2. modular defect flags
3. revision recommendations

## Backlog Order

## Tier 1: Immediate

1. Phase 0
2. Phase 1
3. Phase 3

Rationale:

1. semantic runtime and family forecast are the biggest gap between current ETL maturity and live product capability

## Tier 2: High Value

1. Phase 2
2. Phase 4
3. Phase 5
4. Phase 8

Rationale:

1. these convert the new Silver and Gold richness into operational intelligence and portfolio value

## Tier 3: Strategic Depth

1. Phase 6
2. Phase 7
3. Phase 9

Rationale:

1. these deepen strategic differentiation once the core runtime and forecast base are stable

## Minimum Release Definition

PatentIQ can claim a strong next-generation semantic and forecast release when all of the following are true:

1. semantic runtime uses real embeddings and ANN
2. family-first forecast serving replaces appln-level serving
3. calibrated family citation forecast is live
4. lapse-risk model is live or explicitly deferred
5. semantic and forecast outputs are drillable and provenance-safe
6. portfolio rollups are derived from calibrated micro predictions
7. abstention and coverage caveats are explicit in unsupported slices

## Final Guidance

This backlog should be executed with one rule above all:

do not let richer AI layers bypass the deterministic PatentIQ core.

The AI layers should:

1. use the family-first legal and chronology stack,
2. expose confidence and abstention,
3. stay drillable,
4. stay versioned,
5. remain auditable against Gold and Silver truth.

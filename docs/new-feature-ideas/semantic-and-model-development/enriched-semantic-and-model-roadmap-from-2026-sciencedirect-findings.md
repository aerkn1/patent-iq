# Enriched Semantic And Model Roadmap From 2026 ScienceDirect Findings

## Purpose

Translate the article findings documented in:

- [article_findings/README.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/README.md)

into a concrete PatentIQ roadmap for:

1. semantic retrieval and semantic intelligence,
2. predictive models and derived portfolio forecasts,
3. adjacent AI expansion areas that are now justified by the maturity of the Silver and Gold layers.

This note is additive to, not a replacement for:

- [semantic-similarity-and-vector-layer-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md)
- [15-patentiq-v2-prediction-training-flow-and-guardrails.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md)
- [08-citation-forecast-model-v2-retraining-report.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md)
- [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md)

## Core Reading

The most directly useful papers for this roadmap are:

1. [beyond-citations-dynamic-semantic-graph-approach.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/beyond-citations-dynamic-semantic-graph-approach.md)
2. [patent-intelligence-in-the-age-of-ai.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/patent-intelligence-in-the-age-of-ai.md)
3. [a-survey-on-automated-and-ai-based-tools-for-patent-retrieval.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/a-survey-on-automated-and-ai-based-tools-for-patent-retrieval.md)
4. [monitoring-path-dependence-in-multi-technological-organizations.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/monitoring-path-dependence-in-multi-technological-organizations.md)
5. [towards-automated-quality-assurance-of-patent-specifications.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/towards-automated-quality-assurance-of-patent-specifications.md)
6. [ai-hybrid-intelligence-and-the-future-of-patent-analytics.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/ai-hybrid-intelligence-and-the-future-of-patent-analytics.md)

## Current Starting Point

## Semantic Data State

PatentIQ already has a strong semantic-supporting data contract:

1. [silver_semantic_sampling_eligibility.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet)
   - rows: `21,353,101`
   - semantic candidates: `20,295,898`
   - vector sample families: `2,135,310`
2. [silver_family_text_representative.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet)
   - rows: `20,295,898`
   - claim-backed rows: `406,639`
   - abstract-backed rows: `19,889,259`
   - abstract-fallback rows: `19,889,259`
3. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
   - rows: `20,295,898`
   - distinct families: `20,295,898`

Interpretation:

1. PatentIQ now has broad semantic coverage at family level.
2. The semantic context mart is strong enough for retrieval, ranking, overlays, and UI context.
3. Claim-grade semantic coverage remains thin and EP-heavy.
4. The semantic runtime itself is not yet promoted:
   - [etl/src/patentiq_etl/semantic/run.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/semantic/run.py) still uses `stable_hash_embedding`
   - ANN and query registry are placeholder-only
   - the standalone semantic packaging stage has not produced live vector artifacts in `etl/data/vectors`

## Predictive Modeling State

PatentIQ already has rich upstream features available in Silver and Gold:

1. replay-aligned legal state and yearly history,
2. enforceability branches and field contributions,
3. richer citation metrics and enriched citation network,
4. OECD indicators and percentiles,
5. portfolio ownership bridge,
6. market intelligence and family history marts.

But the live model-serving path is still older than the data platform:

1. [forecast_feature_repo.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend/infrastructure/repositories/forecast_feature_repo.py) still reads an `appln_id`-level `ml_training_table`
2. [model_registry.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend/infrastructure/ml/model_registry.py) still expects the old 10-feature LightGBM contract
3. [portfolio_forecast_service.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend/application/services/portfolio_forecast_service.py) still aggregates application-level predictions
4. [etl/src/patentiq_etl/ml/run.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/ml/run.py) still scaffolds only a minimal placeholder ETL layer

Interpretation:

1. upstream data quality is no longer the main ML bottleneck,
2. model training, calibration, and serving alignment are now the main bottlenecks,
3. the next stage of progress should focus on promoted model pipelines, not on more ETL richness first.

## Guiding Principle From The Article Set

The article bundle points to one consistent direction:

1. patent AI systems should be hybrid, not monolithic,
2. semantic retrieval should be context-aware and legally constrained,
3. structured intermediate representations are better than direct opaque end-to-end outputs,
4. early-value and future-impact modeling should incorporate semantic topology, not just citations,
5. portfolio intelligence should model concentration, lock-in, and pathway evolution rather than only aggregate counts,
6. high-stakes automation should always support abstention and analyst review.

This aligns strongly with PatentIQ's existing architecture:

1. family-first collapse,
2. deterministic legal and chronology layers,
3. explicit branch and field decomposition,
4. history-aware Gold marts,
5. portfolio drillability.

## Enriched Semantic Scope

## Canonical Scope That Should Stay

These existing workflows remain correct and should still ship:

1. `text_to_family_semantic_search`
2. `family_to_family_semantic_search`
3. `family_to_family_semantic_compare`
4. `portfolio_to_portfolio_semantic_compare`
5. `semantic_whitespace_and_collision_mapping`

## New Semantic Scope To Add

### 1. `semantic_reranking_with_legal_context`

Purpose:
- turn raw neighbors into strategy-safe ranked matches

Inputs:
- vector similarity
- legal state
- chronology
- blocking power
- OECD quality
- citation context

Rationale:
- supported by the retrieval survey and the hybrid-intelligence paper
- semantic neighbors should not surface naked

### 2. `structured_semantic_summary_generation`

Purpose:
- create reusable family-level semantic summaries before higher-order classification, clustering, or portfolio comparison

Likely content blocks:
- core technical function
- component or subsystem focus
- application domain
- operating principle
- likely segment anchors

Rationale:
- strongly supported by [patent-intelligence-in-the-age-of-ai.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/patent-intelligence-in-the-age-of-ai.md)
- this creates a stable intermediate layer between raw text and downstream AI workflows

### 3. `semantic_graph_centrality`

Purpose:
- derive graph-aware semantic features from family neighborhoods

Possible metrics:
- semantic degree
- local clustering coefficient
- bridge score
- neighborhood novelty
- community centrality

Rationale:
- supported by [beyond-citations-dynamic-semantic-graph-approach.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/beyond-citations-dynamic-semantic-graph-approach.md)
- useful for early-stage importance and hidden-gem detection

### 4. `semantic_cluster_trajectory_tracking`

Purpose:
- monitor how families, owners, and portfolios move through semantic clusters over time

Possible outputs:
- cluster birth and expansion
- owner entry into new semantic zones
- cluster maturity
- portfolio semantic diversification

Rationale:
- supported by path-dependence literature and the existing PatentIQ history layer

### 5. `analyst_review_and_abstention_lane`

Purpose:
- prevent false confidence in ambiguous or thin-coverage semantic cases

Examples:
- claim-space unavailable
- low-confidence mixed results
- weak legal coverage
- sampled-only whitespace zones

Rationale:
- supported by the trademark similarity paper and the hybrid-intelligence paper

## Recommended Semantic Architecture

The enriched semantic architecture should be:

1. representative family text selection
2. separate `vector_abstract` and `vector_claims`
3. real patent-specialized embeddings
4. ANN shortlist
5. deterministic legal and chronology reranking
6. structured semantic summaries
7. graph-derived neighborhood features
8. workflow-specific thresholds and abstention

## Semantic Readiness By Workflow

### Ready Soon

These can be made reliable with current data once real embeddings and ANN are promoted:

1. abstract-first landscape discovery
2. family-to-family semantic comparison
3. portfolio-to-portfolio abstract-space comparison
4. semantic retrieval with current legal overlay
5. semantically driven segment exploration

### Not Ready For Strong Legal Messaging

These still require caution:

1. broad semantic FTO claims
2. infringement-style claim equivalence claims
3. whitespace proof based only on vector sparsity

Reason:

1. claim-grade text coverage is still narrow,
2. claim-space is still EP-heavy,
3. semantic runtime itself is not yet promoted.

## Enriched Model Scope

## Existing Scope That Should Stay

These prediction scopes remain valid and should still be the formal base inventory:

1. `family_future_citation_forecast`
2. `publication_or_subfamily_grant_probability`
3. `family_jurisdiction_lapse_risk`
4. `family_friction_risk`
5. `jurisdiction_field_trend_forecast`
6. `ep_special_publication_grant_probability`

## New Model Scope To Add

### 1. `family_future_influence_forecast`

Purpose:
- estimate future strategic influence more broadly than raw forward citations

Candidate features:
- forward citation history
- semantic centrality
- legal durability
- field trend position
- OECD quality
- ownership concentration and family scale

Rationale:
- supported by the dynamic semantic graph paper
- better aligned to PatentIQ strategic-intelligence positioning than a citations-only endpoint

### 2. `family_semantic_centrality_score`

Purpose:
- early-stage hidden-gem and bridge-family detection

Candidate use:
- family ranking
- portfolio contributor prioritization
- M&A scouting

Rationale:
- semantic topology is useful before citations mature

### 3. `portfolio_path_dependence_risk`

Purpose:
- detect strategic lock-in and low diversification

Candidate outputs:
- path concentration
- dominant-path dependence
- new-path adoption rate
- path switching momentum

Rationale:
- directly supported by [monitoring-path-dependence-in-multi-technological-organizations.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/monitoring-path-dependence-in-multi-technological-organizations.md)

### 4. `portfolio_contributor_concentration_risk`

Purpose:
- detect overdependence on a small number of families for future portfolio value

Candidate outputs:
- top contributor dependence
- concentration HHI
- value fragility under lapse or friction shocks

Rationale:
- strongly aligned with the forecast notes even if not named as a standalone model there

### 5. `segment_fragmentation_and_crowding_forecast`

Purpose:
- predict whether a field-jurisdiction segment is becoming crowded, consolidating, or fragmenting

Candidate features:
- filing growth
- grant growth
- owner concentration
- fragmentation metrics
- semantic density

Rationale:
- supported by the meta-landscape paper

### 6. `family_semantic_collision_risk`

Purpose:
- estimate strategic collision risk where semantic adjacency intersects with active legal coverage

This is not legal infringement probability.

It is:
- semantically similar active competitor pressure
- suitable for watchlists and analyst review

### 7. `document_quality_assurance_score`

Purpose:
- future expansion for drafting support and application QA

Modules:
- compliance
- technical coherence
- figure-reference consistency

Rationale:
- supported by the patent specification QA paper

## Recommended Model Families By Scope

### Tree/Tabular First

Best first choice for:

1. `family_future_citation_forecast`
2. `family_jurisdiction_lapse_risk`
3. `family_friction_risk`
4. `publication_or_subfamily_grant_probability`
5. `ep_special_publication_grant_probability`

Rationale:
- best fit for mixed structured features
- easier calibration and explainability
- faster release path than deep end-to-end modeling

### Sequence Or History-aware Models Later

Best later choice for:

1. `portfolio_path_dependence_risk`
2. `segment_fragmentation_and_crowding_forecast`
3. certain history-aware family-risk models

Rationale:
- these need richer temporal dynamics than static tabular snapshots alone

### Graph-aware Models As Enrichment

Best for:

1. `family_future_influence_forecast`
2. `family_semantic_centrality_score`
3. semantic cluster evolution

Rationale:
- graph structure is the value add, not a replacement for all tabular models

## New Feature Families To Materialize

The current ETL/ML scaffold is too thin. The following feature families should be added explicitly.

## Semantic-topology Features

1. semantic degree
2. semantic bridge score
3. local neighborhood density
4. cross-cluster proximity
5. novelty versus neighborhood centroid

## Legal-history Features

1. branch-state tenure
2. active-jurisdiction survival history
3. lapse or expiry transition counts
4. friction-event history
5. partial-lapse volatility

## Portfolio Structure Features

1. owner concentration
2. contributor concentration
3. semantic diversification
4. path dependence metrics
5. active coverage durability by field and jurisdiction

## Segment Dynamics Features

1. fragmentation
2. crowding
3. top-owner expectation
4. acceleration or cooling
5. semantic density versus legal density gap

## OECD And Quality Features

1. percentile and z-score versions
2. grant-lag
3. quality composites
4. science-grounding
5. generality, originality, radicalness

## Reliability And Evaluation Rules

The article set strengthens these evaluation requirements.

## Semantic Evaluation

PatentIQ should evaluate:

1. exact-vs-ANN recall agreement
2. rank stability across reruns
3. legal-filtered semantic hit usefulness
4. claim-space versus abstract-space divergence
5. analyst acceptance of shortlists

## Forecast Evaluation

PatentIQ should evaluate:

1. subgroup calibration
2. stability of top family contributors
3. interval coverage
4. cohort fairness by field and year
5. reliability under sparse-history conditions

## Abstention Rules

Abstention should be explicit when:

1. semantic coverage is sampled or weak
2. claim coverage is absent for a claim-oriented workflow
3. model cohort support is thin
4. calibration drift is high
5. portfolio concentration makes a summary too fragile

## Product Scope Expansion Opportunities

The article findings justify several expansions that go beyond the current note inventory.

## Strong Candidates

1. semantic graph intelligence
2. structured semantic summaries
3. portfolio path dependence
4. semantic collision watchlists
5. contributor fragility analysis
6. drafting and specification QA

## Weaker Or Later Candidates

1. broad legal-opinion automation
2. universal claim-space infringement matching
3. direct monolithic portfolio prediction as the primary product truth

## Recommended Rollout Order

## Phase 1: Promote What The Data Already Supports

1. replace hash embeddings with a real patent-specialized embedding model
2. materialize vector artifacts and ANN runtime
3. retrain `family_future_citation_forecast` at family level
4. add `family_jurisdiction_lapse_risk`
5. add `family_friction_risk`

## Phase 2: Add Strategic Intelligence Layers

1. structured semantic summaries
2. semantic reranking with legal and chronology context
3. semantic-topology feature family
4. `jurisdiction_field_trend_forecast`
5. `family_future_influence_forecast`

## Phase 3: Add Portfolio And Segment Intelligence

1. `portfolio_path_dependence_risk`
2. contributor concentration and fragility layers
3. segment fragmentation and crowding forecast
4. semantic cluster trajectory views

## Phase 4: Adjacent AI Product Expansion

1. drafting QA
2. analyst copilot for grounded semantic summaries
3. advanced whitespace and collision mapping

## Final Position

The article set does not suggest replacing the current PatentIQ architecture.

It suggests deepening it in a way that is already compatible with the current Silver and Gold data platform:

1. keep family-first,
2. keep legal and chronology overlays deterministic,
3. make semantics hybrid and context-aware,
4. make prediction multi-model and drillable,
5. add graph and portfolio-structure intelligence,
6. keep abstention and analyst review explicit.

That is the strongest path to a richer but still trustworthy PatentIQ intelligence stack.

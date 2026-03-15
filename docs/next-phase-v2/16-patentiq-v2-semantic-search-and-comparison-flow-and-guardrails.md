# PatentIQ V2 Semantic Search And Comparison Flow And Guardrails

## Purpose

Define the safest end-to-end build and release flow for PatentIQ V2 semantic search, vector embeddings, and semantic comparison so that:

1. embeddings are generated from the correct representative family text,
2. vector retrieval does not bypass chronology, legal status, or family-first analytics,
3. semantic comparison remains auditable and useful rather than fuzzy and misleading,
4. vector spaces are chosen by workflow type,
5. retrieval quality and comparison quality are validated before MVP exposure,
6. every semantic workflow has explicit guardrails, failure impact, and MVP-safe conditions.

This document is the operational companion to:

1. [10-patentiq-v2-bronze-silver-gold-knowledge-tree.md](./10-patentiq-v2-bronze-silver-gold-knowledge-tree.md)
2. [12-patentiq-v2-database-structure-and-metric-maps.md](./12-patentiq-v2-database-structure-and-metric-maps.md)
3. [14-patentiq-v2-metrics-generation-flow-and-guardrails.md](./14-patentiq-v2-metrics-generation-flow-and-guardrails.md)
4. [semantic-similarity-and-vector-layer-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md)
5. [mega-cluster-dataset-scope-and-boundary-governance-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md)

## Semantic Scope Inventory

PatentIQ V2 should support these semantic scopes:

1. `text_to_family_semantic_search`
2. `family_to_family_semantic_search`
3. `family_to_family_semantic_compare`
4. `portfolio_to_portfolio_semantic_compare`
5. `semantic_whitespace_and_collision_mapping`

## Shared Semantic Governance Contract

Every semantic workflow must satisfy these rules:

1. semantic retrieval is a discovery layer, not legal proof,
2. all semantic hits must resolve to `docdb_family_id`,
3. chronology and legal context must be joined before strategic display,
4. `vector_claims` and `vector_abstract` must remain separate spaces,
5. representative text selection must be deterministic and versioned,
6. dataset scope and semantic sampling status must be exposed in metadata,
7. every vector artifact must be tied to:
   - `embedding_model_version`
   - `embedding_manifest_version`
   - `corpus_snapshot`
   - `vector_space`
   - `language_policy_version`
   - `sampling_policy_version`

## Shared Semantic Artifacts

### `vec_embedding_manifest`

Purpose:
- canonical list of embedding inputs and preprocessing rules

Required columns:
- `vector_space`
- `text_source_type`
- `representative_selection_rule`
- `language_policy`
- `chunking_policy`
- `embedding_model_version`
- `introduced_in_version`

### `vec_family_embeddings`

Purpose:
- canonical family-level embedding registry

Required columns:
- `docdb_family_id`
- `vector_space`
- `representative_appln_id`
- `representative_publn_id`
- `text_provenance`
- `is_abstract_fallback`
- `earliest_priority_timestamp`
- `wipo_field`
- `overall_bp_percentile`
- `embedding_model`
- `embedding_model_version`
- `text_source_type`
- `language_code`
- `is_machine_translated`
- `corpus_snapshot`

### `vec_index_registry`

Purpose:
- record the active vector index and ANN configuration

Required columns:
- `vector_space`
- `index_backend`
- `index_version`
- `distance_metric`
- `ann_config`
- `build_snapshot`
- `sampling_policy_version`

### `vec_query_registry`

Purpose:
- store query metadata for evaluation and audit

Required columns:
- `query_id`
- `query_type`
- `vector_space`
- `query_text_hash`
- `query_family_id`
- `created_at`
- `embedding_model_version`

### `vec_raw_match_results`

Purpose:
- raw nearest-neighbor output before deterministic joins

Required columns:
- `query_id`
- `matched_docdb_family_id`
- `semantic_similarity_score_raw`
- `rank_raw`
- `vector_space`
- `index_version`

### `vec_semantic_comparison_rollup`

Purpose:
- reusable semantic-overlap layer for family and portfolio compare workflows

Required columns:
- `comparison_scope`
- `left_entity_id`
- `right_entity_id`
- `vector_space`
- `semantic_overlap_score`
- `cluster_overlap_score`
- `whitespace_gap_score`
- `comparison_snapshot`

## Shared Build Flow

## Stage S0: Freeze Corpus Snapshot

### Goal

Freeze the exact family text corpus used for embedding generation and evaluation.

### Inputs

1. `silver_family_core`
2. `silver_family_member_publications`
3. `bronze_uspto_ft_document`
4. `bronze_uspto_ft_biblio_application`
5. `bronze_uspto_ft_claims`
6. `bronze_uspto_ft_abstract`
7. `bronze_epab_document`
8. `bronze_epab_publication`
9. `bronze_epab_application`
10. `bronze_epab_claims`
11. `bronze_epab_abstract`
12. `bronze_patstat_appln_abstr`
13. representative text sources from titles, abstracts, and claims
14. scope and sampling rules

### Outputs

1. `corpus_snapshot`
2. family count
3. sampled-family count if MVP sampling is used
4. manifest of included languages and source types

### Guardrails

1. no embedding job should run against a mutable live corpus,
2. the semantic layer must declare whether it is full-corpus or sampled,
3. sampled subsets must be reproducible,
4. MVP corpus scope must honor the semantic sampling guardrail:
   - in-scope mega-cluster families
   - active grants only
   - reproducible `5%` to `10%` sample unless broader scope is explicitly approved.

### Stop Conditions

Stop if:

1. representative text coverage is too low for the intended workflow,
2. corpus snapshot is not reproducible,
3. sampling policy is undefined.

### Downstream Blast Radius

If wrong here, semantic rankings, comparisons, and whitespace maps become non-reproducible and hard to trust.

## Stage S1: Representative Family Text Selection

### Goal

Pick the single representative family member for embedding without cluttering retrieval with duplicates.

### Inputs

1. `silver_family_member_publications`
2. `silver_kind_code_normalization`
3. `bronze_uspto_ft_document`
4. `bronze_uspto_ft_biblio_application`
5. `bronze_epab_document`
6. `bronze_epab_publication`
7. `bronze_epab_application`
8. title, abstract, and claims sources

### Outputs

1. representative family text selection record
2. preferred `representative_appln_id`
3. preferred `representative_publn_id`
4. `representative_stage`
5. `text_source_type`

### Core Logic

Use the deterministic hierarchy:

1. U.S. granted `B` Claim 1 from USPTO full text,
2. if no U.S. grant claim exists, English EP granted `B` Claim 1 from EPAB,
3. if no usable U.S. or EP grant claims exist, English PATSTAT abstract fallback,
4. never use `A`-document claims for FTO or infringement-oriented `vector_claims`,
5. never prefer `C0` as technical text unless no better artifact exists.

### Guardrails

1. never embed every `A/B/C` member as separate family-level search targets,
2. keep the selected representative linked to the family and publication provenance,
3. retain fallback reason when no English granted text exists,
4. for MVP claim-space embeddings, extract Claim 1 only,
5. USPTO and EPAB full-text sources must act as text providers only and must not replace PATSTAT/Register metadata layers for classifications, citations, parties, or legal truth.

### Stop Conditions

Stop if:

1. the representative hierarchy produces multiple candidates with no deterministic tie-break,
2. too many in-scope families lack usable text,
3. claims text is missing for most families intended for FTO workflows.

### Downstream Blast Radius

Wrong here corrupts:

1. family-level deduplication,
2. semantic FTO precision,
3. family-to-family comparisons,
4. whitespace maps.

## Stage S2: Text Normalization And Language Policy

### Goal

Normalize text inputs consistently before embedding.

### Inputs

1. representative titles
2. representative abstracts
3. representative claims
4. language metadata

### Outputs

1. normalized text payloads per vector space
2. language flags
3. translation flags

### Guardrails

1. claims and abstracts must remain separate text channels,
2. machine-translated text must be flagged,
3. normalization must not destroy legal claim structure needed for `vector_claims`,
4. chunking policy must be versioned,
5. XML/HTML tags must be stripped,
6. formatting noise and layout line breaks must be removed,
7. inline reference numerals should be removed where safe,
8. U.S. or EP application-stage claims must not flow into `vector_claims` for FTO messaging.

### Stop Conditions

Stop if:

1. normalization strips too much legal/technical structure,
2. translation coverage is inconsistent and unlabeled,
3. chunking produces empty or truncated payloads at material scale.

### Downstream Blast Radius

Wrong here corrupts:

1. embedding quality,
2. claim-vs-abstract separation,
3. cross-language comparison quality.

## Stage S3: Embedding Model And Vector-Space Selection

### Goal

Choose workflow-appropriate embedding models and vector spaces.

### Supported vector spaces

1. `vector_abstract`
2. `vector_claims`

### Workflow-to-space mapping

1. `text_to_family_semantic_search`
   - default: `vector_abstract`
   - FTO variant: `vector_claims`
2. `family_to_family_semantic_search`
   - `vector_abstract` for technology discovery
   - `vector_claims` for legal-scope adjacency
3. `family_to_family_semantic_compare`
   - both spaces if available, separately labeled
4. `portfolio_to_portfolio_semantic_compare`
   - cluster/overlap on `vector_abstract`
   - enforceability-aware overlap on `vector_claims`
5. `semantic_whitespace_and_collision_mapping`
   - `vector_abstract` for exploration
   - `vector_claims` overlay for active protection density

### Model families

Preferred:

1. patent-specialized sentence-transformer models
2. patent/legal domain embedding models

Fallback:

1. high-quality general technical embeddings, only if domain models are not deployable

Not recommended as primary MVP model:

1. generic consumer-text embeddings with no patent tuning

### Guardrails

1. one embedding model version per active vector space at a time for MVP,
2. no silent switching between models across queries,
3. generic embeddings must not be presented as legally reliable FTO signals.

### Stop Conditions

Stop if:

1. chosen model is not stable on patent phrasing,
2. query-time latency is incompatible with MVP,
3. the model cannot support both English technical abstracts and claim language adequately.

### Downstream Blast Radius

Wrong here corrupts:

1. semantic retrieval relevance,
2. semantic compare quality,
3. FTO shortlist usefulness,
4. whitespace credibility.

## Stage S4: Embedding Generation

### Goal

Generate family-level vectors for each supported space.

### Inputs

1. representative family text
2. `vec_embedding_manifest`
3. selected embedding model

### Outputs

1. `vec_family_embeddings`

Mandatory payload fields:
1. `docdb_family_id`
2. `vector_space`
3. `representative_appln_id`
4. `representative_publn_id`
5. `text_provenance`
6. `is_abstract_fallback`
7. `earliest_priority_timestamp`

Additional abstract-space payloads where needed:
1. `wipo_field`
2. `overall_bp_percentile`

### Guardrails

1. every vector row must resolve to exactly one `docdb_family_id`,
2. `vector_space` must be explicit,
3. embeddings must carry representative document provenance,
4. sampled corpora must expose `sampling_policy_version`,
5. claim-space vectors must come only from granted U.S. or EP claim text unless clearly flagged as abstract fallback.

### Stop Conditions

Stop if:

1. embedding failure rate is materially high,
2. vector dimension mismatch occurs across a supposedly single space,
3. sample coverage drifts unexpectedly between runs.

### Downstream Blast Radius

Wrong here corrupts the index, retrieval quality, and all downstream semantic comparisons.

## Stage S5: Vector Index Build

### Goal

Build the ANN or exact similarity index used for retrieval.

### Inputs

1. `vec_family_embeddings`
2. chosen backend:
   - `Qdrant`
   - `Milvus`
   - `pgvector`
   - or server-side exact similarity

### Outputs

1. active vector index
2. `vec_index_registry`

### Guardrails

1. distance metric must be fixed and documented,
2. ANN settings must be versioned,
3. index must be built separately per vector space,
4. index recall must be measured against an exact-search sample.

### Stop Conditions

Stop if:

1. ANN recall is too low for top-k retrieval,
2. index latency is too high for MVP,
3. index build is not reproducible from the stored embeddings.

### Downstream Blast Radius

Wrong here corrupts retrieval rank order, comparison overlap, and query-time trust.

## Stage S6: Offline Retrieval Evaluation

### Goal

Measure whether the vector layer retrieves families that are actually useful for intended workflows.

### Evaluation sets

1. curated family-to-family relevance pairs
2. curated text-to-family FTO prompts
3. curated portfolio-to-portfolio overlap benchmarks
4. duplicate-family suppression fixtures

### Primary retrieval metrics

1. `Recall_at_10`
2. `Recall_at_50`
3. `MRR`
4. `nDCG_at_10`
5. `duplicate_family_rate`

### Comparison metrics

1. `cluster_purity`
2. `semantic_overlap_rank_stability`
3. `Jaccard_overlap_top_k`
4. `Spearman` on comparison rankings where benchmark labels exist

### Guardrails

1. evaluate abstract and claims spaces separately,
2. judge duplicate suppression at family level, not publication level,
3. do not use legal-threat precision metrics before chronology/legal joins are applied.

### Stop Conditions

Stop if:

1. duplicate-family rate is high,
2. retrieval differs wildly between repeated builds with the same corpus,
3. `vector_claims` cannot outperform or at least justify itself for FTO-style queries.

### Downstream Blast Radius

Wrong here corrupts:

1. query relevance,
2. semantic compare ordering,
3. cluster quality,
4. user trust in semantic discovery.

## Stage S7: Hybrid Retrieval And Reranking

### Goal

Combine vector search with deterministic filters and, optionally, lexical retrieval.

### Inputs

1. `vec_raw_match_results`
2. keyword/lexical candidates where enabled
3. `gold_family_summary`
4. `gold_family_blocking_power`
5. `silver_family_status_pt`

### Outputs

1. reranked family matches
2. `gold_semantic_match_context`

### Recommended retrieval stack

1. semantic ANN retrieval
2. optional lexical merge
3. family-level deduplication
4. chronology classification
5. legal-status join
6. reranking for workflow-specific objectives

### Guardrails

1. reranking must never overwrite raw similarity scores silently,
2. the product must expose:
   - raw similarity
   - vector space
   - chronology relation
   - legal status
3. lexical and semantic blending weights must be versioned.

### Stop Conditions

Stop if:

1. reranking changes are not explainable,
2. family-level deduplication fails,
3. chronology or legal joins are missing.

### Downstream Blast Radius

Wrong here corrupts:

1. semantic FTO shortlists,
2. comparison workspaces,
3. whitespace results,
4. explainability of semantic hits.

## Stage S8: Chronology And Legal Gating

### Goal

Convert raw semantic neighbors into strategy-safe result categories.

### Inputs

1. `vec_raw_match_results`
2. `gold_family_summary`
3. `gold_family_blocking_power`
4. family time and status tables

### Output categories

1. `prior_art`
2. `peer`
3. `follower`
4. `current_threat`
5. `shadow_portfolio`
6. `dead_but_relevant`

### Core Logic

1. compare query family date or query design date to matched family priority date,
2. attach current legal state,
3. attach blocking-power context if the family is active,
4. classify for the UI.

### Guardrails

1. no semantic result should appear as threat without chronology and legal joins,
2. dead families can be prior art but not current blocking threats,
3. pending families may be watch items but not current enforceable blockers.

### Stop Conditions

Stop if:

1. chronology relation cannot be determined,
2. legal state is missing for a supposedly strategic result,
3. the UI would have to show unlabeled raw similarity only.

### Downstream Blast Radius

Wrong here corrupts:

1. FTO risk interpretation,
2. invalidation and prior-art flows,
3. semantic collision maps.

## Stage S9: Semantic Comparison Rollups

### Goal

Build reusable semantic comparison layers for families, portfolios, and assignees.

### Inputs

1. family-level embeddings
2. retrieval neighbors
3. family-level deterministic analytics
4. owner and portfolio mappings

### Outputs

1. `vec_semantic_comparison_rollup`
2. comparison payloads for:
   - family-to-family compare
   - portfolio-to-portfolio compare
   - assignee-to-family compare

### Generated Comparison Metrics

1. `semantic_overlap_score`
2. `claims_overlap_score`
3. `abstract_overlap_score`
4. `cluster_overlap_score`
5. `semantic_whitespace_gap_score`
6. `active_overlap_density`
7. `blocking_power_overlap_weight`

### Comparison Logic

1. family-to-family compare:
   - compare in both vector spaces where available
   - keep claim and abstract overlap separate
2. portfolio-to-portfolio compare:
   - aggregate family overlap into field or cluster overlap
   - weight by active family importance if needed
3. assignee-to-family compare:
   - compare one family against the semantic envelope of an owner’s portfolio
4. whitespace mapping:
   - identify areas with high semantic adjacency but low active enforceable density

### Guardrails

1. no comparison score should collapse claim and abstract spaces into one unlabeled number,
2. portfolio semantic overlap must be family-based, not publication-count based,
3. whitespace must be filtered by legal reality, not vector sparsity alone,
4. out-of-scope sampled semantic zones must be labeled as sampled.

### Stop Conditions

Stop if:

1. portfolio compare is dominated by duplicate family representations,
2. one vector space overwhelms the other without labeling,
3. whitespace scores are not joined to active legal coverage.

### Downstream Blast Radius

Wrong here corrupts:

1. compare workspace,
2. whitespace opportunity views,
3. semantic collision narratives,
4. family-owner comparison surfaces.

## Stage S10: Semantic Reliability Evaluation

### Goal

Determine whether the semantic layer is safe to expose in MVP.

### Retrieval reliability checks

1. `Recall_at_10`
2. `MRR`
3. `nDCG_at_10`
4. `duplicate_family_rate`
5. exact-vs-ANN recall agreement

### Strategic reliability checks

1. chronology classification precision
2. legal-status join completeness
3. percentage of results with blocking-power context
4. false-current-threat rate on curated fixtures

### Comparison reliability checks

1. family-to-family overlap stability
2. portfolio overlap stability across reruns
3. whitespace gap stability after legal filtering
4. top-k cluster overlap stability

### Stop Conditions

Stop MVP exposure if:

1. duplicate-family rate remains high,
2. chronology or legal joins are incomplete in material share of results,
3. semantic comparison rankings are unstable across reruns,
4. `vector_claims` retrieval is not reliable enough for FTO messaging.

## Stage S11: MVP Promotion Rules

### Safe For MVP If

1. representative family collapse is fully enforced,
2. `vector_abstract` and `vector_claims` are clearly separated,
3. top-k retrieval quality is acceptable on curated fixtures,
4. duplicate-family rate is low,
5. chronology and legal gating are complete for strategic displays,
6. sampled semantic scope is clearly labeled where sampling is used,
7. comparison outputs remain explainable and drillable to family evidence.

### Unsafe For MVP If

1. raw similarity is shown as legal risk without chronology or legal status,
2. `vector_claims` and `vector_abstract` are blended into one opaque score,
3. embedding every publication creates result clutter,
4. whitespace results are not filtered by active legal density,
5. semantic comparison is unstable between repeated runs on the same snapshot.

## Workflow-Specific Safe-Use Conditions

### `text_to_family_semantic_search`

Safe if:
1. query goes to the correct vector space,
2. results are family-deduped,
3. chronology and legal overlays are attached.

Unsafe if:
1. free-text query is used to imply infringement directly,
2. only abstract-based similarity is shown for FTO.

### `family_to_family_semantic_search`

Safe if:
1. both families are shown with representative provenance,
2. overlap is labeled by vector space.

Unsafe if:
1. one unlabeled similarity score hides claim-vs-abstract divergence.

### `family_to_family_semantic_compare`

Safe if:
1. comparison shows abstract overlap, claim overlap, and deterministic overlays separately.

Unsafe if:
1. semantic overlap is mistaken for legal equivalence.

### `portfolio_to_portfolio_semantic_compare`

Safe if:
1. overlap is aggregated from family-level truth,
2. sampled scope and active legal density are disclosed.

Unsafe if:
1. publication duplication inflates overlap,
2. sampled semantic coverage is presented as full-corpus certainty.

### `semantic_whitespace_and_collision_mapping`

Safe if:
1. whitespace is filtered by active coverage, blocking power, and time,
2. uncovered growth areas are labeled as opportunities rather than guaranteed freedom.

Unsafe if:
1. whitespace is defined only as low vector density.

## Minimal Release Order

If the team needs the safest release order:

1. `text_to_family_semantic_search`
2. `family_to_family_semantic_search`
3. `family_to_family_semantic_compare`
4. `portfolio_to_portfolio_semantic_compare`
5. `semantic_whitespace_and_collision_mapping`

This order is recommended because:

1. search is easier to validate than portfolio comparison,
2. family-level semantics are easier to explain than portfolio overlap,
3. whitespace requires the strongest deterministic overlays and therefore should ship last.

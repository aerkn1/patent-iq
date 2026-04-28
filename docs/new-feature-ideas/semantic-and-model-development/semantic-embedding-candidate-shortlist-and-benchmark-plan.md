# Semantic Embedding Candidate Shortlist And Benchmark Plan

## Purpose

Define the concrete embedding candidates, evaluation procedure, and promotion thresholds for PatentIQ semantic runtime promotion.

This note operationalizes:

1. [semantic-embedding-model-selection-decision.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md)
2. [phases/phase-01-semantic-runtime-foundation.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md)
3. [phases/phase-02-semantic-reranking-and-structured-summaries.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/phases/phase-02-semantic-reranking-and-structured-summaries.md)

## Current Semantic Reality

PatentIQ is currently:

1. family-first
2. abstract-dominant
3. claim-space real but narrow
4. legally and chronologically strong in overlays
5. not yet promoted to a real embedding + ANN runtime

This means model selection must optimize for:

1. real retrieval usefulness
2. explainable legal-safe reranking
3. honest coverage boundaries
4. family-first evaluation

## Evaluation Assets To Use

### Canonical evaluation registries

1. [semantic_eval_fixture_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_fixture_registry.parquet)
2. [semantic_eval_pair_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_pair_registry.parquet)

### Runtime context and corpus

1. [silver_family_text_representative.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet)
2. [silver_semantic_sampling_eligibility.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet)
3. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
4. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
5. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)

### Baseline runtime artifacts

1. [vec_query_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet)
2. [vec_embedding_manifest.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_embedding_manifest.json)
3. [vec_ann_index_manifest.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json)

## Candidate Shortlist

## `vector_abstract` candidates

### Candidate A: lexical baseline

Role:

1. required baseline only

Use:

1. exact-scan local fallback
2. sanity floor for evaluation

Why include:

1. deterministic
2. cheap
3. regression-safe
4. proves whether the promoted models actually add value

### Candidate B: strong general retrieval embedding model

Role:

1. default recommended production candidate for abstract-space

Expected profile:

1. sentence embedding or retrieval embedding model
2. strong semantic retrieval behavior on technical prose
3. good multilingual or translation-robust behavior is a bonus

Why include:

1. abstract-space is the dominant PatentIQ semantic corpus
2. recent retrieval literature suggests modern general models can outperform older patent-specific embeddings for broad search tasks

### Candidate C: optional patent-specific abstract encoder

Role:

1. challenger, not the default assumption

Why include:

1. to test whether patent-specific inductive bias helps on PatentIQ abstract fixtures
2. to avoid assuming general models always win in this corpus

## `vector_claims` candidates

### Candidate D: lexical baseline

Role:

1. same regression floor as abstract-space

### Candidate E: PatentSBERTa-family

Role:

1. default recommended production candidate for claim-space

Why include:

1. retrieval-native architecture
2. patent semantic similarity focus
3. best current fit for `vector_claims` in PatentIQ

### Candidate F: PatentBERT baseline

Role:

1. research and offline comparison baseline

Why include:

1. strong patent-domain encoder
2. useful benchmark even if not the likely production winner

Why not production default:

1. not the cleanest retrieval-first runtime fit
2. better as a comparison and possible future fine-tune source

### Candidate G: SEARCHFORMER-style lane

Role:

1. optional later benchmark for prior-art or invalidity workflows

Why not include in first general runtime promotion:

1. objective is narrower than PatentIQ’s current semantic runtime
2. should not block general discovery/comparison promotion

## Benchmark Structure

The benchmark must be split by vector space and workflow.

### Abstract-space benchmark tasks

1. `text_to_family_semantic_search`
2. `family_to_family_semantic_search`
3. `family_to_family_semantic_compare`
4. portfolio exploration and neighborhood sanity

Primary eval fixture groups:

1. `abstract_active_discovery`
2. `dead_family_suppression`
3. `pending_family_watch`
4. `partially_lapsed_watch`

### Claim-space benchmark tasks

1. `text_to_family_semantic_search`
2. `family_to_family_semantic_compare`

Primary eval fixture groups:

1. `claim_active_discovery`

### Pair benchmark tasks

From [semantic_eval_pair_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_pair_registry.parquet):

1. same-field pair coherence
2. family-to-family comparison stability
3. compare-overlap usefulness before legal reranking

## Evaluation Procedure

## Stage 1: raw retrieval benchmark

For each candidate and each vector space:

1. encode query fixtures
2. retrieve top-k family neighbors from the corresponding vector space
3. record raw similarity outputs

Use:

1. exact-scan first
2. ANN only after exact ranking is established

Metrics:

1. recall@10
2. recall@20
3. MRR@10
4. same-field hit rate
5. anchor-family self-exclusion correctness

## Stage 2: legal/context reranking benchmark

For top-k raw neighbors:

1. join legal status
2. join chronology
3. join blocking power
4. join OECD percentile
5. apply workflow-specific reranking rules

Metrics:

1. legal join completeness
2. chronology join completeness
3. blocking-context completeness
4. dead-family suppression success
5. pending-family caveat success
6. partially-lapsed caveat success

## Stage 3: workflow-specific usefulness review

Evaluate separately for:

1. discovery workflows
2. comparison workflows
3. current-threat gated workflows

Metrics:

1. top-10 reviewer usefulness
2. strategic false-positive rate
3. dead/current-threat violation rate
4. vector-space labeling completeness

## Stage 4: ANN approximation benchmark

Only after exact-scan winner is selected:

1. build ANN on the winning model
2. compare ANN top-20 versus exact top-20

Metrics:

1. exact-vs-ANN recall agreement at top-20
2. latency reduction
3. ANN candidate loss by workflow

## Promotion Thresholds

## Common thresholds

These must be satisfied before promotion:

1. vector-space labeling completeness `= 100%`
2. legal-status join completeness `>= 99.0%`
3. chronology join completeness `>= 99.0%`
4. blocking-context completeness `>= 95.0%`
5. exact-vs-ANN recall agreement at top-20 `>= 0.95`
6. duplicate family rate `<= 1.0%`

## Abstract-space thresholds

The winning abstract model should:

1. beat the lexical baseline on recall@20
2. beat the lexical baseline on MRR@10
3. maintain dead-family suppression success `>= 0.99`
4. maintain pending and partial-lapse caveat correctness `>= 0.98`

## Claim-space thresholds

The winning claim model should:

1. beat the lexical baseline on claim-active fixture retrieval
2. improve pair coherence on same-field comparison
3. never be used to claim unsupported legal equivalence
4. preserve explicit abstention where claim-space is unavailable

## Rejection Rules

A candidate should be rejected if any of the following happen:

1. it underperforms lexical baseline on the core fixture set
2. it increases dead-family suppression failures materially
3. it weakens chronology or blocking-context completeness
4. it causes vector-space confusion in outputs
5. it performs well only on raw similarity but degrades after legal-safe reranking

## Rollback Rules

After promotion, rollback to the baseline if:

1. exact-vs-ANN agreement falls below `0.95`
2. legal join completeness falls below `0.99`
3. dead-family suppression failure rate exceeds `1%`
4. production query latency becomes unacceptable without accuracy gain

## Recommended First Benchmark Order

### Step 1

Abstract-space:

1. lexical baseline
2. chosen general retrieval model
3. optional patent-specific abstract challenger

### Step 2

Claim-space:

1. lexical baseline
2. PatentSBERTa-family
3. optional PatentBERT comparison baseline

### Step 3

Only after those are stable:

1. SEARCHFORMER-style claim/prior-art lane

## Expected Outcome

The expected best-fit outcome for PatentIQ is:

1. abstract-space winner: strong general retrieval model
2. claim-space winner: PatentSBERTa-family
3. lexical fallback retained for local reproducibility and regression testing
4. SEARCHFORMER reserved for later high-recall prior-art work

## Consumption

The chosen winners will feed:

1. Phase 01 promoted vector artifacts
2. Phase 02 reranking and semantic summaries
3. backend semantic retrieval repository and endpoint contracts
4. later semantic graph and semantic-collision intelligence

## Next Step

Implement the benchmark runner that:

1. reads Phase 00 fixtures
2. scores each candidate in exact mode
3. records raw metrics and workflow-specific failure cases
4. writes a promotion report artifact

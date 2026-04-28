# BGE-M3 And PatentSBERTa Local Installation, Storage, And Runtime Guide

## Purpose

Provide the concrete operating guide for the first promoted PatentIQ semantic runtime using:

1. `BGE-M3` for `vector_abstract`
2. `PatentSBERTa` for `vector_claims`

This note explains:

1. why this split is appropriate
2. how to install the models locally
3. how to generate and store outputs
4. what should be stored locally versus in production
5. which quality gates and tests must pass before promotion

This note is implementation-oriented and follows:

1. [semantic-embedding-model-selection-decision.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md)
2. [semantic-embedding-candidate-shortlist-and-benchmark-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md)
3. [phases/phase-01-semantic-runtime-foundation.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md)

## Decision

## Runtime split

### `vector_abstract`

Use:

1. `BAAI/bge-m3`

Why:

1. abstract-space is the dominant PatentIQ semantic corpus
2. BGE-M3 is a strong retrieval model
3. BGE-M3 supports:
   - dense vectors
   - sparse lexical weights
   - ColBERT-style multi-vector interaction
4. BGE-M3 handles long input up to `8192` tokens, which gives future expansion headroom beyond abstracts

Primary source:

1. https://huggingface.co/BAAI/bge-m3

### `vector_claims`

Use:

1. `AI-Growth-Lab/PatentSBERTa`

Why:

1. retrieval-native sentence-transformer style
2. directly aligned with patent similarity use
3. better first fit for claim-space than PatentBERT

Primary source:

1. https://huggingface.co/AI-Growth-Lab/PatentSBERTa

## One important storage refinement

The BGE-M3 feature set is attractive, but PatentIQ should not store all three output modes at full corpus scale immediately.

### What to store first

1. full-corpus dense embeddings
2. sparse lexical output only if it is stored in an index-oriented representation
3. ColBERT or multi-vector outputs only for reranking or a bounded hot subset

### What not to do initially

Do not persist full-corpus ColBERT-style token vectors for all semantic families as a first release.

Why:

1. storage cost will be very large
2. write and load time will be large
3. reranking only needs top-k candidates, not the full corpus all the time

## Recommended retrieval architecture

## Abstract runtime

### Stage 1

Use BGE-M3 dense vectors for full-corpus shortlist retrieval.

### Stage 2

Combine with one of the following:

1. BGE-M3 sparse lexical retrieval
2. BM25 or another lexical index over the same representative abstracts

### Stage 3

For top `50-100` candidates only:

1. rerank with BGE-M3 multi-vector or weighted fusion
2. then apply PatentIQ legal and chronology reranking

## Claim runtime

Use PatentSBERTa dense retrieval for claim-backed families only.

Then:

1. apply family/legal gating
2. keep claim-space clearly labeled
3. abstain where claim-space is not available

## Local Installation Guidance

## Python dependency policy

Use local model execution, not API calls, for the canonical ETL build.

Why:

1. PatentIQ corpus embedding is batch-heavy
2. version control and reproducibility matter
3. cost and latency are better controlled locally

## Local install for BGE-M3

Recommended package path:

1. `sentence-transformers`
2. `transformers`
3. `torch`

Phase note:

1. the current PatentIQ `dense-only` promotion path uses `BGE-M3` through `sentence-transformers`
2. `FlagEmbedding` is deferred to the later hybrid phase when sparse and multi-vector outputs are promoted

Suggested commands:

```bash
cd etl
poetry add sentence-transformers transformers torch
```

Alternative if not using Poetry for this component:

```bash
pip install -U sentence-transformers transformers torch
```

Then load:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-m3")
```

Notes:

1. this is the correct dense-only runtime choice for the current Phase 01 promotion
2. on CPU-only environments, keep conservative batch sizes
3. add `FlagEmbedding` only when sparse lexical and multi-vector reranking are being implemented

## Local install for PatentSBERTa

Recommended package path:

1. `sentence-transformers`

Suggested commands:

```bash
cd etl
poetry add sentence-transformers transformers torch
```

Alternative:

```bash
pip install -U sentence-transformers transformers torch
```

Then load:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("AI-Growth-Lab/PatentSBERTa")
```

## Model download behavior

Both models will normally download from Hugging Face on first use and then cache locally.

Default local cache is typically under:

1. `~/.cache/huggingface/`

For PatentIQ reproducibility, record in the runtime manifest:

1. model id
2. revision or commit hash if pinned
3. library version
4. pooling strategy
5. normalization policy
6. max sequence length

## Local ETL Output Design

## Abstract outputs

### Dense corpus artifact

Store:

1. `vec_family_embeddings_abstracts_dense.parquet`

Recommended columns:

1. `docdb_family_id`
2. `vector_space`
3. `embedding_model`
4. `embedding_model_version`
5. `embedding_runtime`
6. `queryable_text_hash`
7. `token_count`
8. `text_provenance`
9. `text_source_type`
10. `is_abstract_fallback`
11. `family_earliest_priority_date`
12. `primary_wipo_field`
13. `owner_name_harmonized`
14. `family_ui_blocking_power_score`
15. `oecd_quality_percentile`
16. `family_composite_status`
17. dense embedding payload

### Sparse lexical artifact

Do not store sparse output as a giant free-form JSON blob by default.

Preferred forms:

1. `vec_family_embeddings_abstracts_sparse.parquet`
   - `docdb_family_id`
   - `token_ids`
   - `token_weights`
2. or a dedicated lexical index build directory:
   - `etl/data/vectors/indexes/abstract_sparse/`

If using a search engine backend later, this can be converted into:

1. OpenSearch
2. Vespa
3. another inverted-index store

### Multi-vector rerank artifact

Do not persist full-corpus multi-vector outputs first.

Recommended first implementation:

1. compute on demand for query and top-k candidates
2. optionally cache for hot families only

If later persisted, store as:

1. `vec_family_embeddings_abstracts_colbert_hotset.parquet`

for a bounded hot subset only.

## Claim outputs

### Dense corpus artifact

Store:

1. `vec_family_embeddings_claims_dense.parquet`

Recommended columns mirror the abstract dense artifact, with:

1. `vector_space = vector_claims`
2. claim-specific provenance
3. explicit coverage labeling

## Shared manifests

### Embedding manifest

Store:

1. `vec_embedding_manifest.json`

Should include:

1. release id
2. corpus snapshot
3. model ids by vector space
4. model revisions
5. max length
6. pooling policy
7. normalization policy
8. row counts
9. vector dimensions
10. output paths

### Runtime and index manifest

Store:

1. `vec_ann_index_manifest.json`

Should include:

1. dense index method
2. sparse index method
3. rerank policy
4. top-k shortlist size
5. top-k rerank size
6. exact-vs-ANN validation metrics

### Query registry

Store:

1. `vec_query_registry.parquet`

This should come from Phase 00 fixtures and be reused for benchmark and release validation.

## Recommended Local File Layout

Use:

1. `etl/data/vectors/`

Suggested structure:

```text
etl/data/vectors/
  vec_family_embeddings_abstracts_dense.parquet
  vec_family_embeddings_abstracts_sparse.parquet
  vec_family_embeddings_claims_dense.parquet
  vec_query_registry.parquet
  vec_embedding_manifest.json
  vec_ann_index_manifest.json
  indexes/
    abstract_dense/
    abstract_sparse/
    claims_dense/
  caches/
    abstract_colbert_hotset/
```

## Production Storage Design

## Canonical persisted artifacts

In production, persist:

1. dense vector parquet shards in object storage
2. release-pinned manifests
3. ANN indexes or vector DB snapshots
4. sparse lexical index snapshots

Recommended pattern:

1. object storage for canonical release artifacts
2. vector/search service loads the active release

### Suggested production pattern

Canonical release artifacts:

1. Azure Blob or equivalent object storage
2. versioned by release id and corpus snapshot

Serving layer:

1. backend semantic service
2. local ANN index or dedicated vector/search engine

### Dense serving choices

1. local FAISS or HNSW index snapshots
2. Qdrant / Milvus / similar vector service

### Sparse serving choices

1. OpenSearch
2. Vespa
3. another lexical or hybrid search backend

### Rerank layer

1. BGE-M3 multi-vector rerank for top-k abstract candidates
2. legal and chronology rerank after semantic shortlist

## What should not be production-only

Do not make production the only place where embeddings can be built.

The canonical build must remain reproducible locally or on your controlled batch infrastructure so that:

1. release artifacts can be regenerated
2. manifests remain trustworthy
3. training and evaluation stay consistent

## Quality Gates

These are the minimum release gates for the promoted semantic runtime.

## Corpus and artifact integrity

1. duplicate family rate `<= 1.0%`
2. empty-text row rate `= 0`
3. vector-space labeling completeness `= 100%`
4. manifest/output count reconciliation `= exact`

## Context completeness

1. legal-status join completeness `>= 99.0%`
2. chronology join completeness `>= 99.0%`
3. blocking-context completeness `>= 95.0%`
4. OECD context completeness should be tracked and should remain high enough for rerank features

## Retrieval quality

1. promoted model must beat lexical baseline on Phase 00 fixture usefulness
2. dead-family suppression success `>= 0.99`
3. pending and partial-lapse caveat correctness `>= 0.98`
4. exact-vs-ANN recall agreement at top-20 `>= 0.95`

## Honesty and safety gates

1. claim-space must remain explicitly labeled
2. abstract-space must remain explicitly labeled
3. unsupported workflows must abstain
4. no semantic result should appear without legal and chronology overlays in analyst-facing product flows

## Tests

## Installation tests

1. model imports succeed
2. first local load succeeds
3. model id and revision are captured in manifests

## Artifact tests

1. parquet row counts reconcile to eligible families
2. no duplicate `docdb_family_id` within a vector space
3. query registry rows are non-empty
4. embedding dimensions are consistent

## Retrieval tests

1. exact retrieval against Phase 00 fixtures
2. pair-registry coherence checks
3. legal suppression and caveat checks
4. ANN versus exact agreement checks

## Release tests

1. backend can load manifests
2. backend can load indexes
3. retrieval returns family ids plus legal context
4. returned rows are provenance-labeled

## Implementation Sequence

## Step 1

Install and pin:

1. `BAAI/bge-m3`
2. `AI-Growth-Lab/PatentSBERTa`

## Step 2

Promote local exact-scan embedding generation:

1. BGE-M3 dense abstract embeddings
2. PatentSBERTa dense claim embeddings

## Step 3

Add lexical hybrid support for abstracts:

1. sparse BGE-M3 or BM25-style index

## Step 4

Add top-k reranking:

1. BGE-M3 multi-vector rerank on abstract candidates
2. legal and chronology rerank after semantic scoring

## Step 5

Only after the exact benchmark is good:

1. add ANN indexes
2. run ANN agreement gate

## Practical Bottom Line

The best first implementation is:

1. `BGE-M3` for abstract dense retrieval
2. `PatentSBERTa` for claim dense retrieval
3. lexical hybrid support in abstract-space
4. multi-vector rerank only for top-k
5. local canonical build, production service loading release artifacts

This gives PatentIQ the strongest practical semantic promotion path without overcommitting to full-corpus multi-vector storage too early.

# Phase 01 MVP Partial-Corpus Operating Note

## Date

2026-04-06

## Purpose

Record the decision to proceed with a bounded MVP semantic corpus rather than waiting for a full clean abstract build across every planned abstract phase.

This note exists so the current state is explicit rather than silently treated as a canonical full-corpus Phase 01 release.

## Decision

For MVP demonstration and backend/frontend integration work, PatentIQ will temporarily use:

1. a salvaged abstract embedding artifact from `abstract phase 00`,
2. a continued claim embedding build under the new phased and chunked runtime,
3. explicit caveat labeling that the abstract corpus is only a partial promoted sample, not a full clean abstract release.

## Accepted Abstract Artifact

Use:

- [vec_family_embeddings_abstracts_phase_00_of_10_mvp_demo.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/phases/abstracts/vec_family_embeddings_abstracts_phase_00_of_10_mvp_demo.parquet)

Do not treat as canonical:

- `vec_family_embeddings_abstracts.parquet`
- full 10-phase abstract completion
- ANN benchmark baseline

## Why This Was Needed

The full abstract phase `00` run on Apple `MPS` required:

1. phased chunking,
2. multiple resumptions after `MPS` memory pressure,
3. a schema-normalized merge after early chunk files inferred different physical types.

That produced a merged artifact with duplicate families because the same chunk filenames were reused across different chunking configurations.

The duplicate-merged output was then salvage-audited by:

1. deduping to one row per `docdb_family_id`,
2. reconciling the deduped result back to the expected phase membership from `_tmp_semantic_base.parquet`.

## Salvage Audit Result

### Phase scope

Expected unique abstract families in phase `00`:

- `172,508`

### Deduped usable artifact

Usable unique abstract family embeddings:

- `168,924`

Missing expected families after dedupe:

- `3,584`

Unexpected extra families:

- `0`

### Quality result

Accepted for MVP demo and integration:

1. duplicate families after dedupe: `0`
2. embedding dimensions: `1024..1024`
3. null core semantic fields: `0`
4. primary field completeness: `100%`

Known incompleteness:

1. missing expected phase members: `3,584`
2. chronology anchor completeness: `84.63%`
3. blocking context completeness: `84.63%`

## Policy Interpretation

This artifact is:

1. acceptable for MVP demonstration,
2. acceptable for retrieval/UI/backend wiring,
3. acceptable for semantic compare proof-of-shape,
4. not acceptable as the final canonical abstract corpus release.

This artifact is not sufficient for:

1. final ANN promotion quality claims,
2. exact abstract-space coverage claims,
3. production release without caveat metadata.

## Required MVP Labeling

Any consumer of this artifact must expose:

1. `semantic_corpus_mode = partial_mvp_demo`
2. `vector_space = vector_abstract`
3. `sampling_policy_version = phase00_partial_salvage_2026_04_06`
4. `abstract_phase_coverage = phase_00_only`
5. `known_missing_family_count = 3584`

## Archived Non-Canonical Artifact

The duplicate-merged phase artifact should remain archived only for traceability:

- [vec_family_embeddings_abstracts_phase_00_of_10_raw_duplicate_merge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/phases/abstracts/vec_family_embeddings_abstracts_phase_00_of_10_raw_duplicate_merge.parquet)

## Claims Build Policy From This Point

Claims should continue under the same safer runtime pattern:

1. phased execution
2. chunked checkpoint writes
3. one stable configuration held constant through a phase
4. `MPS` device with conservative batch pressure

### Current recommended claim config

1. `SEMANTIC_DEVICE=mps`
2. `SEMANTIC_PHASE_COUNT=3`
3. `SEMANTIC_FETCH_CHUNK_ROWS=1024`
4. `SEMANTIC_ENCODE_CHUNK_ROWS=128`
5. `SEMANTIC_BATCH_SIZE=16`
6. `OMP_NUM_THREADS=1`
7. `KMP_DUPLICATE_LIB_OK=TRUE`

## Next Step

Proceed with:

1. claim phase `00`
2. claim phase `01`
3. claim phase `02`
4. claims audit

Then decide whether to:

1. keep abstract MVP partial mode for demo,
2. or rebuild the full abstract set later on stronger hardware or with a stricter single-config rerun.

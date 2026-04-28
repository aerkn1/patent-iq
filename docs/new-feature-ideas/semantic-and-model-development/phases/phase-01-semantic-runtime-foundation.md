# Phase 01: Semantic Runtime Foundation

## Goal

Promote a real semantic vector runtime in place of placeholder embeddings.

## Input Data

1. [silver_family_text_representative.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet)
2. [silver_semantic_sampling_eligibility.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet)
3. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
4. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
5. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)

## Actual Metrics Used

### Representative text metrics

1. `representative_claim_1_en`
2. `representative_abstract_en`
3. `text_provenance`
4. `is_abstract_fallback`
5. `representative_stage`

### Context metrics attached to retrieval results

1. `family_ui_blocking_power_score`
2. `family_status`
3. `primary_wipo_field`
4. `quality_index_4_percentile` or equivalent OECD percentile
5. chronology anchor such as `family_earliest_priority_date`

## Config And Policy

1. keep `vector_claims` and `vector_abstract` separate
2. claims only from EP grant claims in MVP
3. abstract fallback remains allowed and must be labeled
4. embed only family representatives, not all publications
5. use backend or dedicated vector service, not client-side ANN

## Generation Logic

1. select eligible families from semantic eligibility mart
2. encode claim and abstract payloads with a patent-specialized embedding model
3. build two ANN indexes
4. store vector manifests with:
   - model name
   - model version
   - corpus snapshot
   - vector space
   - sampling policy
5. expose a retrieval service returning family IDs and lightweight evidence

## Expected Outputs

1. `vec_family_embeddings_claims.parquet`
2. `vec_family_embeddings_abstracts.parquet`
3. `vec_embedding_manifest.json`
4. `vec_ann_index_manifest.json`
5. `vec_query_registry`
6. backend semantic retrieval contract

## Where Outputs Are Consumed

1. semantic search APIs
2. family compare UI
3. portfolio compare UI
4. Phase 02 reranking
5. Phase 07 semantic graph build

## Quality Gates

1. `duplicate_family_rate <= 1.0%`
2. exact-vs-ANN recall agreement at top-20 `>= 0.95`
3. legal-status join completeness `>= 99.0%`
4. chronology join completeness `>= 99.0%`
5. blocking-context completeness `>= 95.0%`
6. results always label vector space and provenance

## Stop Conditions

1. one unlabeled blended semantic score is exposed
2. legal joins are incomplete in material share of results
3. claim-space is used for unsupported workflows

# Phase 02: Semantic Reranking And Structured Summaries

## Goal

Convert raw semantic neighbors into explainable, strategy-safe semantic outputs.

## Input Data

1. vector outputs from Phase 01
2. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
3. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
4. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
5. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)

## Actual Metrics Used

1. similarity score from vector search
2. family legal status
3. active branch / enforceability context
4. blocking power percentile
5. OECD quality percentile
6. chronology anchors

## Config And Policy

1. never show semantic hits without legal and chronology overlays
2. comparison outputs must show claim and abstract overlap separately
3. abstain when claim coverage is absent for claim-oriented workflows
4. whitespace views must filter by active legal density

## Generation Logic

1. retrieve raw top-k neighbors
2. dedupe to family level
3. attach legal, chronology, blocking, and OECD context
4. rerank by workflow-specific policy
5. generate structured summary fields such as:
   - function
   - component
   - application
   - segment anchors
6. mark unsupported or low-confidence outputs with abstention flags

## Expected Outputs

1. `vec_raw_match_results`
2. `vec_semantic_comparison_rollup`
3. `semantic_summary_family`
4. `semantic_abstention_registry`

## Where Outputs Are Consumed

1. semantic compare workspace
2. semantic collision narratives
3. future whitespace mapping
4. semantic explainability panels

## Quality Gates

1. `>= 95%` of exposed results have complete context payload
2. `0` unlabeled claim-vs-abstract blended compare outputs
3. family compare top-k stability Jaccard `>= 0.85`
4. portfolio compare top-k stability Jaccard `>= 0.80`
5. false-current-threat rate on curated fixtures `<= 2.0%`

## Stop Conditions

1. semantic overlap is presented as legal equivalence
2. dead families surface as current threats without explicit context
3. whitespace is driven by vector sparsity alone

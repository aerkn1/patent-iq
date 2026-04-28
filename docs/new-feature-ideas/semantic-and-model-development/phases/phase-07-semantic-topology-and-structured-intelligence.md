# Phase 07: Semantic Topology And Structured Intelligence

## Goal

Add graph-aware semantic features and reusable semantic summaries on top of the promoted runtime.

## Input Data

1. vector artifacts from Phase 01
2. raw semantic match graph
3. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
4. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
5. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)

## Actual Metrics Used

1. semantic degree
2. bridge score
3. local density
4. cluster assignment
5. cluster drift through time
6. structured semantic summary fields

## Config And Policy

1. graph features augment, not replace, tabular model features
2. cluster outputs remain family-first
3. summaries must stay grounded to source text provenance

## Generation Logic

1. build semantic graph from top-k neighborhood relations
2. compute graph metrics
3. assign cluster labels
4. generate structured family summaries
5. track cluster history over time

## Expected Outputs

1. `vec_semantic_graph_features.parquet`
2. `semantic_summary_family.parquet`
3. `semantic_cluster_history.parquet`

## Where Outputs Are Consumed

1. future influence models
2. hidden-gem ranking
3. portfolio semantic diversification views
4. analyst compare workflows

## Quality Gates

1. graph feature coverage `>= 95%` of embedded families
2. cluster rerun stability NMI `>= 0.80`
3. summary generation success `>= 98%` of embedded families
4. summary provenance completeness `100%`

## Stop Conditions

1. graph covers weak minority of embedded families
2. cluster drift too high on same-snapshot reruns
3. summaries lose evidence grounding

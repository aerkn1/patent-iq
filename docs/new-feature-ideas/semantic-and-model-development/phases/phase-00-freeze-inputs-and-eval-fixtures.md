# Phase 00: Freeze Inputs And Eval Fixtures

## Goal

Freeze reproducible semantic and ML evaluation inputs before promoted runtime or training work starts.

## Input Data

### Semantic fixtures

1. [silver_family_text_representative.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet)
   - `docdb_family_id`
   - `representative_appln_id`
   - `representative_publn_id`
   - `representative_claim_1_en`
   - `representative_abstract_en`
   - `text_provenance`
   - `is_abstract_fallback`
2. [silver_semantic_sampling_eligibility.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet)
   - `docdb_family_id`
   - `is_semantic_candidate`
   - `is_in_vector_sample`
3. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
   - current legal context
   - blocking and OECD overlays
   - field and chronology context

### Forecast fixtures

1. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
2. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
3. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
4. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
5. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
6. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)

## Config And Policy

1. freeze one `training_snapshot_id`
2. record `snapshot_cutoff_date`
3. use time-aware splits by default
4. group by `docdb_family_id` where duplicate family members can leak
5. stratify by jurisdiction and field where model scope needs it

## Implementation Logic

### Semantic

1. build curated fixture sets for:
   - text-to-family search
   - family-to-family compare
   - portfolio overlap
   - false-current-threat suppression
2. store expected relevant families and expected exclusions
3. separate fixtures by vector space where needed

### Models

1. build `ml_split_registry`
2. declare:
   - train
   - validation
   - locked test
3. store split policy per model scope
4. record all source table row counts and hashes

## Expected Outputs

1. `ml_split_registry`
2. `training_snapshot_manifest`
3. `semantic_eval_fixture_registry`
4. `semantic_eval_queries`
5. `semantic_eval_expected_matches`

## Downstream Consumers

1. semantic ANN evaluation
2. model training pipelines
3. calibration builders
4. regression and release tests

## Quality Gates

1. `100%` promoted artifacts trace to one frozen snapshot
2. `0` detected family leakage across train and test
3. fixture coverage includes all supported semantic workflows
4. source row-count manifest is complete for every training table

## Stop Conditions

1. family leakage detected
2. semantic fixtures biased to one workflow only
3. snapshot reproducibility cannot be proven

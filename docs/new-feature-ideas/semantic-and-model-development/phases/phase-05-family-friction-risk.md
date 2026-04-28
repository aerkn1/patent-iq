# Phase 05: Family Friction Risk

## Goal

Predict post-grant or family-level friction exposure.

## Input Data

1. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
2. EP register overlay marts
3. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
4. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
5. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)

## Actual Metrics Used

1. early post-grant citation velocity
2. citing-assignee concentration
3. generality and radicalness
4. legal durability and active breadth
5. attacker density from enriched citation network
6. EP opposition or friction overlay signals where applicable

## Config And Policy

1. prediction unit is family-first
2. rare-event evaluation uses PR-focused metrics
3. jurisdiction-aware inputs stay visible in explanation payloads

## Training Logic

1. build family-level friction labels
2. materialize rare-event-safe feature table
3. train imbalance-aware classifier
4. calibrate probabilities
5. expose risk buckets and top drivers

## Expected Outputs

1. `ml_label_family_friction_event.parquet`
2. `ml_feature_family_friction_risk.parquet`
3. `ml_prediction_family_friction_risk.parquet`

## Where Outputs Are Consumed

1. portfolio high-friction exposure summary
2. family watchlists
3. legal-intelligence drilldowns

## Quality Gates

1. PR-AUC `>= 3x` positive-rate baseline
2. precision in top-5% risk bucket `>= 2x` baseline prevalence
3. calibration error `<= 0.06`
4. risk bucket ordering stable across reruns

## Stop Conditions

1. evaluation relies on accuracy or ROC-AUC only
2. positive-event support too weak for claimed slices
3. explanation payload cannot separate key drivers

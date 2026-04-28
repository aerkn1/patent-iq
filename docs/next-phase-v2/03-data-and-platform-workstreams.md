# Data And Platform Workstreams

## Workstream 1: Canonical Entity Layer

### Goal

Create the minimum trustworthy entity model required for family-first and owner-aware analytics.

### Required entities

1. `family_time`
2. `legal_status_events`
3. `assignee_harmonized`
4. `corporate_tree`
5. `oecd_quality_indicators_family`
6. `oecd_quality_cohort_stats`
7. `tech_market_filing_grant_trends`

### Tasks

1. Define canonical family IDs and family model rules.
2. Resolve earliest priority, publication, grant, and expiry anchors.
3. Map application-level OECD inputs to family-level facts.
4. Create assignee normalization and parent-rollup logic.
5. Add jurisdiction-aware legal status normalization.

## Workstream 2: Metric Contract Rebuild

### Goal

Replace partial or ambiguous analytics definitions with explicit API-ready contracts.

### Required contract fields

1. `counting_unit`
2. `family_model`
3. `overlap_policy`
4. `lag_warning`
5. `data_completeness_pct`
6. `cohort_key`
7. `score_components`

### Tasks

1. Rebuild citation metrics as family-aware by default.
2. Separate raw and adjusted citations.
3. Implement pendency-aware grant-rate eligibility logic.
4. Add non-exclusive category disclosure for field totals.
5. Enforce office-specific quality-indicator compatibility.

## Workstream 3: Backend Service Refactor

### Goal

Move the current service layer to explicit, composable analytics services instead of endpoint-specific logic islands.

### Service targets

1. Patent overview service,
2. Patent analysis service,
3. Portfolio overview service,
4. Portfolio analytics service,
5. Comparison service,
6. Trend intelligence service,
7. Quality intelligence service.

### Tasks

1. Split data access from metric assembly.
2. Consolidate duplicated family/citation logic.
3. Add typed response schemas for all new analytics surfaces.
4. Introduce feature flags for rebuilt endpoints.
5. Maintain backward-compatible fallbacks where needed during rollout.

## Workstream 4: Data Performance And Caching

### Goal

Ensure contest demos feel fast and stable even when deeper analytics are introduced.

### Tasks

1. Precompute heavy gold marts for hot dashboards.
2. Cache seeded portfolio and patent flows.
3. Benchmark cold and warm paths.
4. Add cache invalidation strategy per snapshot/version.
5. Guard against expensive repeated joins in request paths.

## Workstream 5: Validation And Observability

### Goal

Make metric failures visible before they reach UI or judges.

### Tasks

1. Add fixture-backed repository tests.
2. Add golden tests for family aggregation and OECD normalization.
3. Add API smoke tests for all critical workflows.
4. Log metric provenance and missing-data reasons.
5. Track endpoint latency and degraded-mode behavior.

## Suggested Technical Task Clusters

### Cluster P0-A: Family-first migration

1. Family aggregation helpers,
2. citation deduplication,
3. trend date backbone,
4. family/publication mode switch.

### Cluster P0-B: Assignee intelligence

1. Normalization rules,
2. corporate parent mapping,
3. owner/family join contracts,
4. citing-applicant rollups.

### Cluster P0-C: Quality and trend reliability

1. OECD ingestion,
2. cohort stats lookup,
3. grant-rate logic,
4. lag/completeness metadata.

### Cluster P1-A: Compare and cluster platform

1. Compare endpoints,
2. clustering pipeline,
3. AI label hooks,
4. report/export contracts.

## Workstream 6: Citation Forecast Model V2

### Goal

Retrain the 3-year and 5-year citation forecast models on a richer, V2-aligned feature schema that matches the rebuilt family-first product logic.

### Tasks

1. Replace the narrow inference feature table with a versioned V2 feature mart.
2. Build family, legal, technology, market, assignee, and OECD quality feature groups.
3. Compare LightGBM baseline against count-aware challengers where practical.
4. Recalibrate uncertainty intervals on the final selected model.
5. Expose feature contributions and model metadata through stable contracts.

### Required outputs

1. Training dataset spec,
2. train/validation/test split contract,
3. model cards for 3-year and 5-year horizons,
4. calibration report,
5. inference migration plan.

## Workstream 7: Azure Runtime And Artifact Delivery

### Goal

Ship a contest-ready Azure runtime that serves the product cheaply and transparently without moving heavy ETL or training into cloud infrastructure.

### Tasks

1. Define Blob or ADLS folder layout for Bronze, Silver, Gold, models, vectors, manifests, and Data Room downloads.
2. Implement backend manifest loading and release-pointer resolution.
3. Run DuckDB as the embedded analytics engine in the backend.
4. Run sampled semantic ANN retrieval in-process inside the backend service.
5. Keep temporary user/session/worklist state in memory only for MVP.

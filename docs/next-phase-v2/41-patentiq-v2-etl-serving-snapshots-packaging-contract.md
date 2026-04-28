# PatentIQ V2 ETL Serving Snapshots Packaging Contract

## Purpose

Define the ETL-side packaging stage that produces backend-ready serving databases for PatentIQ V2 so that:

1. the backend does not query remote Azure Blob parquet files directly at request time,
2. local and Azure runtimes consume the same released serving artifacts,
3. serving data is domain-split rather than monolithic,
4. serving snapshot generation is reproducible, versioned, and auditable,
5. backend startup only downloads the local serving datasets it actually needs.

This note extends:

1. [40-patentiq-v2-backend-serving-runtime-config-and-cloud-local-parity.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/40-patentiq-v2-backend-serving-runtime-config-and-cloud-local-parity.md)
2. [36-patentiq-v2-azure-deployment-and-release-blueprint.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/36-patentiq-v2-azure-deployment-and-release-blueprint.md)
3. [16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md)
4. [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md)

---

## 1. Why This Must Be An ETL Stage

Serving DuckDB snapshots should be built by ETL, not by the backend.

Why:

1. ETL already owns the data contracts and release artifacts,
2. serving databases should be deterministic outputs of a known release,
3. backend startup should resolve and consume artifacts, not shape them,
4. packaging logic belongs next to Gold/Silver/ML/Semantic production logic,
5. auditability is much better if serving DBs are formal ETL artifacts with stage manifests.

So the rule is:

1. backend never builds serving snapshots for itself,
2. ETL builds and certifies them,
3. backend only loads them.

---

## 2. Stage Recommendation

Add a dedicated ETL stage group for serving snapshot packaging.

Recommended stage name:

1. `serving-snapshots`

Accepted aliases if desired:

1. `serving_snapshots`
2. `backend-serving-artifacts`
3. `backend_serving_artifacts`

Preferred naming principle:

1. keep it aligned with existing ETL stage naming like:
   - `gold-market-semantic`
   - `semantic-ann`
   - `ml-phase0-foundation`
2. make the stage describe the artifact purpose, not just file format.

Recommended implementation placement:

1. `etl/src/patentiq_etl/serving/`
2. `etl/src/patentiq_etl/serving/run.py`
3. add stage wiring in [etl/scripts/run_stage.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/scripts/run_stage.py)

Suggested functions:

1. `run_serving_snapshots(settings)`
2. `build_core_serving_snapshot(settings)`
3. `build_semantic_serving_snapshot(settings)`
4. `build_market_serving_snapshot(settings)`

---

## 3. Output Contract

The stage should build and publish these artifacts.

Required outputs:

1. `core_serving.duckdb`
2. `semantic_serving.duckdb`
3. `market_serving.duckdb`
4. `serving_snapshot_manifest.json`
5. `serving_snapshot_audit.json`

Suggested local output directory:

1. `etl/data/serving/`

Suggested structure:

```text
etl/data/serving/
  core_serving.duckdb
  semantic_serving.duckdb
  market_serving.duckdb
  serving_snapshot_manifest.json
  serving_snapshot_audit.json
```

Suggested Azure Blob structure:

```text
serving/
  2026-04-06-serving/
    core_serving.duckdb
    semantic_serving.duckdb
    market_serving.duckdb
    serving_snapshot_manifest.json
    serving_snapshot_audit.json
```

---

## 4. Dependencies

The packaging stage should run only after required upstream marts and model/semantic artifacts are ready.

Minimum upstream dependencies:

1. Gold stage outputs required by the selected serving snapshots
2. the active forecast release metadata, if forecast-serving tables are included
3. the semantic release manifests, if semantic-serving metadata needs release alignment

Recommended dependency order:

1. `silver`
2. `gold`
3. `ml` or the current promoted forecast model release
4. `semantic`
5. `semantic-ann`
6. `serving-snapshots`
7. `publish`

Important nuance:

1. `serving-snapshots` does not need the raw vector parquet inside the `.duckdb` files,
2. but it may need semantic release metadata and context marts to align serving contracts.

---

## 5. Domain Split

The packaging stage should not build one giant all-purpose serving database.

It should build three domain-oriented serving databases.

## 5.1 `core_serving.duckdb`

Purpose:

1. family page serving
2. publication evidence serving
3. family-first forecast serving
4. portfolio page serving
5. report metadata serving for non-semantic, non-market sections

Include directly from Gold:

1. `gold_family_summary`
2. `gold_family_blocking_power`
3. `gold_family_heritage_summary`
4. `gold_portfolio_summary`
5. `gold_portfolio_forecast_summary`
6. `gold_portfolio_heritage_summary`
7. `gold_portfolio_threat_matrix`

Include directly from Silver when compact and serving-safe:

1. `silver_family_status_pt`
2. `silver_family_owner_bridge`
3. `silver_assignee_harmonized`
4. `silver_family_wipo_fields`
5. `silver_family_citation_metrics`
6. `silver_family_coverage_metrics`
7. `silver_family_member_publications`
8. `silver_family_oecd_quality`

Build serving-derived tables where raw sources are too heavy:

1. `family_status_history_serving`
2. `branch_status_summary_serving`
3. `publication_evidence_serving`
4. `family_forecast_features_serving`
5. `family_compare_current_serving`

`family_compare_current_serving` should be a current-snapshot serving table built from:

1. `gold_family_summary`
2. `gold_family_blocking_power`
3. `gold_family_compare_pit`

Purpose:

1. low-latency family compare serving,
2. precomputed cohort-relative blocking posture,
3. precomputed lifecycle-aware legal durability percentile,
4. precomputed priority-year x field citation-heritage percentile,
5. one-row-per-family current compare payloads for backend compare lenses.

## 5.2 `semantic_serving.duckdb`

Purpose:

1. semantic hit enrichment
2. semantic compare context
3. semantic evidence for reports and family pages

Include directly:

1. `gold_semantic_match_context`

Optional serving-derived additions:

1. `semantic_family_resolution_serving`
2. `semantic_compare_context_serving`

Do not include:

1. abstract embedding parquet
2. claim embedding parquet
3. ANN `.bin` indexes
4. ANN family-id arrays

Reason:

1. DuckDB is the context layer here, not the vector retrieval engine.

## 5.3 `market_serving.duckdb`

Purpose:

1. market overview
2. market segment views
3. field and trend views
4. market sections in compare and reports

Include directly from Gold:

1. `gold_market_intelligence_overview`
2. `gold_market_intelligence_segments`
3. `gold_market_intelligence_timeseries`
4. `gold_portfolio_field_timeseries`
5. `gold_family_field_contributions`
6. `gold_family_field_contributions_timeseries`
7. `gold_family_blocking_power_timeseries`

Only include Silver if a route truly needs a compact non-Gold support table.

---

## 6. Build Method

Each serving snapshot should be built by:

1. opening a fresh local DuckDB file,
2. attaching only the required source parquet files,
3. creating stable serving tables or views,
4. materializing final serving tables inside the target `.duckdb`,
5. running snapshot-specific audits,
6. compacting and closing the DB.

Recommended build flow per snapshot:

1. create empty target DuckDB
2. register source Gold/Silver parquet inputs as temporary views
3. create serving tables with stable names
4. create lightweight indexes only if useful for DuckDB lookup paths
5. run `ANALYZE`
6. optionally run `CHECKPOINT`
7. close DB
8. record audit metrics

Important design rule:

1. materialize final serving tables,
2. do not rely on runtime `read_parquet(...)` views inside the finished serving snapshots.

Why:

1. the finished `.duckdb` should be self-contained,
2. backend should not need the original source parquet files once the serving DBs are built.

---

## 7. Table Naming Inside The Serving DBs

Use serving-stable names rather than leaking raw file names directly.

Recommended naming:

### Core

1. `family_summary`
2. `family_blocking_power`
3. `family_heritage_summary`
4. `portfolio_summary`
5. `portfolio_forecast_summary`
6. `portfolio_heritage_summary`
7. `portfolio_threat_matrix`
8. `family_status_pt`
9. `family_owner_bridge`
10. `assignee_harmonized`
11. `family_wipo_fields`
12. `family_citation_metrics`
13. `family_coverage_metrics`
14. `family_member_publications`
15. `family_oecd_quality`
16. `family_status_history_serving`
17. `branch_status_summary_serving`
18. `publication_evidence_serving`
19. `family_forecast_features_serving`

### Semantic

1. `semantic_match_context`
2. `semantic_family_resolution_serving`
3. `semantic_compare_context_serving`

### Market

1. `market_intelligence_overview`
2. `market_intelligence_segments`
3. `market_intelligence_timeseries`
4. `portfolio_field_timeseries`
5. `family_field_contributions`
6. `family_field_contributions_timeseries`
7. `family_blocking_power_timeseries`

This keeps backend repositories independent from raw parquet filenames.

---

## 8. Snapshot Manifest Contract

The packaging stage should emit a dedicated serving manifest.

Suggested file:

1. `serving_snapshot_manifest.json`

Required fields:

```json
{
  "serving_release": "2026-04-06-serving",
  "contract_version": "1",
  "built_at": "2026-04-06T15:00:00Z",
  "source_gold_release": "2026-04-06-gold",
  "forecast_release": "family_future_citation_forecast_v2_2026-04-06",
  "semantic_release": "semantic-mvp-2026-04-06",
  "snapshots": {
    "core": {
      "filename": "core_serving.duckdb",
      "tables": ["family_summary", "portfolio_summary", "family_forecast_features_serving"],
      "bytes": 0
    },
    "semantic": {
      "filename": "semantic_serving.duckdb",
      "tables": ["semantic_match_context"],
      "bytes": 0
    },
    "market": {
      "filename": "market_serving.duckdb",
      "tables": ["market_intelligence_overview", "market_intelligence_segments"],
      "bytes": 0
    }
  }
}
```

The backend release manifest should later reference this serving release.

---

## 9. Snapshot Audit Contract

The packaging stage should emit a separate audit file.

Suggested file:

1. `serving_snapshot_audit.json`

Audit should include:

1. per-snapshot file size
2. per-table row counts
3. per-table column counts
4. null checks for key ids
5. duplicate checks where relevant
6. source release ids
7. serving snapshot build duration
8. warnings for missing optional tables

Recommended key checks:

### Core

1. `family_summary.docdb_family_id` null count = `0`
2. `portfolio_summary.owner_id` null count = `0`
3. `family_forecast_features_serving.docdb_family_id` duplicate count = `0`

### Semantic

1. `semantic_match_context.docdb_family_id` null count = `0`
2. duplicate family rows follow the intended semantic context contract

### Market

1. market overview exists
2. market segments exist
3. timeseries row counts are non-zero when expected

The stage manifest should also include:

1. file sizes
2. warnings
3. release lineage

---

## 10. Backend Consumption Contract

The backend should expect the serving snapshots as opaque released artifacts.

That means:

1. backend does not inspect ETL source parquet layouts,
2. backend only needs:
   - serving manifest
   - `.duckdb` files
   - release ids
3. backend repositories query stable serving table names only.

Local runtime:

1. backend reads the local serving manifest
2. backend opens local `.duckdb` files

Prod runtime:

1. backend resolves the active release manifest
2. backend downloads required `.duckdb` files from Azure Blob to local ephemeral storage
3. backend opens those local files

This is the exact same repository/query path in both environments.

---

## 11. Performance Contract

The serving snapshot stage should optimize for:

1. bounded startup download size
2. low cold-start penalty
3. strong local DuckDB query speed
4. minimal unnecessary duplication across snapshots

The key performance policy is:

1. prefer split snapshots over one monolithic all-domain DB
2. prefer materialized serving tables over runtime source parquet reads
3. keep vectors and ANN artifacts out of the serving DBs
4. keep raw historical ledgers out unless they are truly needed as serving tables

Planning ranges:

1. `core_serving.duckdb`: roughly `2GB` to `4GB`
2. `semantic_serving.duckdb`: roughly `<1GB` to `1.5GB`
3. `market_serving.duckdb`: roughly `<1GB` to `2GB`

These are targets, not hard limits.

---

## 12. TDD Implementation Plan

This stage should be implemented test-first.

Recommended test files:

1. `etl/tests/test_serving_snapshots_stage.py`
2. `etl/tests/test_serving_snapshot_manifest.py`
3. `etl/tests/test_serving_snapshot_audit.py`

Recommended first tests:

1. stage writes all three `.duckdb` files
2. manifest is emitted with expected keys
3. audit is emitted with expected per-snapshot metrics
4. `core_serving.duckdb` contains required serving tables
5. `semantic_serving.duckdb` does not contain embedding payload tables
6. `market_serving.duckdb` contains expected market tables
7. row counts and null checks pass on a bounded local fixture set

Implementation rule:

1. agree on table list and manifest contract in tests first
2. then fill in build logic

---

## 13. Stage Wiring Plan

Recommended ETL wiring steps:

1. add new package:
   - `etl/src/patentiq_etl/serving/__init__.py`
   - `etl/src/patentiq_etl/serving/run.py`
2. add a stage function:
   - `run_serving_snapshots`
3. register it in [etl/scripts/run_stage.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/scripts/run_stage.py)
4. stage should emit:
   - stage manifest
   - stage stats
   - artifact paths
5. stage should be publishable through the existing release flow

Recommended stage summary text:

`Materialized backend-ready split DuckDB serving snapshots for core, semantic, and market V2 serving contracts.`

---

## 14. Publish Contract

After successful packaging, the publish/release flow should upload:

1. `core_serving.duckdb`
2. `semantic_serving.duckdb`
3. `market_serving.duckdb`
4. `serving_snapshot_manifest.json`
5. `serving_snapshot_audit.json`

The release manifest should then point to:

1. the serving release id
2. the active snapshot filenames or blob keys

Suggested release-manifest addition:

```json
{
  "serving_release": "2026-04-06-serving",
  "serving_snapshots": {
    "core": "serving/2026-04-06-serving/core_serving.duckdb",
    "semantic": "serving/2026-04-06-serving/semantic_serving.duckdb",
    "market": "serving/2026-04-06-serving/market_serving.duckdb"
  }
}
```

---

## 15. What Not To Do

Avoid:

1. building serving DBs inside backend startup
2. querying Azure Blob parquet directly on hot paths
3. storing ANN binary payloads inside DuckDB
4. copying the entire Silver layer into serving DBs
5. treating the serving snapshot stage as a one-off manual export with no manifest or audit
6. creating too many tiny serving DBs that make repository orchestration messy

---

## 16. Final Recommendation

PatentIQ V2 should add a dedicated ETL stage named `serving-snapshots` that:

1. builds `core_serving.duckdb`, `semantic_serving.duckdb`, and `market_serving.duckdb`,
2. materializes only serving-stable tables,
3. emits a serving manifest and audit,
4. publishes these artifacts to Azure Blob as part of the release contract,
5. lets the backend load the same released serving artifacts in both local and Azure runtimes.

This is the cleanest path to:

1. fast-enough backend startup,
2. strong local/cloud parity,
3. reproducible serving data,
4. lower runtime complexity than remote parquet serving.

### 2026-04-10 execution note

`backend_v2` now prefers `family_compare_current_serving` inside `core_serving.duckdb` for the family compare hot path.

Current transition policy:

1. if `core_serving.duckdb` and `family_compare_current_serving` are available, backend queries that local serving snapshot in both local and Azure-like cached modes
2. if they are missing, backend temporarily falls back to raw parquet reconstruction
3. once the ETL serving-snapshot stage materializes this table in released artifacts, the fallback should be removed for the family compare route

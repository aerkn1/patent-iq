# Optimum Product Gap Analysis: Extra Requirements & Architecture Changes

## Scope
This analysis combines:
1. Existing feature-definition files under `docs/new-feature-ideas/`.
2. Current backend/frontend implementation.
3. Current `analytics.duckdb` + parquet-backed data coverage.

## Current-State Evidence Snapshot
1. Core data exists for patents/families/citations/portfolio analytics:
   - `patent_core`: 1,079,510 rows
   - `portfolio_master`: 205,904 owners
   - `family_members_metrics`: 1,009,490 families
2. Coverage gaps:
   - `portfolio_citation_metrics`: 94,931 / 205,904 owners (**46.1%** coverage)
   - `portfolio_citation_timeseries`: 95,051 / 205,904 owners (**46.16%** coverage)
   - `is_actively_maintained` in `patent_core`: **7.78%** non-null
   - citation events with both sides family-mapped: **39.69%**
3. Missing key fields for planned features:
   - no `priority_date`
   - no `inpadoc_family_id`
   - no jurisdiction-level legal status timeline (`active/lapsed/expired`)
   - no `expiration_date`
   - no inventor entities/links
   - no claim/description text corpus table (only abstract/title in `patent_core`)
4. API/frontend baseline:
   - portfolio tabs still include `Licensing`
   - API surface is mostly overview/analytics/patents/citation/forecast/discovery
   - no workspace, semantic search, comparison workspace, or family-first mode APIs
   - frontend API base is hardcoded to Ngrok fallback logic

## Extra Requirements Needed (Beyond Existing Markdown Definitions)

### XR-01: Canonical Family-Time Model
Define canonical time keys per family:
1. `earliest_priority_date` (mandatory for trend logic)
2. `first_publication_date`
3. `earliest_grant_date`
4. `estimated_expiration_date` (+ term adjustments where data permits)

### XR-02: Family Model Governance
Add dual family model support (`DOCDB_SIMPLE`, `INPADOC_EXTENDED`) with strict metric labeling and no silent mixing.

### XR-03: Legal Status Event Mart
Create jurisdiction-level legal-event history at family level:
`active`, `pending`, `granted`, `lapsed`, `expired`, `opposed`, `revoked`, plus event dates.

### XR-04: Assignee Identity Graph
Add corporate-tree resolution:
subsidiary -> ultimate parent mapping with confidence score and effective date ranges.

### XR-05: Citation Clean-Room Metrics
Provide both raw and adjusted metrics:
1. raw forward/backward
2. self-citation scrubbed
3. intra-family scrubbed
4. self+intra-family scrubbed

### XR-06: Search Corpus Expansion
Ingest full searchable fields:
title, abstract, claims, description, multilingual text normalization, IPC/CPC harmonization.

### XR-07: Data Completeness & Confidence Contracts
Every endpoint returns:
`data_snapshot`, `coverage_pct`, `completeness_flags`, `family_model`, `method_version`.

### XR-08: Feature Computation Layer
Precompute heavy family/portfolio marts (materialized tables) instead of per-request expensive joins/scans.

### XR-09: Explainability Contract
Recommendations/rankings must expose feature contributions and source evidence links.

### XR-10: Workspace/Collaboration Domain
Persistent user workspaces, watchlists, saved queries, snapshots, annotations, and sharing permissions.

### XR-11: OECD Quality Benchmark Integration
Ingest OECD-style indicator sets (EPO/USPTO) as an optional benchmark layer with:
1. office-aware metric availability matrix,
2. cohort normalization support (`filing_year`, `tech_field`),
3. composite-score explainability (`quality_index_4/6` components).

## Architecture Changes Needed

## A) Data Platform Architecture
1. Introduce a medallion-style pipeline:
   - `bronze`: raw ingestion (PATSTAT/INPADOC/legal/SEP/litigation/standards)
   - `silver`: normalized entity tables (family, assignee, legal events, citation graph)
   - `gold`: product marts (family trends, ranking, compare, search facets, OECD quality marts)
2. Add data-quality gates and schema contracts (null checks, key uniqueness, date sanity).
3. Version all marts and keep reproducible snapshots.

## B) Backend Service Architecture
1. Split API by domains:
   - `search-service` (semantic/hybrid/NL query agent),
   - `family-analytics-service`,
   - `comparison-service`,
   - `workspace-service`,
   - `intelligence-service` (SEP/litigation/standards).
2. Add async job orchestration for heavy recomputations (trend rebuilds, embeddings, graph indexing).
3. Add cache/materialization layer for hot portfolio/family dashboards.
4. Introduce feature flags and API versioning (`/v2`) to deprecate licensing-tab behavior safely.

## C) Search/ML Architecture
1. Hybrid retrieval stack:
   - boolean + field filters,
   - vector retrieval,
   - optional graph-based retrieval.
2. Query planner for multilingual NL input to explicit query DSL.
3. Re-ranking with family-level and legal/renewal signals.
4. Explainability module for ranking rationale and evidence traceability.

## D) Frontend Architecture
1. Replace monolithic portfolio page with modular domain views:
   - Family Analytics
   - Trends
   - Compare
   - Search Workspace
2. Add global `family vs publication` mode switch and synchronized filters.
3. Remove licensing tab from nav and align copy/metrics accordingly.
4. Add workspace UX primitives:
   - save set,
   - annotate,
   - snapshot,
   - share.
5. Replace hardcoded API base with environment-configured runtime endpoints.

## Recommended Implementation Order
1. **Phase 1 (Foundation)**: XR-01, XR-02, XR-03, XR-05, XR-07, XR-08
2. **Phase 2 (Search/Intelligence)**: XR-04, XR-06, search-service, hybrid retrieval, explainability
3. **Phase 3 (Product UX)**: XR-10, comparison workspace, prosecution timeline, market/tech trends
4. **Phase 4 (Advanced Mapping)**: SEP/litigation/standards integrations and risk intelligence

## Immediate High-Impact Corrections
1. Family-first trend logic requires priority-date ingestion (currently absent).
2. Application-vs-granted analytics are not reliable with current status derivation; redesign status model from legal events.
3. Citation analytics should expose adjusted metrics; current APIs mainly surface raw/application-level totals.
4. Licensing tab deprecation should start in frontend and API contracts now to reduce migration complexity.
5. OECD-derived scores/indicators need explicit cohort-normalization metadata before being used in cross-portfolio ranking.

## Linked Methodology Addendum
1. `patstat-methodology-compliance-requirements.md`

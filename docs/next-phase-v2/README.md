# Next Phase V2

This folder contains the execution plan for turning PatentIQ into a contest-ready end-to-end patent intelligence platform in a 5-week delivery window.

## File Map

1. [00-program-charter.md](./00-program-charter.md)
   - Program objective, delivery window, non-negotiable principles, and release strategy.
2. [01-scope-and-release-definitions.md](./01-scope-and-release-definitions.md)
   - Contest release scope, deferred items, and feature definitions grouped by product area.
3. [02-five-week-roadmap.md](./02-five-week-roadmap.md)
   - Week-by-week milestones, outputs, and decision gates.
4. [03-data-and-platform-workstreams.md](./03-data-and-platform-workstreams.md)
   - Data model rebuild, backend contract changes, infrastructure, and technical task clusters.
5. [04-product-and-ui-workstreams.md](./04-product-and-ui-workstreams.md)
   - Frontend/product workstreams, UX consolidation, reporting, and compare workflows.
6. [05-ai-agents-operating-model.md](./05-ai-agents-operating-model.md)
   - AI agent lanes, responsibilities, handoff rules, and guardrails.
7. [06-skills-specification.md](./06-skills-specification.md)
   - Internal skill definitions for reusable execution workflows during delivery.
8. [07-quality-gates-and-demo-readiness.md](./07-quality-gates-and-demo-readiness.md)
   - Reliability standards, testing gates, release criteria, and demo readiness checklist.
9. [08-citation-forecast-model-v2-retraining-report.md](./08-citation-forecast-model-v2-retraining-report.md)
   - Current-model weaknesses, V2 retraining scope, feature-table redesign, and ML quality gates.
10. [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](./09-forecast-v2-mvp-use-cases-and-feature-semantics.md)
   - Detailed patent/family and portfolio forecast flows, feature semantics, filing-rate context rules, and serving behavior.
11. [10-patentiq-v2-bronze-silver-gold-knowledge-tree.md](./10-patentiq-v2-bronze-silver-gold-knowledge-tree.md)
   - Concrete Bronze/Silver/Gold table tree tied to PATSTAT sources, current DuckDB views, and V2 target marts.
12. [11-patentiq-v2-metric-lineage-catalog.md](./11-patentiq-v2-metric-lineage-catalog.md)
   - Canonical metric names, formulas, dependencies, and layer-by-layer lineage from Bronze to Gold.
13. [12-patentiq-v2-database-structure-and-metric-maps.md](./12-patentiq-v2-database-structure-and-metric-maps.md)
   - Mermaid diagrams for the full PatentIQ V2 database structure and cross-layer metric relation map.
14. [13-patentiq-v2-cross-layer-dbdiagram.dbml](./13-patentiq-v2-cross-layer-dbdiagram.dbml)
   - dbdiagram.io-compatible DBML file showing Bronze, Silver, Gold, vector, and ML tables with PK/FK-style logical relations.
15. [14-patentiq-v2-metrics-generation-flow-and-guardrails.md](./14-patentiq-v2-metrics-generation-flow-and-guardrails.md)
   - Step-by-step run order for metric generation, including per-step formulas, sanity checks, stop conditions, and downstream failure impact.
16. [15-patentiq-v2-prediction-training-flow-and-guardrails.md](./15-patentiq-v2-prediction-training-flow-and-guardrails.md)
   - End-to-end model-training runbook covering feature tables, model families, calibration, reliability gates, MVP-safe conditions, and downstream blast radius for every prediction scope.
17. [16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md](./16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md)
   - End-to-end semantic-search and vector-comparison runbook covering USPTO/EPAB/PATSTAT representative text hierarchy, separate claim and abstract vector spaces, indexing, retrieval, comparison rollups, safety gates, and downstream blast radius.
18. [17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md](./17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md)
   - Explicit clarification that MVP families and portfolios are bounded to the 10-field mega-cluster, with ghost-node handling for out-of-bounds citation relationships.
19. [18-patentiq-v2-patstat-register-legal-power-up.md](./18-patentiq-v2-patstat-register-legal-power-up.md)
   - EP-only PATSTAT Register integration plan defining Bronze ingestion, Silver overlay tables, Level 2 and Level 3 UI usage, EP-special grant-model features, and asymmetry guardrails.
20. [19-patentiq-v2-storage-sizing-estimate.md](./19-patentiq-v2-storage-sizing-estimate.md)
   - Storage planning note with low/base/high GB estimates for the 10-field mega-cluster across Bronze, Silver, Gold, vectors, ML artifacts, and raw full-text retention variants.
21. [20-patentiq-v2-data-room-architecture-and-contract.md](./20-patentiq-v2-data-room-architecture-and-contract.md)
   - In-app Data Room contract covering the read-only evidence room, wiki-style methodology pages, dataset catalog, manifests, backend endpoints, and approved download surfaces.
22. [21-patentiq-v2-azure-runtime-and-storage-architecture.md](./21-patentiq-v2-azure-runtime-and-storage-architecture.md)
   - Final Azure MVP architecture covering local one-time ETL, Blob-backed artifact storage, DuckDB in the backend, in-process semantic ANN runtime, and temporary in-memory app state.
23. [22-patentiq-v2-backend-frontend-application-architecture.md](./22-patentiq-v2-backend-frontend-application-architecture.md)
   - Modular-monolith application architecture covering deployable service count, backend module boundaries, publication-level evidence support, frontend workspace hierarchy, and Data Room placement.
24. [23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md](./23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md)
   - Comprehensive UX and backend page-contract baseline covering page questions, layout settlement, component groups, Market Intelligence workspace, endpoint wiring, and V1-to-V2 migration guidance.
25. [24-patentiq-v2-local-etl-and-artifact-build-runbook.md](./24-patentiq-v2-local-etl-and-artifact-build-runbook.md)
   - Dedicated local ETL runbook covering source certification, bounded-scope seeding, Bronze/Silver/Gold build order, pre-check tests, model/vector artifact generation, release certification, and Azure artifact publishing.
26. [ETL_IMPLEMENTATION_LOG.md](../../etl/ETL_IMPLEMENTATION_LOG.md)
   - Running implementation log for the ETL workspace covering created scripts, inputs used, methods, calculations, warnings, and future stage execution records.
27. [26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md](./26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md)
   - Raw extraction playbook defining how the bounded mega-cluster universe should be obtained from PATSTAT, Register, USPTO, EPAB, and reference inputs before Bronze parquet landing.
28. [27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md](./27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md)
   - Stage-level audit contract defining the JSON stats snapshots, count proofs, coverage metrics, and failure-localization signals the ETL must emit during execution.
29. [28-patentiq-v2-tip-chunked-full-scope-execution-plan.md](./28-patentiq-v2-tip-chunked-full-scope-execution-plan.md)
   - TIP-specific full-scope execution plan covering chunk keys, Blob-first offload, worker limits for 4 CPU / 32 GB RAM / 30 GB disk, manifest rules, and phased extraction order.
30. [29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md](./29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md)
   - Scope policy defining the main `2007-2026` operating window, the separate mega-cluster heritage backfill horizon, and the clean data-model split between current-state and historical analytics.

## Primary Source Inputs

This planning package is derived primarily from:

- `docs/new-feature-ideas/patent-expert-findings-revised-definitions.md`
- `docs/new-feature-ideas/data-analytics-powerups-and-nuances-requirements.md`
- `docs/new-feature-ideas/patstat-methodology-compliance-requirements.md`
- `docs/new-feature-ideas/patent-landscape-analysis-requirements.md`
- `docs/new-feature-ideas/market-analysis-additional-features-nonoverlap.md`
- `docs/oecd-patent-quality/oecd-patent-quality-definitions-and-feature-mapping.md`

## Program Intent

The goal is not to implement every idea at full depth. The goal is to ship a coherent, reliable, explainable product that demonstrates:

1. Family-first patent intelligence,
2. Trustworthy trend and quality analytics,
3. Competitive and market comparison workflows,
4. Contest-grade polish, performance, and demo resilience.

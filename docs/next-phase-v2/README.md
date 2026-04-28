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
   - End-to-end semantic-search and vector-comparison runbook covering the current EPAB-first / PATSTAT-fallback representative text hierarchy, separate claim and abstract vector spaces, indexing, retrieval, comparison rollups, safety gates, and downstream blast radius.
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
   - Dedicated local ETL runbook covering source certification, TIP raw extraction, Blob-to-local consolidation before Bronze, bounded-scope seeding, Bronze/Silver/Gold build order, pre-check tests, model/vector artifact generation, release certification, and Azure artifact publishing.
26. [25-patentiq-v2-semantic-scope-without-uspto-policy.md](./25-patentiq-v2-semantic-scope-without-uspto-policy.md)
   - Operating policy note defining the maximum viable semantic MVP when USPTO full text is unavailable, keeping EPAB claim enrichment plus PATSTAT abstract fallback and narrowing claim-heavy workflows accordingly.
27. [ETL_IMPLEMENTATION_LOG.md](../../etl/ETL_IMPLEMENTATION_LOG.md)
   - Running implementation log for the ETL workspace covering created scripts, inputs used, methods, calculations, warnings, and future stage execution records.
28. [26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md](./26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md)
   - Raw extraction playbook defining how the bounded mega-cluster universe should be obtained from PATSTAT, Register, USPTO, EPAB, and reference inputs before Bronze parquet landing.
29. [27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md](./27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md)
   - Stage-level audit contract defining the JSON stats snapshots, count proofs, coverage metrics, and failure-localization signals the ETL must emit during execution.
30. [28-patentiq-v2-tip-chunked-full-scope-execution-plan.md](./28-patentiq-v2-tip-chunked-full-scope-execution-plan.md)
   - TIP-specific full-scope execution plan covering chunk keys, Blob-first offload, worker limits for 4 CPU / 32 GB RAM / 30 GB disk, manifest rules, and phased extraction order.
31. [29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md](./29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md)
   - Scope policy defining the main `2007-2026` operating window, the separate mega-cluster heritage backfill horizon, and the clean data-model split between current-state and historical analytics.
32. [36-patentiq-v2-azure-deployment-and-release-blueprint.md](./36-patentiq-v2-azure-deployment-and-release-blueprint.md)
   - Azure-first deployment, release, DNS, CI/CD, and artifact-promotion blueprint for the remotely deployed PatentIQ product.
33. [37-patentiq-v2-client-input-overlays-applicability-and-ui-contract.md](./37-patentiq-v2-client-input-overlays-applicability-and-ui-contract.md)
   - Client-enriched overlay applicability matrix covering required inputs, flows, outputs, and UI/backend implications.
34. [38-patentiq-v2-report-generation-use-cases-and-contract.md](./38-patentiq-v2-report-generation-use-cases-and-contract.md)
   - Report-generation contract covering family, portfolio, compare, and client-enriched report flows.
35. [39-patentiq-v2-azure-openai-gpt-4o-mini-llm-augmentation-contract.md](./39-patentiq-v2-azure-openai-gpt-4o-mini-llm-augmentation-contract.md)
   - Grounded LLM augmentation contract using Azure OpenAI `gpt-4o-mini` for summaries, comparisons, and reports.
36. [40-patentiq-v2-backend-serving-runtime-config-and-cloud-local-parity.md](./40-patentiq-v2-backend-serving-runtime-config-and-cloud-local-parity.md)
   - Backend V2 serving-runtime contract for local/prod parity, artifact resolution, and split DuckDB serving snapshots.
37. [41-patentiq-v2-etl-serving-snapshots-packaging-contract.md](./41-patentiq-v2-etl-serving-snapshots-packaging-contract.md)
   - ETL-side packaging contract for `core`, `semantic`, and `market` serving DuckDB snapshots.
38. [42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md](./42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md)
   - Detailed Phase 03 execution plan, current implementation status, and promotion gates for the family future-citation forecast.
39. [43-patentiq-v2-point-in-time-feature-layer-plan.md](./43-patentiq-v2-point-in-time-feature-layer-plan.md)
   - Point-in-time feature-layer plan covering the implemented family PIT core and the remaining product-serving PIT backlog.
40. [44-patentiq-v2-phase-03-seal-decision-and-accepted-caveats.md](./44-patentiq-v2-phase-03-seal-decision-and-accepted-caveats.md)
   - Explicit acceptance note sealing the current Phase 03 artifacts as an MVP candidate release with caveats.
41. [45-patentiq-v2-phase-04-family-jurisdiction-lapse-risk-execution-plan.md](./45-patentiq-v2-phase-04-family-jurisdiction-lapse-risk-execution-plan.md)
   - Execution plan for Phase 04 family x jurisdiction lapse-risk modeling, outputs, and evaluation gates.
42. [46-patentiq-v2-phase-04-seal-decision-and-serving-contract.md](./46-patentiq-v2-phase-04-seal-decision-and-serving-contract.md)
   - Explicit acceptance note sealing the current Phase 04 artifacts as an MVP candidate release and defining backend/UI serving rules.
43. [47-patentiq-v2-phase-05-family-friction-risk-execution-plan.md](./47-patentiq-v2-phase-05-family-friction-risk-execution-plan.md)
   - Phase 05 execution note defining the current label-chronology blocker, the MVP friction-proxy fallback, and the conditions required for an honest supervised friction-risk model.
44. [48-patentiq-v2-post-phase-04-prioritization-and-next-execution-path.md](./48-patentiq-v2-post-phase-04-prioritization-and-next-execution-path.md)
   - Reprioritization note explaining why Phase 06 becomes the next real model after sealing Phases 03 and 04, with Phase 05 shifted to proxy-first and EP-chronology preparation.
45. [49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md](./49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md)
   - Detailed execution plan for Phase 06 jurisdiction-field trend forecasting, including labels, features, split policy, baseline model, outputs, and quality gates.
46. [50-patentiq-v2-phase-06-direction-first-audit-and-reframe.md](./50-patentiq-v2-phase-06-direction-first-audit-and-reframe.md)
   - Audit note comparing raw-count, naive, growth-first, and direction-first strategies and documenting the recommended direction/band-first Phase 06 product pivot.
47. [51-patentiq-v2-phase-06-seal-decision-and-serving-contract.md](./51-patentiq-v2-phase-06-seal-decision-and-serving-contract.md)
   - Explicit acceptance note sealing the current Phase 06 artifacts as an MVP candidate release under a direction-band-first serving contract.
48. [52-patentiq-v2-portfolio-model-applicability-audit-and-coverage-contract.md](./52-patentiq-v2-portfolio-model-applicability-audit-and-coverage-contract.md)
   - Audit note proving current portfolio applicability of sealed lower-level models and defining mandatory coverage fields for portfolio-derived prediction outputs.
49. [53-patentiq-v2-portfolio-derived-prediction-layer-implementation-and-serving-contract.md](./53-patentiq-v2-portfolio-derived-prediction-layer-implementation-and-serving-contract.md)
   - Implementation and serving contract for the first real portfolio-derived prediction layer built from sealed Phases 03, 04, and 06, including live artifact paths, coverage policy, and backend/UI usage rules.
50. [54-patentiq-v2-phase-08-portfolio-derived-prediction-layer-execution-plan.md](./54-patentiq-v2-phase-08-portfolio-derived-prediction-layer-execution-plan.md)
   - Full standalone Phase 08 execution plan clarifying which portfolio-derived prediction branches are already executable from current inputs and which remain blocked by missing grant-pipeline or friction artifacts.
51. [55-patentiq-v2-pending-grant-pipeline-execution-plan.md](./55-patentiq-v2-pending-grant-pipeline-execution-plan.md)
   - Standalone execution plan and current baseline-candidate status note for the pending-grant pipeline model, including the current product-safe serving recommendation of rank/percentile-first rather than raw-probability-first.
52. [56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md](./56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md)
   - Dedicated execution plan and implementation note for chronological CPC/WIPO classification PIT layers across family, portfolio, and market-intelligence product behavior.
53. [57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md](./57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md)
   - Audit note proving the raw CPC/IPC plus member-publication chronology is strong enough for a first-seen classification visibility model and defining the upgrade path from stable replay to visibility-timed classification PIT.
54. [58-patentiq-v2-backend-ui-wiring-tdd-execution-plan.md](./58-patentiq-v2-backend-ui-wiring-tdd-execution-plan.md)
   - Repo-specific backend/frontend execution plan defining the KISS/TDD wiring order, shared config and client patterns, and the page-by-page rollout sequence for Portfolio, Family, Market Intelligence, Publication, Compare, and Data Room.
55. [59-patentiq-v2-backend-v2-split-decision-and-clean-architecture.md](./59-patentiq-v2-backend-v2-split-decision-and-clean-architecture.md)
   - Decision note preserving the current backend as legacy/reference and defining `backend_v2` as the clean V2 backend target with page-shaped route groups and V2-only schemas.
56. [60-patentiq-v2-portfolio-page-ui-design-spec.md](./60-patentiq-v2-portfolio-page-ui-design-spec.md)
   - Portfolio-page visual and interaction spec covering layout, components, motion, typography, color system, and page-level data framing for the V2 UI.
57. [61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md](./61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md)
   - Audit and remediation plan for the initial portfolio V2 implementation, including endpoint gaps, contract mismatches, and staged repair work.
58. [62-patentiq-v2-portfolio-executive-metric-sensibility-audit.md](./62-patentiq-v2-portfolio-executive-metric-sensibility-audit.md)
   - Sensibility audit for portfolio executive metrics, including normalization, labeling, and product-safe presentation rules.
59. [63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md](./63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md)
   - Serving-boundary audit separating raw Silver analytics from Gold presentation marts and defining what must be normalized before UI exposure.
60. [64-patentiq-v2-citation-serving-refactor-execution-plan.md](./64-patentiq-v2-citation-serving-refactor-execution-plan.md)
   - Execution plan for refactoring citation-derived UI marts across family, portfolio, publication, and market layers.
61. [65-patentiq-v2-blocking-power-rebuild-impact-matrix.md](./65-patentiq-v2-blocking-power-rebuild-impact-matrix.md)
   - Rebuild dependency matrix for the blocking-power correction, including downstream mart impact and required rerun order.
62. [66-patentiq-v2-blocking-power-current-state-audit.md](./66-patentiq-v2-blocking-power-current-state-audit.md)
   - Pre-rebuild audit of the active blocking-power marts, highlighting pending-family distortion and normalization issues.
63. [67-patentiq-v2-derived-metric-formula-alignment-audit.md](./67-patentiq-v2-derived-metric-formula-alignment-audit.md)
   - Formula-alignment audit classifying major derived metrics as aligned, acceptable proxy, needs rebuild, or labeling-only issue.
64. [68-patentiq-v2-family-blocking-power-rebuild-audit.md](./68-patentiq-v2-family-blocking-power-rebuild-audit.md)
   - First real rebuild audit after the family blocking-power correction, limited to family-layer marts and history tables.
65. [69-patentiq-v2-blocking-power-downstream-pit-rebuild-audit.md](./69-patentiq-v2-blocking-power-downstream-pit-rebuild-audit.md)
   - Downstream rebuild audit covering PIT and ranking marts refreshed from the corrected blocking base, plus the remaining current-serving mart gap.
66. [70-patentiq-v2-current-serving-rebuild-audit.md](./70-patentiq-v2-current-serving-rebuild-audit.md)
   - Current-serving rebuild audit covering the refreshed family summary, portfolio marts, market summary PIT, and the remaining portfolio/market presentation risks.
67. [71-patentiq-v2-peer-banding-and-compare-ranking-policy.md](./71-patentiq-v2-peer-banding-and-compare-ranking-policy.md)
   - Peer-bucket policy for qualitative bands and cross-scale compare ranking, including the separation between entity peer ranks and CPC/WIPO/jurisdiction market ranks.
68. [72-patentiq-v2-portfolio-ui-ux-audit-and-restructure-spec.md](./72-patentiq-v2-portfolio-ui-ux-audit-and-restructure-spec.md)
   - Portfolio UX audit and first restructure spec covering duplicate tab content, visual-system flattening, and the five-story IA reset for the V2 workspace.
69. [73-patentiq-v2-enterprise-frontend-structure-blueprint.md](./73-patentiq-v2-enterprise-frontend-structure-blueprint.md)
   - Enterprise frontend blueprint covering the target app structure, design-system ownership, chart and grid strategy, and phased V2 migration path.
70. [90-patentiq-v2-azure-deployment-prep-starting-point.md](./90-patentiq-v2-azure-deployment-prep-starting-point.md)
   - Starting-point note for Azure deployment preparation, covering the current serving artifact baseline, code-level deployment gaps, and the initial local plus Azure rollout order.
71. [91-patentiq-v2-runtime-bootstrap-contract.md](./91-patentiq-v2-runtime-bootstrap-contract.md)
   - Runtime bootstrap contract for local Docker Compose and Azure Container Apps, covering mounted artifact layout, init logging, and non-overwrite rules.
72. [94-patentiq-v2-azure-deployment-execution-runbook.md](./94-patentiq-v2-azure-deployment-execution-runbook.md)
   - Actual Azure execution runbook covering host Azure CLI bring-up, provider registration, ACA and VM backend phases, Cloudflare-backed public cutover, and post-cutover cleanup.
73. [95-patentiq-v2-backend-vm-deployment-plan.md](./95-patentiq-v2-backend-vm-deployment-plan.md)
   - Backend migration plan from Azure Container Apps to a VM-backed runtime, covering recommended VM and disk sizes, Blob-to-local artifact sync, local DuckDB serving, cutover steps, and expected cost/performance tradeoffs.
74. [96-patentiq-v2-backend-vm-execution-checklist.md](./96-patentiq-v2-backend-vm-execution-checklist.md)
   - Exact execution checklist for the VM-backed backend option, covering Azure resource creation, disk attachment, VM preparation, bootstrap-to-local-disk, backend container startup, validation, reverse proxy, Cloudflare cutover, and the later in-place resize outcome.
75. [97-patentiq-v2-domain-and-cloudflare-cutover-checklist.md](./97-patentiq-v2-domain-and-cloudflare-cutover-checklist.md)
   - Step-by-step domain cutover checklist for `patentiq.app`, covering Name.com nameserver switch, Cloudflare DNS and SSL mode, ACA frontend custom domain, ACA TXT validation, VM backend origin-certificate install, runtime API repointing, and final lock-down.

## Repo Wiring Target

For the V2 application implementation:

1. [frontend_v1](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v1) is the preserved legacy UI reference
2. [frontend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2) is the clean V2 frontend target
3. [backend](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend) is the preserved legacy/reference backend
4. [backend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2) is the clean V2 backend target

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

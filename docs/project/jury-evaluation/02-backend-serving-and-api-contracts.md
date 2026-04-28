# Section 02. Backend Serving Architecture And API Contracts

## Table Of Contents

1. [Purpose Of This Section](#purpose-of-this-section)
2. [What The Backend Actually Does In PatentIQ](#what-the-backend-actually-does-in-patentiq)
3. [Backend V2 Design Intent](#backend-v2-design-intent)
4. [FastAPI Runtime Boundary](#fastapi-runtime-boundary)
5. [Configuration And Runtime Modes](#configuration-and-runtime-modes)
   - [1. Core runtime settings](#1-core-runtime-settings)
   - [2. Artifact modes](#2-artifact-modes)
   - [3. Runtime diagnostics](#3-runtime-diagnostics)
6. [DuckDB Access Pattern](#duckdb-access-pattern)
7. [Repository-Led Data Access And Fallback Strategy](#repository-led-data-access-and-fallback-strategy)
   - [1. Family repository](#1-family-repository)
   - [2. Portfolio repository](#2-portfolio-repository)
   - [3. Publication repository](#3-publication-repository)
   - [4. Semantic repository](#4-semantic-repository)
   - [5. Market intelligence repository](#5-market-intelligence-repository)
   - [6. What This Means Operationally](#6-what-this-means-operationally)
8. [Page-Shaped API Contract Pattern](#page-shaped-api-contract-pattern)
   - [1. Overview endpoints](#1-overview-endpoints)
   - [2. Section endpoints](#2-section-endpoints)
   - [3. Response metadata contract](#3-response-metadata-contract)
9. [Workspace Route Groups And Their Responsibilities](#workspace-route-groups-and-their-responsibilities)
10. [How Services Convert Data Into Page-Shaped Contracts](#how-services-convert-data-into-page-shaped-contracts)
    - [1. Portfolio service](#1-portfolio-service)
    - [2. Family service](#2-family-service)
    - [3. Publication service](#3-publication-service)
    - [4. Compare service](#4-compare-service)
    - [5. Market intelligence service](#5-market-intelligence-service)
    - [6. Semantic service](#6-semantic-service)
11. [Frontend V2 Consumption And Contract Mapping](#frontend-v2-consumption-and-contract-mapping)
    - [1. API base URL and fetch wrapper](#1-api-base-url-and-fetch-wrapper)
    - [2. Typed client adapters](#2-typed-client-adapters)
    - [3. Workspace orchestration in the frontend](#3-workspace-orchestration-in-the-frontend)
    - [4. Route-to-frontend traceability table](#4-route-to-frontend-traceability-table)
12. [Current Architecture Implementation Truths](#current-architecture-implementation-truths)
13. [Testing Evidence For The Contract Layer](#testing-evidence-for-the-contract-layer)
14. [Key Takeaways](#key-takeaways)

## Purpose Of This Section

Section 01 explained how PatentIQ builds trusted analytical artifacts. This section explains the next step: how those artifacts are turned into live application contracts for the product runtime.

The main question answered here is:

How does PatentIQ transform Gold marts, selected Silver marts, vector assets, and serving snapshots into stable frontend-consumable APIs?

The answer is not "the frontend reads the database." The answer is:

1. ETL materializes analytical assets.
2. `backend_v2/` resolves the correct released artifacts for the runtime.
3. repositories encapsulate the storage access pattern,
4. services reshape raw rows into page-shaped contracts,
5. `frontend_v2/` consumes only typed HTTP DTOs and never touches storage directly.

Primary implementation references:

1. `backend_v2/README.md:1-88`
2. `docs/next-phase-v2/59-patentiq-v2-backend-v2-split-decision-and-clean-architecture.md:5-71`
3. `docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md:51-107`
4. `docs/next-phase-v2/41-patentiq-v2-etl-serving-snapshots-packaging-contract.md:22-140`

## What The Backend Actually Does In PatentIQ

The backend is intentionally not a second ETL layer and not a business-logic-free pass-through.

It has four concrete responsibilities:

1. resolve the correct released artifacts for the runtime,
2. query them safely and deterministically,
3. shape data into page-level contracts aligned with UX needs,
4. attach caveats, support levels, coverage metadata, and pagination so the frontend can explain what the UI is showing.

That role is explicitly documented in the V2 architecture notes and is visible in the codebase design.

Implementation references:

1. `backend_v2/README.md:5-21`
2. `docs/next-phase-v2/59-patentiq-v2-backend-v2-split-decision-and-clean-architecture.md:32-62`

## Backend V2 Design Intent

The V2 backend is designed around family-first, page-shaped contracts.

The intended design rules are:

1. page-shaped contracts first,
2. thin FastAPI routers,
3. orchestration in application services,
4. DuckDB and Parquet access behind repositories,
5. explicit support and caveat metadata on strategic responses.

This is not only architectural aspiration. The repo structure and service wiring match those rules directly.

Implementation references:

1. `backend_v2/README.md:5-21`
2. `docs/next-phase-v2/59-patentiq-v2-backend-v2-split-decision-and-clean-architecture.md:34-62`
3. `docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md:51-107`

## FastAPI Runtime Boundary

`backend_v2/main.py` defines a compact FastAPI boundary:

1. app metadata comes from `Settings`,
2. CORS is enabled for local browser and containerized browser access,
3. the V2 API router is mounted under `/api/v1`,
4. a dedicated `/health` endpoint exposes liveness.

The mounted V2 route groups are:

1. `portfolios`
2. `families`
3. `publications`
4. `market_intelligence`
5. `compare`
6. `semantic`
7. `stats`

This shows that the backend is workspace-oriented rather than source-table-oriented.

Implementation references:

1. `backend_v2/main.py:8-34`
2. `backend_v2/api/v1/router.py:1-20`
3. `backend_v2/tests/test_app.py:6-17`

## Configuration And Runtime Modes

### 1. Core runtime settings

`backend_v2/config/settings.py` centralizes runtime configuration with the `PATENTIQ_V2_` environment prefix.

The most important defaults are:

1. `api_prefix="/api/v1"`
2. `etl_data_root=<repo>/etl/data`
3. `artifact_mode="local_fs"`
4. `local_artifact_root=<repo>/etl/data/serving`
5. `serving_manifest_path=<repo>/etl/data/serving/serving_snapshot_manifest.json`
6. `duckdb_threads=2`
7. `duckdb_memory_limit="4GB"`
8. `raw_parquet_fallback_enabled=True`

This is why the backend can run against local ETL artifacts by default without extra storage indirection.

Implementation references:

1. `backend_v2/config/settings.py:17-60`

### 2. Artifact modes

The runtime supports two artifact-resolution modes:

| Mode | Runtime behavior | Why it exists |
| --- | --- | --- |
| `local_fs` | reads the serving manifest from local disk and resolves snapshot files from the serving directory | local development, deterministic offline execution |
| `azure_blob_cached` | reads the manifest from a URL, downloads the referenced snapshots into local cache, then queries the cached file | cloud/runtime parity without querying remote blob parquet directly per request |

`ArtifactLocator` is the key component:

1. it resolves `core_serving.duckdb` and `semantic_serving.duckdb`,
2. it caches the parsed manifest,
3. it materializes remote files into `cache_dir`,
4. it exposes a small runtime-description payload for inspection.

This behavior is aligned with the ETL-side serving contract: ETL builds and releases serving snapshots, while the backend only resolves and consumes them.

Implementation references:

1. `backend_v2/README.md:70-106`
2. `backend_v2/infrastructure/artifacts/locator.py:29-191`
3. `docs/next-phase-v2/41-patentiq-v2-etl-serving-snapshots-packaging-contract.md:22-39`
4. `backend_v2/tests/test_artifact_locator.py:8-109`

### 3. Runtime diagnostics

The backend exposes `/api/v1/stats/runtime`, which reports:

1. app name,
2. API prefix,
3. DuckDB thread and memory settings,
4. runtime profile,
5. artifact mode,
6. resolved `core_serving.duckdb` path if available.

This gives a compact operational checksum of which runtime mode is actually active.

Implementation references:

1. `backend_v2/api/v1/stats.py:9-21`
2. `backend_v2/tests/test_app.py:13-17`

## DuckDB Access Pattern

The backend uses DuckDB in a deliberately constrained way:

1. every repository operation gets an in-memory scratch connection,
2. connection settings apply thread and memory limits from config,
3. read-only serving snapshots are attached when available,
4. raw Parquet is read directly only behind repository methods.

The code comment in `DuckDbProvider` is important. It explains why the runtime does **not** use a shared writable scratch database:

1. repository access is read-mostly,
2. UI traffic can issue many concurrent requests,
3. a file-backed scratch DB would increase lock contention.

This is an important quality signal: runtime reads are intentionally isolated and low-risk.

Implementation references:

1. `backend_v2/infrastructure/duckdb/connection.py:10-27`

## Repository-Led Data Access And Fallback Strategy

The repository layer is the most important implementation seam in `backend_v2`. It hides where data comes from and lets services work in business terms rather than storage terms.

### 1. Family repository

`FamilyRepository` is a hybrid current-state repository.

Its artifact list shows the current runtime reality:

1. if `core_serving.duckdb` exists, it is preferred,
2. but several supporting Gold, Silver, and ML artifacts are still read directly from Parquet,
3. if serving tables are absent and fallback is enabled, raw Parquet queries are used.

For family overview and compare-oriented context, the repository prefers:

1. `core_db.family_summary`
2. `core_db.family_blocking_power`
3. `core_db.family_heritage_summary`
4. `core_db.family_compare_current_serving`

If those are unavailable, it falls back to:

1. `gold_family_summary.parquet`
2. `gold_family_blocking_power.parquet`
3. `gold_family_heritage_summary.parquet`
4. `gold_family_compare_pit.parquet`

This is especially visible in:

1. `get_family_overview_context()`
2. `get_family_compare_contexts()`
3. `get_family_compare_suggestions()`

Implementation references:

1. `backend_v2/infrastructure/repositories/family_repository.py:13-86`
2. `backend_v2/infrastructure/repositories/family_repository.py:238-342`
3. `backend_v2/infrastructure/repositories/family_repository.py:1188-1415`

### 2. Portfolio repository

`PortfolioRepository` follows the same hybrid strategy.

Its artifact list includes:

1. serving snapshot access through `core_serving.duckdb`,
2. Gold marts for portfolios, families, citations, and classifications,
3. Silver marts for owner bridge and enriched citation support,
4. ML artifacts for lapse and pending-grant contracts.

One clear example is `get_owner_families()`, which:

1. first checks whether serving tables such as `family_owner_bridge`, `portfolio_forecast_contributors`, `family_blocking_power`, and `family_summary` are present in `core_db`,
2. serves from those current-serving tables when possible,
3. falls back to raw Parquet when the serving path is incomplete.

This means portfolio pages are already partly serving-backed, but not yet fully detached from raw analytical marts.

Implementation references:

1. `backend_v2/infrastructure/repositories/portfolio_repository.py:17-114`
2. `backend_v2/infrastructure/repositories/portfolio_repository.py:783-896`

### 3. Publication repository

`PublicationRepository` is the clearest example of a strong serving-first drilldown path.

It:

1. checks whether `publication_evidence_serving` exists in `core_serving.duckdb`,
2. uses that serving table for publication member resolution when available,
3. falls back to raw Silver/Bronze inputs otherwise,
4. then supplements that with Bronze/Silver evidence tables such as PATSTAT application/title/abstract, EPAB claims, and EP Register marts.

This is appropriate because publication pages are evidence-first pages rather than synthetic analytical pages.

Implementation references:

1. `backend_v2/infrastructure/repositories/publication_repository.py:14-53`
2. `backend_v2/infrastructure/repositories/publication_repository.py:127-212`

### 4. Semantic repository

`SemanticRepository` is also hybrid, but in a different way.

It does **not** use the semantic serving DB for live search ranking itself. Instead:

1. vector payloads remain in Parquet files,
2. the semantic serving DB is used for `semantic_match_context` coverage reference,
3. exact ranking is computed at runtime with `list_cosine_similarity(embedding, ?)`,
4. claim-space and abstract-space support are checked explicitly per family.

This is why the semantic service can honestly state that ANN artifacts exist in ETL, but the live backend is currently serving exact ranking for determinism.

Implementation references:

1. `backend_v2/infrastructure/repositories/semantic_repository.py:14-28`
2. `backend_v2/infrastructure/repositories/semantic_repository.py:30-68`
3. `backend_v2/infrastructure/repositories/semantic_repository.py:170-234`

### 5. Market intelligence repository

`MarketIntelligenceRepository` currently stays outside the serving-snapshot path.

Its artifact list is pure Gold/Silver:

1. market overview, summary, segments, leaderboard, CPC, citation, and jurisdiction marts,
2. supporting member-publication and UP/legal Silver tables,
3. no `ArtifactLocator`,
4. no attached serving snapshot dependency.

This is an important implementation detail: the market workspace is currently a Gold/Silver parquet runtime, not yet a serving-snapshot runtime.

Implementation references:

1. `backend_v2/infrastructure/repositories/market_intelligence_repository.py:10-67`

### 6. What This Means Operationally

Today’s backend is best described as a **hybrid serving runtime**:

1. core current-family and compare flows increasingly prefer serving snapshots,
2. publication evidence can prefer serving tables,
3. semantic coverage metadata can prefer semantic serving context,
4. market intelligence still reads released Gold/Silver parquet directly,
5. raw-parquet fallback remains intentionally enabled while serving coverage is being expanded route by route.

This is consistent with the backend README and with the ETL serving plan. It is not a contradiction. It is the current rollout state.

Implementation references:

1. `backend_v2/README.md:70-88`
2. `docs/next-phase-v2/41-patentiq-v2-etl-serving-snapshots-packaging-contract.md:22-38`

## Page-Shaped API Contract Pattern

### 1. Overview endpoints

Overview endpoints are designed to bootstrap a page shell:

1. identity,
2. headline cards,
3. first visible context,
4. enough metadata for the UI to render the workspace safely.

Representative overview routes are:

1. `/api/v1/portfolios/{owner_id}/overview`
2. `/api/v1/families/{family_id}/overview`
3. `/api/v1/publications/{publication_id}/overview`
4. `/api/v1/market-intelligence/overview`
5. `/api/v1/market-intelligence/workspace`

Implementation references:

1. `docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md:60-91`
2. `backend_v2/api/v1/portfolios.py:24-26`
3. `backend_v2/api/v1/families.py:10-12`
4. `backend_v2/api/v1/publications.py:10-12`
5. `backend_v2/api/v1/market_intelligence.py:10-21`

### 2. Section endpoints

Section endpoints carry heavier or more specialized page payloads:

1. paginated tables,
2. chronology and timeseries,
3. field or classification detail,
4. legal drilldowns,
5. evidence panels,
6. comparison-specific slices.

This contract style lets the frontend load the page shell quickly and hydrate large panels lazily.

Representative examples visible in code:

1. portfolio citation and filing endpoints,
2. family legal, members, citations, and classification endpoints,
3. publication text and register-evidence endpoints,
4. market segment detail endpoints,
5. compare timeslice and lookup endpoints,
6. semantic family search and compare endpoints.

Implementation references:

1. `backend_v2/api/v1/portfolios.py:29-280`
2. `backend_v2/api/v1/families.py:15-67`
3. `backend_v2/api/v1/publications.py:15-27`
4. `backend_v2/api/v1/market_intelligence.py:24-167`
5. `backend_v2/api/v1/compare.py:15-84`
6. `backend_v2/api/v1/semantic.py:10-46`

### 3. Response metadata contract

Every strategic response uses the common `ResponseMeta` contract, which supports:

1. `page`
2. `artifact_sources`
3. `support_level`
4. `caveats`
5. `coverage`
6. `pagination`

This is one of the most important design decisions in the application. The API returns not only numbers and rows, but also the context needed to interpret those numbers responsibly.

Implementation references:

1. `backend_v2/domain/schemas/common.py:6-47`

## Workspace Route Groups And Their Responsibilities

| Route group | Main job | Character of response |
| --- | --- | --- |
| `portfolios` | owner-level strategic workspace | executive cards, family tables, fields, citations, forecast, pending grants |
| `families` | family-level analytical and legal workspace | overview, legal footprint, field footprint, member set, citations, classification |
| `publications` | document-evidence drilldown | bibliography, text evidence, timeline, EP Register evidence |
| `market-intelligence` | field/segment-wide market surfaces | segment overview, history, jurisdictions, CPC, grant mix, attacker and citation trends |
| `compare` | family-vs-family and portfolio-vs-portfolio lenses | contrast rows, overlap views, timeslice comparisons, lookup helpers |
| `semantic` | family-anchor vector search and pairwise semantic comparison | candidate-only semantic ranking and context |
| `stats` | runtime diagnostics | environment and serving-mode metadata |

Implementation references:

1. `backend_v2/api/v1/router.py:1-20`
2. `backend_v2/api/v1/portfolios.py:15-280`
3. `backend_v2/api/v1/families.py:6-67`
4. `backend_v2/api/v1/publications.py:6-27`
5. `backend_v2/api/v1/market_intelligence.py:6-167`
6. `backend_v2/api/v1/compare.py:11-84`
7. `backend_v2/api/v1/semantic.py:6-46`
7. `backend_v2/api/v1/stats.py:6-21`

## How Services Convert Data Into Page-Shaped Contracts

Services are where storage rows become product contracts. They do not merely pass repository results through unchanged.

### 1. Portfolio service

`PortfolioService.get_overview()` demonstrates the page-shaping role clearly.

It:

1. queries summary, peer context, forecast coverage, owner status counts, and top families,
2. builds status-mix slices,
3. converts raw portfolio metrics into page-ready summary cards,
4. injects peer-relative band language,
5. attaches coverage metadata and caveats,
6. records `artifact_sources` in the response meta.

This is why the portfolio page can explain both raw footprint and confidence context without the frontend re-deriving business logic.

Implementation references:

1. `backend_v2/application/services/portfolios.py:288-550`

### 2. Family service

`FamilyService` shapes the family page in two layers:

1. overview payload for identity, headline cards, and overview metrics,
2. section payloads for fields, legal, timeseries, members, semantic context, forecasts, citations, and classification.

It also explicitly exposes quality-related metrics such as:

1. `quality_index_6`,
2. `oecd_quality_percentile`,
3. `generality`,
4. `originality`,
5. `radicalness`,
6. legal durability and coverage stability context.

This demonstrates that the family page is not a UI-only summary. It is a structured explanation contract over the deeper warehouse.

Implementation references:

1. `backend_v2/application/services/families.py:244-441`
2. `backend_v2/application/services/families.py:443-744`

### 3. Publication service

`PublicationService` is intentionally evidence-first.

Its overview and section payloads emphasize:

1. factual publication identity,
2. stage classification,
3. title and abstract availability,
4. claim availability,
5. EP Register evidence when applicable,
6. explicit caveats that publication pages are not synthetic strength pages.

This is an important design discipline: not every page in PatentIQ is a score page. Publication pages are evidence drilldowns used to support the strategic pages.

Implementation references:

1. `backend_v2/application/services/publications.py:16-187`
2. `backend_v2/application/services/publications.py:189-346`

### 4. Compare service

`CompareService` turns raw compare marts into explainable contrast contracts instead of naive side-by-side dumps.

It:

1. builds family compare around three explicit lenses: blocking posture, legal durability, and citation heritage,
2. builds portfolio compare around mass, elite density, and crown-jewel strength,
3. switches between percentile-first and band-first winner logic depending on whether the entities share the same cohort or peer bucket,
4. exposes compare-safe historical timeslice views for both families and portfolios,
5. attaches lookup and suggestion helpers so the frontend can keep compare scoped to entities that really exist in the current serving surface.

This matters because the compare layer is one of the clearest examples of business logic living in the service layer rather than in React components.

Implementation references:

1. `backend_v2/application/services/compare.py:526-960`
2. `backend_v2/application/services/compare.py:961-1433`
3. `backend_v2/application/services/compare.py:1435-1809`
4. `backend_v2/application/services/compare.py:1810-2246`

### 5. Market intelligence service

`MarketIntelligenceService` composes a broader workspace contract than the other services.

It:

1. reads scope summary and overview summary,
2. assembles segment lists and selected-segment detail,
3. maps owners, families, jurisdictions, CPC, and citation trend slices,
4. exposes methodology notes and caveats together with the data.

This service makes the market workspace page-shaped even though it is backed by multiple Gold marts rather than a single source table.

Implementation references:

1. `backend_v2/application/services/market_intelligence.py:16-129`
2. `backend_v2/application/services/market_intelligence.py:131-340`

### 6. Semantic service

`SemanticService` is unusually explicit about what the semantic layer can and cannot claim.

It:

1. validates whether the requested family exists in the requested vector space,
2. exposes coverage of the current semantic payload,
3. labels the runtime as exact vector ranking,
4. marks the entire surface as `candidate_only`,
5. carries strong caveats about abstract fallback and non-legal interpretation.

This is the right posture for review: the system explains semantic power without overstating legal certainty.

Implementation references:

1. `backend_v2/application/services/semantic.py:14-197`
2. `backend_v2/application/services/semantic.py:225-329`

## Frontend V2 Consumption And Contract Mapping

### 1. API base URL and fetch wrapper

The frontend never hardcodes storage paths. It always goes through the backend base URL.

`frontend_v2/lib/config.ts` resolves the API base URL by:

1. preferring `NEXT_PUBLIC_API_BASE_URL`,
2. defaulting to `http://localhost:8000` in development,
3. rewriting `localhost` to `host.docker.internal` when the browser is running through the container bridge.

`fetchJson()` then:

1. calls the resolved backend URL,
2. forces `cache: "no-store"`,
3. expects JSON,
4. normalizes HTTP error handling.

Implementation references:

1. `frontend_v2/lib/config.ts:1-40`
2. `frontend_v2/lib/api/core.ts:1-40`

### 2. Typed client adapters

The V2 frontend client files are not dumb transport wrappers. They are adapters from backend response shapes into frontend-native typed contracts.

Examples:

1. `portfolio-v2.ts` defines backend payload types, normalizes support/coverage, reshapes pagination, and composes a dashboard payload through multi-endpoint fetches.
2. `family-v2.ts` converts backend snake_case fields into typed family identity, meta, coverage, and section payloads.
3. `publication-v2.ts` maps factual overview and section blocks into publication-specific frontend types.
4. `market-v2.ts` maps the market workspace and section routes into strongly typed market responses rather than letting page components assemble URLs ad hoc.
5. `semantic-v2.ts` and `compare-v2.ts` explicitly preserve `artifactSources` in the mapped frontend meta.

An important nuance:

1. compare and semantic clients preserve `artifactSources`,
2. portfolio, family, and publication clients currently prioritize support, coverage, caveats, and UI-specific shapes and do not expose `artifactSources` in their typed frontend meta.

So provenance is always present on the backend contract, but it is surfaced selectively in the frontend client layer today.

Implementation references:

1. `frontend_v2/lib/api/portfolio-v2.ts:49-107`
2. `frontend_v2/lib/api/portfolio-v2.ts:501-548`
3. `frontend_v2/lib/api/portfolio-v2.ts:866-920`
4. `frontend_v2/lib/api/family-v2.ts:43-49`
5. `frontend_v2/lib/api/family-v2.ts:126-194`
6. `frontend_v2/lib/api/publication-v2.ts:27-31`
7. `frontend_v2/lib/api/publication-v2.ts:95-167`
8. `frontend_v2/lib/api/market-v2.ts:1-223`
9. `frontend_v2/lib/api/semantic-v2.ts:47-54`
10. `frontend_v2/lib/api/semantic-v2.ts:163-174`
11. `frontend_v2/lib/api/compare-v2.ts:33-38`
12. `frontend_v2/lib/api/compare-v2.ts:132-141`

### 3. Workspace orchestration in the frontend

The frontend workspaces actively orchestrate endpoint calls. They are not pre-hydrated static pages.

#### Portfolio workspace

The portfolio workspace:

1. calls `fetchPortfolioDashboard(ownerId)` on load,
2. that dashboard call itself performs a `Promise.allSettled()` across overview, families, fields, forecast, threats, and classification,
3. subsequent tabs trigger additional endpoint calls for citations, families, fields, contributors, and pending grants.

Implementation references:

1. `frontend_v2/components/portfolio/portfolio-workspace.tsx:202-232`
2. `frontend_v2/components/portfolio/portfolio-workspace.tsx:301-827`
3. `frontend_v2/lib/api/portfolio-v2.ts:866-920`

#### Family workspace

The family workspace:

1. loads overview first,
2. then lazily hydrates legal, fields, timeseries, classification, and forecast sections,
3. loads members and citations through separate section calls.

Implementation references:

1. `frontend_v2/components/family/family-workspace.tsx:2040-2094`
2. `frontend_v2/components/family/family-workspace.tsx:2096-2155`

#### Publication workspace

The publication workspace:

1. loads the overview first,
2. then loads `text`, `legal-timeline`, and `register-evidence` in parallel with `Promise.allSettled()`.

Implementation references:

1. `frontend_v2/components/publication/publication-workspace.tsx:328-390`

#### Market workspace

The market workspace:

1. loads the workspace shell from `/market-intelligence/workspace`,
2. separately hydrates market history and leading jurisdictions,
3. parallelizes jurisdiction grant detail,
4. parallelizes CPC trend and CPC-jurisdiction detail,
5. separately loads CPC-owner detail.

Implementation references:

1. `frontend_v2/components/market/market-workspace.tsx:620-930`

### 4. Route-to-frontend traceability table

| User-facing page | Frontend entry point | Primary client module | Backend route family | Main backend service | Current storage mode |
| --- | --- | --- | --- | --- | --- |
| Portfolio workspace | `app/(workspace)/portfolio/[ownerId]/page.tsx` -> `PortfolioWorkspace` | `frontend_v2/lib/api/portfolio-v2.ts` | `/api/v1/portfolios/*` | `PortfolioService` | hybrid `core_serving.duckdb` + Gold/Silver/ML parquet |
| Family workspace | `app/(workspace)/family/[familyId]/page.tsx` -> `FamilyWorkspace` | `frontend_v2/lib/api/family-v2.ts` | `/api/v1/families/*` | `FamilyService` | hybrid `core_serving.duckdb` + Gold/Silver/ML parquet |
| Publication workspace | `app/(workspace)/publication/[publicationId]/page.tsx` -> `PublicationWorkspace` | `frontend_v2/lib/api/publication-v2.ts` | `/api/v1/publications/*` | `PublicationService` | `publication_evidence_serving` when present, else Silver/Bronze parquet |
| Market intelligence workspace | `app/(workspace)/market/page.tsx` -> `MarketWorkspace` | `frontend_v2/lib/api/market-v2.ts` | `/api/v1/market-intelligence/*` | `MarketIntelligenceService` | direct Gold/Silver parquet |
| Compare workspaces | `app/(workspace)/compare/families/page.tsx` and `app/(workspace)/compare/portfolios/page.tsx` | `frontend_v2/lib/api/compare-v2.ts` | `/api/v1/compare/*` | `CompareService` | hybrid through family/portfolio repositories |
| Semantic workspace | `app/(workspace)/compare/semantic/page.tsx` | `frontend_v2/lib/api/semantic-v2.ts` | `/api/v1/semantic/*` | `SemanticService` | semantic serving for context counts, raw vector parquet for ranking |

Implementation references:

1. `frontend_v2/components/portfolio/portfolio-workspace.tsx:202-232`
2. `frontend_v2/components/family/family-workspace.tsx:2040-2094`
3. `frontend_v2/components/publication/publication-workspace.tsx:328-390`
4. `frontend_v2/components/market/market-workspace.tsx:620-930`
5. `frontend_v2/lib/api/market-v2.ts:1-223`
6. `frontend_v2/app/(workspace)/compare/families/page.tsx:1-18`
7. `frontend_v2/app/(workspace)/compare/portfolios/page.tsx:1-18`
8. `frontend_v2/app/(workspace)/compare/semantic/page.tsx:1-14`
9. `frontend_v2/lib/api/compare-v2.ts:33-141`
10. `frontend_v2/lib/api/semantic-v2.ts:47-174`

## Current Architecture Implementation Truths

The current implementation has a few important runtime truths:

1. the backend is already page-shaped and service-oriented,
2. the backend is **not** a monolithic serving-only runtime yet,
3. serving snapshots already matter in the core and semantic paths,
4. raw-parquet fallback is still active by design during rollout,
5. the publication page is intentionally evidence-first,
6. the semantic page is intentionally candidate-only and exact-ranking-based,
7. the market workspace is currently a direct Gold/Silver runtime.

These points are not weaknesses when documented honestly. They show architectural discipline and current release truth.

## Testing Evidence For The Contract Layer

Representative backend tests already validate important parts of the serving and contract layer:

1. `test_app.py` verifies the app health endpoint and confirms the `/api/v1` mount.
2. `test_artifact_locator.py` verifies local-manifest and cached-remote resolution for `core_serving.duckdb` and `semantic_serving.duckdb`.
3. `test_portfolio_endpoints.py` verifies portfolio route shapes and query-parameter forwarding behavior against the declared response models.

These tests are not the whole validation story, but they are direct evidence that:

1. runtime resolution logic is exercised,
2. route groups are mounted correctly,
3. page-shaped contract wiring is being tested, not only repository internals.

Implementation references:

1. `backend_v2/tests/test_app.py:6-17`
2. `backend_v2/tests/test_artifact_locator.py:8-109`
3. `backend_v2/tests/test_portfolio_endpoints.py:20-220`

## Key Takeaways

1. `backend_v2` is the contract bridge between the ETL warehouse and the UI, not a second data-processing engine.
2. The backend architecture is intentionally clean: routers delegate, services shape, repositories access storage.
3. PatentIQ already supports released serving artifacts, but the current runtime is still hybrid, with serving-first behavior in some domains and Gold/Silver parquet access in others.
4. The API design is page-shaped and metadata-rich, which is why the frontend can render explainable workspaces instead of raw database views.
5. `frontend_v2` consumes only HTTP DTOs and typed client adapters, preserving separation between UI and storage.
6. The current implementation is candid about support levels, coverage, caveats, and rollout state, which is the right posture for an analytical product.

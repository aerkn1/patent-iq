# PatentIQ V2 UX Page Contracts And Backend Wiring Baseline

## Purpose

Provide the initial comprehensive baseline for:

1. how PatentIQ data should be represented in the UI,
2. how each workspace should be laid out,
3. how backend modules should serve those pages,
4. how the V2 experience should differ from the current V1 frontend/backend shape,
5. how performance and clarity should be preserved through page-shaped contracts.

This document is a baseline intended to evolve during implementation.

## V1 To V2 Transition

### Current V1 tendencies

The current product shape is closer to:

1. patent/application-centric routing,
2. fewer top-level backend route groups,
3. broader service files,
4. dashboard-first rather than workspace-first UX,
5. weaker separation between strategic pages and evidence pages.

### V2 target

The V2 target should be:

1. family-first analytics,
2. publication as evidence drill-down,
3. page-shaped backend contracts,
4. dedicated `Market Intelligence` workspace,
5. dedicated `Data Room` workspace,
6. modular backend services with clear domain boundaries.

## Workspace Map

PatentIQ MVP should expose these workspaces:

1. `Portfolio`
2. `Lookup / Explore`
3. `Compare`
4. `Forecasts`
5. `Market Intelligence`
6. `Data Room`
7. `Family` pages
8. `Publication` pages

## Universal UX Rules

1. every page must answer a primary question,
2. every score must show visible components and caveats,
3. every strategic surface must have an evidence path,
4. overview payloads should render the page shell,
5. heavy sections should hydrate lazily through dedicated endpoints,
6. frontend should consume only backend page contracts, not storage or low-level table APIs.

## Backend Contract Pattern

Use two endpoint classes:

### Overview endpoints

Purpose:
1. page shell,
2. identity block,
3. summary cards,
4. first-tab or first-section content.

Examples:
1. `/api/v1/portfolios/{owner_id}/overview`
2. `/api/v1/families/{family_id}/overview`
3. `/api/v1/publications/{publication_id}/overview`
4. `/api/v1/market-intelligence/overview`

### Section endpoints

Purpose:
1. heavy tab content,
2. large tables,
3. timeseries,
4. long text,
5. second-order analyses.

Examples:
1. `/api/v1/families/{family_id}/fields`
2. `/api/v1/families/{family_id}/timeseries`
3. `/api/v1/publications/{publication_id}/text`
4. `/api/v1/market-intelligence/segments/{segment_id}/timeseries`

## Backend Service Wiring

Recommended internal backend services:

1. `family_service`
2. `publication_service`
3. `portfolio_service`
4. `market_intelligence_service`
5. `comparison_service`
6. `forecast_service`
7. `semantic_service`
8. `data_room_service`
9. `manifest_service`
10. `session_state_service`

## Page Contracts

## 1. Portfolio Workspace

### Primary question

`What does this owner's in-scope mega-cluster portfolio look like right now, and how is it positioned against market conditions?`

### Layout

1. header with owner identity and scope badges
2. summary cards
3. top families strip/table
4. field exposure and concentration section
5. market-context section
6. forecast section
7. threat / compare links

### Core components

1. `PortfolioHeader`
2. `PortfolioSummaryCards`
3. `TopFamiliesTable`
4. `PortfolioFieldDistribution`
5. `PortfolioMarketContextPanel`
6. `PortfolioForecastPanel`
7. `PortfolioThreatPanel`

### Backend endpoints

1. `GET /api/v1/portfolios/{owner_id}/overview`
2. `GET /api/v1/portfolios/{owner_id}/families`
3. `GET /api/v1/portfolios/{owner_id}/fields`
4. `GET /api/v1/portfolios/{owner_id}/market-context`
5. `GET /api/v1/portfolios/{owner_id}/forecasts`
6. `GET /api/v1/portfolios/{owner_id}/threats`

### Backend services involved

1. `portfolio_service`
2. `forecast_service`
3. `comparison_service`
4. `market_intelligence_service`

### Performance plan

1. overview endpoint returns first 10 families and top summary cards,
2. fields, market context, forecasts, and threats hydrate separately,
3. large family tables paginate server-side.

## 2. Family Workspace

### Primary question

`How strong, broad, exposed, and explainable is this family right now?`

### Layout

1. identity header
2. overview tab
3. blocking power tab
4. legal / coverage tab
5. citation analytics tab
6. documents & prosecution tab
7. forecast and semantic links

### Core components

1. `FamilyIdentityHeader`
2. `FamilyOverviewGrid`
3. `BlockingPowerSummaryCard`
4. `BlockingPowerByJurisdiction`
5. `BlockingPowerByField`
6. `BlockingPowerTimeseries`
7. `SupportingDiagnosticsPanel`
8. `FamilyMembersTable`
9. `ProsecutionEvidencePanel`

### Backend endpoints

1. `GET /api/v1/families/{family_id}/overview`
2. `GET /api/v1/families/{family_id}/blocking-power`
3. `GET /api/v1/families/{family_id}/jurisdictions`
4. `GET /api/v1/families/{family_id}/fields`
5. `GET /api/v1/families/{family_id}/timeseries`
6. `GET /api/v1/families/{family_id}/members`
7. `GET /api/v1/families/{family_id}/citations`
8. `GET /api/v1/families/{family_id}/forecasts`
9. `GET /api/v1/families/{family_id}/semantic-context`

### Backend services involved

1. `family_service`
2. `forecast_service`
3. `semantic_service`
4. `publication_service`

### Performance plan

1. overview endpoint powers first render,
2. jurisdiction, field, and timeseries sections are lazy,
3. publication evidence is linked out rather than embedded fully.

## 3. Publication Workspace

### Primary question

`What is the exact document-level evidence behind this family member?`

### Layout

1. publication header
2. bibliographic summary
3. legal / register evidence
4. claims / abstract / description tabs
5. timeline/events
6. related family context

### Core components

1. `PublicationHeader`
2. `PublicationBiblioCard`
3. `PublicationLegalTimeline`
4. `PublicationClaimsViewer`
5. `PublicationAbstractPanel`
6. `RegisterEvidencePanel`
7. `RelatedFamilyPanel`

### Backend endpoints

1. `GET /api/v1/publications/{publication_id}/overview`
2. `GET /api/v1/publications/{publication_id}/text`
3. `GET /api/v1/publications/{publication_id}/legal-timeline`
4. `GET /api/v1/publications/{publication_id}/register-evidence`

### Backend services involved

1. `publication_service`
2. `family_service`

### Performance plan

1. overview endpoint returns metadata and text availability,
2. long text loads separately,
3. descriptions should be lazy-loaded or streamed.

## 4. Lookup / Explore Workspace

### Primary question

`Find the right family, owner, or publication quickly.`

### Layout

1. global search bar
2. result-type tabs
3. filter row
4. result cards
5. quick navigation links

### Core components

1. `GlobalSearchBar`
2. `SearchResultTabs`
3. `FamilyResultCard`
4. `OwnerResultCard`
5. `PublicationResultCard`
6. `SearchFiltersBar`

### Backend endpoints

1. `GET /api/v1/search`
2. `GET /api/v1/search/suggest`

### Backend services involved

1. `family_service`
2. `portfolio_service`
3. `publication_service`

### Performance plan

1. return lightweight cards only,
2. do not preload deep analytics in search results.

## 5. Compare Workspace

### Primary question

`How do two families or two portfolios differ strategically and structurally?`

### Layout

1. compare selector
2. summary cards
3. field overlap matrix
4. blocking power contrast
5. forecast contrast
6. semantic overlap section

### Core components

1. `CompareSelector`
2. `CompareSummaryCards`
3. `CompareFieldMatrix`
4. `CompareBlockingPanel`
5. `CompareForecastPanel`
6. `CompareSemanticOverlapPanel`

### Backend endpoints

1. `GET /api/v1/compare/families`
2. `GET /api/v1/compare/portfolios`

### Backend services involved

1. `comparison_service`
2. `forecast_service`
3. `semantic_service`

### Performance plan

1. one overview compare response for first paint,
2. heavy drill-downs follow as section calls.

## 6. Forecasts Workspace

### Primary question

`What is likely to happen next, and how reliable is that view?`

### Layout

1. scope switcher
2. forecast summary cards
3. model info banner
4. drivers / confidence / caveat panel
5. breakdown tables

### Core components

1. `ForecastScopeSwitcher`
2. `ForecastSummaryCards`
3. `ForecastModelInfoBanner`
4. `ForecastDriverPanel`
5. `ForecastConfidencePanel`

### Backend endpoints

1. `GET /api/v1/forecasts/families/{family_id}`
2. `GET /api/v1/forecasts/portfolios/{owner_id}`
3. `GET /api/v1/forecasts/models`

### Backend services involved

1. `forecast_service`
2. `data_room_service`

### Performance plan

1. first response contains headline forecast values and caveats,
2. model cards and breakdowns can hydrate separately.

## 7. Market Intelligence Workspace

### Primary question

`What is happening in the technology-market landscape itself at this point in time?`

### Role

This workspace should remain distinct from portfolio state.

It should show:
1. rising vs cooling fields,
2. concentration conditions,
3. blocking-density and citation-intensity across market segments,
4. whitespace / saturation signals,
5. top assignee presence by segment,
6. jurisdiction hotspot alignment.

Interpretation:
1. `Market Intelligence` is the workspace name,
2. `segment` is the default UI-neutral grouping term for fields, clusters, and other bounded market slices,
3. cluster-level cuts may still appear inside the workspace where analytically useful.

### Layout

1. market snapshot header
2. top-line state cards
3. market condition table
4. concentration and hotspot panels
5. selected-segment drill-down
6. optional time-series panel

### Core components

1. `MarketIntelligenceHeader`
2. `MarketStateCards`
3. `MarketConditionsTable`
4. `MarketConcentrationPanel`
5. `MarketHotspotPanel`
6. `MarketDetailDrawer`
7. `MarketTimeseriesChart`

### Backend endpoints

1. `GET /api/v1/market-intelligence/overview`
2. `GET /api/v1/market-intelligence/segments`
3. `GET /api/v1/market-intelligence/segments/{segment_id}`
4. `GET /api/v1/market-intelligence/segments/{segment_id}/timeseries`
5. `GET /api/v1/market-intelligence/segments/{segment_id}/assignees`
6. `GET /api/v1/market-intelligence/segments/{segment_id}/jurisdictions`

### Backend services involved

1. `market_intelligence_service`
2. `comparison_service`
3. `portfolio_service` for owner-exposure overlays

### Performance plan

1. overview returns top-line cards and first segment page,
2. selected segment drill-down hydrates on interaction,
3. point-in-time tables should be precomputed from Gold marts.

## 8. Data Room Workspace

### Primary question

`What data, methods, models, and semantic artifacts power PatentIQ?`

### Layout

1. overview
2. sources
3. pipeline
4. datasets
5. metrics
6. models
7. semantic
8. manifests

### Core components

1. `DataRoomOverview`
2. `SourceWikiPage`
3. `PipelineLineageView`
4. `DatasetCatalogTable`
5. `MetricWikiPage`
6. `ModelCardView`
7. `SemanticMethodCard`
8. `ManifestViewer`

### Backend endpoints

1. `GET /api/v1/data-room/overview`
2. `GET /api/v1/data-room/catalog`
3. `GET /api/v1/data-room/catalog/{dataset_id}`
4. `GET /api/v1/data-room/schema/{dataset_id}`
5. `GET /api/v1/data-room/wiki/{page_id}`
6. `GET /api/v1/data-room/manifests`
7. `GET /api/v1/data-room/download/{dataset_id}`

### Backend services involved

1. `data_room_service`
2. `manifest_service`

### Performance plan

1. overview and catalog first,
2. schema and wiki pages fetched lazily,
3. download links issued on demand.

## Frontend Component Settlement

Use these component groupings:

1. `components/ui`
2. `components/portfolio`
3. `components/family`
4. `components/publication`
5. `components/compare`
6. `components/forecasts`
7. `components/market-intelligence`
8. `components/data-room`
9. `components/semantic`

## Frontend Route Settlement

Recommended routes:

1. `/portfolio/[ownerId]`
2. `/family/[familyId]`
3. `/publication/[publicationId]`
4. `/compare`
5. `/forecasts`
6. `/market-intelligence`
7. `/data-room`
8. `/lookup`
9. `/explore`

## Backend Performance Rules

1. precompute heavy Gold marts,
2. route handlers must remain thin,
3. no direct Blob access from frontend for page logic,
4. no direct frontend orchestration of low-level warehouse tables,
5. large tables must paginate server-side,
6. long text must be lazy-loaded,
7. semantic retrieval must return candidate ids first, then analytic enrichment.

## Initial Migration Guidance

### From current V1

Refactor away from:

1. patent/application-first routing only,
2. broader all-purpose page services,
3. dashboard-first UX without stable workspace contracts.

### Toward V2

Move to:

1. family-first primary routes,
2. publication evidence routes,
3. dedicated market intelligence workspace,
4. dedicated Data Room workspace,
5. dedicated backend services with page-shaped contracts.

## Relationship To Other V2 Docs

This baseline should be read together with:

1. [20-patentiq-v2-data-room-architecture-and-contract.md](./20-patentiq-v2-data-room-architecture-and-contract.md)
2. [21-patentiq-v2-azure-runtime-and-storage-architecture.md](./21-patentiq-v2-azure-runtime-and-storage-architecture.md)
3. [22-patentiq-v2-backend-frontend-application-architecture.md](./22-patentiq-v2-backend-frontend-application-architecture.md)
4. [04-product-and-ui-workstreams.md](./04-product-and-ui-workstreams.md)
5. [03-data-and-platform-workstreams.md](./03-data-and-platform-workstreams.md)

# Section 03. Frontend V2 Workspace Architecture And UI Wiring

## Table Of Contents

1. [Purpose Of This Section](#purpose-of-this-section)
2. [What `frontend_v2` Actually Is](#what-frontend_v2-actually-is)
3. [Governing UX Rules Behind The Frontend](#governing-ux-rules-behind-the-frontend)
4. [Route-Group Shell Architecture](#route-group-shell-architecture)
   - [1. Root layout versus workspace layout](#1-root-layout-versus-workspace-layout)
   - [2. Why the home page sits outside the workspace shell](#2-why-the-home-page-sits-outside-the-workspace-shell)
5. [Top-Level Workspace Map](#top-level-workspace-map)
6. [Shared Shell Components](#shared-shell-components)
   - [1. `AppFrame`](#1-appframe)
   - [2. `WorkspaceNav`](#2-workspacenav)
   - [3. `WorkspaceContext` and per-page overrides](#3-workspacecontext-and-per-page-overrides)
7. [Launcher And Entry Patterns](#launcher-and-entry-patterns)
   - [1. Operator console on `/`](#1-operator-console-on-)
   - [2. Portfolio entry search](#2-portfolio-entry-search)
   - [3. Direct family and publication jumps](#3-direct-family-and-publication-jumps)
   - [4. Compare hub](#4-compare-hub)
8. [Deep Workspace Wiring Pattern](#deep-workspace-wiring-pattern)
   - [1. Thin route files, client-owned workspaces](#1-thin-route-files-client-owned-workspaces)
   - [2. URL-driven versus local-state workspaces](#2-url-driven-versus-local-state-workspaces)
   - [3. Overview-first, section-later hydration](#3-overview-first-section-later-hydration)
9. [How The Major Workspaces Behave](#how-the-major-workspaces-behave)
   - [1. Portfolio workspace](#1-portfolio-workspace)
   - [2. Family workspace](#2-family-workspace)
   - [3. Publication workspace](#3-publication-workspace)
   - [4. Market workspace](#4-market-workspace)
   - [5. Compare workspaces](#5-compare-workspaces)
   - [6. Semantic workspace](#6-semantic-workspace)
10. [Shared Rendering Primitives And Visual System](#shared-rendering-primitives-and-visual-system)
   - [1. Surfaces and panels](#1-surfaces-and-panels)
   - [2. Workspace tabs](#2-workspace-tabs)
   - [3. Sortable data tables](#3-sortable-data-tables)
   - [4. Methodology disclosures and tooltips](#4-methodology-disclosures-and-tooltips)
   - [5. Color and chart tokens](#5-color-and-chart-tokens)
11. [Frontend Contract Boundary](#frontend-contract-boundary)
12. [Current Frontend Implementation Truths](#current-frontend-implementation-truths)
13. [Testing Evidence For The Frontend Layer](#testing-evidence-for-the-frontend-layer)
14. [Key Takeaways](#key-takeaways)

## Purpose Of This Section

Section 02 explained how `backend_v2` turns analytical marts into page-shaped API contracts. This section explains the next layer: how `frontend_v2` turns those contracts into the actual application workspaces.

The main question answered here is:

How does the V2 frontend organize routes, state, panels, tables, charts, and evidence cues so the application behaves like an intelligence workspace instead of a loose analytics dashboard?

Primary implementation references:

1. `frontend_v2/README.md:1-120`
2. `docs/new-feature-ideas/ui-workspace-and-page-contract-requirements.md:9-122`
3. `docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md:1-91`
4. `docs/next-phase-v2/78-patentiq-v2-shell-and-landing-implementation-note.md:5-68`

## What `frontend_v2` Actually Is

`frontend_v2` is the current Next.js application runtime. It is the main user-facing implementation for:

1. portfolio workspaces,
2. family workspaces,
3. publication drill-down,
4. market intelligence,
5. compare,
6. semantic search and compare through the V2 backend runtime.

Implementation references:

1. `frontend_v2/README.md:1-15`
2. `frontend_v2/README.md:5-18`

## Governing UX Rules Behind The Frontend

The frontend is not arbitrary styling over endpoints. It follows product rules that are documented in the project notes:

1. PatentIQ should be a guided family-first intelligence workspace, not a loose chart collection.
2. Every strategic page should answer a primary analytical question.
3. Every strategic page should be backed by a page-shaped backend contract.
4. Heavy sections should hydrate separately rather than bloating the initial page load.
5. Strategic insight should always have a drill-down path to evidence or methodology.

Those rules directly explain the V2 frontend structure:

1. stable top-level workspaces,
2. launcher routes plus deep entity routes,
3. overview-first page loading,
4. explicit methodology, caveat, and support UI,
5. separate treatment of strategic pages versus evidence pages.

Implementation references:

1. `docs/new-feature-ideas/ui-workspace-and-page-contract-requirements.md:9-122`
2. `docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md:24-91`

## Route-Group Shell Architecture

### 1. Root layout versus workspace layout

The V2 frontend uses a deliberate split between the global root layout and the workspace route group:

1. `frontend_v2/app/layout.tsx` only defines global metadata and loads `globals.css`.
2. `frontend_v2/app/(workspace)/layout.tsx` wraps workspace routes in `AppFrame`.
3. `AppFrame` then composes the left navigation rail, the route-context bar, and the content canvas.

This shows that the workspace shell is not accidental page duplication. It is a route-group-level architectural decision.

Implementation references:

1. `frontend_v2/app/layout.tsx:1-22`
2. `frontend_v2/app/(workspace)/layout.tsx:1-7`
3. `frontend_v2/components/ui/app-frame.tsx:1-28`
4. `docs/next-phase-v2/78-patentiq-v2-shell-and-landing-implementation-note.md:13-31`

### 2. Why the home page sits outside the workspace shell

The home page is intentionally not forced into the same chrome as deep analytical routes.

That separation exists because:

1. the home page is an operator entry console,
2. workspaces need persistent navigation and route context,
3. entry pages and detail pages serve different user jobs.

This is explicitly recorded in the shell implementation note and reflected in the code: the home page is under `app/page.tsx`, while the analytical shell lives only under `app/(workspace)/layout.tsx`.

Implementation references:

1. `frontend_v2/app/page.tsx:1-120`
2. `frontend_v2/app/(workspace)/layout.tsx:1-7`
3. `docs/next-phase-v2/78-patentiq-v2-shell-and-landing-implementation-note.md:13-24`

## Top-Level Workspace Map

The current route model is best understood as a mix of launcher pages and deep workspace pages:

| Route | Role in the product | Current entry behavior |
| --- | --- | --- |
| `/` | operator landing page | owner search, family jump, publication jump, shortcuts to market/compare/semantic |
| `/portfolio` | portfolio launcher | debounced owner suggestion search |
| `/portfolio/[ownerId]` | owner workspace | full portfolio drill-down |
| `/family` | family launcher | direct jump by family id |
| `/family/[familyId]` | family workspace | evidence-first family page |
| `/publication` | publication launcher | direct jump by publication id |
| `/publication/[publicationId]` | publication workspace | document evidence page |
| `/market` | market workspace | immediate workspace load |
| `/compare` | compare hub | route split into family, portfolio, and semantic lanes |
| `/compare/families` | family compare workspace | entity compare and timeslice compare |
| `/compare/portfolios` | portfolio compare workspace | entity compare and timeslice compare |
| `/compare/semantic` | semantic discovery workspace | anchor-family semantic search and semantic compare |

Implementation references:

1. `frontend_v2/app/page.tsx:1-120`
2. `frontend_v2/app/(workspace)/portfolio/page.tsx:1-14`
3. `frontend_v2/app/(workspace)/portfolio/[ownerId]/page.tsx:1-13`
4. `frontend_v2/app/(workspace)/family/page.tsx:1-21`
5. `frontend_v2/app/(workspace)/family/[familyId]/page.tsx:1-10`
6. `frontend_v2/app/(workspace)/publication/page.tsx:1-21`
7. `frontend_v2/app/(workspace)/publication/[publicationId]/page.tsx:1-13`
8. `frontend_v2/app/(workspace)/market/page.tsx:1-14`
9. `frontend_v2/app/(workspace)/compare/page.tsx:1-56`
10. `frontend_v2/app/(workspace)/compare/families/page.tsx:1-18`
11. `frontend_v2/app/(workspace)/compare/portfolios/page.tsx:1-18`
12. `frontend_v2/app/(workspace)/compare/semantic/page.tsx:1-14`

## Shared Shell Components

### 1. `AppFrame`

`AppFrame` is the shared workspace shell. It:

1. renders `WorkspaceNav`,
2. creates the shared `WorkspaceContextProvider`,
3. renders the route-context bar,
4. provides the main content canvas for all workspace routes.

The use of `Suspense` around both the nav and the context bar is deliberate. It keeps the shell responsive while route-level content resolves.

Implementation references:

1. `frontend_v2/components/ui/app-frame.tsx:1-28`

### 2. `WorkspaceNav`

`WorkspaceNav` is more than a static sidebar. It reads the current pathname and query string and then:

1. determines the active top-level workspace,
2. builds child navigation for route-driven workspaces,
3. humanizes current entity names from route segments,
4. shows a small active-scope summary based on query parameters.

Current primary navigation items are:

1. `Home`
2. `Portfolio`
3. `Family`
4. `Publication`
5. `Market`
6. `Compare`

Subnavigation is currently implemented for:

1. portfolio, where `tab=` drives overview/families/fields/citation/forecast,
2. market, where `section=` and `tab=` drive overview/competition/jurisdictions/technology,
3. compare, where route-level lanes split into hub/families/portfolios/semantic.

Implementation references:

1. `frontend_v2/components/ui/workspace-nav-config.ts:1-63`
2. `frontend_v2/components/ui/workspace-nav.tsx:16-128`
3. `frontend_v2/components/ui/workspace-nav.tsx:130-200`

### 3. `WorkspaceContext` and per-page overrides

`WorkspaceContext` provides the top context bar above every workspace page. It derives:

1. eyebrow text,
2. route-aware page title,
3. description,
4. breadcrumbs,
5. active filter chips.

The important architectural detail is the override system. Individual workspace components can call `useWorkspaceContextOverride()` to replace the generic route-derived title and description with live entity data after the overview payload loads.

Examples:

1. portfolio replaces the generic title with the live owner label and injects owner-switch controls,
2. family replaces the generic description with the representative publication title,
3. publication replaces the generic description with title text or authority/date context.

Implementation references:

1. `frontend_v2/components/ui/workspace-context.tsx:14-175`
2. `frontend_v2/components/ui/workspace-context.tsx:185-260`
3. `frontend_v2/components/portfolio/portfolio-workspace.tsx:900-923`
4. `frontend_v2/components/family/family-workspace.tsx:2241-2249`
5. `frontend_v2/components/publication/publication-workspace.tsx:418-440`

## Launcher And Entry Patterns

### 1. Operator console on `/`

The home page is designed as an operator console, not a marketing splash page.

It combines:

1. portfolio entry search,
2. direct family jump,
3. direct publication jump,
4. shortcut links into market, compare, semantic, and portfolio entry flows.

This is exactly the kind of bounded operational entry the product needs.

Implementation references:

1. `frontend_v2/app/page.tsx:17-120`
2. `frontend_v2/components/home/operator-entry-console.tsx:16-141`
3. `docs/next-phase-v2/78-patentiq-v2-shell-and-landing-implementation-note.md:45-68`

### 2. Portfolio entry search

`PortfolioEntrySearch` is the most sophisticated launcher pattern in the app.

It:

1. debounces backend suggestion requests by 180 ms,
2. searches real harmonized owner ids through the V2 API client,
3. supports keyboard navigation and exact-match promotion,
4. navigates using the harmonized owner id returned by the backend.

This matters because it proves the frontend is not routing on informal labels. It routes on bounded identifiers resolved from the backend search contract.

Implementation references:

1. `frontend_v2/app/(workspace)/portfolio/page.tsx:1-14`
2. `frontend_v2/components/portfolio/portfolio-entry-search.tsx:14-183`

### 3. Direct family and publication jumps

Family and publication launcher pages use the same reusable `DirectWorkspaceJump` pattern.

This gives the product:

1. honest entry points in the navigation,
2. bounded direct access by identifiers,
3. less reliance on hardcoded demo ids.

Implementation references:

1. `frontend_v2/app/(workspace)/family/page.tsx:1-21`
2. `frontend_v2/app/(workspace)/publication/page.tsx:1-21`
3. `frontend_v2/components/ui/direct-workspace-jump.tsx:8-49`
4. `docs/next-phase-v2/78-patentiq-v2-shell-and-landing-implementation-note.md:33-44`

### 4. Compare hub

The compare index page is not a data page. It is a route-selection hub that makes the product distinction explicit:

1. family compare,
2. portfolio compare,
3. semantic discovery/compare.

This is good product design because it avoids conflating metric compare with semantic similarity.

Implementation references:

1. `frontend_v2/app/(workspace)/compare/page.tsx:1-56`

## Deep Workspace Wiring Pattern

### 1. Thin route files, client-owned workspaces

The dynamic route files are intentionally thin.

They mostly do only two things:

1. receive route params from Next.js,
2. pass those params into a client workspace component.

This keeps routing simple while letting the interactive workspace own its own filters, loading states, and drill-down behavior.

Implementation references:

1. `frontend_v2/app/(workspace)/portfolio/[ownerId]/page.tsx:1-13`
2. `frontend_v2/app/(workspace)/family/[familyId]/page.tsx:1-10`
3. `frontend_v2/app/(workspace)/publication/[publicationId]/page.tsx:1-13`
4. `frontend_v2/app/(workspace)/market/page.tsx:1-14`
5. `frontend_v2/app/(workspace)/compare/semantic/page.tsx:1-14`

### 2. URL-driven versus local-state workspaces

One of the most important frontend design choices is that not every workspace stores its section state the same way.

Current URL-driven workspaces:

1. portfolio, using query parameters such as `tab` and `field`,
2. market, using `state`, `segment`, `section`, and `tab`,
3. compare, using query parameters for compare mode, ids, years, and tab,
4. semantic, using `familyId`, `space`, `sameFieldOnly`, and `excludeSameOwner`.

Current mostly local-state workspaces:

1. family, which keeps its active section tab in component state,
2. publication, which renders one evidence page and hydrates internal sections without URL tab state.

This distinction is rational:

1. portfolio, market, compare, and semantic benefit from deep-linkable analytical state,
2. family and publication are more evidence-centric and less filter-heavy in the current release.

Implementation references:

1. `frontend_v2/components/portfolio/portfolio-workspace.tsx:114-200`
2. `frontend_v2/components/market/market-workspace.tsx:554-614`
3. `frontend_v2/components/compare/family-compare-workspace.tsx:346-404`
4. `frontend_v2/components/compare/portfolio-compare-workspace.tsx:205-264`
5. `frontend_v2/components/semantic/semantic-workspace.tsx:155-163`
6. `frontend_v2/components/semantic/semantic-workspace.tsx:304-325`
7. `frontend_v2/components/family/family-workspace.tsx:2004-2009`
8. `frontend_v2/components/family/family-workspace.tsx:2385-2385`
9. `frontend_v2/components/publication/publication-workspace.tsx:295-311`

### 3. Overview-first, section-later hydration

The frontend repeatedly follows the same loading strategy:

1. fetch overview or workspace shell first,
2. render the main entity/page context,
3. hydrate heavy sections after that,
4. keep section loading and section errors local to the workspace.

This pattern matches the backend contract design from Section 02 and is visible throughout the code.

Implementation references:

1. `frontend_v2/components/portfolio/portfolio-workspace.tsx:202-232`
2. `frontend_v2/components/family/family-workspace.tsx:2040-2089`
3. `frontend_v2/components/publication/publication-workspace.tsx:328-407`
4. `frontend_v2/components/market/market-workspace.tsx:616-760`
5. `docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md:40-91`

## How The Major Workspaces Behave

### 1. Portfolio workspace

The portfolio workspace is the heaviest V2 frontend orchestration component.

Its main architectural traits are:

1. it is a client component on a dynamic owner route,
2. it dynamically imports the large tab bodies,
3. it loads a dashboard shell first through `fetchPortfolioDashboard(ownerId)`,
4. it lazily hydrates citation, family, field, forecast, contributor, and pending-grant slices by tab,
5. it persists the last owner in local storage,
6. it overrides the workspace context bar with live owner identity and owner-switch controls.

This is the clearest frontend example of page-shell bootstrapping plus section-level fanout.

Implementation references:

1. `frontend_v2/components/portfolio/portfolio-workspace.tsx:1-170`
2. `frontend_v2/components/portfolio/portfolio-workspace.tsx:202-380`
3. `frontend_v2/components/portfolio/portfolio-workspace.tsx:900-980`

### 2. Family workspace

The family workspace is an evidence-heavy, chart-and-table composition surface.

It:

1. defines four analytical tabs: publications, legal, fields, and citation,
2. loads the overview first,
3. immediately starts legal, fields, timeseries, classification, and forecast section calls after overview success,
4. separately loads members and citations,
5. uses caveats, support labels, chart tokens, metric tooltips, pills, and sortable tables across the same page.

Unlike portfolio, the current family section selection is local UI state rather than URL query state.

Implementation references:

1. `frontend_v2/components/family/family-workspace.tsx:1-120`
2. `frontend_v2/components/family/family-workspace.tsx:2004-2094`
3. `frontend_v2/components/family/family-workspace.tsx:2096-2275`

### 3. Publication workspace

The publication workspace stays intentionally evidence-first.

It:

1. loads a factual overview,
2. then loads `text`, `legal-timeline`, and `register-evidence` in parallel with `Promise.allSettled`,
3. merges caveats from overview and all loaded sections,
4. uses the workspace context bar to show the resolved publication id plus title or authority/date context,
5. links back to the family when a family id is available.

This design is consistent with the product rule that publication is a provenance page, not the default analytical unit.

Implementation references:

1. `frontend_v2/components/publication/publication-workspace.tsx:328-440`
2. `docs/new-feature-ideas/ui-workspace-and-page-contract-requirements.md:21-27`

### 4. Market workspace

The market workspace behaves more like a command surface than a single detail page.

It:

1. reads route query state for market state, selected segment, analysis section, and active tab,
2. loads the main workspace payload first,
3. loads market history and leading jurisdictions separately,
4. parallelizes jurisdiction analysis calls,
5. parallelizes CPC technology detail calls,
6. carries basis metadata and methodology disclosures in the UI itself.

This makes the market page the clearest frontend example of a route-driven analytical control panel.

Implementation references:

1. `frontend_v2/components/market/market-workspace.tsx:554-760`
2. `frontend_v2/components/feedback/methodology-disclosure.tsx:1-74`
3. `docs/new-feature-ideas/ui-workspace-and-page-contract-requirements.md:46-76`

### 5. Compare workspaces

The compare frontend is intentionally split into separate lanes.

Family compare and portfolio compare both:

1. support entity-vs-entity and timeslice modes,
2. derive current mode and entity ids from the query string,
3. maintain suggestion and lookup state locally,
4. update the URL with `router.replace(..., { scroll: false })`,
5. rely on typed compare adapters rather than raw JSON.

This mirrors the backend `CompareService` design from Section 02 and keeps compare fully explainable instead of collapsing multiple comparison semantics into one page.

Implementation references:

1. `frontend_v2/app/(workspace)/compare/page.tsx:1-56`
2. `frontend_v2/components/compare/family-compare-workspace.tsx:346-470`
3. `frontend_v2/components/compare/portfolio-compare-workspace.tsx:205-340`
4. `frontend_v2/lib/api/compare-v2.ts:1-220`

### 6. Semantic workspace

The semantic workspace is a bounded discovery interface.

It:

1. derives the anchor family and vector-space controls from the URL,
2. debounces semantic-covered family suggestions,
3. loads semantic search results only after a family anchor exists,
4. uses `useTransition()` when updating semantic search parameters in the URL,
5. keeps caveats visible from the backend semantic contract,
6. distinguishes claim-space and abstract-space search explicitly.

This is exactly the correct frontend posture for a semantic feature that is powerful but intentionally caveated.

Implementation references:

1. `frontend_v2/components/semantic/semantic-workspace.tsx:155-340`
2. `frontend_v2/lib/api/semantic-v2.ts:1-220`

## Shared Rendering Primitives And Visual System

### 1. Surfaces and panels

`Surface` is the foundational analytical panel primitive. It standardizes:

1. header structure,
2. icon/title composition,
3. badges,
4. optional actions,
5. body framing.

This gives the workspaces a consistent evidence-panel language without forcing identical content blocks.

Implementation references:

1. `frontend_v2/components/ui/surface.tsx:1-48`

### 2. Workspace tabs

`WorkspaceTabs` provides a reusable tablist with:

1. stable ids,
2. human-facing labels,
3. small hint text,
4. explicit ARIA tab semantics.

It is used where the workspace needs section switching without creating a new route.

Implementation references:

1. `frontend_v2/components/ui/workspace-tabs.tsx:1-45`
2. `frontend_v2/components/family/family-workspace.tsx:34-39`

### 3. Sortable data tables

`DataTableShell` is the standard sortable analytical table wrapper across V2.

It uses TanStack Table and provides:

1. stable row ids,
2. client-side sorting,
3. common empty states,
4. optional toolbars,
5. consistent table styling.

This matters because PatentIQ is table-heavy, and the UI contains many score, evidence, and ranking tables.

Implementation references:

1. `frontend_v2/components/data-table/data-table-shell.tsx:1-134`

### 4. Methodology disclosures and tooltips

Two primitives are especially important for explainability:

1. `MethodologyDisclosure`, which previews caveats and expands to the full note set,
2. `PortfolioMetricTooltip`, which provides compact in-place metric definitions with accessible tooltip behavior.

These primitives directly support the product requirement that strategic scores must expose meaning and caveats visibly.

Implementation references:

1. `frontend_v2/components/feedback/methodology-disclosure.tsx:1-74`
2. `frontend_v2/components/portfolio/portfolio-metric-tooltip.tsx:1-80`
3. `docs/new-feature-ideas/ui-workspace-and-page-contract-requirements.md:67-85`

### 5. Color and chart tokens

The V2 frontend does not leave chart semantics to ad hoc color choices.

`enterpriseTokens` and `chartTokens` define:

1. the accent, warning, info, success, and critical palette,
2. panel radii and shadow system,
3. consistent chart colors for rank, risk, delta, and trajectory states.

That consistency matters because portfolio, family, market, compare, and semantic all use chart-heavy surfaces.

Implementation references:

1. `frontend_v2/lib/design/tokens.ts:1-33`
2. `frontend_v2/lib/design/chart-tokens.ts:1-104`
3. `frontend_v2/README.md:104-120`

## Frontend Contract Boundary

The frontend V2 application is not allowed to reach into storage or low-level ETL outputs directly.

The intended layering is:

1. page route files pass ids into client workspaces,
2. client workspaces call typed API adapters under `frontend_v2/lib/api/*`,
3. those adapters normalize backend DTOs into frontend-native types,
4. presentation components render only typed data, not raw storage rows.

This boundary is the reason the same data can be presented in multiple workspace styles without coupling React components to DuckDB, Parquet, or serving snapshots.

Implementation references:

1. `frontend_v2/README.md:1-41`
2. `docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md:40-91`
3. `frontend_v2/lib/api/compare-v2.ts:1-220`
4. `frontend_v2/lib/api/semantic-v2.ts:1-220`

## Current Frontend Implementation Truths

The current frontend has a few important implementation truths:

1. `frontend_v2` is the active V2 UI target, but it is still evolving workspace by workspace.
2. The route-group shell is real and deliberate; the home page is intentionally outside the workspace chrome.
3. Portfolio and market are the most URL-addressable analytical workspaces.
4. Family and publication are more evidence-first and currently keep more interaction state local to the page.
5. Compare is intentionally separated into family, portfolio, and semantic lanes.
6. The semantic page is a bounded discovery workspace, not a universal legal-search surface.
7. The frontend README describes smoke and accessibility coverage; in the current repo, that coverage is consolidated into one Playwright suite rather than separate named spec files.

These are not contradictions. They are the current, inspectable release state of the frontend.

## Testing Evidence For The Frontend Layer

The frontend test evidence currently comes from the Playwright configuration and the consolidated smoke/accessibility suite.

`playwright.config.ts` shows that the test runner:

1. targets `frontend_v2/tests/e2e`,
2. starts the built app on `127.0.0.1:3000`,
3. sets `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000`,
4. prefers the locally installed Chrome application on macOS when available.

The consolidated `smoke.spec.ts` then covers:

1. home route loading,
2. portfolio entry loading,
3. market workspace loading and segment switching,
4. portfolio workspace loading and major tab transitions,
5. family workspace loading,
6. publication workspace loading,
7. family-to-publication drill navigation,
8. serious accessibility violation checks across the core routes and portfolio drilldown tabs.

This is direct evidence that the frontend is being exercised as a route-based workspace product, not just as isolated visual components.

Implementation references:

1. `frontend_v2/playwright.config.ts:1-33`
2. `frontend_v2/tests/e2e/smoke.spec.ts:1-223`

## Key Takeaways

1. `frontend_v2` is a workspace-first Next.js application, not a dashboard skin over raw data.
2. The route-group shell, left navigation rail, context bar, and launcher pages are intentional product architecture, not cosmetic framing.
3. Deep routes stay thin while client workspace components own filters, loading, and drill-down orchestration.
4. The UI wiring follows the same page-shaped philosophy as the backend: overview first, heavy sections later, caveats and methodology visible throughout.
5. Shared primitives such as `Surface`, `WorkspaceTabs`, `DataTableShell`, `MethodologyDisclosure`, and metric tooltips give the product consistent analytical behavior across very different pages.
6. The current frontend is honest about scope: portfolio, family, publication, market, compare, and semantic are implemented to different depths.

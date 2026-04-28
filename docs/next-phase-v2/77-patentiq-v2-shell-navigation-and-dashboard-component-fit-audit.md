# PatentIQ V2 Shell, Navigation, and Dashboard Component-Fit Audit

## Purpose

Audit the current `frontend_v2` shell and landing structure against:

1. the current V2 codebase,
2. the stronger navigation/style patterns in `frontend_v1`,
3. external reference products reviewed through GitHub MCP and web research,
4. the actual data structures already exposed by PatentIQ V2.

This note is meant to prevent the next frontend pass from drifting into:

1. generic admin-template UI,
2. chart-first decoration without analytical payoff,
3. component choices that do not match our real payloads.

Read this together with:

1. [76-patentiq-v2-external-dashboard-reference-adaptation-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/76-patentiq-v2-external-dashboard-reference-adaptation-plan.md)
2. [75-patentiq-v2-compare-ui-and-semantic-runtime-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/75-patentiq-v2-compare-ui-and-semantic-runtime-plan.md)
3. [34-patentiq-v2-compare-and-semantic-workspace-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/34-patentiq-v2-compare-and-semantic-workspace-contract.md)
4. [33-patentiq-v2-portfolio-and-forecast-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md)

## Inputs Reviewed

### Current V2 shell

1. `frontend_v2/app/layout.tsx`
2. `frontend_v2/components/ui/app-frame.tsx`
3. `frontend_v2/components/ui/workspace-nav.tsx`
4. `frontend_v2/components/ui/page-shell.tsx`
5. `frontend_v2/app/page.tsx`
6. `frontend_v2/components/ui/app-frame.module.css`
7. `frontend_v2/components/ui/workspace-nav.module.css`
8. `frontend_v2/components/ui/page-shell.module.css`
9. `frontend_v2/app/page.module.css`
10. `frontend_v2/app/globals.css`

### Current V2 workspace/data shape

1. `frontend_v2/components/portfolio/portfolio-workspace.tsx`
2. `frontend_v2/lib/types/portfolio-v2.ts`
3. `frontend_v2/lib/types/family-v2.ts`
4. `frontend_v2/lib/types/market-v2.ts`
5. `frontend_v2/components/market/market-workspace.tsx`
6. `frontend_v2/components/family/family-workspace.tsx`

### V1 inheritance references

1. `frontend_v1/components/app-sidebar.tsx`
2. `frontend_v1/components/app-header.tsx`
3. `frontend_v1/app/page.tsx`

### External references

Reviewed via GitHub MCP:

1. `dubinc/dub`
2. `Openpanel-dev/openpanel`
3. `umami-software/umami`

Reviewed via web sources:

1. `https://dub.co/analytics`
2. `https://openpanel.dev/`
3. `https://docs.umami.is/docs/filters`
4. `https://v2.umami.is/docs/reports/report-retention`

Reviewed via Context7:

1. Recharts component capabilities under `/recharts/recharts`

## Current V2 Audit

### 1. Shell is too thin for an enterprise workspace

Current V2 wraps everything in:

1. root layout
2. a single top header
3. a centered canvas

That is not enough for a product with:

1. owner-scoped pages,
2. family evidence pages,
3. publication drillthrough,
4. market intelligence,
5. compare workspaces,
6. later semantic workflows.

`frontend_v2/components/ui/app-frame.tsx` currently only renders `WorkspaceNav` plus a generic `canvas`.

This creates three problems:

1. no route-context layer,
2. no entity breadcrumbs,
3. no consistent location for filters, scope caveats, or quick actions.

### 2. Primary navigation is incomplete

Current top navigation only exposes:

1. `Home`
2. `Portfolios`
3. `Markets`
4. `Compare`

That leaves `Family` and `Publication` as hidden destinations even though they are critical evidence workspaces.

This is weaker than both:

1. V1, which at least made the main workflows legible through explicit nav items and homepage entry actions,
2. Umami, which separates shell navigation cleanly across `SideNav`, `TopNav`, and route groups.

### 3. Landing page is still a brochure, not an operator console

`frontend_v2/app/page.tsx` is visually cleaner than early V2, but it remains mostly:

1. static route cards,
2. product copy,
3. abstract signals.

It does not yet function as the actual first screen an analyst should use to:

1. search an owner,
2. jump to a family,
3. jump to a publication,
4. resume recent work,
5. open compare directly with prefilled ids.

V1’s homepage was rougher visually, but stronger functionally because it included:

1. quick lookup,
2. live stats,
3. direct operational entry.

### 4. V2 visual language is cleaner than before, but still generic in the wrong places

The current shell uses:

1. frosted white panels,
2. soft gradients,
3. rounded cards,
4. serif-heavy large titles.

This is acceptable for selected hero surfaces, but across the entire app it becomes:

1. too homogeneous,
2. too static,
3. insufficiently “instrumented”.

The main issue is not that the UI is plain.

The main issue is that the shell does not visually distinguish:

1. command surfaces,
2. evidence surfaces,
3. rankings,
4. time-series panels,
5. legal/support caveat sections.

### 5. Page shell is oversized and under-contextualized

`frontend_v2/components/ui/page-shell.tsx` is useful for marketing-style framing, but too heavy as a default pattern for analytical workspaces.

The giant title panel works for:

1. homepage,
2. maybe compare index,
3. maybe market index.

It is not the right baseline for:

1. portfolio detail,
2. family detail,
3. publication detail.

Those pages need:

1. entity context,
2. compact summary strip,
3. filter scope row,
4. caveat visibility,
5. action rail.

### 6. Portfolio already has enough data to look stronger than it does

Current portfolio types already support:

1. summary cards with bands and peer percentiles,
2. top family preview,
3. filing timeseries,
4. field segment rows,
5. field timeseries,
6. citation summary,
7. citation timeseries,
8. citation families,
9. citation attackers,
10. citation fields,
11. citation jurisdictions,
12. market context,
13. compare timeslices,
14. pending-grant rows.

This means current UI weakness is no longer primarily a data problem.

It is now mostly:

1. shell organization,
2. panel hierarchy,
3. filter ergonomics,
4. chart/panel selection discipline.

### 7. Market is visually stronger than shell, but still lacks command framing

`frontend_v2/components/market/market-workspace.tsx` already uses:

1. `ComposedChart`
2. `BarChart`
3. `Treemap`
4. sparklines

So market has the beginnings of a more useful analytical surface.

The missing part is not raw component variety.

The missing part is:

1. better shell context,
2. stronger segment command header,
3. clearer filter persistence,
4. tighter selected-segment narrative.

### 8. Family is disciplined, but too flat in presentation

The family workspace is now safer and more structured than before, but it still reads like:

1. a good data page,
2. not yet a premium evidence workspace.

The next issue to solve there is not “more data”.

It is:

1. better sequencing,
2. stronger legal/evidence contrast,
3. clearer jurisdiction contribution presentation,
4. tighter linkouts to publication/family/compare routes.

## What V1 Still Donates

V1 should not be copied structurally, but it still donates three useful product instincts.

### 1. Brand identity is more recognizable

V1’s logo treatment and red/white identity are more distinctive than the current generic `PIQ` badge.

### 2. Entry actions are more operational

The V1 homepage made search and lookup first-class actions.

V2 still needs that.

### 3. Navigation speaks in workflows, not just page labels

V1’s naming was imperfect, but it framed the product around tasks:

1. lookup,
2. explore,
3. portfolio analysis.

That is still stronger than a purely static “workspace card” homepage.

## External Product Lessons That Actually Fit PatentIQ

## 1. `Dub`: summary-strip + control-bar + ranked breakdown discipline

The strongest patterns from Dub are not its exact visuals.

They are:

1. summary metrics embedded directly in tab headers,
2. a dedicated chart section with view switching,
3. strong ranked breakdown components,
4. visible sharing/export/filter affordances.

Evidence:

1. Dub’s analytics page emphasizes “Success at a glance”, real-time metrics, detailed geo/device breakdowns, date range, export, filters, and dashboard sharing. Source: `https://dub.co/analytics`
2. The Dub repo’s `analytics-tabs.tsx` puts totals inside the tab strip.
3. `analytics-card.tsx` uses expandable cards with main tabs, optional subtabs, and “View All”.
4. `bar-list.tsx` is a strong ranked-list pattern with search, selection, filter staging, percentages, and modal expansion.

PatentIQ fit:

1. use Dub-like metric tabs and ranked bar lists,
2. do not copy Dub’s product semantics,
3. do not treat every section as a generic card grid.

## 2. `OpenPanel`: analytical workflow framing

OpenPanel’s strongest value is that it treats the dashboard as a working surface, not as decoration.

Evidence:

1. OpenPanel explicitly promotes line charts, bar charts, Sankey flows, and custom dashboards. Source: `https://openpanel.dev/`
2. The homepage also stages retention, notifications, revenue tracking, conversion tracking, and search-console integration in a single analytical workflow. Source: `https://openpanel.dev/`
3. `notifications-and-integrations.mdx` shows clear left-sidebar workflow, right-side editor behavior, and project/workspace separation.

PatentIQ fit:

1. portfolio pages should feel like analytical workspaces with filters and drilldown,
2. forecast, citations, and field sections should behave as task clusters,
3. notification-style “watch these changes” ideas can later inform alerts and semantic monitoring.

## 3. `Umami`: calm shell + universal filtering

Umami’s best lesson is restraint plus consistency.

Evidence:

1. Umami docs describe universal filtering where date range and filters apply across all screens and reports. Source: `https://docs.umami.is/docs/filters`
2. The top of the screen holds date and field filters consistently across reports. Source: `https://docs.umami.is/docs/filters`
3. Umami’s retention report uses a saved parameterized report model with explicit date scope and cohort chart framing. Source: `https://v2.umami.is/docs/reports/report-retention`
4. The repo separates `SideNav`, `TopNav`, and `(main)` dashboard routing cleanly.

PatentIQ fit:

1. V2 needs persistent top-level filters and visible current filter state,
2. market and portfolio should stop scattering filters into isolated local panels,
3. saved “report-like” compare and semantic views are a good later direction.

## Recharts Fit Audit

Context7 confirms our current chart stack can already support the component types we need most:

1. `ComposedChart`
2. `AreaChart`
3. `BarChart`
4. `Treemap`
5. `ScatterChart`
6. `RadarChart`
7. `Sankey`
8. `Brush`
9. `ReferenceLine`
10. `ReferenceArea`

That means the next UI pass does not require a chart-library rewrite.

The real question is not what Recharts supports.

The real question is which of those components fit our data truthfully.

## Component Fit By Workspace

## Shared Shell

### Use

1. Left-rail desktop navigation with top utility/context row.
2. Compact entity header band for detail pages.
3. Persistent filter state chips near the top of the workspace.
4. Clear support/caveat strip for model or coverage warnings.

### Avoid

1. giant marketing hero on every detail page,
2. hiding evidence routes from global nav,
3. burying filters inside individual cards.

## Landing Page

### Use

1. operator entry console,
2. owner search,
3. family jump,
4. publication jump,
5. compare quick-start,
6. recent or pinned work,
7. live platform stats.

### Avoid

1. route-card grid as the primary action model,
2. copy-heavy hero without direct operational entry,
3. static sample links as the only way to enter a workspace.

## Portfolio

Portfolio is the richest place to improve immediately.

### Best-fit components

1. `ComposedChart` for filing strength:
   - yearly family filings as bars,
   - rolling 3y filing count as line,
   - reference marker for incomplete latest year or long-run average.
2. Vertical `BarChart` or Dub-style ranked `bar-list` for:
   - most cited families,
   - top attackers,
   - top forecast contributors.
3. `Treemap` for:
   - leading WIPO fields,
   - global CPC or classification importance blocks.
4. `AreaChart` with `Brush` for:
   - citation timeseries,
   - field share over time where long year ranges exist.
5. Dense comparison strip for:
   - summary cards with band labels, peer percentiles, and count-scope caveats.

### Good panel sequencing

#### Executive tab

1. compact owner briefing header,
2. summary metric strip,
3. filing strength panel,
4. leading fields map,
5. top families leaderboard,
6. caveats/support strip.

#### Citations tab

1. citation summary,
2. citation trend,
3. most cited families,
4. attackers,
5. fields,
6. jurisdictions.

#### Families tab

1. dense table first,
2. dropdown filters for exact WIPO field/status,
3. secondary preview cards only if they improve scan speed.

#### Forecast tab

1. interval-first forecast lane,
2. risk bands,
3. contributor leaderboard,
4. pending-grant support panel.

### Avoid

1. donut-chart spam,
2. overly decorative KPI cards,
3. duplicate panels across tabs,
4. Sankey for citations right now.

Reason:

Current portfolio citation payloads are not stored at a full link-grain suitable for a truthful owner -> field -> jurisdiction flow diagram.

## Family

### Best-fit components

1. compact evidence header instead of oversized hero,
2. legal-state ribbon + coverage/support pills,
3. jurisdiction contribution cards,
4. dated chronology table for citations/legal anchors,
5. small multiple bars for branch/jurisdiction counts,
6. narrow timeseries or banded strip for historical blocking/enforceability proxies.

### Use cautiously

1. `RadarChart` only for compare-style normalized profiles, not as the main family summary chart.

### Avoid

1. treating raw citation internals as user-facing score truth,
2. using large decorative charts where chronology tables are clearer,
3. mixing legal and evidence semantics into one undifferentiated card grid.

## Market

### Best-fit components

1. segment command table with sparklines,
2. treemap for segment or CPC importance blocks,
3. bar leaderboard for top owners,
4. composed chart for market growth versus prior year,
5. attack/jurisdiction ranked tables with filter chips,
6. selected-segment command header with clear rationale.

### Avoid

1. flattening market into just another portfolio page,
2. making selected segment context feel like a detail card rather than an active command surface.

## Compare

### Best-fit components

1. side-by-side score/band strips,
2. normalized delta bars,
3. compact top-family or crown-jewel table,
4. optional radar only for tightly normalized peer metrics.

### Avoid

1. radar as the default compare view,
2. mixing absolute scale and percentile scale in one chart without explicit labeling.

## Component Decisions To Make Explicit

### Adopt now

1. `ComposedChart` for filings strength and mixed stock/flow views.
2. Vertical `BarChart` and ranked list cards for family/attacker/contributor leaderboards.
3. `Treemap` for field and CPC composition.
4. `Brush` for longer time-series panels.
5. `ReferenceLine` and `ReferenceArea` for incomplete years, cohort thresholds, and market medians.

### Use later or selectively

1. `ScatterChart` for peer benchmarking if percentile/size axes are made explicit.
2. `RadarChart` for compare-only normalized lens panels.

### Do not prioritize now

1. `Sankey`

Reason:

It is available in Recharts, but our current serving contracts do not yet expose stable node-link flow data at the right grain for a truthful Sankey.

## Recommended Next Frontend Pass

## Phase 1: shell and landing

1. Introduce `app/(workspace)/layout.tsx`
2. Move to a real workspace shell:
   - left rail on desktop,
   - compact top utility row,
   - entity context bar on detail pages
3. Rebuild home as an operator entry console

## Phase 2: portfolio restructure

1. Use the new shell
2. Re-sequence executive tab
3. Rebuild citations tab around:
   - summary
   - trend
   - ranked families
   - ranked attackers
4. Make families tab a true table-first workspace

## Phase 3: family and market cleanup

1. family becomes calmer evidence-first
2. market becomes stronger command-first
3. unify filters and support/caveat placement

## Phase 4: semantic after runtime exists

Semantic workspace should only begin after backend runtime and routes are real.

The shell work should be completed before that so semantic lands inside a mature product frame.

## Bottom Line

PatentIQ V2 does not need more generic cards.

It needs:

1. stronger shell structure,
2. route-context visibility,
3. operator-first landing actions,
4. ranked analytical panels,
5. filter persistence,
6. better component matching to existing data outputs.

The best composite direction is:

1. `Dub` for summary-strip, ranked-list, and expandable analytics-card behavior,
2. `OpenPanel` for analytical workflow framing and richer dashboard modules,
3. `Umami` for calm shell and universal filter discipline,
4. `Recharts` components already in our stack for truthful implementation.

That is enough to make `frontend_v2` materially more premium and useful without changing the core frontend stack.

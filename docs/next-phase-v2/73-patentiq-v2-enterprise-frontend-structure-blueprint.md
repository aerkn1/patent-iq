# PatentIQ V2 Enterprise Frontend Structure Blueprint

## Purpose

Define the strongest practical frontend structure for PatentIQ V2 as an enterprise SaaS platform.

This note converts the earlier audit and visual-direction documents into a concrete implementation baseline:

1. target application structure,
2. component ownership boundaries,
3. chart and table strategy,
4. UX rules by data shape,
5. phased migration sequence from the current `frontend_v2`.

Read this together with:

1. [60-patentiq-v2-portfolio-page-ui-design-spec.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/60-patentiq-v2-portfolio-page-ui-design-spec.md)
2. [72-patentiq-v2-portfolio-ui-ux-audit-and-restructure-spec.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/72-patentiq-v2-portfolio-ui-ux-audit-and-restructure-spec.md)
3. [22-patentiq-v2-backend-frontend-application-architecture.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/22-patentiq-v2-backend-frontend-application-architecture.md)

## Main Decision

PatentIQ should **not** evolve into a generic dashboard shell.

It should behave like a:

1. corporate intelligence application,
2. evidence-backed analytical workspace,
3. family-first and portfolio-first decision product,
4. premium but restrained enterprise SaaS surface.

The best path is:

1. keep `frontend_v2` as the implementation target,
2. preserve `frontend_v1` only as a reference library,
3. rebuild the V2 presentation layer around a real design system and chart strategy,
4. stop relying on one giant global stylesheet and page-sized client components for product growth.

## Recommended Stack

### Core application layer

1. `Next.js` App Router on a patched release line
2. `React 19`
3. `TypeScript` strict mode

### UI system

1. `shadcn/ui` patterns or direct `Radix UI` primitives for accessible enterprise controls
2. `clsx` for state composition
3. `next/font` for stable typography loading

### Data display

1. `@tanstack/react-table` for normal tables
2. `AG Grid` only for truly enterprise-heavy grids:
   - multi-column grouping
   - advanced filtering
   - pinned analytics views
   - export-heavy analyst workflows

### Charting

Use a **split chart strategy**:

1. `Apache ECharts` for:
   - treemap
   - sunburst
   - heatmap
   - graph / relationship views
   - parallel coordinates
   - dense compare visuals
   - custom domain-specific series
2. `Recharts` for:
   - KPI sparklines
   - compact line and bar charts
   - simple summary visuals embedded in cards
3. `visx` for:
   - highly custom topology views
   - overlap maps
   - concentration or flow visuals when product-specific geometry matters

### Motion

1. `framer-motion` for page and section transitions only
2. no decorative motion on dense analytical surfaces

## Why this stack is the strongest practical enterprise fit

### Why not keep pure custom CSS plus current primitives

That path continues the current drift:

1. inconsistent spacing,
2. repeated shell patterns,
3. styling coupled to page-level implementation,
4. weak accessibility guarantees,
5. slow future page growth.

### Why not use `frontend_v1` as the base

`frontend_v1` has useful ideas, but its structure is not sustainable:

1. large page-level client components,
2. mixed experimental and generated UI,
3. environment-specific API wiring,
4. weaker long-term module boundaries.

### Why not use one chart library for everything

PatentIQ’s data shapes are too different:

1. rankings and compact KPI charts,
2. historical chronology,
3. classification structure,
4. portfolio concentration,
5. threat relationships,
6. market overlays,
7. compare geometry.

One chart library will force compromises that make the product either too generic or too brittle.

## Target frontend structure

The implementation target should converge toward the following structure inside `frontend_v2`.

```text
app/
  (workspace)/
    layout.tsx
    page.tsx
    portfolio/
      page.tsx
      [ownerId]/page.tsx
    family/
      [familyId]/page.tsx
    market/
      page.tsx
  globals.css
  page.tsx

components/
  ui/
    app-frame/
    navigation/
    surface/
    data-table/
    feedback/
    form/
  charts/
    echarts/
    recharts/
    visx/
    shared/
  workspace/
    portfolio/
      overview/
      families/
      technology/
      citations/
      forecast/
    family/
    market/

lib/
  api/
  config/
  design/
    tokens.ts
    chart-tokens.ts
    typography.ts
  format/
  types/
```

## Ownership rules

### `components/ui`

Only generic, reusable building blocks belong here:

1. app chrome,
2. navigation,
3. cards,
4. buttons,
5. tabs,
6. selects,
7. dialogs,
8. tooltips,
9. base table wrappers,
10. skeleton and empty states.

No portfolio-specific logic should live here.

### `components/charts`

This layer owns:

1. chart containers,
2. chart tokens,
3. shared legends,
4. shared tooltip content,
5. axis and annotation helpers,
6. common accessibility wrappers.

It should not know about portfolio or family semantics directly.

### `components/workspace`

This layer owns domain meaning:

1. portfolio concentration,
2. family evidence,
3. citation chronology,
4. classification exposure,
5. risk bands,
6. market overlays.

This is where business framing should live.

## Portfolio page contract

The portfolio page should remain organized into five stories:

1. `Overview`
2. `Families`
3. `Technology`
4. `Citations`
5. `Forecast`

### `Overview`

Use only:

1. KPI groups,
2. coverage summary,
3. preview lists,
4. one forecast headline,
5. one pressure preview.

Do not put full-detail tables here.

### `Families`

Use:

1. enterprise grid,
2. saved filter presets,
3. ranking logic,
4. concentration preview,
5. row-level drill-through to family pages.

### `Technology`

Use:

1. ranked bars,
2. stacked mix charts,
3. chronology chart,
4. classification structure visual,
5. compare deltas as comparison-first visual blocks.

### `Citations`

Use:

1. chronology line and area charts,
2. attacker concentration bars,
3. diversity and concentration cards,
4. threat rows as citation-derived evidence.

### `Forecast`

Use:

1. interval-first headline panels,
2. risk-band distributions,
3. contributor concentration views,
4. pending-grant triage,
5. strong coverage and support disclosure.

## Component-to-data-shape rules

### Metric cards

Use for:

1. bounded KPIs,
2. percentile or banded indicators,
3. compact coverage summaries.

Avoid using cards as the default answer for every domain object.

### Lists and ranked strips

Use for:

1. top families,
2. top fields,
3. top attackers,
4. top risky segments.

### Tables and grids

Use for:

1. analyst filtering,
2. pagination,
3. evidence export,
4. exact row comparison.

Avoid table-first treatment for classification, compare shape, and executive storytelling.

### Chart-first visuals

Use for:

1. time series,
2. direction and band movement,
3. concentration and Pareto patterns,
4. segment and field structure,
5. relationship maps,
6. compare deltas.

## Typography contract

Use a restrained three-font model:

1. `Geist` for UI and interface text,
2. `Geist Mono` for IDs, technical labels, and exact evidence tokens,
3. `Lora` for headline and selective metric emphasis.

Rules:

1. serif is emphasis, not the default reading font,
2. metric emphasis should be consistent,
3. IDs and harmonized keys should always look technical and machine-stable,
4. no fallback drift between routes.

## Color and surface contract

The palette should remain corporate:

1. white and blue-gray neutrals as the base,
2. restrained deep red as the brand accent,
3. green, amber, and red reserved for state semantics,
4. no decorative color per panel unless it communicates domain meaning.

Surface rules:

1. glass only in moderation,
2. shadows soft and sparse,
3. one clear border system,
4. dense views should feel stable before they feel flashy.

## Accessibility and resilience rules

Every new analytical component must support:

1. focus-visible behavior,
2. keyboard navigation,
3. contrast-safe text and controls,
4. tooltip fallback copy,
5. reduced-motion mode,
6. robust empty and partial states.

## Migration sequence

### Phase 1: Foundation

1. patch `Next.js`
2. load typography through `next/font`
3. introduce app frame and primary navigation
4. replace inline shell styling with reusable shell components
5. stabilize tokens

### Phase 2: UI system consolidation

1. introduce reusable UI primitives
2. split global CSS into component-owned styling where practical
3. standardize cards, tabs, filters, banners, and table wrappers

### Phase 3: Portfolio redesign

1. rebuild `Overview`
2. upgrade `Families` into enterprise grid + preview pair
3. rebuild `Technology` visuals around chart-first semantics
4. absorb threat view fully into `Citations`
5. upgrade `Forecast` to interval and band-first communication

### Phase 4: Family and market redesign

1. align family page with the same shell and component rules
2. build market workspace with enterprise chart patterns from the start

## Immediate implementation recommendation

The next coding passes should prioritize:

1. app shell and navigation,
2. font loading and token stability,
3. page-shell cleanup,
4. chart strategy split,
5. portfolio `Technology` and `Forecast` redesign before lower-priority decorative work.

## Final rule

Every screen should answer this question clearly:

Is the user looking at:

1. a current-state fact,
2. a historical replay,
3. a normalized comparison,
4. a forecast,
5. or a coverage caveat?

If a surface mixes those modes without clear visual separation, it is not enterprise-ready.

# PatentIQ V2 Tailwind Component Migration And UI Debloat Plan

## Goal

Move `frontend_v2` from page-owned CSS modules toward a Tailwind-based enterprise analytics system without turning PatentIQ into a generic dashboard kit.

The migration should solve two problems together:

1. component inconsistency across `portfolio`, `family`, `publication`, `market`, `compare`, and `semantic`
2. UI bloat from repeated caveats, support-level copy, denominator explanations, and duplicated summary values

## Why Tailwind Is Now The Right Move

`frontend_v2` is currently driven by custom CSS modules and a small dependency set in [frontend_v2/package.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/package.json). That has worked for initial V2 delivery, but it continues the drift already called out in [73-patentiq-v2-enterprise-frontend-structure-blueprint.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/73-patentiq-v2-enterprise-frontend-structure-blueprint.md) and [77-patentiq-v2-shell-navigation-and-dashboard-component-fit-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/77-patentiq-v2-shell-navigation-and-dashboard-component-fit-audit.md).

Allowing Tailwind means we can use:

1. `shadcn/ui` patterns and `Radix UI` primitives for accessible controls
2. `Tailwind CSS` tokens for consistent spacing, borders, radii, and density
3. a split chart and table strategy that fits the actual backend contracts

## Recommended Dependency Set

### Foundation

Required:

1. `tailwindcss`
2. `@tailwindcss/postcss`
3. `class-variance-authority`
4. `tailwind-merge`
5. `tw-animate-css`

Recommended for typed shadcn-style composition:

1. `@radix-ui/react-dialog`
2. `@radix-ui/react-dropdown-menu`
3. `@radix-ui/react-hover-card`
4. `@radix-ui/react-navigation-menu`
5. `@radix-ui/react-scroll-area`
6. `@radix-ui/react-select`
7. `@radix-ui/react-separator`
8. `@radix-ui/react-slot`
9. `@radix-ui/react-tabs`
10. `@radix-ui/react-tooltip`

### Data Tables

Default:

1. `@tanstack/react-table`
2. `@tanstack/react-virtual`

Optional and limited:

1. `ag-grid-react`
2. `ag-grid-community`
3. `ag-grid-enterprise`

AG Grid should be reserved for:

1. future `Data Room`
2. publication or family evidence matrices if they become analyst-grade export surfaces
3. any table requiring grouped/pinned/export-heavy workflows

### Charts

Keep:

1. `recharts`

Add:

1. `echarts`
2. `echarts-for-react`

Optional specialty layer:

1. `@visx/xychart`
2. `@visx/responsive`
3. `@visx/tooltip`
4. `@visx/shape`
5. `@visx/group`
6. `@visx/scale`
7. `@visx/brush`

## Chart And Table Fit By PatentIQ Data Contract

### Recharts

Best for:

1. KPI sparklines
2. compact line charts
3. compact bar charts
4. small chronology panels
5. forecast interval and band summaries inside cards

Use on:

1. portfolio overview
2. family overview
3. publication summary

### ECharts

Best for:

1. treemap
2. heatmap
3. graph / relationship views
4. sankey when truthful node-link data exists
5. radar compare views
6. parallel coordinates
7. dense compare geometry

Use on:

1. market intelligence
2. compare
3. later semantic graph exploration

### visx

Best for:

1. custom topology
2. overlap maps
3. brush-linked exploration
4. product-specific geometry that neither Recharts nor ECharts handles cleanly

Use sparingly.

### TanStack Table

Default table engine for:

1. portfolio rows
2. family evidence tables
3. publication register tables
4. market ranked tables
5. compare support rows
6. semantic result lists

### AG Grid

Only for:

1. Data Room
2. analyst evidence matrix
3. advanced export or grouping workflows

## Target Component Structure

Keep `components/ui` as the shared primitive layer, but split by responsibility.

### `frontend_v2/components/ui`

Own:

1. button
2. input
3. select
4. tabs
5. tooltip
6. dialog
7. sheet
8. breadcrumb
9. sidebar
10. badge / pill
11. card / surface
12. skeleton
13. empty-state

### `frontend_v2/components/data-table`

Own:

1. base table shell
2. column visibility
3. filter row
4. pagination
5. row selection
6. density switch
7. table empty state

### `frontend_v2/components/charts/recharts`

Own:

1. sparkline
2. compact line chart
3. compact bar chart
4. interval band chart
5. brush timeline when light-weight

### `frontend_v2/components/charts/echarts`

Own:

1. treemap panel
2. heatmap panel
3. radar panel
4. graph panel
5. parallel panel
6. sankey panel

### `frontend_v2/components/charts/visx`

Own:

1. overlap map
2. custom topology
3. analyst brush components

### `frontend_v2/components/filters`

Own:

1. scope chips
2. persistent filter row
3. compact query controls
4. report-state badges

### `frontend_v2/components/feedback`

Own:

1. support strip
2. caveat indicator
3. coverage state
4. methodology linkout

### `frontend_v2/components/layout`

Own:

1. compact entity header
2. workspace section header
3. command rail
4. analytics panel grid

## UI Debloat Rules

These rules are mandatory. Tailwind migration should not preserve current verbosity.

### 1. One support surface per page

Do not repeat:

1. support level badge in the hero
2. support summary card
3. support row inside a section
4. caveat panel at the bottom

Choose one visible support surface:

1. a compact top strip with support tone and one short label
2. a `Methodology / Coverage` drawer or sheet for details

### 2. Do not repeat denominators

The same denominator story currently appears in multiple places, especially on portfolio.

Show denominator or scope once:

1. in a compact scope strip
2. with hover help
3. with a single deeper methodology entry point

Do not also repeat it as:

1. summary note
2. coverage panel paragraph
3. second caveat sentence

### 3. Caveats are not a primary content block

Caveats should never dominate a page unless the page is explicitly an evidence or methodology view.

Default behavior:

1. show a caveat count or warning pill if material
2. link to `Methodology / Support`
3. show full caveat cards only in evidence-first or methodology-first contexts

### 4. Avoid mirrored explanation copy in compare

Compare currently uses descriptive copy in multiple sections and then repeats caveats again.

Keep:

1. compare header
2. actual metric panels
3. one evidence tab

Remove:

1. repeated interpretation paragraphs
2. caveat-first section framing
3. support and caveat counts in the hero if the evidence tab already carries them

### 5. Publication should be evidence-first, not support-first

Publication is currently especially verbose relative to its analytics value.

Keep visible:

1. bibliographic summary
2. family context
3. text/register/timeline tabs
4. provenance entry point

Move out of the default path:

1. full method caveat list
2. text availability explanation cards
3. support badge prominence in the hero

### 6. Market should behave like an instrument panel

Keep:

1. command filters
2. segment selector
3. executive segment summary
4. evidence tabs

Reduce:

1. explanatory ribbon note text
2. duplicated freshness and comparable-year copy
3. long rationale prose when the same meaning is already encoded in metrics

### 7. Family chronology should not over-explain data lineage inline

Family can keep exact evidence and chronology, but the current trajectory notes are too editorial for a professional analytics workspace.

Prefer:

1. one short chronology note
2. one optional provenance drawer

Avoid:

1. stacked paragraphs below every chronology table

## Page-Level Cleanup Targets

### Portfolio

Current problems:

1. summary cards plus coverage panel plus scope note repeat the same scope story
2. executive tab is still too explanatory

Target:

1. compact scope strip near the top
2. summary cards
3. one `Coverage / Methodology` sheet
4. no large coverage prose in the main flow

### Family

Current problems:

1. repeated caveat panels by tab
2. chronology notes are too verbose

Target:

1. compact support strip
2. evidence tab for full detail
3. one provenance / methodology entry

### Publication

Current problems:

1. support badge in hero
2. text availability panel
3. full caveat panel at bottom

Target:

1. compact entity header
2. exact evidence panels
3. provenance footer or sheet
4. support details hidden behind methodology

### Market

Current problems:

1. too many notes explaining freshness and comparability
2. drawer and controls restate information already visible in pills

Target:

1. tighter command bar
2. leaner summary drawer
3. one methodology chip opening a sheet

### Compare

Current problems:

1. hero repeats support and caveats
2. evidence tab repeats explanatory copy

Target:

1. compare header with entity context only
2. summary and overlap panels first
3. evidence tab carrying support rows
4. methodology link for caveats

## Migration Sequence

### Phase 1

1. add Tailwind foundation dependencies
2. wire Tailwind into `frontend_v2`
3. keep existing CSS modules temporarily
4. introduce shared `ui`, `data-table`, and `feedback` primitives

### Phase 2

1. migrate shell, pills, surfaces, tabs, and filter controls
2. remove duplicated caveat and support surfaces
3. standardize compact entity header pattern

### Phase 3

1. migrate portfolio and market first
2. add TanStack table wrappers
3. keep Recharts for compact visuals

### Phase 4

1. add ECharts surfaces for market and compare
2. reserve AG Grid for Data Room and matrices
3. use visx only for custom topology

## Immediate Implementation Recommendation

Do next:

1. Tailwind foundation
2. shared primitives
3. portfolio debloat
4. publication debloat
5. compare hero and evidence cleanup

Do not do next:

1. full AG Grid rollout
2. blanket chart-library rewrite
3. page-by-page Tailwind rewrite without shared primitives

## External References

1. Tailwind Next.js install: `https://tailwindcss.com/docs/installation/framework-guides/nextjs`
2. shadcn install and components: `https://ui.shadcn.com/docs/installation/next`
3. shadcn GitHub: `https://github.com/shadcn-ui/ui`
4. Radix primitives overview: `https://www.radix-ui.com/primitives/docs/overview/introduction`
5. Radix GitHub: `https://github.com/radix-ui/primitives`
6. TanStack Table docs: `https://tanstack.com/table/latest`
7. TanStack Table GitHub: `https://github.com/TanStack/table`
8. AG Grid React docs: `https://ag-grid.com/react-data-grid/`
9. AG Grid GitHub: `https://github.com/ag-grid/ag-grid`
10. Apache ECharts docs: `https://echarts.apache.org/en/index.html`
11. Apache ECharts GitHub: `https://github.com/apache/echarts`
12. visx GitHub: `https://github.com/airbnb/visx`
13. Tremor docs: `https://www.tremor.so/docs/getting-started/about`
14. OpenPanel: `https://openpanel.dev/`
15. Umami reports: `https://v2.umami.is/docs/reports` and `https://v2.umami.is/docs/reports/report-retention`

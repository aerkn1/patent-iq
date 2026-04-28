# PatentIQ V2 Portfolio UI/UX Audit And Restructure Specification

## Purpose

Capture the current portfolio-page UX problems in `frontend_v2`, record the concrete evidence behind those problems, and define the first clean restructure path for the portfolio workspace.

This note is intentionally narrower than the original page design spec. It is a remediation and implementation note driven by the actual current state of the page.

Read this together with:

1. [60-patentiq-v2-portfolio-page-ui-design-spec.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/60-patentiq-v2-portfolio-page-ui-design-spec.md)
2. [61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md)
3. [71-patentiq-v2-peer-banding-and-compare-ranking-policy.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/71-patentiq-v2-peer-banding-and-compare-ranking-policy.md)

## Main Conclusion

The current portfolio page is functionally richer than before, but it does not yet feel like a coherent product surface.

The main problem is not missing data alone.

The main problem is that the page currently:

1. duplicates deep-dive content across top-level tabs,
2. uses nearly the same visual wrapper for almost every data type,
3. mixes current overlays, historical replay views, and forecast views without enough layout separation,
4. repeats page-level framing and explanatory chrome in ways that weaken hierarchy.

As a result, the page reads like a collection of recovered endpoint panels rather than a deliberate intelligence workspace.

## Direct Audit Findings

### 1. Duplicate page framing

Current page framing is duplicated:

1. the route page renders a full shell header in [frontend_v2/components/ui/page-shell.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/ui/page-shell.tsx),
2. the portfolio page then renders a second hero in [frontend_v2/components/portfolio/portfolio-header.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/portfolio/portfolio-header.tsx).

This creates a hero-on-hero stack and wastes the strongest visual real estate before the actual workspace begins.

### 2. Executive tab is not a briefing tab

In [frontend_v2/components/portfolio/portfolio-workspace.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/portfolio/portfolio-workspace.tsx), the `executive` tab currently renders:

1. summary cards,
2. coverage panel,
3. full top-families table,
4. full forecast panel,
5. full field-exposure panel,
6. full threat panel.

That means the Executive tab is already a near-complete page, and the later tabs often feel like repetition rather than drilldown.

### 3. Top-level IA is too fragmented

Current primary tabs:

1. `Executive`
2. `Citations`
3. `Families`
4. `Field Clusters`
5. `Threats`
6. `Forecast`
7. `Classification`
8. `Compare`

Problems:

1. `Threats` is citation-derived competitive pressure and does not need its own first-order tab,
2. `Classification` belongs to the technology/field story,
3. `Compare` is a secondary analytical lens, not a peer tab to the portfolio’s core narratives,
4. `Field Clusters`, `Classification`, and `Compare` are three separate tabs for what most users perceive as one broader technology-footprint story.

### 4. Visual language is too uniform

The current CSS in [frontend_v2/app/globals.css](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/app/globals.css) applies almost the same treatment to:

1. summary cards,
2. field rows,
3. forecast cards,
4. compare tables,
5. citation summaries,
6. threat rows.

Symptoms:

1. same border treatment,
2. same shadow depth,
3. same rounded surface language,
4. same red-accent pill treatment,
5. same table/list fallback for very different semantic objects.

This makes the whole page look safe and generic instead of intentional and domain-shaped.

### 5. Component type often does not fit the data

Examples:

1. [frontend_v2/components/portfolio/portfolio-market-context-panel.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/portfolio/portfolio-market-context-panel.tsx) uses forecast-card styling for market-overlay data,
2. [frontend_v2/components/portfolio/portfolio-citation-summary-panel.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/portfolio/portfolio-citation-summary-panel.tsx) also uses forecast-card styling for citation evidence,
3. [frontend_v2/components/portfolio/portfolio-classification-panel.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/portfolio/portfolio-classification-panel.tsx) reduces technology structure to a plain table,
4. [frontend_v2/components/portfolio/portfolio-compare-panel.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/portfolio/portfolio-compare-panel.tsx) presents shape comparison as a plain evidence table instead of a comparison-first visual.

## What Still Feels Professional In V1

The old `frontend_v1` portfolio slice is narrower, but some of its product behaviors are stronger:

1. a clearer distinction between headline metrics and deep-dive components,
2. chart-first treatment for time-based data,
3. more deliberate metric grouping inside a single card,
4. less duplication between “summary” and “detail” surfaces,
5. better use of motion and sectional density for reading rhythm.

Reference components:

1. [frontend_v1/components/portfolio-overview-card.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v1/components/portfolio-overview-card.tsx)
2. [frontend_v1/components/portfolio-health-cards.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v1/components/portfolio-health-cards.tsx)
3. [frontend_v1/components/portfolio-forecast-card.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v1/components/portfolio-forecast-card.tsx)
4. [frontend_v1/components/portfolio-citation-evolution-chart.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v1/components/portfolio-citation-evolution-chart.tsx)

The V2 page should not copy V1 literally, but it should inherit:

1. clearer grouping,
2. more chart-first semantics,
3. less panel repetition,
4. more obvious difference between summary lanes and drilldown lanes.

## Required IA Reset

The portfolio workspace should collapse into five primary stories:

1. `Overview`
2. `Families`
3. `Technology`
4. `Citations`
5. `Forecast`

### `Overview`

This is a briefing tab, not a mirror of the whole workspace.

It should contain:

1. summary metrics,
2. coverage/reliability context,
3. top-family preview only,
4. top-field footprint preview only,
5. short forecast headline,
6. short external-pressure preview.

It should not contain the full heavy tables that also define the detail tabs.

### `Families`

This tab owns:

1. family ranking,
2. family filtering,
3. family sort/search,
4. family-level forecast contribution context.

### `Technology`

This tab owns both current and historical technology structure:

1. current field exposure,
2. current market overlay,
3. field chronology with caveated fallback behavior,
4. classification exposure,
5. compare/time-slice evidence.

This makes the field/classification/compare story coherent instead of split into three parallel tabs.

### `Citations`

This tab owns:

1. citation summary,
2. forward chronology,
3. attacker momentum,
4. field and jurisdiction pressure slices,
5. current external threat concentration.

`Threats` should become a citation sub-surface, not a separate top-level page mode.

### `Forecast`

This tab owns:

1. interval-first portfolio forecast,
2. lapse-risk bands,
3. contributor concentration,
4. pending-grant contract when available,
5. coverage caveats relevant to forecast consumption.

Current market overlay should not be duplicated here if it already lives in `Technology`.

## Required Visual Reset

The current token system is serviceable, but the page needs more distinct component families.

### Keep

1. the red/white/gray V1-adjacent palette,
2. serif metric emphasis,
3. soft glass depth in moderation,
4. tooltip-heavy explanation model.

### Change

1. remove the route-level shell hero from the portfolio page,
2. keep a single owner hero with stronger spacing and less explanatory copy,
3. reduce repeated pills and dashed warning boxes,
4. stop reusing forecast cards for citation and market-overlay evidence,
5. give tables stronger sectional framing and less generic spreadsheet treatment,
6. use compact preview strips and ranked lists in `Overview`,
7. reserve full tables for detail tabs only.

## Component-Type Recommendations By Data Shape

### Use ranked preview lists for

1. top families,
2. top fields,
3. top external pressure rows.

### Use chart-first components for

1. field chronology,
2. citation chronology,
3. compare/time-slice shape deltas,
4. contributor concentration.

### Use metric-card groups only for

1. core summary KPIs,
2. forecast headline interval,
3. compact coverage indicators.

### Avoid table-first presentation for

1. classification exposure,
2. compare shape,
3. market overlay,
4. executive summaries.

## Browser-Based Audit Note

Playwright MCP was used to audit the rendered page through `host.docker.internal`.

Audit-specific environment handling was required because:

1. the browser runner is containerized,
2. the local frontend had to point at `host.docker.internal:8000`,
3. the backend had to allow `host.docker.internal` origins and be reachable from outside `127.0.0.1`.

These adjustments were necessary for the audit path and should not be confused with the actual portfolio UX fix.

## First Implementation Pass

The current first polish pass in `frontend_v2` has been applied with the following concrete changes:

1. `PortfolioHeader` now uses a two-lane hero:
   - left lane for owner narrative and signal cards,
   - right lane for owner identity and search.
2. `PortfolioPrimaryTabs` now uses label plus sub-label treatment so the top-level IA reads as briefing lanes rather than generic pills.
3. `PortfolioOverviewBrief` now starts with a `Current read` headline strip and summary metric tiles before the ranked preview panels.
4. `Forecast` now has a stronger composition:
   - forecast headline as the main panel,
   - coverage and consumption guidance as the side rail,
   - pending-grant and contributors as the lower detail band.

This pass improves hierarchy and reduces the “uniform generic card” feel, but it does not yet complete the full portfolio visual reset.

## Remaining Frontend Gaps After The First Pass

The following items remain for the next portfolio UI refinement cycle:

1. citation panels still need more chart-first and evidence-shaped presentation,
2. market-overlay styling still reads too close to forecast-card language,
3. technology panels still rely too heavily on table/list treatment for classification and compare,
4. a full browser-based rendered audit through MCP still depends on exposing the backend to the containerized browser path, not only to local loopback.

The first portfolio refactor should do only the following:

1. remove duplicate route-shell hero framing,
2. reduce top-level tabs to the five real stories,
3. turn `Executive` into `Overview`,
4. replace heavy executive panels with compact previews,
5. move `Threats` into `Citations`,
6. move `Classification` and `Compare` into `Technology`,
7. keep the data contracts stable while changing the page composition.

This gives a visible product improvement without reopening backend serving contracts first.

## Second Implementation Pass

After the structural cleanup:

1. replace plain classification tables with composition-first visuals,
2. replace compare table with visual delta modules,
3. redesign citation tab with clearer chronology-vs-pressure separation,
4. tighten typography, spacing, and motion to match the chosen V1-derived tone,
5. add route-safe browser/dev-origin configuration for local audit and QA tooling.

## Product Rule

The portfolio page should present one clear thought per tab.

If a component makes the same argument as another tab, it does not belong in the overview.

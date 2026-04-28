# PatentIQ V2 External Dashboard Reference Adaptation Plan

## Purpose

Document the GitHub reference repositories reviewed through MCP and convert them into an explicit adaptation plan for `frontend_v2`.

This note is not a moodboard.

It is an implementation filter:

1. which external products are worth borrowing from,
2. which exact behaviors fit PatentIQ V2,
3. which patterns should be rejected,
4. how those patterns map onto our current route and component structure.

Read this together with:

1. [60-patentiq-v2-portfolio-page-ui-design-spec.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/60-patentiq-v2-portfolio-page-ui-design-spec.md)
2. [72-patentiq-v2-portfolio-ui-ux-audit-and-restructure-spec.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/72-patentiq-v2-portfolio-ui-ux-audit-and-restructure-spec.md)
3. [73-patentiq-v2-enterprise-frontend-structure-blueprint.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/73-patentiq-v2-enterprise-frontend-structure-blueprint.md)
4. [75-patentiq-v2-compare-ui-and-semantic-runtime-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/75-patentiq-v2-compare-ui-and-semantic-runtime-plan.md)

## Current PatentIQ V2 Constraint

PatentIQ V2 currently uses:

1. `Next.js 16`
2. `React 19`
3. `TypeScript`
4. `CSS modules`
5. `Recharts`
6. a custom shell built around:
   - `frontend_v2/components/ui/app-frame.tsx`
   - `frontend_v2/components/ui/workspace-nav.tsx`
   - `frontend_v2/components/ui/page-shell.tsx`

That means we should borrow:

1. information architecture,
2. layout behavior,
3. panel semantics,
4. navigation patterns,
5. dashboard reading rhythm.

We should **not** try to transplant:

1. Tailwind utility stacks,
2. shadcn component trees,
3. full monorepo structures,
4. unrelated backend product assumptions.

## Reference Repositories Reviewed

### 1. `dubinc/dub`

Repository:

1. `https://github.com/dubinc/dub`

Why it matters:

1. strongest enterprise SaaS shell discipline,
2. clear route segmentation,
3. domain-oriented UI folder ownership,
4. operator-grade layout, not a template demo.

Concrete evidence:

1. App Router structure under `apps/web/app`
2. UI domains under `apps/web/ui`
3. dedicated layout grouping and workspace-specific UI folders

PatentIQ V2 borrowing value:

1. best reference for application shell and workspace structure,
2. best reference for route and domain ownership,
3. best reference for how `portfolio`, `family`, `market`, `compare`, and later `semantic` should feel like parts of one product.

### 2. `Openpanel-dev/openpanel`

Repository:

1. `https://github.com/Openpanel-dev/openpanel`

Why it matters:

1. it is a real analytics product, not a static admin kit,
2. it emphasizes live analytical workflows,
3. it balances dense metrics, control bars, and dashboard drilldowns.

Concrete evidence:

1. analytics-focused product positioning in the README
2. real app split between `api`, `public`, `worker`
3. modern TS product stack with `Next.js`, `tRPC`, `Tailwind`, `Shadcn`

PatentIQ V2 borrowing value:

1. best reference for analytics panel behavior,
2. best reference for control bars, filters, and panel sequencing,
3. best reference for how `citations`, `technology`, and `forecast` should feel like analytical workspaces instead of card dumps.

### 3. `umami-software/umami`

Repository:

1. `https://github.com/umami-software/umami`

Why it matters:

1. it shows better restraint than many analytics products,
2. it has clear top-nav / side-nav shell separation,
3. it organizes dashboard routes cleanly under a `(main)` app group.

Concrete evidence:

1. `src/app/(main)/SideNav.tsx`
2. `src/app/(main)/TopNav.tsx`
3. `src/app/(main)/dashboard`
4. clean route grouping under `src/app/(main)`

PatentIQ V2 borrowing value:

1. best reference for clarity and navigational calm,
2. best reference for not over-decorating analytical surfaces,
3. best reference for the family and market pages where readability matters more than visual novelty.

### 4. `vercel/nextjs-postgres-nextauth-tailwindcss-template`

Repository:

1. `https://github.com/vercel/nextjs-postgres-nextauth-tailwindcss-template`

Why it matters:

1. it is structurally clean,
2. it shows a useful `(dashboard)` route grouping,
3. it is a good App Router baseline.

PatentIQ V2 borrowing value:

1. only as route and layout scaffolding inspiration,
2. not as a visual or analytical reference.

### 5. `metabase/metabase` and `apache/superset`

Repositories:

1. `https://github.com/metabase/metabase`
2. `https://github.com/apache/superset`

Why they matter:

1. they prove what serious analytics products need in terms of filter logic, chart variety, and dashboard composition,
2. they are useful for future charting and analysis interaction design.

Why they are not direct design references:

1. they are BI platforms, not operator-first product intelligence apps,
2. their visual and architectural assumptions are heavier than PatentIQ needs,
3. copying them would push PatentIQ toward a generic BI tool instead of a focused IP intelligence product.

## Reference Ranking For PatentIQ V2

### Tier A: direct reference

1. `dubinc/dub`
2. `Openpanel-dev/openpanel`
3. `umami-software/umami`

### Tier B: structural helper

1. `vercel/nextjs-postgres-nextauth-tailwindcss-template`

### Tier C: idea bank only

1. `metabase/metabase`
2. `apache/superset`

## Adaptation Rules

### Rule 1: borrow patterns, not implementation stacks

PatentIQ should borrow:

1. layout hierarchy,
2. navigation behavior,
3. control-bar logic,
4. reading rhythm,
5. dashboard segmentation.

PatentIQ should not borrow:

1. Tailwind code,
2. shadcn component internals,
3. monorepo complexity,
4. unrelated auth or billing shells.

### Rule 2: keep PatentIQ as a product workspace, not a BI tool

The references should make PatentIQ:

1. more coherent,
2. more navigable,
3. more analytical,
4. more enterprise-grade.

They should not make PatentIQ:

1. more generic,
2. more card-heavy,
3. more admin-template-like,
4. more BI-dashboard-like than the product needs.

### Rule 3: shell consistency first, page novelty second

Before reworking every page visually, PatentIQ must first unify:

1. global navigation,
2. workspace framing,
3. route entry points,
4. page-mode headers,
5. cross-page identity treatment.

## What To Borrow From Each Repo

### Borrow from `Dub`

#### A. Workspace-level navigation discipline

Apply to:

1. `frontend_v2/components/ui/workspace-nav.tsx`
2. `frontend_v2/components/ui/app-frame.tsx`
3. future `frontend_v2/app/(workspace)/layout.tsx`

Target effect:

1. the shell should feel like a product control surface,
2. each route should feel intentional,
3. navigation should emphasize major product modes, not page leftovers.

#### B. Domain-owned component grouping

Apply to:

1. `frontend_v2/components/portfolio`
2. `frontend_v2/components/family`
3. `frontend_v2/components/compare`
4. future `frontend_v2/components/market`
5. future `frontend_v2/components/semantic`

Target effect:

1. stop growing one-off generic page components,
2. align component ownership with workspace semantics.

#### C. Operator-grade table/list treatment

Apply to:

1. portfolio families
2. most-cited families
3. attacker lists
4. compare support rows

Target effect:

1. cleaner row hierarchy,
2. stronger row actions,
3. less spreadsheet-like dead space.

### Borrow from `Openpanel`

#### A. Analytical control-bar pattern

Apply to:

1. `portfolio citations`
2. `portfolio technology`
3. `portfolio forecast`
4. future `market`
5. future `semantic search`

Target effect:

1. filters, sort, and scope selection should feel like a deliberate analysis bar,
2. controls should sit close to the panel they affect,
3. deep filters should not be hidden in random form pockets.

#### B. Summary-first panel sequencing

Apply to:

1. `portfolio executive`
2. `citations`
3. `technology`
4. `forecast`

Target effect:

1. lead with interpretation,
2. follow with evidence,
3. then expose dense detail.

#### C. Dense analytics without visual collapse

Apply to:

1. chart and table adjacency,
2. panel grouping,
3. compare pages,
4. forecast detail.

Target effect:

1. multiple panels can live on one page without looking like repeated cards.

### Borrow from `Umami`

#### A. Side/top navigation calm

Apply to:

1. future V2 workspace shell
2. family page
3. market page
4. semantic page later

Target effect:

1. reduce visual noise,
2. improve scanability,
3. make dense analytical content feel trustworthy.

#### B. Dashboard restraint

Apply to:

1. metric density,
2. spacing,
3. chart framing,
4. panel typography.

Target effect:

1. stop overusing pills and repeated highlight boxes,
2. use stronger visual contrast only where it matters.

### Borrow from `Vercel dashboard template`

#### A. App Router grouping discipline

Apply to:

1. `app/(workspace)`
2. route-level shell composition
3. future compare/semantic layouts

Target effect:

1. keep route and layout structure predictable,
2. reduce ad hoc page wrapper behavior.

## PatentIQ Route Mapping

### 1. Home

Primary references:

1. `Dub`
2. `Umami`

Required change:

1. turn the landing page into an entry console, not a brochure grid,
2. show live route entry modules:
   - portfolio owner search
   - family jump
   - publication jump
   - compare launch
   - market launch
3. keep product positioning secondary.

### 2. Portfolio

Primary references:

1. `Dub`
2. `Openpanel`

Required change:

1. one strong owner hero only,
2. no duplicate route shell hero above it,
3. tighter story-based tabs:
   - Overview
   - Families
   - Technology
   - Citations
   - Forecast
4. stronger control bars and chart-first panel semantics,
5. more deliberate table actions and preview rows.

### 3. Family

Primary references:

1. `Umami`
2. `Dub`

Required change:

1. keep family page cleaner than portfolio,
2. use a stronger evidence hierarchy,
3. keep legal and evidence sections readable rather than flashy,
4. make jurisdiction and chronology panels feel like auditable operator views.

### 4. Compare

Primary references:

1. `Openpanel`
2. `Dub`

Required change:

1. treat compare as a serious analytical workflow, not a form plus raw result dump,
2. stronger compare entry layout,
3. clearer left/right entity anchoring,
4. better lens cards,
5. more deliberate support-row treatment.

### 5. Market

Primary references:

1. `Openpanel`
2. `Umami`

Required change:

1. market should feel like a command view,
2. use more analytical filtering and fewer generic cards,
3. emphasize current overlays, chronology, and ranking surfaces separately.

### 6. Semantic

Primary references:

1. `Openpanel`
2. `Dub`

Required change:

1. semantic should be introduced as a discovery workspace,
2. query controls, provenance, and caveats should be first-class,
3. search results must feel like analytical hits, not search-engine snippets.

## Concrete Next Frontend Pass

### Phase 1: shell upgrade

Implement first:

1. dedicated workspace layout under `app/(workspace)/layout.tsx`
2. stronger global navigation
3. route-aware header/breadcrumb layer
4. removal of page-shell duplication on portfolio and later other pages

References:

1. `Dub` shell discipline
2. `Umami` navigation calm

### Phase 2: landing page reset

Implement next:

1. entry-console landing page
2. live search and route launch modules
3. reduced brochure copy

References:

1. `Dub`
2. `Umami`

### Phase 3: portfolio restructure

Implement next:

1. story-based tab reset
2. control-bar improvement
3. summary-preview-detail hierarchy
4. better compare and citation panel composition

References:

1. `Openpanel`
2. `Dub`

### Phase 4: family and market cleanup

Implement next:

1. calmer analytical framing
2. stronger chart/list fit by data type
3. reduce repetitive wrappers

References:

1. `Umami`
2. `Openpanel`

### Phase 5: semantic workspace after backend runtime

Implement only after semantic backend is ready:

1. semantic search
2. family semantic compare
3. later portfolio semantic compare

References:

1. `Openpanel` for control bars and results
2. `Dub` for workflow layout

## Explicit Non-Goals

Do not:

1. migrate V2 to Tailwind just because the references use it,
2. adopt shadcn blindly,
3. imitate Mixpanel-style purple product aesthetics,
4. turn PatentIQ into a chart zoo,
5. import BI-platform interaction patterns where an operator workspace is cleaner.

## Final Decision

The strongest external-reference blend for PatentIQ V2 is:

1. `Dub` for shell, route ownership, and enterprise structure,
2. `Openpanel` for analytical panel behavior and control-bar design,
3. `Umami` for restraint, readability, and dashboard calm.

PatentIQ should adapt that blend into its current stack rather than chasing generic admin templates.

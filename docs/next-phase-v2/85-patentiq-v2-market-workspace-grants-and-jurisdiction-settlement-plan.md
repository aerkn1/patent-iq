# PatentIQ V2 Market Workspace Grants And Jurisdiction Settlement Plan

## Purpose

Settle the market workspace expansion for grant, application, jurisdiction, and EP unitary analytics without breaking the current V2 market information architecture, backend contract assumptions, or component styling discipline.

This note is intentionally conservative.

It is not a redesign brief.

It is a settlement plan for:

1. what the current market workspace already contains under the same or nearby names,
2. what must stay unchanged,
3. where the new charts should be added,
4. how to preserve deduplication clarity,
5. how to keep the current V2 component language intact.

Read this together with:

1. [30-patentiq-v2-market-intelligence-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md)
2. [76-patentiq-v2-external-dashboard-reference-adaptation-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/76-patentiq-v2-external-dashboard-reference-adaptation-plan.md)
3. [83-patentiq-v2-heritage-placement-and-scope-visibility-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/83-patentiq-v2-heritage-placement-and-scope-visibility-plan.md)
4. [84-patentiq-v2-heritage-placement-plan-portfolio-and-market.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/84-patentiq-v2-heritage-placement-plan-portfolio-and-market.md)

## Recheck Result

The current market workspace already contains partial scope, freshness, support, and non-overlap messaging.

It does **not** contain a dedicated named scope component such as:

1. `ScopeBanner`
2. `BasisBanner`
3. `DedupBanner`
4. `MetricBasisPanel`

But it already has the raw data and lighter UI patterns needed for those concerns:

1. `workspace.scope` in the contract
2. `meta.support_level`
3. `meta.caveats`
4. `methodology`
5. `snapshot_date`
6. panel-level descriptive copy that already warns about unique-family and CPC-overlap semantics

This means we should **reuse and strengthen** the existing surfaces instead of introducing a second parallel scope-note system.

## Current Market Surfaces That Already Exist

### Existing page structure

Current market workspace structure in [market-workspace.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/market/market-workspace.tsx):

1. page section tabs:
   - `Overview`
   - `Field analysis`
2. field-analysis tabs:
   - `Competition`
   - `Technology`

These labels should remain in place unless there is a hard product reason to remove them.

### Existing market panels

The current market page already includes:

1. `Market-wide chronology`
2. `Field league table`
3. `Market filters`
4. `Selected field drilldown`
5. `Selected field summary`
6. `Citation pressure chronology`
7. `Top owner presence`
8. `Top families in selected field`
9. `Top citing owners`
10. `Top citing jurisdictions`
11. `Top CPC groups in selected field`
12. `Field footprint by jurisdiction`
13. `CPC geography within field`
14. `Global CPC importance`
15. `Methodology and caveats`

### Existing scope and caveat primitives

The current implementation already exposes:

1. `scope_type` and `snapshot_date` through `workspace.scope`
2. methodology and caveats through `workspace.methodology` and `workspace.meta.caveats`
3. release metadata through `workspace.meta.release_id`
4. support metadata through `workspace.meta.support_level`

Current examples:

1. `Market-wide chronology` already states `Unique family universe across the bounded market scope, capped through 2023 for consistency.`
2. `Field footprint by jurisdiction` already states `Unique family geography for the selected field across jurisdictions, without summing CPC overlaps.`
3. methodology links already display `scope_type` and `release_id`

### Existing styling primitives

The current page already has reusable visual blocks in [market-workspace.module.css](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/market/market-workspace.module.css):

1. `sectionBreak`
2. `summaryDrawer`
3. `controlNote`
4. `marketChronologyLead`
5. `marketCountCard`
6. `fieldAnalyticsCard`
7. `supportSurface`
8. `methodologySurface`

And the shared UI primitives already used by the market page are:

1. [Surface](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/ui/surface.tsx)
2. [InfoPill / StatusPill](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/ui/data-pill.tsx)
3. [DataTableShell](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/data-table/data-table-shell.tsx)
4. [MethodologyDisclosure](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/feedback/methodology-disclosure.tsx)

## Protection Rules

### Rule 1: keep current market section labels

Do not rename:

1. `Overview`
2. `Field analysis`
3. `Competition`
4. `Technology`

The current query-param routing and workspace rhythm are already built around them. Renaming them creates churn without improving data correctness.

### Rule 2: keep current ready-to-use panels intact

The following existing panels should remain visually and structurally unchanged unless a clear defect is found:

1. `Market-wide chronology`
2. `Field league table`
3. `Citation pressure chronology`
4. `Top owner presence`
5. `Top families in selected field`
6. `Top citing owners`
7. `Top citing jurisdictions`
8. `Top CPC groups in selected field`
9. `CPC geography within field`
10. `Global CPC importance`

### Rule 3: add new scope semantics without inventing a new component family

Do not add a standalone new visual family named:

1. `ScopeBanner`
2. `BasisBanner`
3. `DedupBanner`

Instead:

1. use `InfoPill` rows inside existing `Surface` headers,
2. use `controlNote` or `sectionBreakMeta` for freshness and basis text,
3. use `MethodologyDisclosure` for deeper caveats,
4. add small basis chips only where the counting unit changes.

### Rule 4: preserve the current market style language

New panels must:

1. use `Surface`,
2. use the same title / description / badge pattern,
3. use `DataTableShell` before inventing a custom table,
4. reuse existing market CSS classes where possible,
5. avoid introducing a new visual theme, card family, or header treatment.

## Naming Collision Audit

### Names that already exist and must not be duplicated

Do not create new panels with these names:

1. `Market-wide chronology`
2. `Field league table`
3. `Top citing jurisdictions`
4. `Field footprint by jurisdiction`
5. `CPC geography within field`
6. `Global CPC importance`
7. `Methodology and caveats`

### Names that can be safely added

Use new names that clearly distinguish unit and semantics:

1. `Leading jurisdictions by field`
2. `Applications and grants by jurisdiction`
3. `Grant mix by office`
4. `EP unitary registrations`

### Backend naming guardrail

Avoid generic `jurisdictions` payloads once grant panels are added.

Use explicit section names such as:

1. `citation_jurisdictions`
2. `field_jurisdictions`
3. `applications_grants_by_jurisdiction`
4. `grant_mix_by_office`
5. `unitary_patent_summary`

## Deduplication Settlement

The market workspace now spans multiple counting units.

Those units must remain visually separated.

### Unit 1: unique family stock

Use for:

1. `Market-wide chronology`
2. `Field league table`
3. `Selected field summary`
4. `Field footprint by jurisdiction`
5. `Leading jurisdictions by field`

UI label:

1. `Basis: unique DOCDB families`

### Unit 2: publication-stage application / grant events

Use for:

1. `Applications and grants by jurisdiction`
2. `Grant mix by office`
3. `EP unitary registrations`

Recommended default basis:

1. distinct `appln_id`

UI label:

1. `Basis: distinct application-stage / grant-stage events`

### Unit 3: citation events

Use for:

1. `Citation pressure chronology`
2. `Top citing jurisdictions`
3. `Top citing owners`

UI label:

1. `Basis: citation events`

### Unit 4: overlapping CPC slices

Use for:

1. `Top CPC groups in selected field`
2. `CPC geography within field`
3. `Global CPC importance`

UI label:

1. `Basis: overlapping CPC slices`

### Mandatory rule

Never visually place a `citation event` panel and a `unique family footprint` panel under the same title theme without a basis chip.

The current market page is already close to this line. The new grant work must not make it worse.

## Settled Layout

## 1. `Overview` stays as the market-wide surface

Do not rename or rebuild it.

Keep:

1. `Market-wide chronology`
2. `Field league table`

Add one new panel below `Field league table`:

### `Leading jurisdictions by field`

Purpose:

1. give a fast market-wide view of where each served field is strongest geographically,
2. support the new grant/jurisdiction program without disturbing existing panels.

Best representation:

1. `DataTableShell` by default
2. optional matrix view later

Default unit:

1. unique families

Columns:

1. `Field`
2. `Leading jurisdiction`
3. `Top 3 jurisdictions`
4. `Current family stock`
5. `Active family stock`

Badge row:

1. `Basis: unique DOCDB families`
2. `Safe to compare across fields`

## 2. `Field analysis` stays as the selected-field workspace

Keep the current flow:

1. `Market filters`
2. `Selected field drilldown`
3. `Selected field summary`

Do not replace these with a new hero layout.

### Existing tabs

Keep:

1. `Competition`
2. `Technology`

### New tab

Add:

1. `Jurisdictions & Grants`

This is the lowest-risk expansion because it keeps the current tabs stable and avoids reclassifying existing panels.

## Tab Settlement

### `Competition`

Keep unchanged.

Panels:

1. `Citation pressure chronology`
2. `Top owner presence`
3. `Top families in selected field`
4. `Top citing owners`
5. `Top citing jurisdictions`

Only additive change allowed:

1. a small basis chip row in panel headers where helpful

### `Technology`

Keep mostly unchanged.

Panels:

1. `Top CPC groups in selected field`
2. `CPC geography within field`
3. `Global CPC importance`

Move `Field footprint by jurisdiction` out of `Technology` and into the new tab below.

Reason:

1. it is a geography / footprint panel, not a CPC structure panel,
2. moving it improves semantic clarity without changing the component itself,
3. this keeps `Technology` as the CPC-only tab.

### `Jurisdictions & Grants`

This tab becomes the new home for geography, grant, and application views.

Panel order:

1. `Field footprint by jurisdiction`
2. `Applications and grants by jurisdiction`
3. `Grant mix by office`
4. `EP unitary registrations`

#### 1. `Field footprint by jurisdiction`

Reused from the current page.

Preserve:

1. title
2. description
3. `DataTableShell`
4. the current non-overlap wording

Only changes:

1. move it into the new tab
2. add small basis chips in the header

#### 2. `Applications and grants by jurisdiction`

Purpose:

1. show filing versus grant flow over time by office / jurisdiction,
2. separate event-flow interpretation from current family stock.

Best representation:

1. chart/table toggle

Default chart:

1. heatmap or grouped time-series bars by year and jurisdiction

Fallback if heatmap is too heavy for the first pass:

1. `DataTableShell`

Required chips:

1. `Basis: distinct appln_id events`
2. `Not directly comparable to unique family stock`

#### 3. `Grant mix by office`

Purpose:

1. provide a latest-year ranked office snapshot without forcing a full chronology read.

Best representation:

1. horizontal grouped bars
2. table fallback

Default unit:

1. distinct `appln_id`

#### 4. `EP unitary registrations`

Purpose:

1. expose the EP unitary feature separately from normal jurisdiction totals.

Best representation:

1. yearly line or small-card chronology
2. secondary member-state coverage strip

Required semantics:

1. separate `register-confirmed` from heuristic `EP C0` inference
2. do not present UP as ordinary country-level grant counts

## Style Settlement

### Reuse targets

New panels should reuse:

1. `Surface`
2. `InfoPill`
3. `StatusPill`
4. `DataTableShell`
5. `sectionToggle`
6. `detailGrid`
7. `featureSurface`
8. `detailSurface`
9. `supportSurface`

### New CSS should be minimal

If new CSS is required, it should be limited to:

1. chart-specific wrappers for grant/jurisdiction views
2. optional chip rows for basis / summation metadata

Do **not** create:

1. a new banner family,
2. a new card family,
3. a new header gradient style,
4. a second methodology-note style.

### Basis chips

When the counting unit changes, add a small chip row inside the `Surface` meta area.

Recommended chip texts:

1. `Unique families`
2. `Grant/application events`
3. `Citation events`
4. `Overlapping CPC slices`

These chips should use existing pill styles.

## Backend Contract Settlement

## Preserve the current workspace contract

Keep [MarketWorkspaceResponse](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/domain/schemas/market_intelligence.py) focused on:

1. scope
2. overview
3. filters
4. segments
5. selected field summary
6. current competition / CPC context already served

Do not keep inflating `/market-intelligence/workspace` with every new chart dataset.

## Add lazy section endpoints instead

Recommended additive endpoints:

1. `GET /api/v1/market-intelligence/segments/{segment_id}/applications-grants`
2. `GET /api/v1/market-intelligence/segments/{segment_id}/grant-mix`
3. `GET /api/v1/market-intelligence/segments/{segment_id}/unitary-patent`
4. `GET /api/v1/market-intelligence/leading-jurisdictions`

Each new section response should include:

1. `metric_basis`
2. `scope_basis`
3. `sum_safe`
4. `overlap_policy`

This keeps the deduplication semantics explicit without forcing a new top-level component contract.

## Existing copy that should be preserved

The following current copy is already directionally correct and should be retained or lightly adapted:

1. `Unique family universe across the bounded market scope`
2. `without summing CPC overlaps`
3. `latest comparable year`
4. `Methodology and caveats`

This is enough to avoid a second, redundant wording system.

## Implementation Order

### Phase 1: low-risk layout settlement

1. keep `Overview` and `Field analysis`
2. keep `Competition` and `Technology`
3. add `Jurisdictions & Grants`
4. move `Field footprint by jurisdiction` into the new tab without changing its inner implementation
5. add basis chips to panels whose units differ

### Phase 2: add new data panels

1. `Leading jurisdictions by field`
2. `Applications and grants by jurisdiction`
3. `Grant mix by office`
4. `EP unitary registrations`

### Phase 3: optional tightening

1. enrich methodology copy for grant-event versus family-stock distinctions
2. add downloadable data hooks for the new panels
3. add view toggles where a chart/table dual mode materially improves readability

## Final Settlement

The safer V2 path is:

1. preserve the current market workspace skeleton,
2. preserve the current component and CSS language,
3. preserve the current panel names where they already work,
4. add one new additive tab for geography and grants,
5. reuse existing scope and methodology surfaces instead of inventing a second scope-component family,
6. keep deduplication clarity at the panel-header level through basis chips and explicit payload semantics.

This gives PatentIQ the new grant and jurisdiction views without destabilizing the current market workspace or introducing a second design language into `frontend_v2`.

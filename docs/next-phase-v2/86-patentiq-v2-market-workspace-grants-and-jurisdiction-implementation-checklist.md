# PatentIQ V2 Market Workspace Grants And Jurisdiction Implementation Checklist

## Purpose

Convert the settled market-workspace direction into a concrete implementation checklist for:

1. `backend_v2`
2. `frontend_v2`
3. contract additions
4. panel sequencing
5. validation

This note assumes the structural settlement defined in:

1. [85-patentiq-v2-market-workspace-grants-and-jurisdiction-settlement-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/85-patentiq-v2-market-workspace-grants-and-jurisdiction-settlement-plan.md)
2. [30-patentiq-v2-market-intelligence-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md)

## Non-Negotiable Constraints

## UX and styling

1. keep `Overview` and `Field analysis`
2. keep `Competition` and `Technology`
3. add one new tab only: `Jurisdictions & Grants`
4. preserve current market panel styling and reuse:
   - `Surface`
   - `InfoPill`
   - `StatusPill`
   - `DataTableShell`
   - `MethodologyDisclosure`
5. do not introduce a new banner family or new hero treatment

## Data semantics

1. do not reuse `fully_active` as a synonym for `granted`
2. separate unique-family stock from event-flow panels
3. separate citing-side geography from protection-footprint geography
4. separate CPC-overlap panels from unique-family panels

## Contract shape

1. keep `GET /api/v1/market-intelligence/workspace` as the shell payload
2. add lazy section endpoints for new panels
3. keep new response metadata additive and optional

## Current Touch Points

### Backend files

1. [backend_v2/api/v1/market_intelligence.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/api/v1/market_intelligence.py)
2. [backend_v2/application/services/market_intelligence.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/application/services/market_intelligence.py)
3. [backend_v2/infrastructure/repositories/market_intelligence_repository.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/repositories/market_intelligence_repository.py)
4. [backend_v2/domain/schemas/market_intelligence.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/domain/schemas/market_intelligence.py)

### Frontend files

1. [frontend_v2/components/market/market-workspace.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/market/market-workspace.tsx)
2. [frontend_v2/components/market/market-workspace.module.css](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/market/market-workspace.module.css)
3. [frontend_v2/lib/api/market-v2.ts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/lib/api/market-v2.ts)
4. [frontend_v2/lib/types/market-v2.ts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/lib/types/market-v2.ts)

## Delivery Strategy

## Step 1. Preserve current market shell and move as little as possible

Goal:

1. add new functionality without disturbing already-good market surfaces

Implementation:

1. do not touch the `Overview` section flow except to append one new panel after `Field league table`
2. keep the `Competition` tab unchanged
3. keep the `Technology` tab unchanged except for moving `Field footprint by jurisdiction` into the new tab
4. add `Jurisdictions & Grants` as a third inner tab in `Field analysis`

Risk reduction:

1. the current `Competition` and `Technology` panel wiring is already stable and should not be mixed with new grant logic

## Step 2. Add small additive semantics metadata to section responses

Current issue:

1. `MarketSectionResponse` exposes `rows` and `meta`, but not explicit panel-basis semantics

Recommended additive schema extension in [market_intelligence.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/domain/schemas/market_intelligence.py):

1. add optional fields to `MarketSectionResponse`:
   - `section_key: str | None = None`
   - `metric_basis: str | None = None`
   - `scope_basis: str | None = None`
   - `sum_safe: bool | None = None`
   - `overlap_policy: str | None = None`

Why:

1. existing clients will remain compatible
2. new panels get explicit deduplication semantics
3. current panels can gradually adopt the same metadata without a breaking response rewrite

Recommended values:

1. `metric_basis`
   - `unique_docdb_families`
   - `distinct_appln_stage_events`
   - `citation_events`
   - `overlapping_cpc_slices`
2. `scope_basis`
   - `bounded_primary_field_universe`
   - `selected_field_current_slice`
   - `citing_side_geography`
   - `ep_unitary_register_plus_member_state_coverage`
3. `sum_safe`
   - `true` for unique-family rows and distinct-event rows
   - `false` for CPC-overlap panels
4. `overlap_policy`
   - short text for the UI basis chips and tooltip copy

## Backend Checklist

## A. Repository layer

File:

1. [market_intelligence_repository.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/repositories/market_intelligence_repository.py)

### A1. Add a market-wide leading-jurisdictions query

Method to add:

1. `get_leading_jurisdictions(as_of_year: int | None = None, limit_per_field: int = 5) -> list[dict[str, object]]`

Recommended source:

1. `gold_family_classification_jurisdiction_pit.parquet`

Required behavior:

1. restrict to the served 10 fields
2. use unique-family counts
3. return `family_count` and `active_family_count`
4. rank within each field

Return columns:

1. `as_of_year`
2. `wipo_field`
3. `jurisdiction_code`
4. `family_count`
5. `active_family_count`
6. `rank_within_field`

### A2. Add applications-and-grants-by-jurisdiction query

Method to add:

1. `get_segment_applications_grants(segment_id: str, year_from: int | None = None, year_to: int | None = None, jurisdiction_limit: int = 12) -> list[dict[str, object]]`

Recommended source:

1. `silver_family_member_publications.parquet`

Required behavior:

1. join to field membership so rows are field-bounded
2. count by `publn_auth`
3. group by publication year
4. filter out invalid outlier years such as `9999`
5. default counting unit: distinct `appln_id`

Return columns:

1. `wipo_field`
2. `publn_year`
3. `jurisdiction_code`
4. `application_count`
5. `grant_count`
6. `application_family_count`
7. `grant_family_count`

Recommended first-pass rule:

1. return both `*_count` and `*_family_count` only if the extra width is manageable
2. otherwise return distinct `appln_id` counts only and keep family counts for a later endpoint revision

### A3. Add grant-mix-by-office query

Method to add:

1. `get_segment_grant_mix(segment_id: str, as_of_year: int | None = None, limit: int = 12) -> list[dict[str, object]]`

Recommended source:

1. `silver_family_member_publications.parquet`

Required behavior:

1. latest-year office snapshot
2. return both application and grant counts for the selected year
3. sort by grant count descending

Return columns:

1. `wipo_field`
2. `publn_year`
3. `jurisdiction_code`
4. `application_count`
5. `grant_count`

### A4. Add EP unitary summary query

Method to add:

1. `get_segment_unitary_patent_summary(segment_id: str) -> list[dict[str, object]]`

Recommended sources:

1. `silver_ep_register_up_status.parquet`
2. `silver_up_status.parquet`
3. `silver_family_member_publications.parquet`
4. `silver_family_jurisdiction_unrolled.parquet`

Required behavior:

1. separate `register_confirmed` from heuristic `ep_c0_publication`
2. return yearly rows
3. include member-state coverage count when possible

Return columns:

1. `event_year`
2. `signal_type`
   - `register_confirmed`
   - `heuristic_ep_c0`
3. `family_count`
4. `appln_count`
5. `member_state_count_avg`

### A5. Keep current field-jurisdiction query unchanged

Do not rewrite:

1. `get_segment_field_jurisdictions`

Only frontend placement changes in the first pass.

## B. Service layer

File:

1. [market_intelligence.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/application/services/market_intelligence.py)

### B1. Add service methods for the new endpoints

Methods to add:

1. `get_leading_jurisdictions(...)`
2. `get_segment_applications_grants(...)`
3. `get_segment_grant_mix(...)`
4. `get_segment_unitary_patent_summary(...)`

### B2. Map rows into UI-ready section payloads

For each new method:

1. normalize numeric types
2. attach `section_key`
3. attach `metric_basis`
4. attach `scope_basis`
5. attach `sum_safe`
6. attach `overlap_policy`
7. attach `ResponseMeta` with relevant caveats

Recommended caveats:

1. applications/grants:
   - office-coded event flow
   - not equal to unique-family stock
2. unitary:
   - register-confirmed versus heuristic signal
   - member-state coverage is synthetic footprint, not separate national grant events
3. leading jurisdictions:
   - jurisdiction code includes office-like codes unless filtered in UI

### B3. Keep current `get_workspace` lean

Do not expand `selected_segment` with the new heavy datasets in the first pass.

Keep the current shell payload stable and lazy-load the new tab content.

## C. Router layer

File:

1. [market_intelligence.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/api/v1/market_intelligence.py)

### C1. Add new endpoints

Add:

1. `GET /market-intelligence/leading-jurisdictions`
2. `GET /market-intelligence/segments/{segment_id}/applications-grants`
3. `GET /market-intelligence/segments/{segment_id}/grant-mix`
4. `GET /market-intelligence/segments/{segment_id}/unitary-patent`

Recommended query params:

1. `as_of_year`
2. `year_from`
3. `year_to`
4. `limit`
5. `offset` where useful

### C2. Keep response model stable

Use:

1. `MarketSectionResponse`

Do not create a parallel new response envelope unless the existing shape proves insufficient.

## Frontend Checklist

## A. Types

File:

1. [market-v2.ts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/lib/types/market-v2.ts)

### A1. Extend `MarketSectionResponse` semantics in the frontend model

Add optional fields matching backend additions:

1. `section_key?: string | null`
2. `metric_basis?: string | null`
3. `scope_basis?: string | null`
4. `sum_safe?: boolean | null`
5. `overlap_policy?: string | null`

### A2. Add new row types

Add:

1. `MarketLeadingJurisdictionRow`
2. `MarketApplicationGrantRow`
3. `MarketGrantMixRow`
4. `MarketUnitaryPatentRow`

Keep them flat and table-friendly.

## B. API client

File:

1. [market-v2.ts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/lib/api/market-v2.ts)

### B1. Add fetch helpers

Add:

1. `fetchMarketLeadingJurisdictions`
2. `fetchMarketSegmentApplicationsGrants`
3. `fetchMarketSegmentGrantMix`
4. `fetchMarketSegmentUnitaryPatent`

All should:

1. use `fetchJson`
2. normalize payload rows
3. return typed structures

### B2. Keep current workspace fetch unchanged

Do not modify:

1. `fetchMarketWorkspace`

except if a new query param is needed for the active tab state in the URL layer.

## C. Market workspace component

File:

1. [market-workspace.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/market/market-workspace.tsx)

### C1. Add the new inner tab

Current inner tab type:

1. `competition`
2. `technology`

Change to:

1. `competition`
2. `technology`
3. `jurisdictions`

Label:

1. `Jurisdictions & Grants`

Do not rename the existing two tabs.

### C2. Keep current panels in place unless explicitly moved

Unchanged:

1. `Competition` tab body
2. `Technology` tab body except one moved panel

Move only:

1. `Field footprint by jurisdiction`

from `Technology` into `Jurisdictions & Grants`

Do not rewrite its component or table columns in the first pass.

### C3. Add new local state for lazy sections

Add state for:

1. `leadingJurisdictions`
2. `applicationsGrants`
3. `grantMix`
4. `unitaryPatent`
5. loading flags
6. per-section error messages

Recommended pattern:

1. mirror the existing market-history lazy fetch approach
2. fetch only when the new tab becomes active or when selected field changes

### C4. Add one new `Overview` panel

After `Field league table`, add:

1. `Leading jurisdictions by field`

Default implementation:

1. `Surface`
2. `DataTableShell`
3. `InfoPill` chips for:
   - `Unique families`
   - `Safe to compare`

### C5. Add the new `Jurisdictions & Grants` tab body

Panel order:

1. reused `Field footprint by jurisdiction`
2. `Applications and grants by jurisdiction`
3. `Grant mix by office`
4. `EP unitary registrations`

Recommended first-pass rendering:

1. `Applications and grants by jurisdiction`
   - `Surface`
   - chart/table toggle if easy
   - otherwise `DataTableShell` first
2. `Grant mix by office`
   - `Surface`
   - horizontal bar chart if low-risk
   - `DataTableShell` fallback
3. `EP unitary registrations`
   - `Surface`
   - small chronology cards or simple line chart
   - clear chip separation for signal type

### C6. Add basis chips, not new banners

For panels with changing count logic, add small chip rows in `badge` or `actions`.

Recommended chips:

1. `Unique families`
2. `Grant/application events`
3. `Citation events`
4. `Overlapping CPC slices`

Do not create a new large banner component.

### C7. Preserve existing CSS language

Reuse:

1. `detailGrid`
2. `featureSurface`
3. `detailSurface`
4. `supportSurface`
5. `sectionToggle`

Add only minimal new CSS classes for:

1. grant-panel chart wrappers
2. basis-chip rows if needed

Do not create:

1. a new card family
2. a new hero background
3. a new methodology styling pattern

## D. CSS checklist

File:

1. [market-workspace.module.css](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/components/market/market-workspace.module.css)

Allowed additions:

1. `basisChipRow`
2. `grantChartSurface`
3. `unitarySignalStrip`
4. `jurisdictionTabStack`

Disallowed additions:

1. a second `sectionBreak` variant
2. a new global banner treatment
3. a separate style system for grant panels

## Endpoint Payload Sketches

## 1. `GET /market-intelligence/leading-jurisdictions`

Response sketch:

```json
{
  "section_key": "leading_jurisdictions",
  "metric_basis": "unique_docdb_families",
  "scope_basis": "bounded_primary_field_universe",
  "sum_safe": true,
  "overlap_policy": "Safe to compare across fields because each field uses a unique family rollup basis.",
  "rows": [
    {
      "as_of_year": 2023,
      "wipo_field": "Computer technology",
      "jurisdiction_code": "CN",
      "family_count": 1484838,
      "active_family_count": 557239,
      "rank_within_field": 1
    }
  ],
  "meta": { "...": "existing section meta fields" }
}
```

## 2. `GET /market-intelligence/segments/{segment_id}/applications-grants`

Response sketch:

```json
{
  "section_key": "applications_grants_by_jurisdiction",
  "metric_basis": "distinct_appln_stage_events",
  "scope_basis": "selected_field_current_slice",
  "sum_safe": true,
  "overlap_policy": "Counts reflect publication-stage events by office and should not be read as unique-family stock.",
  "rows": [
    {
      "wipo_field": "Computer technology",
      "publn_year": 2023,
      "jurisdiction_code": "EP",
      "application_count": 91879,
      "grant_count": 40139
    }
  ],
  "meta": { "...": "existing section meta fields" }
}
```

## 3. `GET /market-intelligence/segments/{segment_id}/grant-mix`

Response sketch:

```json
{
  "section_key": "grant_mix_by_office",
  "metric_basis": "distinct_appln_stage_events",
  "scope_basis": "selected_field_current_slice",
  "sum_safe": true,
  "overlap_policy": "Latest-year office counts remain event-flow counts rather than unique-family totals.",
  "rows": [
    {
      "wipo_field": "Computer technology",
      "publn_year": 2023,
      "jurisdiction_code": "US",
      "application_count": 222404,
      "grant_count": 176440
    }
  ],
  "meta": { "...": "existing section meta fields" }
}
```

## 4. `GET /market-intelligence/segments/{segment_id}/unitary-patent`

Response sketch:

```json
{
  "section_key": "unitary_patent_summary",
  "metric_basis": "distinct_appln_stage_events",
  "scope_basis": "ep_unitary_register_plus_member_state_coverage",
  "sum_safe": false,
  "overlap_policy": "Member-state coverage rows describe synthetic UP footprint and must not be summed as ordinary national grant counts.",
  "rows": [
    {
      "event_year": 2023,
      "signal_type": "register_confirmed",
      "family_count": 2,
      "appln_count": 2,
      "member_state_count_avg": 18
    }
  ],
  "meta": { "...": "existing section meta fields" }
}
```

## Testing Checklist

## Backend

1. add repository tests for each new query
2. add service tests for section semantics metadata
3. add endpoint tests for the four new routes
4. verify no regression in current market routes

Suggested test files:

1. `backend_v2/tests/test_market_intelligence_repository.py` if created
2. `backend_v2/tests/test_market_intelligence.py`
3. route-level tests beside current market endpoint coverage

## Frontend

1. type-check new `market-v2` row types
2. verify the current `Competition` and `Technology` tabs remain unchanged
3. verify the new `Jurisdictions & Grants` tab loads lazily
4. verify `Field footprint by jurisdiction` still renders identically after moving tabs
5. verify basis chips appear only on panels whose units differ

Suggested validation:

1. `npm run build`
2. `tsc --noEmit`
3. live browser audit of:
   - `Overview`
   - `Competition`
   - `Technology`
   - `Jurisdictions & Grants`

## Execution Order

### Phase 1: backend foundations

1. extend `MarketSectionResponse`
2. implement repository methods
3. implement service methods
4. expose router endpoints
5. add tests

### Phase 2: frontend contract wiring

1. extend `market-v2.ts` types
2. add fetch helpers
3. add local state and lazy loaders
4. add the new inner tab

### Phase 3: low-risk panel wiring

1. move `Field footprint by jurisdiction`
2. add `Leading jurisdictions by field`
3. add basis chips

### Phase 4: new grant/jurisdiction panels

1. add `Applications and grants by jurisdiction`
2. add `Grant mix by office`
3. add `EP unitary registrations`

### Phase 5: verification

1. run tests
2. run type-check/build
3. run live browser pass
4. tighten copy only after the panels are reading correctly

## Final Rule

If any implementation choice forces a tradeoff between:

1. preserving the current market workspace structure and style, or
2. introducing a cleaner but substantially different new design,

choose the first option for this pass.

This expansion should feel like the current market workspace grew new evidence lanes, not like a second market page was introduced inside `frontend_v2`.

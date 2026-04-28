# PatentIQ V2 Family Workspace Current-State Audit

## Purpose

Audit whether the V2 `Family` workspace should be the next implementation path after the current portfolio work, and determine:

1. whether the data coverage is already strong enough,
2. what parts of the backend and frontend are already present,
3. what is still stubbed or missing,
4. which family sections can be implemented immediately from existing marts.

## Short Conclusion

The `Family` workspace should be the next implementation path before `Market Intelligence`.

Reason:

1. the family-level data layer is already materially rich and broad enough to support a serious page,
2. the current V2 family backend and frontend are mostly placeholders,
3. most required family sections can be built directly from already-existing Gold, Silver, ML, and serving artifacts,
4. market pages still depend more heavily on chronology caveats, overlay interpretation, and higher-order aggregation choices.

So this is not a data-readiness blocker.

It is an implementation-gap problem.

## Implementation Update

As of `2026-04-10`, the first real V2 family workspace slice has been implemented.

### Backend now serves live family sections

Implemented from the live family marts:

1. `GET /api/v1/families/{family_id}/overview`
2. `GET /api/v1/families/{family_id}/legal`
3. `GET /api/v1/families/{family_id}/fields`
4. `GET /api/v1/families/{family_id}/timeseries`
5. `GET /api/v1/families/{family_id}/members`
6. `GET /api/v1/families/{family_id}/semantic-context`
7. `GET /api/v1/families/{family_id}/forecasts`
8. `GET /api/v1/families/{family_id}/citations`
9. `GET /api/v1/families/{family_id}/classification`

Current behavior:

1. overview now joins family summary, blocking, heritage, and compare-serving context,
2. legal now returns jurisdiction legal footprint rows, historical family status rows, and dated last-event anchors where available,
3. fields now return current field contribution rows and field chronology rows,
4. members now return paginated publication evidence rows,
5. citations now return curated family citation summary and PIT-safe citation chronology rows,
6. classification now returns current classification summary and chronology rows,
7. forecasts remain explicitly coverage-gated,
8. lapse-risk remains explicit only when model rows exist for the family.

Important citation-serving caveat:

1. raw adjusted citation intermediates such as `family_adjusted_citation_score_raw` and `family_rcf_score` should not be surfaced directly in family UI,
2. the current family citation tab now exposes counts, weighting summaries, and PIT-safe chronology only.

Important legal-footprint caveat:

1. jurisdiction legal rows are currently `contribution-based`, derived from `branch_enforceability_contribution_raw`,
2. they should be presented as office contribution into family-level enforceability, not as a fake normalized standalone `0..100` jurisdiction truth score.

### Frontend now renders a real family workspace

The V2 family page at:

1. [page.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/app/(workspace)/family/[familyId]/page.tsx)

now renders a live client workspace with:

1. `Overview`
2. `Legal`
3. `Fields`
4. `Evidence`
5. `Forecast`

Current UX behavior:

1. overview shows live family summary cards and explainability metrics,
2. legal shows descriptive legal coverage, branch-state mix chips, lead-jurisdiction cards, historical status summaries, and lapse rows when model coverage exists,
3. fields shows current field footprint and classification chronology,
4. evidence shows member publications with pagination and citation context,
5. forecast shows interval rows only when the family actually has forecast coverage.

Legal-tab presentation note:

1. the lead-jurisdiction cards are still contribution-first views derived from family legal footprint rows,
2. the lapse overlay stays horizon-switched and coverage-gated; probability remains suppressed whenever the model flags display gating.

### Real-family smoke result

For real family `94821745`, current route smoke results are:

1. overview: `200`, `5` summary cards
2. legal: `200`, `1` jurisdiction legal row, `2` status-history rows, `0` lapse rows
3. fields: `200`, `1` current row, `2` chronology rows
4. citations: `200`, `1` row
5. classification: `200`, `2` chronology rows
6. members: `200`, `1` publication row
7. forecasts: `200`, `0` forecast rows

This is expected for that specific family because it is `pending_emerging` and currently has descriptive family coverage but no phase-03 or phase-04 model rows.

## What Was Audited

### Existing V2 family route surface

1. [families.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/api/v1/families.py)
2. [families.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/application/services/families.py)
3. [family_repository.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/repositories/family_repository.py)
4. [page.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/app/(workspace)/family/[familyId]/page.tsx)

### Current contract / notes

1. [32-patentiq-v2-family-and-publication-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md)
2. [23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md)
3. [march-2026-family-legal-analytics-master-index.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/march-2026-family-legal-analytics-master-index.md)
4. [57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md)

### Data artifacts checked

1. `gold_family_summary.parquet`
2. `gold_family_blocking_power.parquet`
3. `gold_family_compare_pit.parquet`
4. `gold_family_classification_mix_pit.parquet`
5. `gold_family_blocking_power_timeseries.parquet`
6. `gold_family_field_contributions.parquet`
7. `gold_family_field_contributions_timeseries.parquet`
8. `gold_family_heritage_summary.parquet`
9. `silver_family_member_publications.parquet`
10. `silver_family_citation_metrics.parquet`
11. `silver_family_feature_snapshot_pit.parquet`
12. `silver_family_classification_pit_dense.parquet`
13. `ml_prediction_family_future_citations.parquet`
14. `ml_prediction_family_jurisdiction_lapse_risk.parquet`
15. `core_serving.duckdb`

## Audit Findings

## 1. Current V2 family backend is mostly a stub

The route group exists, but it is not serving a real family page yet.

### What exists

Current backend endpoints:

1. `GET /api/v1/families/{family_id}/overview`
2. `GET /api/v1/families/{family_id}/legal`
3. `GET /api/v1/families/{family_id}/fields`
4. `GET /api/v1/families/{family_id}/timeseries`
5. `GET /api/v1/families/{family_id}/members`
6. `GET /api/v1/families/{family_id}/semantic-context`
7. `GET /api/v1/families/{family_id}/forecasts`

### What they currently do

Current implementation behavior in [families.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/application/services/families.py):

1. `overview_metrics` is always empty,
2. every section endpoint returns `rows=[]`,
3. only a small caveat is added to `fields`.

Observed service behavior on real family ids:

1. `52626827`: overview `0`, legal `0`, fields `0`, forecasts `0`
2. `76320812`: overview `0`, legal `0`, fields `0`, forecasts `0`
3. `47225421`: overview `0`, legal `0`, fields `0`, forecasts `0`

So the family API surface is present but not implemented.

## 2. Current V2 family frontend is also mostly a stub

The route exists, but it is only a placeholder shell.

Current page:

1. [page.tsx](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/app/(workspace)/family/[familyId]/page.tsx)

Current behavior:

1. shows title `Family {id}`
2. shows a short placeholder description
3. does not fetch family overview
4. does not render any family sections

There are currently no dedicated V2 family UI components under `frontend_v2/components`.

## 3. Data readiness for family is already strong

The family data layer is not the problem.

Observed artifact row counts:

1. `gold_family_summary.parquet`: `17,633,618`
2. `gold_family_blocking_power.parquet`: `17,633,618`
3. `gold_family_compare_pit.parquet`: `164,988,135`
4. `gold_family_classification_mix_pit.parquet`: `164,988,135`
5. `gold_family_blocking_power_timeseries.parquet`: `152,145,173`
6. `gold_family_field_contributions.parquet`: `172,223,907`
7. `gold_family_field_contributions_timeseries.parquet`: `172,223,907`
8. `gold_family_heritage_summary.parquet`: `21,353,101`
9. `silver_family_member_publications.parquet`: `42,692,835`
10. `silver_family_citation_metrics.parquet`: `21,353,101`
11. `silver_family_feature_snapshot_pit.parquet`: `17,633,618`
12. `silver_family_classification_pit_dense.parquet`: `164,988,135`
13. `ml_prediction_family_future_citations.parquet`: `23,545,912`
14. `ml_prediction_family_jurisdiction_lapse_risk.parquet`: `26,394,286`

This is enough to build a serious family page without waiting for new ETL branches.

## 4. Core serving already contains a useful family serving base

Observed family tables inside `core_serving.duckdb`:

1. `family_summary`
2. `family_blocking_power`
3. `family_heritage_summary`
4. `family_compare_current_serving`
5. `family_owner_bridge`

Observed current-serving row counts:

1. `family_summary`: `17,633,618`
2. `family_blocking_power`: `17,633,618`
3. `family_heritage_summary`: `21,353,101`
4. `family_compare_current_serving`: `17,633,618`
5. `family_owner_bridge`: `27,840,126`

This matters because:

1. identity/header/summary-card content can be served from the current serving snapshot fast,
2. compare-style percentiles and bands can be reused from `family_compare_current_serving`,
3. only the heavier chronology/classification/member/prediction sections need parquet fallback or dedicated query logic.

## 5. The family contract is much richer than the current implementation

The target family contract expects at least:

1. identity header
2. summary rail
3. blocking and explainability panels
4. legal and jurisdiction coverage
5. field and market footprint
6. trajectory / timeseries
7. classification footprint
8. evidence / publication members
9. forecast and semantic links

The current API set does not even align fully to the documented backend contract.

### Missing endpoint groups versus the baseline contract

The baseline family contract in [23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md) expects:

1. `/blocking-power`
2. `/jurisdictions`
3. `/citations`
4. `/forecasts`
5. `/semantic-context`

Current family API is missing:

1. `/blocking-power`
2. `/jurisdictions`
3. `/citations`

So there is both:

1. a wiring gap,
2. an endpoint-shape gap.

## 6. Family descriptive sections are implementable now

Based on current column shapes, these sections can be implemented immediately.

### Identity / header

From `gold_family_summary.parquet`:

1. `docdb_family_id`
2. `owner_name_harmonized`
3. `owner_name_display`
4. `primary_wipo_field`
5. `family_composite_status`
6. `family_priority_year`
7. `family_size_docdb`
8. `family_distinct_owner_count`
9. `is_main_window_family`
10. `is_heritage_backfill_family`

### Summary rail / blocking

From `gold_family_blocking_power.parquet` and current serving:

1. `family_ui_blocking_power_score`
2. `family_overall_legal_enforceability_score`
3. `family_market_threat_score_raw`
4. `family_adjusted_citation_score_raw`
5. `family_raw_absolute_blocking_power`

### Legal / coverage

From `gold_family_summary.parquet` and `gold_family_compare_pit.parquet`:

1. `active_jurisdiction_count`
2. `active_grant_branch_count`
3. `lapsed_jurisdiction_count`
4. `opposed_branch_count`
5. `family_active_jurisdiction_share_asof`
6. `family_coverage_stability_score_asof`
7. `family_jurisdiction_count_asof`

### Field footprint

From `gold_family_field_contributions.parquet`:

1. `wipo_industry_code`
2. `base_fraction`
3. `enforceability_contribution_score`
4. `heritage_contribution_score`
5. `active_market_weight`
6. `is_active_on_snapshot`

### Trajectory

From `gold_family_blocking_power_timeseries.parquet` and `gold_family_field_contributions_timeseries.parquet`:

1. blocking power over time
2. field contribution evolution over time

### Classification footprint

From `gold_family_classification_mix_pit.parquet` and `silver_family_classification_pit_dense.parquet`:

1. current WIPO and CPC mix
2. breadth and concentration metrics
3. `first_seen_classification_visibility` chronology path

### Evidence

From `silver_family_member_publications.parquet`:

1. family member publication list
2. grant/application/modifier stage flags
3. publication ids and office metadata for publication drilldown

### Citation diagnostics

From `silver_family_citation_metrics.parquet` and `silver_family_feature_snapshot_pit.parquet`:

1. forward citation totals
2. weighted citation diagnostics
3. science grounding
4. diversity and attacker-density proxies

## 7. Prediction layers are available, but not universal

Prediction coverage is meaningful but not full-universe.

Observed distinct-family overlap:

1. families in `gold_family_summary`: `17,633,618`
2. families with family-future-citation predictions: `11,772,956`
3. families with family-jurisdiction lapse-risk predictions: `11,270,130`

Approximate overlap against current family summary:

1. forecast coverage: about `66.8%`
2. lapse coverage: about `63.9%`

This is enough for a family page, but it means:

1. forecast and lapse sections must be coverage-gated,
2. the page should not assume those sections exist for every family,
3. support badges and caveats should be first-class, not an afterthought.

### Important status-level pattern

Observed coarse status breakdown:

1. `fully_active` with both forecast and lapse: `7,425,060`
2. `pending_emerging` with forecast but no lapse: `3,401,259`
3. `fully_active` with lapse but no forecast: `2,958,577`
4. `pending_emerging` with neither: `2,899,197`

This suggests:

1. family forecast and lapse should not be merged into one unconditional hero panel,
2. `pending_emerging` families especially need careful coverage messaging,
3. the family page should render prediction cards conditionally, with explicit support state.

## 8. Sample-family coverage is internally consistent for descriptive marts

Example families audited:

1. `94821745`
2. `94613006`
3. `89761229`
4. `89557704`

Observed for these real families:

1. `summary`: present
2. `blocking`: present
3. `compare_pit`: present
4. `classification_mix`: present
5. `field_contrib`: present
6. `member_pubs`: present
7. `citation_metrics`: present
8. `feature_pit`: present

This is exactly the pattern needed for the first solid family workspace.

## 9. Family compare already provides a reusable logic fragment

Current compare code already uses family-serving context via:

1. [family_repository.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/repositories/family_repository.py)
2. [compare.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/application/services/compare.py)

So the family page does not need to invent:

1. identity resolution,
2. some peer-banding semantics,
3. compare-context enrichment,
4. serving-vs-parquet fallback strategy.

The family page should reuse that logic rather than duplicate it.

## Main Gaps

## Backend gaps

1. family endpoints are stubbed
2. family API surface is incomplete relative to the documented contract
3. no real page-shaped family overview payload exists yet
4. no current section payloads exist for legal, fields, timeseries, members, citations, or forecasts

## Frontend gaps

1. family route is placeholder-only
2. no family API client exists in `frontend_v2`
3. no family components exist
4. no tabbed family workspace exists

## Serving gaps

1. current serving includes family summary, blocking, heritage, and compare
2. current serving does **not** yet include the deeper family chronology / classification / prediction marts
3. those deeper sections will need either parquet-backed repository reads or expanded serving packaging in a later pass

## Recommendation

Proceed with `Family` as the next implementation workspace.

Recommended execution order:

1. build a real `family overview` contract from current serving plus compare context
2. add `family blocking-power`, `family legal/jurisdictions`, and `family citations` endpoints
3. add `family fields`, `family timeseries`, and `family members` sections from existing raw marts
4. add prediction sections as conditional, support-badged panels
5. only after family is solid, move to `Market Intelligence`

## Recommended First Family Workspace Scope

The first useful family page should include:

1. `FamilyIdentityHeader`
2. `FamilySummaryRail`
3. `Blocking + explainability`
4. `Legal coverage + lapse strip`
5. `Field footprint`
6. `Trajectory`
7. `Classification footprint`
8. `Evidence / member publications`

The first version does **not** need to block on:

1. full semantic-context implementation
2. publication page completion
3. perfect prediction coverage

## Final Assessment

Family is the cleaner and higher-confidence next path than market.

Not because market is unimportant.

Because family already has:

1. strong raw and derived data coverage,
2. a clear page contract,
3. reusable compare/service logic,
4. direct traceability into evidence,
5. fewer aggregation ambiguities than market.

The V2 family layer is ready to build.

What is missing is the page-shaped backend and frontend implementation, not the underlying data foundation.

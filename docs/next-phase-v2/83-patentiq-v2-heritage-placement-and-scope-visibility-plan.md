# PatentIQ V2 Heritage Placement And Scope Visibility Plan

## Current State

The heritage layer is present in the data, but only partly visible in the current product.

Observed in the current environment:

1. `gold_family_summary.parquet`
   - current first-class family universe
   - year coverage: `2007-2025`
   - no `heritage_backfill` rows present in this mart

2. `gold_family_heritage_summary.parquet`
   - separate heritage-support mart
   - year coverage: `1956-2025`
   - total rows: `21,353,101`
   - `1996-2006` rows: `3,632,786`
   - all `1996-2006` rows are `is_heritage_backfill_family = true`

3. overlap between the two marts
   - heritage rows also present in `gold_family_summary`: `17,633,618`
   - heritage-only rows not present in `gold_family_summary`: `3,719,483`
   - `1996-2006` rows present in `gold_family_summary`: `0`

4. `gold_portfolio_heritage_summary.parquet`
   - exists and is populated
   - owners with at least one heritage-backfill family: `1,138,258`

Conclusion:

1. the heritage backfill is not missing
2. it is not primarily a data-quality issue
3. it is a product-boundary issue
4. heritage-only families are not in the current first-class family universe, so the app uses the old backfill mostly as support for heritage metrics rather than as default navigable family objects

## Policy Fit

This aligns with the two-horizon policy already defined in:

1. [29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md)
2. [32-patentiq-v2-family-and-publication-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md)
3. [33-patentiq-v2-portfolio-and-forecast-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md)

That policy says:

1. `main_window` families are the current operating universe
2. `heritage_backfill` families are historical support scope
3. current-state views must not silently collapse those two scopes into one

## Product Placement Decision

### 1. Family View

Best placement:

1. keep `Heritage` in the summary rail as a secondary score
2. do not use heritage to define whether the family is first-class current-state
3. place richer heritage interpretation in the `Evidence` tab, not the `Legal` tab

Why:

1. heritage is historical citation memory, not current legal force
2. many families legitimately have thin or zero heritage
3. heritage-only backfill families should not silently behave like normal current-state family entities

Recommended family UX:

1. summary card label:
   - `Heritage`
2. supporting status:
   - `Not yet established`
   - `Thin heritage`
   - `Established heritage`
   - `Foundational heritage`
3. details shown in `Evidence`:
   - heritage score
   - raw family citation count
   - out-of-bounds citation share
   - scope flags:
     - `main_window`
     - `heritage_backfill`

### 2. Portfolio View

Best placement:

1. show one compressed heritage card in `Executive`
2. put the real drilldown in `Citations` or `Families`
3. never dump the full heritage-only population by default for large owners

Recommended executive card:

1. label:
   - `Heritage Depth`
2. value:
   - peer-relative heritage band or percentile if available
3. support line:
   - `main-window families: X`
   - `heritage-backfill families: Y`

Recommended portfolio drilldowns:

1. `Top heritage families`
2. `Heritage-supported family count`
3. optional age-bucket split:
   - `1996-2006`
   - `2007-2014`
   - `2015+`

Why:

1. portfolio-level heritage is useful, but very size-biased
2. large additive heritage mass needs denominator context
3. showing the support mix makes the metric interpretable

### 3. Compare View

Best placement:

1. keep heritage as one explicit compare lens
2. position it as `depth / lineage / citation memory`
3. do not merge it into legal durability or blocking posture

Why:

1. compare is exactly where heritage belongs conceptually
2. it provides historical influence context without pretending to be present legal force

### 4. Search And Navigation

Best placement:

1. do not include heritage-only families in default family search
2. do not expose them as current-state family pages by default
3. if needed later, add a separate retrieval mode

Possible future mode:

1. `Include heritage-only families`
2. or a dedicated `Historical heritage` workspace

Why:

1. the current family workspace contract assumes a current-state family object
2. heritage-only families would otherwise look like broken or incomplete current objects

## Recommended States

### Family-Level Heritage States

Use:

1. `Not yet established`
   - no meaningful heritage support in current heritage mart
2. `Thin heritage`
3. `Established heritage`
4. `Foundational heritage`

These should map to the heritage score or heritage band, not to legal status.

### Portfolio-Level Heritage Support States

Use:

1. `Thin coverage`
   - very few heritage-supported families
2. `Mixed coverage`
3. `Deep historical base`

This state should depend on:

1. `main_window_family_count`
2. `heritage_backfill_family_count`
3. `portfolio_total_heritage_score`

## What Should Change In V2

### Family Page

1. keep the current heritage card
2. add an explicit scope line in the overview:
   - `Current scope: main window`
   - `Heritage support: yes/no`
3. add an evidence panel:
   - `Heritage support`
   - `Raw family citation count`
   - `Out-of-bounds citation share`

### Portfolio Page

1. surface `heritage_backfill_family_count`
2. surface `main_window_family_count`
3. add a heritage support note to the executive heritage card
4. add a `Top heritage families` ranked panel

### Compare

1. keep `Citation Heritage` as a separate lens
2. make sure the compare card note clearly states that heritage can include historical backfill support

## Rollout Order

### Phase 1: Visibility Fix

Cheap and high-value.

1. family:
   - show scope/support wording around heritage
2. portfolio:
   - add `heritage_backfill_family_count`
   - add `main_window_family_count`
   - clarify the heritage card tooltip

### Phase 2: Drilldown

Moderate.

1. portfolio:
   - add `Top heritage families`
   - add age-bucket split
2. family:
   - add heritage support panel in `Evidence`

### Phase 3: Separate Historical Mode

Only if product needs it.

1. heritage-only family search mode
2. historical heritage workspace
3. explicit navigation guardrails so users know they are outside the current operating window

## Acceptance Criteria

1. users can tell whether a heritage metric includes historical backfill support
2. users can distinguish `main_window` families from `heritage_backfill` support
3. current family search remains current-state focused
4. heritage-only families do not silently appear as normal family entities
5. large portfolio heritage cards show denominator context, not just additive mass

## Final Recommendation

The best placement for heritage is:

1. `family`: secondary summary card plus evidence drilldown
2. `portfolio`: executive summary card plus ranked drilldown
3. `compare`: explicit separate lens
4. `search/navigation`: separate mode later, not default now

That gives heritage visible analytical value without confusing it with the current-state operating universe.

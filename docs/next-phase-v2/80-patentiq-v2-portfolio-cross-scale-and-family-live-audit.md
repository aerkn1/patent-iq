# PatentIQ V2 Portfolio Cross-Scale And Family Live Audit

Date: 2026-04-12

## Scope

This pass re-checked the live `frontend_v2` workspaces after the portfolio shell and component-enrichment changes.

Audited routes:

- medium portfolio: `ASELSAN_ELEKTRONIK_SANAYI_VE_TICARET_ANONIM_SIRKETI`
- smaller portfolio: `UNIVERSITY_OF_KENTUCKY`
- family drill-through: `66631682`

## Findings

### 1. Portfolio workspace now holds across medium and smaller owners

The portfolio route rendered successfully for both audited owners across:

- `Executive`
- `Families`
- `Technology`
- `Citations`
- `Forecast`

The enriched portfolio components no longer degrade into false-empty states after the earlier citation loading repair. The `UNIVERSITY_OF_KENTUCKY` citation lane did require a longer settle window than the medium owner, but it eventually rendered:

- forward clean mass
- distinct citing families
- lead cited family
- citation summary baseline
- pressure footprint filters

### 2. Scope wording was still misleading on smaller owners

`UNIVERSITY_OF_KENTUCKY` exposed a legitimate interpretation problem:

- analytics scope: `68`
- primary-owner scope: `80`

This is possible because the analytics mart is a bounded slice while the primary-owner bridge is broader, but the prior UI wording made it read like a contradiction.

Fix applied:

- portfolio hero signal copy now explicitly calls analytics scope a bounded mart
- primary-owner scope now explains when families sit outside the bounded analytics mart
- identity / summary notes now explain that rankings and status mix follow primary-owner scope while semantic and grant coverage follow the analytics slice

### 3. Family workspace covers the expected live surfaces

The audited family route `66631682` showed the expected current serving contract in the UI:

- current legal state
- jurisdiction footprint cards
- branch-state mix
- legal history summary
- dated last-event anchors
- current field / classification footprint
- curated citation summary
- citation chronology
- member publication table
- support-aware forecast and lapse rows

This means the family workspace is currently aligned with the intended V2 evidence-first drill-through shape.

### 4. Family percentile rendering had a formatting bug

The family overview showed ordinal text such as `1th percentile`.

Fix applied:

- introduced a shared ordinal formatter
- family workspace now renders `1st`, `2nd`, `3rd`, etc.
- portfolio percentile labels now use the same formatter to avoid the same defect elsewhere

### 5. Family trajectory was under-served by the Evidence tab

The prior `Observed family trajectory` table was reading directly from the PIT feature-snapshot rows. For some families, that materially under-represented the historical story.

Concrete example:

- family `44559919`
- feature anchors: `1` row, year `2012`
- blocking-history mart: `16` rows, years `2011-2026`
- field-history mart: `32` rows across `16` years

Fix applied:

- Evidence tab now renders a dedicated `Blocking trajectory` panel from `gold_family_blocking_power_timeseries`
- Evidence tab now renders a dedicated `Field trajectory` panel from `gold_family_field_contributions_timeseries`
- the old PIT table is kept only as `Observed feature anchors`
- Evidence caveats now include timeseries caveats such as sparse anchor warnings

Result:

- the family page now separates `trajectory history` from `observed PIT anchors`
- sparse PIT coverage no longer collapses the visible historical story into a single-row table

## Files Changed

- `frontend_v2/components/portfolio/portfolio-format.ts`
- `frontend_v2/components/portfolio/portfolio-header.tsx`
- `frontend_v2/components/portfolio/portfolio-summary-cards.tsx`
- `frontend_v2/components/family/family-workspace.tsx`
- `frontend_v2/components/family/family-workspace.module.css`
- `backend_v2/application/services/families.py`
- `backend_v2/tests/test_family_service.py`

## Validation

- ESLint passed on touched files
- `tsc --noEmit` passed
- `pytest backend_v2/tests/test_family_service.py -q` passed
- live browser re-check confirmed:
  - bounded-scope note now appears on `UNIVERSITY_OF_KENTUCKY`
  - bad ordinal strings such as `1th percentile` are gone from family `66631682`

Trajectory contract re-check confirmed on family `44559919`:

- `feature_anchor_points = 1`
- `blocking_history_points = 16`
- `field_history_rows = 32`
- `first_trajectory_year = 2011`
- `latest_trajectory_year = 2026`

## Remaining Gap

The family legal tab now exposes:

- relative legal strength within the family footprint
- legal contribution
- family share
- coefficient mode
- market multiplier
- last event date / type

It still does **not** expose a universal cross-family or cross-market jurisdiction truth score. The current product surface is now better for jurisdiction-by-jurisdiction legal reading, but it remains family-relative and contribution-based by design.

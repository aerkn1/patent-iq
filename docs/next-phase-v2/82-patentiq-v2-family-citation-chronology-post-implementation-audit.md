# PatentIQ V2 Family Citation Chronology Post-Implementation Audit

Date: 2026-04-12

## Purpose

Audit the new standalone family citation chronology after implementation and determine:

1. what is now materially correct,
2. what is still semantically weak,
3. which remaining gaps can be fixed cheaply without rebuilding existing Gold marts.

This pass is audit-only.

No Gold parquet was rebuilt during this audit.

## Short Conclusion

The standalone chronology fix worked.

Family citation chronology is now materially more correct than the old PIT-anchored version because it is derived from the family-collapsed citation event ledger.

However, the current row model is still not final.

The remaining issues are mostly:

1. sparse year ladders,
2. one misleading flag,
3. one empty completeness field,
4. support labeling that is too coarse for UI interpretation.

These are mostly serving and presentation issues, not raw citation-absence issues.

The cheapest next improvements do **not** require rebuilding the existing Gold suite.

## What Is Now Correct

### 1. Family-member citation aggregation is working

The new chronology correctly aggregates citations across family members rather than collapsing onto a single publication.

Example: family `44559919`

Current chronology output:

1. `16` chronology rows
2. span `2010..2026`
3. latest forward clean count `116`
4. latest distinct citing families `86`
5. latest distinct citing owners `40`
6. latest forward citation date `2024-05-14`

Underlying clean event ledger for the same family:

1. clean forward citation events `116`
2. distinct citing families `86`
3. distinct citing owners `41`
4. event span `2012-12-13 .. 2024-05-14`

So the chronology now reflects real family-level event history rather than sparse PIT anchor coverage.

### 2. Rich families, medium families, and sparse families all now produce usable chronology

Spot checks:

1. family `43381800`
   - years `2009..2026`
   - latest forward clean `486`
   - latest citing families `406`
2. family `44559919`
   - years `2010..2026`
   - latest forward clean `116`
   - latest citing families `86`
3. family `40939319`
   - sparse-but-usable chronology with `16` rows
   - latest forward clean `30`
4. family `37832163`
   - low-signal chronology still present
   - latest forward clean `5`
5. family `66631682`
   - very light evidence family
   - latest forward clean `1`

So the family page no longer depends on PIT sparsity to decide whether chronology exists.

### 3. Member-level drilldown is feasible from current data

The current event ledger plus `silver_family_member_publications.parquet` is sufficient to recover which family members are actually receiving citations.

Example: family `44559919`

Top cited member publications:

1. `US2011222523A1`: `85` citation events, `67` citing families
2. `CN102318237A`: `10` citation events, `10` citing families
3. `WO2011110108A1`: `10` citation events, `9` citing families

Office-level split:

1. `US`: `92` citation events across `4` cited publications
2. `CN`: `10`
3. `WO`: `10`
4. `JP`: `4`

So richer family Evidence panels such as `top cited family members` or `citation office distribution` are feasible without a major ETL rewrite.

## What Is Still Weak

### 1. The year ladder is sparse, not dense

The chronology mart only emits:

1. family priority year,
2. citation event years,
3. current snapshot year.

It does **not** emit a dense year ladder across the full span.

Observed distribution:

1. families with chronology rows: `8,367,531`
2. families with missing years inside the first-to-last span: `8,268,579`
3. gap rate: `98.82%`
4. median missing years: `7`
5. p90 missing years: `14`
6. only `98,952` families have no internal year gaps

This is not a raw-data bug.

It is a modeling choice.

For tables it is acceptable.

For line charts it is semantically weaker because the chart visually implies a smoother annual replay than the mart really stores.

### 2. `is_observed_as_of_snapshot` is now misleading

In the new chronology mart:

1. every row currently has `is_observed_as_of_snapshot = true`
2. this is no longer a real PIT observation flag
3. most rows are event-year or anchor-year rows, not true feature-snapshot observations

Observed global counts:

1. `true`: `30,759,429`
2. `false`: `0`

So this field should not be shown as if it distinguishes observed from synthetic chronology rows.

### 3. `data_completeness_pct_asof` is empty everywhere

Observed global counts:

1. non-null `data_completeness_pct_asof`: `0`

So this field should not currently be treated as a real data-quality signal in the family chronology UI.

### 4. `chronology_support_level` is too coarse

Current distribution:

1. `high`: `24,303,918` rows
2. `limited`: `6,455,511` rows

And:

1. `17,862,039` rows have `chronology_support_level = high` while `forward_citation_event_count_year = 0`
2. that is `73.49%` of all `high` rows

This does **not** mean the field is mathematically wrong.

It means the label is acting more like `family has some cumulative citation support by this year` rather than `this row is strongly observed this year`.

That is defensible internally, but too coarse for user-facing interpretation if not explained.

## What This Means For The Family Page

### Good enough now

The family Evidence lane can now honestly show:

1. family-level citation chronology,
2. cumulative forward citation growth,
3. distinct citing-family growth,
4. backward citation accumulation,
5. early-window closure state,
6. member publication links.

### Not honest yet

The family Evidence lane should **not** yet pretend that:

1. chronology rows are dense annual observations,
2. `Observed snapshot` means something meaningful for this mart,
3. completeness is quantified,
4. support labels are granular enough to distinguish thin from rich annual evidence.

## What Is Feasible Without Rebuilding Gold

### Cheap serving/UI fixes

These are inexpensive and do not require rebuilding existing Gold parquets.

1. Remove or hide `is_observed_as_of_snapshot` from the family chronology UI.
2. Remove or hide `data_completeness_pct_asof` from chronology surfaces until it is populated honestly.
3. Densify chronology **in the family service only** for charting.
   - fill missing years between min and max year,
   - carry cumulative counts forward,
   - set yearly event count to `0`,
   - tag the row as `filled_year`.
4. Replace current support presentation with a more honest pair of concepts:
   - `historical support`
   - `event activity this year`

This is the cheapest path because the family endpoint is per-family, so service-level densification is cheap.

### Cheap enrichment panels

These are also feasible without rebuilding the existing Gold family suite.

1. `Top cited member publications`
   - join `cited_pat_publn_id` from the citation ledger to `silver_family_member_publications`
2. `Citation distribution by office`
   - same join, grouped by `publn_auth`
3. `Top citing owners for this family`
   - group `citing_assignee_name` from the event ledger

These are good Evidence-lane enrichments because they improve defensibility without inventing new strategic metrics.

## What Would Require A New Build Or Wider Refactor

### 1. Dense chronology mart

If the goal is a truly dense yearly chronology parquet rather than service-level filling, that would require a new builder revision and a new output contract.

That is not necessary for the first improved family Evidence surface.

### 2. Better support/completeness modeling

If we want real support tiers such as:

1. `strong`
2. `moderate`
3. `limited`
4. `anchor_only`

or an honest completeness percentage, then the chronology mart needs richer derivation logic.

That is a moderate ETL refinement, not just UI work.

## Recommended Next Steps

### First pass

1. keep the current standalone chronology mart,
2. hide the misleading `Observed snapshot` and null completeness fields,
3. densify years in the family service for chart rendering only,
4. keep the raw ledger table sparse and auditable.

### Second pass

Add two Evidence enrichments from current data:

1. `Top cited family members`
2. `Top citing owners`

These are the highest-value additions because they make the family page more intelligible without touching strategic metric derivation.

### Later

Only after that, decide whether the chronology mart itself should be revised to:

1. emit dense yearly rows,
2. replace `is_observed_as_of_snapshot` with a truthful row-kind field,
3. compute a more honest support-level taxonomy.

## Final Judgment

The standalone chronology fix succeeded.

The remaining family citation chronology problems are now mostly:

1. row semantics,
2. support semantics,
3. charting behavior,
4. optional evidence enrichments.

They are no longer primarily a missing-citation-data problem.

That is the right place to be.

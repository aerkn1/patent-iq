# PatentIQ V2 Family Citation Chronology Standalone Audit

Date: 2026-04-12

## Purpose

Audit what is required to obtain a correct family citation chronology in V2, and determine whether the fix can be executed as a standalone Gold build without rebuilding the existing Gold mart suite.

This pass is audit-only.

No Gold parquet was rebuilt during this audit.

## Short Conclusion

The current family citation chronology is under-served because it is derived from the wrong source.

Current state:

1. family chronology in the backend is read from PIT anchors in [family_repository.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/repositories/family_repository.py)
2. the current Gold family citation timeseries builder is also PIT-anchored in [build_gold.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py)
3. sparse PIT coverage can collapse a family with many citation events into a one-row chronology

The correct fix is:

1. build a new family citation chronology mart directly from the citation event ledger
2. expose it through a dedicated standalone Gold stage
3. migrate family UI/backend readers to that new chronology mart
4. leave the existing PIT citation-timeseries mart in place until downstream portfolio readers are deliberately migrated

So yes, this can and should be a standalone run.

It should not rebuild the existing Gold suite.

## Current Problem

### Backend family chronology is PIT-anchored

Current chronology query in [family_repository.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/repositories/family_repository.py):

1. anchors off `silver_family_feature_snapshot_pit.parquet`
2. uses those anchor dates to count citation events up to each PIT row
3. therefore only produces chronology rows where PIT anchors exist

This is why families with thin PIT anchor coverage still show sparse chronology even when the citation event ledger is rich.

### Existing Gold family citation timeseries is also PIT-anchored

Current Gold section in [build_gold.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py):

1. section key: `family_citation_ts`
2. output: `gold_family_citation_timeseries_pit.parquet`
3. source: `family_pit`
4. current stage exposure: `build_gold_family_metrics()`

This means the existing Gold citation timeseries is not a true event-derived chronology mart either.

## Concrete Evidence

### Family `44559919`

Observed current family service behavior:

1. citation chronology rows: `1`
2. observed feature-anchor rows: `1`
3. both show only year `2012`

But the underlying historical sources show:

1. `silver_enriched_citation_network`
   - `116` forward citation events
   - `86` distinct citing families
   - event years `2012..2024`
2. `gold_family_blocking_power_timeseries`
   - `16` rows
   - years `2011..2026`
3. `gold_family_field_contributions_timeseries`
   - `32` rows
   - `16` years

So the chronology problem is not raw citation-event absence.

It is chronology derivation anchored to sparse PIT rows.

## Existing Builder Readiness

The codebase is already close to supporting a standalone chronology build.

### What is already in place

1. [build_gold.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py) already has section-level Gold building through `_build_gold_selected(...)`
2. `family_citation_ts` is already a separate Gold section key
3. the stage runner in [run.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/run.py) already exposes narrow Gold stage functions
4. the ETL CLI in [run_stage.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/scripts/run_stage.py) already supports running a single named Gold stage

### What is not yet in place

1. there is no dedicated `gold-family-citation-chronology` stage today
2. the only exposed stage that builds the current family citation timeseries is `gold-family-metrics`
3. `gold-family-metrics` also rebuilds:
   - blocking
   - heritage
   - attacker
   - family citation summary

So current stage exposure is not standalone enough for the family chronology use case.

## Dependency Risk

This is the main audit finding.

The existing `gold_family_citation_timeseries_pit.parquet` is used outside the family page.

Observed consumers:

1. [portfolio_repository.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/repositories/portfolio_repository.py)
   - `self.family_citation_timeseries_path = gold_family_citation_timeseries_pit.parquet`
2. [build_gold.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py)
   - portfolio citation summary aggregation reads `out_family_citation_timeseries`
   - portfolio cited-family leaderboard also reads latest citation PIT values from it

This means an in-place semantic rewrite of `gold_family_citation_timeseries_pit.parquet` is possible, but it is not the safest first move.

It would change downstream portfolio behavior at the same time.

## Recommended Fix

### 1. Add a new standalone Gold chronology mart

Recommended new output:

1. `gold_family_citation_chronology.parquet`

Recommended grain:

1. `docdb_family_id x as_of_year`

Recommended source:

1. `silver_enriched_citation_network.parquet`
2. family summary metadata for priority year and scope guards from `gold_family_summary.parquet`
3. optional family current metadata only where needed for labels, not for chronology truth

### 2. Derive chronology directly from event history

Recommended columns:

1. `docdb_family_id`
2. `as_of_year`
3. `as_of_date`
4. `forward_citation_event_count_year`
5. `forward_citation_event_count_asof`
6. `forward_clean_citation_event_count_asof`
7. `forward_unique_citing_family_count_asof`
8. `forward_unique_citing_owner_count_asof`
9. `forward_citations_weighted_asof`
10. `backward_citation_event_count_year`
11. `backward_citation_event_count_asof`
12. `backward_clean_citation_event_count_asof`
13. `backward_distinct_cited_family_count_asof`
14. `first_forward_citation_date_asof`
15. `latest_forward_citation_date_asof`
16. `window_5y_closed`
17. `window_7y_closed`
18. `forward_clean_5y_asof`
19. `forward_clean_7y_asof`
20. `historical_citation_safe`
21. `chronology_support_level`
22. `method_version`

### 3. Keep the old PIT mart during migration

Do not replace `gold_family_citation_timeseries_pit.parquet` immediately.

Reason:

1. portfolio citation marts and repositories still depend on it
2. a direct overwrite would combine two changes:
   - fixing family chronology
   - changing portfolio citation aggregation semantics
3. that is the wrong blast radius for a first pass

### 4. Migrate family readers first

First migration target:

1. [family_repository.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/repositories/family_repository.py)
   - `get_family_citation_chronology()`

Then:

1. family service
2. family Evidence tab

Only after family validation should portfolio readers be reconsidered.

## Standalone Stage Design

### Recommended new builder function

Add a dedicated builder in [build_gold.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py):

1. `build_gold_family_citation_chronology(settings)`

Stage name:

1. `gold-family-citation-chronology`

This function should only write:

1. `gold_family_citation_chronology.parquet`

It should not rewrite:

1. `gold_family_blocking_power.parquet`
2. `gold_family_heritage_summary.parquet`
3. `gold_family_attacker_summary.parquet`
4. `gold_family_citation_summary.parquet`
5. `gold_family_citation_timeseries_pit.parquet`

### Recommended runner exposure

Add:

1. `run_gold_family_citation_chronology(settings)` in [run.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/run.py)
2. stage aliases in [run_stage.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/scripts/run_stage.py):
   - `gold-family-citation-chronology`
   - `gold_family_citation_chronology`

### Recommended execution shape

Targeted command after implementation:

```bash
PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-family-citation-chronology
```

This is the correct command shape for a standalone chronology build.

It avoids the existing broader:

```bash
PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-family-metrics
```

which would rebuild unrelated family Gold outputs.

## Testing Impact

Current tests in [test_gold_build.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/tests/test_gold_build.py) validate the existing PIT-based timeseries output.

Recommended test addition:

1. keep the existing PIT citation-timeseries test unchanged
2. add a new dedicated chronology test for:
   - event-derived year ladder
   - cumulative forward counts
   - backward counts
   - early-window closure flags
   - support labeling

## Recommended Execution Order

1. add the new standalone chronology builder and stage
2. build only `gold_family_citation_chronology.parquet`
3. update family repository to read the new chronology mart
4. validate family `44559919` and a few additional families across sparse and rich citation coverage
5. only after that decide whether portfolio should eventually migrate off the PIT citation-timeseries mart

## Bottom Line

To obtain the correct family citation chronology:

1. do not rely on sparse PIT feature anchors
2. do not use `gold-family-metrics` as the execution path
3. add a standalone event-derived family citation chronology mart
4. expose it through its own ETL stage
5. migrate family readers first, keep existing Gold outputs untouched until that is validated

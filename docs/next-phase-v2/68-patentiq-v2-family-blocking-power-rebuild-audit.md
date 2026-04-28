# PatentIQ V2 Family Blocking-Power Rebuild Audit

## Purpose

This note records the first real rebuild and audit pass after the family blocking-power formula correction was implemented in code on `2026-04-10`.

This audit covers only the family-layer rebuild stages:

1. `gold-family-metrics`
2. `gold-history-blocking`

It does **not** mean the downstream portfolio, market, PIT-compare, or ranking marts have all been rebuilt yet.

Related notes:

1. [65-patentiq-v2-blocking-power-rebuild-impact-matrix.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/65-patentiq-v2-blocking-power-rebuild-impact-matrix.md)
2. [66-patentiq-v2-blocking-power-current-state-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/66-patentiq-v2-blocking-power-current-state-audit.md)
3. [67-patentiq-v2-derived-metric-formula-alignment-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/67-patentiq-v2-derived-metric-formula-alignment-audit.md)

---

## Implemented Formula Change

The Gold family blocking builder now applies four important corrections:

1. the citation pillar is damped before fusion using `ln(1 + adjusted_citation_score_raw)` rather than feeding the raw ratio directly into blocking power,
2. pending families are lifecycle-gated before fusion,
3. a modest technology-breadth uplift is applied,
4. UI normalization now uses `percent_rank` within the primary WIPO field cohort rather than one global family pool.

Current code:

1. [build_gold.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py)

---

## Rebuild Execution

Executed successfully with:

1. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-family-metrics`
2. `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python etl/scripts/run_stage.py gold-history-blocking`

Result:

1. `gold-family-metrics` completed with status `success`
2. `gold-history-blocking` completed with status `success`

---

## Rebuilt Outputs

Confirmed rebuilt:

1. `gold_family_blocking_power.parquet`
2. `gold_family_heritage_summary.parquet`
3. `gold_family_attacker_summary.parquet`
4. `gold_family_citation_summary.parquet`
5. `gold_family_citation_timeseries_pit.parquet`
6. `gold_family_blocking_power_timeseries.parquet`

Most important row-count check:

1. `gold_family_blocking_power_timeseries.parquet`: `152,145,173` rows

---

## Before vs After Audit

### Current Family Blocking Distribution

#### Before rebuild

From [66-patentiq-v2-blocking-power-current-state-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/66-patentiq-v2-blocking-power-current-state-audit.md):

1. UI median: `46.41`
2. UI p90: `90.04`
3. UI p99: `98.94`
4. raw absolute score was effectively dominated by the undamped citation term in extreme cases

#### After family rebuild

1. UI median: `36.48`
2. UI p90: `89.34`
3. UI p99: `98.97`
4. raw p50: `0.0224`
5. raw p90: `0.1265`
6. raw p99: `0.9778`
7. raw max: `3.2522`

Interpretation:

1. the raw blocking scale is now dramatically more controlled,
2. the UI percentile distribution still spans the full range by design,
3. the change did not collapse the ranking system, but it did materially compress the raw score explosion underneath it.

### Pending-Family Distortion

#### Before rebuild

From [66-patentiq-v2-blocking-power-current-state-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/66-patentiq-v2-blocking-power-current-state-audit.md):

1. pending family count: `6,405,024`
2. pending families with UI blocking `>= 90`: `493,039`
3. pending UI p90: `87.17`
4. pending UI p99: `98.59`
5. pending max: `99.99998`

#### After family rebuild

1. pending family count: `6,405,024`
2. pending families with UI blocking `>= 90`: `203,400`
3. pending UI p90: `56.44`
4. pending UI p99: `93.89`
5. pending max: `95.89`
6. pending raw p90: `0.0325`
7. pending raw p99: `0.1403`
8. pending raw max: `0.4678`

Interpretation:

1. the main failure mode is materially reduced,
2. pending families no longer reach absurd raw blocking magnitudes,
3. the count of pending families surfacing in the `>= 90` UI band dropped from `493,039` to `203,400`,
4. this is a strong improvement, but not yet a complete elimination of the pending-family high-percentile issue.

### Reduction Summary

Most important deltas:

1. pending `>= 90` count fell by `289,639`
2. pending `>= 90` count fell by about `58.7%`
3. pending max UI score fell from `99.99998` to `95.89`
4. pending raw max is now bounded below `0.5` in the rebuilt family layer

---

## What Improved

1. extreme citation-ratio explosions no longer dominate family raw blocking scores,
2. pending families are much less likely to appear as near-perfect blockers,
3. field-cohort normalization is now more semantically consistent than one global population rank,
4. the historical blocking-timeseries layer now uses the same corrected family fusion contract.

---

## What Is Still Not Finished

1. portfolio summary, compare, and classification-density marts are still downstream of older built artifacts until the broader rebuild order is completed,
2. market density and ranking marts are also still waiting on the downstream rebuild chain,
3. the pending-family UI tail is improved but not fully resolved,
4. the current family formula is still an MVP correction, not yet the final fully event-native legal engine described in the notes.

---

## Practical Conclusion

The family blocking-power correction is now real in the rebuilt family-layer artifacts and it materially improves the main audited distortion.

However, the platform is still in a mixed state:

1. family blocking marts are rebuilt,
2. downstream portfolio and market marts are not yet fully rebuilt from that corrected base,
3. the next step remains the broader rebuild chain from [65-patentiq-v2-blocking-power-rebuild-impact-matrix.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/65-patentiq-v2-blocking-power-rebuild-impact-matrix.md).

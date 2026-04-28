# PatentIQ V2 Blocking-Power Downstream PIT Rebuild Audit

## Purpose

This note records the downstream rebuild status after the `2026-04-10` family blocking-power correction was propagated into the main PIT and ranking marts.

This note is intentionally separate from the family-only rebuild audit in [68-patentiq-v2-family-blocking-power-rebuild-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/68-patentiq-v2-family-blocking-power-rebuild-audit.md).

The main question here is not whether the corrected family formula compiled. That was already proven. The question here is which downstream marts now truly reflect that corrected base, what their row coverage looks like, and which active current-serving marts are still stale.

Related notes:

1. [65-patentiq-v2-blocking-power-rebuild-impact-matrix.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/65-patentiq-v2-blocking-power-rebuild-impact-matrix.md)
2. [67-patentiq-v2-derived-metric-formula-alignment-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/67-patentiq-v2-derived-metric-formula-alignment-audit.md)
3. [68-patentiq-v2-family-blocking-power-rebuild-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/68-patentiq-v2-family-blocking-power-rebuild-audit.md)

Audit date: `2026-04-10`

---

## Scope

This audit covers the downstream marts that were rebuilt from the corrected family blocking base:

1. `gold_family_compare_pit.parquet`
2. `gold_family_classification_jurisdiction_pit.parquet`
3. `gold_portfolio_summary_pit.parquet`
4. `gold_portfolio_compare_pit.parquet`
5. `gold_portfolio_classification_jurisdiction_pit.parquet`
6. `gold_market_cpc_trend_pit.parquet`
7. `gold_market_cpc_jurisdiction_trend_pit.parquet`
8. `gold_cpc_importance_pit.parquet`

This audit does **not** certify the current-serving marts that still depend on a stale current family summary snapshot.

Most important excluded current-serving gap:

1. `gold_family_summary.parquet` was not successfully rebuilt in this pass,
2. therefore the current-serving `gold_portfolio_*` executive marts that depend on that family-summary path are also not yet fully refreshed,
3. the failure mode was not a formula error but a monolithic DuckDB spill and disk-pressure problem during rebuild.

---

## Rebuild Execution Summary

The downstream PIT chain completed successfully after switching the heaviest builders to chunked output and removing stale cached chunk directories before rerun.

Confirmed rebuilt row counts:

1. `gold_family_compare_pit.parquet`: `164,988,135`
2. `gold_family_classification_jurisdiction_pit.parquet`: `566,936,693`
3. `gold_portfolio_summary_pit.parquet`: `36,127,659`
4. `gold_portfolio_compare_pit.parquet`: `36,127,659`
5. `gold_portfolio_classification_jurisdiction_pit.parquet`: `822,946,329`
6. `gold_market_cpc_trend_pit.parquet`: `862,969`
7. `gold_market_cpc_jurisdiction_trend_pit.parquet`: `15,883,551`
8. `gold_cpc_importance_pit.parquet`: `152,753`

All rebuilt PIT/ranking marts span `2007` through `2026`.

---

## Coverage Audit

### Family PIT Coverage

`gold_family_compare_pit.parquet`

1. rows: `164,988,135`
2. distinct families: `17,633,618`
3. year range: `2007-2026`

Interpretation:

1. the corrected blocking base is now present across the full family compare PIT range,
2. the rebuilt row count is large enough to indicate the chunked builder preserved broad historical coverage rather than silently truncating late years.

### Family Classification x Jurisdiction PIT Coverage

`gold_family_classification_jurisdiction_pit.parquet`

1. rows: `566,936,693`
2. distinct families: `10,392,690`
3. year range: `2007-2026`

Support distribution:

1. `limited`: `438,350,487`
2. `moderate`: `89,111,715`
3. `strong`: `39,474,491`

Interpretation:

1. the support-level distribution is directionally sensible for a deep classification x jurisdiction surface,
2. `limited` support remains the dominant state, so the UI must keep support labeling prominent instead of presenting every slice as equally reliable.

### Portfolio PIT Coverage

`gold_portfolio_summary_pit.parquet`

1. rows: `36,127,659`
2. distinct owners: `3,034,400`
3. year range: `2007-2026`

`gold_portfolio_compare_pit.parquet`

1. rows: `36,127,659`
2. distinct owners: `3,034,400`
3. year range: `2007-2026`

Interpretation:

1. the portfolio PIT chain was rebuilt successfully from the corrected family base,
2. the compare view and summary view remain aligned on row coverage,
3. these are PIT marts, not the current-serving executive portfolio marts used by the V2 backend page contracts.

### Portfolio Classification x Jurisdiction PIT Coverage

`gold_portfolio_classification_jurisdiction_pit.parquet`

1. rows: `822,946,329`
2. distinct owners: `2,183,765`
3. year range: `2007-2026`
4. placeholder-owner rows in the audited null/unknown bucket: `0`

Support distribution:

1. `limited`: `650,901,240`
2. `moderate`: `120,488,081`
3. `strong`: `51,557,008`

Interpretation:

1. the placeholder-owner leakage that previously distorted some portfolio views is not present in this rebuilt PIT mart,
2. support coverage is still heavily `limited`, so slice-level UI outputs need support chips and explanatory tooltips.

### Market CPC PIT Coverage

`gold_market_cpc_trend_pit.parquet`

1. rows: `862,969`
2. year range: `2007-2026`

`gold_market_cpc_jurisdiction_trend_pit.parquet`

1. rows: `15,883,551`
2. year range: `2007-2026`

`gold_cpc_importance_pit.parquet`

1. rows: `152,753`
2. year range: `2007-2026`

Interpretation:

1. the market-side CPC ranking and density views were rebuilt successfully from the corrected family base,
2. this is enough to proceed with PIT market-context wiring once the UI presentation contract is finalized.

---

## Distribution Audit

### Family Blocking Snapshot

Audited current family blocking after the rebuild:

1. total families: `17,633,618`
2. pending families: `6,405,024`
3. pending families with UI blocking `>= 90`: `203,400`
4. overall UI median: `36.48`
5. overall UI p90: `89.52`
6. overall UI p99: `99.00`
7. overall raw p99: `0.9814`
8. overall raw max: `3.2522`

Interpretation:

1. the corrected family blocking base remained stable after the downstream rebuild chain,
2. the main explosion problem is materially reduced relative to the pre-rebuild state,
3. the remaining high pending tail is a product-labeling and support-communication problem more than a raw explosion problem.

### Portfolio Blocking PIT Distribution

From `gold_portfolio_summary_pit.parquet`:

1. average blocking p50: `46.51`
2. average blocking p90: `88.31`
3. average blocking p99: `99.35`
4. average blocking max: `100.00`
5. total blocking p99: `2,208.23`
6. total blocking max: `11,738,976.27`
7. top-family blocking-share p99: `1.00`
8. top-family blocking-share max: `1.00`

Interpretation:

1. `portfolio_avg_blocking_power_score_asof` remains usable as a normalized peer-facing indicator,
2. `portfolio_total_blocking_power_score_asof` is an aggregate mass measure and must not be presented as if it were a bounded `0-100` score,
3. `portfolio_top_family_blocking_share_asof` saturates at `1.00` for highly concentrated or very small portfolios, so it is best presented as a concentration ratio with tooltip context rather than as a quality score.

### Market CPC Blocking Density Distribution

From `gold_market_cpc_trend_pit.parquet`:

1. blocking density p50: `43.08`
2. blocking density p90: `69.20`
3. blocking density p99: `97.94`
4. blocking density max: `100.00`

From `gold_market_cpc_jurisdiction_trend_pit.parquet`:

1. blocking density p50: `60.41`
2. blocking density p90: `96.32`
3. blocking density p99: `99.86`
4. blocking density max: `100.00`

Interpretation:

1. jurisdiction-sliced market density is naturally more extreme than CPC-only density,
2. the UI should frame this as relative density within a slice, not as a direct statement of legal certainty or portfolio quality.

---

## Real Portfolio Spot Checks

Audited `2026` PIT rows for real owner keys in the rebuilt portfolio summary mart:

1. `APPLE`: `27,018` historical families, `18,111` active families, average blocking `59.54`, total blocking `1,608,626.32`
2. `APPLE_INC_`: `67` historical families, `37` active families, average blocking `42.52`, total blocking `2,849.03`
3. `TESLA`: `356` historical families, `213` active families, average blocking `54.26`, total blocking `19,317.39`
4. `TESLA_INC_`: `193` historical families, `96` active families, average blocking `45.77`, total blocking `8,833.24`

Interpretation:

1. the rebuilt PIT marts are returning sensible portfolio-scale values for real companies,
2. the presence of both `APPLE` and `APPLE_INC_`, and both `TESLA` and `TESLA_INC_`, proves that owner-key consolidation is still not perfectly canonical at the PIT mart layer,
3. backend search and routing should therefore keep using explicit owner-key resolution rather than assuming a single textual variant per real-world company.

Top audited `2026` portfolio slices:

1. `APPLE` strongest observed audited slices were centered on `Computer technology`, `G06F3/00`, especially in `US`, `DE`, and `WO`
2. `TESLA` strongest observed audited slices were centered on `Electrical machinery, apparatus, energy`, especially `H01M4/00` and `H01M10/00` in `WO` and `US`

Interpretation:

1. the slice-level outputs align with obvious company-domain intuition,
2. this does not prove product readiness alone, but it is a meaningful sensibility check against absurd or empty slice outputs.

### Market Top Slice Sanity Check

Top audited `2026` market slices by family count in `gold_market_cpc_jurisdiction_trend_pit.parquet` included:

1. `Electrical machinery, apparatus, energy` / `Y02E60/00` / `CN`
2. `Computer technology` / `G06F16/00` / `CN`
3. `Computer technology` / `G06F3/00` / `CN`
4. `Computer technology` / `G06F3/00` / `US`
5. `IT methods for management` / `G06Q10/00` / `CN`

Interpretation:

1. the top market slices are plausible for the audited period,
2. nothing in the rebuilt sample suggests the downstream CPC market marts collapsed during chunked rebuild.

---

## What Is Still Not Finished

The downstream PIT and ranking chain is in much better shape now, but the current-serving chain is still mixed.

Still pending:

1. `gold_family_summary.parquet` remains stale because the rebuild path still runs as a monolithic heavy spill job,
2. current-serving portfolio executive marts that depend on the current family summary path are therefore not yet re-certified from the corrected blocking base,
3. current-serving market summary marts should be rerun after the current family summary path is stabilized,
4. the builder should be refactored so the current family summary stage writes chunked outputs instead of relying on one large temporary spill footprint.

Operational implication:

1. PIT/ranking marts are refreshed,
2. current-serving family and portfolio executive marts are not yet fully refreshed,
3. backend/UI wiring should not claim that every active surface is already rebuilt from the corrected blocking base.

---

## Practical Conclusion

The corrected blocking-power contract is now propagated through the main family, portfolio, and market PIT/ranking marts.

That is enough to say the downstream analytical history surfaces have been materially refreshed.

It is **not** enough to say the full serving layer is finished.

The remaining blocker is now narrow and concrete:

1. refactor the current family summary rebuild to avoid spill-heavy one-shot execution,
2. rerun the current-serving family and portfolio summary chain from that refreshed base,
3. perform one final sensibility audit on the active backend-facing marts after that rerun.

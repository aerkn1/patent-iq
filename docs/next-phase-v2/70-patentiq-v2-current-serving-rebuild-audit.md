# PatentIQ V2 Current-Serving Rebuild Audit

## Purpose

This note records the first post-rebuild audit of the current-serving Gold marts after the blocking-power correction had already been propagated through:

1. family blocking/history marts,
2. downstream PIT/ranking marts,
3. the current `gold_family_summary` dataset,
4. the current `gold-portfolio` serving stage,
5. the remaining `gold-market-summary-pit` rebuild.

This is the note that closes the narrow rebuild gap described in [69-patentiq-v2-blocking-power-downstream-pit-rebuild-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/69-patentiq-v2-blocking-power-downstream-pit-rebuild-audit.md).

Audit date: `2026-04-10`

Related notes:

1. [68-patentiq-v2-family-blocking-power-rebuild-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/68-patentiq-v2-family-blocking-power-rebuild-audit.md)
2. [69-patentiq-v2-blocking-power-downstream-pit-rebuild-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/69-patentiq-v2-blocking-power-downstream-pit-rebuild-audit.md)
3. [63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md)

---

## Rebuild Status

### 1. `gold_family_summary.parquet`

Status: `refreshed`

Important implementation note:

1. the family-summary stage was changed to publish a parquet dataset directory rather than forcing one giant merged file,
2. this avoided the prior spill-heavy merge failure,
3. the published dataset contains `32` bucket parquet parts.

Readback check:

1. row count: `17,633,618`

### 2. `gold-portfolio`

Status: `refreshed`

Completed at:

1. `2026-04-10 11:20:35` local session time

Refreshed outputs and row counts:

1. `gold_portfolio_summary.parquet`: `3,034,400`
2. `gold_portfolio_threat_matrix.parquet`: `15,269,449`
3. `gold_portfolio_field_timeseries.parquet`: `5,520,241`
4. `gold_portfolio_heritage_summary.parquet`: `3,852,589`
5. `gold_portfolio_citation_summary.parquet`: `21,945,507`
6. `gold_portfolio_citation_timeseries.parquet`: `21,945,507`
7. `gold_portfolio_attacker_momentum.parquet`: `6,016,882`
8. `gold_portfolio_citation_pressure_by_field.parquet`: `2,052,577`
9. `gold_portfolio_citation_pressure_by_jurisdiction.parquet`: `2,000,661`
10. `gold_portfolio_forecast_summary.parquet`: `3,034,400`
11. `gold_portfolio_forecast_segments.parquet`: `11,040,482`
12. `gold_portfolio_forecast_contributors.parquet`: `17,866,740`

### 3. `gold_market_summary_pit.parquet`

Status: `refreshed`

Completed at:

1. `2026-04-10 11:23:12` local session time

Readback check:

1. row count: `504`

---

## Current Portfolio Summary Audit

### Distribution Check

From `gold_portfolio_summary.parquet`:

1. rows: `3,034,400`
2. distinct owners: `3,034,400`
3. `portfolio_avg_blocking_power_within_mega_cluster` p50: `38.05`
4. `portfolio_avg_blocking_power_within_mega_cluster` p90: `89.14`
5. `portfolio_avg_blocking_power_within_mega_cluster` p99: `98.71`
6. `portfolio_avg_blocking_power_within_mega_cluster` max: `100.00`
7. `portfolio_current_threat_score` p99: `1.8159`
8. `portfolio_current_threat_score` max: `14,299.07`
9. `portfolio_crown_jewel_index` p99: `5.0280`
10. `portfolio_crown_jewel_index` max: `24.2529`
11. `portfolio_total_mass_score` p99: `5.7088`
12. `portfolio_total_mass_score` max: `48,747.64`

Interpretation:

1. `portfolio_avg_blocking_power_within_mega_cluster` still behaves like a normalized `0-100` score and remains product-safe as a score-like metric,
2. `portfolio_current_threat_score`, `portfolio_crown_jewel_index`, and `portfolio_total_mass_score` are **not** normalized score fields,
3. these fields should be labeled as `index`, `aggregate`, or `mass` measures in backend/UI contracts, not shown as bounded `0-100` scores.

### Real Owner Spot Check

Sample rows:

1. `APPLE`: `27,018` families, `18,111` active-grant families, average blocking `55.0310`, threat `972.7839`, crown-jewel index `22.1066`, total mass `7,519.3960`
2. `APPLE_INC_`: `67` families, `37` active-grant families, average blocking `43.0682`, threat `2.4606`, crown-jewel index `9.6049`, total mass `17.2025`
3. `TESLA`: `356` families, `213` active-grant families, average blocking `55.1337`, threat `14.0319`, crown-jewel index `15.3019`, total mass `120.8306`
4. `TESLA_INC_`: `193` families, `96` active-grant families, average blocking `45.8390`, threat `6.9202`, crown-jewel index `14.7230`, total mass `59.3085`

Interpretation:

1. the owner splits such as `APPLE` vs `APPLE_INC_` and `TESLA` vs `TESLA_INC_` still prove that harmonized-owner canonicalization is not fully collapsed into one key per real-world company,
2. the metrics themselves are internally plausible once the unbounded fields are treated as indices rather than normalized scores,
3. backend search and routing should keep explicit owner-key resolution and not assume one textual form per company.

---

## Portfolio Forecast Audit

### Output Shape

The refreshed forecast summary currently serves interval-first citation outputs and expected lapse aggregates, not score bands:

1. `portfolio_expected_future_citations_total_3y`
2. `portfolio_expected_future_citations_lower_3y`
3. `portfolio_expected_future_citations_upper_3y`
4. `portfolio_expected_future_citations_total_5y`
5. `portfolio_expected_future_citations_lower_5y`
6. `portfolio_expected_future_citations_upper_5y`
7. `portfolio_expected_lapses_count_12m`
8. `portfolio_expected_lapses_count_24m`
9. coverage percentages and coverage-status caveats

This is aligned with the earlier model-serving decisions:

1. Phase 03 is interval-first rather than exact-count-first,
2. Phase 04 remains aggregate/gated rather than hard-probability-first.

### Real Owner Spot Check

Sample forecast rows:

1. `APPLE`: citations `16,003.147` over `3y` with interval `[12,296.049, 21,400.618]`; citations `31,659.702` over `5y` with interval `[27,553.280, 36,761.811]`; expected lapses `494.852` over `12m`; coverage status `medium`
2. `APPLE_INC_`: citations `0.415` over `3y` with interval `[0.155, 0.809]`; citations `0.501` over `5y` with interval `[0.273, 0.764]`; lapse aggregates unavailable; coverage status `low`
3. `TESLA`: citations `100.023` over `3y` with interval `[86.754, 117.567]`; citations `186.890` over `5y` with interval `[172.415, 204.153]`; expected lapses `0.765` over `12m`; coverage status `low`
4. `TESLA_INC_`: citations `23.930` over `3y` with interval `[19.551, 29.542]`; citations `44.383` over `5y` with interval `[39.825, 49.769]`; expected lapses `0.135` over `12m`; coverage status `medium`

Interpretation:

1. the forecast marts are rebuilt and readable,
2. the coverage caveat fields are mandatory for UI display because the owner-level support quality clearly varies,
3. `portfolio_hotspot_coverage_pct_3y` and `portfolio_hotspot_coverage_pct_5y` are currently `1.0` for the sampled owners and should therefore be treated carefully in UI copy to avoid implying more certainty than the coverage status does.

---

## Portfolio Threat Matrix Audit

### Data Quality Check

From `gold_portfolio_threat_matrix.parquet`:

1. total rows: `15,269,449`
2. rows with unknown/unassigned attacker name: `178,307`
3. rows where focal owner equals citing assignee: `46,296`

Interpretation:

1. unknown-attacker rows are still present and should not be mixed into the default visible threat leaderboard,
2. self-threat rows are also present and should be excluded or moved behind an explicit `include self-citations` control,
3. the current threat matrix is useful, but it still needs one serving-layer filter pass before being treated as a polished product surface.

### Real Owner Spot Check

Top observed threat rows:

1. `APPLE` top visible external threats include `QUALCOMM` and `SAMSUNG_ELECTRONICS_COMPANY` across `Digital communication`, `Computer technology`, and `Telecommunications`
2. `TESLA` top visible external threats include `LG_ENERGY_SOLUTION`, `GM_GLOBAL_TECHNOLOGY_OPERATIONS`, and `VOLKSWAGEN`
3. `APPLE` also still shows one self-row (`APPLE`) in the top results if no self-filter is applied

Interpretation:

1. the threat matrix is semantically valuable,
2. the default API/UI contract should filter unknown attackers and self-rows before ranking and pagination.

---

## Market Summary PIT Audit

### Coverage Check

From `gold_market_summary_pit.parquet`:

1. total rows: `504`
2. year range: `1956-2025`
3. distinct years: `62`

Interpretation:

1. the market summary PIT rebuild succeeded technically,
2. it does **not** currently include `2026`,
3. backend/UI wiring should therefore not assume parity with the `2007-2026` family and portfolio PIT surfaces.

### Sensibility Check

Distribution:

1. `segment_blocking_density_asof` p50: `0.0`
2. `segment_blocking_density_asof` p90: `75.8153`
3. `segment_blocking_density_asof` max: `89.1496`
4. `segment_enforceability_density_asof` p50: `0.0`
5. `segment_enforceability_density_asof` p90: `1.2429`
6. `segment_enforceability_density_asof` max: `1.4670`
7. rows where `segment_active_family_count_asof > segment_family_count_asof`: `144 / 504`

Interpretation:

1. the blocking-density field looks usable as a relative density measure,
2. the enforceability-density field is low-range and should not be styled as a `0-100` score,
3. the fact that `segment_active_family_count_asof` exceeds `segment_family_count_asof` in `144` rows indicates a denominator mismatch or field-label mismatch that must be clarified before UI exposure.

### 2025 Segment Spot Check

Top `2025` segments by family count include:

1. `Computer technology`
2. `Measurement`
3. `Electrical machinery, apparatus, energy`
4. `IT methods for management`
5. `Digital communication`

Observed values:

1. all top `2025` segments were labeled `cooling`,
2. `segment_enforceability_density_asof` was `0.0` for the top visible rows,
3. `segment_active_family_count_asof` materially exceeded `segment_family_count_asof` in those same rows.

Interpretation:

1. the output is structurally present,
2. the segment summary mart still needs a semantics audit before it is promoted as a trustworthy score-heavy market card source.

---

## Practical Conclusion

The rebuild chain is now materially complete:

1. family summary is refreshed,
2. current-serving portfolio marts are refreshed,
3. market summary PIT is refreshed.

The remaining issues are no longer rebuild failures. They are now mostly **serving-contract and metric-labeling issues**:

1. several portfolio fields are indices/aggregates, not normalized scores,
2. threat matrix default views should exclude unknown attackers and self-rows,
3. market summary PIT still has denominator/labeling questions and stops at `2025`,
4. owner-key canonicalization remains imperfect for real companies like `APPLE` and `TESLA`.

That means the next work is not another blind rebuild. The next work is:

1. tighten backend/UI field labels and tooltips,
2. filter threat defaults,
3. audit and possibly rename the market summary denominator fields,
4. decide whether `2026` should be added to market summary PIT or explicitly documented as not yet available.

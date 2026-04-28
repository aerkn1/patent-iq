# PatentIQ V2 Blocking-Power Current-State Audit

## Purpose

This note records the current on-disk audit state for the planned blocking-power and citation-normalization refactor. It complements [65-patentiq-v2-blocking-power-rebuild-impact-matrix.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/65-patentiq-v2-blocking-power-rebuild-impact-matrix.md) by answering three questions:

1. do the expected Gold marts exist,
2. do the logically safe marts actually stay free of blocking, enforceability, and heritage-serving fields,
3. do the current family, portfolio, and market distributions still show the distortion patterns already identified in the design notes.

The cross-metric semantic classification of the current formulas is recorded separately in [67-patentiq-v2-derived-metric-formula-alignment-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/67-patentiq-v2-derived-metric-formula-alignment-audit.md).

Audit date: `2026-04-10`

---

## Audit Method

Two passes were used:

1. a metadata-only parquet inspection using `pyarrow.parquet.ParquetFile` to verify existence, row counts, schemas, and trigger-field presence without scanning the full datasets,
2. a targeted quantitative pass using DuckDB `approx_quantile` over the highest-risk serving metrics.

The audit was run against the current Gold directory:

`etl/data/gold`

---

## Structural Inventory Findings

### Must Rebuild Set

The `Must Rebuild` set from [65-patentiq-v2-blocking-power-rebuild-impact-matrix.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/65-patentiq-v2-blocking-power-rebuild-impact-matrix.md) is fully present on disk.

1. total expected: `22`
2. existing: `22`
3. missing: `0`

The following marts currently carry explicit blocking-serving fields:

1. `gold_family_blocking_power.parquet`
2. `gold_family_compare_pit.parquet`
3. `gold_family_classification_jurisdiction_pit.parquet`
4. `gold_semantic_match_context.parquet`
5. `gold_portfolio_summary.parquet`
6. `gold_portfolio_summary_pit.parquet`
7. `gold_portfolio_compare_pit.parquet`
8. `gold_portfolio_classification_mix_pit.parquet`
9. `gold_portfolio_classification_jurisdiction_pit.parquet`
10. `gold_market_summary_pit.parquet`
11. `gold_market_cpc_trend_pit.parquet`
12. `gold_market_cpc_jurisdiction_trend_pit.parquet`
13. `gold_cpc_importance_pit.parquet`

The following marts currently carry explicit enforceability-serving fields:

1. `gold_family_compare_pit.parquet`
2. `gold_family_classification_jurisdiction_pit.parquet`
3. `gold_portfolio_summary_pit.parquet`
4. `gold_portfolio_compare_pit.parquet`
5. `gold_portfolio_classification_mix_pit.parquet`
6. `gold_portfolio_classification_jurisdiction_pit.parquet`
7. `gold_market_summary_pit.parquet`
8. `gold_market_cpc_trend_pit.parquet`
9. `gold_market_cpc_jurisdiction_trend_pit.parquet`
10. `gold_cpc_importance_pit.parquet`

The following marts currently carry explicit heritage-style serving fields:

1. `gold_family_blocking_power.parquet`
2. `gold_family_heritage_summary.parquet`
3. `gold_portfolio_summary.parquet`
4. `gold_portfolio_field_timeseries.parquet`
5. `gold_portfolio_heritage_summary.parquet`

Two important dependency notes remain true even where direct trigger columns are not visible in the schema:

1. `gold_family_blocking_power_timeseries.parquet` still belongs in the rebuild set because it is the historical extension of the current family blocking logic.
2. `gold_market_leaderboard_pit.parquet` still belongs in the rebuild set because its ordering semantics depend on upstream market density outputs even though the exact trigger column names are not materialized directly in its schema.

### Logically Safe To Keep Set

The `Logically Safe To Keep` set is also fully present on disk.

1. total expected: `16`
2. existing: `16`
3. missing: `0`

Most important result:

1. blocking-signal columns found: `0`
2. enforceability-signal columns found: `0`
3. heritage-signal columns found: `0`

That means the current safe set is structurally clean and does not secretly carry the known blocking/enforceability/heritage contamination through schema-visible serving fields.

---

## Row-Count Snapshot

### Must Rebuild Marts

1. `gold_family_summary.parquet`: `17,633,618`
2. `gold_family_blocking_power.parquet`: `17,633,618`
3. `gold_family_heritage_summary.parquet`: `21,353,101`
4. `gold_family_blocking_power_timeseries.parquet`: `152,145,173`
5. `gold_family_compare_pit.parquet`: `164,988,135`
6. `gold_family_classification_jurisdiction_pit.parquet`: `566,936,693`
7. `gold_semantic_match_context.parquet`: `20,295,898`
8. `gold_portfolio_summary.parquet`: `3,034,400`
9. `gold_portfolio_field_timeseries.parquet`: `5,520,241`
10. `gold_portfolio_heritage_summary.parquet`: `3,852,589`
11. `gold_portfolio_forecast_summary.parquet`: `3,034,400`
12. `gold_portfolio_forecast_segments.parquet`: `11,040,482`
13. `gold_portfolio_forecast_contributors.parquet`: `17,866,740`
14. `gold_portfolio_summary_pit.parquet`: `36,127,659`
15. `gold_portfolio_compare_pit.parquet`: `36,127,659`
16. `gold_portfolio_classification_mix_pit.parquet`: `158,834,197`
17. `gold_portfolio_classification_jurisdiction_pit.parquet`: `828,526,264`
18. `gold_market_summary_pit.parquet`: `504`
19. `gold_market_cpc_trend_pit.parquet`: `862,969`
20. `gold_market_cpc_jurisdiction_trend_pit.parquet`: `15,883,551`
21. `gold_cpc_importance_pit.parquet`: `152,753`
22. `gold_market_leaderboard_pit.parquet`: `7,600`

### Logically Safe Marts

1. `gold_family_classification_mix_pit.parquet`: `164,988,135`
2. `gold_family_citation_summary.parquet`: `17,633,618`
3. `gold_family_citation_timeseries_pit.parquet`: `164,988,135`
4. `gold_portfolio_citation_summary.parquet`: `21,945,507`
5. `gold_portfolio_citation_timeseries.parquet`: `21,945,507`
6. `gold_portfolio_attacker_momentum.parquet`: `6,016,882`
7. `gold_portfolio_citation_pressure_by_field.parquet`: `2,052,577`
8. `gold_portfolio_citation_pressure_by_jurisdiction.parquet`: `2,000,661`
9. `gold_market_citation_trend_pit.parquet`: `294`
10. `gold_market_citation_pressure_by_jurisdiction_pit.parquet`: `6,063`
11. `gold_market_attacker_leaderboard_pit.parquet`: `4,771,190`
12. `gold_portfolio_threat_matrix.parquet`: `15,269,449`
13. `gold_family_attacker_summary.parquet`: `6,334,292`
14. `gold_market_intelligence_segments.parquet`: `10`
15. `gold_market_intelligence_timeseries.parquet`: `504`
16. `gold_market_intelligence_overview.parquet`: `1`

---

## Quantitative Sensibility Findings

### Family Blocking Distribution

Current family blocking remains heavily compressed toward the top end.

1. median: `46.41`
2. p90: `90.04`
3. p99: `98.94`
4. max: `100.0`

This remains inconsistent with the intended interpretation of blocking power as a constrained, stage-aware serving metric.

### Pending-Family Distortion

The strongest current distortion remains `pending_emerging` families appearing as extremely strong blockers.

1. pending family count: `6,405,024`
2. pending families with blocking score `>= 90`: `493,039`
3. pending median: `0.0`
4. pending p90: `87.17`
5. pending p99: `98.59`
6. pending max: `99.99998`

This confirms the existing issue is not anecdotal. It is present at material scale.

### Portfolio Executive Distortion

Portfolio executive metrics still inherit the family-level distortion and also show unbounded aggregate behavior.

#### `gold_portfolio_summary.parquet`

`portfolio_avg_blocking_power_within_mega_cluster`

1. p50: `46.79`
2. p90: `90.05`
3. p99: `98.58`
4. max: `99.99990`

`portfolio_current_threat_score`

1. p50: `0.048`
2. p90: `0.277`
3. p99: `1.87`
4. max: `14,299.07`

`portfolio_heritage_score`

1. p50: `0.0`
2. p90: `9.49`
3. p99: `105.31`
4. max: `484,497.78`

`portfolio_hit_rate_top_decile`

1. p50: `0.0`
2. p90: `0.638`
3. p99: `1.0`
4. max: `1.0`

Interpretation:

1. average blocking is still too close to the family distortion pattern,
2. threat and heritage are clearly unbounded mass/index measures, not UI-safe normalized scores,
3. top-decile hit rate saturates at `1.0`, so it is not a clean executive quality metric in the current form.

### Portfolio PIT Distortion

`gold_portfolio_compare_pit.parquet` still carries the same upstream dependency problem.

`portfolio_avg_blocking_power_score_asof`

1. p50: `46.66`
2. p90: `88.12`
3. p99: `99.34`
4. max: `100.0`

`portfolio_total_blocking_power_score_asof`

1. p50: `68.37`
2. p90: `347.97`
3. p99: `2,235.95`
4. max: `11,738,976.27`

`portfolio_avg_enforceability_score_asof`

1. p50: `0.268`
2. p90: `1.345`
3. p99: `2.664`
4. max: `12.246`

Interpretation:

1. average blocking PIT still reflects the same compressed high-end shape,
2. total blocking is an unbounded aggregate and must not be treated like a normalized score,
3. enforceability is not obviously broken, but it remains downstream of the family-stage logic and therefore still needs rebuild.

### Market Density Distortion

`gold_market_summary_pit.parquet` is structurally smaller, but still downstream of the same family foundation.

`segment_blocking_density_asof`

1. p50: `0.0`
2. p90: `75.91`
3. max: `89.15`

`segment_enforceability_density_asof`

1. p50: `0.0`
2. p90: `1.247`
3. max: `1.467`

Interpretation:

1. market blocking density is not obviously exploding like portfolio total mass, but it is still derived from the current family blocking system,
2. market density outputs should therefore be treated as dependent rebuild targets, not validated end-state metrics.

---

## Audit Conclusions

### Structural Conclusion

The rebuild matrix is confirmed by the on-disk Gold state.

1. every expected `must rebuild` mart exists,
2. every expected `safe to keep` mart exists,
3. the safe set is structurally clean with respect to blocking, enforceability, and heritage-serving columns.

### Semantic Conclusion

The current high-risk surfaces still show the same problems already identified in earlier notes.

1. pending families can still rank as top blockers at large scale,
2. portfolio executive metrics still inherit the family distortion,
3. several portfolio metrics are clearly aggregate masses or indices rather than normalized UI scores,
4. market density outputs are still dependent on the same family foundation and should be rebuilt after the fix.

### Practical Conclusion

The blocking-power refactor should proceed exactly in the staged order defined in [65-patentiq-v2-blocking-power-rebuild-impact-matrix.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/65-patentiq-v2-blocking-power-rebuild-impact-matrix.md).

No change is needed to the `Logically Safe To Keep` set on the basis of this audit.

---

## Immediate Implications

1. do not present current family or portfolio blocking-style metrics as fully trustworthy until the family Gold blocking contract is corrected,
2. keep citation evidence and classification evidence marts in service because the audit shows they are not structurally contaminated,
3. rebuild the three ranking-ready marts from `2026-04-10` together with the broader family, portfolio, and market dependency chain after the blocking-power correction,
4. keep the backend/UI caveats currently in place for portfolio executive metrics until the rebuild is complete.

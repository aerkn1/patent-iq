# PatentIQ V2 Portfolio Executive Metric Sensibility Audit

## Goal

Audit the metrics currently shown on the portfolio `Executive` tab and decide which are safe to expose now, which must be relabeled, and which must be withheld until upstream scoring is corrected.

This note is specifically about current serving sensibility, not long-term feature desirability.

For the broader layer-boundary refactor beyond portfolio, see [63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md).

## Scope

Current executive-tab sources:

1. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
2. [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
3. current V2 portfolio overview contract in [portfolios.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/application/services/portfolios.py)

## Main Conclusion

The executive tab previously mixed:

1. safe counts,
2. useful but unbounded aggregate indices,
3. blocking-rank-derived metrics that are currently contaminated by upstream family blocking-power inflation.

So the executive surface should not present all of these as peers.

## Direct Evidence

### Source formulas in the current Gold rollup

Portfolio executive metrics are currently built in [build_gold.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/gold/build_gold.py#L1418):

1. `portfolio_avg_blocking_power_within_mega_cluster = avg(family_ui_blocking_power_score)`
2. `portfolio_hit_rate_top_decile = avg(family_ui_blocking_power_score >= 90)`
3. `portfolio_crown_jewel_index = sum(top-ranked family_raw_absolute_blocking_power)`
4. `portfolio_total_mass_score = sum(granted family_raw_absolute_blocking_power)`
5. `portfolio_current_threat_score = sum(granted family_market_threat_score_raw)`
6. `portfolio_heritage_score = sum(family_adjusted_citation_score_raw)`

Because family-level blocking power is currently inflated for some `pending_emerging` families, any portfolio metric that depends on family blocking rank is not safe for executive use.

### Distribution audit from the current Gold summary mart

Observed current distributions:

1. `portfolio_family_count_within_mega_cluster`
   - median `1`
   - p90 `8`
   - p99 `57`
   - max `163,158`
2. `portfolio_avg_blocking_power_within_mega_cluster`
   - median `46.4`
   - p90 `90.1`
   - p99 `98.6`
   - max `99.9999`
3. `portfolio_hit_rate_top_decile`
   - median `0.0`
   - p90 `0.6667`
   - p99 `1.0`
   - max `1.0`
4. `portfolio_crown_jewel_index`
   - median `0.0319`
   - p99 `24.28`
   - max `3090.79`
5. `portfolio_current_threat_score`
   - median `0.0483`
   - p99 `1.816`
   - max `14299.07`
6. `portfolio_heritage_score`
   - median `0.0`
   - p90 `9.47`
   - p99 `101.95`
   - max `484497.78`

### Single-family portfolio artifact

Current audit result:

1. total portfolios: `3,034,400`
2. single-family portfolios: `1,589,496`
3. single-family portfolios with `portfolio_hit_rate_top_decile = 1.0`: `232,034`
4. single-family portfolios with `portfolio_avg_blocking_power >= 90`: `232,034`
5. single-family portfolios with non-zero `portfolio_crown_jewel_index`: `941,240`

This confirms that several current executive metrics are strongly distorted by very small portfolio size and should not be shown as clean strategic executive signals.

## Metric Decision Table

### Safe now

1. `portfolio_family_count_within_mega_cluster`
   - keep
   - count only
2. `portfolio_active_grant_family_count`
   - keep
   - count and ratio over in-scope families
3. `semantic_candidate_family_count`
   - keep
   - count and ratio over in-scope families
4. family-status split derived from current owner families:
   - pending / filing
   - active
   - abandoned
   - keep as counts plus ratios

### Keep, but relabel as unbounded indices

1. `portfolio_total_mass_score`
   - relabel to `Granted Blocking Mass`
2. `portfolio_current_threat_score`
   - relabel to `Granted Threat Mass`
3. `portfolio_heritage_score`
   - relabel to `Citation Heritage Mass`

Rules:

1. never present these as normalized scores,
2. never imply `0..100`,
3. mark as unbounded indices in tooltip/caveat text.

### Withhold from executive until upstream rebuild

1. `portfolio_avg_blocking_power_within_mega_cluster`
2. `portfolio_hit_rate_top_decile`
3. `portfolio_crown_jewel_index`

Reason:

All three are downstream of current family blocking-power rank contamination.

### Do not surface currently

1. `portfolio_opposition_rate`

Reason:

Current distribution is effectively flat zero in the serving mart and is not adding reliable executive signal.

## Immediate Serving Action

The current V2 executive surface should use:

1. in-scope family count,
2. pending / filing families,
3. active families,
4. abandoned families,
5. active grant families,
6. semantic candidate families,
7. granted blocking mass,
8. granted threat mass,
9. citation heritage mass.

And it should explicitly hide:

1. average blocking power,
2. top-decile hit rate,
3. crown jewel index.

## Relationship To The Silver/Gold Refactor

This audit confirms the needed layer boundary:

1. `silver` should hold raw analytic facts,
2. `gold` should hold normalized, stage-aware serving metrics,
3. executive-tab metrics must come from the corrected Gold layer only.

This audit should be treated as the serving acceptance gate before exposing rebuilt blocking-derived portfolio metrics again.

## Next Step

1. fix family blocking-power semantics for `pending_emerging`,
2. rebuild Gold family blocking power,
3. rebuild Gold portfolio summary,
4. rerun this audit,
5. only then reconsider returning `Avg Blocking Power`, `Top-Decile Hit Rate`, and `Crown Jewel Index` to the executive tab.

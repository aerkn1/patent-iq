# PatentIQ V2 Portfolio Current-State Audit And Remediation Plan

## Goal

Record the current state of portfolio-serving marts and define the clean remediation path for the V2 portfolio workspace.

This note should now be read together with the broader cross-surface serving-boundary audit in [63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md), which expands the same representation rules across family, publication, portfolio, and market surfaces.

This note answers four questions:

1. which portfolio views are truly point-in-time today,
2. which portfolio views are only current overlays,
3. which important portfolio surfaces are still missing despite already-available data,
4. what the next clean implementation order should be.

## Main Conclusion

Portfolio PIT is not absent.

It is uneven.

Current state:

1. `family` PIT is the strongest and most native layer,
2. `market` PIT is strong in classification and CPC trend lanes,
3. `portfolio` PIT exists for classification and compare,
4. current portfolio `field-timeseries` and current portfolio `market-context` are not true chronology lanes today.

This means the current V2 portfolio UI must separate:

1. historical PIT views,
2. current-state overlays,
3. forecast-derived views,

instead of letting them blur together under one generic “field history” interpretation.

## Direct Evidence From Current Artifacts

### Real PIT-safe or PIT-usable portfolio lanes

1. [gold_portfolio_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_classification_mix_pit.parquet)
   - owner-year WIPO/CPC exposure
   - `2007..2026`
   - usable with `current owner replay` caveat
2. [gold_portfolio_compare_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_compare_pit.parquet)
   - owner-year normalized compare lane
   - includes explicit caveat/support fields:
     - `historical_compare_safe`
     - `historical_owner_truth_supported`
     - `current_owner_bridge_replayed_to_history`
     - `historical_field_mix_supported`

### Not true chronology today

1. [gold_portfolio_field_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet)
   - currently only one distinct `snapshot_date` globally
   - current audit read: `2026-03-15`
2. [gold_portfolio_forecast_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet)
   - also only one distinct `snapshot_date` globally
   - current audit read: `2026-03-15`

Therefore:

1. `field-timeseries` should be treated as a current field-exposure overlay mart,
2. `market-context` should be treated as a current market-direction overlay mart,
3. neither should be presented as historical owner chronology.

## Family And Market PIT Read

### Family PIT

Family PIT remains the strongest historical foundation:

1. [silver_family_feature_snapshot_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit.parquet)
2. [silver_family_classification_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense.parquet)
3. [gold_family_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_mix_pit.parquet)

### Market PIT

Market PIT is also materially available:

1. [gold_market_cpc_trend_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_cpc_trend_pit.parquet)
2. [gold_cpc_importance_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_cpc_importance_pit.parquet)
3. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)

So the correct product statement is not:

1. portfolio PIT is unavailable,

but:

1. portfolio PIT is selectively available,
2. family and market PIT are stronger than portfolio PIT in current state,
3. the current portfolio field/market chronology surfaces are weaker than the portfolio classification/compare lanes.

## Missing Portfolio Views Despite Existing Data

The portfolio page is currently underusing the citation layer.

### Data already available for portfolio citation surfaces

#### Family-first V2 sources

1. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
   - `family_forward_citations_raw`
   - `family_forward_citations_clean`
   - `family_forward_citations_weighted`
   - `family_backward_patent_citation_count`
   - `family_backward_citations_clean`
   - `family_backward_npl_citation_count`
   - `family_adjusted_citation_score_raw`
2. [silver_family_feature_snapshot_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit.parquet)
   - `pre_asof_forward_citations_clean`
   - `pre_asof_forward_citations_weighted`
   - `pre_asof_unique_citing_family_count`
   - `pre_asof_citing_assignee_diversity`
3. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
   - `citation_date`
   - `citation_year`
   - `citing_assignee_name`
   - `citing_jurisdiction_code`
   - `citing_primary_wipo_field`
   - `citation_lethality_score`
4. [silver_family_citation_edges_clean.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges_clean.parquet)
   - clean family citation edge pool
   - usable for family-first forward/backward aggregation logic

#### Existing legacy portfolio citation marts

1. [portfolio_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/data_cache/portfolio_citation_metrics.parquet)
   - `94,931` owners
2. [portfolio_citation_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/data_cache/portfolio_citation_timeseries.parquet)
   - `95,051` owners

This confirms the portfolio citation gap is not a raw-data absence problem.

It is a serving-contract and product-integration gap.

### Missing or underpowered portfolio surfaces

The current V2 portfolio workspace is still missing:

1. current forward citation summary,
2. current backward citation summary,
3. NPL / science-grounding summary,
4. forward citation chronology,
5. citing-assignee attack momentum over time,
6. jurisdiction-sliced citation attack momentum,
7. field-sliced attacker momentum from the event ledger,
8. self-citation / intra-family-scrubbed ratios,
9. citing-assignee diversity and unique-citing-family summary,
10. backward crowdedness and dependency summary.

## Semantic Separation Required In The UI

### `Field Clusters`

This tab should be current-state and evidence-heavy.

It should answer:

1. where the portfolio is concentrated now,
2. which fields are currently heating or cooling,
3. who threatens the owner in those fields now.

Primary sources:

1. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
2. [gold_portfolio_field_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet)
   - current overlay only
3. [gold_portfolio_forecast_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet)
   - current overlay only
4. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)

### `Classification`

This tab should own historical WIPO/CPC chronology.

It should answer:

1. how the owner’s WIPO mix changed over time,
2. how the owner’s CPC mix changed over time,
3. which CPC groups gained or declined,
4. how concentration/diversification changed.

Primary sources:

1. [gold_portfolio_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_classification_mix_pit.parquet)
2. [silver_family_classification_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense.parquet)

### `Market Context`

This should be renamed conceptually to `Current Market Overlay`.

It is not historical PIT in current state.

### `Compare`

This should remain the normalized historical portfolio-shape tab.

It is the right historical portfolio summary lane today.

## Recommended Portfolio IA

Stable top-level tabs should become:

1. `Executive`
2. `Families`
3. `Citations`
4. `Field Clusters`
5. `Threats`
6. `Forecast`
7. `Classification`
8. `Compare`

### Why add `Citations`

Because a large share of the real available portfolio intelligence is citation-native and currently missing from the page.

`Citations` should become the home for:

1. forward citation summary,
2. backward / NPL summary,
3. forward citation chronology,
4. attacker momentum over time,
5. field-sliced and jurisdiction-sliced attack views,
6. citation hygiene / diversity / self-scrub indicators.

## Recommended Backend Contract Extensions

Next portfolio endpoints should include:

1. `GET /api/v1/portfolios/{owner_id}/citation-summary`
2. `GET /api/v1/portfolios/{owner_id}/citation-timeseries`
3. `GET /api/v1/portfolios/{owner_id}/citation-attackers`
4. `GET /api/v1/portfolios/{owner_id}/citation-jurisdictions`
5. `GET /api/v1/portfolios/{owner_id}/citation-fields`

Serving rules:

1. forward citation history can be PIT-first from family PIT + citation event ledger,
2. attacker momentum can be time-windowed from the enriched citation network,
3. backward citation views should initially stay current-summary-first unless a full owner-year backward mart is packaged.

## Current UI/Serving Corrections Required

Immediate corrections:

1. do not label `field-timeseries` as if it were a trustworthy historical portfolio timeline,
2. do not label `market-context` as if it were PIT chronology,
3. keep the `current owner replay` caveat visible in historical portfolio classification and compare views,
4. avoid claiming that `Field Clusters` and `Classification` are different historical sources when the current field tab is still partly falling back to classification chronology.

## Implementation Order

### Step 1

Correct the documentation and UI copy:

1. `Field Clusters` = current exposure + current overlay
2. `Classification` = historical WIPO/CPC chronology
3. `Market Context` = current market overlay

### Step 2

Add the `Citations` workspace from current data already available.
Current status: implemented in `frontend_v2` and `backend_v2` with `/citation-summary`, `/citation-timeseries`, and `/citation-attackers`.

### Step 3

Package a clean V2 portfolio citation mart from family-first V2 sources so the page no longer depends on legacy `data_cache` citation marts.

### Step 4

Only after that, decide whether a real multi-snapshot portfolio field-timeseries mart should be rebuilt for true portfolio chronology.

## Bottom Line

The portfolio page is not blocked by missing data.

It is blocked by incorrect separation of:

1. historical PIT,
2. current overlays,
3. citation intelligence that already exists but is not yet surfaced.

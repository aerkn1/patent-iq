# PatentIQ V2 Portfolio Citation Family Ranking And Filing Strength Plan

## Purpose

Define the implementation-ready plan for two portfolio product gaps:

1. a dedicated `most cited families in portfolio` ranking,
2. a first-class `filings over time` strength view.

This note is intentionally narrow and execution-oriented.

Primary references:

1. [33-patentiq-v2-portfolio-and-forecast-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md)
2. [60-patentiq-v2-portfolio-page-ui-design-spec.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/60-patentiq-v2-portfolio-page-ui-design-spec.md)
3. [64-patentiq-v2-citation-serving-refactor-execution-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md)
4. [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md)

## Product Decision

The product does not need a new top-level portfolio tab for these additions.

Placement:

1. `Most cited families` belongs in the `Citations` tab.
2. `Filing strength over time` belongs in the `Executive` tab.

Reasoning:

1. the first view is a citation-ranked family drill-down,
2. the second view is a portfolio strength / buildup narrative,
3. placing both in existing tabs avoids another IA split while still making each a first-class panel.

## Use-case Interpretation

### A. Most cited families in portfolio

This use case must answer:

1. which families in the owner portfolio receive the highest external citation pull,
2. which cited families are early-validated versus long-tail accumulated,
3. which families are citation-strong but legally weak or pending,
4. how the user can navigate from the portfolio into the underlying family workspace.

Important serving decision:

1. ranking must be family-first,
2. family citation totals must already include citations to family members,
3. default ranking must not use unstable citation-derived proxy scores as the headline sort.

### B. Filing strength over time

This use case must answer:

1. whether the owner built or lost filing momentum over time,
2. whether recent portfolio buildup is accelerating, flat, or cooling,
3. where filing peaks occurred,
4. how large the recent filing window is versus prior windows.

Important serving decision:

1. this is a historical strength view, not a forecast panel,
2. it must be based on family filing anchors, not publication spikes,
3. it must remain explicitly caveated as current-owner replay.

## Data Availability Assessment

### A. Citation family ranking

Already available upstream:

1. family-collapsed forward citation counts from `gold_family_citation_summary`
2. early-window citation counts such as `family_fwd_cits5` and `family_fwd_cits7`
3. family metadata from `gold_family_summary`
4. blocking proxy from `gold_family_blocking_power`
5. current owner bridge from `silver_family_owner_bridge` or serving `family_owner_bridge`

Conclusion:

1. no new Silver work is required,
2. this should be formalized as a dedicated Gold serving mart for predictable backend usage.

### B. Filing strength over time

Already available upstream:

1. family filing anchors via `family_priority_year`
2. family metadata in `gold_family_summary`
3. current owner-family bridge

Conclusion:

1. no new Bronze/Silver extraction is required for the first slice,
2. a dedicated Gold owner-year rollup is still preferred so backend routes do not reconstruct the logic ad hoc.

## Target Gold Marts

### 1. `gold_portfolio_citation_family_leaderboard.parquet`

Grain:

1. `owner_name_harmonized x docdb_family_id`

Required columns:

1. `owner_name_harmonized`
2. `docdb_family_id`
3. `family_priority_year`
4. `primary_wipo_field`
5. `family_composite_status`
6. `family_forward_citations_clean`
7. `family_forward_citations_weighted_raw`
8. `family_fwd_cits5`
9. `family_fwd_cits7`
10. `unique_citing_family_count`
11. `citing_assignee_diversity`
12. `family_ui_blocking_power_score`
13. `method_version`

Serving rules:

1. default sort is `family_forward_citations_clean desc`,
2. alternate sorts may include `family_fwd_cits5`, `family_forward_citations_weighted_raw`, and `family_ui_blocking_power_score`,
3. the mart must not surface `family_adjusted_citation_score_raw` directly.

### 2. `gold_portfolio_filing_timeseries.parquet`

Grain:

1. `owner_name_harmonized x filing_year`

Required columns:

1. `owner_name_harmonized`
2. `filing_year`
3. `family_filing_count`
4. `cumulative_family_count`
5. `rolling_3y_family_filing_count`
6. `prior_3y_family_filing_count`
7. `rolling_3y_change_pct`
8. `momentum_direction`
9. `method_version`

Serving rules:

1. `filing_year` must use the family filing anchor, not publication year,
2. one family is counted once,
3. `momentum_direction` is a descriptive band, not a modeled forecast.

## Backend Contract

### 1. `GET /api/v1/portfolios/{owner_id}/citation-families`

Purpose:

1. ranked most-cited family table inside the portfolio citation workspace

Query params:

1. `limit`
2. `offset`
3. `wipo_field`
4. `status`
5. `sort`

Response rows:

1. `family_id`
2. `family_priority_year`
3. `primary_field`
4. `status`
5. `forward_citations_clean`
6. `forward_citations_weighted`
7. `early_citations_5y`
8. `early_citations_7y`
9. `unique_citing_family_count`
10. `citing_assignee_diversity`
11. `blocking_score`

Required caveats:

1. family-member citations are collapsed to family level
2. current owner bridge is used for portfolio membership
3. blocking remains a proxy and is secondary to the citation ranking

### 2. `GET /api/v1/portfolios/{owner_id}/filing-timeseries`

Purpose:

1. portfolio buildup and filing momentum panel

Query params:

1. `year_from`
2. `year_to`

Response rows:

1. `year`
2. `family_filing_count`
3. `cumulative_family_count`
4. `rolling_3y_family_filing_count`
5. `prior_3y_family_filing_count`
6. `rolling_3y_change_pct`
7. `momentum_direction`

Required caveats:

1. current-owner replay
2. family-priority-year chronology
3. descriptive historical momentum, not forecast output

## Frontend Contract

### A. `Citations` tab

Add `PortfolioMostCitedFamiliesPanel`.

Layout:

1. keep summary and chronology at the top,
2. keep field/jurisdiction slices,
3. add `Most cited families` beneath the field/jurisdiction matrix and above attacker or threat detail.

Behavior:

1. table with pagination
2. exact WIPO field dropdown filter
3. lifecycle status filter
4. family link per row
5. default sort by forward citations

### B. `Executive` tab

Add `PortfolioFilingStrengthPanel`.

Layout:

1. place after summary cards / reliability and before or within the overview briefing band
2. compact enough for executive scan, but still chart-first

Behavior:

1. yearly filing count line or area chart
2. cumulative build line
3. side rail for `peak year`, `last 3y`, `vs prior 3y`, `momentum`
4. caveat copy visible near the chart

## Execution Order

1. update contracts and this plan note
2. build the two Gold marts
3. add backend repository, service, schema, and route support
4. add frontend API/types/panels
5. run audits on small, medium, and large portfolios

## Acceptance Criteria

1. a real owner portfolio returns a non-empty cited-family ranking when citation coverage exists
2. ranking reflects family-level citation totals, not publication-level noise
3. filing chronology reflects family-priority-year counts and avoids publication spikes
4. both panels behave with pagination / empty / caveat states
5. both panels preserve local and Azure-compatible serving semantics

# Field-Sliced Competitor Intelligence And Tech Trend Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must perform competitor intelligence using field-specific point-in-time rankings rather than generic portfolio-wide blocking scores.

## Core Principle

Competitors are defined by technology collisions, not by generic portfolio size.

A company becomes a true competitor when it collides with another company inside the same field, cluster, or WIPO sector at the same point in time.

This means PatentIQ should treat competitor discovery as a field-sliced, point-in-time ranking problem rather than a static portfolio-ranking problem.

## Why Generic Blocking Power Is Insufficient

## CTR-01: Generic Scores Cannot Drive Competitor Discovery

Requirement:
PatentIQ must not use only a generic overall blocking-power score to identify competitors.

Why:
Users care about who threatens them in their specific field, not who owns the largest abstract portfolio.

## CTR-02: Competitor Intelligence Must Be Sliced By Field

Requirement:
Competitor rankings must be computed within a specific WIPO field, CPC cluster, or equivalent technology slice.

## Two Leaderboards

## CTR-03: Current Threat Leaderboard

Requirement:
For each field and point in time, PatentIQ must support a leaderboard ranking companies by current enforceability-based field score.

Primary question answered:
“Who can block or sue us in this field today?”

## CTR-04: Historical Pioneer Leaderboard

Requirement:
For each field and point in time, PatentIQ must support a separate leaderboard ranking companies by heritage or historical-influence score.

Primary question answered:
“Who historically built the foundations of this field?”

## Point-In-Time Gold Mart

## CTR-05: Competitor Rankings Must Use A Snapshot Mart

Requirement:
PatentIQ should not rebuild field-level competitor rankings from raw documents at interactive query time.

Instead, it should persist a gold-layer time-series mart such as:

`portfolio_field_timeseries_mart`

Default recommendation:
Use monthly snapshots for competitor intelligence and annual rollups only for coarse strategic charts.

## CTR-06: Recommended Snapshot Grain

Recommended granularity:
1. one row per `snapshot_date`,
2. per `harmonized_assignee`,
3. per `wipo_field`,
4. with separate enforceability and heritage metrics.

## CTR-07: Recommended Columns

Recommended columns:
1. `snapshot_date`
2. `harmonized_assignee`
3. `wipo_field`
4. `active_family_count`
5. `enforceability_score`
6. `heritage_score`
7. `method_version`
8. `family_model`
9. `tech_trend_coefficient`
10. `snapshot_grain`

## Query Semantics

## CTR-08: Threat Leaderboards Order By Enforceability Score

Requirement:
Field-specific threat rankings should sort by `enforceability_score` at the requested snapshot date.

## CTR-09: Pioneer Leaderboards Order By Heritage Score

Requirement:
Field-specific pioneer rankings should sort by `heritage_score` at the requested snapshot date.

## CTR-10: Point-In-Time Queries Must Be Instant On The UI Path

Requirement:
The mart must be structured so the UI can answer questions like:
1. top threats in Batteries at `2023-12-31`,
2. top pioneers in Digital Communication at `2020-12-31`,
3. change in company dominance between two dates.

The UI should be able to answer these queries with a direct mart lookup plus sort, not a raw-document rebuild.

Related threat-network rule:
Competitor intelligence should also support citing-assignee attacker leaderboards built from the enriched forward-citation network rather than only from ownership-side portfolio strength.

Reference:
`citation-event-ledger-and-attacker-leaderboard-requirements.md`

## Bottom-Up Blocking Power Architecture

## CTR-11: Overall Blocking Power Must Be Summed From Field Scores

Requirement:
PatentIQ must not calculate a generic overall blocking-power score first and then divide it across fields.

Instead, it must:
1. calculate field-specific contributions first,
2. then sum them to derive the family or portfolio overall score.

Why:
Fields are not equally valuable at a given point in time.

## CTR-12: Tech Trend Coefficient Must Weight Field Value Over Time

Requirement:
The platform should calculate a time-varying trend multiplier for each WIPO field so a family’s enforceability contribution is amplified in rising sectors and discounted in stagnating sectors.

## CTR-13: Tech Trend Coefficient Formula

Recommended formula:

`Tech Trend Coefficient(field, t) = 1 + ((Global Filings(field, t) - Global Filings(field, t-1)) / Global Filings(field, t-1))`

Interpretation:
1. positive growth boosts field importance,
2. contraction reduces field importance,
3. the value of legal monopolies changes with sector momentum.

## CTR-14: Add A Global Tech Trends Timeseries Table

Requirement:
The silver layer should include a table such as:

`global_tech_trends_timeseries`

with year-over-year growth metrics for WIPO fields derived from raw patent-family filing activity.

At minimum this table should contain:
1. `snapshot_date` or `year`,
2. `wipo_field`,
3. `global_family_filings`,
4. `prior_period_global_family_filings`,
5. `growth_rate`,
6. `tech_trend_coefficient`,
7. `counting_unit`,
8. `family_model`.

## CTR-14A: Localized Jurisdiction-Tech Trends Are A Higher-Precision Extension

Requirement:
PatentIQ should treat global field coefficients as the base model and support a jurisdiction-tech localized coefficient layer as a higher-precision extension where data coverage allows.

Reference:
`jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`

Parallel-engine rule:
The localized trend engine must not replace the global trend engine, because the product still needs macro field-growth views for market intelligence and executive planning.

Reference:
`parallel-global-and-local-trend-engines-requirements.md`

## Field-Specific Family Scoring

## CTR-15: Base Enforceability Must Be Computed Before Field Splitting

Requirement:
For each family and point in time, compute the base enforceability score from:
1. market weighting,
2. kind-code or normalized legal-stage weighting,
3. current active legal status.

## CTR-16: Split Family Score By WIPO Fraction

Requirement:
After computing the base enforceability score, allocate it across the family’s touched WIPO fields using the field fraction logic already defined in the WIPO contribution note.

## CTR-17: Apply Tech Trend Coefficient Per Field

Requirement:
Each field slice of the family’s score must then be multiplied by the relevant field’s trend coefficient at that date.

Refinement:
If localized jurisdiction-tech coefficients are available, they should be preferred over global field-only coefficients for enforceability scoring.

## CTR-18: Bottom-Up Overall Blocking Power Formula

Recommended structure:

`Overall Blocking Power(family, t) = SUM(Base Score(t) * Field Fraction(i) * Tech Trend Coefficient(i, t))`

Why:
This makes the overall score responsive to shifts in the economic and strategic relevance of each field.

Implementation rule:
Do not calculate a generic overall score and then apportion it across fields. The order must be field-first, then overall rollup.

## 3D Matrix Requirement

## CTR-19: Data Model Must Support Time X Tech X Score

Requirement:
The data model must support analysis across:
1. time,
2. technology field,
3. score type.

At minimum:
1. enforceability score,
2. heritage score,
3. optionally overall score.

## CTR-20: Support Pivoting And Heatmaps

Requirement:
The product should be able to render a competitor’s field-level strength over time as:
1. line charts,
2. heatmaps,
3. field-dominance tables,
4. field-pivot alerts.

These views should support both:
1. enforceability mode for current legal threat,
2. heritage mode for historical innovation leadership.

## Product And Alerting Expectations

## CTR-21: Competitor Pivot Detection

Requirement:
The product should support identifying when a company is shifting its enforceability strength from one field to another across time.

## CTR-22: Sleeping Giant Alerts

Requirement:
If a family sits in a field whose trend coefficient sharply rises, the platform should be able to surface that family or owner as a newly important threat even if the legal footprint has not changed recently.

## Mapping To Existing Requirements

This note sharpens and extends several prior notes.

### Overlaps With Existing Docs

1. `wipo-field-contribution-timeseries-requirements.md`
2. `citation-semantics-and-tech-field-mapping-requirements.md`
3. `global-legal-status-normalization-and-influence-evaluation-requirements.md`
4. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
5. `market-analysis-additional-features-nonoverlap.md`
6. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`
7. `parallel-global-and-local-trend-engines-requirements.md`

### Net-New Additions

1. field-sliced competitor leaderboards,
2. bottom-up overall blocking power from field scores,
3. field-specific tech trend coefficient,
4. `portfolio_field_timeseries_mart`,
5. `global_tech_trends_timeseries`,
6. field-collision-based competitor discovery.
7. attacker leaderboards from enriched citation events.

## Delivery Priority

### P0

1. field-level enforceability and heritage leaderboards,
2. `portfolio_field_timeseries_mart`,
3. field-first then overall-score aggregation,
4. `global_tech_trends_timeseries`.

### P1

1. competitor pivot visualizations,
2. sleeping-giant alerts,
3. field heatmaps and dominance views.

### P2

1. deeper scenario forecasting on competitor field shifts,
2. more advanced cross-field collision analytics.

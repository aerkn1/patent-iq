# WIPO Field Contribution Timeseries Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must measure a patent family's contribution to a technology field over time, separating:

1. current enforceability contribution,
2. historical heritage contribution.

## Core Principle

A family's contribution to an industry field is not static. It changes over time based on:

1. which kind-code stage the family has reached,
2. whether the family is currently active,
3. which markets remain enforceable,
4. how much adjusted citation influence the family has accumulated.

## Two Different Contribution Scopes

## WCR-01: Enforceability Scope

Requirement:
The enforceability contribution must represent how much legally enforceable blocking presence the family contributes to a technology field at a specific point in time.

This scope is:
1. time-varying,
2. highly sensitive to grants, lapses, revocations, and expiry,
3. driven by kind-code stage and market weighting.

## WCR-02: Heritage Scope

Requirement:
The heritage contribution must represent how much historical inventive influence the family contributes to a technology field, regardless of whether the family is still active today.

This scope is:
1. cumulative,
2. citation-driven,
3. not zeroed out by legal death.

## The Role Of Kind Codes

## WCR-03: Kind Codes Drive Enforceability Weight

Requirement:
At any selected point in time, the effective legal contribution of a family to a WIPO field must be driven by the highest legally meaningful kind-code stage the family has achieved and still maintains at that date.

Illustrative semantics:
1. all-`A` family: low contribution because it is still pending,
2. standard `B` family: normal enforceable contribution,
3. EP `B2` or equivalent resilience signal: elevated contribution because the right is battle-tested.

## WCR-04: Kind Codes Do Not Directly Drive Heritage Weight

Requirement:
For historical heritage views, citation-weighted influence is primary. Kind codes may still affect the historical narrative, but they should not zero out foundational influence merely because the family never became or no longer remains enforceable.

## Enforceability Contribution Calculation

## WCR-05: Base Fraction Must Be Computed From Unique WIPO Fields

Requirement:
If a family maps to `N` unique WIPO fields after the full CPC/IPC deduplication funnel, its base field fraction is:

`1 / N`

for each field in the enforceability contribution calculation.

## WCR-06: Active Status Must Be Evaluated At The Requested Date

Requirement:
Before computing enforceability contribution, the engine must reconstruct whether the family has any active enforceable rights at the selected point in time.

If no active enforceable right exists, enforceability contribution must be `0` for that date.

## WCR-07: Max Active Stage Must Be Determined At The Requested Date

Requirement:
The engine must determine the strongest active normalized legal stage at the selected date using the legal event ledger and kind-code normalization layer.

## WCR-08: Market Weight Must Be Applied Using Current Active Coverage

Requirement:
The enforceability contribution must use market weighting only for the jurisdictions that remain active at the selected point in time.

## WCR-09: Dynamic Enforceability Contribution Formula

Recommended formula:

`Dynamic Field Contribution = Base Fraction * (Kind Code Weight * Market Weight)`

Interpretation:

1. base fraction allocates the family across touched fields,
2. kind-code weight captures legal maturity or resilience,
3. market weight captures commercial significance of active geographies.

## WCR-10: Enforceability Contribution Must Fall When Coverage Falls

Requirement:
If active grant coverage shrinks because jurisdictions lapse or expire, the family's enforceability contribution to the field must decline immediately in the time series.

## Heritage Contribution Calculation

## WCR-11: Heritage Base Fraction Uses The Same Field Allocation

Requirement:
The family’s heritage contribution to each touched WIPO field should start from the same `1 / N` base fraction across unique mapped fields.

## WCR-12: Heritage Weight Uses Adjusted Citation Influence

Requirement:
The heritage contribution should be driven by an adjusted family-level citation score such as clean-room forward impact, RCF, or another cohort-normalized influence metric.

Dimensionality rule:
This heritage contribution remains a global family-field measure and should not be converted into a defender-side jurisdiction-specific output.

Trend-context rule:
If trend context is used to scale or interpret heritage importance, it should come from the global field trend layer rather than localized enforceability trends.

## WCR-13: Heritage Contribution Formula

Recommended formula:

`Heritage Field Contribution = Base Fraction * Adjusted Citation Score`

Why:
This preserves the role of a foundational but no-longer-enforceable family in historical innovation analysis.

Reference:
`score-dimensionality-and-citation-weighting-requirements.md`

OECD extension:
Generality, originality, and radicalness should be available as complementary “nature of innovation” descriptors alongside the main heritage and enforceability lines.

Reference:
`oecd-quality-nature-of-innovation-requirements.md`

## WCR-14: Dead Families Can Still Dominate Heritage Slices

Requirement:
A dead or abandoned family may contribute `0` to enforceability but still contribute materially to heritage if its citation influence is high.

## Time-Series Architecture

## WCR-15: Field Contribution Must Be Stored As A Time Series

Requirement:
PatentIQ should persist yearly or periodic snapshots of field contribution rather than recomputing the full historical field-distribution state from scratch for every UI interaction.

## WCR-16: Gold Mart For WIPO Field Contribution

Requirement:
Create a gold-layer mart such as:

`wipo_industry_contributions_timeseries`

Recommended granularity:
1. one row per `docdb_family_id`,
2. per `year_end` or other agreed snapshot date,
3. per `wipo_field_name`.

## WCR-17: Recommended Gold Mart Columns

Recommended columns:
1. `snapshot_year`
2. `docdb_family_id`
3. `wipo_field_name`
4. `base_fraction`
5. `heritage_contribution_score`
6. `enforceability_contribution_score`
7. `max_active_stage`
8. `active_market_weight`
9. `is_active_on_snapshot`
10. `family_model`
11. `method_version`

## Query And UI Expectations

## WCR-18: Field-Dominance Charts Must Support Historical Time Windows

Requirement:
If the user asks how a company's dominance in a WIPO field changed over time, the UI should query the timeseries mart rather than relying on a single present-day score.

## WCR-19: Enforceability And Heritage Lines Must Be Separable

Requirement:
The UI should be able to plot:
1. enforceability contribution over time,
2. heritage contribution over time,

as separate or toggleable lines.

## WCR-20: Contribution Drops Must Be Explainable

Requirement:
When a field-contribution score drops materially, the product should be able to explain whether the cause was:
1. lapse,
2. expiry,
3. reduced active market coverage,
4. loss of grant-stage status,
5. normalization change.

## Relationship To Existing Notes

This note sharpens and operationalizes prior requirements.

### Overlaps With Existing Docs

1. `citation-semantics-and-tech-field-mapping-requirements.md`
2. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
3. `legal-status-lifecycle-and-point-in-time-analytics-requirements.md`
4. `global-legal-status-normalization-and-influence-evaluation-requirements.md`
5. `family-level-collapse-and-metric-calculation-requirements.md`
6. `score-dimensionality-and-citation-weighting-requirements.md`
7. `global-vs-local-trend-role-allocation-requirements.md`
8. `oecd-quality-nature-of-innovation-requirements.md`

### Net-New Additions

1. explicit heritage-vs-enforceability contribution formulas by WIPO field,
2. yearly family-field contribution mart design,
3. field-level dynamic “slice of the pie” architecture,
4. direct linkage between kind-code stage progression and time-series field dominance.

## Delivery Priority

### P0

1. field-level base fraction logic,
2. enforceability contribution formula,
3. heritage contribution formula,
4. yearly gold mart design,
5. separation of heritage and enforceability lines in analytics.

### P1

1. explanation layer for score changes,
2. field-dominance comparison by owner and year,
3. chart-ready API contract.

### P2

1. sub-annual snapshots,
2. predictive field dominance projections.

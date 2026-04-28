# Parallel Global And Local Trend Engines Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must run global and localized technology-trend engines in parallel so the platform can support both high-level market intelligence and jurisdiction-specific asset valuation.

## Core Principle

PatentIQ must not replace global trend intelligence with localized trend intelligence.

The platform should operate two parallel trend engines:
1. a macro global trend engine for executive and market-intelligence questions,
2. a micro localized trend engine for valuation, blocking power, and jurisdiction-specific threat analysis.

These two engines serve different personas and different product surfaces.

## The Two Parallel Trend Engines

## PTE-01: Global Trend Engine Supports Macro Market Intelligence

Requirement:
PatentIQ should maintain a global trend engine that tracks filing momentum by:
1. time,
2. technology field.

Illustrative dimensions:
`time x tech field`

Primary purpose:
Support high-level landscape and market-intelligence questions.

## PTE-02: Local Trend Engine Supports Micro Valuation

Requirement:
PatentIQ should maintain a localized trend engine that tracks filing momentum by:
1. time,
2. technology field,
3. jurisdiction.

Illustrative dimensions:
`time x tech field x jurisdiction`

Primary purpose:
Support valuation, competitor blocking power, and jurisdiction-specific enforceability analysis.

## PTE-03: Global And Local Engines Must Coexist

Requirement:
The product must not treat the localized trend layer as a replacement for the global layer.

Why:
Removing the global layer would prevent users from asking broad strategic questions about which fields are growing fastest worldwide.

## Silver-Layer Tables

## PTE-04: Maintain A Global Trends Table

Requirement:
The silver layer should include a table such as:

`global_tech_trends_timeseries`

for macro field-level growth analysis.

## PTE-05: Maintain A Local Trends Table

Requirement:
The silver layer should include a table such as:

`local_tech_trends_timeseries`

or the equivalent localized trend table already defined elsewhere for jurisdiction-field growth analysis.

## PTE-06: Both Tables Can Be Derived From The Same Base Filing Data

Requirement:
Engineering should derive both global and local trend tables from the same family-level filing base so they remain methodologically aligned.

Implementation note:
DuckDB can compute both outputs efficiently by:
1. separate aggregate queries,
2. `ROLLUP`,
3. `GROUPING SETS`,
4. or other equivalent aggregation strategies.

## Product Surface Mapping

## PTE-07: Global Trends Power Market Intelligence Modules

Requirement:
The global trend engine should power product surfaces such as:
1. market intelligence,
2. landscape analysis,
3. executive sector trend dashboards,
4. global whitespace discovery.

## PTE-08: Local Trends Power Valuation And Blocking Modules

Requirement:
The localized trend engine should power product surfaces such as:
1. asset valuation,
2. blocking-power scoring,
3. competitor threat analysis,
4. jurisdiction-specific risk and opportunity views.

Role-allocation rule:
For pure accuracy in current enforceability and blocking-power scoring, localized trends should be the direct scoring input rather than blended with global averages.

Reference:
`global-vs-local-trend-role-allocation-requirements.md`

## Persona Mapping

## PTE-09: Global Trends Serve Executive Planning

Requirement:
The global trend view should support users who need to understand broad industry direction before making high-level R&D or portfolio-allocation decisions.

## PTE-10: Local Trends Serve Transactional And Legal Evaluation

Requirement:
The localized trend view should support users who need to value, defend, license, or challenge concrete assets in specific countries.

## Arbitrage And Whitespace Opportunity

## PTE-11: The Platform Should Compare Global Versus Local Growth

Requirement:
PatentIQ should support comparing global trend growth and local trend growth for the same field to identify geographic arbitrage or whitespace opportunity.

## PTE-12: Support Global-Local Delta Metrics

Requirement:
The data model should support calculating a delta such as:
1. local growth minus global growth,
2. local trend coefficient versus global trend coefficient,
3. local filing acceleration relative to global sector growth.

## PTE-13: Arbitrage Insights Should Be Productizable

Requirement:
The platform should be able to surface insights such as:
1. a field booming globally but under-covered by the user in a rising jurisdiction,
2. a field stagnating globally but accelerating sharply in a specific geography,
3. competitor migration into a new jurisdiction before the user has coverage there.

## Consistency Rules

## PTE-14: Global Trends Must Remain Family-Count Based

Requirement:
The global trend engine must use family-level counting rather than document counts.

## PTE-15: Local Trends Must Also Remain Family-Count Based

Requirement:
The localized trend engine must also use family-level counting so the two trend layers are directly comparable.

## PTE-16: Trend Engines Must Share Field Taxonomy

Requirement:
Both global and local engines should use the same normalized field taxonomy such as WIPO 35 or the agreed equivalent.

## PTE-17: Trend Engines Must Share Time Semantics

Requirement:
Both global and local trend tables should use aligned time anchors and snapshot semantics so deltas remain interpretable.

## Relationship To Existing Notes

This note clarifies how the platform should keep macro and micro trend logic in parallel rather than forcing one to replace the other.

### Overlaps With Existing Docs

1. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
2. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`
3. `market-analysis-additional-features-nonoverlap.md`
4. `score-dimensionality-and-citation-weighting-requirements.md`
5. `global-vs-local-trend-role-allocation-requirements.md`

### Net-New Additions

1. parallel global and local trend-engine architecture,
2. explicit module-to-engine mapping,
3. persona-to-engine mapping,
4. global-local delta and arbitrage analytics,
5. requirement to preserve both trend tables in silver layer.

## Delivery Priority

### P0

1. global trend table,
2. local trend table,
3. aligned field and time semantics,
4. module routing between macro and micro trend use cases.

### P1

1. global-local delta metrics,
2. arbitrage insight generation,
3. UI comparisons of global and local growth for selected fields.

### P2

1. advanced geographic whitespace scoring,
2. predictive competitor migration analytics.

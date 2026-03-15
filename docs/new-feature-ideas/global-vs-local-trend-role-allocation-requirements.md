# Global Vs Local Trend Role Allocation Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Clarify exactly where global technology trends and localized jurisdiction-tech trends are allowed to influence PatentIQ metrics, so macro landscaping and micro asset valuation remain accurate and are not conflated.

## Core Principle

PatentIQ must assign different jobs to:
1. global 3D field trends,
2. localized 4D jurisdiction-tech trends.

The platform should not use a global average to score the current blocking power of a local legal right.

At the same time, the platform should not discard the global trend engine, because it is required for macro landscaping, relative hotspot analysis, and heritage-context scaling.

## Division Of Labor

## GLA-01: Current Market Threat Uses Strictly Localized Trends

Requirement:
For current market threat, blocking power, and asset valuation of a specific family or portfolio, PatentIQ should use strictly localized jurisdiction-tech trend values.

Why:
The commercial blocking value of a right is constrained by the local market where that right is enforceable.

## GLA-02: Global Trends Must Not Directly Boost Local Enforceability Scores

Requirement:
PatentIQ must not directly boost a jurisdiction-specific enforceability or blocking-power score using only global field momentum.

Why:
If a field is booming globally but stagnant in a specific jurisdiction, a right in that jurisdiction should reflect its local commercial reality.

## GLA-03: Global Trends Power Pure Market Landscaping

Requirement:
Global field trends should remain the primary trend layer for macro market-landscaping and executive sector-overview modules.

Examples:
1. fastest-growing global WIPO fields,
2. declining global sectors,
3. global field momentum timelines,
4. top macro industry shifts.

## GLA-04: Local Trends Power Pure Asset Valuation

Requirement:
Localized jurisdiction-tech trends should remain the primary trend layer for:
1. family valuation,
2. portfolio blocking power,
3. jurisdiction-specific threat scoring,
4. legal-commercial asset assessment.

## Relative Momentum And Arbitrage

## GLA-05: Global Trends Provide The Baseline For Relative Hotspot Analysis

Requirement:
PatentIQ should use global trends as the baseline against which localized trends are compared.

Why:
This enables the product to distinguish:
1. merely average local growth,
2. truly exceptional local acceleration relative to global conditions.

## GLA-06: Relative Hotspot Index Should Be Supported

Requirement:
The platform should support a derived metric such as:

`Relative Hotspot Index = Local Trend / Global Trend`

or an equivalent global-local comparison measure.

## GLA-07: Relative Hotspot Views Belong To Market Intelligence, Not Core Blocking Power

Requirement:
The relative hotspot or arbitrage metric should be exposed as a separate market-intelligence or whitespace signal, not silently folded into the local enforceability score.

## GLA-08: Geographic Whitespace Alerts Should Use Global-Local Delta

Requirement:
The product should support alerts such as:
1. a field is accelerating in a specific jurisdiction faster than the global average,
2. competitors are shifting filings into a jurisdiction where the user lacks coverage,
3. local growth is materially outpacing global sector growth.

## Heritage And Pioneer Scoring

## GLA-09: Heritage Remains Global In Scope

Requirement:
Historical pioneer and heritage metrics should remain global family-field signals rather than jurisdiction-fragmented outputs.

## GLA-10: Global Trends May Contextualize Heritage Importance

Requirement:
PatentIQ may use global field momentum to scale or contextualize the strategic importance of a heritage score.

Interpretation:
A historically pioneering family in a field that is now globally surging may deserve a higher present-day heritage significance than an equally pioneering family in a field that is globally fading.

## GLA-11: Heritage Scaling Must Not Leak Into Local Enforceability

Requirement:
If global trend context is used to amplify or contextualize heritage, that effect must stay within heritage-oriented views and must not silently bleed into jurisdiction-specific enforceability scoring.

## Product Surface Mapping

## GLA-12: Market Intelligence Uses Global Trend Views

Requirement:
Modules such as landscape analysis, executive dashboards, and broad field-comparison surfaces should default to global field trends.

## GLA-13: Asset Valuation Uses Local Trend Views

Requirement:
Modules such as asset valuation, blocking-power scoring, and competitor family threat cards should default to localized jurisdiction-tech trend views.

## GLA-14: Delta Views Compare The Two

Requirement:
Hotspot maps, whitespace maps, and geographic-arbitrage views should explicitly compare local and global trend layers rather than pretending they are the same metric.

## Consistency Rules

## GLA-15: Macro Economics Must Not Be Mistaken For Micro Asset Value

Requirement:
The platform must avoid conflating:
1. global field growth,
2. local legal-commercial blocking value.

## GLA-16: Local Accuracy Takes Precedence In Valuation

Requirement:
When scoring a specific enforceable asset, localized trend accuracy must take precedence over global macro simplification.

## GLA-17: Global Context Takes Precedence In Landscaping

Requirement:
When summarizing the broader market or industry terrain, global trend context must take precedence over localized valuation detail.

## Relationship To Existing Notes

This note clarifies how earlier trend, heritage, and blocking-power rules should be allocated across product modules.

### Overlaps With Existing Docs

1. `parallel-global-and-local-trend-engines-requirements.md`
2. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`
3. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
4. `score-dimensionality-and-citation-weighting-requirements.md`
5. `wipo-field-contribution-timeseries-requirements.md`

### Net-New Additions

1. strict rule that local trends alone drive current blocking-power accuracy,
2. global trends as macro-landscaping layer,
3. relative hotspot index concept,
4. heritage scaling by global field momentum,
5. explicit module-level division of labor.

## Delivery Priority

### P0

1. local-only trend use for enforceability scoring,
2. global-only trend use for macro landscape views,
3. explicit separation of the two in product definitions.

### P1

1. relative hotspot index,
2. global-local delta surfaces,
3. heritage-context scaling rules.

### P2

1. advanced arbitrage ranking,
2. richer executive-to-asset drill-down flows.

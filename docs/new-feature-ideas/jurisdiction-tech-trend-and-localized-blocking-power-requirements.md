# Jurisdiction-Tech Trend And Localized Blocking Power Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Refine overall blocking-power and enforceability scoring so PatentIQ values patents and families using localized technology trends at the jurisdiction level rather than only global field-level trend coefficients.

## Core Principle

The commercial and strategic value of a patent right depends on:
1. its legal stage,
2. the jurisdiction where it is enforceable,
3. the technology field it covers,
4. the local momentum of that field inside that jurisdiction.

This means a field-level global trend coefficient is useful but incomplete. PatentIQ should support a localized jurisdiction-by-field trend layer for higher-precision blocking-power and enforceability scoring.

## Why Localized Trend Weighting Is Needed

## JTR-01: Global Field Trend Alone Is Not Sufficient

Requirement:
PatentIQ should not assume that the same technology field has the same strategic weight in every jurisdiction.

Why:
Some jurisdictions are the true manufacturing, commercialization, or litigation hubs for a specific field, while others are not.

## JTR-02: Jurisdiction And Technology Must Be Valued Together

Requirement:
For enforceability scoring, the platform should model the intersection of:
1. jurisdiction market weight,
2. jurisdiction-specific legal enforceability,
3. technology-field momentum in that same jurisdiction.

## 4D Tensor Architecture

## JTR-03: The Data Model Must Support Time X Tech X Jurisdiction X Score

Requirement:
The scoring architecture should support a 4D analytical structure across:
1. time,
2. technology field,
3. jurisdiction,
4. score.

Interpretation:
This is a refinement of the earlier 3D `time x tech x score` model, not a contradiction of it.

Boundary rule:
This 4D structure applies to jurisdiction-aware enforceability and blocking-power inputs. It must not be forced onto heritage or defender-side citation influence outputs.

Reference:
`score-dimensionality-and-citation-weighting-requirements.md`

## JTR-04: Localized Coefficient Volume Is Operationally Safe

Requirement:
Engineering may treat this as a modest coefficient table expansion rather than a performance risk.

Implementation implication:
DuckDB should comfortably handle a jurisdiction-tech trend table on the order of tens of thousands of rows for MVP use.

## Localized Trend Coefficient

## JTR-05: Compute Trend By Jurisdiction And Field

Requirement:
PatentIQ should calculate localized technology trend coefficients by grouping patent-family filing activity by:
1. jurisdiction,
2. WIPO field or equivalent normalized field,
3. time period.

## JTR-06: Localized Trend Formula

Recommended formula:

`Local Trend Coefficient(field, jurisdiction, t) = 1 + ((Local Filings(field, jurisdiction, t) - Local Filings(field, jurisdiction, t-1)) / Local Filings(field, jurisdiction, t-1))`

Interpretation:
1. positive growth boosts local field importance,
2. contraction reduces local field importance,
3. field value becomes location-sensitive rather than globally flat.

## JTR-07: Local Trend Inputs Must Be Family-Count Based

Requirement:
The localized trend calculation should use family-level filing counts rather than document counts so A/B/C lifecycle noise does not distort local growth rates.

## Silver-Layer Data Requirement

## JTR-08: Add A Jurisdiction-Tech Trends Timeseries Table

Requirement:
The silver layer should include a table such as:

`jurisdiction_tech_trends_timeseries`

to store localized technology growth metrics.

## JTR-09: Recommended Columns

Recommended columns:
1. `snapshot_date` or `year`,
2. `jurisdiction_code`,
3. `wipo_field`,
4. `local_family_filings`,
5. `prior_period_local_family_filings`,
6. `local_growth_rate`,
7. `local_trend_coefficient`,
8. `counting_unit`,
9. `family_model`,
10. `method_version`.

## Blocking Power Redefinition

## JTR-10: Family Blocking Power Must Be Built From Jurisdiction-Level Rights

Requirement:
For localized blocking-power scoring, PatentIQ should calculate the contribution of each active jurisdictional branch of the family rather than starting from a single family-wide base score.

Why:
The same family can be strategically dominant in one country and marginal in another.

## JTR-11: Document-Level Branches Still Roll Up To The Family

Requirement:
Even though scoring becomes more granular, the final analytics unit remains the family.

Implementation rule:
Use document or branch-level rights only as inputs to family-level aggregation, not as the default reporting unit.

## JTR-12: Localized Family Blocking Power Formula

Recommended structure:

`Overall Blocking Power(t) = SUM over jurisdictions j and fields i of (Stage Multiplier(j, t) * Market Weight(j) * WIPO Fraction(i) * Local Trend Coefficient(i, j, t))`

Interpretation:
1. stage multiplier captures enforceability strength,
2. market weight captures jurisdiction commercial importance,
3. WIPO fraction allocates the family across fields,
4. localized trend captures how hot that field is in that jurisdiction.

## JTR-13: Stage Multiplier Must Come From The Normalized Legal Stage Layer

Requirement:
The jurisdiction-level stage input must come from the jurisdiction-aware kind-code normalization table rather than raw kind-code assumptions.

## JTR-14: Market Weight Must Come From Tiered Market Weighting

Requirement:
The jurisdiction-level market input must come from the tiered market weighting table or its successor weighting layer.

## JTR-15: WIPO Fraction Must Respect Existing Deduplication Rules

Requirement:
The field-allocation term must use the same WIPO field mapping and fraction rules already defined for tech breadth and field-contribution analytics.

## Enforceability Score Refinement

## JTR-16: Enforceability Score Should Be Localized When Data Supports It

Requirement:
If the required tables are available, the enforceability score should use jurisdiction-tech localized coefficients instead of only a global field coefficient.

Allocation rule:
For current market-threat and blocking-power accuracy, localized values should be treated as the primary scoring input, not merely a refinement of global averages.

Reference:
`global-vs-local-trend-role-allocation-requirements.md`

## JTR-17: Global Field Coefficients Remain A Valid Fallback

Requirement:
If localized jurisdiction-tech coefficients are missing for a slice, the engine may fall back to the global field coefficient rather than failing the score.

This fallback must be explicit in metadata.

Architecture rule:
The global trend layer should also remain a first-class product engine for macro market intelligence rather than existing only as a fallback for localized valuation.

Reference:
`parallel-global-and-local-trend-engines-requirements.md`

## JTR-18: Score Metadata Must Expose Coefficient Mode

Requirement:
Any API or mart using this logic should expose whether the score was built using:
1. localized jurisdiction-tech coefficients,
2. global field coefficients,
3. a mixed fallback mode.

Related normalization rule:
The raw absolute score generated by this localized formula should remain separate from any percentile-ranked UI score.

Reference:
`blocking-power-score-normalization-and-percentile-ranking-requirements.md`

## Product And UI Expectations

## JTR-19: Support Geographic Threat Maps

Requirement:
The frontend should be able to render a world or regional threat map showing where a company’s rights are most strategically dangerous after combining:
1. legal enforceability,
2. jurisdiction market weight,
3. localized field momentum.

## JTR-20: Field Maps Must Be Slice-Aware

Requirement:
If a user selects a field such as Semiconductors, the map should show field-specific threat by jurisdiction rather than a generic total portfolio heatmap.

## JTR-21: Localized Threat Visualization Must Remain Explainable

Requirement:
Any UI or export should be able to explain the jurisdictional score using visible components such as:
1. legal stage,
2. market weight,
3. field fraction,
4. local trend coefficient.

## Relationship To Existing Notes

This note refines several prior requirements rather than replacing them.

### Overlaps With Existing Docs

1. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
2. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
3. `global-legal-status-normalization-and-influence-evaluation-requirements.md`
4. `wipo-field-contribution-timeseries-requirements.md`
5. `kind-code-normalization-and-tiered-market-weighting-build-guide.md`
6. `blocking-power-score-normalization-and-percentile-ranking-requirements.md`
7. `score-dimensionality-and-citation-weighting-requirements.md`
8. `parallel-global-and-local-trend-engines-requirements.md`
9. `global-vs-local-trend-role-allocation-requirements.md`

### Net-New Additions

1. jurisdiction-by-field localized trend coefficients,
2. 4D blocking-power tensor model,
3. jurisdiction-level branch contribution to family blocking power,
4. `jurisdiction_tech_trends_timeseries`,
5. geographic threat-map support.

## Delivery Priority

### P0

1. localized coefficient table design,
2. family-level formula updated to accept jurisdiction-tech coefficients,
3. explicit fallback from local to global coefficient mode,
4. score metadata for coefficient provenance.

### P1

1. geographic threat maps,
2. jurisdiction-level threat decomposition,
3. field-specific global-versus-local trend comparison views.

### P2

1. more advanced manufacturing-hub modeling,
2. scenario analysis on shifting local market hotspots.

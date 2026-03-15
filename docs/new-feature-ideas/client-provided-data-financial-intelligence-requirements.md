# Client-Provided Data Financial Intelligence Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ should optionally accept highly aggregated client-provided business inputs so the platform can evolve from pure patent intelligence into business and financial intelligence without forcing clients to upload raw sensitive financial systems data.

## Core Principle

PatentIQ should treat client financial integration as:
1. optional,
2. aggregation-first,
3. low-risk,
4. client-controlled,
5. separable from the core public patent engine.

The platform should ask for only the minimum structured inputs needed to unlock high-value business use cases rather than demanding raw ERP, P&L, or product-margin data.

## Security And Trust Model

## CFD-01: Client Financial Data Must Be Optional

Requirement:
All financially enriched workflows should be optional overlays on top of the public patent-intelligence engine rather than required inputs.

## CFD-02: Prefer Aggregated Inputs Over Raw Financial Systems Data

Requirement:
PatentIQ should request highly aggregated business inputs such as:
1. product revenue by product line,
2. average maintenance-cost assumptions,
3. R&D spend by year and WIPO field,

instead of raw internal accounting ledgers.

## CFD-03: Prefer Client-Side Local Processing For Sensitive Inputs

Requirement:
When feasible, joins between sensitive client business data and patent scores should execute locally in the client environment rather than on PatentIQ servers.

## CFD-04: DuckDB WASM Is The Preferred Security Pattern

Requirement:
The preferred architecture for sensitive business-data enrichment is:
1. backend computes public patent metrics,
2. clean patent metric tables are sent to the client,
3. the client uploads optional business CSVs locally,
4. DuckDB WASM or equivalent local processing joins the datasets in-browser,
5. sensitive financial rows never need to be persisted server-side.

## Use Case 1: Revenue At Risk

## CFD-05: Support Product-To-Family Revenue Mapping

Requirement:
PatentIQ should support an optional product-to-family mapping dataset that links client products to protected DOCDB families and a rough annual revenue figure.

## CFD-06: Preferred Input Format Is CSV

Recommended CSV structure:
1. `product_sku`
2. `product_name`
3. `annual_revenue_usd`
4. `linked_docdb_family_ids`

## CFD-07: Revenue Mapping Needs Validation

Requirement:
The client-side ingestion layer should validate:
1. numeric revenue fields,
2. presence of referenced family IDs in the loaded patent dataset,
3. malformed or orphaned family references.

## CFD-08: Revenue Risk Calculation Uses Patent Cliff And Defense Signals

Requirement:
The revenue-at-risk workflow should combine:
1. linked family expiration or coverage-end signals,
2. linked family blocking-power strength,
3. linked family legal resilience status,
4. the time-to-expiry horizon.

## CFD-09: Revenue Risk Output Should Support Timeline Views

Requirement:
The UI should support a revenue-protection timeline or patent-cliff chart showing how much revenue is exposed as linked families weaken, expire, or remain poorly defended.

## Use Case 2: Portfolio Pruning ROI

## CFD-10: Support A Simple Maintenance-Cost Assumption Input

Requirement:
PatentIQ should support a lightweight manual settings input for estimated annual maintenance cost per active family.

## CFD-11: Pruning Workflows Should Use Explicit Threshold Controls

Requirement:
The pruning workflow should let the client define settings such as:
1. maintenance cost assumption,
2. pruning percentile threshold,
3. whether zero-citation or zero-generality filters are required.

## CFD-12: Prune Candidates Should Be Based On Existing Strategic Metrics

Requirement:
The pruning workflow should identify low-value assets using already computed patent metrics such as:
1. low blocking power,
2. weak heritage,
3. zero or near-zero citations,
4. zero generality,
5. active-but-strategically weak status.

## CFD-13: Pruning Output Should Quantify Annual Savings

Requirement:
The pruning workflow should estimate immediate annual maintenance savings as:
1. number of prune candidates,
2. multiplied by the cost assumption,
3. with clear disclosure that this is an estimated scenario result.

## CFD-14: Exportable Pruning Lists Should Be Supported

Requirement:
The product should support exporting the exact family IDs or assets that fall into the prune zone so the client can route them to counsel or portfolio managers.

## Use Case 3: R&D Efficiency Tracker

## CFD-15: Support R&D Spend Input By Year And WIPO Field

Requirement:
PatentIQ should support optional client-provided R&D spend inputs keyed by:
1. year,
2. WIPO 35 field,
3. spend amount.

## CFD-16: Manual Grid Or Small CSV Is Acceptable

Requirement:
Because the field taxonomy is limited, the platform may accept this input via:
1. a CSV,
2. a manual UI grid,
3. or both.

## CFD-17: R&D Efficiency Must Use Family-First Output Metrics

Requirement:
The R&D efficiency workflow should compare spend against family-first strategic outputs such as:
1. crown-jewel families,
2. top-decile originality/radicalness assets,
3. field-specific elite-family counts.

## CFD-18: Cost Per Crown Jewel Should Be Supported

Requirement:
The platform should support a derived metric such as:

`Cost per Crown Jewel = R&D Spend / Count of Top-Tier Families`

for a selected year and WIPO field.

## CFD-19: Efficiency Views Should Support External Benchmarking

Requirement:
The product should compare the client’s field-specific R&D-to-elite-IP conversion rate against a benchmark such as:
1. industry baseline,
2. anonymized peer cohort,
3. competitor-estimated public benchmark where methodologically defensible.

## Processing And Validation Rules

## CFD-20: Client Inputs Must Validate Against PatentIQ Taxonomies

Requirement:
Client data ingestion should validate:
1. WIPO field names,
2. year ranges,
3. family IDs,
4. numeric assumptions,
5. required column presence.

## CFD-21: Financial Insights Must Be Clearly Labeled As Client-Enriched

Requirement:
Any dashboard, chart, or export using client-provided business inputs should clearly indicate that the result is a client-enriched analysis rather than a pure public-data metric.

## CFD-22: Client-Enriched Results Must Preserve Public Metric Provenance

Requirement:
When public patent metrics are joined to client business data, the system should preserve the provenance of:
1. the patent score method,
2. the client-side inputs,
3. the scenario assumptions,
4. the date of the calculation.

## Product Surfaces

## CFD-23: Revenue At Risk Belongs In Executive And Product Dashboards

Requirement:
The revenue-at-risk workflow should surface:
1. cliff charts,
2. risk matrices,
3. product-level exposure views,
4. time-to-expiry warnings.

## CFD-24: Pruning ROI Belongs In Portfolio Management Surfaces

Requirement:
The pruning workflow should surface:
1. prune-zone views,
2. savings cards,
3. exportable action lists,
4. threshold scenario controls.

## CFD-25: R&D Efficiency Belongs In Strategy And Innovation Surfaces

Requirement:
The R&D efficiency workflow should surface:
1. cost-per-crown-jewel comparisons,
2. field-by-field efficiency charts,
3. diagnostic underperformance alerts,
4. year-over-year efficiency changes.

## Relationship To Existing Notes

This note extends the patent-intelligence stack into optional client-enriched financial and operational intelligence.

### Overlaps With Existing Docs

1. `portfolio-size-normalization-and-crown-jewel-ranking-requirements.md`
2. `oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`
3. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
4. `march-2026-family-legal-analytics-master-index.md`

### Net-New Additions

1. optional client financial integration layer,
2. product-to-family revenue mapping,
3. pruning ROI calculator,
4. R&D efficiency tracker,
5. client-side DuckDB WASM security pattern.

## Delivery Priority

### P0

1. define CSV/manual input contracts,
2. validate client-side joins against family IDs and WIPO fields,
3. preserve public metric provenance in enriched outputs,
4. keep client-enriched mode optional and clearly labeled.

### P1

1. revenue-at-risk dashboard,
2. pruning ROI scenario calculator,
3. R&D efficiency by field dashboard,
4. exportable action artifacts.

### P2

1. richer client-side scenario modeling,
2. deeper benchmark layers,
3. more enterprise-grade local-only execution patterns.

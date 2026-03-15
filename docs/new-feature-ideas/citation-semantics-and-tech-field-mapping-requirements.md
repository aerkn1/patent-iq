# Citation Semantics And Tech Field Mapping Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must handle:

1. forward versus backward citations in family-level scoring,
2. current-enforceability versus historical-heritage scopes,
3. the distinction between geographic markets and technology fields,
4. WIPO 35 technology-field mapping from CPC/IPC,
5. strict deduplication required for accurate tech-breadth metrics.

## Core Principle

Citations, technology breadth, and market breadth answer different questions and must not be blended carelessly.

1. forward citations measure external impact,
2. backward citations measure technical crowdedness and dependency,
3. geographic market breadth measures territorial enforceability,
4. technology breadth measures cross-sector disruptive scope.

## Part 1: Forward And Backward Citations In Family Scoring

## CSR-00: Patent Citations And NPL Citations Must Be Distinguished

Requirement:
PatentIQ must preserve a first-class distinction between:

1. `patent_citations`
2. `non_patent_literature_citations` or `npl_citations`

Rule:
1. patent-family citation metrics drive collision, blocking-power, crowdedness, and follower analysis,
2. NPL citations support science-grounding, research-intensity, and quality interpretation,
3. NPL references must never be silently blended into patent-citation impact metrics.

## CSR-01: Family-Level Citation Collapse Is Mandatory

Requirement:
All forward and backward citations pointing to or from any `A`, `B`, or `C` document in the family must collapse to the canonical family entity before citation-based metrics are calculated.

## CSR-02: Forward Citations Measure External Collision And Influence

Requirement:
Forward citations should be interpreted as evidence that later actors are technically colliding with, learning from, or navigating around the invention.

Constraint:
For current blocking-power and current-threat logic, forward impact should be based on later patent-family citations rather than NPL references.

## CSR-03: Heritage-Scope Forward Impact Includes Dead Families

Requirement:
Historical innovation or heritage metrics must count adjusted forward citations even if the family is now lapsed, expired, or dead.

Why:
Historical pioneering influence survives legal expiry.

## CSR-04: Current Blocking Forward Impact Requires Live Rights

Requirement:
Forward-citation multipliers used in current blocking-power or current threat metrics should only activate when the family still has active enforceable grant-stage rights.

Why:
A pending or dead patent may be influential, but it cannot currently block the market.

Dimensionality rule:
Citation influence and heritage should remain globally aggregated at the family-field level rather than being split into defender-side jurisdiction slices.

Reference:
`score-dimensionality-and-citation-weighting-requirements.md`

## CSR-05: Backward Citations Measure Crowdedness

Requirement:
Backward citations must be used as a proxy for how crowded, mature, or derivative the technical space is.

Interpretation:
1. high backward citations often imply crowded space and incremental innovation,
2. low backward citations can imply foundational or whitespace-like invention.

Separation rule:
Backward patent citations and backward NPL citations must remain separately queryable and separately labeled.

Interpretation extension:
1. backward patent citations indicate prior-art density and competitive dependency,
2. backward NPL citations indicate science-linkage or research grounding,
3. the platform must not imply that NPL-heavy patents are more legally blocking solely because they cite more scientific literature.

## CSR-06: Backward Citations Affect Pioneer Scoring

Requirement:
Historical pioneer or novelty-like metrics should penalize very high backward-citation density and reward relatively sparse prior-art dependence.

## CSR-07: Backward Citations Can Signal FTO Risk

Requirement:
If a family heavily cites currently active competitor rights, the platform should support an elevated FTO or dependency-risk signal.

Why:
Building on a competitor’s active patent stack may imply licensing or infringement exposure despite having one’s own grant.

## Part 2: Scope Separation

## CSR-08: Current Enforceability Scope And Historical Heritage Scope Must Be Separate

Requirement:
The platform must distinguish at least two citation-analysis scopes:

1. `historical_heritage_scope`
2. `current_enforceability_scope`

### Historical heritage scope

Includes:
1. dead and active families,
2. adjusted forward influence,
3. prior-art significance,
4. pioneer positioning.

### Current enforceability scope

Includes:
1. only families with active enforceable rights,
2. forward citations as current threat multiplier,
3. live blocking relevance.

## Part 3: Clarifying “Market” Terminology

## CSR-09: Geographic Market Must Be Distinguished From Technology Market

Requirement:
PatentIQ must use distinct terminology for:

1. `geographic_market` or `market_breadth`
2. `technology_field`, `industry_sector`, or `tech_breadth`

These must never be silently conflated.

### Geographic market

Meaning:
Where in the world the family has actual or potential territorial protection.

Examples:
1. `US`
2. `CN`
3. `DE`
4. UP member-state footprint

### Technology field

Meaning:
What industries, technology sectors, or WIPO technology fields the family touches.

## CSR-10: Use WIPO 35 Technology Fields As The Standard Sector Layer

Requirement:
The default open taxonomy for technology sectors should be the WIPO 35 technology-field concordance.

Why:
It provides a globally standard way to compress large IPC/CPC spaces into a manageable sector view.

## Part 4: CPC / IPC Unification For WIPO Mapping

## CSR-11: CPC And IPC Must Be Unified Before WIPO Mapping

Requirement:
The platform must not map CPC and IPC separately into competing sector systems for the same family-level metric.

Rule:
1. truncate specific CPC codes to their IPC-equivalent structural form,
2. merge truncated CPC codes and raw IPC codes into one canonical technical-code stream,
3. then join that stream to the WIPO concordance.

## CSR-12: WIPO Mapping Uses IPC Backbone

Requirement:
When mapping to WIPO 35 fields, the canonical intermediate code should be IPC-compatible because the WIPO concordance is IPC-based.

## Part 5: Relevancy Handling

## CSR-13: Tech Breadth Uses Boolean Presence, Not Relevancy Weight

Requirement:
For family-level tech-breadth / blocking-scope metrics, any unique mapped field touched by the family should count once regardless of whether the underlying classification was primary or secondary.

Why:
If a patent legally touches both AI and transport, it can act as a roadblock in both spaces.

## CSR-14: Portfolio Distribution Charts Should Support Fractional Counting

Requirement:
For macro portfolio distributions or field-share charts, the system should support fractional counting so multi-field families do not inflate total counts.

Recommended rule:
If one family maps to `N` WIPO fields, assign `1/N` to each field in distribution charts.

## Part 6: The Double-Deduplication Funnel

## CSR-15: Step A - Raw Sweep

Requirement:
Collect every IPC and CPC code from every `A`, `B`, and `C` document attached to the family.

## CSR-16: Step B - Unification

Requirement:
Truncate collected CPC codes to standard IPC-compatible structure and merge them with IPC codes into one canonical code column.

## CSR-17: Step C - Technical-Level Deduplication

Requirement:
Run a first `DISTINCT` at the technical-code level so repeated classifications across jurisdictions and lifecycle documents collapse to unique canonical codes.

## CSR-18: Step D - WIPO Concordance Join

Requirement:
Join the deduplicated canonical code set to the WIPO 35 concordance table.

## CSR-19: Step E - Technology-Field-Level Deduplication

Requirement:
Run a second `DISTINCT` on the mapped WIPO field names because multiple canonical IPC codes may map to the same WIPO field.

Why:
Without this second deduplication, one field such as Pharmaceuticals could be counted multiple times inside the same family.

## Part 7: Output Semantics

## CSR-20: Tech Breadth Must Report Unique WIPO Field Count

Requirement:
Family-level tech breadth should be expressed as the count of unique WIPO technology fields touched after double deduplication.

## CSR-21: Blocking Scope Should Report Both Geography And Technology

Requirement:
The product should support statements like:

1. geographic spread / market breadth,
2. tech breadth / WIPO field count,
3. adjusted forward impact,
4. backward-citation crowdedness.

These are distinct dimensions, not interchangeable metrics.

## CSR-21A: Citation Outputs Must Preserve Source Type

Requirement:
Any citation-facing API, mart, or UI should preserve enough metadata to distinguish:

1. `forward_patent_citations`
2. `backward_patent_citations`
3. `backward_npl_citations`

Recommended output semantics:
1. `citation_impact` means adjusted patent-family forward impact,
2. `crowdedness` means backward patent prior-art density,
3. `science_grounding` means backward NPL dependence or research linkage.

## Part 8: Product And UI Expectations

## CSR-22: Keep Terminology Analyst-Grade

Requirement:
UI, APIs, and reports should use terminology consistently:

1. `Geographic Spread / Market Breadth` = countries, territorial enforceability, weighted reach
2. `Tech Breadth / Industry Sectors` = WIPO 35 fields or equivalent clusters
3. `Forward Impact` = adjusted forward citations
4. `Crowdedness` = backward citations / prior-art density

## CSR-23: Current Threat And Historical Influence Must Stay Separate In Citation Views

Requirement:
If a family is historically influential but no longer enforceable, the UI should show strong historical impact without overstating present legal threat.

## CSR-24: Geographic Citation Weighting Should Enter Through The Citing Side

Requirement:
If PatentIQ weights citations by strategic importance, it should weight the citing documents or citing families rather than geographically fragmenting the cited family’s heritage score.

Why:
This preserves global historical influence while still distinguishing high-value citations from low-value citations.

Blocking-power rule:
Adjusted citation impact must still feed the final family-level blocking-power fusion score rather than remain only a standalone heritage metric.

Reference:
`blocking-power-market-citation-fusion-requirements.md`

OECD extension:
Fixed-window citation indicators and downstream field-diversity measures such as generality should be supported as citation-quality upgrades rather than treated as disconnected side metrics.

Reference:
`oecd-quality-nature-of-innovation-requirements.md`

Threat-network extension:
Forward citations should also be capturable as dated, citing-side events so the platform can build attacker leaderboards and geographic collision timelines.

Reference:
`citation-event-ledger-and-attacker-leaderboard-requirements.md`

## Mapping To Existing Requirements

This note sharpens several prior documents.

### Overlaps With Existing Docs

1. `DAP-03`: citation metadata layer,
2. `R-02`, `R-03`, `R-12`, `R-14`: family-aware citation metrics,
3. `FCR-06`, `FCR-07`, `FCR-11`, `FCR-12`: family-level tech breadth and clean-room citation logic,
4. `GIR-03`, `GIR-04`: age-normalized impact / RCF logic,
5. `PKR-08`, `PKR-09`: citation aggregation across lifecycle docs,
6. `score-dimensionality-and-citation-weighting-requirements.md`,
7. `blocking-power-market-citation-fusion-requirements.md`,
8. `oecd-quality-nature-of-innovation-requirements.md`,
9. `citation-event-ledger-and-attacker-leaderboard-requirements.md`.

### Net-New Additions

1. explicit split between heritage-scope and enforceability-scope citation logic,
2. strict geographic-market versus technology-field terminology,
3. WIPO-35-based double-deduplication funnel,
4. separate boolean and fractional counting rules by product use case.

## Delivery Priority

### P0

1. family-level forward/backward citation collapse,
2. current-vs-historical citation scope separation,
3. WIPO 35 field mapping pipeline,
4. CPC-to-IPC unification,
5. double deduplication for tech breadth.

### P1

1. RCF support in influence ranking,
2. fractional field distributions,
3. UI terminology cleanup for geography vs technology.

### P2

1. deeper FTO dependency-risk analytics from backward citation graphs,
2. more advanced cross-taxonomy field explanations.

# Unitary Patent And UPC Representation Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must represent the European Unitary Patent (UP) and Unified Patent Court (UPC) effects in ETL, analytics, legal risk, and valuation-oriented product logic.

## Why This Matters

The UP changes how European patent families should be counted, valued, and risk-scored. If the pipeline treats the UP as a normal EP publication or ignores the `C0` registration layer, multiple core analytics become wrong:

1. family breadth is understated,
2. filing momentum is overstated,
3. renewal-cost logic becomes misleading,
4. legal-status decay appears gradual when it may actually be catastrophic,
5. citation views fragment across `A`, `B`, and `C0` records.

## Detection Rules

### UPR-01: Detect Unitary Patent Status

Requirement:
PatentIQ must not infer UP status from ordinary EP grant kind codes such as `B1` or `B2`.

Accepted detection signals:
1. an `EP...C0` publication,
2. an INPADOC Chapter IV legal event corresponding to unitary effect registration, especially `IV.2(1)`.

Implementation note:
UP detection should be normalized into a boolean or status field at family and publication level.

If PATSTAT Register UP tables are available, the pipeline should prefer:
1. `reg701_appln`,
2. `reg741_appln_status`,
3. `reg731_event_data`

as the strongest EP-side procedural truth for publication-detail and UP evidence views.

### UPR-02: Preserve Legal Linkage To The Original EP Grant

Requirement:
The `C0` record must be treated as a legal registration layer attached to the already-granted EP patent, not as a new technical invention.

Implication:
`A`, `B`, and `C0` records must resolve into the same canonical family and legal storyline.

## ETL And Jurisdiction Expansion Rules

### UPR-03: Unroll UP Coverage Into Participating States

Requirement:
When a family is detected as having unitary effect, the ETL pipeline must expand the UP into the participating UP member states for geographic-footprint analytics.

Recommended approach:
1. maintain a static DuckDB UP lookup table of the participating ISO country codes,
2. if UP status is true, append the UP member states to the family jurisdiction list,
3. also append classic non-UP EP validation states when present,
4. also append other international family members such as `US`, `CN`, and `JP`,
5. deduplicate all jurisdiction codes before counting.

Outcome:
Family breadth should reflect true territorial footprint rather than just `EP` as a single jurisdiction token.

### UPR-04: Count Geographic Footprint After Expansion

Requirement:
Family breadth and jurisdiction spread metrics must count the unrolled UP member states, not the unexpanded EP placeholder.

Illustrative effect:
`US + CN + EP` should not remain breadth `3` if the EP right is unitary and effectively covers many member states.

### UPR-05: Keep Expansion Logic Separate From Document Counting

Requirement:
Geographic expansion for breadth must not create extra R&D events in trend analytics.

Implication:
Unrolled UP states affect territorial footprint and blocking coverage metrics, but they must not create extra filing events.

## Analytics Impacts

### UPR-06: Citation Analytics Must Stay Family-First

Requirement:
Forward and backward citation analytics must aggregate at `docdb_family_id` or equivalent canonical family level so that the invention absorbs citations to:
1. application documents (`A1`, `A2`),
2. grant documents (`B1`, `B2`),
3. legal registration layer (`C0`) without expecting direct citation volume on `C0`.

Why:
The `C0` record is a legal registration artifact, not the primary technical citation target.

### UPR-07: Filing Momentum Must Ignore C0 Inflation

Requirement:
Filing momentum and R&D activity trends must count families, not publications, so that the `C0` registration does not create a false filing spike.

Implementation rule:
Collapse `A`, `B`, and `C0` into one family event anchored on earliest priority date.

### UPR-08: Family Breadth Must Value Footprint, Not Renewal Spend

Requirement:
Value-proxy logic must treat unrolled UP footprint as the signal of geographic scope, not raw renewal-cost estimates.

Why:
The UP can cover many states under one renewal payment, so raw maintenance spend is no longer a reliable standalone proxy for value.

## Legal Status And Risk Rules

### UPR-09: Model UP Renewal As All-Or-Nothing Coverage

Requirement:
If a UP renewal is missed, legal-status analytics must reflect simultaneous loss of coverage across all participating UP states.

Implication:
Legal coverage should show a sudden cliff, not a slow country-by-country decay pattern.

### UPR-10: Flag Centralized UPC Revocation Risk

Requirement:
Any patent family with unitary effect must carry a centralized UPC revocation vulnerability flag in defensive-strength or litigation-risk analytics.

Why:
A single UPC revocation can destroy protection across all participating UP states at once.

### UPR-11: Treat Negative UP Status Events As Catastrophic Coverage Loss

Requirement:
For legal event marts and risk dashboards, a negative UP event on a `C0`-linked family should be treated as a high-severity coverage drop.

Examples:
1. lapse due to missed renewal,
2. centralized revocation,
3. major adverse UPC status outcome.

### UPR-12: Surface Single-Point-Of-Failure Risk In UI

Requirement:
UI and report outputs should explicitly identify UP-backed families as potential single-point-of-failure assets where one negative event can erase broad territorial coverage.

## MVP Guidance For The 2014-2025 EP Demo Scope

### UPR-13: UP Handling Is Mandatory For Demo Data

Requirement:
Because the demo scope includes EP grants spanning the post-UP launch period, UP handling must be present in the demo-grade ETL and analytics stack.

### UPR-14: Static DuckDB UP Lookup Table

Requirement:
Engineering should add a static UP lookup table in DuckDB containing the participating ISO country codes used by breadth and legal-coverage logic.

Suggested SQL pattern:
Use `CASE WHEN` or equivalent branching so that UP families add the UP state array before deduplication and final breadth counting.

## Product And UI Expectations

### UPR-15: Family Breadth Explanation

Requirement:
Where family breadth is shown, the UI should clarify that UP-based breadth may include expanded participating member states rather than a single `EP` token.

### UPR-16: Legal Coverage Visualization

Requirement:
Coverage views should distinguish:
1. classic EP validations,
2. unrolled UP member-state coverage,
3. non-EP family members,
4. catastrophic UP coverage loss when applicable.

### UPR-17: Risk Labeling

Requirement:
If litigation or blocking-risk views are present, UP-backed families should expose a UPC-centralization risk note.

### UPR-18: Register-Derived UP Truth Must Not Inflate Global Scoring

Requirement:
PATSTAT Register UP status may sharpen EP publication and family evidence surfaces, but it must not by itself raise cross-office blocking-power or percentile scores relative to offices without equivalent procedural-depth data.

## Mapping To Existing Requirements

This note does not replace earlier requirements; it sharpens them.

### Overlaps With Existing Docs

1. `R-02`, `R-14`, `R-22`: family-first citation and analytics mode,
2. `R-18`, `R-20`: filing-momentum and priority-date trend backbone,
3. `R-19`: family spread as value proxy,
4. `DAP-01`: legal-status layer,
5. `PMC-01`: family as default counting unit,
6. `PMC-04` and `PMC-16`: trend correctness and tech/market matrix integrity.

### Net-New Additions

1. explicit UP detection rules,
2. UP jurisdiction unrolling rules,
3. UP-specific renewal cliff logic,
4. UPC centralized revocation vulnerability treatment,
5. `C0`-specific handling in legal and valuation analytics.

## Delivery Priority

### P0

1. UP detection,
2. jurisdiction unrolling,
3. family-breadth correction,
4. family-first citation and trend safeguards,
5. UP renewal-cliff handling.

### P1

1. UPC risk labeling,
2. UI coverage explanation,
3. catastrophic-event visualization.

### P2

1. deeper UPC litigation workflow support,
2. expanded reporting and scenario simulation.

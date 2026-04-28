# Score Dimensionality And Citation Weighting Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define which score families in PatentIQ should use 4D jurisdiction-aware modeling versus 3D global field modeling, and clarify how geographic bias should enter citation-based metrics without breaking the logic of historical influence.

## Core Principle

PatentIQ must separate:
1. territorial legal power,
2. global technological influence.

Legal monopolies stop at borders.
Technological influence does not.

This means:
1. enforceability-oriented metrics can require jurisdiction-aware dimensionality,
2. heritage and citation-influence metrics must remain globally aggregated at the family-field level.

## Dimensionality Rules

## SDR-01: Enforceability Uses 4D Dimensionality

Requirement:
Current market threat and enforceability scoring should use a jurisdiction-aware structure such as:

`time x tech field x jurisdiction x score`

Why:
Patent enforceability is inherently territorial.

## SDR-02: Heritage Uses 3D Dimensionality

Requirement:
Historical pioneer and heritage scoring should remain in a global field-level structure such as:

`time x tech field x score`

Why:
Historical inventive influence is not limited to the countries where the assignee filed.

## SDR-03: Citation Influence Must Not Be Forced Into A Defender-Side 4D Model

Requirement:
PatentIQ must not split the cited family’s heritage score into jurisdiction-specific sub-scores just because the citing activity originated in different countries.

Why:
Doing so would understate globally influential inventions that filed narrowly but shaped worldwide R&D.

## The Zero-Heritage Trap

## SDR-04: Narrow Filing Geography Must Not Erase Global Influence

Requirement:
If a family filed only in one jurisdiction but was heavily cited worldwide, the heritage logic must still treat it as globally influential inside its technology field.

Implication:
No “US heritage = 0” style interpretation should arise merely because the cited family lacked a US filing.

## Citation Weighting Logic

## SDR-05: Geographic Bias In Citation Value Should Enter Through The Citing Side

Requirement:
When PatentIQ wants to weight forward citations by strategic importance, it should weight the citing documents or citing families rather than geographically fragmenting the cited family’s heritage score.

Why:
This preserves global influence on the cited side while still recognizing that not all citations are equally meaningful.

## SDR-06: Weighted Citation Impact May Use A PageRank-Like Logic

Requirement:
Adjusted forward-citation impact may weight each incoming citation based on the strategic quality of the citing right.

Interpretation:
A citation from a strong active right in a high-value jurisdiction and field may count more than a citation from a weak or abandoned right in a low-value slice.

## SDR-07: Citing-Side Weight Inputs

Requirement:
If weighted citation impact is implemented, the weight of a citing document or family may consider:
1. normalized legal stage of the citing right,
2. jurisdiction market weight of the citing right,
3. local or global tech-trend coefficient of the citing field,
4. active versus inactive status,
5. citation-cleaning rules already defined elsewhere.

## SDR-08: Heritage Score Remains Globally Aggregated After Citation Weighting

Requirement:
Even when incoming citations are quality-weighted, the resulting heritage score should still aggregate to a global family-field influence score rather than a jurisdiction-fragmented defender-side score.

## Metric Cheat Sheet

## SDR-09: Current Market Threat Uses 4D Logic

Requirement:
Current market threat and enforceability should use:
1. time,
2. tech field,
3. jurisdiction.

## SDR-10: Overall Blocking Power Is A 3D Rollup Built From 4D Enforceability Inputs

Requirement:
Overall blocking power may be presented at a family-field or family-level rollup, but it should be built from the underlying jurisdiction-aware enforceability contributions and then normalized appropriately.

Clarification:
This rollup must also incorporate the global citation-impact pillar through family-level fusion before normalization.

Reference:
`blocking-power-market-citation-fusion-requirements.md`

## SDR-11: Historical Pioneer Score Uses 3D Logic

Requirement:
Heritage or pioneer score should use:
1. time,
2. tech field,
3. globally aggregated citation influence.

## SDR-12: Citation Quality Weighting Should Not Change Heritage Dimensionality

Requirement:
Applying strategic weights to incoming citations may refine the citation score, but it must not force the final heritage score into a jurisdiction-sliced output.

## Architecture Guidance

## SDR-13: Enforceability And Heritage Must Have Different Mart Semantics

Requirement:
PatentIQ should maintain separate marts or clearly separated columns for:
1. enforceability-oriented jurisdiction-aware outputs,
2. heritage-oriented global field outputs.

## SDR-14: APIs Must Expose Score Scope

Requirement:
Any API serving these metrics should identify whether a score is:
1. jurisdiction-aware enforceability,
2. globally aggregated heritage,
3. citation-quality-weighted heritage.

## SDR-15: Documentation Must Prevent Dimensionality Drift

Requirement:
Engineering documentation and metric definitions must explicitly state that 4D logic is not a universal scoring template for every metric family.

## Relationship To Existing Notes

This note clarifies how the earlier scoring architecture should be applied across metric types.

### Overlaps With Existing Docs

1. `citation-semantics-and-tech-field-mapping-requirements.md`
2. `wipo-field-contribution-timeseries-requirements.md`
3. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`
4. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
5. `blocking-power-score-normalization-and-percentile-ranking-requirements.md`
6. `blocking-power-market-citation-fusion-requirements.md`

### Net-New Additions

1. explicit 4D-versus-3D score-governance rules,
2. the zero-heritage trap warning,
3. citing-side weighting for citation quality,
4. PageRank-like interpretation for weighted forward citations,
5. dimensionality guardrails for APIs and marts.

## Delivery Priority

### P0

1. dimensionality rules documented in metric definitions,
2. heritage kept global and not jurisdiction-fragmented,
3. enforceability kept jurisdiction-aware,
4. score-scope metadata in marts and APIs.

### P1

1. weighted forward-citation quality layer,
2. citation-quality provenance fields,
3. expert-facing explanation of citing-side weighting.

### P2

1. more advanced network centrality methods for citation quality,
2. scenario analysis for evolving citation-network influence.

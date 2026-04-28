# Blocking Power Lifecycle And Point-In-Time Scoring Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must calculate blocking power and related strategic-strength metrics as time-varying family-level scores rather than static values.

## Core Principle

### BPR-01: Blocking Power Is A Time-Varying Curve

Requirement:
Blocking power must be modeled as a dynamic family-level score that changes over the patent lifecycle as legal, territorial, and financial conditions change.

Implication:
A family that scores high today may score much lower later if:
1. major jurisdictions lapse,
2. UP renewal fails,
3. revocation occurs,
4. legal term expires.

## Why Static Scoring Fails

If blocking power is stored as a flat number without time context:

1. historical comparisons become wrong,
2. renewal/lapse events are flattened away,
3. current-state and historical-state analysis get mixed,
4. lifecycle decay cannot be studied,
5. date-trigger workflows become unreliable.

## The Three Blocking-Power Pillars Over Time

## Pillar 1: Market And Legal Enforceability

### BPR-02: Enforceability Starts Low In The Pending Phase

Requirement:
During the early years when only `A`-stage documents exist, blocking power must remain low because there is little or no enforceable legal right.

### BPR-03: Enforceability Spikes On Grant In Major Markets

Requirement:
Blocking power must jump materially when enforceable grant-stage rights (`B1`, `B2`, equivalent stages) are obtained in major jurisdictions.

### BPR-04: Enforceability Decays As Jurisdictions Lapse

Requirement:
As renewals are not maintained and jurisdictions fall away, the market/legal pillar must decline accordingly.

### BPR-05: Enforceability Falls To Zero At Full Expiry

Requirement:
Once the family is no longer enforceable in all relevant jurisdictions, the current blocking-power contribution from legal enforceability must drop to zero.

## Pillar 2: Technological Impact / Citations

### BPR-06: Citation Impact Accumulates Over Time

Requirement:
Citation-based impact should generally increase over time as new forward citations arrive.

### BPR-07: Citation Momentum Has Early Lag

Requirement:
Blocking-power logic should recognize that newly filed families often show little or no citation activity in the earliest window due to publication lag and observation delay.

### BPR-08: Relative Impact Must Be Re-Normalized Over Time

Requirement:
Because raw citations only increase, any cohort-normalized impact metric such as RCF must be recomputed over time rather than treated as fixed forever.

Why:
A family’s relative standing can decline even while raw citations rise if its cohort grows faster.

## Pillar 3: Technological Breadth

### BPR-09: Tech Breadth Is Mostly Stable But Not Always Frozen

Requirement:
Technology breadth should usually remain stable after core classification is established, but the platform must allow limited change if later divisional, continuation, or related grant-stage documents introduce new CPC coverage inside the family structure.

## Lifecycle Shape Expectations

### BPR-10: Blocking Power Should Follow A Ramp / Peak / Decay / Cliff Pattern

Requirement:
For many successful families, the score should be expected to:
1. ramp slowly during the pending phase,
2. peak after major grants and resilience signals,
3. decay as jurisdictions lapse,
4. collapse at expiry or full loss of enforceability.

This is not a fixed formula, but it is the intended lifecycle behavior the metrics should support.

## Point-In-Time Architecture

### BPR-11: Blocking Power Must Be Rebuilt From Events At Query Time

Requirement:
Current and historical blocking power must be computed from event history and point-in-time reconstruction, not from a single overwritten status column.

### BPR-12: Legal Status Event Mart Is The Source Of Truth

Requirement:
The legal-status event mart must capture the lifecycle events that change blocking power, such as:
1. application publication,
2. grant issuance,
3. opposition or challenge entry,
4. opposition survival or amendment,
5. lapse,
6. renewal continuity,
7. revocation,
8. expiry,
9. UP registration and UP lapse where applicable.

### BPR-13: Event Ledger Must Be Append-Only

Requirement:
The event mart should behave like a ledger. New legal events append state changes rather than overwrite historical truth.

## Query Semantics

### BPR-14: “Today” Queries Must Use Today’s Reconstructed State

Requirement:
When a user asks for current blocking power, the engine must apply all events up to now and exclude events in the future.

### BPR-15: Historical Queries Must Ignore Later Events

Requirement:
When a user asks for blocking power at a historical date, the engine must ignore legal events, citations, or coverage changes that occurred after the requested date.

### BPR-16: Date Trigger Features Must Rebuild Historical Reality

Requirement:
Any date-trigger or historical comparison feature must rebuild the family’s state as of the requested date rather than reuse the present-day score.

## Family-Level Blocking Power Logic

### BPR-17: Blocking Power Must Be Calculated At Family Level

Requirement:
The blocking-power engine must evaluate the family as the core entity and collapse all lifecycle documents into the same strategic asset.

### BPR-18: Legal Enforceability Should Use Grant-Weighted Signals

Requirement:
The enforceability component should prefer:
1. active grant-stage rights,
2. market-tier-weighted jurisdiction coverage,
3. opposition-survival signals such as EP `B2`,
4. current active status at the point in time.

Refinement:
Where supported, the market/legal pillar should also accept jurisdiction-by-field localized trend weighting rather than only global field-level trend weighting.

### BPR-19: Citation Component Should Use Clean-Room Family Impact

Requirement:
The citation component should use family-level adjusted citation impact after scrubbing:
1. intra-family citations,
2. self-citations where possible.

Fusion rule:
This citation component must remain an explicit input to final blocking power and should be fused with the market-threat pillar at family level before UI normalization.

Reference:
`blocking-power-market-citation-fusion-requirements.md`

### BPR-20: Tech Breadth Component Should Use Deduplicated Family CPC Scope

Requirement:
The technology-breadth component should use deduplicated family CPC coverage, optionally updated when later family-stage filings materially broaden scope.

## Status Changes That Must Cause Immediate Score Movement

### BPR-21: Major Grant Event

Requirement:
A major grant in a top-tier market should cause a positive jump in blocking power.

### BPR-22: Opposition Survival Event

Requirement:
An opposition-survival event such as EP `B2` should cause a significant positive resilience adjustment.

### BPR-23: Jurisdiction Lapse Event

Requirement:
A lapse in a meaningful jurisdiction should cause a downward movement in the market/legal pillar.

### BPR-24: UP Lapse Or Revocation Event

Requirement:
A negative UP event must cause a large and sudden drop because it affects many territories at once.

### BPR-25: Final Expiry Event

Requirement:
At full expiry, current blocking power must collapse to zero even though historical influence remains available elsewhere in the platform.

## Product And UI Expectations

### BPR-26: Blocking Power Should Be Interpretable As “Current Threat”

Requirement:
The UI should clearly indicate that blocking power is a current or point-in-time strategic threat metric, not a timeless historical prestige score.

Related scoring rule:
The UI score should be treated as a normalized peer-relative indicator built from the underlying raw blocking-power math, not as the raw absolute score itself.

Reference:
`blocking-power-score-normalization-and-percentile-ranking-requirements.md`

### BPR-27: Historical Blocking Power Views Should Be Supported

Requirement:
Users should be able to inspect or compare blocking power at past dates if the product exposes date-trigger or historical-analysis features.

### BPR-28: Historical Influence Must Be Kept Separate

Requirement:
If a family has high historical citations but no enforceable rights today, the UI should show strong historical influence without implying current blocking power.

## Mapping To Existing Requirements

This note sharpens and connects several prior requirements.

### Overlaps With Existing Docs

1. `R-04`: blocking-power definition update,
2. `R-16`: opposition resilience,
3. `MKT-03`: date-trigger feature,
4. `LSR-15` to `LSR-21`: legal-status event mart and point-in-time logic,
5. `FCR-08` to `FCR-16`: family-level legal, citation, and trend logic,
6. `UPR-09` to `UPR-12`: UP cliff and centralized failure risk,
7. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`,
8. `blocking-power-score-normalization-and-percentile-ranking-requirements.md`,
9. `blocking-power-market-citation-fusion-requirements.md`.

### Net-New Additions

1. explicit time-varying blocking-power lifecycle behavior,
2. lifecycle-shape expectations for strategic scoring,
3. event-to-score movement rules,
4. clear distinction between current blocking power and historical influence.

## Delivery Priority

### P0

1. event-based blocking-power reconstruction,
2. point-in-time query support,
3. current-vs-historical distinction,
4. major event hooks for grants, lapses, B2 survival, and UP loss.

### P1

1. historical blocking-power comparison views,
2. lifecycle visualization,
3. richer decomposition of score changes over time.

### P2

1. predictive blocking-power decay modeling,
2. scenario simulation under future lapse assumptions.

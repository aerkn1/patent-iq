# Blocking Power Market-Citation Fusion Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must fuse jurisdiction-aware enforceability math and global citation-impact math into a single raw blocking-power score before percentile normalization.

## Core Principle

Overall blocking power must not be treated as a pure legal-footprint score.

A family can only be a true blocking asset if it has:
1. enforceable legal reach,
2. evidence that competitors are actually colliding with it.

This means the final raw blocking-power score must combine:
1. 4D market threat,
2. 3D adjusted citation impact.

## Why Citations Must Be In Blocking Power

## BCF-01: Enforceability Without Collision Is Incomplete

Requirement:
PatentIQ must not calculate final blocking power from legal enforceability alone.

Why:
A globally protected patent with no forward citations may be a defensive asset, but it is not proving real competitive blockage.

## BCF-02: Forward Citations Are Evidence Of Real Traffic

Requirement:
Forward citations should be treated as evidence that later innovators are colliding with, learning from, or navigating around the family’s technical territory.

Interpretation:
Legal rights define the tollbooth. Citations show whether traffic is actually approaching it.

## Fusion Architecture

## BCF-03: Keep 4D And 3D Components Separate Until Family-Level Fusion

Requirement:
PatentIQ must not try to multiply global citation impact into every jurisdictional branch separately.

Why:
The citation impact is a global family-level signal, while enforceability remains jurisdiction-aware.

## BCF-04: Market Threat Score Comes From 4D Enforceability Math

Requirement:
The first pillar of the fusion must be a jurisdiction-aware market-threat score built from active legal rights and local market/tech conditions.

Illustrative structure:

`Market Threat Score = SUM over jurisdictions j and fields i of (Stage(j, t) * GDP(j) * Trend(i, j, t))`

## BCF-05: Citation Impact Comes From The 3D Adjusted Citation Layer

Requirement:
The second pillar of the fusion must be an adjusted family-level citation score that already accounts for:
1. citation cleaning,
2. self-citation removal where possible,
3. citing-side quality weighting if implemented,
4. age or cohort normalization such as RCF where applicable.

## BCF-06: Fusion Happens At Family Level Before UI Normalization

Requirement:
PatentIQ should combine the market-threat score and adjusted citation score at the family level before converting the result into the 1-100 UI blocking-power score.

## Raw Absolute Blocking Power Formula

## BCF-07: Use A Weighted Fusion Formula

Requirement:
The raw absolute blocking-power score should be built from an explicit weighted blend of:
1. market threat,
2. adjusted citation impact.

Recommended structure:

`Raw Absolute Blocking Power = (w_market * Market Threat Score) + (w_citation * Adjusted Citation Score)`

Where:
1. `w_market + w_citation = 1`,
2. the default MVP may begin with equal weighting if no better calibrated weights are available.

## BCF-08: Fusion Weights Must Be Explicit And Versioned

Requirement:
The chosen fusion weights must be recorded in method metadata so the score remains reproducible and auditable across releases.

## BCF-09: Citation Impact Must Not Be Orphaned From Final Blocking Power

Requirement:
If PatentIQ exposes a final blocking-power score, adjusted citation impact must be an explicit input unless the product clearly labels the score as a legal-footprint-only view.

## Normalization Step

## BCF-10: Percentile Ranking Applies After Fusion

Requirement:
The percentile-ranking normalization step must run on the fused raw absolute blocking-power score, not on the legal-only market-threat pillar.

Why:
The final UI metric is meant to represent combined blocking reality, not only territorial coverage.

## BCF-11: Cohort Ranking Should Use The Same Field-Time Peer Group

Requirement:
The normalized UI score should be percentile-ranked within the relevant field and time cohort after the fusion step, consistent with the existing normalization note.

## Mart And API Expectations

## BCF-12: Persist Component Scores Separately

Requirement:
PatentIQ should store at least:
1. `market_threat_score`,
2. `adjusted_citation_score`,
3. `raw_absolute_blocking_power`,
4. `ui_blocking_power_score`.

## BCF-13: Expose Component Metadata

Requirement:
Any mart or API should expose metadata such as:
1. `fusion_method`,
2. `market_weight`,
3. `citation_weight`,
4. `normalization_method`,
5. `cohort_definition`,
6. `snapshot_date`.

## BCF-14: Support Decomposition In Product Views

Requirement:
The UI should be able to explain whether a family scores highly because of:
1. strong legal reach,
2. strong citation collision,
3. both.

## Relationship To Existing Notes

This note reconnects the citation and enforceability architecture into a final blocking-power formula.

### Overlaps With Existing Docs

1. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
2. `citation-semantics-and-tech-field-mapping-requirements.md`
3. `score-dimensionality-and-citation-weighting-requirements.md`
4. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`
5. `blocking-power-score-normalization-and-percentile-ranking-requirements.md`

### Net-New Additions

1. explicit market-plus-citation fusion pipeline,
2. family-level fusion timing before normalization,
3. weighted raw blocking-power formula,
4. fusion-weight metadata requirements,
5. score decomposition requirements.

## Delivery Priority

### P0

1. market-threat pillar calculation,
2. adjusted-citation pillar calculation,
3. fused raw blocking-power formula,
4. post-fusion percentile normalization,
5. component-score persistence.

### P1

1. fusion-weight calibration,
2. product decomposition views,
3. field-specific weight-tuning experiments.

### P2

1. learned fusion-weight optimization,
2. scenario analysis across alternative fusion strategies.

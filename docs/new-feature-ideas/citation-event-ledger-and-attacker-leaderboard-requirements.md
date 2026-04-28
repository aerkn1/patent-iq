# Citation Event Ledger And Attacker Leaderboard Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must model forward citations as dated, jurisdiction-aware threat events and how it should rank citing assignees as attackers at family and portfolio level.

## Core Principle

A citation is not just a count.

Each citation event carries:
1. a date,
2. a citing jurisdiction,
3. a citing assignee,
4. a legal-stage or kind-code profile,
5. a threat level.

PatentIQ should therefore model forward citations as an event ledger and use that ledger to power attacker leaderboards, geographic collision views, and portfolio threat matrices.

## Citation Event Ledger

## CEL-01: Forward Citations Must Be Stored As Events

Requirement:
PatentIQ should store forward citations as dated events rather than only as aggregate counts.

## CEL-02: Citation Event Date Uses The Citing Publication Date

Requirement:
For point-in-time citation analysis, the event date should be anchored to the publication date of the citing document or the agreed equivalent citation-observation date.

## CEL-03: Citation Events Must Collapse To Family-Level Relationships

Requirement:
The event ledger must remain consistent with the family-first collapse principle by mapping both cited and citing documents to their canonical family IDs.

## CEL-04: Citation Events Must Retain Citing-Side Context

Requirement:
The enriched citation event layer should preserve at least:
1. cited family,
2. citing family,
3. citing assignee,
4. citing date,
5. citing jurisdiction,
6. citing kind code or normalized legal stage.

## Geographic Collision Tracking

## CEL-05: The Product Must Support Geographic Citation Breakdown Over Time

Requirement:
PatentIQ should support time-series views showing where forward citations are coming from geographically.

Why:
This reveals where the market is beginning to collide with the protected invention.

## CEL-06: Geographic Collision Shifts Must Be Interpretable

Requirement:
The UI should be able to surface transitions such as:
1. citations initially dominated by research-stage applications in one region,
2. later replaced by active grant-stage collisions in more commercially significant regions.

## Attacker Leaderboard

## CEL-07: Citing Assignees Must Be Ranked By Citation Lethality, Not Raw Count Alone

Requirement:
When PatentIQ shows who is citing a family, it should rank citing assignees by the strategic lethality of their citations rather than by raw volume alone.

## CEL-08: Citation Lethality Uses Citing-Side 4D Inputs

Requirement:
The citing-side threat score for each citation should incorporate factors such as:
1. citing kind code or normalized legal stage,
2. citing jurisdiction market weight,
3. local technology trend in the citing field and jurisdiction.

Illustrative structure:

`Citation Lethality = Citing Kind Code Weight * Citing Geo Weight * Local Tech Trend`

## CEL-09: Raw Count And Lethality Score Must Both Be Visible

Requirement:
The product should expose both:
1. citation count,
2. lethality-weighted citation score.

Why:
A low-volume but high-lethality citer may be more dangerous than a high-volume low-quality citer.

## CEL-10: Assignee Leaderboards Must Explain Why A Citer Ranks Highly

Requirement:
The UI should be able to explain whether a citing assignee ranks highly because of:
1. many citations,
2. strong grant-stage citations,
3. high-value jurisdictions,
4. collisions in rising local markets,
5. some combination of the above.

## Portfolio Threat Matrix

## CEL-11: Family-Level Attacker Signals Must Roll Up To Portfolio Threat Views

Requirement:
PatentIQ should aggregate family-level attacker signals across a harmonized portfolio to create portfolio-level threat matrices.

## CEL-12: Portfolio Threat Views Should Support Multiple Cuts

Requirement:
The portfolio threat matrix should support aggregation by:
1. citing assignee,
2. citing jurisdiction,
3. time window,
4. technology field.

## CEL-13: Portfolio Threat Should Support Time-Series Momentum

Requirement:
The platform should support time-series tracking of how citation pressure from specific assignees, regions, or fields changes over time.

## Drill-Down Flow

## CEL-14: The Product Should Support A Three-Level Threat Drill-Down

Requirement:
The attacker-leaderboard experience should support progressive drill-down across:
1. portfolio threat matrix,
2. family collision zone,
3. raw citing-publication proof.

## CEL-15: Level 1 Is The Executive Portfolio Threat Matrix

Requirement:
At the portfolio level, the UI should summarize which citing assignees are the strongest threats against the selected portfolio, field, and time window.

Typical output:
1. top threatening assignee,
2. total lethal citation count,
3. time-window trend,
4. optional field or jurisdiction filter.

## CEL-16: Level 2 Is The Family Collision Zone

Requirement:
When a user drills into a threatening assignee, the platform should reveal which of the target portfolio’s families are receiving those citations and how the collision intensity changed over time.

## CEL-17: Level 3 Is The Publication-Level Proof View

Requirement:
At the deepest level, the platform should show the raw enriched citation events, including:
1. citing publication,
2. citing assignee,
3. citing jurisdiction,
4. date,
5. lethality score and explanation.

## CEL-18: Drill-Down Must Remain Point-In-Time Sliceable

Requirement:
The drill-down flow must remain sliceable by:
1. time,
2. geography,
3. citing assignee,
4. field.

Why:
The user should be able to reconstruct what the threat picture looked like at different dates or in different markets.

## Silver-Layer Table Design

## CEL-19: Create An Enriched Citation Network Table

Requirement:
The silver layer should include an enriched citation network table such as:

`enriched_citation_network`

## CEL-20: Recommended Columns

Recommended columns:
1. `cited_family_id`
2. `citing_family_id`
3. `citing_assignee`
4. `citing_date`
5. `citing_jurisdiction`
6. `citing_kind_code`
7. `citing_normalized_stage`
8. `citation_lethality_score`
9. `wipo_field`
10. `snapshot_metadata` or equivalent method fields

## Relationship To Existing Notes

This note operationalizes citation events as threat-network records and connects them to competitor discovery.

### Overlaps With Existing Docs

1. `citation-semantics-and-tech-field-mapping-requirements.md`
2. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
3. `score-dimensionality-and-citation-weighting-requirements.md`
4. `blocking-power-market-citation-fusion-requirements.md`

### Net-New Additions

1. citation event ledger,
2. enriched citation network table,
3. attacker leaderboard ranked by lethality,
4. geographic collision tracking,
5. portfolio threat matrix from aggregated citation attacks,
6. three-level drill-down flow from portfolio to family to publication proof.

## Delivery Priority

### P0

1. citation event ledger,
2. enriched citation network table,
3. family-level attacker leaderboard,
4. portfolio-level threat aggregation.

### P1

1. geographic collision timeline views,
2. attacker explanation layer,
3. jurisdiction-specific portfolio threat dashboards.

### P2

1. more advanced attacker-network visualizations,
2. predictive citation-threat acceleration alerts.

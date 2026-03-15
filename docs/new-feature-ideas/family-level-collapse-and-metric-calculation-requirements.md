# Family-Level Collapse And Metric Calculation Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define the strict family-level calculation logic PatentIQ must use so market, technology, legal, financial, and future-looking analytics reflect the real invention rather than noisy lifecycle documents.

## Core Principle

### FCR-01: Collapse Principle

Requirement:
Every lifecycle publication associated with the same invention must be mathematically collapsed into its parent `docdb_family_id` before core analytics are calculated.

This includes:
1. `A`-level application publications,
2. `B`-level grant publications,
3. `C`-level modifiers or special legal-status records.

Implication:
If an invention has `A1`, `B1`, and `C0`, the family count is `1`, not `3`.

## Why This Matters

If analytics are performed at document level instead of family level:

1. inventions are double-counted or triple-counted,
2. filing momentum is distorted by administrative publications,
3. citations are fragmented across lifecycle documents,
4. pending and granted rights are mixed incorrectly,
5. portfolio rollups become bureaucratic noise rather than commercial intelligence.

## Lifecycle Handling Rules

### FCR-02: Read The Whole Family, Select The Correct Document Signal

Requirement:
The analytics engine must inspect the entire family but selectively extract the right signal from the right document layer.

Examples:
1. use `B`-level claims for legal/enforceability analysis,
2. use earliest application/priority timing for R&D chronology,
3. use `C`-level records for post-grant legal-status modifiers,
4. aggregate citations across all lifecycle documents to the family.

### FCR-03: Do Not Sum A/B/C Records As Separate Assets

Requirement:
Lifecycle records must never be added together as if they were independent inventions, patents, or innovation events.

## Dimension-Specific Calculation Rules

## Market Dimension

### FCR-04: Market Breadth = Family Breadth

Requirement:
Market coverage must be calculated as the set of unique jurisdictions associated with the family after family-level collapse.

Computation:
1. collect all jurisdiction codes from family-linked records,
2. apply UP unrolling rules if a `C0` or UP legal event is present,
3. append classic EP validations outside UP where available,
4. append international family members,
5. deduplicate all jurisdictions,
6. count the final unique list.

Interpretation:
Family breadth is a proxy for where the owner expects enough value to justify protection.

### FCR-05: Geographic Spread Is A Value-Intent Signal

Requirement:
Wide family breadth must be interpreted as a commercial-intent or market-targeting signal, not as proof of technical merit by itself.

## Technology And CPC Dimension

### FCR-06: Technical Footprint Must Aggregate CPCs At Family Level

Requirement:
The system must collect CPC codes from all family-linked lifecycle documents, deduplicate them, and assign the family to one or more technology clusters.

Why:
Application-stage and grant-stage records may carry slightly different CPC assignments as scope is refined.

### FCR-07: Family Tech Breadth Must Reflect Cross-Domain Reach

Requirement:
If deduplicated CPC coverage spans multiple technical zones, the family should be recognized as broader platform technology rather than a narrow single-use asset.

Interpretation examples:
1. narrow domain family,
2. multi-domain enabling family,
3. foundational platform family.

## Legal Dimension

### FCR-08: Legal Strength Must Exclude Pure A-Level Claims

Requirement:
Legal-risk and blocking analyses must not rely on `A`-level claims as if they were enforceable rights.

Rule:
1. use `B`-level claims when available,
2. use `C`-level records only as legal modifiers on top of granted rights,
3. treat `A`-level-only families as pending or speculative, not fully enforceable.

### FCR-09: Opposition Resilience Must Use B2-Like Survival Signals

Requirement:
Where an EP `B2` or equivalent maintained-after-challenge signal exists, legal-strength metrics must apply a strong uplift to defensive quality or resilience.

Why:
Survival through opposition is a direct real-world validation of legal durability.

### FCR-10: Enforceability Must Be Family-Aware

Requirement:
Legal status should reflect whether the family has enforceable granted members, where they are active, and whether post-grant events have modified or weakened the coverage.

## Financial / Value Dimension

### FCR-11: Adjusted Citation Impact Must Be Calculated At Family Level

Requirement:
Forward citation impact must count citations to any lifecycle document in the family, then collapse those citations to the canonical family entity.

### FCR-12: Clean-Room Citation Score Must Scrub Internal Noise

Requirement:
The family-level citation score used for value/impact analytics must subtract:
1. intra-family citations,
2. self-citations from the same owner or harmonized corporate group where possible.

Why:
This reveals external technological recognition rather than internally manufactured citation volume.

### FCR-13: Use Family Spread As A Value Proxy, Not Raw Maintenance Cost

Requirement:
Do not use estimated renewal spend as a standalone value score. Use territorial footprint and legal durability as stronger signals.

## Future / Momentum Dimension

### FCR-14: Trend Lines Must Anchor On Earliest Priority Date

Requirement:
All R&D momentum trend lines must use the family earliest priority date as the canonical time anchor.

Why:
Priority date best reflects when the invention work actually happened, while `B` grant dates are delayed by examination lag.

### FCR-15: Pending vs Granted Mix Must Be Family-Based

Requirement:
The system must calculate recent-family cohort status by distinguishing:
1. pending families where only `A`-level records exist,
2. granted families where `B`-level records exist,
3. modified or broadened legal state through `C`-level overlays where applicable.

### FCR-16: Do Not Use Grant Date As R&D Momentum Proxy

Requirement:
Grant-date charts must not be used as the primary signal for current R&D trajectory.

Grant dates may still be shown as a secondary prosecution or maturity diagnostic.

## Portfolio Harmonization Rules

### FCR-17: Score Families First, Then Roll Up

Requirement:
Every family must be fully scored before portfolio-level aggregation happens.

Pipeline order:
1. collapse lifecycle documents,
2. compute family-level metrics,
3. harmonize ownership,
4. roll up family metrics under the parent entity.

### FCR-18: Use Assignee Identity Graph For Final Portfolio Aggregation

Requirement:
After family metrics are calculated, the platform must roll them into a harmonized owner graph rather than leaving them attached to raw fragmented assignee strings.

Steps:
1. extract raw owners from relevant family records,
2. harmonize subsidiaries and name variants,
3. map to ultimate parent where available,
4. aggregate family metrics at the parent level.

### FCR-19: Portfolio Metrics Must Reflect Distinct Inventions, Not Publication Count

Requirement:
Portfolio dashboards must present the portfolio as a set of distinct families/inventions by default, with publication counts available only as secondary diagnostics.

## Implementation Expectations

### FCR-20: Core ETL Outputs Must Preserve

Required fields:
1. `docdb_family_id`,
2. `kind_code`,
3. `earliest_priority_date`,
4. jurisdiction identifiers,
5. CPC identifiers,
6. legal-status events,
7. harmonized owner mappings where available.

### FCR-21: Metric Engines Must Declare Their Source Layer

Requirement:
For every family-level metric, the platform should be able to state which lifecycle signals contributed:
1. application layer,
2. grant layer,
3. post-grant modifier layer,
4. family aggregate layer.

### FCR-22: Product Must Explain Family-First Counting

Requirement:
UI and reports should explain that one family may include many publications but is treated as one invention for default analytics.

## Mapping To Existing Requirements

This note consolidates and sharpens prior family-first ideas.

### Overlaps With Existing Docs

1. `PMC-01`: family as default counting unit,
2. `R-02`, `R-03`, `R-14`, `R-20`, `R-21`, `R-22`,
3. `R-19`: family spread as value-context signal,
4. `R-16`: opposition resilience,
5. `DAP-02`, `DAP-03`, `DAP-11`, `DAP-12`,
6. `PKR-01` to `PKR-22`: kind-code semantics,
7. `UPR-01` to `UPR-17`: UP and `C0` treatment.

### Net-New Additions

1. one consolidated collapse principle across all five analytics dimensions,
2. explicit dimension-by-dimension family-level computation logic,
3. strict sequencing rule of family scoring before owner rollup,
4. clean-room citation definition as a named family-level metric pattern.

## Delivery Priority

### P0

1. enforce family collapse in ETL and marts,
2. family-level citation and trend calculations,
3. family-level market breadth and CPC aggregation,
4. granted-right preference in legal metrics,
5. owner harmonization after family scoring.

### P1

1. more explicit UI explanations of family-first logic,
2. clean-room citation labeling,
3. portfolio rollup explainability.

### P2

1. deeper scenario analysis on family-to-parent aggregation,
2. more advanced multi-layer legal and tech drill-downs.

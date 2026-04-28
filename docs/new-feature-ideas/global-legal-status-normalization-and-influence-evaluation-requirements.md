# Global Legal Status Normalization And Influence Evaluation Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must handle:

1. high-impact but expired patents,
2. jurisdiction-specific kind-code meaning,
3. global family aggregation across many countries,
4. market-weighted family breadth and enforceability logic.

## Core Principle

Expired or abandoned patents can lose current legal force without losing historical analytical value. At the same time, global families cannot be evaluated correctly unless raw jurisdiction + kind-code combinations are normalized before aggregation.

## Part 1: Evaluating “Ghost Influence”

## GIR-01: Historical Citation Influence Must Survive Legal Death

Requirement:
Expired, abandoned, or lapsed families must remain eligible for historical influence, prior-art, and innovation-heritage analytics.

Why:
A dead patent can still be foundational technology.

## GIR-02: Raw Citation Counts Must Not Be Compared Naively Across Age

Requirement:
PatentIQ must not compare an old family with hundreds of citations directly against a young family with fewer citations using raw counts alone.

## GIR-03: Implement Relative Citation Frequency (RCF)

Requirement:
Patent or family impact comparison should support a cohort-normalized Relative Citation Frequency metric.

Recommended calculation:
1. compute family-level forward citations,
2. define the comparison cohort by:
   - filing year,
   - CPC/tech class,
3. divide the family’s citation count by the average citation count of its cohort.

Interpretation:
1. `RCF > 1` means above-cohort influence,
2. very high RCF on an old expired family implies foundational influence,
3. very high RCF on a young active family implies accelerating momentum.

## GIR-04: Use RCF Or Equivalent Age-Normalized Measures In Ranking

Requirement:
When ranking historical influence or comparing old and young families, use age-normalized or cohort-normalized citation impact rather than raw counts only.

## Part 2: Portfolio-Level Separation Of Historical And Current Value

## GIR-05: Portfolio Dashboards Must Be Bifurcated

Requirement:
Portfolio analytics must separate at least two pillars:

1. `innovation_heritage_and_influence`
2. `current_blocking_power_and_market_threat`

## GIR-06: Historical Influence Pillar Includes Dead Families

Requirement:
The historical innovation/influence pillar must include expired, abandoned, and lapsed families when calculating:
1. historical R&D footprint,
2. foundational citation impact,
3. prior-art credibility,
4. long-run technology leadership.

## GIR-07: Current Blocking Pillar Excludes Dead Families

Requirement:
The current blocking/market-threat pillar must exclude families that are no longer legally enforceable at the selected point in time.

Why:
Historical influence and current legal monopoly are not the same thing.

## GIR-08: UI Must Explain The Split Explicitly

Requirement:
Portfolio views and reports must clearly label whether a score reflects:
1. historical influence,
2. current enforceability,
3. current market threat,
4. blended score with explicit methodology.

## Part 3: The “Rosetta Stone” Normalization Layer

## GIR-09: Raw Kind Codes Must Not Be Used Directly Across Jurisdictions

Requirement:
PatentIQ must not assume that the same raw kind code has the same semantic meaning across offices.

Why:
For example, `B2` in EP and `B2` in the US do not carry the same legal meaning.

## GIR-10: Build A Jurisdiction + Kind Code Normalization Table

Requirement:
The silver data layer must include a normalization table mapping:

1. `jurisdiction_code`
2. `raw_kind_code`

into normalized fields such as:

1. `universal_stage`
2. `legal_status_proxy`
3. `value_multiplier`
4. `is_enforceable`
5. `is_application_stage`
6. `is_post_grant_modifier`

Implementation note:
For a concrete MVP build blueprint for both the kind-code normalization table and the tiered market weighting table, see:

- `docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md`

## GIR-11: Example Universal Stages

Recommended normalized stages:
1. `published_application`
2. `standard_grant`
3. `opposition_survivor`
4. `unitary_registration`
5. `corrected_or_reexamined`
6. `other_post_grant_modifier`

## GIR-12: Use Office-Aware Value Multipliers Carefully

Requirement:
If the product uses legal-strength or value multipliers derived from normalized stages, those multipliers must be office-aware and methodology-labeled.

Example pattern:
1. application-stage rights lower confidence,
2. standard grants establish enforceability,
3. opposition survivors receive stronger resilience weighting,
4. unitary registrations amplify geographic scope but are not new inventions.

## Part 4: Family Aggregation Across Many Jurisdictions

## GIR-13: Use The “Max Stage” Rule For Family Grant Presence

Requirement:
When deriving family-level granted status, the engine should evaluate all family members across jurisdictions and set `is_granted = TRUE` if at least one member maps to a grant-stage or stronger universal stage.

Why:
A family can contain pending, granted, amended, and post-grant-modified members at once.

## GIR-14: Preserve Richer State Than Boolean Grant Flags

Requirement:
Even if `is_granted` is derived through a max-stage rule, the system must also preserve richer family status signals such as:
1. active granted count,
2. opposed count,
3. unitary registration presence,
4. partially lapsed pattern,
5. dead-jurisdiction count.

## GIR-15: Unroll UP Geography Before Market Aggregation

Requirement:
If UP/C0 logic is detected, the engine must expand UP member states before market-footprint aggregation, using the rules already defined in the UP requirements note.

## Part 5: Tiered Market Weighting

## GIR-16: Jurisdiction Count Alone Is Not Enough

Requirement:
PatentIQ must not treat all jurisdiction counts as equal for commercial-value estimation.

Why:
A family active in a few major markets can be commercially more important than a family active in many small markets.

## GIR-17: Add Market Tier Weights To Jurisdictions

Requirement:
The pipeline should define market tiers for jurisdictions, for example based on:
1. GDP,
2. patent litigation intensity,
3. market size,
4. commercial relevance to IP enforcement.

Illustrative structure:
1. Tier 1: major markets such as `US`, `CN`, `EP/UP`, `JP`
2. Tier 2: important secondary markets such as `KR`, `CA`, `AU`, `IN`
3. Tier 3: other markets

## GIR-18: Weighted Market Reach Must Complement Raw Breadth

Requirement:
Product and analytics layers should expose both:
1. raw geographic breadth,
2. weighted market reach.

Why:
Raw jurisdiction count and commercially weighted reach answer different questions.

## GIR-19: UP Unrolling Must Respect Tier Weighting

Requirement:
After UP states are unrolled into the jurisdiction array, the weighted-market logic must still balance those states against the significance of other major markets such as the US or China.

## Part 6: Point-In-Time Filtering Before Aggregation

## GIR-20: Apply Time Filters Before Family Status Aggregation

Requirement:
When answering current-state questions, the system must first filter or reconstruct legal status at the requested `point_in_time`, then aggregate family metrics.

## GIR-21: Historical Influence Queries Must Drop Current-Enforceability Filters

Requirement:
When answering historical influence questions, the pipeline must keep dead families in scope while still labeling them as no longer active.

## Part 7: Golden Aggregation Sequence

## GIR-22: Mandatory Aggregation Order

Requirement:
To avoid inconsistent outputs, PatentIQ should follow this sequence:

1. fetch raw global family documents,
2. map each `jurisdiction + kind_code` through the normalization table,
3. unroll `C0` / UP geography where applicable,
4. apply `point_in_time` filtering depending on the metric,
5. aggregate normalized stages to the family using max-stage and richer rollups,
6. compute raw and weighted market metrics,
7. compute historical-influence and current-blocking views separately,
8. roll up to the harmonized portfolio owner.

## Mapping To Existing Requirements

This note sharpens several already-existing ideas.

### Overlaps With Existing Docs

1. `DAP-01`, `DAP-11`, `DAP-12`: legal-status and cohort-normalized quality context,
2. `PMC-01`, `PMC-09`, `PMC-13`: family-first analytics and normalized impact,
3. `PKR-14`, `PKR-15`: office-aware kind-code handling and B2 semantics,
4. `UPR-03`, `UPR-04`, `UPR-09`, `UPR-10`: UP unrolling and legal-risk handling,
5. `LSR-01` to `LSR-30`: point-in-time legal-status logic,
6. `FCR-11` and `FCR-12`: family-level adjusted citation impact.

### Net-New Additions

1. RCF-style age-normalized impact logic,
2. explicit bifurcated portfolio dashboard requirement,
3. normalized jurisdiction + kind-code Rosetta table,
4. tiered market weighting across jurisdictions,
5. explicit aggregation order for global family analytics.

## Delivery Priority

### P0

1. jurisdiction + kind-code normalization table,
2. point-in-time legal filtering,
3. bifurcated portfolio analytics,
4. family-level citation normalization support,
5. weighted market reach metric.

### P1

1. formal RCF endpoint or ranking field,
2. richer market-tier reporting,
3. UI explanation of historical vs current influence.

### P2

1. more advanced market-tier calibration,
2. expanded cross-office value-multiplier experimentation.

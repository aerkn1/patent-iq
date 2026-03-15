# OECD Quality Nature Of Innovation Requirements

## Source

User-provided implementation guidance captured on March 8, 2026, layered on top of:
1. `docs/oecd-patent-quality/oecd-patent-quality-definitions-and-feature-mapping.md`
2. the OECD source files already stored in `docs/oecd-patent-quality/`

## Purpose

Define how PatentIQ should incorporate OECD patent-quality concepts as a new analytical dimension describing the nature and behavior of innovation, rather than treating quality as only a citation-count or size proxy.

## Core Principle

PatentIQ currently models:
1. size or reach,
2. legal status,
3. citation volume and influence.

The OECD framework adds a distinct dimension:
`nature_of_innovation`

This dimension explains:
1. how broadly a patent influences downstream fields,
2. how creatively it combines prior domains,
3. how radical or cross-domain the inventive step is,
4. how to correct citation-window bias for recent patents.

## What OECD Adds To The Architecture

## OQN-01: OECD Does Not Replace WIPO Or CPC Mapping

Requirement:
PatentIQ must not treat the OECD framework as a replacement for CPC/IPC/WIPO field mapping.

Why:
OECD indicators depend on field mapping and citation-network structure; they are an overlay on top of the existing field taxonomy, not a substitute for it.

## OQN-02: OECD Adds A New “Nature Of Innovation” Layer

Requirement:
PatentIQ should treat OECD-derived quality indicators as a new layer that explains the character of innovation rather than only its volume, legal status, or market footprint.

## Generality

## OQN-03: Generality Upgrades Technological Breadth

Requirement:
PatentIQ should use OECD-style generality to refine the understanding of downstream technological breadth.

Interpretation:
If a family is cited by later patents across many different WIPO fields, it has high generality and behaves more like a foundational bottleneck technology.

## OQN-04: Generality Belongs In The Enforceability-Side Breadth Story

Requirement:
Generality should be used to enrich the technological-breadth and blocking-scope interpretation inside enforceability-oriented views.

Important:
It does not replace local enforceability math. It explains how many sectors the protected bottleneck appears to touch downstream.

## Originality And Radicalness

## OQN-05: Originality Upgrades Heritage Logic

Requirement:
PatentIQ should use OECD-style originality to refine heritage and pioneer interpretation by analyzing how diverse the backward-citation field mix is.

## OQN-06: Radicalness Captures Cross-Field Inventive Import

Requirement:
PatentIQ should use radicalness to identify inventions that cite prior art from outside their own core field and therefore represent cross-domain recombination.

## OQN-07: Radicalness Can Override Simple Crowdedness Penalties

Requirement:
If a family has many backward citations, the platform should not automatically treat it as merely incremental when the originality or radicalness profile is unusually high.

Why:
High backward-citation volume can still reflect breakthrough recombination rather than simple crowdedness.

## Citation Window / Truncation Fix

## OQN-08: Use OECD Fixed Citation Windows For Fair Comparability

Requirement:
PatentIQ should prefer fixed-window forward-citation indicators such as `fwd_cits5` and `fwd_cits7` when comparing cohorts with different observation lengths.

Why:
This reduces the unfair advantage older patents receive simply because they have had more time to accumulate citations.

## OQN-09: Fixed-Window Citation Features Belong In The Silver Layer

Requirement:
The citation-impact layer should incorporate OECD truncation-aware indicators before downstream scoring, ranking, or ML feature generation.

## Cohort Normalization Validation

## OQN-10: OECD Explicitly Validates Cohort-Based Interpretation

Requirement:
PatentIQ should continue interpreting quality indicators at the cohort level, especially by:
1. filing year,
2. technology field.

Why:
This matches both the OECD methodology and the platform’s existing percentile/rank-based scoring direction.

## OQN-11: OECD Metrics Must Not Be Compared As Raw Global Values

Requirement:
OECD-derived indicators such as generality, originality, radicalness, grant lag, and forward-citation windows must not be interpreted as globally comparable raw numbers without cohort context.

## Silver-Layer Implementation Guidance

## OQN-12: Compute Generality Using Field Concentration Of Forward Citations

Requirement:
PatentIQ should compute generality from the field distribution of forward citations, using the WIPO field mapping of the citing patents or families.

Computation-order rule:
This should be calculated after collapsing and deduplicating the citation pool at family level, not by averaging per-patent generality scores.

Reference:
`oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`

Recommended structure:

`Generality = 1 - SUM((share of forward citations by WIPO field)^2)`

Interpretation:
This is an HHI-style diversity measure over the downstream field mix.

## OQN-13: Compute Originality Using Field Concentration Of Backward Citations

Requirement:
PatentIQ should compute originality from the field distribution of backward citations, using the WIPO field mapping of the cited prior-art families.

Recommended structure:

`Originality = 1 - SUM((share of backward citations by WIPO field)^2)`

Computation-order rule:
This should be calculated from the deduplicated family-level backward citation pool rather than by averaging member-level originality values.

## OQN-13A: Backward NPL Citations Must Remain A Separate Science-Grounding Feature

Requirement:
PatentIQ must not silently merge backward NPL references into patent-only originality, crowdedness, or blocking-power metrics.

Rule:
1. backward patent citations remain the default patent-network input for originality and crowdedness,
2. backward NPL citations should feed a separate `science_grounding` or `research_intensity` feature family,
3. any blended patent-plus-NPL originality variant must be explicitly labeled as a derived extension rather than the default OECD-style interpretation.

Recommended outputs:
1. `backward_patent_citation_count_clean`
2. `backward_npl_citation_count`
3. `science_grounding_score`

Product implication:
The UI may use high-NPL signals to communicate that a family is science-linked or research-grounded, but it must not imply stronger current blocking power solely from NPL density.

## OQN-14: Radicalness Should Compare Outside-Field Dependence

Requirement:
PatentIQ should define radicalness by measuring how much a family’s backward-citation structure relies on fields outside the family’s own primary or mapped field set.

## Product Use Cases

## OQN-15: Generality Supports “Foundational Bottleneck” Messaging

Requirement:
The UI should be able to explain that a family is not only strong in one field, but also exhibits high downstream generality across other sectors.

## OQN-16: Originality And Radicalness Support “Breakthrough Recombination” Messaging

Requirement:
The UI should be able to highlight when a family combines ideas from distant fields and therefore looks like a radical or cross-domain breakthrough rather than a routine continuation.

## OQN-17: OECD Tags Should Be Explainable

Requirement:
If PatentIQ exposes labels such as:
1. `High Generality`
2. `Radical Innovation`
3. `Cross-Field Pioneer`

the product must also expose the underlying metric logic and peer context.

## Relationship To Existing Notes

This note extends the existing OECD definitions into the March 8 family/legal/analytics cluster.

### Overlaps With Existing Docs

1. `docs/oecd-patent-quality/oecd-patent-quality-definitions-and-feature-mapping.md`
2. `citation-semantics-and-tech-field-mapping-requirements.md`
3. `wipo-field-contribution-timeseries-requirements.md`
4. `score-dimensionality-and-citation-weighting-requirements.md`
5. `blocking-power-market-citation-fusion-requirements.md`
6. `oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`

### Net-New Additions

1. `nature_of_innovation` as an explicit analytical dimension,
2. generality as downstream breadth enrichment,
3. originality and radicalness as heritage upgrades,
4. fixed-window citation metrics as truncation controls,
5. HHI-style formulas for OECD field-diversity metrics,
6. collapse-first family computation for OECD quality metrics.

## Delivery Priority

### P0

1. cohort-safe ingestion of OECD indicators,
2. use of `fwd_cits5` and `fwd_cits7`,
3. generality/originality/radicalness fields available in marts and APIs,
4. explainable OECD tags in UI.

### P1

1. custom in-pipeline HHI recomputation from citation networks,
2. stronger product messaging around foundational bottlenecks and radical recombination,
3. integration into portfolio compare and peer benchmarking surfaces.

### P2

1. richer composite quality narratives,
2. more advanced OECD-driven clustering and insight drafting.

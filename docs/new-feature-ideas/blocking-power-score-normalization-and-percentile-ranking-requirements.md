# Blocking Power Score Normalization And Percentile Ranking Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ must convert raw blocking-power math into bounded, interpretable UI scores without distorting the extreme power-law distribution of patent value.

## Core Principle

PatentIQ must explicitly separate:
1. the absolute score used as the raw mathematical output of the model,
2. the normalized score shown to users in the UI.

The raw score answers:
"What is the unbounded strategic value implied by the underlying formula?"

The normalized score answers:
"Where does this family rank relative to its peers in the relevant cohort?"

## Why Raw Sums Cannot Be Shown Directly

## BNS-01: Absolute Scores Are Unbounded

Requirement:
The blocking-power math may legitimately produce raw scores with very different magnitudes across families.

Implication:
Raw values such as `2.5`, `42.8`, or `845.2` are not inherently interpretable to end users unless they are contextualized against a peer group.

## BNS-02: UI Scores Must Be Human-Interpretable

Requirement:
The UI-facing blocking-power score should be a bounded, immediately understandable metric rather than a naked raw sum.

## Why Min-Max Scaling Must Be Rejected

## BNS-03: Do Not Use Min-Max Scaling For Blocking Power UI Scores

Requirement:
PatentIQ must not normalize blocking-power UI scores using simple min-max scaling across the patent population.

Why:
Patent data typically follows a highly skewed power-law distribution, so min-max scaling compresses almost all normal patents into a near-zero band and overreacts to a few extreme outliers.

## BNS-04: Outlier-Driven Compression Is A Product Failure Mode

Requirement:
The scoring design must explicitly avoid normalization methods that cause most families to collapse into an unusably narrow range such as `1-4`.

## Percentile Ranking As The UI Normalization Layer

## BNS-05: UI Blocking Power Should Use Point-In-Time Percentile Ranking

Requirement:
PatentIQ should convert raw blocking-power scores into UI scores using percentile rank against a relevant peer cohort.

Interpretation:
The UI score is not a rescaled raw number. It is a relative ranking measure.

## BNS-06: Percentile Ranking Must Be Point-In-Time

Requirement:
Percentile calculation must be performed within the requested time cohort rather than across all history.

Why:
The competitive meaning of a score depends on the peer landscape at that date.

## BNS-07: Default Cohort For Field Scores

Requirement:
For field-specific blocking-power views, the percentile cohort should default to:
1. active families,
2. inside the same `wipo_field`,
3. at the same `snapshot_date` or `snapshot_year`.

## BNS-08: Percentile Interpretation Must Be Preserved

Requirement:
A UI blocking-power score of `95` should mean that the family outranks roughly 95% of its peer cohort on the underlying raw score.

## Recommended SQL Method

## BNS-09: Use Percentile Window Functions In DuckDB

Requirement:
The gold-layer normalization step should use SQL window functions such as `PERCENT_RANK()` to derive UI scores from raw absolute scores.

## BNS-10: Recommended SQL Pattern

Recommended structure:

```sql
SELECT
    docdb_family_id,
    wipo_field,
    snapshot_year,
    raw_absolute_score,
    ROUND(
        PERCENT_RANK() OVER (
            PARTITION BY wipo_field, snapshot_year
            ORDER BY raw_absolute_score ASC
        ) * 100,
        1
    ) AS ui_blocking_power_score
FROM family_absolute_scores;
```

## Raw Versus Normalized Data Model

## BNS-11: Store Raw And UI Scores Separately

Requirement:
PatentIQ should persist both:
1. the raw absolute blocking-power score,
2. the normalized percentile-based UI score.

Fusion rule:
The raw absolute blocking-power score should already be the fused market-plus-citation score rather than a legal-only intermediate.

Reference:
`blocking-power-market-citation-fusion-requirements.md`

Why:
The raw score is required for auditability, decomposition, and future re-normalization. The UI score is required for intuitive product behavior.

## BNS-12: Do Not Overwrite Raw Scores With Normalized Scores

Requirement:
Normalized scores must not replace the raw values in marts or APIs that need explainability or decomposition.

## BNS-13: Metadata Must Expose Normalization Method

Requirement:
Any mart or API serving UI scores should expose metadata such as:
1. `normalization_method`,
2. `cohort_definition`,
3. `snapshot_date`,
4. `counting_unit`,
5. `family_model`.

## Cohort Design Rules

## BNS-14: Percentile Cohorts Must Be Semantically Relevant

Requirement:
The cohort used for percentile normalization must match the view being shown.

Examples:
1. field leaderboard uses same-field cohort,
2. current blocking-power card uses current active cohort,
3. historical chart uses historical point-in-time cohort.

## BNS-15: Current And Historical Cohorts Must Stay Separate

Requirement:
Current-state normalized scores must not be computed against historical or dead-family-inclusive cohorts unless that scope is explicitly intended.

## BNS-16: Heritage And Enforceability Scores Must Not Share The Same Cohort By Default

Requirement:
If percentile normalization is applied to both heritage and enforceability metrics, each should use its own semantically correct peer cohort rather than a blended one.

## Product Expectations

## BNS-17: UI Score Must Always Be Clearly Labeled As Relative

Requirement:
The product should communicate that the 1-100 blocking-power score is a percentile-like peer ranking, not an absolute physical quantity.

## BNS-18: Expert Views Should Still Allow Raw-Score Inspection

Requirement:
Advanced or audit views should allow inspection of the underlying absolute score and its contributing components.

## BNS-19: Similar UI Scores Across Fields Must Be Understood As Relative Within Cohort

Requirement:
A score of `45` in AI and a score of `45` in Typewriters should be interpreted as “slightly below average for that field,” not as identical raw strategic value.

## Relationship To Existing Notes

This note refines the score-presentation layer of the broader blocking-power model.

### Overlaps With Existing Docs

1. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
2. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
3. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`
4. `wipo-field-contribution-timeseries-requirements.md`
5. `blocking-power-market-citation-fusion-requirements.md`

### Net-New Additions

1. explicit raw-versus-normalized score separation,
2. percentile ranking as the default UI normalization method,
3. rejection of min-max scaling,
4. cohort-specific normalization rules,
5. raw-score preservation requirements.

## Delivery Priority

### P0

1. raw score storage,
2. percentile-based UI score generation,
3. normalization metadata,
4. cohort definitions for current field-level blocking power.

### P1

1. raw-score audit views,
2. percentile normalization for additional strategic score types,
3. richer cohort-selection options for expert workflows.

### P2

1. advanced cross-cohort benchmarking tools,
2. alternative robust normalization experiments for internal validation only.

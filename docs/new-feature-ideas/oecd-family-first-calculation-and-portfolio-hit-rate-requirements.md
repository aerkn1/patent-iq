# OECD Family-First Calculation And Portfolio Hit-Rate Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define the correct computation order for OECD-style quality metrics in PatentIQ and specify how those family-level metrics should be rolled up to the portfolio level without mathematically distorting the signal.

## Core Principle

PatentIQ must not calculate OECD quality metrics at the patent or publication level and then average them up to the family.

For highest reliability, the pipeline must:
1. collapse citation evidence to the family first,
2. deduplicate cited and citing families,
3. compute the metric at family level,
4. normalize against the correct family cohort,
5. aggregate to portfolios using hit-rate style density metrics rather than simple means.

## Why Patent-Level Aggregation Fails

## OFF-01: Patent-Level Averaging Can Destroy Family Originality

Requirement:
PatentIQ must not average per-patent originality, generality, or radicalness values to obtain a family score.

Why:
Different family members often expose different parts of the same invention’s citation structure across jurisdictions. Averaging member-level metrics can erase cross-field diversity that only becomes visible after pooling.

## OFF-02: Cross-Jurisdiction Citation Redundancy Must Be Deduplicated

Requirement:
If multiple family members cite the same prior-art family, or are cited by the same later family, that relationship should be counted once in family-level OECD calculations.

Why:
Without deduplication, the family’s citation structure is inflated by office-level administrative redundancy rather than real technological diversity.

## Collapse-First Computation Order

## OFF-03: Pool All Relevant Family Documents First

Requirement:
The pipeline should collect citation evidence from all relevant family documents, including the applicable `A` and `B` members used by the citation model.

## OFF-04: Map Citation Targets And Sources To Families

Requirement:
Before OECD math is run, both backward-cited and forward-citing documents should be mapped to their canonical cited or citing family IDs.

## OFF-05: Deduplicate At The Family Relationship Level

Requirement:
After mapping to family IDs, duplicate citation relationships must be removed before field-distribution metrics are computed.

## OFF-06: Run OECD Diversity Math Only After Collapse And Deduplication

Requirement:
Metrics such as generality and originality should be computed only after the family’s clean forward and backward citation pools have been assembled.

## OFF-07: Family Generality Formula Uses Deduplicated Forward-Citing Families

Requirement:
Family-level generality should be computed from the deduplicated forward-citing family set and the field distribution of those citing families.

## OFF-08: Family Originality Formula Uses Deduplicated Backward-Cited Families

Requirement:
Family-level originality should be computed from the deduplicated backward-cited family set and the field distribution of those cited families.

## Cohort Normalization

## OFF-09: Family OECD Metrics Must Be Cohort-Normalized At Family Level

Requirement:
After family-level OECD metrics are calculated, they should be normalized against peer families rather than peer applications.

## OFF-10: Family Cohort Anchor Uses Earliest Priority Year

Requirement:
Because a family may have members filed in different years, the family should be cohort-anchored using its earliest priority year for OECD-style normalization unless a more specific methodology is explicitly documented.

## OFF-11: Primary Field For Cohort Ranking Must Be Defined Explicitly

Requirement:
When percentile-normalizing family OECD metrics, PatentIQ should use the agreed primary WIPO field or equivalent family field anchor and document that choice in metadata.

## Portfolio Rollup Logic

## OFF-12: Do Not Use Mean OECD Scores As The Default Portfolio Rollup

Requirement:
PatentIQ should not rely on simple portfolio averages of family OECD scores as the primary summary metric.

Why:
Patent portfolios exhibit highly skewed, power-law behavior. Means are easily distorted by long tails and do not communicate the density of standout assets well.

## OFF-13: Use Decile Or Percentile Hit Rates For Portfolio Quality Density

Requirement:
Portfolio-level OECD quality views should emphasize hit-rate style metrics such as:
1. share of active families in the top 10% for generality,
2. share of active families in the top 10% for originality,
3. share of active families in the top 10% for radicalness.

## OFF-14: Portfolio OECD Views Should Be Framed As Quality Density

Requirement:
The product should express portfolio OECD rollups as density of high-performing families rather than only average score.

Examples:
1. percentage of active families that are highly radical,
2. percentage of active families with high generality,
3. share of families with top-decile originality.

## MVP Proxy Rule

## OFF-15: Representative Member Rule Is An Acceptable Interim Proxy

Requirement:
If the MVP must rely on precomputed OECD application-level files and there is not enough time to rebuild the full collapse-first citation engine, PatentIQ may use a representative-member proxy at the family level.

## OFF-16: Representative Member Selection Must Be Explicit

Requirement:
If the representative-member proxy is used, the selection rule must be explicit and deterministic, such as:
1. highest citation-count member,
2. strongest granted member,
3. highest legal stage member.

## OFF-17: Representative-Member Proxy Must Be Labeled As Temporary

Requirement:
Any family-level OECD metric derived from representative-member selection rather than true collapse-first recalculation must be labeled as a proxy in metadata and planning docs.

## Relationship To Existing Notes

This note operationalizes the family-first rule specifically for OECD quality metrics.

### Overlaps With Existing Docs

1. `oecd-quality-nature-of-innovation-requirements.md`
2. `family-level-collapse-and-metric-calculation-requirements.md`
3. `citation-semantics-and-tech-field-mapping-requirements.md`
4. `docs/oecd-patent-quality/oecd-patent-quality-definitions-and-feature-mapping.md`

### Net-New Additions

1. explicit prohibition on patent-level-then-average OECD scoring,
2. collapse-first citation-pool pipeline for OECD metrics,
3. earliest-priority-year cohort anchoring for families,
4. portfolio hit-rate rollups instead of mean-based rollups,
5. representative-member proxy rule for MVP fallback.

## Delivery Priority

### P0

1. family-first OECD computation order,
2. family-level deduplication of citation pools,
3. family-cohort normalization,
4. portfolio hit-rate summaries.

### P1

1. full in-pipeline recomputation of OECD metrics from raw citation pools,
2. richer portfolio density views by field and owner,
3. metadata and UI disclosure for proxy versus true family calculations.

### P2

1. advanced portfolio quality decomposition,
2. more granular quality-density benchmarking by cohort and competitor.

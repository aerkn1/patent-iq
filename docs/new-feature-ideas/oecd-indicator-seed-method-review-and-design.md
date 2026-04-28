# OECD Indicator Seed Method Review And Design

## Purpose

Define what is already fixed by OECD methodology, what is already fixed by PatentIQ notes, and what remains a deliberate PatentIQ family-first adaptation before building `oecd_indicator_seed.parquet`.

This note is intended to prevent a common failure mode:
1. treating the current `silver_family_oecd_quality` proxy mart as the final OECD layer,
2. silently mixing patent-level OECD formulas with family-level PatentIQ marts,
3. generating a seed file without explicit cohort, window, and normalization policy.

## Source Order

Review order for method decisions:
1. official OECD paper and dissemination notes,
2. local OECD notes in `docs/oecd-patent-quality/`,
3. local family-first and citation notes in `docs/new-feature-ideas/` and `docs/next-phase-v2/`,
4. supporting citation literature where OECD leaves room for implementation choice.

Primary sources:
1. OECD, *Measuring Patent Quality: Indicators of Technological and Economic Value*.
2. local note `docs/oecd-patent-quality/oecd-patent-quality-definitions-and-feature-mapping.md`.
3. local note `docs/new-feature-ideas/oecd-quality-nature-of-innovation-requirements.md`.
4. local note `docs/new-feature-ideas/oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`.

## What OECD Already Fixes

### OECD-01: Cohort Interpretation

OECD indicators are intended to be interpreted within cohorts rather than as globally comparable raw values.

Stable methodology:
1. cohort anchor uses year,
2. cohort segmentation uses technology field,
3. normalized indicators should be compared only against peer inventions in the same cohort.

For PatentIQ:
1. raw metric generation and cohort statistics must remain separate concepts,
2. the seed should preserve both raw values and cohort metadata.

### OECD-02: Forward Citation Windows

OECD forward-citation indicators are publication-window metrics.

Stable methodology:
1. `fwd_cits5` means forward citations observed within 5 years after publication,
2. `fwd_cits7` means forward citations observed within 7 years after publication,
3. recent cohorts are truncation-sensitive.

For PatentIQ:
1. fixed windows are mandatory,
2. raw lifetime forward-citation totals should not replace `fwd_cits5` and `fwd_cits7`,
3. recent-year rows should carry an observation-completeness flag or similar disclosure.

### OECD-03: Diversity Metrics

OECD-style generality and originality are diversity measures over field distributions.

Recommended structure already aligned with local notes:
1. `generality = 1 - SUM(share_of_forward_citing_field^2)`
2. `originality = 1 - SUM(share_of_backward_cited_field^2)`

These are HHI-style inverse concentration measures.

### OECD-04: Composite Indexes

The OECD paper defines experimental quality composites:
1. `quality_index_4`: forward citations, family size, claims, generality.
2. `quality_index_6`: the same plus backward citations and grant lag.

The OECD paper also makes clear that these composites:
1. are experimental,
2. rely on normalized components,
3. should be disclosed with their component definitions.

## What PatentIQ Notes Already Fix

### PIQ-01: Family-First Computation Order

PatentIQ must not compute OECD metrics at patent level and then average them up to family.

Already fixed by local notes:
1. assemble citation evidence across family members first,
2. map sources and targets to family ids,
3. deduplicate at family relationship level,
4. compute OECD metrics at family grain,
5. only then normalize within family cohorts.

### PIQ-02: Patent And NPL Separation

Backward NPL references remain a separate science-grounding layer.

Already fixed by local notes:
1. backward patent citations drive originality and crowdedness,
2. backward NPL citations drive science-grounding or research-intensity companion metrics,
3. any blended NPL-plus-patent originality variant must be explicitly labeled as derived.

### PIQ-03: Family Cohort Normalization Anchor

PatentIQ notes already prefer earliest-priority-year anchoring for family-level OECD normalization.

That is a deliberate family-first adaptation, not a contradiction of OECD intent.

Interpretation:
1. OECD patent-level files use filing year,
2. PatentIQ family-level cohorts should use `family_priority_year`,
3. this keeps the cohort anchor stable even when family members publish across different years.

### PIQ-04: Primary Field Requirement

PatentIQ notes already require a defined family field anchor for normalization.

For the seed:
1. preserve `primary_wipo_field`,
2. optionally preserve `family_tech_breadth_wipo_count`,
3. document any many-field behavior explicitly.

## Family-First Design Decisions

These decisions are now fixed for the seed design unless a later note explicitly overrides them.

### DD-01: Window Anchor

Use `earliest_family_publication_date` to determine whether a forward citation falls inside the `5y` or `7y` observation window.

Reason:
1. OECD forward citations are publication-window indicators,
2. a priority-year anchor would start the clock before citations can reasonably occur,
3. family-first PatentIQ still needs a publication-based observation window even if cohort normalization uses priority year.

### DD-02: Cohort Anchor

Use `family_priority_year` plus `primary_wipo_field` for family-level OECD cohort normalization.

Reason:
1. this is already specified in PatentIQ notes,
2. it is the cleanest family-level analogue to OECD filing-year cohorts,
3. it avoids instability caused by later member publications.

### DD-03: Citation Pool Grain

Use deduplicated family-to-family relationships as the default pool for:
1. `generality`,
2. `originality`,
3. `radicalness`.

Reason:
1. this is already mandated by local family-first notes,
2. it removes cross-office redundancy,
3. it prevents member-level administrative duplication from inflating diversity.

### DD-04: Radicalness Logic

Define radicalness as outside-field dependence of the deduplicated backward patent-family pool relative to the focal family's own field set.

Default implementation:
1. identify the focal family's primary or mapped field set,
2. compute the share of backward-cited families that fall outside that set,
3. retain the raw outside-field share and a normalized cohort-relative score.

This is consistent with existing PatentIQ notes even though radicalness is less mechanically standardized than generality/originality in many public secondary summaries.

### DD-05: Composite Index Policy

Generate both:
1. raw component values,
2. cohort-normalized component values,
3. then compose `quality_index_4` and `quality_index_6` from normalized components only.

Default composite rule:
1. unweighted mean of normalized components,
2. preserve component columns so the composite never becomes opaque.

This matches the OECD direction and is the safest default unless a later product note explicitly requests weighted composites.

Current implementation note:
1. `quality_index_4` and `quality_index_6` are materialized as explicit family-first variants,
2. the claims component is currently omitted because there is no safe corpus-wide claims count,
3. the omission is labeled in-schema as `claims_omitted_family_first_variant` rather than hidden behind a silent proxy.

## Recommended Seed Schema

Minimum viable `oecd_indicator_seed.parquet` rows should be long-form, one indicator per family:

1. `docdb_family_id`
2. `family_priority_year`
3. `primary_wipo_field`
4. `indicator_name`
5. `indicator_value_raw`
6. `indicator_value_normalized`
7. `normalization_basis`
8. `observation_window_years`
9. `is_truncation_sensitive`
10. `cohort_size`
11. `snapshot_year`
12. `method_version`
13. `is_proxy`
14. `source_family_grain`

Recommended initial `indicator_name` set:
1. `fwd_cits5`
2. `fwd_cits7`
3. `generality`
4. `originality`
5. `radicalness`
6. `bwd_cits`
7. `npl_cits`
8. `science_grounding`
9. `family_size`
10. `grant_lag`
11. `quality_index_4`
12. `quality_index_6`

## What We Can Build Now

Using current Bronze and Silver inputs, PatentIQ can already build:
1. `fwd_cits5`
2. `fwd_cits7`
3. `generality`
4. `originality`
5. `radicalness`
6. backward patent citation counts
7. backward NPL counts
8. science-grounding companion metric
9. family-size companion metric
10. family-level `grant_lag`
11. explicit family-first `quality_index_4` / `quality_index_6` variants with the claims omission labeled

These inputs already exist across:
1. `silver_enriched_citation_network`
2. `silver_family_citation_metrics`
3. `silver_family_wipo_fields`
4. `silver_family_member_publications`
5. `silver_family_npl_backlinks`
6. `silver_family_core`

## What Still Requires Explicit Product Choice

Before generation, the following must be locked in deliberately:

1. exact `grant_lag` construction at family grain,
2. whether `quality_index_4` and `quality_index_6` should be:
   - strict OECD-style composites,
   - or PatentIQ-labeled family-first adaptations,
3. whether normalized values should be:
   - z-scores,
   - percentile ranks,
   - or both,
4. truncation policy for the newest cohorts:
   - include with warning,
   - or suppress incomplete cohorts in the seed.

Recommended resolution after source review:
1. store both percentile rank and z-score in the rich seed,
2. treat percentile rank as the canonical exposed normalization for product and benchmark views,
3. treat z-score as the secondary analytical normalization for modeling or composite experimentation.

## Recommended Next Build Order

1. materialize a family-level OECD cohort stats table,
2. generate raw `fwd_cits5`, `fwd_cits7`, `generality`, `originality`, and `radicalness`,
3. normalize them within `family_priority_year x primary_wipo_field`,
4. add explicit metadata flags for truncation and proxy status,
5. then materialize `oecd_indicator_seed.parquet`,
6. only after that decide whether Bronze should ingest the seed as a reference or whether Silver should consume it directly.

## Practical Bottom Line

The missing OECD seed is not blocked by Bronze.

PatentIQ already has enough data to generate a strong internal family-first OECD seed now.

What remains is not raw-data absence but methodology packaging:
1. formalize the cohort-stat table,
2. lock the family-grain grant-lag rule,
3. decide whether composite indexes are strict OECD replicas or PatentIQ family-first variants.

# OECD Indicator Seed Build Spec

## Goal

Define the exact artifact, columns, build order, and minimum methodology needed to generate `oecd_indicator_seed.parquet` from the data already present in Bronze and Silver.

This spec assumes:
1. no full Bronze rerun is required,
2. the current Silver citation and field layers are the main computational base,
3. the seed is a reusable reference-style artifact, not a replacement for Silver marts.

## Artifact Scope

Implemented artifact set:
1. `etl/data/raw/refs/oecd_indicator_seed.parquet`
2. `etl/data/raw/refs/oecd_indicator_cohort_stats.parquet`
3. `etl/data/raw/refs/oecd_indicator_longform.parquet`
4. `etl/data/raw-bounded/refs/oecd_quality_indicator_seed.parquet`
5. `etl/data/bronze/bronze_ext_oecd_indicator_seed.parquet`

Artifact roles:
1. the seed is the wide family-level raw base,
2. the cohort companion carries normalization context,
3. the long-form artifact carries normalized family-by-indicator rows plus explicit composite variants,
4. the bounded/Bronze projection closes the Bronze reference contract using the long-form artifact as source.

Optional follow-on copy for Bronze contract completeness:
1. `etl/data/raw-bounded/refs/oecd_indicator_seed.parquet`
2. `etl/data/bronze/bronze_ext_oecd_indicator_seed.parquet`

Primary use:
1. benchmark-style OECD metric seed,
2. reusable family-level quality overlay,
3. future Gold / ML / API / portfolio analytics input.

## Build Inputs

Required current inputs:
1. `silver_family_core`
2. `silver_family_wipo_fields`
3. `silver_family_member_publications`
4. `silver_enriched_citation_network`
5. `silver_family_citation_metrics`
6. `silver_family_npl_backlinks`

Helpful optional inputs:
1. `silver_family_field_contributions`
2. `silver_family_status_pt`
3. `silver_family_enforceability_branches`

## Grain

Current implementation uses two complementary grains:
1. wide family-level raw seed in `oecd_indicator_seed.parquet`,
2. long-form normalized projection in `oecd_indicator_longform.parquet`.

Why:
1. the wide seed is tractable to compute and easy to audit,
2. the long-form projection is better for Bronze compatibility and downstream benchmarking,
3. separating them keeps the raw family artifact stable while allowing richer normalized views.

## Minimum Required Columns

To stay compatible with the existing Bronze contract, every row must include:
1. `appln_id`
2. `docdb_family_id`
3. `indicator_name`
4. `indicator_value`
5. `snapshot_year`

Recommended additional columns for the raw seed before any Bronze projection:
1. `family_priority_year`
2. `primary_wipo_field`
3. `indicator_value_raw`
4. `indicator_value_normalized`
5. `normalization_basis`
6. `cohort_size`
7. `observation_window_years`
8. `is_truncation_sensitive`
9. `is_proxy`
10. `method_version`
11. `source_family_grain`

Implementation note:
1. if Bronze remains unchanged, a projection step can emit the required 5-column contract from the richer seed table,
2. the richer file should still be kept on disk because it is more useful than the minimal Bronze contract.

## Default Indicator Set

### P0

These should be generated first:
1. `fwd_cits5`
2. `fwd_cits7`
3. `generality`
4. `originality`
5. `radicalness`
6. `bwd_cits`
7. `npl_cits`
8. `science_grounding`

### P1

These can be added from the same base:
1. `family_size`
2. `grant_lag`
3. `quality_index_4`
4. `quality_index_6`

## Family Anchors

### Cohort Anchor

Use:
1. `family_priority_year`
2. `primary_wipo_field`

This is the family-level normalization cohort.

### Citation Window Anchor

Use:
1. `family_earliest_publication_date`

Fallback only if that is missing:
1. `family_earliest_priority_date`

## Computation Rules

### `fwd_cits5`

Definition:
1. count distinct clean forward-citing families
2. whose first clean citation date falls within 5 years of the focal family publication anchor

Rules:
1. exclude intra-family citations,
2. exclude self-citations,
3. exclude out-of-bounds ghost citations,
4. count distinct citing families, not citation events.

### `fwd_cits7`

Same as above, but 7-year window.

### `generality`

Definition:
1. compute the distribution of deduplicated forward-citing families across WIPO fields,
2. calculate `1 - SUM(share^2)`.

Rules:
1. field source is the citing family's primary WIPO field,
2. the forward pool must already be family-collapsed and deduplicated.

### `originality`

Definition:
1. compute the distribution of deduplicated backward-cited patent families across WIPO fields,
2. calculate `1 - SUM(share^2)`.

Rules:
1. use backward patent-family citations only,
2. do not silently merge NPL references into this metric.

### `radicalness`

Definition:
1. measure the share of backward-cited patent families that fall outside the focal family field set.

Default field set:
1. `primary_wipo_field` plus any covered family WIPO fields when available.

Recommended raw formula:
1. `outside_field_backward_share = backward_cited_families_outside_field_set / all_deduplicated_backward_cited_families`

### `bwd_cits`

Definition:
1. deduplicated backward patent-family count.

### `npl_cits`

Definition:
1. backward NPL reference count for the family.

### `science_grounding`

Definition:
1. normalized family-level science-linkage companion score derived from `npl_cits`
2. optionally blended with clean backward patent volume only if explicitly labeled

Default policy:
1. keep it separate from originality and blocking power.

## Cohort Statistics

To support normalization, build a companion cohort table first:

Suggested artifact:
1. `etl/data/temp/oecd_indicator_cohort_stats.parquet`

Grain:
1. `family_priority_year x primary_wipo_field x indicator_name`

Columns:
1. `family_priority_year`
2. `primary_wipo_field`
3. `indicator_name`
4. `cohort_size`
5. `mean`
6. `std_dev`
7. `p10`
8. `p25`
9. `p50`
10. `p75`
11. `p90`
12. `p99`
13. `max`

Normalization outputs:
1. percentile rank,
2. optional z-score,
3. keep both if disk budget is acceptable.

Recommended default after source review:
1. store percentile rank as the canonical exposed normalized value,
2. also store z-score in the rich seed as a secondary analytical field,
3. use percentile rank for product displays, cohort benchmarking, and threshold tags,
4. use z-score for modeling or composite experimentation where distance from cohort center matters.

## Composite Indicators

### `quality_index_4`

Current implemented policy:
1. explicit family-first variant,
2. normalized `fwd_cits5`,
3. normalized `family_size`,
4. normalized `generality`,
5. claims component omitted and labeled as `claims_omitted_family_first_variant`.

### `quality_index_6`

Components:
1. current `quality_index_4` variant components
2. normalized `bwd_cits`
3. normalized `grant_lag`

Default rule:
1. unweighted mean of normalized components

Important:
1. the current implementation keeps the claims omission explicit in-schema rather than silently substituting a weak proxy.

## `appln_id` Policy

The current Bronze contract expects `appln_id`, but the seed is family-level.

Default rule:
1. choose a deterministic representative `appln_id` per family,
2. use the earliest-priority application when available,
3. otherwise use the lowest `appln_id` in the family.

This field should be treated as a compatibility anchor, not as the true metric grain.

## `snapshot_year` Policy

Default:
1. use the build year of the seed as `snapshot_year`

This is a publication/dissemination stamp, not the cohort anchor.

## Truncation Policy

Forward-window metrics are truncation-sensitive for recent cohorts.

Default:
1. include rows for all cohorts,
2. mark `is_truncation_sensitive = true` when the full 5-year or 7-year window is not observable,
3. avoid suppressing the rows entirely in the seed.

## Recommended Build Order

1. derive family anchors:
   - representative `appln_id`
   - `family_priority_year`
   - `family_earliest_publication_date`
   - `primary_wipo_field`
2. assemble deduplicated clean forward citation family pools
3. assemble deduplicated clean backward patent-family citation pools
4. assemble backward NPL family pools
5. compute raw family-level OECD indicators
6. build cohort statistics table
7. compute normalized values
8. materialize the long-form seed
9. if desired, project the richer seed into the current Bronze 5-column contract

## First Implementation Recommendation

First implementation should generate only:
1. `fwd_cits5`
2. `fwd_cits7`
3. `generality`
4. `originality`
5. `radicalness`
6. `bwd_cits`
7. `npl_cits`
8. `science_grounding`

Reason:
1. current Silver already has the needed inputs,
2. these are the strongest note-aligned indicators,
3. they avoid premature grant-lag / claims-proxy decisions.

## Quality Gates

Minimum audit after generation:
1. no duplicate `docdb_family_id x indicator_name` rows,
2. no missing `primary_wipo_field` for normalized rows,
3. no missing `family_priority_year` for normalized rows,
4. `fwd_cits5 <= fwd_cits7`,
5. `generality`, `originality`, `radicalness` all in valid bounded ranges,
6. no silent inclusion of NPL citations in originality,
7. cohort sizes above an explicit minimum threshold for normalized values.

## Current Implementation Note

The first local implementation materializes:
1. a wide family-level raw seed in `etl/data/raw/refs/oecd_indicator_seed.parquet`

The normalized cohort-stat companion is still planned, but was deferred in the first pass to keep local generation tractable on the bounded mega-cluster slice.

## Practical Bottom Line

PatentIQ already has enough data to generate a strong first `oecd_indicator_seed.parquet` without rerunning full Bronze.

The remaining work is now mainly:
1. optional cohort-stat materialization,
2. later long-form Bronze projection if a downstream consumer requires the generic `indicator_name / indicator_value` contract.

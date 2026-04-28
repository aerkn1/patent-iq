# PatentIQ V2 Mega-Cluster Scope And Ghost-Node Clarification

## Purpose

Make the MVP dataset boundary explicit for implementation teams so there is no ambiguity about:

1. what counts as the in-scope family universe,
2. what a portfolio means inside the MVP,
3. how out-of-bounds citation families are preserved,
4. which analytics must roll only over the in-scope mega-cluster.

This note operationalizes:

1. [mega-cluster-dataset-scope-and-boundary-governance-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md)
2. [march-2026-family-legal-analytics-master-index.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/march-2026-family-legal-analytics-master-index.md)

## Core Rule

PatentIQ MVP does **not** operate on a universal global patent estate.

It operates on a bounded `10-field mega-cluster` family universe.

That means:

1. the canonical family universe is the set of families falling inside the selected 10 WIPO fields,
2. the canonical portfolio universe is the harmonized owner’s family set **within** that mega-cluster,
3. all family and portfolio analytics roll over that bounded in-scope set,
4. out-of-bounds citation relationships are preserved through ghost nodes, not full family ingestion.

## In-Scope Family Universe

The MVP in-scope family universe is:

1. the extracted global family set for the main operating window `2007-2026`,
2. restricted to the 10 WIPO mega-cluster fields already defined in the source requirements.

Heritage and historical citation analytics may additionally use an older mega-cluster backfill horizon, but that backfill must remain explicitly separated from the main operating window.

Implementation meaning:

1. `silver_family_core` should represent the in-scope extracted family universe,
2. all downstream Silver and Gold marts should treat this as the canonical family base,
3. families outside the mega-cluster are not full first-class family objects in the MVP analytical warehouse unless a later expansion explicitly adds them.
4. older mega-cluster families included only for historical support must be flagged separately from main-window families rather than silently merged into current-state analytics.

## In-Scope Portfolio Universe

### What a portfolio means in MVP

A portfolio in MVP means:

`all in-scope mega-cluster families owned by the harmonized assignee / ultimate parent`

It does **not** mean:

`the company’s full universal worldwide patent estate across every industry`

### Required interpretation

For any company, including large conglomerates:

1. portfolio size,
2. hit rate,
3. crown jewel density,
4. blocking power,
5. heritage,
6. attacker leaderboard,
7. comparison,
8. forecast rollups,
9. semantic overlap,

must all be interpreted as:

`within the mega-cluster`

### Required labels

Recommended labels include:

1. `portfolio_size_active_within_mega_cluster`
2. `portfolio_blocking_power_within_mega_cluster`
3. `hit_rate_within_mega_cluster`
4. `forecasted_future_impact_within_mega_cluster`

## Ghost Nodes

### What a ghost node is

A ghost node is an out-of-bounds cited or citing family that remains visible to network math without becoming a full in-scope family object.

Minimum ghost-node metadata should include:

1. family id if resolvable,
2. citation linkage,
3. date context where available,
4. high-level field identity where available,
5. `is_out_of_bounds = TRUE`

### What ghost nodes are used for

Ghost nodes should be included in:

1. patent citation graph integrity,
2. forward and backward citation counts where the method requires them,
3. OECD field-diversity math such as generality and originality,
4. science-grounding and related citation-network diagnostics where applicable.

### What ghost nodes must not receive

Ghost nodes must not receive fabricated:

1. full legal-status reconstruction,
2. full 4D enforceability math,
3. full blocking-power scores,
4. portfolio ownership rollups,
5. complete family detail pages as if they were in-scope assets.

## Rollup Rules

### Family-level analytics

Family-level analytics should roll over:

1. in-scope families as canonical entities,
2. with ghost-node-aware citation and OECD math where required.

### Portfolio-level analytics

Portfolio-level analytics should roll over:

1. in-scope families owned by the harmonized assignee,
2. using in-scope denominators only,
3. while exposing `out_of_bounds_citation_share` or equivalent when ghost nodes materially influence citation-side metrics.

### Comparison-level analytics

Family, portfolio, and assignee comparison workflows should compare:

1. in-scope mega-cluster entities,
2. not implied universal estates,
3. with explicit labeling when sampled semantic layers or ghost-node contributions are involved.

## Implementation Guardrails

1. no Gold mart should label a bounded portfolio metric as universal or total-global,
2. no portfolio denominator should include unseen out-of-scope families,
3. no ghost node should be promoted to a full family analytics object without explicit ingestion,
4. family and portfolio APIs should carry scope metadata,
5. citation and OECD marts should carry ghost-node contribution metadata where material.

## Minimal Required Metadata

Every relevant family or portfolio payload should be able to expose:

1. `scope_type = mega_cluster_bounded`
2. `covered_wipo_fields`
3. `coverage_start_year`
4. `coverage_end_year`
5. `ghost_node_contribution_flag`
6. `out_of_bounds_citation_share`
7. `semantic_sampling_flag` where applicable

## Short Implementation Summary

Use this interpretation everywhere in MVP:

1. `family` = in-scope mega-cluster family
2. `portfolio` = harmonized owner’s in-scope mega-cluster family set
3. `ghost node` = out-of-bounds citation/network stub preserved for math, not a full analytics object

If any UI, API, or mart would imply something broader than that, it should be renamed or relabeled before release.

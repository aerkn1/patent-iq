# Mega-Cluster Dataset Scope And Boundary Governance Requirements

## Source

User-provided implementation guidance captured on March 9, 2026.

## Purpose

Define the optimal MVP dataset boundary for PatentIQ, the systemic risks introduced by that scope, and the non-negotiable guardrails required so a 10-field extraction remains mathematically sound for family, portfolio, citation, semantic, and financial analytics.

## Core Principle

The MVP dataset should be treated as a sector-bounded intelligence environment rather than a universal patent universe.

This is valid if:
1. the scope is explicitly declared,
2. denominators are bounded to the extracted cohort,
3. out-of-bounds citation nodes remain visible to citation math,
4. UI and API labels never imply universal portfolio completeness.

## Mega-Cluster Definition

## DSG-01: The MVP Should Use A 10-Field Convergent Mega-Cluster

Requirement:
PatentIQ should use a two-horizon scope policy:
1. a main operating window of `2007-2026`,
2. a separate older heritage backfill horizon when historical influence requires it,
3. both bounded to the same 10-field mega-cluster.

The main operating window should cover the following WIPO-convergent mega-cluster fields:
1. Computer Technology,
2. Digital Communication,
3. Semiconductors,
4. Electrical Machinery, Apparatus, Energy,
5. Optics,
6. Measurement,
7. Audio-Visual Technology,
8. Transport,
9. Medical Technology,
10. IT Methods for Management.

Rationale:
1. these fields create a realistic convergence zone across compute, power, sensing, and application layers,
2. they are rich enough to stress-test citation, OECD, trend, and semantic logic,
3. they are bounded enough to remain deliverable in a 5-week MVP.
4. separating the operating window from the heritage backfill avoids forcing current-state analytics and deep historical influence into one inconsistent inclusion rule.

## Why This Scope Is Valid

## DSG-02: The Mega-Cluster Should Be Treated As The Goldilocks Zone

Requirement:
The 10-field extraction should be treated as the minimum viable environment that is large enough to validate cross-field mathematics but bounded enough to remain operationally feasible.

Validation benefits:
1. OECD generality and radicalness can observe real cross-field citation diversity,
2. semantic whitespace can emerge across continuous adjacent domains rather than isolated islands,
3. localized 4D trend matrices can be stress-tested across many field-jurisdiction combinations.

## Risk And Constraint Rules

## DSG-03: Citation Edge Explosion Must Be Treated As A First-Class Scale Risk

Requirement:
Engineering should treat citation-edge scale as a graph problem rather than as a simple linear table expansion.

Implications:
1. RCF and citing-side weighting can become RAM-heavy if joins are naive,
2. citation marts should be physically optimized for family-level joins,
3. pre-aggregation and enriched citation-network tables are required for interactive use.

## DSG-04: Semantic Embedding Scope Must Be Sampled For The MVP

Requirement:
The semantic vector layer should not embed the full mega-cluster for the MVP.

Recommended MVP sampling rule:
1. filter to families with active `B1` or `B2`-level grant presence,
2. take a bounded random or stratified sample such as 5% to 10%,
3. preserve sample metadata so the UI can label the semantic layer as sampled.

Rationale:
1. full-cluster embedding cost is not compatible with a 5-week MVP,
2. a smaller active-grant sample is sufficient to prove semantic FTO and whitespace workflows,
3. sampling reduces compute and storage cost without breaking the deterministic stack.

## DSG-05: Physical Data Layout Must Be Optimized For DuckDB

Requirement:
Silver and Gold parquet outputs for the mega-cluster should be physically organized to maximize DuckDB scan efficiency.

Recommended layout:
1. sort heavily used marts by `docdb_family_id`,
2. co-sort snapshot marts by `snapshot_year`,
3. keep high-cardinality time-series marts partition-aware where practical,
4. rely on columnar pruning and zone maps rather than row-store indexing assumptions.

## DSG-05A: Constrained Source Extraction Must Stay Chunk-Aligned

Requirement:
When the mega-cluster is extracted from a constrained environment such as TIP, every source-specific raw export must respect the same field/year chunk boundary before it is uploaded or handed to Bronze.

Examples:
1. PATSTAT and Register rows are extracted only for the active field/year chunk,
2. EPAB queries use only the EP publication anchors inside the active chunk,
3. USPTO bulk XML files are reduced to only the publication-level documents whose identifiers belong to the active chunk rather than copying whole mixed-scope bulk files.

Rationale:
1. keeps RAM and local disk usage within the constrained runtime envelope,
2. makes chunk manifests explainable and retry-safe,
3. avoids leaking out-of-scope text-provider payloads into the bounded raw store.

## Boundary Guardrails

## DSG-06: Out-Of-Bounds Citations Must Be Preserved As Ghost Nodes

Requirement:
When an in-scope family cites or is cited by an out-of-scope family, the citation must be preserved for network and OECD math even if the full family record is not extracted.

Implementation rule:
1. create a ghost-node record for the out-of-bounds family,
2. preserve at least family id, high-level field identity where available, and citation linkage,
3. flag the record with `is_out_of_bounds = TRUE`,
4. do not fabricate full 4D enforceability or portfolio views for ghost nodes.

## DSG-07: Portfolio Metrics Must Use Sector-Bounded Denominators

Requirement:
Portfolio-level denominators must be bounded to the mega-cluster extraction rather than to a hypothetical universal portfolio.

Examples:
1. quality hit rate divides by in-scope portfolio families only,
2. crown-jewel density divides by in-scope active families only,
3. field-level threat or strength metrics must state the sector-bounded scope explicitly.

## DSG-08: UI And API Labels Must Declare Scope Explicitly

Requirement:
The platform must not label a sector-bounded portfolio metric as a universal global metric.

Required labeling examples:
1. `portfolio_size_active_within_mega_cluster`,
2. `hit_rate_within_mega_cluster`,
3. `mega_cluster_blocking_power`,
4. `out_of_bounds_citation_share`.

## DSG-09: Out-Of-Scope Client Inputs Must Be Rejected Cleanly

Requirement:
Client-provided financial or R&D inputs that map to fields outside the mega-cluster should be rejected with explicit scope-aware validation messages.

Rationale:
1. prevents divide-by-zero or misleading efficiency metrics,
2. keeps client-enriched dashboards aligned with the active analysis universe,
3. makes the system boundary explicit to enterprise users.

## Portfolio Representation Rules

## DSG-10: Conglomerates Must Be Presented As Sector-Bounded Portfolios

Requirement:
Large diversified assignees should be represented as ultimate-parent portfolios within the mega-cluster, not as implied universal global patent estates.

Rationale:
1. this is usually the strategically relevant lens for competitor analysis,
2. out-of-scope divisions would dilute threat relevance,
3. field-normalized portfolio math remains valid within the bounded cohort.

## DSG-11: Safe Zone Metrics Remain Valid Inside The Bounded Cohort

Requirement:
The following metric families remain mathematically valid inside the mega-cluster when denominators are bounded correctly:
1. family-level blocking power,
2. OECD cohort-normalized quality,
3. attacker leaderboards,
4. field-sliced collision metrics,
5. crown-jewel and hit-rate views.

## DSG-12: Scope Metadata Must Be First-Class In Data Contracts

Requirement:
Portfolio, family, and citation APIs should carry explicit scope metadata such as:
1. covered WIPO field list,
2. coverage start and end years,
3. whether the metric is in-scope only,
4. whether ghost nodes contributed to the result,
5. whether semantic layers are sampled.

## Relationship To Existing Notes

This note defines the dataset boundary rules that constrain all other field-, citation-, portfolio-, and semantic-layer notes.

### Overlaps With Existing Docs

1. `citation-semantics-and-tech-field-mapping-requirements.md`
2. `oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`
3. `portfolio-size-normalization-and-crown-jewel-ranking-requirements.md`
4. `semantic-similarity-and-vector-layer-requirements.md`
5. `predictive-signals-and-interpretable-forecasting-requirements.md`

### Net-New Additions

1. the 10-field mega-cluster definition,
2. sector-bounded portfolio semantics,
3. ghost-node handling for out-of-bounds citations,
4. semantic sampling guardrails,
5. scope-aware labeling and denominator governance.

## Delivery Priority

### P0

1. lock the 10-field scope,
2. implement ghost-node citation handling,
3. bound denominators to in-scope portfolios,
4. label all portfolio and family metrics with scope metadata.

### P1

1. semantic active-grant sampling,
2. parquet physical layout optimization,
3. scope-aware client-input validation.

### P2

1. broader field expansion strategy,
2. dynamic cluster reconfiguration,
3. universal-portfolio reconciliation layers beyond the MVP.

# PATSTAT Methodology Compliance Requirements (Benchmark Addendum)

## Purpose
Translate benchmark methodologies (PATSTAT-based platform) into enforceable requirements for PatentIQ, with explicit readiness status against current data/code.

## Methodology-to-Requirement Mapping

### PMC-01: DOCDB Family as Default Counting Unit
Requirement: All KPI defaults must count `docdb_family_id`, with publication/application counts only as secondary views.
Status: **Supported (partial in UI/API)**.

### PMC-02: CPC-First + Keyword-Supplement Search
Requirement: Scope builder must use CPC as primary, and report incremental recall from keyword matches not covered by CPC.
Status: **Partial** (CPC available; no incremental-recall audit).

### PMC-03: Applicant Harmonization + Corporate Consolidation
Requirement: Add harmonized applicant baseline (`han_name`-equivalent) and parent-group mapping rules for conglomerates/state entities.
Status: **Missing** (`han_name`/corporate tree absent).

### PMC-04: Publication Delay Correction
Requirement: All recent-year trend charts include 18-month lag warning and optional completeness-adjusted projection.
Status: **Missing** (not enforced in API contracts/UI).

### PMC-05: Grant Rate with Pendency Adjustment
Requirement: Grant-rate endpoints must include filing-year cutoff policy and pendency-aware denominator logic.
Status: **Missing** (no pendency-adjusted grant-rate metric).

### PMC-06: Multi-Assignment / Non-Exclusive Counting Rules
Requirement: Category charts must explicitly allow overlap and show “sum may exceed total” metadata.
Status: **Partial** (overlap exists; no standardized disclosure contract).

### PMC-07: Sector Trend Analysis (Time-Series)
Requirement: Track applicant sectors over time (`company`, `university`, `research`, `government/nonprofit`, `individual`, `other`).
Status: **Missing** (no sector labels in current marts).

### PMC-08: Extended Portfolio Analysis Beyond Core CPC
Requirement: Add adjacent-domain expansion mode to reveal platform/dependency IP outside primary scope.
Status: **Partial** (discovery exists, no automatic adjacency framework).

### PMC-09: Citation Impact vs Volume Separation
Requirement: Distinguish high-volume assignees from high-influence families using family-normalized citation density and impact ranking.
Status: **Partial** (citation metrics exist; family-level influence ranking incomplete).

### PMC-10: Geographic Shift Cohort Analysis
Requirement: Office/jurisdiction trends must be cohortized (e.g., 2000-2009, 2010-2015, 2016-2019, 2020-2024).
Status: **Missing** (no cohortized geographic trend endpoints).

### PMC-11: Inventor-Level Analytics with Name-Variant Controls
Requirement: Add inventor ranking/longevity metrics with “lower-bound” quality flag when identity resolution is uncertain.
Status: **Missing** (no inventor entities in current marts).

### PMC-12: Corporate Entity Decomposition
Requirement: Decompose portfolio activity by subsidiary/legal entity and trend emergence of new entities over time.
Status: **Missing** (owner-level only, no legal-entity decomposition timeline).

### PMC-13: Cohort-Normalized Patent Quality Scoring (OECD-Compatible)
Requirement: Implement optional OECD-compatible quality scoring where component indicators are normalized by `(filing_year, tech_field)` cohorts before composition.
Status: **Missing** (current APIs do not expose cohort normalization metadata/contracts).

### PMC-14: Composite Score Explainability Contract
Requirement: Composite quality scores (including OECD-style 4/6 component variants) must expose component values and aggregation method in API payloads.
Status: **Missing** (no standardized score decomposition endpoint).

### PMC-15: Office-Specific Indicator Compatibility Rules
Requirement: Enforce office-aware metric availability and comparability rules (for example, EPO `*_xy` citation variants available, USPTO not).
Status: **Missing** (no explicit compatibility matrix in contracts/UI).

### PMC-16: Tech/Market Filing-vs-Grant Trend Matrix
Requirement: Provide cohortized trend endpoints for technology x market slices with:
1. `filings_total`,
2. `grants_total`,
3. `grant_rate` (pendency-adjusted eligibility window).
Status: **Missing** (existing trend/grant metrics are not unified into a tech+market matrix contract).

## Additional Architecture Changes Required
1. New silver-layer entities:
   - `family_time` (priority/publication/grant/expiry anchors)
   - `legal_status_events`
   - `assignee_harmonized` + `corporate_tree`
   - `inventor_harmonized`
   - `applicant_sector_map`
2. New gold marts:
   - `family_trend_cohorts`
   - `grant_rate_pendency_adjusted`
   - `sector_trend_timeseries`
   - `family_citation_impact_rank`
   - `entity_decomposition_timeline`
   - `oecd_quality_indicators_family`
   - `oecd_quality_cohort_stats`
   - `tech_market_filing_grant_trends`
3. API contract upgrades:
   - `counting_unit`, `family_model`, `overlap_policy`, `data_completeness_pct`, `lag_warning`.
   - `cohort_key` (`filing_year`, `tech_field`, `office`)
   - `score_components` for any composite score.

## Immediate Delivery Sequence
1. **P0**: PMC-01, PMC-04, PMC-05, PMC-06, PMC-09, PMC-13
2. **P1**: PMC-02, PMC-03, PMC-08, PMC-10, PMC-14, PMC-16
3. **P2**: PMC-07, PMC-11, PMC-12, PMC-15

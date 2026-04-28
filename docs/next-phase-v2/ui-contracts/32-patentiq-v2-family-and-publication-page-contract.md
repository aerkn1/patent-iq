# PatentIQ V2 Family And Publication Page Contract

## Purpose

Define the detailed contract for the family-first intelligence page and the publication-evidence page so the frontend can render them from real Silver/Gold data without falling back into patent-centric dashboard behavior.

This contract also aligns to:

1. [patentiq-v2-page-ideas.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/patentiq-v2-page-ideas.md)
2. [creative-frontend-notes.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/creative-frontend-notes.md)

## Family Page Primary Question

`How strong, broad, explainable, and strategically exposed is this family right now?`

## Publication Page Primary Question

`What exact document-level evidence supports the family-level story?`

## Family Data Inputs

## Core Gold marts

1. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
2. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
3. [gold_family_blocking_power_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet)
4. [gold_family_field_contributions.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions.parquet)
5. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)
6. [gold_family_heritage_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet)
7. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)

## Supporting Silver marts

1. `silver_family_status_pt`
2. `silver_family_status_history`
3. `silver_branch_status_history_dense`
4. `silver_family_member_publications`
5. `silver_family_oecd_quality`
6. `silver_family_citation_metrics`

## Family Page Layout

1. `FamilyIdentityHeader`
2. `FamilySummaryRail`
3. `Strength And Explainability Grid`
4. `Legal And Coverage Section`
5. `Field And Market Footprint Section`
6. `Trajectory Section`
7. `Classification Footprint Section`
7. `Evidence Section`
8. `Links To Forecast And Semantic`

## Family Components

## 1. `FamilyIdentityHeader`

Use:

1. `docdb_family_id`
2. owner display
3. primary WIPO field
4. family status
5. scope badges

Must also show:

1. `main_window` vs `heritage_backfill`
2. owner plurality if `family_distinct_owner_count > 1`

## 2. `FamilySummaryRail`

Best representation:

1. compact summary cards across the top

Cards:

1. `Blocking Power`
   - `family_ui_blocking_power_score`
2. `Legal Enforceability`
   - `family_overall_legal_enforceability_score`
3. `Family Size`
   - `family_size_docdb`
4. `Active Reach`
   - `active_jurisdiction_count`
5. `Heritage`
   - `family_heritage_score`

## 3. `StrengthAndExplainabilityGrid`

Best representation:

1. a balanced grid mixing scores and components

Panels:

1. `BlockingPowerSummaryCard`
2. `BlockingPowerComponentsCard`
3. `OECDQualityCard`
4. `CitationSignalCard`

Why:

1. no score should appear without components,
2. family pages need defensibility more than eye candy.

## 4. `LegalAndCoverageSection`

Best representation:

1. jurisdiction table + history sparkline + branch-state chips

Use:

1. current family status
2. active/lapsed/opposed branch counts
3. dense branch history where needed
4. timeline summaries from family history
5. family-jurisdiction lapse-risk overlay where supported

Add:

1. `JurisdictionLapseRiskStrip`

Show:

1. `12m / 24m` switch
2. risk band chip
3. percentile
4. calibrated probability only when backend marks `probability_display_allowed = true`
5. `office_support_level` badge
6. caveat drawer entry when support is `moderate` or `limited`

## 5. `FieldAndMarketFootprintSection`

Best representation:

1. stacked bar or ranked table for field contributions
2. smaller timeseries panel for historical field weight movement

Use:

1. `wipo_industry_code`
2. `base_fraction`
3. `enforceability_contribution_score`
4. `heritage_contribution_score`
5. `active_market_weight`

## 6. `TrajectorySection`

Best representation:

1. dual-timeseries panel
2. optional `TimeSliceComparisonLauncher`

Views:

1. blocking power over time
2. field contribution evolution

This is where users should understand:

1. whether the family is strengthening,
2. whether it is broadening across fields,
3. whether legal state changes altered the trajectory.

## 6B. `ClassificationFootprintSection`

Best representation:

1. current WIPO and CPC chips,
2. chronological breadth sparkline,
3. `current vs selected year` classification comparison,
4. expandable ranked CPC main-group table.

Show:

1. primary WIPO field,
2. top CPC main groups,
3. classification breadth band,
4. concentration vs diversification state,
5. chronological belonging in WIPO/CPC structures where supported.

Required contract direction:

1. family pages should use [gold_family_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_mix_pit.parquet) for summary cards and [silver_family_classification_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense.parquet) for deeper chronology drill-down
2. this section must still caveat that the first implementation is `stable_family_classification_replay`, not dated code-mutation history

## 6A. `FamilyTimeSliceCompare`

This is not the default hero visualization of the family page.

It should appear only when the user explicitly enters compare mode from the trajectory section.

Best representation:

1. year selector with `current vs selected year`
2. optional `2-3 overlay radar` for normalized shape comparison
3. exact metric table with delta chips beneath the radar

Allowed radar axes:

1. blocking power percentile from [gold_family_blocking_power_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet)
2. legal durability or active-state share derived from [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
3. field breadth or contribution intensity from [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)
4. active market weight where year-safe
5. citation influence proxy only when computed from year-safe history inputs

Rules:

1. radar is compare-only, not always-on
2. max overlays: `3`
3. all axes must be normalized to `0..100`
4. if fewer than `4` usable axes exist for a chosen year, fall back to a delta table instead of radar
5. OECD current-only metrics must not be shown as historical radar axes unless a historical derivation is later added

## 7. `EvidenceSection`

Best representation:

1. family member table
2. publication drilldown links
3. provenance chips

Required:

1. member publication row list
2. representative text/source availability
3. evidence path into the publication page

## 8. `SemanticAndForecastLinks`

This should not be a generic CTA row.

It should show:

1. whether semantic evidence is claim-backed or abstract-backed
2. whether forecast coverage is available
3. link into comparison and forecast workspaces

## Publication Page Layout

1. `PublicationHeader`
2. `BibliographicEvidenceCard`
3. `ClaimsAbstractTabs`
4. `LegalAndRegisterTimeline`
5. `FamilyContextPanel`
6. `SourceProvenanceFooter`

## Publication Components

## 1. `PublicationHeader`

Show:

1. publication id
2. stage / kind
3. office
4. linked family id

## 2. `BibliographicEvidenceCard`

Use:

1. publication metadata
2. owner
3. title
4. dates

## 3. `ClaimsAbstractTabs`

Best representation:

1. tabbed viewers with provenance chips

Tabs:

1. abstract
2. claim 1
3. optional full text if ever supported

## 4. `LegalAndRegisterTimeline`

Use:

1. legal event rows
2. EP Register or office overlays where applicable

## 5. `FamilyContextPanel`

This keeps publication evidence anchored to the family-first product.

Show:

1. family summary chip row
2. blocking score
3. family status
4. link back to family page

## 6. `SourceProvenanceFooter`

Always show:

1. source system
2. text provenance
3. fallback or translation status

## Backend Contract

### Family overview

`GET /api/v1/families/{family_id}/overview`

Returns:

1. identity header
2. summary rail
3. explainability grid seed

### Family heavy sections

1. `GET /api/v1/families/{family_id}/legal`
2. `GET /api/v1/families/{family_id}/fields`
3. `GET /api/v1/families/{family_id}/timeseries`
4. `GET /api/v1/families/{family_id}/members`
5. `GET /api/v1/families/{family_id}/semantic-context`
6. `GET /api/v1/families/{family_id}/forecasts`

### Publication

1. `GET /api/v1/publications/{publication_id}/overview`
2. `GET /api/v1/publications/{publication_id}/text`
3. `GET /api/v1/publications/{publication_id}/legal-timeline`
4. `GET /api/v1/publications/{publication_id}/register-evidence`

## UI Rules

1. Family is the default strategic scope.
2. Publication is the evidence scope.
3. No family score without visible components and caveats.
4. No semantic panel without provenance.
5. No legal state shown without snapshot/date context.

## UI-Hub Alignment

Recommended creative treatment:

1. one restrained `family constellation` or jurisdiction-coverage centerpiece near the top,
2. scroll-synced distinction between current-state strength and historical trajectory,
3. side-panel evidence reveal patterns rather than modal overload.

Keep flat:

1. member publication tables,
2. evidence lists,
3. prosecution/legal tables,
4. forecast caveats.

Publication pages should be flatter than family pages.
They are evidence surfaces first, not cinematic narratives.

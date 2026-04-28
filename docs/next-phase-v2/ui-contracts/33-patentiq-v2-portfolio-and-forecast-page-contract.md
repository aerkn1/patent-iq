# PatentIQ V2 Portfolio And Forecast Page Contract

## Purpose

Define concrete page contracts for the portfolio intelligence workspace and the forecast workspace using the real Gold/Silver marts and the family-first forecast semantics from the V2 notes.

This contract also aligns to:

1. [patentiq-v2-page-ideas.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/patentiq-v2-page-ideas.md)
2. [creative-frontend-notes.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/creative-frontend-notes.md)
3. [61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md)

## Portfolio Primary Question

`What does this owner's in-scope mega-cluster portfolio look like right now, where is it strong or fragile, and which families drive the story?`

## Forecast Primary Question

`What is likely to happen next, over which horizon, and how reliable is that view?`

## Portfolio Data Inputs

1. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
2. [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
3. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)
4. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
5. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
6. [gold_family_heritage_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet)
7. [gold_portfolio_field_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet)
8. [silver_family_owner_bridge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet)

## Portfolio V2 Frontend Execution Snapshot (2026-04-09)

- `frontend_v2` route shell and workspace have been implemented to match this contract in:
  - `frontend_v2/app/(workspace)/portfolio/[ownerId]/page.tsx`
  - `frontend_v2/components/portfolio/portfolio-workspace.tsx`
  - `frontend_v2/lib/api/portfolio-v2.ts`
  - `frontend_v2/lib/types/portfolio-v2.ts`
- The portfolio workspace includes:
  - header with scoped identity and search navigation,
  - summary cards with coverage badge,
  - threat/table sections,
  - field and forecast cards with interval-first forecast language,
  - classification and drilldown tabs.
- The current adapter now also supports:
  - typed fallback rendering for missing backend slices,
  - coverage/support metadata pass-through,
  - endpoint payload hydration for `/threats` and `/classification`.
- Backend endpoints implemented:
  - `GET /api/v1/portfolios/{owner_id}/threats`
  - `GET /api/v1/portfolios/{owner_id}/classification`
  - `GET /api/v1/portfolios/{owner_id}/field-timeseries`
  - `GET /api/v1/portfolios/{owner_id}/market-context`
  - `GET /api/v1/portfolios/{owner_id}/forecast-contributors`
  - `GET /api/v1/portfolios/{owner_id}/compare-timeslice`
  - `GET /api/v1/portfolios/{owner_id}/pending-grants`

## 2026-04-09 Runtime Audit Snapshot (Backend-FE)

- Backend-v2 smoke routes are reachable (`/health`, `/api/v1/portfolios/{owner_id}/overview`, `/api/v1/portfolios/{owner_id}/families`, `/api/v1/portfolios/{owner_id}/fields`, `/api/v1/portfolios/{owner_id}/forecast`, `/api/v1/stats/runtime`).
- Portfolio handlers are now wired to real marts for core sections:
  - `GET /api/v1/portfolios/{owner_id}/overview` (summary cards/counts/top families)
  - `GET /api/v1/portfolios/{owner_id}/families` (phase03 contributor-ranked family rows)
  - `GET /api/v1/portfolios/{owner_id}/fields` (phase06 field segments)
  - `GET /api/v1/portfolios/{owner_id}/forecast?horizon=3y|5y` (interval and risk-band context)
- `PortfolioOverviewResponse` now carries phase coverage caveat metadata in response metadata.
- `frontend_v2` now wires threats and classification payloads from dedicated endpoints; fallback remains only for missing/empty payloads.
- Artifact availability audit from local storage:
  - `etl/data/gold/gold_portfolio_summary.parquet` (rows: 3,034,400)
  - `etl/data/gold/gold_portfolio_forecast_summary.parquet` (rows: 3,034,400)
  - `etl/data/gold/gold_portfolio_forecast_segments.parquet` (rows: 11,040,482)
  - `etl/data/gold/gold_portfolio_forecast_contributors.parquet` (rows: 17,866,740)
  - `etl/data/gold/gold_portfolio_classification_mix_pit.parquet` (rows: 158,834,197)
  - `etl/data/gold/gold_portfolio_threat_matrix.parquet` (rows: 15,269,449)
  - `etl/data/gold/gold_portfolio_field_timeseries.parquet` (rows: 5,520,241)
- Completed actions:
  - added `/api/v1/portfolios/{owner_id}/threats` and `/api/v1/portfolios/{owner_id}/classification` endpoints and corresponding frontend section mapping
  - added `/api/v1/portfolios/{owner_id}/field-timeseries`, `/market-context`, `/forecast-contributors`, `/compare-timeslice`, and `/pending-grants` section endpoints for the tabbed portfolio workspace contract
  - add coverage/assertion tests for `/api/v1/portfolios/{owner_id}/overview`, `/families`, `/fields`, `/forecast`, `/threats`, `/classification`
  - added service-contract coverage for portfolio mappings used by `/threats` and `/classification`

## Portfolio Layout

The portfolio page should not remain a long dashboard stack. It should be a workspace with stable top-level tabs and field-driven secondary navigation.

## 2026-04-09 Audit Correction

Current-state audit from [61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md) requires a semantic separation:

1. `Field Clusters` is a current exposure and current market-overlay tab,
2. `Classification` is the historical WIPO/CPC chronology tab,
3. `Compare` is the normalized historical portfolio-shape tab,
4. `Citations` is now a first-class top-level tab backed by citation summary, chronology, and attacker endpoints.

Important current caveat:

1. [gold_portfolio_field_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet) is currently a single-snapshot mart, not a true multi-snapshot chronology mart,
2. [gold_portfolio_forecast_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet) is also current-overlay only,
3. therefore `market context` should be interpreted as `current market overlay`, not historical PIT.

### Top-level tabs

1. `Executive`
2. `Families`
3. `Citations`
4. `Field Clusters`
5. `Threats`
6. `Forecast`
7. `Classification`
8. `Compare`

### Field cluster navigation

Within `Field Clusters`, the UI should expose:

1. `All` cluster view
2. dynamic chips for the portfolio's top in-scope WIPO fields
3. optional CPC drill-down beneath the selected WIPO field

Rules:

1. top-level tabs stay stable across all owners
2. field cluster tabs are data-driven from the owner's real exposure profile
3. deep links should support both `tab` and selected `field`
4. the UI must not hardcode synthetic owner or field examples

## Portfolio Components

## 1. `PortfolioHeader`

Show:

1. owner identity
2. scope badge
3. family count
4. active grant family count
5. semantic candidate count

## 2. `PortfolioSummaryCards`

Use direct fields from `gold_portfolio_summary`:

1. `portfolio_family_count_within_mega_cluster`
2. `portfolio_avg_blocking_power_within_mega_cluster`
3. `portfolio_total_mass_score`
4. `portfolio_hit_rate_top_decile`
5. `portfolio_crown_jewel_index`
6. `portfolio_current_threat_score`
7. `portfolio_heritage_score`

Best representation:

1. a balanced top ribbon of six to eight cards with short interpretation text

## 3. `TopFamiliesPanel`

Best representation:

1. table with pinned top rows and optional sparkline cells

Columns:

1. family id
2. owner weight
3. blocking score
4. status
5. heritage
6. primary field
7. forecast contributor value when available

## 4. `ConcentrationAndReliabilityPanel`

Purpose:

1. prevent misleading “big total” interpretation,
2. make fragility visible.

Use:

1. top contributor dependence
2. effective family counts
3. unsupported share
4. caveat flags
5. model coverage status

Best representation:

1. left card for concentration
2. right card for reliability and caveats

## 5. `FieldAndMomentumPanel`

Best representation:

1. field exposure treemap or ranked bar chart
2. current field overlay beneath it
3. `CompareThisPortfolioOverTime` action in the panel header

This panel should answer:

1. where the portfolio is concentrated,
2. which current fields are heated or cooled by the present market overlay,
3. whether the portfolio is broadly positioned or narrowly exposed.

Add:

1. current CPC main-group evidence within the selected field,
2. top gaining / declining CPC groups,
3. current vs selected-year classification mix when the classification PIT lane is available.

### `FieldClustersTab`

This becomes the primary home for:

1. `FieldAndMomentumPanel`
2. `PortfolioClassificationExposurePanel`
3. current field overlay evidence
4. selected field cluster evidence

The `Executive` tab should show only a preview of field concentration, while full exploration lives here.

## 5A. `PortfolioTimeSliceCompare`

This is a compare utility, not a default portfolio hero component.

Best representation:

1. `current vs selected year` or `year A vs year B` switcher
2. radar for portfolio shape change
3. normalized delta table beneath it

Allowed radar axes:

1. current or historical blocking strength aggregated from [gold_family_blocking_power_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet)
2. active legal durability from [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
3. field breadth and concentration from [gold_portfolio_compare_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_compare_pit.parquet)
4. threat intensity where year-safe
5. projected future influence, but only for `current vs projected` comparison and not for historical years

Rules:

1. radar appears only in compare state
2. max overlays: `3`
3. all axes normalized to `0..100`
4. exact values and deltas must appear next to the radar
5. if owner composition is not historically modeled for a selected year, the UI must caveat that the view is a portfolio membership replay from current owner bridge and historical family state

## 5B. `PortfolioClassificationExposurePanel`

Best representation:

1. stacked share chart for WIPO/CPC mix,
2. CPC gain/loss table,
3. concentration / diversification trend strip.

This panel should consume:

1. [gold_portfolio_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_classification_mix_pit.parquet)
2. [silver_family_classification_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense.parquet) for deeper drill-down or family-first fallback
3. the classification PIT execution lane defined in [56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md)

Rules:

1. historical CPC/WIPO portfolio mix must always carry the ownership-history caveat until true owner history exists
2. UI must not imply true historical owner possession when it is still a current-owner replay

## 5C. `PortfolioCitationWorkspace`

This is the citation workspace for the portfolio and should now include the two missing first-class views requested by product:

1. a ranked `most cited families in portfolio` lane,
2. a family-priority-year `filings over time` strength lane.

Best representation:

1. current forward / backward / NPL citation summary cards,
2. forward citation chronology,
3. top attacker assignees over time,
4. jurisdiction and field attack slices,
5. citation hygiene and diversity strip,
6. ranked most-cited family table,
7. filing-strength chronology preview that links to the full executive filing panel.

Primary sources:

1. [silver_family_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet)
2. [silver_family_feature_snapshot_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit.parquet)
3. [silver_enriched_citation_network.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet)
4. [gold_family_citation_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_summary.parquet)
5. [gold_portfolio_citation_family_leaderboard.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_family_leaderboard.parquet)
6. [gold_portfolio_filing_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_filing_timeseries.parquet)
4. optionally the legacy transition marts:
   - [portfolio_citation_metrics.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/data_cache/portfolio_citation_metrics.parquet)
   - [portfolio_citation_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/data_cache/portfolio_citation_timeseries.parquet)

### `PortfolioMostCitedFamiliesPanel`

Purpose:

1. answer `which families in this portfolio receive the most external citation pull`,
2. keep the ranking family-first rather than publication-first,
3. expose the family navigation path from portfolio to family workspace.

Rules:

1. ranking must be family-collapsed across member publications,
2. default sort should be `forward citation clean` descending,
3. weighted or blocking-based ranking may exist as alternate sorts, but must not replace the raw citation ranking default,
4. rows must link to the family page,
5. field and status filters must be supported.

Recommended columns:

1. `family_id`
2. `family_priority_year`
3. `primary_wipo_field`
4. `family_composite_status`
5. `family_forward_citations_clean`
6. `family_fwd_cits5`
7. `pre_asof_unique_citing_family_count`
8. `citing_assignee_diversity`
9. `family_ui_blocking_power_score`

Recommended endpoint:

1. `GET /api/v1/portfolios/{owner_id}/citation-families`

### `PortfolioFilingStrengthPanel`

Purpose:

1. answer `how has this owner built position over time`,
2. show portfolio filing momentum without implying forecast truth,
3. anchor the chronology on family filing year rather than publication year.

Rules:

1. use `family_priority_year` / earliest valid family filing year,
2. one family counts once at its priority-year anchor,
3. this panel should not be described as a prediction view,
4. current-owner replay caveat must remain visible until true owner history exists.

Best representation:

1. yearly family filing counts,
2. cumulative family build curve,
3. rolling `3y` filing mass,
4. latest-window momentum label such as `accelerating`, `stable`, or `cooling`.

Recommended endpoint:

1. `GET /api/v1/portfolios/{owner_id}/filing-timeseries`

## 6. `ThreatAndExposurePanel`

Use:

1. `gold_portfolio_threat_matrix`

Best representation:

1. heat table by citing assignee x field
2. top external pressure list

Key fields:

1. `citing_assignee_name`
2. `wipo_field`
3. `citation_lethality_sum`
4. `collided_family_count`

## 7. `ForecastPanel`

This panel should be family-bottom-up and horizon-explicit.

Show:

1. `3y` and `5y` horizon switcher
2. expected future citations total
3. expected future citations per effective family
4. interval / confidence
5. contributor list
6. caveat metadata
7. explicit coverage fields for the contributing model scope

This must never be framed as:

1. one opaque direct portfolio model

Important audit rule:

1. forecast-derived `market context` is current-overlay evidence, not historical chronology.

Add alongside the citation forecast:

1. `CoverageAttritionRiskPanel`
2. `PendingGrantPipelinePanel`

Show:

1. `12m / 24m` lapse-risk switch
2. high-risk branch count
3. high-risk share

## Visual Inheritance Decision

The portfolio V2 page should inherit the strongest stable visual primitives from `frontend_v1` rather than maintaining a separate theme language.

Use:

1. `Geist` for UI labels and controls
2. `Geist Mono` for ids and numeric evidence where useful
3. `Lora` for headline / metric serif emphasis
4. V1 light palette direction:
   - white / off-white surfaces
   - dark gray text
   - red primary / accent
   - light gray borders and muted rails

Do not:

1. revert to V1 component density wholesale
2. import V1 metric semantics into V2
3. force V2 into a Tailwind rewrite just to match V1 tokens

This is a visual inheritance decision, not a product-contract rollback.
4. top risky jurisdictions
5. top risky families
6. support coverage summary by office
7. caveat metadata when `limited` support share is material
8. explicit coverage fields for the underlying scored family subset

Rules:

1. risk band distribution is primary
2. exact branch probabilities are secondary
3. probability-heavy visuals should be suppressed when support is `limited`

### `PendingGrantPipelinePanel`

This panel is still `candidate_only`, but it is now model-backed in the portfolio workspace instead of warning-only.

Current backend behavior:

1. prefer a global pending-grant prediction mart when it exists
2. otherwise allow an owner-scoped pending-branch scoring fallback cache
3. keep the UI contract `rank/percentile-first` even when the fallback is used

If shown internally or behind a feature gate, show:

1. office-relative rank
2. percentile
3. priority tier
4. support level
5. top pending contributors

Do not headline:

1. exact expected likely-grant counts
2. raw `12m` / `24m` probabilities
3. executive-style portfolio conversion totals

Rules:

1. rank / percentile is primary
2. priority tier is secondary
3. raw probability is optional detail only
4. if the backend does not mark the branch as sealed, the panel must render candidate caveat copy

## 8. `DrilldownTables`

Tabbed:

1. families
2. threats
3. forecasts
4. field slices

## Forecast Workspace Layout

The dedicated `Forecasts` workspace should be a cross-entity intelligence page, not just a card wrapper.

Order:

1. `ForecastScopeSwitcher`
2. `ForecastHeader`
3. `HorizonSelector`
4. `PredictionAndIntervalCards`
5. `DriverAndCaveatPanel`
6. `ContributorBreakdown`
7. `ConfidenceAndCompletenessPanel`
8. `ModelInfoFooter`
9. `LegalAttritionRiskPanel`

## Forecast Components

## 1. `ForecastScopeSwitcher`

Switches:

1. family
2. portfolio

## 2. `HorizonSelector`

Tabs:

1. `3y`
2. `5y`

Why:

1. notes explicitly require both,
2. the UI should not collapse them into one blended narrative.

## 3. `PredictionAndIntervalCards`

Show:

1. expected future citations as a secondary numeric
2. lower bound
3. upper bound
4. percentile or normalized relative strength as a primary interpretation aid

Rules:

1. the interval should be visually primary
2. the exact count should never appear alone without the interval
3. copy should frame the output as directional outlook, not literal exact-count promise

## 4. `DriverAndCaveatPanel`

Show:

1. top positive drivers
2. top negative drivers
3. feature completeness
4. cohort/coverage caveats

## 5. `ContributorBreakdown`

For portfolio scope:

1. ranked family contributors
2. dependence percentage
3. concentration warning if above threshold

For family scope:

1. show factor contributions instead of family rows

## 6. `ConfidenceAndCompletenessPanel`

Show:

1. completeness percentage
2. confidence band
3. support-level summary
4. limited-support warning when office calibration evidence is weak
5. prediction coverage status
6. phase-specific coverage percentages and denominators

Required portfolio prediction coverage fields:

1. `phase03_family_coverage_pct`
2. `phase03_family_covered_count`
3. `phase03_family_denominator_count`
4. `phase04_family_coverage_pct`
5. `phase04_family_covered_count`
6. `phase04_family_denominator_count`
7. `phase04_avg_scored_jurisdictions_per_covered_family`
8. `phase06_current_field_mix_supported`
9. `coverage_caveat_text`

Rules:

1. headline portfolio prediction cards must not appear without coverage context
2. low-coverage aggregates must be visually downgraded
3. side-by-side portfolio comparison must show coverage next to each aggregate

## 7. `LegalAttritionRiskPanel`

This panel consumes the Phase 04 lapse-risk model.

Show:

1. risk band
2. percentile
3. calibrated probability only when backend marks `probability_display_allowed = true`
4. `office_support_level`
5. support reason
6. legal-status context beside the risk output

Rendering rules:

1. `strong` support:
   - probability may be shown normally
2. `moderate` support:
   - risk band remains primary
   - probability appears with a caveat badge
3. `limited` support:
   - hide or strongly downgrade exact probability
   - show band and percentile only
3. sparse cohort flags
4. if suppressed, explicit suppression reason

## 8. `PendingGrantPipelinePanel`

This panel now consumes the pending-grant candidate model when the backend serves either:

1. a global prediction mart, or
2. an owner-scoped pending-grant cache built from the sealed candidate artifacts.

Show:

1. pending pipeline percentile
2. pending pipeline rank within office or current owner-office slice
3. priority tier
4. support level
5. top pending branch shortlist
6. top jurisdiction split
7. top field split

Rendering rules:

1. raw probability must not be the headline value
2. percentile/rank remains primary while the model is candidate-only
3. exact expected likely-grant counts stay subordinate and caveated until the lower-level model is sealed
4. explicit candidate-status caveat must be visible

## Backend Contract

### Portfolio

1. `GET /api/v1/portfolios/{owner_id}/overview`
2. `GET /api/v1/portfolios/{owner_id}/families`
3. `GET /api/v1/portfolios/{owner_id}/fields`
4. `GET /api/v1/portfolios/{owner_id}/threats`
5. `GET /api/v1/portfolios/{owner_id}/classification`
6. `GET /api/v1/portfolios/{owner_id}/forecast`

### Forecast workspace

1. `GET /api/v1/forecasts/families/{family_id}`
2. `GET /api/v1/forecasts/portfolios/{owner_id}`
3. `GET /api/v1/forecasts/models`

### Required portfolio forecast metadata

Any portfolio-derived forecast response must include:

1. `aggregation_scope = family_bottom_up`
2. `phase03_family_coverage_pct`
3. `phase03_family_covered_count`
4. `phase03_family_denominator_count`
5. `phase04_family_coverage_pct`
6. `phase04_family_covered_count`
7. `phase04_family_denominator_count`
8. `phase04_avg_scored_jurisdictions_per_covered_family`
9. `phase06_current_field_mix_supported`
10. `portfolio_prediction_coverage_status`
11. `coverage_caveat_text`

If pending-grant candidate outputs are enabled, also include:

1. `pending_grant_candidate_enabled`
2. `pending_grant_model_status`
3. `pending_pipeline_rank_within_peer_set` or explicit owner-slice fallback wording
4. `pending_pipeline_percentile`
5. `pending_pipeline_priority_tier`
6. `pending_pipeline_support_level`
7. `pending_pipeline_caveat_text`
8. `pending_pipeline_top_jurisdiction`
9. `pending_pipeline_top_field`
10. `pending_pipeline_branch_count`
11. `pending_pipeline_family_count`

Current implemented ETL sources for this response shape are:

1. [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
2. [gold_portfolio_forecast_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet)
3. [gold_portfolio_forecast_contributors.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_contributors.parquet)

Backend must treat these marts as the canonical MVP portfolio-derived prediction layer rather than recomputing portfolio rollups ad hoc from lower-level model files.

Current serving interpretation:

1. Phase 03 outputs are `interval-first`
2. Phase 04 outputs are `risk-band-first`
3. Phase 06 outputs are `direction-band-first`
4. pending-grant outputs, if enabled, are `rank/percentile-first`
5. the portfolio layer aggregates those lower-level semantics; it does not upgrade them into exact-count certainty

## UI Rules

1. Every forecast must declare `prediction_unit`.
2. Portfolio forecast must be labeled `family_bottom_up`.
3. No interval may be shown without completeness/caveat context.
4. High contributor concentration must create a visible fragility banner.
5. No portfolio aggregate may be shown without model coverage context.

## UI-Hub Alignment

Portfolio page:

1. may use one authored visual centerpiece for contributor concentration or portfolio shape,
2. should otherwise stay bento-like and flat,
3. should use strong side panels for threats, caveats, and evidence.

Forecast page:

1. may use a restrained trajectory or interval reveal,
2. must keep confidence, calibration, and caveat panels flat,
3. must visually separate present-known facts from future-expected outputs.

Avoid:

1. using motion in dense tables,
2. making forecast outputs feel like certain facts,
3. decorative 3D in reliability-heavy sections.

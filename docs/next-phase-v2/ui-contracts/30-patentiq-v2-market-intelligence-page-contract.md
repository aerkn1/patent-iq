# PatentIQ V2 Market Intelligence Page Contract

## Purpose

Define the concrete page contract for the `Market Intelligence` workspace so it becomes a real product surface rather than a generic placeholder.

This note turns the baseline in:

1. [04-product-and-ui-workstreams.md](../04-product-and-ui-workstreams.md)
2. [23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md](../23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md)
3. [17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md](../17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md)
4. [patentiq-v2-page-ideas.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/patentiq-v2-page-ideas.md)
5. [creative-frontend-notes.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/creative-frontend-notes.md)

into an implementation-ready page layout that uses the actual Gold marts currently available.

## Primary Question

`What is happening in the bounded mega-cluster landscape itself right now, and where are the rising, cooling, concentrated, crowded, or open segments?`

## Product Role

This page is not:

1. a portfolio page in disguise,
2. a semantic-only explorer,
3. a raw chart dump.

It is:

1. the point-in-time landscape view,
2. the macro context that portfolio and family pages can link into,
3. the evidence-backed explanation layer for segment state labels such as `rising`, `cooling`, and `stable`.
4. the future home for CPC-within-WIPO trend and importance exploration.

## Scope Rules

All visuals and labels must remain explicitly bounded to:

1. the in-scope mega-cluster family universe,
2. the approved operating horizon,
3. the currently active release.

Required scope metadata on the page:

1. `scope_type = mega_cluster_bounded`
2. covered field count
3. coverage year range
4. snapshot date

## Actual Data Inputs

## Core Gold marts

1. [gold_market_intelligence_overview.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_overview.parquet)
   - `segment_count`
   - `rising_segment_count`
   - `cooling_segment_count`
   - `total_family_count`
   - `avg_segment_family_count`
2. [gold_market_intelligence_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_segments.parquet)
   - `segment_id`
   - `wipo_industry_code`
   - `market_state`
   - `total_family_count`
   - `latest_year`
3. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)
   - `family_priority_year`
   - `wipo_industry_code`
   - `family_count`
   - `prior_family_count`
   - `market_state`

## Supporting enrichment marts

1. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)
   - active field weight and stage context
2. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
   - `family_ui_blocking_power_score`
3. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
   - owner presence overlays and concentration context
4. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)
   - citing-assignee and field threat structure

## Supporting Silver marts where needed

1. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
2. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)

## Phase 06 Trend Overlay

The current Market Intelligence forecast overlay must use the sealed `Phase 06` contract, not the earlier raw-count framing.

Approved prediction artifacts:

1. [ml_prediction_jurisdiction_field_trend_forecast.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_jurisdiction_field_trend_forecast.parquet)
2. [model_card_jurisdiction_field_trend_forecast.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_jurisdiction_field_trend_forecast.json)
3. [51-patentiq-v2-phase-06-seal-decision-and-serving-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/51-patentiq-v2-phase-06-seal-decision-and-serving-contract.md)

Required serving emphasis:

1. `predicted_direction_band`
2. `support_level`
3. optional `trend_strength_band` as secondary

Disallowed primary emphasis:

1. exact future raw filing count as the headline signal
2. hotspot certainty language without support caveats

## Page Layout

Use a desktop-first two-axis layout:

1. a fixed summary band at the top,
2. a left-side segment selection rail,
3. a central landscape workspace,
4. a right-side detail drawer on demand.

On mobile:

1. convert the left rail into a sticky filter sheet,
2. collapse the detail drawer into a bottom sheet,
3. keep the state cards and primary league table above the first fold.

## Section Order

1. `Market Intelligence Header`
2. `Landscape State Ribbon`
3. `Segment League Table`
4. `Segment State Map`
5. `Momentum And Breadth Panel`
6. `Blocking And Saturation Panel`
7. `Top Owner Presence Panel`
8. `Selected Segment Drawer`
9. `Methodology And Caveats Footer`
10. `CPC Within Field Trend Panel`
11. `CPC Importance Leaderboard`

## Component Contract

## 1. `MarketIntelligenceHeader`

Purpose:

1. orient the user,
2. expose scope,
3. expose filters,
4. show release freshness.

Display:

1. page title
2. snapshot date
3. scope badge
4. year-range badge
5. field filter
6. market-state filter
7. optional owner overlay selector

## 2. `LandscapeStateRibbon`

Best representation:

1. five compact cards with strong labels and a secondary explanation line

Cards:

1. `Segments In Scope`
   - from `segment_count`
2. `Rising Segments`
   - from `rising_segment_count`
3. `Cooling Segments`
   - from `cooling_segment_count`
4. `Families In Scope`
   - from `total_family_count`
5. `Average Segment Size`
   - from `avg_segment_family_count`

Why cards are right here:

1. these are orientation metrics,
2. they are not trend narratives yet,
3. the user needs immediate landscape shape before drilling into segments.

## 3. `SegmentLeagueTable`

Best representation:

1. sortable table with visual state chips and mini trend sparks

Primary columns:

1. `Segment`
   - `wipo_industry_code`
2. `State`
   - `market_state`
3. `Families`
   - `total_family_count`
4. `Latest Year`
   - `latest_year`
5. `Momentum Spark`
   - derived from timeseries
6. `Blocking Density`
   - derived from field-weighted family blocking overlays
7. `Crowding Flag`
   - derived composite badge

Interaction:

1. click row opens the `Selected Segment Drawer`
2. multi-sort by state then size is allowed

Why table, not only cards:

1. users need cross-segment ranking,
2. market intelligence is comparative by nature,
3. tables make caveat badges and sortable evidence explicit.

## 4. `SegmentStateMap`

Best representation:

1. a treemap or packed-rect view where area = segment size and color = `market_state`

Inputs:

1. `wipo_industry_code`
2. `total_family_count`
3. `market_state`

Why this is useful:

1. immediately shows relative segment mass,
2. quickly reveals whether the rising segments are tiny or structurally important,
3. avoids making the user parse a large table first.

## 5. `MomentumAndBreadthPanel`

Best representation:

1. line chart plus state-transition annotations

Inputs:

1. `family_priority_year`
2. `wipo_industry_code`
3. `family_count`
4. `prior_family_count`
5. `market_state`

Views:

1. selected-segment timeseries
2. compare-to-mega-cluster median
3. year-over-year delta band

Why:

1. market-state labels need visible evidence,
2. line charts are the clearest way to defend `rising/cooling/stable`.

## 5A. `CPCWithinFieldTrendPanel`

Best representation:

1. selected WIPO field with nested CPC main-group trend lines,
2. filing and publication toggles,
3. jurisdiction filter,
4. CPC share-within-field ranking.

Purpose:

1. let users inspect which CPC main groups are driving a WIPO field,
2. show whether the field is broad-based or dominated by a few CPC clusters,
3. support deeper market-intelligence exploration than only the top-level 10 WIPO fields.

This panel should consume:

1. [gold_market_cpc_trend_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_cpc_trend_pit.parquet)
2. current family-year classification backbone from [silver_family_classification_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense.parquet)
3. the classification PIT execution lane in [56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md)

Current contract caveat:

1. first release is `primary_wipo_field_asof x cpc_main_group x year`
2. it is not yet a jurisdiction-sliced CPC trend mart
3. segment heat-state is inherited from market summary where available and otherwise derived from classification-basis segment growth

## 5B. `CPCImportanceLeaderboard`

Best representation:

1. sortable ranked table by CPC main group,
2. importance score chip,
3. growth, blocking, and share components.

Purpose:

1. surface the most strategically important CPC groups inside a selected WIPO field,
2. support compare and report use cases with explainable ranking inputs.

This panel should consume:

1. [gold_cpc_importance_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_cpc_importance_pit.parquet)
2. [gold_market_cpc_trend_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_cpc_trend_pit.parquet) for drilldown

Current contract caveat:

1. importance is a normalized CPC-year ranking signal
2. it is not an absolute universal technology value score

## 6. `BlockingAndSaturationPanel`

Best representation:

1. two-part panel:
   - left: blocking density bar or percentile strip
   - right: saturation/crowding narrative card

Inputs:

1. field-linked family counts
2. family blocking power aggregates
3. optionally threat-matrix support

Derived outputs:

1. average segment blocking score
2. top-decile blocking family share
3. crowding badge
4. whitespace candidate badge

Why:

1. market attractiveness is not only momentum,
2. users need to see whether a rising segment is already heavily defended.

## 7. `TopOwnerPresencePanel`

Best representation:

1. compact ranked table plus concentration badge

Inputs:

1. owner-linked families in the selected segment
2. owner family counts
3. optional threat or citation share overlays

Columns:

1. owner
2. in-segment family count
3. share of segment
4. average blocking score
5. concentration role badge such as `dominant`, `contender`, `fragmented`

Why:

1. users want to know who is present, not just whether a segment is rising.
2. historical owner counts are replay-based proxies unless true ownership history is modeled.

## 8. `SelectedSegmentDrawer`

Best representation:

1. right-side drawer with evidence-first detail

Subsections:

1. segment summary
2. state rationale
3. timeseries
4. owner presence
5. jurisdiction footprint
6. linked portfolios/families
7. methodology and caveat note

## 9. `MethodologyAndCaveatsFooter`

Always visible, short form.

Must include:

1. scope label
2. release id
3. state-label methodology link
4. caveat if any slice is sparse or partially supported

## Backend Contract

## Overview endpoint

`GET /api/v1/market-intelligence/overview`

Returns:

1. header metadata
2. state ribbon metrics
3. default first-page segment league rows
4. default chart seed

## Section endpoints

1. `GET /api/v1/market-intelligence/segments`
   - paginated league table
2. `GET /api/v1/market-intelligence/segments/{segment_id}`
   - detail drawer header and summary
3. `GET /api/v1/market-intelligence/segments/{segment_id}/timeseries`
   - selected segment trend data
4. `GET /api/v1/market-intelligence/segments/{segment_id}/owners`
   - owner presence table
5. `GET /api/v1/market-intelligence/segments/{segment_id}/jurisdictions`
   - jurisdiction footprint

## UI Rules

1. `market_state` must never appear without a visible rationale path.
2. Segment size and state must be visible together.
3. Any whitespace badge must consider blocking/crowding context, not trend only.
4. Portfolio overlays must be optional and clearly labeled as overlays, not intrinsic market state.

## Degraded Mode

If only the three market Gold marts are available:

1. keep header, ribbon, league table, state map, and timeseries,
2. hide owner presence and blocking-density subpanels,
3. show `reduced_context_mode` badge.

## Best Visual Language

Recommended direction:

1. use strong state chips:
   - `rising`
   - `cooling`
   - `stable`
2. use warm/cool neutral palette rather than alarm colors for everything,
3. keep evidence panels clean and table-driven,
4. avoid “AI magic” framing,
5. prefer compact strategic density over decorative dashboards.

## UI-Hub Alignment

This page is one of the best candidates for stronger creative treatment from the UI-Hub notes, but only in bounded places.

Good uses:

1. one authored macro `segment atlas` or `market map` hero,
2. a cinematic transition from landscape overview into selected-segment evidence,
3. restrained motion on state change and segment focus.

Keep flat:

1. segment league table,
2. owner-presence tables,
3. methodology and caveat panels,
4. downloadable evidence lists.

Additional workspace rules from UI-Hub:

1. use one major animated centerpiece only,
2. keep evidence cards and tables fast and flat,
3. use strong side panels for drill-down and methodology,
4. keep `Market Intelligence` separate from `Portfolio` state rather than blending them visually.

# PatentIQ V2 Point-In-Time Feature Layer Plan

## Goal

Define which PatentIQ product features need true `point-in-time` metrics rather than current-state metrics, identify what is already supported by existing history marts, and set the build order for the missing layer.

This note is broader than Phase 03.

The same point-in-time requirement affects:

1. leakage-safe ML training,
2. family and portfolio time-slice comparison,
3. market-intelligence historical views,
4. report generation,
5. some client-enriched overlays.

## Core Rule

There are two valid metric classes in PatentIQ:

1. `current-state metrics`
   - answer: `what is true now?`
   - can safely use current Gold/Silver summary marts

2. `point-in-time metrics`
   - answer: `what was true at year X or as_of_date X?`
   - must be reconstructed from history or event-backed marts
   - must not silently reuse current-state values

If the UI or model says:

1. `in 2015`,
2. `as of 2018`,
3. `current vs selected year`,
4. `historical trajectory`,
5. `forecast from as_of_date`,

then the metric must be point-in-time safe.

## What Is Already Historically Safe Enough

These marts already support real historical product behavior and should be reused rather than recomputed ad hoc:

1. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)
   - family legal-state history
   - active / lapsed / dead reconstruction

2. [silver_branch_status_history_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history_dense.parquet)
   - detailed branch-level legal replay

3. [gold_family_blocking_power_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet)
   - yearly family blocking-power history

4. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)
   - yearly field contribution history

5. [gold_portfolio_field_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet)
   - portfolio field-history structure

6. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)
   - market/segment history

These should be treated as the first historically safe building blocks for V2 historical product surfaces.

## What Is Still Current-State Only

These metrics are currently available mainly as latest/current-state values and must not be back-projected into historical compare or leakage-safe model training:

1. `family_forward_citations_clean`
2. `family_forward_citations_weighted`
3. `family_fwd_cits5`
4. `family_fwd_cits7`
5. `family_rcf_score`
6. `unique_citing_family_count`
7. `citing_assignee_diversity`
8. `attacker_density_score`
9. `family_coverage_stability_score`
10. `active_jurisdiction_count` from current summary marts
11. `active_grant_branch_count` from current summary marts
12. `family_composite_status` from current point snapshot marts
13. OECD current-quality composites such as:
    - `family_quality_index_4_score`
    - `family_quality_index_6_score`
    - `oecd_quality_percentile`
14. current owner bridge interpretation when shown for past years
15. current forecast scores if shown as if they existed historically

These are fine for `today` views.

They are not yet valid for:

1. `2015 vs 2021` family compare,
2. `portfolio in 2018`,
3. Phase 03 as-of-date training,
4. historical report narration,
5. client-enriched year-over-year overlays.

## Product Features That Need Point-In-Time Support

## 1. Family Time-Slice Compare

This is already reflected in [32-patentiq-v2-family-and-publication-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md).

Needs point-in-time-safe values for:

1. legal durability / active-state share
2. blocking power percentile
3. field contribution intensity
4. field breadth
5. citation influence proxy
6. jurisdiction breadth as of selected year
7. grant-active depth as of selected year

Already supportable now:

1. legal durability from `silver_family_status_history`
2. blocking power from `gold_family_blocking_power_timeseries`
3. field contribution from `gold_family_field_contributions_timeseries`

Still missing or incomplete:

1. pre-as-of citation influence proxy
2. pre-as-of external citing-family structure
3. pre-as-of coverage breadth snapshot

## 2. Portfolio Time-Slice Compare

Already reflected in [33-patentiq-v2-portfolio-and-forecast-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md).

Needs point-in-time-safe values for:

1. portfolio blocking strength by year
2. active legal durability by year
3. field breadth and concentration by year
4. threat intensity by year when supported
5. portfolio membership logic for historical years

Already supportable now:

1. field mix from `gold_portfolio_field_timeseries`
2. family-level history inputs from `silver_family_status_history`
3. family blocking inputs from `gold_family_blocking_power_timeseries`

Still missing or caveated:

1. historical owner-membership truth
2. fully historical portfolio concentration using year-correct membership
3. historical threat matrix replay at portfolio level

## 3. Market Intelligence Workspace

Already reflected in [30-patentiq-v2-market-intelligence-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md).

Needs point-in-time-safe values for:

1. segment heat/cooling state
2. field momentum
3. jurisdiction-field condition
4. leader tables by selected year
5. historical vs current segment composition

Already supportable now:

1. `gold_market_intelligence_timeseries`
2. `gold_family_field_contributions_timeseries`
3. `gold_portfolio_field_timeseries`

Still missing or caveated:

1. some historical leaderboards still rely on current owner mapping
2. some citation-influence slices still need year-safe citation proxies
3. CPC-within-WIPO field trend and importance views are not yet built as PIT marts

## 4. Report Generation

Already reflected in [38-patentiq-v2-report-generation-use-cases-and-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/38-patentiq-v2-report-generation-use-cases-and-contract.md).

Needs point-in-time-safe values whenever the report says:

1. `historically`,
2. `in year X`,
3. `trajectory`,
4. `how this changed over time`.

Safe now:

1. legal history sections
2. blocking-power history sections
3. field-contribution history sections
4. market timeseries sections

Unsafe until rebuilt:

1. back-projected OECD statements
2. historical citation-leadership claims using current citation summaries
3. historical portfolio-composition claims using only current owner bridge

## 5. Client-Enriched Overlays

Already reflected in [37-patentiq-v2-client-input-overlays-applicability-and-ui-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/37-patentiq-v2-client-input-overlays-applicability-and-ui-contract.md).

These need point-in-time support when they show:

1. `revenue at risk in year X`,
2. `R&D efficiency over time`,
3. `prune scenario compared against past years`,
4. `product exposure trend`.

Safe now:

1. current-state scenarios
2. current vs projected scenarios

Not fully safe yet:

1. historical year-by-year exposure overlays using current family-state metrics
2. historical ROI narratives using current legal or citation values

## 6. Phase 03 And Later ML Phases

This is where the point-in-time layer becomes mandatory, not optional.

Needs point-in-time-safe values for:

1. pre-as-of citation state
2. pre-as-of legal state
3. pre-as-of coverage state
4. pre-as-of field and trend context
5. pre-as-of network externality signals

The same pattern will later affect:

1. Phase 03 future citation forecast
2. Phase 04 lapse risk
3. Phase 05 friction risk
4. Phase 06 jurisdiction-field trend forecast

## What We Should Build

We should not try to backfill every metric at once.

We should create a dedicated point-in-time layer with three levels, plus one additional classification PIT lane:

## Level A: Family Point-In-Time Core

New artifacts:

1. `silver_family_feature_snapshot_pit.parquet`
2. optional `gold_family_feature_snapshot_pit.parquet`

Native grain:

1. `docdb_family_id`
2. `as_of_date`
3. `as_of_year`

First columns:

1. `family_composite_status_asof`
2. `active_jurisdiction_count_asof`
3. `active_grant_branch_count_asof`
4. `lapsed_jurisdiction_count_asof`
5. `family_size_docdb_asof`
6. `family_jurisdiction_count_asof`
7. `family_coverage_stability_score_asof`
8. `family_tech_breadth_wipo_count_asof`
9. `family_field_contribution_primary_asof`
10. `family_blocking_power_percentile_asof`
11. `family_rcf_score_asof`
12. `pre_asof_forward_citations_clean`
13. `pre_asof_forward_citations_weighted`
14. `pre_asof_unique_citing_family_count`
15. `pre_asof_citing_assignee_diversity`
16. `pre_asof_attacker_density_score`
17. `is_observed_as_of_snapshot`
18. `data_completeness_pct_asof`

## Level B: Portfolio Point-In-Time Summary

New artifacts:

1. `gold_portfolio_summary_pit.parquet`
2. optional `gold_portfolio_compare_snapshot_pit.parquet`

Native grain:

1. `owner_key`
2. `as_of_year`

First columns:

1. `portfolio_active_family_count_asof`
2. `portfolio_blocking_strength_asof`
3. `portfolio_field_concentration_asof`
4. `portfolio_legal_durability_asof`
5. `portfolio_current_owner_replay_flag`

## Level C: Market Point-In-Time Serving Summary

New artifacts:

1. `gold_market_segment_summary_pit.parquet`

Native grain:

1. `segment_key`
2. `as_of_year`

First columns:

1. `segment_heat_state_asof`
2. `segment_growth_index_asof`
3. `segment_owner_count_hist_proxy_asof`
4. `segment_blocking_density_asof`
5. `segment_field_balance_asof`

## Level D: Classification PIT And CPC Market Intelligence

This is the next classification-focused PIT-serving lane after the currently implemented family, portfolio, and market PIT core.

It should be handled through:

1. [56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md)

Implemented now:

1. `silver_family_classification_pit_dense`
2. `gold_family_classification_mix_pit`
3. `gold_portfolio_classification_mix_pit`

Still required:

1. `gold_market_cpc_trend_pit`
2. `gold_cpc_importance_pit`

Why this matters:

1. families should show chronological CPC/WIPO belonging in UI,
2. portfolios should show classification exposure over time,
3. market intelligence should support CPC trend and importance views inside WIPO fields.

## What Should Not Be Back-Projected

The following should remain current-only until an explicit historical derivation exists:

1. `oecd_quality_percentile`
2. `family_quality_index_4_score`
3. `family_quality_index_6_score`
4. current semantic corpus coverage flags
5. current forecast scores
6. current owner-bridge labels if no historical owner logic exists

UI and reports must keep caveating these as current-only.

## Execution Plan

## Step 1: Build Phase 03-Critical Point-In-Time Features

Priority: immediate

Goal:

1. remove the remaining current-state leakage from Phase 03
2. create reusable point-in-time family rows for forecast training

Work:

1. derive `pre_asof_forward_citations_clean`
2. derive `pre_asof_forward_citations_weighted`
3. derive `pre_asof_unique_citing_family_count`
4. derive `pre_asof_citing_assignee_diversity`
5. derive `pre_asof_attacker_density_score`
6. derive legal-state counts at `as_of_date`
7. derive coverage breadth at `as_of_date`
8. persist PIT audit checks for:
   - anchor-date correctness
   - duplicate family/year keys
   - negative/out-of-range values
   - future-anchor row count

Inputs:

1. `silver_enriched_citation_network`
2. `silver_family_status_history`
3. `silver_branch_status_history_dense`
4. `gold_family_blocking_power_timeseries`
5. `gold_family_field_contributions_timeseries`
6. `gold_family_summary`

## Step 2: Promote Family Time-Slice Product Safety

Priority: after Step 1

Goal:

1. ensure `current vs selected year` family compare uses only historically safe fields

Work:

1. build a family compare serving table from point-in-time features
2. mark current-only metrics explicitly
3. expose metric-support flags for each selected year

## Step 3: Promote Portfolio Time-Slice Product Safety

Priority: after Step 2

Goal:

1. ensure portfolio compare is not silently using current-state membership or current-only fields

Work:

1. aggregate family point-in-time rows to portfolio point-in-time summaries
2. add historical-membership caveat flags
3. keep `current vs projected` distinct from `current vs historical`

## Step 4: Promote Market Historical Safety

Priority: after Step 3

Goal:

1. standardize market/segment year-safe metrics into a serving-friendly summary mart

Work:

1. reuse `gold_market_intelligence_timeseries`
2. add summary rollups for historical leaderboards
3. ensure historical segment states are directly queryable

## Step 5: Extend Later ML Phases

Priority: after Phase 03 hardening

Use the same point-in-time layer for:

1. Phase 04 lapse risk
2. Phase 05 friction risk
3. Phase 06 trend forecast

## Release Rules

Before a metric is allowed in a historical product view, it must pass one of these:

1. it comes from an explicit history/timeseries mart, or
2. it comes from a point-in-time snapshot table keyed by `as_of_date` or `as_of_year`.

Otherwise it must be:

1. hidden,
2. clearly labeled current-only, or
3. shown only in `current vs projected` mode rather than historical mode.

## Practical Conclusion

So the answer is:

1. `yes`, this point-in-time layer is required beyond ML,
2. `yes`, some historical product surfaces are already supportable from existing history marts,
3. `no`, not every product metric needs a full new backfill,
4. `yes`, the missing work should start with family-level point-in-time features because that unlocks both Phase 03 hardening and the historical compare/report product surfaces.

## Current Implementation Status

Implemented now:

1. [silver_family_feature_snapshot_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit.parquet)
2. [silver_family_feature_snapshot_pit_audit.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_audit.json)
3. [silver_family_feature_snapshot_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense.parquet)
4. [silver_family_feature_snapshot_pit_dense_audit.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense_audit.json)
5. [gold_family_compare_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_compare_pit.parquet)
6. [gold_portfolio_summary_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary_pit.parquet)

Implemented family-level PIT fields now cover:

1. legal-state counts
2. jurisdiction breadth and coverage stability
3. publication-dated family size
4. field breadth from family field-contribution timeseries
5. blocking/enforceability as-of
6. pre-as-of citation and network externality metrics
7. PIT-safe `family_rcf_score_asof`
8. `is_observed_as_of_snapshot`

Implemented dense family-year behavior now covers:

1. one observed row per `(docdb_family_id, as_of_year)` from priority year through the current snapshot year
2. year-end `as_of_date` semantics for closed years and current snapshot-date semantics for the live partial year
3. dense historical compare behavior for the same family across years instead of one anchored checkpoint only
4. explicit `is_partial_snapshot_year` handling for the current year
5. validated multi-year family coverage across `2007..2026`

Implemented product-serving PIT layers now cover:

1. dense family historical compare and report-serving rows via `gold_family_compare_pit`
2. dense portfolio historical summary rows via `gold_portfolio_summary_pit`
3. market historical summary rows via `gold_market_summary_pit`
4. portfolio compare rows via `gold_portfolio_compare_pit`
5. market leaderboard rows via `gold_market_leaderboard_pit`
6. explicit caveat flags for:
   - current owner metadata only
   - current owner bridge replayed to history
   - unsupported historical OECD and owner truth
   - historical field mix only where year-safe source coverage exists

Observed live audit state:

1. [gold_family_compare_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_compare_pit.parquet)
   - `164,988,135` rows
   - year range `2007..2026`
   - `17,633,618` families with multi-year PIT rows
   - duplicate `(docdb_family_id, as_of_year)` keys: `0`
2. [gold_portfolio_summary_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary_pit.parquet)
   - `36,127,659` rows
   - year range `2007..2026`
   - `3,034,400` harmonized owners
   - `3,034,400` owners with multi-year PIT rows
   - duplicate `(owner_name_harmonized, as_of_year)` keys: `0`
   - `current_owner_bridge_replayed_to_history = true` on all rows by design
3. [gold_market_summary_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet)
   - `504` rows
   - year range `1956..2025`
   - `10` segments
   - duplicate `(segment_key, as_of_year)` keys: `0`
   - one row per segment-year from the current market-intelligence timeseries contract
4. [gold_portfolio_compare_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_compare_pit.parquet)
   - `36,127,659` rows
   - year range `2007..2026`
   - `3,034,400` harmonized owners
   - duplicate `(owner_name_harmonized, as_of_year)` keys: `0`
   - historical field-mix support currently exists only for `2026`
   - `current_owner_bridge_replayed_to_history = true` on all rows by design
5. [gold_market_leaderboard_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_leaderboard_pit.parquet)
   - `7,600` rows
   - year range `2007..2025`
   - `10` segments
   - row types:
     - `3,800` family leaderboard rows
     - `3,800` owner leaderboard rows
   - duplicate `(segment_key, as_of_year, leaderboard_entity_type, leaderboard_rank)` keys: `0`
   - owner rows explicitly keep `current_owner_bridge_replayed_to_history = true`
   - family rows explicitly keep `current_owner_bridge_replayed_to_history = false`

Still not yet implemented as full product-serving layers:

1. historical owner-membership truth
2. OECD historical composites
3. classification PIT and CPC-within-WIPO market-intelligence marts

## Next Product-Scope Build Order

The next PIT work should now shift away from Phase 03 hardening and toward reusable product-serving layers.

### 1. Deferred Until Better Source Truth Exists

Do not force these into the first PIT product release:

1. historical owner-membership truth
2. historical OECD composite backprojection
3. historical finance-style overlays built from current ownership assumptions

## Practical Recommendation

The immediate PIT product sequence should be:

1. `gold_family_compare_pit`
2. `gold_portfolio_summary_pit`
3. `gold_market_summary_pit`
4. `gold_portfolio_compare_pit`
5. `gold_market_leaderboard_pit`
6. ownership-history truth and historical OECD only after explicit source derivation exists
7. classification PIT and CPC market-intelligence layer through doc `56`

That order keeps the next backend and UI work aligned with:

1. family compare and report surfaces,
2. portfolio over-time comparison,
3. market intelligence historical views.
4. chronological classification exposure in family, portfolio, and market UI.

Current progress against that sequence:

1. `gold_family_compare_pit`: implemented
2. `gold_portfolio_summary_pit`: implemented
3. `gold_market_summary_pit`: implemented
4. `gold_portfolio_compare_pit`: implemented
5. `gold_market_leaderboard_pit`: implemented
6. classification PIT and CPC market-intelligence layer: planned, not yet implemented

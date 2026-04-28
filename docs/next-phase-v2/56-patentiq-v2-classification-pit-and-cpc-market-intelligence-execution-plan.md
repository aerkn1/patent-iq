# PatentIQ V2 Classification PIT And CPC Market Intelligence Execution Plan

## Goal

Define the missing `classification point-in-time` layer so PatentIQ can show:

1. chronological family membership in WIPO and CPC structures,
2. chronological portfolio exposure by WIPO and CPC structures,
3. market-intelligence trend views for CPC classes inside WIPO fields,
4. point-in-time importance of CPC main groups.

This scope exists in the V2 notes and product intent already, and its family-year foundation is now implemented, but the broader Gold serving marts are not complete yet.

## Current Status

Implemented now:

1. [silver_family_classification_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense.parquet)
   - dense `family x year` classification PIT core
   - exact row parity with [silver_family_feature_snapshot_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense.parquet)
   - `164,988,135` rows for `2007..2026`
2. [silver_family_classification_pit_dense_audit.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense_audit.json)
   - duplicate family-year keys: `0`
   - rows with WIPO membership: `164,988,135`
   - rows with CPC main-group membership: `93,283,467`
3. [gold_family_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_mix_pit.parquet)
   - family-year serving mart for classification breadth, concentration, entropy, and top CPC groups
   - `164,988,135` rows for `2007..2026`
   - duplicate family-year keys: `0`
4. [gold_portfolio_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_classification_mix_pit.parquet)
   - owner-year classification exposure mart with explicit current-owner replay caveat
   - `158,834,197` rows for `2007..2026`
   - duplicate `(owner, year, classification_type, classification_code)` keys: `0`
5. [gold_market_cpc_trend_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_cpc_trend_pit.parquet)
   - market `primary_wipo_field x cpc_main_group x year` trend mart
   - `862,969` rows for `2007..2026`
   - duplicate `(segment_key, year, cpc_main_group)` keys: `0`
6. [gold_cpc_importance_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_cpc_importance_pit.parquet)
   - CPC-year importance mart derived from the market CPC trend layer
   - `152,753` rows for `2007..2026`
   - duplicate `(year, cpc_main_group)` keys: `0`

Upgrade applied before the market marts:

1. [57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md)
2. family classification chronology now uses `first_seen_classification_visibility` instead of stable full-history replay

## Why This Matters

Current V2 product behavior already supports:

1. family PIT legal and blocking history,
2. portfolio PIT legal and field history,
3. market PIT summary at WIPO-field level.

What is still missing is the `classification lens` over that history.

Without it, the UI cannot fully show:

1. how a family broadens or concentrates across CPC/WIPO categories over time,
2. how a portfolio’s classification footprint changes over time,
3. which CPC groups inside a WIPO field are heating, cooling, or strategically important,
4. explainable CPC-centric market-intelligence pivots.

## Current Availability

## Implemented now

1. [silver_family_ipc_cpc_canonical.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_ipc_cpc_canonical.parquet)
   - family-level canonical `ipc_symbols` and `cpc_symbols`
   - rows: `21,353,101`
2. [silver_family_wipo_fields.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet)
   - family-level WIPO field mapping
3. [silver_family_feature_snapshot_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense.parquet)
   - dense family-year PIT backbone
4. [gold_portfolio_field_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet)
   - portfolio field history at WIPO level
5. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)
   - market history at WIPO level
6. [gold_portfolio_compare_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_compare_pit.parquet)
   - portfolio PIT with historical field-mix caveat handling
7. [silver_family_classification_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense.parquet)
   - implemented dense family-year classification lane with `first_seen_classification_visibility`
8. [gold_market_cpc_trend_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_cpc_trend_pit.parquet)
   - market CPC trend at `primary_wipo_field x cpc_main_group x year`
   - includes derived segment heat-state fallback when coarse market summary does not cover the field
9. [gold_cpc_importance_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_cpc_importance_pit.parquet)
   - CPC-year importance/ranking layer derived from the market trend mart

So the scope is now `packaged into serving marts`, with the remaining caveats being semantic rather than missing-artifact blockers.

## Product Scope

This layer should support three visible product behaviors.

## 1. Family Classification History

The family UI should be able to show:

1. current WIPO field membership,
2. current CPC main-group footprint,
3. chronological field/CPC breadth,
4. first-seen and dominant classification groups,
5. concentration vs diversification over time.

## 2. Portfolio Classification History

The portfolio UI should be able to show:

1. WIPO field mix over time,
2. CPC main-group exposure over time,
3. concentration and diversification trend,
4. top gaining / top declining CPC groups,
5. current vs selected-year classification comparison.

## 3. Market Intelligence Classification Trend

The market UI should be able to show:

1. CPC classes inside a chosen WIPO field,
2. filing and publication trend by CPC main group,
3. heating / cooling state by CPC main group,
4. CPC importance by year,
5. CPC group ranking inside a WIPO field and jurisdiction slice.

## Core Design Rule

There are two different things to represent:

1. `classification possession`
   - which CPC/WIPO groups a family belongs to
2. `classification exposure`
   - how much of a portfolio or market is concentrated in those groups

Possession is family-grain.

Exposure is portfolio/market aggregation built from family-grain rows.

## Historical Safety Rule

This scope needs a separate PIT policy from legal state.

Legal state changes continuously and needs explicit replay.

Classification is more stable, but historical rendering still needs a rule for `when a code becomes visible`.

First implementation should use this policy:

1. WIPO and CPC family membership is treated as first visible from member-publication chronology,
2. family-level classification mix expands over the family PIT timeline as codes become visible, but still does not claim full code-mutation history,
3. portfolio history must still carry the `current owner replay` caveat unless true ownership history is later built.

This means:

1. family-level classification chronology is `usable` and materially time-aware via first-seen visibility, but still not truly event-dated code mutation,
2. portfolio-level classification chronology is `usable with current-owner replay caveat`,
3. market-level CPC trend is more defensible because it aggregates family-year presence rather than claiming dated code mutation per publication.

## Recommended New Artifacts

## Level A: Family Classification PIT Core

### 1. `silver_family_classification_pit_dense.parquet`

Native grain:

1. `docdb_family_id`
2. `as_of_year`

Implemented columns:

1. `docdb_family_id`
2. `as_of_date`
3. `as_of_year`
4. `is_observed_as_of_snapshot`
5. `is_partial_snapshot_year`
6. `covered_wipo_fields_asof`
7. `primary_wipo_field_asof`
8. `wipo_field_count_asof`
9. `ipc_subclasses_asof`
10. `cpc_sections_asof`
11. `cpc_subclasses_asof`
12. `cpc_main_groups_asof`
13. `ipc_subclass_count_asof`
14. `cpc_section_count_asof`
15. `cpc_subclass_count_asof`
16. `cpc_main_group_count_asof`
17. `classification_visibility_policy`
18. `classification_membership_replayed_to_history`
19. `historical_classification_truth_supported`

Purpose:

1. create one reusable family-year classification lens
2. avoid every product surface re-deriving CPC/WIPO membership ad hoc
3. keep the first implementation honest via explicit first-seen visibility and caveat fields

### 2. `gold_family_classification_mix_pit.parquet`

Native grain:

1. `docdb_family_id`
2. `as_of_year`

Recommended columns:

1. `primary_wipo_field_asof`
2. `wipo_field_count_asof`
3. `cpc_main_group_count_asof`
4. `classification_concentration_hhi_asof`
5. `classification_entropy_asof`
6. `top_cpc_main_group_asof`
7. `top_cpc_main_group_share_asof`
8. `classification_breadth_band_asof`

Purpose:

1. power family UI summary cards and time-slice comparison
2. avoid exposing long raw classification arrays on every page load

Current implementation status:

1. implemented
2. backed by [gold_family_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_mix_pit.parquet)
3. first-release concentration and entropy assume equal-weight membership across CPC main groups under the stable-replay policy
3. first-release concentration and entropy assume equal-weight membership across visible CPC main groups under the first-seen visibility policy

## Level B: Portfolio Classification PIT

### 3. `gold_portfolio_classification_mix_pit.parquet`

Native grain:

1. `owner_name_harmonized`
2. `as_of_year`
3. `classification_type`
4. `classification_code`

Recommended columns:

1. `owner_name_harmonized`
2. `as_of_year`
3. `classification_type`
4. `classification_code`
5. `classification_label`
6. `portfolio_family_count_hist_proxy`
7. `portfolio_family_share_asof`
8. `portfolio_active_family_share_asof`
9. `portfolio_blocking_density_asof`
10. `portfolio_enforceability_density_asof`
11. `historical_owner_truth_supported`
12. `current_owner_bridge_replayed_to_history`

Purpose:

1. portfolio field/CPC mix over time
2. top rising / falling CPC groups
3. classification concentration and diversification history

Important caveat:

1. until ownership history exists, this mart must explicitly remain a current-owner replay for historical years

Current implementation status:

1. implemented
2. backed by [gold_portfolio_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_classification_mix_pit.parquet)
3. classification rows currently cover `WIPO_FIELD` and `CPC_MAIN_GROUP`

## Level C: Market CPC Trend Layer

### 4. `gold_market_cpc_trend_pit.parquet`

Native grain:

1. `wipo_industry_code`
2. `cpc_main_group`
3. `as_of_year`

Current implementation grain:

1. `primary_wipo_field_asof`
2. `cpc_main_group`
3. `as_of_year`

Implemented columns:

1. `segment_key`
2. `wipo_industry_code`
3. `cpc_main_group`
4. `as_of_year`
5. `cpc_family_count_asof`
6. `cpc_active_family_count_asof`
7. `segment_family_count_classification_basis_asof`
8. `segment_active_family_count_classification_basis_asof`
9. `cpc_family_share_within_segment_asof`
10. `cpc_active_family_share_within_segment_asof`
11. `cpc_prior_family_count_asof`
12. `cpc_growth_index_asof`
13. `cpc_heat_state_asof`
14. `segment_heat_state_asof`
15. `cpc_rank_within_segment_year`
16. `cpc_blocking_density_asof`
17. `cpc_enforceability_density_asof`
18. `classification_visibility_policy`

Purpose:

1. show CPC trending inside specific WIPO fields
2. support market-intelligence pivots beyond only the 10 mega WIPO fields
3. expose CPC heat-state and ranking in a historically aligned market slice

Important boundary:

1. first release uses `primary_wipo_field_asof`, not a fabricated many-to-many CPC-to-all-covered-WIPO mapping
2. coarse market summary heat-state is reused where available and otherwise derived from classification-basis segment growth

### 5. `gold_cpc_importance_pit.parquet`

Native grain:

1. `as_of_year`
2. `cpc_main_group`

Implemented columns:

1. `as_of_year`
2. `cpc_main_group`
3. `cpc_family_count_asof`
4. `cpc_segment_count_asof`
5. `cpc_family_share_global_asof`
6. `cpc_segment_presence_share_asof`
7. `cpc_blocking_density_asof`
8. `cpc_enforceability_density_asof`
9. `cpc_growth_index_asof`
10. `cpc_importance_score_asof`
11. `cpc_importance_band_asof`
12. `cpc_importance_rank_within_year`

Purpose:

1. rank CPC groups by strategic importance for the selected year
2. support leaderboard cards, compare views, and report narration
3. expose a normalized importance score instead of raw blocking/enforceability magnitudes

## Deprecated earlier target shape

The earlier planning shape below is now superseded by the implemented contract above:

1. `jurisdiction_code`
2. `wipo_industry_code`
3. `cpc_main_group`
4. `as_of_year`

## UI Shape

## Family UI

Add a `ClassificationFootprintSection` to the family page.

Show:

1. current primary WIPO field and top CPC main groups,
2. chronological breadth sparkline,
3. `current vs selected year` CPC/WIPO comparison,
4. dominant CPC groups and share,
5. concentration vs diversification chips.

Use:

1. [gold_family_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md)
2. `silver_family_classification_pit_dense` for deep drilldown

## Portfolio UI

Add a `ClassificationExposurePanel` and `ClassificationTimeSliceCompare`.

Show:

1. WIPO field share over time,
2. top CPC main groups over time,
3. concentration and diversification trend,
4. top gaining / declining CPC groups,
5. current vs selected-year classification mix.

Use:

1. `gold_portfolio_classification_mix_pit`
2. explicit `current_owner_bridge_replayed_to_history` caveat

## Market Intelligence UI

Add `CPCWithinFieldTrendPanel` and `CPCImportanceLeaderboard`.

Show:

1. CPC main-group trends inside selected WIPO field,
2. family-share and heat-state by year,
3. heating / cooling CPC groups,
4. CPC importance ranking for the selected year,
5. primary-field-level market slices beyond the coarse mega-field cards.

Use:

1. `gold_market_cpc_trend_pit`
2. `gold_cpc_importance_pit`

## Data Quality Requirements

Current implemented audits should certify:

1. CPC/WIPO family coverage,
2. code normalization quality,
3. family-to-classification duplication policy,
4. chronology rule for classification visibility,
5. portfolio replay caveat behavior,
6. market aggregation sanity by year,
7. no duplicate market CPC keys and no rank gaps in year slices.

## Build Order

Recommended order:

1. `silver_family_classification_pit_dense`
2. `gold_family_classification_mix_pit`
3. `gold_portfolio_classification_mix_pit`
4. `gold_market_cpc_trend_pit`
5. `gold_cpc_importance_pit`

## Immediate Conclusion

The scope is:

1. explicitly aligned with the V2 notes and product intent,
2. now implemented through family, portfolio, and market classification PIT marts,
3. feasible from current raw and Silver data,
4. valuable for family, portfolio, and market-intelligence UI behavior.

The remaining caution is semantic, not structural:

1. family classification chronology is first-seen visibility, not true code-mutation history,
2. portfolio chronology still carries the current-owner replay caveat,
3. market CPC trend is primary-field-based rather than jurisdiction-sliced in the current release.

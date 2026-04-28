# PatentIQ V2 Citation Serving Refactor Execution Plan

## Purpose

Turn the citation portion of the Silver/Gold boundary audit into an implementation-ready execution plan.

This note defines:

1. which citation data should remain evidence-first in `Silver`,
2. which citation features should remain analytic intermediates only,
3. which citation summaries and trend views must be formalized in `Gold` for UI serving,
4. how the family, filing/publication, portfolio, and market surfaces should consume them.

Primary reference:

1. [63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md)

Supporting references:

1. [32-patentiq-v2-family-and-publication-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md)
2. [33-patentiq-v2-portfolio-and-forecast-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md)
3. [30-patentiq-v2-market-intelligence-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md)
4. [citation-event-ledger-and-attacker-leaderboard-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/citation-event-ledger-and-attacker-leaderboard-requirements.md)
5. [field-sliced-competitor-intelligence-and-tech-trend-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/field-sliced-competitor-intelligence-and-tech-trend-requirements.md)
6. [56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md)

---

## Status Update

As of April 9, 2026, the first implementation slice of this plan is built and audited for `family` and `portfolio`.

Implemented Gold marts:

1. `gold_family_citation_summary.parquet`
2. `gold_family_citation_timeseries_pit.parquet`
3. `gold_portfolio_citation_summary.parquet`
4. `gold_portfolio_citation_timeseries.parquet`
5. `gold_portfolio_attacker_momentum.parquet`
6. `gold_portfolio_citation_pressure_by_field.parquet`
7. `gold_portfolio_citation_pressure_by_jurisdiction.parquet`
8. `gold_market_citation_trend_pit.parquet`
9. `gold_market_citation_pressure_by_jurisdiction_pit.parquet`
10. `gold_market_attacker_leaderboard_pit.parquet`

Implementation note:

1. `gold_portfolio_citation_summary` had to be rebuilt as a year-chunked rollup from the narrower family Gold citation marts.
2. The original one-shot aggregation from the wide Silver PIT exhausted DuckDB memory in runtime execution.
3. The year-chunked pattern is now the serving-safe implementation for this mart.

Backend-v2 serving note:

1. portfolio citation endpoints now prefer these explicit Gold marts when present
2. serving excludes placeholder attacker owners and self-owner attacker rows in the portfolio attacker, field, and jurisdiction views
3. market citation endpoints now exist for:
   - `GET /api/v1/market-intelligence/citation-trends`
   - `GET /api/v1/market-intelligence/citation-jurisdictions`
   - `GET /api/v1/market-intelligence/citation-attackers`

Still pending from this plan:

1. any dedicated publication-citation Gold contract
2. the adjacent `WIPO x CPC x jurisdiction x year` ranking marts documented below

---

## 1. Core Execution Decision

The citation refactor should follow this rule:

1. `Silver` remains the citation evidence and feature layer,
2. `Gold` becomes the citation serving and summary layer,
3. `Publication` remains evidence-first unless a future dedicated publication-citation scoring contract is approved,
4. no current UI card or ranking should depend directly on `family_adjusted_citation_score_raw`.

This means:

1. raw citation edges and enriched event rows stay in `Silver`,
2. family, portfolio, and market citation cards and leaderboards move to explicit `Gold` marts,
3. citation-derived blocking and heritage logic is rebuilt after the family-layer serving fix.

---

## 2. Current Inputs

## 2.1 Silver citation inputs

Existing citation-capable Silver sources already available:

1. `silver_family_citation_edges`
2. `silver_family_citation_edges_clean`
3. `silver_enriched_citation_network`
4. `silver_family_citation_metrics`
5. `silver_family_feature_snapshot_pit`

Important current columns and semantics:

1. dated event fields:
   - `citation_date`
   - `citation_year`
2. citing-side context:
   - `citing_assignee_name`
   - `citing_jurisdiction_code`
   - `citing_primary_wipo_field`
   - `citation_lethality_score`
3. family citation summaries:
   - `family_forward_citations_raw`
   - `family_forward_citations_clean`
   - `family_forward_citations_weighted`
   - `family_backward_patent_citation_count`
   - `family_backward_citations_clean`
   - `family_backward_npl_citation_count`
   - `out_of_bounds_citation_count`
   - `out_of_bounds_citation_share`
4. PIT family citation feature fields:
   - `pre_asof_forward_citations_clean`
   - `pre_asof_forward_citations_weighted`
   - `pre_asof_citing_assignee_diversity`

## 2.2 Current Gold citation consumers

Current Gold consumers of citation logic:

1. `gold_family_blocking_power`
2. `gold_family_blocking_power_timeseries`
3. `gold_family_heritage_summary`
4. `gold_family_attacker_summary`
5. `gold_portfolio_threat_matrix`
6. `gold_portfolio_forecast_summary`
7. market and CPC PIT marts that already consume PIT citation-derived features

## 2.3 Current backend serving state

Current backend-v2 portfolio citation endpoints already exist:

1. `GET /api/v1/portfolios/{owner_id}/citation-summary`
2. `GET /api/v1/portfolios/{owner_id}/citation-timeseries`
3. `GET /api/v1/portfolios/{owner_id}/citation-attackers`
4. `GET /api/v1/portfolios/{owner_id}/citation-fields`
5. `GET /api/v1/portfolios/{owner_id}/citation-jurisdictions`

These routes validate product demand, but the serving contract should be made more explicit upstream rather than leaving the portfolio layer to reconstruct citation semantics ad hoc.

---

## 3. Current Problems To Fix

## 3.1 Family citation serving problem

`family_adjusted_citation_score_raw` is currently overused.

It is serving as:

1. a Silver feature,
2. a blocking-power ingredient,
3. a heritage proxy,
4. an implicit UI influence score.

That is too much semantic load for one unstable intermediate.

## 3.2 Portfolio citation serving problem

Portfolio citation surfaces exist, but the upstream contract is still loose:

1. attacker evidence is valid,
2. chronology is valid when it comes from event dates,
3. aggregate citation mass is not yet clearly separated into:
   - raw aggregate,
   - index,
   - normalized serving metric.

## 3.3 Market citation serving problem

Market citation pressure is conceptually valuable, but it still needs:

1. explicit PIT-safe marts,
2. clear separation between current overlay and real chronology,
3. explicit index/rank semantics.

## 3.4 Publication citation serving problem

Publication citation is often tempting to score, but the current product role is evidence-first.

That means:

1. filing/publication citation should remain proof-driven,
2. not be pushed into Gold just for architectural symmetry.

## 3.5 WIPO/CPC/Jurisdiction ranking gap

There is a separate but closely related serving gap around ranking-ready classification and geography slices.

Current state:

1. `WIPO x year` and `CPC x year` are materially available,
2. `jurisdiction by year` is only partial in the current family and portfolio PIT lanes,
3. a clean sealed `WIPO x CPC x jurisdiction x year` ranking mart does not yet exist for family, portfolio, or market.

What exists now:

1. family classification PIT is strong:
   - `gold_family_classification_mix_pit`
   - `silver_family_classification_pit_dense`
2. portfolio classification PIT is strong:
   - `gold_portfolio_classification_mix_pit`
3. market CPC trend and importance PIT are strong:
   - `gold_market_cpc_trend_pit`
   - `gold_cpc_importance_pit`
4. but current market CPC trend is not yet jurisdiction-sliced in the current release.

Execution implication:

1. the citation refactor should treat this as an adjacent Gold-serving extension,
2. not as something already solved by the current classification marts.

---

## 4. Target Layer Split

## 4.1 Keep in Silver

The following remain authoritative Silver citation artifacts:

1. raw citation edges,
2. cleaned citation edges,
3. enriched citation event ledger,
4. family-level raw and cleaned citation counts,
5. out-of-bounds flags and counts,
6. backward patent and backward NPL citation facts,
7. PIT family citation feature snapshots.

## 4.2 Keep as Silver analytic intermediates only

These remain valid for ETL and modeling, but should not be served as final UI truth:

1. `family_forward_citations_weighted`
2. `family_adjusted_citation_score_raw`
3. raw citation lethality accumulations
4. fallback OECD citation blends
5. raw owner-aggregated citation mass before labeling

## 4.3 Formalize in Gold

These should become explicit serving marts or formally documented Gold slices:

1. family citation summary
2. family citation chronology PIT
3. family attacker summary
4. portfolio citation summary
5. portfolio citation chronology
6. portfolio attacker momentum
7. portfolio citation pressure by field
8. portfolio citation pressure by jurisdiction
9. market citation trend PIT
10. market citation pressure leaderboard

---

## 5. Proposed Gold Citation Marts

## 5.1 Family

### `gold_family_citation_summary.parquet`

Purpose:

1. compact family citation cards and explainability panels

Recommended columns:

1. `docdb_family_id`
2. `family_forward_citations_raw`
3. `family_forward_citations_clean`
4. `family_forward_citations_weighted_raw`
5. `family_backward_patent_citation_count`
6. `family_backward_citations_clean`
7. `family_backward_npl_citation_count`
8. `out_of_bounds_citation_share`
9. `citing_assignee_diversity`
10. `citation_support_level`
11. `citation_influence_index`
12. `heritage_mass_index`
13. `method_version`

Rules:

1. keep raw counts visible,
2. if `citation_influence_index` is produced, it must be bounded and documented,
3. `family_adjusted_citation_score_raw` must not be surfaced directly in UI.

### `gold_family_citation_timeseries_pit.parquet`

Purpose:

1. family citation chronology,
2. compare mode,
3. year-safe trajectory charts

Recommended columns:

1. `docdb_family_id`
2. `as_of_year`
3. `pre_asof_forward_citations_clean`
4. `pre_asof_forward_citations_weighted`
5. `pre_asof_citing_assignee_diversity`
6. `pre_asof_unique_citing_family_count`
7. `citation_influence_index_asof`
8. `citation_data_completeness_pct_asof`
9. `historical_citation_safe`
10. `method_version`

### Keep and realign

Existing marts to retain but re-scope:

1. `gold_family_heritage_summary`
2. `gold_family_attacker_summary`

Required change:

1. both should read from formalized Gold citation semantics rather than directly inheriting unstable Silver intermediates.

## 5.2 Publication or filing

No mandatory new Gold mart in this refactor.

Execution decision:

1. publication citation remains Silver evidence-first,
2. only add a Gold publication citation mart if a later product requirement explicitly needs document-level summary scoring.

## 5.3 Portfolio

### `gold_portfolio_citation_summary.parquet`

Purpose:

1. drive the portfolio `Citations` executive summary lane

Recommended columns:

1. `owner_name_harmonized`
2. `snapshot_date`
3. `portfolio_forward_citations_raw`
4. `portfolio_forward_citations_clean`
5. `portfolio_forward_citations_weighted_raw`
6. `portfolio_backward_patent_citation_count`
7. `portfolio_backward_npl_citation_count`
8. `portfolio_citing_assignee_diversity`
9. `portfolio_citation_heritage_mass`
10. `portfolio_citation_pressure_index`
11. `citation_support_level`
12. `method_version`

Rules:

1. show raw counts and indices separately,
2. avoid naming any additive sum a normalized score.

### `gold_portfolio_citation_timeseries.parquet`

Purpose:

1. owner-level citation chronology in the `Citations` tab

Recommended columns:

1. `owner_name_harmonized`
2. `year`
3. `forward_citations_clean`
4. `forward_citations_weighted_raw`
5. `backward_patent_citation_count`
6. `backward_npl_citation_count`
7. `citing_assignee_diversity`
8. `citation_pressure_index`
9. `historical_citation_safe`
10. `method_version`

### `gold_portfolio_citation_pressure_by_field.parquet`

Purpose:

1. field-sliced citation pressure and top-collision panels

Recommended columns:

1. `owner_name_harmonized`
2. `wipo_field`
3. `year` or `snapshot_date`
4. `citation_count`
5. `citation_lethality_sum_raw`
6. `citation_pressure_index`
7. `top_attacker_count`
8. `method_version`

### `gold_portfolio_citation_pressure_by_jurisdiction.parquet`

Purpose:

1. jurisdiction-sliced pressure and attacker views

Recommended columns:

1. `owner_name_harmonized`
2. `jurisdiction_code`
3. `year` or `snapshot_date`
4. `citation_count`
5. `citation_lethality_sum_raw`
6. `citation_pressure_index`
7. `method_version`

### `gold_portfolio_attacker_momentum.parquet`

Purpose:

1. attacker leaderboard,
2. field/jurisdiction filters,
3. time-window delta views

Recommended columns:

1. `owner_name_harmonized`
2. `citing_assignee_name`
3. `wipo_field`
4. `jurisdiction_code`
5. `year`
6. `citation_count`
7. `citation_lethality_sum_raw`
8. `attacker_pressure_index`
9. `momentum_direction`
10. `method_version`

### `gold_portfolio_citation_family_leaderboard.parquet`

Purpose:

1. ranked `most cited families` view inside the portfolio citation workspace,
2. family-first navigation from owner portfolio into cited families,
3. clean separation between raw citation rank and secondary blocking/context overlays.

Recommended columns:

1. `owner_name_harmonized`
2. `docdb_family_id`
3. `family_priority_year`
4. `primary_wipo_field`
5. `family_composite_status`
6. `family_forward_citations_clean`
7. `family_forward_citations_weighted_raw`
8. `family_fwd_cits5`
9. `family_fwd_cits7`
10. `unique_citing_family_count`
11. `citing_assignee_diversity`
12. `family_ui_blocking_power_score`
13. `method_version`

Rules:

1. default rank must be `family_forward_citations_clean desc`,
2. weighted or blocking views may exist as alternate sorts only,
3. this mart should be family-collapsed across member-publication citation evidence,
4. this mart must not expose `family_adjusted_citation_score_raw`.

## 5.4 Market

### `gold_market_citation_trend_pit.parquet`

Purpose:

1. field-level citation chronology and crowdedness views

Recommended columns:

1. `as_of_year`
2. `wipo_field`
3. `citation_count`
4. `citation_lethality_sum_raw`
5. `citation_pressure_index`
6. `distinct_citing_assignee_count`
7. `distinct_citing_jurisdiction_count`
8. `market_citation_state`
9. `method_version`

### `gold_market_citation_pressure_by_jurisdiction_pit.parquet`

Purpose:

1. explain where field pressure is geographically concentrated

Recommended columns:

1. `as_of_year`
2. `wipo_field`
3. `jurisdiction_code`
4. `citation_count`
5. `citation_lethality_sum_raw`
6. `citation_pressure_index`
7. `method_version`

### `gold_market_attacker_leaderboard_pit.parquet`

Purpose:

1. field-sliced competitor or attacker views at market layer

Recommended columns:

1. `as_of_year`
2. `wipo_field`
3. `citing_assignee_name`
4. `citation_count`
5. `citation_lethality_sum_raw`
6. `attacker_pressure_index`
7. `method_version`

## 5.5 Adjacent ranking-ready classification and geography marts

These are not citation-only marts, but they should be planned alongside the same Silver/Gold refactor because they solve the missing `WIPO x CPC x jurisdiction x year` serving layer.

### `gold_family_classification_jurisdiction_pit.parquet`

Purpose:

1. family-level ranking and evidence by technology slice and geography over time

Recommended columns:

1. `docdb_family_id`
2. `as_of_year`
3. `wipo_field`
4. `cpc_main_group`
5. `jurisdiction_code`
6. `is_active_asof`
7. `family_blocking_power_score_asof`
8. `family_enforceability_score_asof`
9. `pre_asof_forward_citations_clean`
10. `classification_jurisdiction_support_level`
11. `historical_compare_safe`
12. `method_version`

### `gold_portfolio_classification_jurisdiction_pit.parquet`

Purpose:

1. portfolio-level ranking and exposure tables across technology slice and geography

Recommended columns:

1. `owner_name_harmonized`
2. `as_of_year`
3. `wipo_field`
4. `cpc_main_group`
5. `jurisdiction_code`
6. `portfolio_family_count_in_slice_asof`
7. `portfolio_active_family_count_in_slice_asof`
8. `portfolio_family_share_in_slice_asof`
9. `portfolio_blocking_density_asof`
10. `portfolio_enforceability_density_asof`
11. `portfolio_citation_pressure_index_asof`
12. `slice_rank_within_owner_year`
13. `historical_owner_truth_supported`
14. `method_version`

### `gold_market_cpc_jurisdiction_trend_pit.parquet`

Purpose:

1. market-level leaderboard and trend views inside `WIPO x CPC x jurisdiction x year`

Recommended columns:

1. `as_of_year`
2. `wipo_field`
3. `cpc_main_group`
4. `jurisdiction_code`
5. `family_count_asof`
6. `active_family_count_asof`
7. `family_share_within_slice_asof`
8. `growth_index_asof`
9. `blocking_density_asof`
10. `enforceability_density_asof`
11. `citation_pressure_index_asof`
12. `slice_rank_within_year`
13. `method_version`

Rules:

1. these marts should be PIT-safe and year-addressable,
2. they should be labeled as replay-derived where historical classification or owner truth is not fully native,
3. they should not be faked from current-only overlays.

---

## 6. Audit Findings For The Implemented Slice

The April 9, 2026 implementation audit found the following for the completed family and portfolio citation marts.

### 6.1 Family citation marts

1. `gold_family_citation_summary.parquet`
   - `17,633,618` rows
   - `17,633,618` distinct families
   - single current snapshot date: `2026-03-15`
2. `gold_family_citation_timeseries_pit.parquet`
   - `164,988,135` rows
   - `17,633,618` distinct families
   - year coverage: `2007..2026`
3. family citation support is currently overwhelmingly `high`
   - this reflects current source completeness behavior and should not be over-interpreted as strategic quality

### 6.2 Portfolio citation marts

1. `gold_portfolio_citation_summary.parquet`
   - `21,945,507` rows
   - `2,143,373` distinct owners
   - year coverage: `2007..2026`
2. `gold_portfolio_citation_timeseries.parquet`
   - row count matches `gold_portfolio_citation_summary`
3. `gold_portfolio_attacker_momentum.parquet`
   - `6,016,882` rows
   - `502,469` distinct owners
   - year coverage: `1997..2025`
4. `gold_portfolio_citation_pressure_by_field.parquet`
   - `2,052,577` rows
5. `gold_portfolio_citation_pressure_by_jurisdiction.parquet`
   - `2,000,661` rows

### 6.3 Market citation marts

1. `gold_market_citation_trend_pit.parquet`
   - `294` rows
   - `10` distinct WIPO fields
   - year coverage: `1996..2025`
2. `gold_market_citation_pressure_by_jurisdiction_pit.parquet`
   - `6,063` rows
   - `43` distinct citing jurisdictions
   - year coverage: `1996..2025`
3. `gold_market_attacker_leaderboard_pit.parquet`
   - `4,771,190` rows
   - `1,069,770` distinct citing assignees
   - year coverage: `1996..2025`
4. placeholder attacker and jurisdiction rows are filtered out in the final market citation marts

### 6.4 Serving findings

1. owner coverage for attacker and pressure marts is naturally lower than the portfolio summary mart because many portfolios have no meaningful external citation pressure rows
2. placeholder attacker rows still exist upstream in the mart, but backend serving excludes placeholder owners from portfolio citation attacker, field, and jurisdiction views
3. self-owner attacker rows also exist upstream because raw `is_self_citation` flags and harmonized owner-name equality are not fully equivalent
4. backend-v2 serving now explicitly excludes `citing_assignee_name == owner_name_harmonized` from:
   - attacker views
   - citation field views
   - citation jurisdiction views
5. market citation chronology had to clamp invalid raw years such as `9999` to the release snapshot-year boundary during ETL
6. market citation state remains lag-sensitive because citation accrual naturally trails filing activity; `market_state_reference` is kept alongside the citation-derived state for this reason

### 6.5 Real owner sanity checks

Observed live portfolio results after the refactor:

1. `APPLE`
   - `2026 family_count = 25,981`
   - `forward_citations_clean_total = 66,355`
   - `backward_citations_clean_total = 77,002`
   - top external attackers now surface as `SAMSUNG_ELECTRONICS_COMPANY`, `QUALCOMM`, `GOOGLE`
2. `TESLA`
   - `2026 family_count = 251`
   - `forward_citations_clean_total = 283`
   - `backward_citations_clean_total = 464`
   - top external fields and jurisdictions remain sensible after the serving filter

### 6.6 Real market sanity checks

Observed live market results after the refactor:

1. latest year is now correctly bounded to `2025`, not `9999`
2. top 2025 market citation fields are:
   - `Computer technology`
   - `Digital communication`
   - `Electrical machinery, apparatus, energy`
3. for 2025 `Computer technology`:
   - `citation_event_count = 85,516`
   - `citation_lethality_sum_raw ≈ 17,042.9`
   - top citing jurisdictions include `US`, `CN`, `EP`, `KR`, `WO`
   - top citing assignees include `SAMSUNG_ELECTRONICS_COMPANY`, `DELL_PRODUCTS`, `HUAWEI_TECHNOLOGIES_COMPANY`

### 6.7 Ranking-ready classification and geography audit

Observed live build results for the adjacent `WIPO x CPC x jurisdiction x year` serving layer:

1. `gold_family_classification_jurisdiction_pit.parquet`
   - `566,936,693` rows
   - `10,392,690` distinct families
   - year coverage: `2007..2026`
   - `35` distinct WIPO fields
   - `9,258` distinct CPC main groups
   - `82` distinct jurisdictions
   - no blank or placeholder jurisdiction codes in the final mart
   - support distribution:
     - `limited = 438,350,487` rows (`77.32%`)
     - `moderate = 89,111,715` rows (`15.72%`)
     - `strong = 39,474,491` rows (`6.96%`)
   - family coverage versus `gold_family_compare_pit` universe:
     - `10,392,690 / 17,633,618 = 58.94%`
   - replay flags are explicit and uniform:
     - `classification_membership_replayed_to_history = true`
     - `historical_classification_truth_supported = false`
     - `historical_compare_safe = true`
2. `gold_portfolio_classification_jurisdiction_pit.parquet`
   - `828,526,264` rows
   - `2,183,767` distinct owners
   - year coverage: `2007..2026`
   - `35` distinct WIPO fields
   - `9,245` distinct CPC main groups
   - `82` distinct jurisdictions
   - no blank or placeholder jurisdiction codes in the final mart
   - support distribution:
     - `limited = 655,836,681` rows (`79.16%`)
     - `moderate = 120,835,458` rows (`14.58%`)
     - `strong = 51,854,125` rows (`6.26%`)
   - owner coverage versus `silver_family_owner_bridge` universe:
     - `2,183,767 / 3,852,589 = 56.68%`
   - replay flags are explicit and uniform:
     - `historical_owner_truth_supported = false`
     - `current_owner_bridge_replayed_to_history = true`
     - `classification_membership_replayed_to_history = true`
     - `historical_classification_truth_supported = false`
     - `historical_compare_safe = true`
   - placeholder-owner caveat still exists upstream:
     - `UNKNOWN_OWNER` remains present as one owner with `5,579,932` rows
     - backend or UI serving should filter placeholder owners for ranked portfolio views
     - as of April 10, 2026 the backend serving layer now suppresses placeholder owners for portfolio-ranked search and resolution paths, and the ETL builders are patched so the next rebuild will exclude those owner rows upstream
3. `gold_market_cpc_jurisdiction_trend_pit.parquet`
   - `15,883,551` rows
   - year coverage: `2007..2026`
   - `35` distinct WIPO fields
   - `9,258` distinct CPC main groups
   - `82` distinct jurisdictions
   - no blank or placeholder jurisdiction codes in the final mart
   - support distribution:
     - `limited = 14,028,150` rows (`88.32%`)
     - `moderate = 1,068,325` rows (`6.73%`)
     - `strong = 787,076` rows (`4.96%`)
   - replay flags are explicit and uniform:
     - `classification_membership_replayed_to_history = true`
     - `historical_classification_truth_supported = false`
     - `historical_compare_safe = true`
4. representative 2026 slice sanity checks are sensible:
   - family layer top slices include:
     - `Electrical machinery, apparatus, energy / Y02E60/00 / CN`
     - `Computer technology / G06F16/00 / CN`
     - `Computer technology / G06F3/00 / US`
   - portfolio layer top slices include:
     - `TOYOTA_MOTOR_CORPORATION / Electrical machinery, apparatus, energy / Y02E60/00 / JP`
     - `SAMSUNG_ELECTRONICS_COMPANY / Computer technology / G06F3/00 / KR`
     - `IBM_INTERNATIONAL_BUSINESS_MACHINES_CORPORATION_ / Computer technology / G06F16/00 / US`
   - real owner spot checks remain sensible:
     - `APPLE` top 2026 slice is `Computer technology / G06F3/00 / US` with `3,237` families
     - `TESLA` top 2026 slices center on `Electrical machinery, apparatus, energy / H01M*`
5. market growth is present and not flat:
   - `4,374,637` rows have non-zero `growth_index_asof`
   - the current growth range is `0.0 .. 917.5`
6. implementation tuning note:
   - the portfolio ranking mart required a dedicated lower bucket count than the broader portfolio classification mix build
   - the final sealed implementation uses `8` owner buckets for the ranking mart, which materially reduced runtime without changing semantics

### 6.8 Acceptance outcome for the implemented slice

1. family citation serving is now formalized in Gold
2. portfolio citation serving is now formalized in Gold
3. market citation serving is now formalized in Gold
4. backend-v2 consumes the explicit Gold portfolio citation marts successfully
5. backend-v2 exposes dedicated market citation endpoints successfully
6. canonical portfolio citation Gold outputs build successfully after switching the summary mart to year chunking
7. ranking-ready classification and geography marts now also build successfully for:
   - family
   - portfolio
   - market
8. the new ranking marts are replay-labeled rather than overstating native historical owner or classification truth
9. ETL validation for the updated build layer passed:
   - `PYTHONPATH=etl/src etl/.venv-seed-backfill/bin/python -m pytest etl/tests/test_gold_build.py -q`
   - `14 passed`

---

## 7. UI Consumption Rules By Surface

## 7.1 Family

Use:

1. `gold_family_citation_summary`
2. `gold_family_citation_timeseries_pit`
3. `gold_family_attacker_summary`
4. Silver event ledger only for proof and drill-down

Do not use directly in UI cards:

1. `family_adjusted_citation_score_raw`

## 7.2 Filing or publication

Use:

1. Silver citation evidence rows only

Do not introduce:

1. publication citation scorecards,
2. publication citation percentile cards,
3. synthetic publication threat scoring

unless a later dedicated Gold contract exists.

## 7.3 Portfolio

Use:

1. `gold_portfolio_citation_summary`
2. `gold_portfolio_citation_timeseries`
3. `gold_portfolio_attacker_momentum`
4. `gold_portfolio_citation_pressure_by_field`
5. `gold_portfolio_citation_pressure_by_jurisdiction`
6. Silver drill-down rows only where the user asks for proof

## 7.4 Market

Use:

1. `gold_market_citation_trend_pit`
2. `gold_market_citation_pressure_by_jurisdiction_pit`
3. `gold_market_attacker_leaderboard_pit`

Do not present:

1. raw lethality sums as market truth scores,
2. current-only citation overlays as PIT chronology.

---

## 8. Implementation Order

1. formalize the citation-serving metric definitions in the lineage catalog,
2. rebuild family citation semantics first:
   - remove direct UI dependency on `family_adjusted_citation_score_raw`,
   - produce family citation summary and PIT chronology marts,
3. rebuild family heritage and attacker marts on top of the corrected family citation contract,
4. build portfolio citation summary and pressure marts,
5. rewire existing backend-v2 portfolio citation endpoints to the explicit Gold marts,
6. build market citation PIT and attacker leaderboards,
7. add ranking-ready `WIPO x CPC x jurisdiction x year` Gold marts for family, portfolio, and market,
8. leave publication citation Silver-first unless a new product requirement changes that.

---

## 9. Acceptance Criteria

The citation refactor is successful when:

1. family citation proof rows remain explorable from Silver ledgers,
2. family citation cards and attacker/heritage summaries no longer expose raw unstable intermediates,
3. portfolio citation tabs read from explicit Gold citation marts rather than mixed ad hoc rollups,
4. market citation views distinguish PIT-safe trend from current overlay,
5. filing/publication citation remains evidence-first and unforced into synthetic scorecards,
6. no UI surface exposes `family_adjusted_citation_score_raw` as a direct user-facing metric,
7. all citation aggregate outputs are labeled as raw counts, indices, bands, or ranks with the correct semantics,
8. family, portfolio, and market have clean year-addressable ranking marts for `WIPO`, `CPC`, and `jurisdiction` slices rather than relying on partial aggregates or current-only overlays.

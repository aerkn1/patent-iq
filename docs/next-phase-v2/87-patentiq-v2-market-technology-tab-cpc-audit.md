# PatentIQ v2 Market Technology Tab CPC Audit

## Scope

Audit of the current `frontend_v2` market technology tab and the wired `backend_v2` contracts against these proposed improvements:

1. Year filter for `Top CPC groups in selected field`
2. `CPC geography within field` filters by CPC main group and jurisdiction
3. Filterable `Top owners per CPC main group`
4. Yearly `applications / grants per CPC main group` by jurisdiction and total

This audit focuses on:

- current UI and backend contract behavior
- existing mart availability
- data quality and support caveats
- implementation cost and recommended settlement

## Current UI / Contract State

### Frontend

The technology tab currently renders three panels:

- `Top CPC groups in selected field`
- `CPC geography within field`
- `Global CPC importance`

See:

- `frontend_v2/components/market/market-workspace.tsx`
  - `Top CPC groups in selected field` at lines `2230-2244`
  - `CPC geography within field` at lines `2256-2270`

The current technology tab is latest-slice only:

- `top_cpcs` is loaded into the workspace payload with `limit=10`
- `cpc_jurisdictions` is loaded into the workspace payload with `limit=12`
- there is no user-facing year selector
- there are no explicit CPC or jurisdiction filters in the current tab

### Backend

Current market API exposure:

- `GET /api/v1/market-intelligence/cpc-trends`
- `GET /api/v1/market-intelligence/cpc-importance`

See:

- `backend_v2/api/v1/market_intelligence.py:95-102`

Important contract gap:

- `cpc-trends` does **not** currently expose `as_of_year`, even though the repository supports it
- there is **no dedicated market API route** for segment CPC-jurisdiction rows
- the workspace currently embeds CPC rows into `selected_segment`, which makes latest-slice rendering easy but is not sufficient for heavy filtering

See:

- repository year-aware CPC trend support in `backend_v2/infrastructure/repositories/market_intelligence_repository.py:1012-1040`
- current embedded selected-segment loading in `backend_v2/application/services/market_intelligence.py:206-218`
- current CPC-jurisdiction repository in `backend_v2/infrastructure/repositories/market_intelligence_repository.py:571-600`

## Underlying Mart Availability

### CPC trend mart

File:

- `etl/data/gold/gold_market_cpc_trend_pit.parquet`

Schema confirms latest-slice CPC metrics by:

- `wipo_industry_code`
- `as_of_year`
- `cpc_main_group`

with metrics such as:

- `cpc_family_count_asof`
- `cpc_active_family_count_asof`
- `cpc_family_share_within_segment_asof`
- `cpc_growth_index_asof`
- `cpc_rank_within_segment_year`

Coverage:

- overall mart years: `2007-2026`
- overall rows: `862,969`
- served market field subset rows: `711,567`
- served market field subset years: `2007-2026`

For the 10 served market fields:

- `2023` served rows: `49,439`
- fields covered: all `10`

Quality flags on the served `2023` slice:

- `historical_compare_safe = true`
- `historical_classification_truth_supported = false`
- `classification_membership_replayed_to_history = true`

Interpretation:

- historical use is available and consistent enough for direction
- historical CPC membership is replayed, not historically observed classification truth

### CPC jurisdiction mart

File:

- `etl/data/gold/gold_market_cpc_jurisdiction_trend_pit.parquet`

Schema confirms latest-slice CPC-by-jurisdiction rows by:

- `wipo_field`
- `as_of_year`
- `cpc_main_group`
- `jurisdiction_code`

with metrics such as:

- `family_count_asof`
- `active_family_count_asof`
- `family_share_within_slice_asof`
- `citation_pressure_index_asof`
- `growth_index_asof`
- `blocking_density_asof`
- `classification_jurisdiction_support_level`

Coverage:

- overall mart years: `2007-2026`
- overall rows: `15,883,551`
- served market field subset rows: `10,773,152`
- served market field subset years: `2007-2026`

For the 10 served market fields:

- `2023` served rows by support level:
  - `limited`: `797,829`
  - `moderate`: `45,701`
  - `strong`: `36,215`

Interpretation:

- the mart is large enough to support server-side filtering
- support-level labeling is important because `limited` dominates the slice

### Owner classification marts

Files:

- `etl/data/gold/gold_portfolio_classification_mix_pit.parquet`
- `etl/data/gold/gold_portfolio_classification_jurisdiction_pit.parquet`

These show that owner x CPC and owner x field x CPC x jurisdiction data exist on the portfolio side, but they are not directly suitable as a drop-in market answer for `top owners per CPC main group within field`.

Why:

- `gold_portfolio_classification_mix_pit` has `classification_type = CPC_MAIN_GROUP`, but no `wipo_field`
- `gold_portfolio_classification_jurisdiction_pit` has `wipo_field + cpc_main_group + jurisdiction_code`, but is jurisdiction-sliced and therefore non-additive back to a pure field+CPC owner leaderboard

Conclusion:

- current owner marts are useful evidence that the data ingredients exist
- they do **not** remove the need for a new market-focused owner-by-field-by-CPC aggregation

### Publication event source

File:

- `etl/data/silver/silver_family_member_publications.parquet`

Key fields:

- `appln_id`
- `docdb_family_id`
- `publn_auth`
- `publn_date`
- `is_application_stage`
- `is_grant_stage`

This is the correct raw source for application / grant event counting.

## Findings By Proposal

### 1. Year filter for `Top CPC groups in selected field`

### Availability

Yes.

The underlying CPC trend mart is year-aware and already supports `as_of_year`.

Evidence:

- repository method supports `as_of_year`: `backend_v2/infrastructure/repositories/market_intelligence_repository.py:1012-1040`
- current API does not expose `as_of_year`: `backend_v2/api/v1/market_intelligence.py:95-97`

### Current behavior

The current UI is **not** all-time and **not** truly user-selectable.

It is a single latest supported slice:

- the workspace currently loads top CPC rows for the selected field
- because the repository resolves unspecified year to latest supported year and the repo year cap is `2023`, the current panel is effectively `2023`

### Quality

Good enough for a year filter if the panel is described as:

- historical-safe
- replayed CPC membership history
- directional composition, not publication-date classification truth

### Cost

Low.

Required change:

- expose `as_of_year` on the `cpc-trends` market route or add a segment-scoped CPC trend endpoint

### Audit conclusion

`Available now with minimal backend contract work.`

## 2. `CPC geography within field` filters by CPC main group and jurisdiction

### Availability

Yes.

The current row grain already includes:

- `as_of_year`
- `wipo_field`
- `cpc_main_group`
- `jurisdiction_code`

Evidence:

- `backend_v2/infrastructure/repositories/market_intelligence_repository.py:571-600`
- `frontend_v2/lib/types/market-v2.ts` `MarketCpcJurisdictionRow`

### Current behavior

The current workspace only loads a latest-year top slice:

- current selected-segment payload requests `limit=12`
- the UI renders only those returned rows

This means frontend-only filtering would be misleading because:

- the data is already truncated before it reaches the client

### Quality

Usable, with an explicit support-level caveat.

For the served fields in `2023`, most rows are `limited`, with a meaningful but much smaller `moderate/strong` tail.

### Cost

Low to medium.

Required change:

- add a dedicated CPC-jurisdiction endpoint with:
  - `segment_id`
  - `as_of_year`
  - optional `cpc_main_group`
  - optional `jurisdiction_code`
  - `limit/offset`

Do not keep expanding the workspace payload for this.

### Audit conclusion

`Available now, but should be implemented as a lazy backend section rather than client-only filtering on the current workspace slice.`

## 3. `Top owners per CPC main group` as filterable

### Availability

Not available as an existing market contract or clean market mart.

It is derivable from existing data.

The defensible path is:

- family classification membership
- plus owner bridge
- aggregated to `field + cpc_main_group + owner`

Evidence:

- family classification basis exists in `gold_family_classification_mix_pit.parquet`
- owner bridge exists in `silver_family_owner_bridge.parquet`
- sample query for `Computer technology` + `G06F3/00` in `2023` returned:
  - `SAMSUNG_ELECTRONICS_COMPANY`
  - `UNKNOWN_OWNER`
  - `VIVO_COMMUNICATION_TECHNOLOGY_COMPANY`
  - `CANON`
  - `IBM...`

### Quality

Current-year quality is acceptable.

Caveats:

- ownership is replayed through the current owner bridge rather than full historical owner truth
- `UNKNOWN_OWNER` can be materially present and should be explicitly handled
- this should start as a current-year view, not as a long historical owner trend

### Cost

Medium.

Recommended implementation path:

- create a dedicated market endpoint
- aggregate from family classification mix + owner bridge
- do **not** derive this from `gold_portfolio_classification_jurisdiction_pit` by summing jurisdiction rows

### Audit conclusion

`Feasible with existing data, but requires a new backend aggregation and should launch as current-year only.`

## 4. Yearly `applications / grants per CPC main group` by jurisdiction and total

### Availability

Not already marted, but derivable.

Correct derivation path:

- field + CPC membership from `gold_family_classification_mix_pit`
- publication events from `silver_family_member_publications`
- office dimension from `publn_auth`

I verified that this works on a concrete slice:

- `Computer technology`
- `G06F3/00`
- years `2021-2023`

Sample `2021` results:

- `CN`: `10,830` applications, `5,767` grants
- `US`: `6,232` applications, `6,219` grants
- `EP`: `1,460` applications, `721` grants

### Quality

Medium.

Caveats:

- CPC membership is replayed historically, so this is not filing-date or publication-date classification truth
- CPC groups are multi-membership, so totals are not additive across CPC groups
- `publn_auth` is an office / route dimension; `WO` and `EP` should be treated accordingly

### Performance / implementation risk

This should **not** be implemented as a broad on-the-fly raw join in the UI path.

Observed audit signal:

- a narrow validation query for one field + one CPC + `2021-2023` completed, but took about `5.8s`

That is acceptable for audit validation but not a good target for an interactive generalized route unless it is:

- pre-aggregated
- cached
- or backed by a dedicated gold section

### Cost

Medium to high.

Recommended implementation path:

- create a dedicated market CPC applications/grants endpoint or mart
- keep methodology explicit:
  - `unit = distinct appln_id publication events`
  - `not additive across CPC groups`

### Audit conclusion

`Feasible, but should be introduced only through a dedicated aggregated backend section, not by querying raw joins directly per page load.`

## Recommended Settlement

### Safe next steps

1. Add year filter to `Top CPC groups in selected field`
2. Add dedicated backend section for `CPC geography within field` with CPC and jurisdiction filters
3. Add `Top owners by CPC main group` as a current-year-only additive panel

### Defer until backend aggregation exists

4. `Applications / grants by CPC main group by jurisdiction and total as yearly`

This one is analytically useful, but it should not ship until the aggregation is formalized and the methodology is visible.

## Implementation Notes

### Suggested contract shape

Do not overload the workspace payload further.

Add lazy endpoints such as:

- `/market-intelligence/segments/{segment_id}/cpc-trends?as_of_year=...`
- `/market-intelligence/segments/{segment_id}/cpc-jurisdictions?as_of_year=...&cpc_main_group=...&jurisdiction_code=...`
- `/market-intelligence/segments/{segment_id}/cpc-owners?as_of_year=...&cpc_main_group=...`
- `/market-intelligence/segments/{segment_id}/cpc-applications-grants?year_from=...&year_to=...&cpc_main_group=...&jurisdiction_code=...`

### Methodology labels that should remain visible

- `Top CPC groups`: replayed CPC membership history
- `CPC geography`: support level (`limited/moderate/strong`)
- `Top owners by CPC`: current-owner replay caveat
- `Applications / grants by CPC`: event counts by office, non-additive across CPC groups

## Final Audit Verdict

- `1`: `Yes, available and low-cost`
- `2`: `Yes, available and low/medium-cost`
- `3`: `Yes, derivable and medium-cost`
- `4`: `Yes, derivable but medium/high-cost and should be aggregated before UI exposure`

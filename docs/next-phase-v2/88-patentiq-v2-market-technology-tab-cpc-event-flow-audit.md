# PatentIQ v2 Market Technology Tab CPC Event Flow Audit

## Scope

Audit of the remaining unimplemented technology-tab proposal:

1. yearly `applications / grants per CPC main group`
2. by jurisdiction and total
3. with usable quality for market-facing analytics in `frontend_v2` and `backend_v2`

This note is additive to:

- [87-patentiq-v2-market-technology-tab-cpc-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/87-patentiq-v2-market-technology-tab-cpc-audit.md)

The earlier audit established schema availability. This audit checks the actual local data shape, duplication risk, coverage, and likely endpoint settlement.

## Current State

The technology tab now already covers:

1. year-filtered `Top CPC groups in selected field`
2. backend-filtered `CPC geography within field`
3. `Top owners by CPC main group`

The remaining gap is a CPC-sliced publication-event panel.

There is currently:

1. no dedicated `backend_v2` route for CPC applications/grants
2. no dedicated market mart pre-aggregated at `field + CPC + jurisdiction + publication year`
3. only the existing field-level applications/grants endpoint in the market grants tab

Relevant current code:

- `backend_v2/infrastructure/repositories/market_intelligence_repository.py`
- `backend_v2/application/services/market_intelligence.py`
- `frontend_v2/components/market/market-workspace.tsx`

## Raw Inputs

The required raw ingredients do exist.

### 1. Field and CPC membership

Source:

- `etl/data/gold/gold_family_classification_mix_pit.parquet`

Relevant columns:

- `docdb_family_id`
- `as_of_year`
- `primary_wipo_field_asof`
- `cpc_main_groups_asof`
- `cpc_main_group_count_asof`

This is the correct family-to-field and family-to-CPC basis for the market technology tab.

### 2. Publication event rows

Source:

- `etl/data/silver/silver_family_member_publications.parquet`

Relevant columns:

- `docdb_family_id`
- `appln_id`
- `publn_auth`
- `publn_date`
- `is_application_stage`
- `is_grant_stage`

Local snapshot checks:

1. total publication rows: `42,692,835`
2. application-stage rows: `24,565,247`
3. grant-stage rows: `11,151,715`
4. invalid publication-year rows: `225`, all `9999`

So the event source is not sparse. It only needs a small invalid-year filter.

## Data Availability

## 1. Is the use case possible?

Yes.

This metric is derivable by joining:

1. `gold_family_classification_mix_pit`
2. `silver_family_member_publications`

Join key:

- `docdb_family_id`

Aggregation grain:

- `primary_wipo_field_asof`
- `cpc_main_group`
- `publn_auth`
- `year(publn_date)`

Counting unit:

- distinct `appln_id`

This is the same event-counting basis already used by the market grants tab, but here it is replayed into CPC slices.

## 2. Is there an existing ready mart?

No.

The current market marts cover:

1. CPC composition by field-year
2. CPC geography by field-year
3. owner concentration by field-year+CPC

But there is no ready market mart for:

- `field + CPC + jurisdiction + publication year + application/grant counts`

So this is feasible, but it is still a new backend aggregation.

## Coverage And Quality

## 1. CPC family coverage is incomplete

At `2023`, the share of served-field families with at least one CPC main-group assignment is:

1. `Audio-visual technology`: `49.68%`
2. `Basic communication processes`: `65.73%`
3. `Computer technology`: `75.09%`
4. `Control`: `50.60%`
5. `Digital communication`: `76.17%`
6. `Electrical machinery, apparatus, energy`: `50.38%`
7. `IT methods for management`: `76.95%`
8. `Measurement`: `43.35%`
9. `Semiconductors`: `73.68%`
10. `Telecommunications`: `49.16%`

This means a CPC event-flow panel is not a complete restatement of the full field universe.

It should be framed as:

- `CPC-coded event flow inside the selected field`

not as:

- `all field applications/grants restated by CPC`

## 2. Event coverage is materially better than family coverage

For the same `2023` served-field slices, the share of publication events that sit on families with at least one CPC main-group assignment is higher than the family-share figures.

Examples:

1. `Computer technology`: `87.53%` of application events, `94.04%` of grant events
2. `Digital communication`: `91.47%` of application events, `96.34%` of grant events
3. `Semiconductors`: `90.04%` of application events, `93.36%` of grant events
4. `IT methods for management`: `79.03%` of application events, `81.50%` of grant events
5. `Measurement`: `82.90%` of application events, `91.15%` of grant events

Interpretation:

1. the metric is analytically useful
2. coverage is good enough for a market drilldown
3. but it still needs a coverage caveat because not all field families contribute CPC main groups

## 3. Historical quality is medium, not perfect

The application/grant events themselves are real dated publication rows.

The CPC assignment is the weaker part:

1. CPC membership is replayed to the PIT year basis
2. it is not true publication-time CPC mutation history
3. this is the same historical caveat already accepted for the existing CPC panels

So the correct interpretation is:

- year-accurate event flow on top of replayed CPC membership

## Duplication And Additivity

## 1. Sums across CPC groups are unsafe

The biggest settlement risk is overcount from CPC overlap.

For `Computer technology` in `2023`:

1. field application total: `463,958`
2. field grant total: `267,438`
3. summed across all CPC groups: `663,612` applications
4. summed across all CPC groups: `471,047` grants

Overcount factor relative to the field total:

1. applications: about `1.43x`
2. grants: about `1.76x`

So this panel must never encourage users to sum multiple CPC rows into a field total.

## 2. Sums within one selected CPC slice are acceptable only for that slice

Within a single chosen CPC main group, the rows are meaningful by:

1. office
2. year

But even there, the correct wording is still:

- office-coded application/grant events

not:

- unique field families

## Row Volume And Runtime

## 1. Unfiltered field-wide CPC event flow is too large for direct UI rendering

For `Computer technology` from `2007-2023`:

1. grouped rows at `year + CPC + jurisdiction`: `324,621`
2. distinct CPC main groups: `6,447`
3. distinct jurisdictions: `76`

Local DuckDB runtime for that one-field grouped aggregate:

- about `3.0s`

This is too large for a default table and too expensive for a casual unfiltered tab render.

## 2. A required CPC filter makes the metric manageable

For `Computer technology` and `G06F3/00` from `2007-2023`:

1. grouped rows at `year + jurisdiction`: `656`
2. local runtime: about `1.5s`

This is manageable for:

1. a lazy-loaded endpoint
2. a chart + table drilldown
3. optional jurisdiction filtering

So the right settlement is:

- require `cpc_main_group`

## 3. The data is not sparse for major CPCs

Example:

- `Computer technology` + `G06F3/00`

Top `2023` offices:

1. `CN`: `10,320` applications, `8,182` grants
2. `US`: `9,649` applications, `9,713` grants
3. `WO`: `3,225` applications, `0` grants
4. `EP`: `2,931` applications, `1,567` grants
5. `KR`: `2,260` applications, `1,837` grants
6. `JP`: `2,144` applications, `1,928` grants

Example chronology for `EP` within the same CPC:

1. `2008`: `206` applications, `0` grants
2. `2012`: `2,158` applications, `87` grants
3. `2018`: `3,574` applications, `1,626` grants
4. `2023`: `2,931` applications, `1,567` grants

So the problem is not sparsity. The problem is mostly overlap and row volume.

## Interpretation Caveats

This metric is useful if the UI and contract make these rules explicit:

1. it is an `application/grant event` view, not a family-stock view
2. it is `office-coded`, so `EP` and `WO` are office/route codes, not countries
3. it is `CPC-sliced`, so different CPC groups are overlapping and non-additive
4. it is `coverage-limited` to families with CPC main-group assignments in the PIT slice
5. historical years use replayed CPC membership, not publication-time CPC truth

## Recommendation

## 1. Data availability verdict

Yes, this feature is available with acceptable quality.

Quality rating:

- `medium to good`

Use it for:

1. selected-CPC chronology
2. office distribution inside one CPC slice
3. application/grant mix inside one CPC slice

Do not use it for:

1. summing across CPC groups
2. presenting it as the full field total without a CPC coverage note
3. default-loading all CPC groups at once

## 2. Backend settlement

Do not implement this as a raw unfiltered UI query.

Preferred additive endpoint:

- `GET /market-intelligence/segments/{segment_id}/cpc-applications-grants`

Recommended parameters:

1. `cpc_main_group` required
2. `year_from` optional
3. `year_to` optional
4. `jurisdiction_code` optional
5. `jurisdiction_limit` optional

Recommended response structure:

1. yearly `total` rows for the selected CPC
2. yearly `jurisdiction` rows for the selected CPC
3. optional top-office slice over the selected range

This avoids mixing:

1. total chronology
2. office table
3. jurisdiction-filtered detail

into one ambiguous row type.

## 3. Frontend settlement

Add this as one more lazy `Surface` in the technology tab, reusing the current market styles.

Recommended controls:

1. `CPC main group` select, required
2. `Jurisdiction` select or text filter, optional
3. `Chart / Table` toggle

Recommended default view:

1. chart of yearly `applications` vs `grants` for the selected CPC total
2. table of top jurisdictions for the selected year or selected range

Do not default to a giant raw CPC x jurisdiction table.

## Final Verdict

The feature is viable with current data.

But the correct settlement is narrow:

1. selected field
2. selected CPC main group
3. yearly event flow
4. optional jurisdiction drilldown

If implemented that way, the metric is informative and cheap enough.

If implemented as an unfiltered all-CPC table, it will be too long, too overlap-heavy, and too easy to misread.

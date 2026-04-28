# PatentIQ V2 Classification First-Seen Visibility Audit And Upgrade Plan

## Goal

Determine whether PatentIQ has enough raw data to replace the current `stable_family_classification_replay` contract with a stronger `first-seen classification visibility` contract for:

1. family chronology,
2. portfolio classification exposure over time,
3. market CPC trend and importance marts.

## Short Conclusion

Yes.

PatentIQ appears to have enough raw data for a strong `first-seen visibility` model for CPC and IPC/WIPO chronology.

It does **not** appear to have enough raw data for true `code mutation history` for CPC.

So the correct next upgrade is:

1. stop replaying the full final family classification set backward unchanged,
2. derive `first_seen_year` for each family-classification pair from member-publication chronology,
3. rebuild family, portfolio, and market classification PIT marts using that visibility rule.

## What Was Audited

Raw classification sources:

1. [bronze_patstat_appln_cpc.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_cpc.parquet)
2. [bronze_patstat_appln_ipc.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_ipc.parquet)

Chronology backbone:

1. [silver_family_member_publications.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet)

Current classification-serving lane:

1. [silver_family_classification_pit_dense.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense.parquet)
2. [gold_family_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_mix_pit.parquet)
3. [gold_portfolio_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_classification_mix_pit.parquet)

## Audit Results

### CPC Join Coverage

Distinct CPC applications:

1. `24,535,049`

Distinct member-publication applications:

1. `30,810,155`

CPC applications that join to the member-publication chronology:

1. `21,889,868`

CPC applications that do not join:

1. `2,645,181`

Approximate CPC appln join coverage:

1. about `89.2%`

### IPC Join Coverage

Distinct IPC applications:

1. `34,417,984`

IPC applications that join to the member-publication chronology:

1. `30,810,155`

IPC applications that do not join:

1. `3,607,829`

Approximate IPC appln join coverage:

1. about `89.5%`

### First-Seen Family-Code Coverage

Derived distinct `family x CPC` pairs with first-seen year:

1. `21,967,482`

Derived distinct `family x IPC` pairs with first-seen year:

1. `30,708,111`

First-seen year span for CPC:

1. min year: `1968`
2. max year: `2025`

First-seen year span for IPC:

1. min year: `1968`
2. max year: `2025`

IPC additional advantage:

1. [bronze_patstat_appln_ipc.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_ipc.parquet) includes `ipc_version`
2. all audited first-seen IPC family-code pairs retained non-null version support in the join path

## What This Means

### What We Can Support Well

We can support:

1. `first visible year` of a CPC or IPC/WIPO classification for a family,
2. family-year classification sets that expand over time instead of appearing fully formed in every year,
3. portfolio classification exposure that changes because family code visibility changes over time,
4. market CPC trend marts that reflect when code-bearing families become visible in the historical corpus.

### What We Still Cannot Claim

We still cannot safely claim:

1. true CPC reassignment history,
2. exact code mutation chronology after first visibility,
3. historical owner truth for portfolio classification exposure.

So this upgrade changes the contract from:

1. `stable_family_classification_replay`

to:

1. `first_seen_classification_visibility`

but **not** to:

1. `fully dated code mutation truth`

## Recommended Contract

For the next classification upgrade:

1. derive `first_seen_date` and `first_seen_year` for each `docdb_family_id x classification_code`,
2. treat a classification as visible in `as_of_year` only when `first_seen_year <= as_of_year`,
3. continue to set:
   - `historical_classification_truth_supported = false`
4. replace:
   - `classification_visibility_policy = stable_family_classification_replay`
   with:
   - `classification_visibility_policy = first_seen_classification_visibility`

## Recommended New Artifact

### `silver_family_classification_visibility_timeline.parquet`

Native grain:

1. `docdb_family_id`
2. `classification_type`
3. `classification_code`

Recommended columns:

1. `docdb_family_id`
2. `classification_type`
   - `WIPO_FIELD`
   - `IPC_SUBCLASS`
   - `CPC_SECTION`
   - `CPC_SUBCLASS`
   - `CPC_MAIN_GROUP`
3. `classification_code`
4. `classification_label`
5. `first_seen_date`
6. `first_seen_year`
7. `visibility_source`
   - `member_publication_first_seen`
8. `historical_classification_truth_supported`

## Rebuild Order

1. build `silver_family_classification_visibility_timeline`
2. rebuild `silver_family_classification_pit_dense` using first-seen visibility rather than stable replay
3. rebuild [gold_family_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_mix_pit.parquet)
4. rebuild [gold_portfolio_classification_mix_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_classification_mix_pit.parquet)
5. build `gold_market_cpc_trend_pit`
6. build `gold_cpc_importance_pit`

## Product Impact

### Family

Families will no longer show the same CPC set in every PIT year.

Instead:

1. codes appear only after their first visible year,
2. breadth, concentration, and top-group summaries can change over time,
3. chronology becomes materially more believable.

### Portfolio

Portfolio classification exposure becomes more realistic because:

1. family code visibility changes over time,
2. owner-year classification shares stop inheriting late-arriving family codes too early,
3. the current-owner replay caveat remains, but the classification chronology itself improves.

### Market

This is the highest-value upgrade.

It enables:

1. CPC groups inside a WIPO field to emerge over time,
2. more defensible filing/publication trend curves,
3. stronger CPC importance ranking over time.

## Recommendation

Proceed with the `first-seen visibility` upgrade before building:

1. `gold_market_cpc_trend_pit`
2. `gold_cpc_importance_pit`

That sequence will make the market-layer classification history meaningfully better than the current stable replay contract.

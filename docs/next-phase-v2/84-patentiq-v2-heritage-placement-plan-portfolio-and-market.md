# PatentIQ V2 Heritage Placement Plan For Portfolio And Market

## Decision

Do **not** prioritize heritage as a first-class family-page lane.

Use heritage primarily in:

1. `Portfolio`
2. `Market Intelligence`

Reason:

1. family pages answer current entity questions first
2. heritage is much more valuable when aggregated or compared across a portfolio or market landscape
3. many individual families legitimately have thin or zero heritage, which makes the signal stronger as a contextual portfolio/market lens than as a family headline

## Current Status

### Portfolio

Portfolio is the strongest immediate fit.

What exists now:

1. [gold_portfolio_heritage_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_heritage_summary.parquet) exists
2. [gold_family_heritage_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet) exists
3. backend portfolio overview already serves `portfolio_heritage_score`
4. frontend portfolio executive already shows a heritage card

What is missing:

1. `main_window_family_count`
2. `heritage_backfill_family_count`
3. `portfolio_family_count_heritage_scope`
4. a visible explanation that heritage can include older support families outside the current operating family universe
5. a ranked `Top heritage families` drilldown

Conclusion:

1. portfolio heritage is not blocked by missing data
2. it is mostly a backend contract and UI placement problem

### Market

Market is a good use case, but not yet contract-ready in the same way as portfolio.

What exists now:

1. market workspace is already historical in chronology terms
2. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet) spans `1956-2025`
3. current market views already show long-run segment trends

What does **not** exist now:

1. no explicit market heritage mart
2. no `market_heritage_score`
3. no `heritage_backfill` flag in current market API contract
4. no market UI section that distinguishes:
   - current operating trend
   - heritage-supported historical influence

Conclusion:

1. market already contains long-run history
2. but it does not yet have heritage semantics
3. so market heritage needs a new serving contract, not just a UI reshuffle

## Recommended Product Placement

### 1. Portfolio

Best placement:

1. `Executive` summary card
2. `Families` or `Citations` drilldown panel

#### Executive

Show one compressed card:

1. label:
   - `Heritage Depth`
2. value:
   - keep current heritage score or heritage band
3. support line:
   - `main-window families: X`
   - `heritage-backfill families: Y`

Why:

1. the executive area is where the user decides whether the portfolio has long-run citation lineage
2. denominator context prevents the metric from looking like an arbitrary additive mass

#### Drilldown

Add a ranked panel:

1. `Top heritage families`

Columns:

1. family id
2. primary field
3. status
4. heritage score
5. scope role
   - `main window`
   - `heritage support`

Optional secondary panel:

1. age-bucket mix
   - `1996-2006`
   - `2007-2014`
   - `2015+`

This is the best placement because large portfolios need a concise executive signal plus a drilldown, not a full separate heritage workspace.

### 2. Market

Best placement:

1. `Overview` methodology-aware support card
2. `Technology` or `Competition` historical depth panel

Do **not** place heritage in market as a simple copy of the portfolio card.

Market heritage should answer:

1. which fields have deep historical lineage
2. which segments are current heat vs historical incumbency
3. whether a segment’s current state is built on a deep old base or a recent acceleration

Recommended market heritage outputs:

1. `market_heritage_depth_score`
2. `market_heritage_backfill_family_count`
3. `market_main_window_family_count`
4. `market_heritage_share_of_segment`
5. `heritage_pressure_label`

Recommended market UI:

1. `Historical depth` card in `Overview`
2. `Deep heritage segments` ranked list
3. segment detail callout:
   - `Current heat`
   - `Historical depth`
   - `Recent acceleration vs inherited depth`

Why:

1. market heritage is most useful as a contrast against current market heat
2. it is not the same as market size or market density

## Execution Plan

### Phase 1: Portfolio Heritage Visibility

Implement first.

#### Backend

Extend portfolio repository/service to join:

1. [gold_portfolio_heritage_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_heritage_summary.parquet)

Expose:

1. `portfolio_total_heritage_score`
2. `portfolio_avg_heritage_score`
3. `portfolio_family_count_heritage_scope`
4. `main_window_family_count`
5. `heritage_backfill_family_count`

#### Frontend

Portfolio executive:

1. rename current heritage card if needed to `Heritage Depth`
2. add support copy under the value
3. add caveat text:
   - current portfolio heritage can include historical backfill support

Portfolio drilldown:

1. `Top heritage families`
2. `Age-bucket heritage mix`

#### Why this phase is cheap

1. the marts already exist
2. the portfolio page already has a heritage slot
3. no new ETL is required for the first pass

### Phase 2: Market Heritage Contract

Implement after portfolio.

#### Required data work

Build a dedicated market heritage mart, likely grouped from:

1. [gold_family_heritage_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet)
2. family-to-field mapping already used by market intelligence

Recommended output:

1. `gold_market_heritage_summary.parquet`

Suggested grain:

1. `wipo_industry_code`
2. optional `as_of_year`

Suggested fields:

1. `market_heritage_depth_score`
2. `market_heritage_backfill_family_count`
3. `market_main_window_family_count`
4. `market_heritage_share_of_segment`
5. `market_deep_heritage_family_count`
6. `market_heritage_age_mix`

#### Backend

Extend market repository/service to expose:

1. overview-level heritage summary
2. segment-level historical depth rows

#### Frontend

Add:

1. `Historical depth` card in market overview
2. `Deep heritage segments` list
3. segment detail support block:
   - `historical depth`
   - `current heat`
   - `market state reference`

### Phase 3: Optional Cross-Links

Only after phases 1 and 2.

Possible additions:

1. portfolio to market:
   - show whether a portfolio is concentrated in deep-heritage segments
2. market to portfolio:
   - show owners with strongest heritage presence in the selected segment

## What Not To Do

1. do not expose heritage-only families in default family search as a side effect of this work
2. do not use raw additive heritage mass without denominator context
3. do not treat market long-run timeseries as if they already solve market heritage semantics
4. do not collapse current-state and heritage-support scope into one unlabeled number

## Acceptance Criteria

### Portfolio

1. users can tell how much of the heritage signal comes from main-window vs backfill families
2. large portfolios have a usable ranked heritage drilldown
3. thin-heritage portfolios do not look broken; they show low support explicitly

### Market

1. users can distinguish current market heat from deep historical lineage
2. heritage is exposed as a separate market lens, not hidden inside generic timeseries
3. market heritage does not require heritage-only family navigation to be useful

## Final Recommendation

According to the current repo state:

1. `Portfolio heritage` should be implemented now
2. `Market heritage` should be planned now but implemented after adding a dedicated market heritage serving contract
3. `Family heritage` should stay secondary and not drive the main product placement decision

That is the cleanest use of the current data without confusing current-state family navigation.

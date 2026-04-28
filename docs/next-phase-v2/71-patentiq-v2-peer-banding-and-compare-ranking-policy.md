# PatentIQ V2 Peer Banding And Compare Ranking Policy

## Purpose

Define how PatentIQ V2 should:

1. convert non-normalized portfolio metrics into client-safe qualitative bands,
2. compare portfolios of very different scale without collapsing into one misleading global score,
3. keep family peer ranking separate from market slice ranking,
4. avoid mixing entity peer percentiles with CPC/WIPO/jurisdiction leaderboard math.

This note turns the earlier qualitative direction into a concrete serving policy.

Related notes:

1. [62-patentiq-v2-portfolio-executive-metric-sensibility-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/62-patentiq-v2-portfolio-executive-metric-sensibility-audit.md)
2. [70-patentiq-v2-current-serving-rebuild-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/70-patentiq-v2-current-serving-rebuild-audit.md)
3. [33-patentiq-v2-portfolio-and-forecast-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md)
4. [34-patentiq-v2-compare-and-semantic-workspace-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/34-patentiq-v2-compare-and-semantic-workspace-contract.md)
5. [portfolio-size-normalization-and-crown-jewel-ranking-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/portfolio-size-normalization-and-crown-jewel-ranking-requirements.md)

Audit date: `2026-04-10`

---

## Core Principle

There are two different ranking systems in PatentIQ and they must not be conflated.

### 1. Entity peer ranking

This ranks a `family` or `portfolio` against similar entities.

Examples:

1. how strong is this family relative to other families in its field and age cohort,
2. how large is this portfolio's blocking footprint relative to portfolios of similar size,
3. how concentrated is this portfolio relative to portfolios with similar family counts.

### 2. Market slice ranking

This ranks a `field`, `CPC`, or `jurisdiction slice`.

Examples:

1. which CPC groups are most important in `2025`,
2. which WIPO field x CPC x jurisdiction slices are heating or cooling,
3. which market slices have the highest blocking density this year.

These market slice ranks provide context for where an entity competes. They are not the same thing as the entity's own peer percentile.

---

## Portfolio Peer Classes

Portfolio peer classes should be decided from `portfolio_family_count_within_mega_cluster`.

This is the right denominator because:

1. it is already the stable in-scope quantity used across portfolio serving,
2. it directly addresses the cross-scale comparison problem,
3. it is available in the refreshed current-serving Gold mart.

### Actual Current Distribution

Observed on `2026-04-10` from `gold_portfolio_summary.parquet`:

1. `1` family: `1,589,496` portfolios
2. `2-5` families: `991,274` portfolios
3. `6-20` families: `351,660` portfolios
4. `21-100` families: `85,692` portfolios
5. `101-500` families: `13,056` portfolios
6. `501+` families: `3,222` portfolios

This bucket design is therefore not arbitrary. It is supported by real population density and keeps enough portfolios in every peer class for stable percentile math.

### Canonical Portfolio Peer Buckets

1. `1`
   - label: `1 family`
2. `2_5`
   - label: `2-5 families`
3. `6_20`
   - label: `6-20 families`
4. `21_100`
   - label: `21-100 families`
5. `101_500`
   - label: `101-500 families`
6. `501_plus`
   - label: `501+ families`

### Why This Peer Logic Is Needed

Without peer buckets:

1. mass metrics over-reward huge portfolios,
2. average metrics over-reward tiny portfolios,
3. crown-jewel metrics become unstable when one-family and mega-portfolios share the same comparator pool.

---

## Portfolio Metric Families

Portfolio compare and executive interpretation should use three distinct lenses.

### 1. Mass

Purpose:

1. show footprint and aggregate strategic weight

Examples:

1. `portfolio_total_mass_score`
2. `portfolio_current_threat_score`
3. `portfolio_heritage_score`

Serving rule:

1. keep raw value,
2. add peer percentile within portfolio-size bucket,
3. show qualitative band as the client-facing headline.

### 2. Density

Purpose:

1. show how concentrated the strong assets are within the portfolio

Examples:

1. `portfolio_hit_rate_top_decile`
2. `portfolio_avg_blocking_power_within_mega_cluster`

Serving rule:

1. use peer percentile or percentile-derived band,
2. suppress when the portfolio is too small for honest density interpretation.

### 3. Crown Jewels

Purpose:

1. compare top-tier strategic weapons while neutralizing raw size

Examples:

1. `portfolio_crown_jewel_index`
2. future top-`10`, top-`10%`, top-`50`, or top-`100` family subset rollups

Serving rule:

1. show this as a separate compare lens,
2. do not merge it into mass or density,
3. use it for startup-versus-giant comparisons when the question is strength of elite assets rather than estate size.

---

## Portfolio Qualitative Bands

For the first banded rollout, the client-facing band labels should be:

### `portfolio_total_mass_score`

1. `low`: `Light Footprint`
2. `medium`: `Meaningful Footprint`
3. `high`: `Heavy Footprint`
4. `very_high`: `Outsize Footprint`

### `portfolio_current_threat_score`

1. `low`: `Low Pressure`
2. `medium`: `Moderate Pressure`
3. `high`: `High Pressure`
4. `very_high`: `Severe Pressure`

### `portfolio_heritage_score`

1. `low`: `Thin Heritage`
2. `medium`: `Established Heritage`
3. `high`: `Deep Heritage`
4. `very_high`: `Foundational Heritage`

### Future density / crown-jewel bands

Recommended names:

1. `portfolio_hit_rate_top_decile`
   - `Sparse`
   - `Selective`
   - `Broad`
   - `Dense`
2. `portfolio_crown_jewel_index`
   - `Limited Arsenal`
   - `Competitive Arsenal`
   - `Elite Arsenal`
   - `Dominant Arsenal`

Band thresholds should be percentile-based:

1. `0-25`: `low`
2. `25-50`: `medium`
3. `50-75`: `high`
4. `75-100`: `very_high`

This is a serving threshold policy, not a mathematical truth claim.

---

## Family Peer Classes

Families should not reuse the portfolio-size peer buckets.

A family is already the atomic asset, so the right peer logic is cohort-based rather than size-bucket-based.

### Current family peer logic

The live family blocking mart already provides:

1. `family_ui_blocking_power_score`

This score is already normalized within primary WIPO field cohorts after the blocking-power rebuild.

### Recommended family peer policy

Use different family cohorts depending on the metric family:

1. `blocking posture`
   - primary cohort: `primary WIPO field`
2. `citation influence / heritage`
   - primary cohort: `priority-year x primary WIPO field`
3. `OECD quality`
   - primary cohort: the OECD-defined family cohort already embedded in the indicator lineage
4. `legal durability`
   - primary cohort: field plus lifecycle stage where possible

Recommended family-facing band names:

1. blocking posture:
   - `Limited`
   - `Established`
   - `Strong`
   - `Leading`
2. legal durability:
   - `Fragile`
   - `Mixed`
   - `Durable`
   - `Highly Durable`
3. citation heritage:
   - `Thin`
   - `Established`
   - `Deep`
   - `Foundational`

Family bands should remain secondary to exact legal/status evidence and cohort percentile.

---

## How Peer Ranking Relates To CPC / WIPO / Jurisdiction Rankings

This is the main separation rule.

### Entity peer percentile answers:

`How strong is this entity relative to similar entities?`

Examples:

1. this portfolio is `82nd` percentile for blocking footprint within the `6-20 families` peer class,
2. this family is `91st` percentile for blocking posture within its field cohort.

### Market ranking answers:

`How important or heated is this market slice right now?`

Examples:

1. this CPC main group ranks `5th` in `2025`,
2. this WIPO x CPC x jurisdiction slice has `high` blocking density,
3. this segment is `heating` or `cooling`.

### Correlation rule

They correlate by overlay, not by denominator sharing.

That means:

1. a portfolio can have `High Pressure` within its peer bucket while also being concentrated in CPC groups that rank highly in the market,
2. a family can have `Leading` blocking posture while sitting in a cooling market slice,
3. a portfolio compare view can say `Outsize Footprint` and separately show that most of that footprint lives in `Computer technology / G06F3/00 / US`.

Do not compute one blended percentile that merges:

1. entity scale,
2. field heat,
3. CPC importance,
4. jurisdiction density.

That would destroy interpretability.

---

## Product Contract

For every banded portfolio metric, backend responses should eventually carry:

1. `raw_value`
2. `peer_percentile`
3. `band_code`
4. `band_label`
5. `peer_bucket`
6. `peer_bucket_label`

For future compare endpoints, portfolio-to-portfolio compare should expose:

1. `mass`
2. `density`
3. `crown_jewel`

Each lens should carry:

1. current raw value,
2. peer percentile,
3. band label,
4. a note when the compared portfolios belong to different peer buckets.

Family-to-family compare should expose:

1. `blocking_posture`
2. `legal_durability`
3. `citation_heritage`

Each family lens should carry:

1. current raw value,
2. cohort-relative percentile,
3. band label,
4. cohort label,
5. a note when the compared families belong to different cohorts and the response is band-first rather than strict-percentile-first.

---

## Immediate Execution Order

1. apply qualitative bands to current-serving portfolio overview metrics that are currently unbounded indices,
2. keep raw numbers visible as analyst evidence,
3. add peer-bucket percentile metadata to those card payloads,
4. then implement compare-lens ranking for `mass`, `density`, and `crown_jewel`,
5. implement family compare lenses using field-relative blocking, lifecycle-aware legal durability, and priority-year x field citation heritage,
6. only after that, add field-filtered compare overlays that reference CPC/WIPO/jurisdiction rankings.

# Portfolio Size Normalization And Crown Jewel Ranking Requirements

## Source

User-provided implementation guidance captured on March 8, 2026.

## Purpose

Define how PatentIQ should compare portfolios of very different sizes without letting either raw volume or small-sample averages produce misleading competitor rankings.

## Core Principle

Portfolio comparison must not rely on a single aggregate statistic.

Large portfolios and small portfolios create opposite distortions:
1. pure summed score over-rewards sheer volume,
2. pure mean or median over-rewards tiny portfolios with a few elite assets.

PatentIQ should therefore expose multiple complementary rollups:
1. total mass,
2. quality density,
3. crown-jewel strength.

## Why Naive Aggregation Fails

## PSN-01: Pure Sum Over-Rewards Volume

Requirement:
PatentIQ must not use the raw sum of family-level blocking or threat scores as the only portfolio ranking metric.

Why:
Very large portfolios can dominate by filing volume even when much of that inventory is strategically mediocre.

## PSN-02: Pure Average Over-Rewards Tiny Portfolios

Requirement:
PatentIQ must not use average or median family score as the only portfolio ranking metric.

Why:
Small portfolios with a handful of elite assets can look unrealistically dominant if size and depth are ignored.

## Crown Jewel Equalizer

## PSN-03: Portfolio Ranking Should Support A Crown Jewel Index

Requirement:
PatentIQ should support a size-agnostic top-tier comparison metric that focuses only on the strongest families in a portfolio.

## PSN-04: Crown Jewel Index Uses Top-N Or Top-Percent Families

Requirement:
The crown-jewel view should rank portfolios using only their best-performing assets in the selected field or cohort, for example:
1. top 10% of families,
2. top 10 families,
3. top 50 families,
4. top 100 families.

## PSN-05: Crown Jewel Index Should Sum Elite Family Scores

Requirement:
The crown-jewel metric should sum the relevant family-level scores of only the selected elite subset rather than averaging the whole portfolio.

Why:
This creates a fairer head-to-head view of the strongest comparable weapons each competitor brings into the field.

## Two-Dimensional Portfolio Comparison

## PSN-06: Portfolio Ranking Should Support A Size X Quality Matrix

Requirement:
The level-1 portfolio dashboard should support a two-dimensional competitor matrix with:
1. size or volume on one axis,
2. quality density on the other axis.

## PSN-07: Size Axis Uses Active Family Mass

Requirement:
The size axis should use a quantity such as:
1. total active families in the selected field,
2. total active field-weighted family mass,
3. or an equivalent family-first size metric.

## PSN-08: Quality Axis Uses Hit Rate Or Elite Density

Requirement:
The quality axis should use a density metric such as:
1. percent of active families above the 90th percentile,
2. OECD hit rate,
3. percent of families classified as elite by the chosen score family.

## PSN-09: The Matrix Should Segment Portfolio Archetypes

Requirement:
The product should support interpretations such as:
1. high size + low/medium density = giants,
2. low size + high density = snipers,
3. high size + high density = apex predators,
4. low size + low density = low-threat or low-relevance players.

## Geographic Volume Nuance

## PSN-10: Geographic Carpet-Bombing Should Not Be Mistaken For Smart Strength

Requirement:
Portfolio ranking logic should not automatically reward broad filing in many low-value jurisdictions as if it were equal to focused strength in high-value jurisdictions.

Why:
The underlying 4D family math already weights jurisdiction value and local trend, so smart targeted filings should remain competitive against blind geographic volume.

## Rollup Views For The Frontend

## PSN-11: Provide A Portfolio Total Mass View

Requirement:
PatentIQ should expose a `portfolio_total_mass` view or equivalent that sums relevant family scores for strict size and total strategic mass analysis.

## PSN-12: Provide A Portfolio Hit-Rate View

Requirement:
PatentIQ should expose a `portfolio_hit_rate` view or equivalent that measures the share of families above selected percentile thresholds.

## PSN-13: Provide A Portfolio Crown-Jewel View

Requirement:
PatentIQ should expose a `portfolio_crown_jewels` view or equivalent that sums only the top tier of assets to create a size-agnostic comparison.

## PSN-14: The UI Must Label These Views Clearly

Requirement:
The product should clearly distinguish whether the user is looking at:
1. total mass,
2. hit-rate density,
3. crown-jewel strength.

Why:
Each view answers a different strategic question.

## Relationship To Existing Notes

This note extends the portfolio-comparison logic around size, density, and elite-asset concentration.

### Overlaps With Existing Docs

1. `oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`
2. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
3. `global-vs-local-trend-role-allocation-requirements.md`
4. `march-2026-family-legal-analytics-master-index.md`

### Net-New Additions

1. explicit rejection of single-metric portfolio ranking,
2. crown-jewel index,
3. size-versus-quality portfolio matrix,
4. portfolio total mass / hit rate / crown-jewel frontend views,
5. portfolio archetype segmentation.

## Delivery Priority

### P0

1. `portfolio_total_mass` rollup,
2. `portfolio_hit_rate` rollup,
3. `portfolio_crown_jewels` rollup,
4. clear UI labeling of the three views.

### P1

1. size-versus-quality competitor matrix,
2. top-N and top-percent crown-jewel variants,
3. portfolio archetype labels and drill-downs.

### P2

1. more advanced efficiency metrics,
2. dynamic field-specific crown-jewel thresholds,
3. scenario benchmarking between startup and giant portfolios.

# PatentIQ V2 Portfolio Model Applicability Audit And Coverage Contract

## Goal

Record whether the sealed lower-level model artifacts are already usable for portfolio-level outputs and define the mandatory coverage fields that must travel with any portfolio-derived prediction.

This note does not define a new model.

It defines:

1. what is already applicable from sealed Phases `03`, `04`, and `06`
2. what the current coverage looks like on real portfolios
3. which coverage fields are required so portfolio outputs remain honest

## Audited Artifact

The current audit is saved at:

1. [portfolio_model_applicability_audit.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/portfolio_model_applicability_audit.json)

It evaluates the top `100` portfolios by current portfolio size.

## Main Conclusion

The sealed lower-level models are already portfolio-applicable, but only through explicit aggregation and explicit coverage disclosure.

Meaning:

1. `Phase 03` is applicable to portfolios through covered family-level citation outlook rows
2. `Phase 04` is applicable to portfolios through covered family-jurisdiction lapse-risk rows
3. `Phase 06` is applicable to current portfolio field exposure and market-direction overlays

They are not yet suitable for silent full-portfolio interpretation without coverage metadata.

## Current Audit Read

Across the top `100` portfolios:

1. average `Phase 03` family coverage is `0.570509`
2. average `Phase 04` family coverage is `0.491255`
3. current `Phase 06` field-mix support at `2026` is available for `100 / 100` audited portfolios

Coverage spread is meaningful:

1. minimum `Phase 03` family coverage in the top-100 sample is `0.194483`
2. minimum `Phase 04` family coverage in the top-100 sample is `0.093701`
3. lower-quartile coverage is:
   - `Phase 03`: `0.488545`
   - `Phase 04`: `0.374253`

So portfolio outputs are usable, but they are not equally complete across owners.

## Concrete Examples

Examples of low-coverage portfolios from the audit:

1. `PANASONIC_CORPORATION`
   - `Phase 03 coverage ≈ 0.238745`
   - `Phase 04 coverage ≈ 0.093701`
2. `SONY_CORPORATION`
   - `Phase 03 coverage ≈ 0.322563`
   - `Phase 04 coverage ≈ 0.215660`
3. `MICROSOFT_CORPORATION`
   - `Phase 03 coverage ≈ 0.357559`
   - `Phase 04 coverage ≈ 0.234080`

Examples of better-covered portfolios:

1. `ZTE_CORPORATION`
   - `Phase 03 coverage ≈ 0.815780`
   - `Phase 04 coverage ≈ 0.507523`
2. `QUALCOMM`
   - `Phase 03 coverage ≈ 0.634370`
   - `Phase 04 coverage ≈ 0.581302`
3. `BOE_TECHNOLOGY_GROUP_COMPANY`
   - `Phase 03 coverage ≈ 0.679693`
   - `Phase 04 coverage ≈ 0.681267`

This is exactly why coverage must be explicit in the contract.

## Required Coverage Fields

Any future portfolio-derived prediction mart or backend response must include:

1. `phase03_family_coverage_pct`
2. `phase03_family_covered_count`
3. `phase03_family_denominator_count`
4. `phase04_family_coverage_pct`
5. `phase04_family_covered_count`
6. `phase04_family_denominator_count`
7. `phase04_avg_scored_jurisdictions_per_covered_family`
8. `phase06_current_field_mix_supported`
9. `phase06_current_field_mix_support_reason`

Recommended additional fields:

1. `portfolio_prediction_coverage_status`
   - `high`
   - `medium`
   - `low`
2. `coverage_caveat_text`
3. `prediction_scope_status`

## Why These Fields Are Required

Without them, portfolio outputs can look like complete portfolio truth even when they are only computed on a subset.

The fields are necessary to answer:

1. how much of the portfolio is actually represented
2. whether two portfolio outputs are fairly comparable
3. whether the UI should downgrade or suppress an aggregate
4. whether the report language should be restrained

## Initial Coverage-Status Policy

First-pass recommendation:

1. `high`
   - coverage `>= 0.75`
2. `medium`
   - coverage `>= 0.50` and `< 0.75`
3. `low`
   - coverage `< 0.50`

For combined portfolio prediction surfaces:

1. use the weaker of `Phase 03` and `Phase 04` coverage status as the overall prediction coverage label
2. do not silently average them into one optimistic number

## Phase 06 Boundary

Current `Phase 06` support is narrower than `Phase 03` and `Phase 04`.

What is safe now:

1. current portfolio exposure to `heating / stable / cooling` segment directions
2. current-year field-mix overlays where [gold_portfolio_compare_pit.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_compare_pit.parquet) marks `historical_field_mix_supported = true`

What is not yet safe:

1. treating Phase 06 as a full historical portfolio trend-replay authority across all years

So the required field now is:

1. `phase06_current_field_mix_supported`

not a misleading all-years support claim.

## Backend Rules

Portfolio-derived prediction endpoints must:

1. return coverage fields alongside every aggregate
2. expose the denominator explicitly
3. expose a human-readable caveat string when coverage is `medium` or `low`
4. avoid returning a confidence-heavy summary without the coverage context

## UI Rules

Portfolio and forecast UIs must:

1. show coverage status near the aggregate headline
2. downgrade emphasis for `low` coverage aggregates
3. avoid portfolio-to-portfolio ranking without visible coverage context
4. keep Phase 06 current-year support caveats visible when market-direction overlays are shown

## Bottom Line

The sealed model stack is already useful for portfolio derivation.

But the correct product rule is:

1. `aggregate`
2. `disclose coverage`
3. `only then interpret`

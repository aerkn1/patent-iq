# PatentIQ V2 Phase 04 Seal Decision And Serving Contract

## Goal

Record the explicit decision for the current `Phase 04` family-jurisdiction lapse-risk artifacts so backend and UI can consume them consistently without overstating subgroup reliability.

This note seals the current artifacts as:

1. `accepted MVP candidate release`
2. `usable for backend and product wiring`
3. `not yet fully promoted production across all office subgroups`

## Decision

Phase 04 is accepted as a sealed candidate release for MVP and demo use.

Decision label:

1. `sealed_candidate_accepted_for_mvp`

This is not the same as:

1. `fully promoted production`

## Why The Decision Is Acceptable

The current live artifact set satisfies the hard requirements that matter most for MVP:

1. branch-level labels are built from legal event and dense branch-history sources
2. grouped time splits prevent family-jurisdiction trajectory leakage
3. `12m` and `24m` baselines train successfully on the live corpus
4. validation selected calibrated probability outputs per horizon
5. larger held-out reliability audit confirms strong overall discrimination and sensible year behavior

## Current Accepted Metrics

Held-out reliability audit from [family_jurisdiction_lapse_risk_reliability_audit.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_reliability_audit.json):

1. `12m ROC AUC ≈ 0.984`
2. `12m PR AUC ≈ 0.113`
3. `12m Brier ≈ 0.0028`
4. `24m ROC AUC ≈ 0.970`
5. `24m PR AUC ≈ 0.105`
6. `24m Brier ≈ 0.0052`

These are strong enough to support:

1. family-jurisdiction lapse prioritization
2. portfolio coverage-attrition rollups
3. report evidence blocks
4. MVP backend and UI contract design

## Why It Is Not Fully Promoted Production

The remaining blocker is subgroup reliability by `jurisdiction_code`.

Current live audit shows:

1. `JP` is reasonably aligned on both horizons
2. `US` is usable, but `24m` is materially overpredicted
3. `CN`, `KR`, `EP`, `DE`, `ES`, and `TW` have near-zero positive rates in the held-out audit slice, so calibration quality is not strongly proven there

So the strict production interpretation gate is still not satisfied for universal office-level probability claims.

## Accepted Caveats

These caveats must travel with the sealed Phase 04 release:

1. treat the models as `accepted candidate`, not final production authority
2. use the outputs primarily as `ranking + risk banding` across all offices
3. expose exact calibrated probabilities only with explicit subgroup support metadata
4. do not claim uniform office-level calibration
5. do not use the current artifact as the sole basis for irreversible renewal or abandonment automation

## Office Reliability Policy

The serving contract should classify office support explicitly.

### `strong`

1. `JP`

Meaning:

1. probability may be shown
2. risk band may be shown
3. no extra downgrade beyond standard caveats

### `moderate`

1. `US`

Meaning:

1. probability may be shown
2. risk band should be the primary visual emphasis
3. `24m` should carry a calibration caveat

### `limited`

1. `CN`
2. `KR`
3. `EP`
4. `DE`
5. `ES`
6. `TW`
7. all other sparse or unsupported offices

Meaning:

1. risk band may be shown
2. percentile or rank may be shown
3. exact calibrated probability should be hidden or visually downgraded
4. UI must say calibration support is limited for this office cohort

## Backend Serving Rules

The backend should return a horizon-explicit lapse-risk response with:

1. `prediction_unit`
2. `docdb_family_id`
3. `jurisdiction_code`
4. `as_of_date`
5. `horizon`
6. `risk_score_raw`
7. `risk_probability_calibrated`
8. `risk_band`
9. `risk_percentile`
10. `office_support_level`
11. `probability_display_allowed`
12. `support_reason`
13. `feature_completeness`
14. `model_version`
15. `calibration_method`
16. `caveats`

### Risk-band-first rule

All offices should receive:

1. rankable score
2. percentile
3. `low / medium / high` band

Only supported offices should receive first-class probability treatment.

### Portfolio aggregation rule

Portfolio services may aggregate:

1. expected lapse counts
2. high-risk branch counts
3. jurisdiction risk concentration
4. top lapse-risk contributors

But the response must include:

1. support coverage by office
2. share of rows with `limited` support
3. caveat metadata when the portfolio is dominated by sparse offices

## UI Rules

### Family / legal section

Use the lapse model as a legal-risk overlay, not as an isolated numeric widget.

Show:

1. `12m / 24m` horizon switch
2. risk band chip
3. percentile
4. calibrated probability only when `probability_display_allowed = true`
5. office support badge:
   - `strong`
   - `moderate`
   - `limited`
6. caveat copy in the legal context drawer

### Portfolio pages

Show:

1. high-risk branch count
2. risk-band distribution
3. top risky jurisdictions
4. top risky families
5. support coverage summary

Do not:

1. imply that all office probabilities are equally calibrated
2. let a single raw probability dominate the visual story

### Copy rules

Preferred language:

1. `lapse risk`
2. `coverage attrition risk`
3. `risk band`
4. `calibration support`

Avoid:

1. `will lapse`
2. `guaranteed renewal failure`
3. `office-precise probability` without support labeling

## Artifact Set Covered By This Decision

The sealed candidate decision covers:

1. [family_jurisdiction_lapse_risk_12m_model.txt](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_12m_model.txt)
2. [family_jurisdiction_lapse_risk_24m_model.txt](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_24m_model.txt)
3. [family_jurisdiction_lapse_risk_calibration.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_calibration.json)
4. [family_jurisdiction_lapse_risk_reliability_audit.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_reliability_audit.json)
5. [model_card_family_jurisdiction_lapse_risk.json](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_jurisdiction_lapse_risk.json)
6. [ml_model_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet)
7. [ml_experiment_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet)
8. [ml_calibration_registry.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet)

## What Happens Next

Because Phase 04 is now sealed for MVP, the next work should be:

1. use these outputs in backend V2 contracts as `risk-band-first`
2. carry `office_support_level` and probability-display flags into UI contracts
3. revisit office-aware recalibration later if final production promotion requires it
4. continue with later modeling phases without blocking on Phase 04 perfection

## Bottom Line

The correct project label for Phase 04 is:

1. `sealed candidate`
2. `accepted for MVP`
3. `ranking and banding reliable overall`
4. `not yet universal office-level production probability authority`

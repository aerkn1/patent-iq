# Predictive Signals And Interpretable Forecasting Requirements

## Source

User-provided implementation guidance captured on March 9, 2026.

## Purpose

Define how PatentIQ should extend the platform from descriptive and diagnostic analytics into predictive analytics using interpretable statistical models rather than unverifiable black-box forecasting.

## Core Principle

PatentIQ should treat the predictive layer as:
1. bounded-probability forecasting,
2. explicitly separated from current-state metrics,
3. interpretable,
4. statistically defensible,
5. fast at query time because heavy training runs offline.

The platform should avoid opaque “AI says so” forecasting and instead rely on:
1. gradient-boosted tabular models with explainability,
2. survival analysis,
3. interpretable anomaly/risk classifiers,
4. bounded time-series forecasting.

## Predictive Use Cases

## PSF-01: Grant Probability Score

Requirement:
PatentIQ should support a grant-probability forecast for pending application-stage assets so users can estimate how much of a shadow portfolio is likely to convert into enforceable rights.

## PSF-02: Lapse / Abandonment Risk

Requirement:
PatentIQ should support a lapse-risk or abandonment-risk forecast estimating whether currently active granted families are likely to be abandoned or allowed to lapse in future renewal windows.

## PSF-03: Opposition / Friction Target Risk

Requirement:
PatentIQ should support a predictive signal estimating the probability that a newly granted family will attract opposition, post-grant review, or equivalent friction events.

## PSF-04: Tech Trend Momentum Forecast

Requirement:
PatentIQ should support bounded short-horizon forecasting for technology-field and jurisdiction trend momentum so users can see emerging future hotspots.

## Execution Grain Rules

## PSF-05: Predictions Must Be Executed At The Lowest Defensible Grain

Requirement:
PatentIQ should calculate forecasts at the lowest defensible micro-level and only aggregate them upward for portfolio or company views.

Rationale:
1. portfolios are heterogeneous collections of assets across different jurisdictions, ages, and technology fields,
2. monolithic portfolio-level prediction destroys the legal and market localization needed for trustworthy forecasting,
3. bottom-up execution preserves drill-down from dashboard warning to exact family, jurisdiction, or publication driver.

## PSF-06: Grant Probability Runs At Publication Or Sub-Family Grain

Requirement:
Grant-probability forecasts should be executed at the pending publication, application, or sub-family grain and only then aggregated upward for assignee or portfolio views.

Operational rule:
1. jurisdiction is mandatory because office behavior differs materially,
2. technology field is mandatory because grant behavior differs by field,
3. portfolio-level pending-threat counts should be sums or distributions of these micro-level grant probabilities rather than direct portfolio-classifier outputs.

## PSF-07: Lapse Risk Runs At The Family-Jurisdiction Intersection

Requirement:
Lapse and abandonment-risk forecasting should be executed at the family-by-jurisdiction intersection because renewal decisions are local legal and economic choices.

Operational rule:
1. upcoming fee windows must be evaluated by office-specific schedules,
2. local tech-trend context must be evaluated in the same jurisdiction,
3. portfolio-level lapse-risk views should aggregate these branch-level hazards into counts, expected losses, or weighted risk shares.

## PSF-08: Friction Risk Runs At Family Grain With Jurisdiction-Aware Inputs

Requirement:
Opposition, review, or litigation-target risk should be forecast at family level while still using jurisdiction-aware collision features from the citing-side network.

Operational rule:
1. family is the correct attack target abstraction for the UI,
2. jurisdiction remains critical because friction is filed in specific legal venues,
3. portfolio-level friction dashboards should roll up family-level forecasts into exposure summaries rather than predicting a portfolio as one object.

## PSF-09: Trend Momentum Forecast Runs At Jurisdiction-By-Field Grain

Requirement:
Technology momentum forecasting should run at the jurisdiction-by-field grain and should not be trained on families or portfolios directly.

Operational rule:
1. the model predicts the macro environment, not asset behavior,
2. family and portfolio dashboards should consume these forecasts as overlays by comparing current coverage against projected hotspots,
3. this is the only forecast class where the base entity is the market slice rather than the family.

## Modeling Rules

## PSF-10: Use Interpretable Tabular Models For Grant Probability

Requirement:
Grant-probability forecasting should use interpretable tabular classification models such as:
1. LightGBM,
2. XGBoost,
3. or equivalent explainable gradient-boosted models.

## PSF-11: Use Survival Analysis For Lapse Risk

Requirement:
Lapse-risk forecasting should use time-to-event models such as:
1. Cox proportional hazards,
2. random survival forests,
3. or equivalent survival-analysis methods.

## PSF-12: Use Imbalance-Aware Models For Friction Risk

Requirement:
Opposition or litigation-target forecasting should use models that explicitly handle rare-event imbalance, such as:
1. LightGBM with focal-loss-style handling,
2. anomaly-detection support,
3. precision-recall-driven evaluation.

## PSF-13: Use Bounded Time-Series Models For Trend Forecasting

Requirement:
Trend forecasting should use interpretable time-series models such as:
1. ARIMA,
2. Prophet,
3. or equivalent bounded forecasting methods.

## Feature Tables

## PSF-14: Grant Probability Feature Set

Recommended feature families:
1. assignee historical grant rate,
2. assignee portfolio size,
3. jurisdiction or office,
4. WIPO field grant rate,
5. claim count,
6. family size,
7. months since filing.

## PSF-15: Lapse-Risk Feature Set

Recommended feature families:
1. maintenance-fee schedule or renewal milestone,
2. current blocking power,
3. generality score,
4. forward citation velocity,
5. age of the family,
6. local tech trend.

## PSF-16: Friction-Risk Feature Set

Recommended feature families:
1. forward citation velocity in the early post-grant window,
2. citing-assignee concentration or HHI,
3. generality,
4. radicalness,
5. current market-threat posture,
6. attacker-leaderboard density.

## PSF-17: Trend-Forecast Feature Set

Recommended feature families:
1. historical local or global filing velocity,
2. multi-year acceleration,
3. optional macro exogenous variables where available,
4. field plus jurisdiction anchors.

## Guardrails

## PSF-18: Predictive Outputs Must Be Clearly Labeled As Forecasts

Requirement:
Forecast outputs must be visually and semantically separated from current-state reality.

## PSF-19: Portfolio Forecast Views Must Aggregate Micro-Level Predictions

Requirement:
Portfolio- or assignee-level forecast views must be built by aggregating scored micro-level predictions rather than by treating the entire portfolio as a single prediction object.

Examples:
1. expected likely grants should aggregate pending publication-level probabilities,
2. expected lapse exposure should aggregate family-jurisdiction survival outputs,
3. high-friction exposure should aggregate family-level friction forecasts,
4. hotspot mismatch should compare portfolio coverage against jurisdiction-field trend forecasts.

## PSF-20: Predictive Outputs Must Preserve Drill-Down Traceability

Requirement:
Every portfolio-level predictive KPI should be decomposable back to the exact micro-level scored rows that produced it.

Examples:
1. a portfolio abandonment-risk warning should open the exact family-jurisdiction branches driving the forecast,
2. a pending-threat count should open the pending publications driving the total,
3. a high-friction warning should open the exact families and legal venues causing the risk.

## PSF-21: Grant Models Must Avoid Right-Censoring Leakage

Requirement:
Grant-probability training data must exclude post-outcome information that would leak future grant knowledge into the model.

## PSF-22: Probabilities Must Be Calibrated

Requirement:
Any model output shown as a probability should be calibrated using methods such as:
1. isotonic regression,
2. Platt scaling,
3. or equivalent probability-calibration methods.

## PSF-23: Lapse Models Must Be Jurisdiction-Specific

Requirement:
Survival curves or hazard models for lapse risk must be trained separately where renewal regimes differ materially by jurisdiction.

## PSF-24: Friction Models Must Be Evaluated With Rare-Event Metrics

Requirement:
Opposition and litigation-target models should prioritize metrics such as precision-recall AUC rather than relying only on accuracy or ROC-AUC.

## PSF-25: Trend Forecast Horizons Must Be Bounded

Requirement:
Technology trend forecasts should be limited to a short defensible horizon such as 3 to 5 years.

## PSF-26: Forecasted Filing Counts Must Respect Non-Negativity

Requirement:
Trend-forecast models must use appropriate constraints or transforms so they do not predict negative filing volumes.

## Architecture Pattern

## PSF-27: Heavy Training Runs Offline

Requirement:
Model training and batch scoring should run offline in Python or equivalent data science pipelines rather than during UI requests.

## PSF-28: DuckDB Silver Layer Stores Deterministic Forecast Outputs

Requirement:
The predictive layer should persist scored outputs into silver-layer forecast tables rather than requiring live heavy inference for every UI request.

## PSF-29: Predictive Tables Should Be Joinable To Existing Marts

Requirement:
Each forecast table should be keyed so it can join directly into the family-first legal, citation, trend, and assignee marts already planned.

## PSF-30: Predictive Tables Must Preserve Their Native Execution Grain

Requirement:
Forecast tables should preserve the native scoring grain of the model rather than prematurely flattening all forecasts to one portfolio table.

Recommended pattern:
1. grant forecasts store publication, application, or sub-family keys,
2. lapse forecasts store family plus jurisdiction keys,
3. friction forecasts store family keys with jurisdictional evidence references,
4. trend forecasts store jurisdiction plus field plus forecast horizon keys.

## Recommended Silver Tables

## PSF-31: Grant Probability Table

Recommended table:
`silver_grant_probability_forecast`

## PSF-32: Survival / Lapse Hazard Table

Recommended table:
`silver_survival_hazards`

## PSF-33: Friction Forecast Table

Recommended table:
`silver_friction_forecast`

## PSF-34: Forecast Flagging In Trend Tables

Requirement:
Future trend forecasts may be appended to existing trend tables if they carry explicit forecast markers such as:
1. `is_forecast`,
2. confidence interval fields,
3. method version.

## UX Requirements

## PSF-35: Forecast Visuals Must Distinguish Actuals From Forecasts

Requirement:
Trend charts should render actuals and forecasts differently, for example:
1. solid line for actuals,
2. dotted line for forecast,
3. shaded band for confidence interval.

## PSF-36: Forecast Cards Must Explain The Driver Set

Requirement:
For interpretable forecast cards, the product should surface top drivers or model explanations rather than only the score.

## PSF-37: Predictive Signals Must Not Override Current Legal Truth

Requirement:
Forecasts should augment decision support but must not replace current legal status, current blocking power, or current breadth metrics.

## EP Register Predictive Extension

## PSF-38: PATSTAT Register May Feed An Isolated EP-Special Grant Model

Requirement:
PATSTAT Register procedural tables may be used to improve EP grant forecasting, but only inside a separately versioned EP-special grant model.

Allowed feature families:
1. search-report milestones,
2. procedural phase codes,
3. procedural result codes,
4. explicit time-limit and prosecution-maturity signals.

## PSF-39: Register Features Must Not Leak Into Global Ranking Math

Requirement:
Register-derived predictive features must not be used to:
1. alter global blocking-power percentiles,
2. alter cross-office portfolio percentile rankings,
3. improve EP legal scoring in a way that has no comparable non-EP source.

Allowed exception:
EP-special grant predictions may be rolled up into portfolio pending-threat totals only after they are scored at native EP publication or branch grain and labeled as forecast outputs.

## Relationship To Existing Notes

This note adds a predictive layer on top of the deterministic analytics stack.

### Overlaps With Existing Docs

1. `docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md`
2. `docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md`
3. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
4. `parallel-global-and-local-trend-engines-requirements.md`
5. `citation-event-ledger-and-attacker-leaderboard-requirements.md`

### Net-New Additions

1. grant probability forecasting,
2. lapse-risk survival analysis,
3. friction / opposition target forecasting,
4. short-horizon trend forecasting,
5. predictive silver-layer table contracts and guardrails.

## Delivery Priority

### P0

1. define predictive tables and method boundaries,
2. keep forecasts separate from current-state truth,
3. calibrate probability outputs,
4. enforce forecast-horizon and non-negativity guardrails.

### P1

1. grant probability engine,
2. lapse-risk survival engine,
3. friction-risk engine,
4. trend-forecast overlays.

### P2

1. richer forecast explainability,
2. dynamic scenario testing,
3. more advanced benchmark and validation layers.

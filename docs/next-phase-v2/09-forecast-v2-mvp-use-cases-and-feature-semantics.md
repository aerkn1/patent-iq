# Forecast V2 MVP Use Cases And Feature Semantics

## Purpose

Define exactly how the successful V2 citation forecast model should behave inside the MVP at patent/family level and portfolio level, with explicit semantics for all major feature groups and especially for filing-rate context.

## Core Modeling Principle

The V2 model should not pretend that a single patent has macro behavior such as a standalone filing rate. Instead, it should attach each patent or family to the correct surrounding context and use that context as predictive signal.

That means:

1. A patent/family prediction uses local context around the asset.
2. A portfolio prediction uses both asset-level signals and portfolio-level momentum structure.
3. Filing-rate features are contextual slice features, not synthetic per-patent rates.

## Canonical Prediction Unit

### Preferred V2 unit

`docdb_family_id`

### Why

1. It matches V2 family-first analytics.
2. It reduces duplicate representations of the same invention.
3. It aligns model outputs with the product views used in ranking, trend, and comparison surfaces.

### UI behavior

1. User may search by publication or `appln_id`.
2. Backend resolves the patent into its canonical family.
3. Forecast is shown as family-level future citation expectation unless the product explicitly labels an application-level fallback.

## Prediction Horizons

### 3-year horizon

Use for:
1. early-signal detection,
2. hidden-gem discovery,
3. near-term portfolio prioritization,
4. fast-moving technology monitoring.

### 5-year horizon

Use for:
1. long-term strategic impact,
2. portfolio durability analysis,
3. acquisition and partner screening,
4. family-ranking context.

## As-Of Logic

### Recommended rule

Keep a leakage-safe `as_of_date` definition, but make it explicit and versioned in metadata.

Base rule:
1. all features must be observable at or before `as_of_date`,
2. all targets must occur strictly after `as_of_date`,
3. any trend or market features must be frozen to the same as-of boundary.

### V2 metadata fields

1. `model_version`
2. `feature_manifest_version`
3. `prediction_unit`
4. `as_of_definition`
5. `family_model`
6. `training_snapshot`
7. `calibration_version`
8. `data_completeness_pct`

## Patent Or Family MVP Use Case

### User goal

Understand whether a patent family is likely to gain meaningful future citation impact and why.

### Step-by-step flow

1. User opens a patent page.
2. System validates the user input and resolves it to a canonical family.
3. System loads:
   - patent core context,
   - family context,
   - legal context,
   - citation history context,
   - assignee context,
   - technology and market context,
   - OECD quality context.
4. System selects the requested model horizon (`3y` or `5y`).
5. System materializes the V2 feature vector from the feature mart.
6. System checks feature availability and missingness.
7. System computes the point prediction.
8. System computes interval estimates using the selected calibration method.
9. System computes explanation outputs:
   - top positive drivers,
   - top negative drivers,
   - feature completeness,
   - caveat metadata.
10. System returns the forecast response.
11. UI renders the response next to family, trend, and quality panels.
12. User can inspect the reasoning and drill into supporting analytics.

### Patent/family response should answer

1. How many future citations are expected?
2. What is the uncertainty?
3. Is this prediction relatively easy or hard?
4. Which factors are pushing the prediction up or down?
5. Is the patent/family sitting in a growing or saturated domain?
6. Are there caveats due to missing data or recent cohorts?

## Portfolio MVP Use Case

### User goal

Understand which families drive future portfolio influence and where that future influence is concentrated across technology, market, and ownership structure.

### Step-by-step flow

1. User opens a portfolio page.
2. System retrieves the canonical family set or patent set mapped to the selected owner.
3. System harmonizes the assignee and owner structure.
4. System determines the effective ownership weight for each forecasted asset if co-assignment exists.
5. System retrieves V2 feature vectors for every eligible asset.
6. System runs batch inference for all assets.
7. System computes:
   - asset-level expected future citations,
   - asset-level intervals,
   - asset-level explanation summaries.
8. System aggregates asset-level predictions into portfolio-level totals.
9. System derives portfolio-level views:
   - total expected future citations,
   - expected citations per effective family,
   - top contributors,
   - difficulty mix,
   - concentration by CPC/cluster/market/jurisdiction,
   - growth exposure.
10. System assembles portfolio-level caveats and completeness metadata.
11. UI renders portfolio forecast cards and drill-down views.
12. User identifies high-upside families and concentrated risk areas.

### Portfolio response should answer

1. What is the total expected future influence of this portfolio?
2. Which families contribute most?
3. Is future upside concentrated or diversified?
4. Which tech or market slices explain the upside?
5. Is the portfolio exposed to segments with rising or falling filing/grant momentum?
6. Are some forecasts weaker due to sparse data or recent cohorts?

## Portfolio Aggregation Contract

### Core rule

Portfolio prediction in V2 must be a bottom-up aggregation layer built from:

1. family-level forecasts,
2. publication or pending-branch grant forecasts,
3. family x jurisdiction lapse forecasts,
4. family-level friction forecasts,
5. jurisdiction x field trend forecasts.

The product must not present a portfolio forecast as if it came from one monolithic direct company model unless such a model is explicitly introduced and independently validated later.

### Why

A portfolio is a heterogeneous basket of:

1. different families,
2. different jurisdictions,
3. different legal stages,
4. different technology slices,
5. different confidence levels.

Direct top-level portfolio modeling would hide this structure and weaken explainability.

### Derived portfolio forecast metrics

#### Future citation outlook

Derived from:
1. family-level future citation forecasts

Recommended outputs:
1. `portfolio_expected_future_citations_total`
2. `portfolio_expected_future_citations_per_effective_family`
3. `portfolio_future_citation_interval_low`
4. `portfolio_future_citation_interval_high`
5. `portfolio_top_contributor_dependence_pct`
6. `portfolio_future_impact_concentration_hhi`

#### Pending grant pipeline

Derived from:
1. publication or branch-level grant probabilities

Recommended outputs:
1. `portfolio_pending_pipeline_percentile`
2. `portfolio_pending_pipeline_rank_within_peer_set`
3. `portfolio_top_pending_branch_shortlist`
4. `portfolio_pending_pipeline_priority_tier`

Only after the lower-level pending-grant model is sealed:
1. `portfolio_expected_likely_grants_count`
2. `portfolio_expected_likely_grants_by_jurisdiction`
3. `portfolio_expected_likely_grants_by_field`
4. `portfolio_grant_pipeline_density`

#### Coverage attrition outlook

Derived from:
1. family x jurisdiction lapse-risk forecasts

Recommended outputs:
1. `portfolio_expected_lapses_count_12m`
2. `portfolio_expected_lapses_count_24m`
3. `portfolio_expected_weighted_reach_loss_12m`
4. `portfolio_expected_weighted_reach_loss_24m`
5. `portfolio_expected_active_jurisdiction_loss`

#### Friction exposure

Derived from:
1. family-level friction-risk forecasts

Recommended outputs:
1. `portfolio_high_friction_family_count`
2. `portfolio_high_friction_family_share`
3. `portfolio_friction_risk_weighted_mass`
4. `portfolio_top_friction_field`

#### Hotspot and trend exposure

Derived from:
1. jurisdiction x field trend forecasts
2. current portfolio field-jurisdiction footprint

Recommended outputs:
1. `portfolio_hotspot_gap_count`
2. `portfolio_hotspot_coverage_pct`
3. `portfolio_emerging_market_exposure_score`
4. `portfolio_cooling_market_exposure_score`

### Portfolio confidence and caveat semantics

Required metadata:
1. `prediction_unit = family_bottom_up`
2. `portfolio_effective_family_count`
3. `portfolio_effective_pending_branch_count`
4. `portfolio_feature_completeness_pct`
5. `portfolio_prediction_confidence_band`
6. `portfolio_top_contributor_dependence_pct`
7. `portfolio_sparse_segment_flags`

Interpretation rules:
1. portfolio certainty should decrease when a large share of predicted value is concentrated in a few families,
2. portfolio certainty should decrease when many underlying assets are in sparse cohorts or unsupported slices,
3. portfolio uncertainty should not be summarized by a naive average of family confidence scores.

### Portfolio aggregation guardrails

1. never mix family and application units silently in one portfolio KPI,
2. never sum uncalibrated probabilities for executive-facing expected counts,
3. never assume family predictions are statistically independent when presenting narrow interval bands,
4. never hide concentration risk when one or two families dominate the forecast,
5. never present unsupported jurisdictions or fields as if they were fully modeled,
6. ownership weights must be applied before aggregation when co-assignment exists,
7. segment rollups must be suppressed if the subgroup sample is too sparse or flagged unreliable,
8. pending-grant candidate outputs should be rank/percentile-first until the lower-level model is sealed,
9. raw pending-grant probabilities should never be the headline portfolio KPI while the model remains candidate-only.

### Portfolio drill-down contract

The portfolio layer must remain explorable in this order:

1. portfolio KPI,
2. segment or jurisdiction/field rollup,
3. family contributor list,
4. underlying branch or pending publication evidence.

## Feature Semantics By Section

## Section A: Citation History Features

### What they represent

Signals of observed technical uptake before the prediction window begins.

### Examples

1. total forward citations before `as_of_date`,
2. citations in year 1, year 2, year 3 after filing,
3. citation velocity,
4. citation acceleration,
5. unique citing families,
6. unique citing assignees,
7. external citation share,
8. self-citation share,
9. intra-family-excluded citation count.

### Patent/family semantics

These features describe how the focal family is already being noticed.

### Portfolio semantics

Aggregated versions describe whether the portfolio’s future upside comes from:

1. a few already-hot families,
2. a broad base of moderate momentum,
3. a pipeline of low-observed but structurally promising assets.

## Section B: Family Structure Features

### What they represent

Signals of invention breadth, geographic intent, and structural maturity.

### Examples

1. family member count,
2. jurisdiction count,
3. family grant coverage,
4. ratio of granted to pending members,
5. family CPC breadth,
6. family CPC entropy,
7. family age,
8. time from earliest priority to first grant.

### Patent/family semantics

These features help separate:

1. narrow local filings,
2. broad commercially defended families,
3. immature families still early in prosecution.

### Portfolio semantics

Portfolio rollups show whether predicted future influence is concentrated in:

1. broad global families,
2. narrow local bets,
3. recently expanded families,
4. mature globally defended assets.

## Section C: Legal Durability Features

### What they represent

Signals of whether the owner is maintaining and defending the family.

### Examples

1. active/lapsed/expired member counts,
2. jurisdiction-level active share,
3. renewal continuity,
4. major-office grant breadth,
5. grant lag,
6. opposition resilience,
7. litigation or challenge flags when available.

### Patent/family semantics

These features indicate whether the family is:

1. still strategically maintained,
2. broadly granted,
3. weakly maintained,
4. already partially abandoned.

### Portfolio semantics

These features help identify whether future expected influence is backed by maintained legal positions or sits in decaying assets.

## Section D: Technology Features

### What they represent

Signals of technical domain breadth, focus, adjacency, and local competitive density.

### Examples

1. CPC section,
2. CPC subclass count,
3. CPC entropy,
4. dominant CPC shares,
5. adjacency to related CPC clusters,
6. cluster density,
7. crowding score,
8. whitespace or saturation score if available.

### Patent/family semantics

These features help the model infer whether the family is:

1. in a central, highly active field,
2. in a narrow niche,
3. in an interdisciplinary area,
4. in a rising adjacent cluster.

### Portfolio semantics

These features show where predicted upside is concentrated across the owner’s technology footprint.

## Section E: Filing-Rate And Grant-Rate Context

### Important rule

Filing-rate and grant-rate features are contextual, not intrinsic to a single patent.

### What this means

For a patent/family:
1. do not create a fake “patent filing rate”,
2. instead attach the family to the surrounding filing and grant environment.

For a portfolio:
1. portfolio-level filing rates are real,
2. because the portfolio itself has a time series of filings and grants.

### Patent/family contextual filing-rate features

These are valid:

1. filing growth in the same CPC slice,
2. filing growth in the same tech cluster,
3. filing growth in the same market/jurisdiction slice,
4. grant-rate trend in the same slice,
5. filing momentum of the owning assignee in the same slice,
6. filing momentum of peer assignees in the same slice,
7. family expansion rate across jurisdictions,
8. recent growth or slowdown of the family’s surrounding market-tech cohort.

### Patent/family contextual grant-rate features

These are valid:

1. grant rate of the same tech-market cohort,
2. owner-specific grant conversion in the same slice,
3. pendency-adjusted grant environment,
4. maturity of the family versus peers in the same cohort.

### Portfolio-level filing-rate features

These are valid direct portfolio features:

1. yearly family filing counts,
2. filing momentum over rolling windows,
3. CPC share evolution,
4. market/jurisdiction filing mix evolution,
5. granted-vs-pending trend,
6. filing concentration across clusters,
7. family growth in target segments,
8. owner filing acceleration or deceleration.

### Portfolio-level grant-rate features

These are valid direct portfolio features:

1. pendency-adjusted grant rate,
2. grant-rate by CPC,
3. grant-rate by market/jurisdiction,
4. grant-rate by family cohort,
5. trend of conversion from pending to granted.

### Why these features matter

They tell the model whether the focal asset sits in:

1. a fast-growing field,
2. a slowing field,
3. an owner expansion phase,
4. a crowded and mature domain,
5. a strong grant-conversion environment,
6. a weak or delayed prosecution environment.

## Section F: Market Context Features

### What they represent

Signals of how the relevant market-tech slice is evolving beyond the focal patent itself.

### Examples

1. slice filing growth,
2. slice grant growth,
3. peer assignee count,
4. concentration of top assignees,
5. citation intensity of the slice,
6. cluster saturation,
7. region-specific expansion patterns.

### Patent/family semantics

These features describe the environment in which the family competes.

### Portfolio semantics

These features describe whether the owner’s future upside is aligned with expanding or declining market-tech zones.

## Section G: Assignee And Ownership Features

### What they represent

Signals tied to the behavior and scale of the owner behind the asset.

### Examples

1. harmonized assignee identifier,
2. parent-group membership,
3. assignee portfolio size,
4. assignee filing momentum in the same slice,
5. assignee grant-rate in the same slice,
6. co-assignment complexity,
7. assignee concentration by cluster.

### Patent/family semantics

These features let the model use the owner’s context without leaking future outcomes.

### Portfolio semantics

At portfolio level, these features inform concentration, diversification, and strategic intensity.

## Section H: OECD Quality Features

### What they represent

Cohort-normalized structural quality context.

### Examples

1. normalized `family_size`,
2. normalized `grant_lag`,
3. normalized `bwd_cits`,
4. normalized `npl_cits`,
5. normalized `claims`,
6. normalized `generality`,
7. normalized `originality`,
8. normalized `radicalness`,
9. optional explainable composites.

### Usage rule

These should not be used as raw cross-cohort features without normalization.

### Patent/family semantics

They help distinguish whether the family is unusually strong for its filing year and tech field.

### Portfolio semantics

They help show whether future expected impact is concentrated in above-cohort or below-cohort quality families.

## Section I: Completeness And Reliability Features

### What they represent

Signals that help the model and the product reason about data quality and temporal bias.

### Examples

1. lag-warning flags,
2. data completeness percentage,
3. missing feature counts,
4. office availability flags,
5. cohort sample size,
6. field-overlap indicator such as `many_field`.

### Why they matter

1. They reduce silent trust failures.
2. They support calibration and caveat generation.
3. They help the UI label weaker predictions appropriately.

## Detailed Patent Or Family Inference Steps

1. Resolve the requested patent to canonical family.
2. Check eligibility for selected horizon.
3. Load frozen V2 feature row at the selected `as_of_date`.
4. Validate schema version and feature completeness.
5. Apply preprocessing:
   - type casting,
   - null handling,
   - categorical encoding,
   - normalization lookups.
6. Run model inference.
7. Run calibration layer.
8. Compute explanation layer.
9. Compute caveat layer:
   - missing features,
   - recent cohort warnings,
   - office-specific limitations.
10. Assemble response contract.
11. Render:
   - expected future citations,
   - uncertainty,
   - drivers,
   - context signals,
   - evidence and caveats.

## Detailed Portfolio Inference Steps

1. Resolve selected owner to harmonized assignee or parent entity.
2. Retrieve eligible family set.
3. Determine ownership share and de-duplication rules.
4. Load V2 feature rows for all eligible families.
5. Validate coverage and identify missing assets.
6. Run batch inference.
7. Run batch calibration.
8. Generate asset-level explanations.
9. Aggregate:
   - total expected future citations,
   - low/high portfolio interval,
   - per-effective-family expectation,
   - difficulty mix,
   - cluster contribution.
10. Build segment views:
   - by CPC,
   - by market,
   - by jurisdiction,
   - by family maturity,
   - by quality bucket.
11. Attach reliability metadata and caveats.
12. Render portfolio-level forecast intelligence.

## Output Contract Expectations

### Patent/family response should include

1. `prediction_unit`
2. `family_model`
3. `horizon`
4. `as_of_date`
5. `expected_citations`
6. `interval`
7. `difficulty_bucket`
8. `top_positive_drivers`
9. `top_negative_drivers`
10. `feature_completeness`
11. `caveats`
12. `model_metadata`

### Portfolio response should include

1. `prediction_unit`
2. `owner_entity`
3. `horizon`
4. `expected_citations_total`
5. `interval_total`
6. `n_assets_effective`
7. `expected_per_effective_asset`
8. `top_contributors`
9. `difficulty_mix`
10. `segment_rollups`
11. `feature_coverage`
12. `model_metadata`

## UX Interpretation Rules

1. The forecast is a directional intelligence signal, not a guarantee.
2. The interval should be visible by default.
3. Top drivers must be visible without opening developer-only panels.
4. Filing-rate context must be labeled as segment or portfolio context, not as patent-owned behavior.
5. If completeness is weak, the UI must downgrade confidence language.

## Failure And Fallback Behavior

### Patent/family level

1. If the feature row is missing, show forecast unavailable.
2. If some contextual features are missing, continue only if completeness remains above threshold and label caveats.
3. If the V2 model is off, fall back to the previous model only with explicit labeling.

### Portfolio level

1. If some assets are missing from the feature mart, continue with coverage disclosure.
2. If the missing share is too large, suppress the forecast or mark it as low confidence.
3. If segment rollups fail, keep total forecast but hide broken segment views.

## Quality Gates Specific To These MVP Flows

1. Patent-level predictions must be traceable back to the feature row and model version.
2. Portfolio-level totals must reconcile with summed asset-level contributions under the documented aggregation rule.
3. Filing-rate context must be slice-correct and frozen at the as-of date.
4. No portfolio or patent response may silently mix family and application units.
5. Explanation outputs must be consistent with the served model and manifest version.

## Final Semantics Summary

### A patent/family prediction means

“Given what was knowable by the as-of date about this family and the surrounding tech-market-owner context, this family is expected to receive this many additional citations over the selected horizon.”

### A portfolio prediction means

“Given what was knowable by the as-of date about the portfolio’s families and the surrounding tech-market-owner context, this portfolio is expected to generate this amount of additional future citation impact, concentrated in these families and segments.”

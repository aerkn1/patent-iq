# Citation Forecast Model V2 Retraining Report

## Purpose

Re-scope the citation prediction rebuild so the 3-year and 5-year forecast models align with the new V2 data model, family-first product logic, and contest reliability standards.

## Current State Summary

### What exists today

1. The deployed forecast path serves two LightGBM models (`3y`, `5y`) from external artifacts loaded by `ModelRegistry`.
2. Inference is driven from `ml_training_table` through `ForecastFeatureRepository`.
3. The serving path uses only 10 model features:
   - `cites_pre_asof`
   - `family_members_count`
   - `family_jurisdiction_count`
   - `major_office_grant_auth_count`
   - `family_cpc_subclass_count`
   - `has_us_grant`
   - `has_cn_grant`
   - `has_jp_grant`
   - `has_kr_grant`
   - `as_of_year`
4. The current training table contains `1,079,510` rows and `1,009,490` distinct families.
5. `53,637` families have more than one row in the current table; maximum repeated rows per family is `27`.
6. The repo contains serving code and model docs, but no concrete in-repo training pipeline or experiment runner.

### What the current docs say

1. `docs/project/citation_prediction_models.md` describes the 10-feature deployed setup and reported metrics.
2. `docs/project/ml_guideline.md` describes a much richer 42-feature design, but that design is not what the current serving path uses.

## Primary Weaknesses In The Current Model Stack

### W-01: The serving feature set is too narrow

The current model depends mostly on early citation count, family breadth, grant flags, and year. It omits many high-value signals already implied by V2:

1. legal durability and renewal continuity,
2. assignee harmonization and ownership structure,
3. OECD-normalized quality indicators,
4. technology concentration and adjacency,
5. market and cohort context,
6. citation composition and externality signals.

Impact:
The model cannot fully distinguish family breadth from true quality, strategic durability, or technology/market momentum.

### W-02: The training grain does not match the product grain

The V2 product is moving to family-first analytics, but the model is still served at `appln_id` grain. The table includes `docdb_family_id`, yet the model ignores it as a first-class prediction unit.

Impact:
1. Prediction logic is misaligned with the platform narrative.
2. Multi-row families can over-weight repeated family structures during training.
3. Portfolio aggregation inherits application-grain artifacts even when the product defaults to family-level intelligence.

### W-03: Model reproducibility is weak

The application loads pretrained artifacts from Hugging Face, but the repository does not include:

1. a deterministic feature-builder,
2. a training script,
3. an experiment log,
4. a model card generator,
5. a reproducible calibration workflow.

Impact:
Retraining is hard to audit, hard to repeat, and risky under contest deadlines.

### W-04: The implementation does not deliver the explainability promised in docs

The docs discuss SHAP and richer interpretability, but the current serving response exposes only raw `features_used`, not feature contributions.

Impact:
Users see inputs, not reasons. That is weaker than the standard required for contest-grade trust.

### W-05: Missing-value behavior is too blunt

The serving code casts missing numeric values to `0.0`.

Impact:
This can convert missingness into a false negative signal and hide data quality problems from the user and evaluator.

### W-06: Calibration is too coarse

Calibration is bucketed by prediction magnitude rather than a richer residual-risk model with subgroup checks.

Impact:
Coverage may look acceptable globally while still failing for specific years, offices, tech fields, or low-data segments.

### W-07: No explicit product-aware feature hygiene

The current feature list does not clearly encode:

1. self-citation vs external citation differences,
2. intra-family citation exclusions,
3. lag/completeness flags,
4. office-aware comparability rules,
5. quality component provenance.

Impact:
The forecast layer risks drifting away from the logic users see elsewhere in the product.

### W-08: Portfolio aggregation is mechanically simple

Portfolio forecasts sum patent-level predictions weighted by owner share. This is serviceable, but it does not explicitly model:

1. same-family dependency,
2. overlapping uncertainty,
3. owner concentration effects,
4. cluster-level contribution structure.

Impact:
Portfolio totals are useful, but not yet as strong as the rest of the planned V2 platform.

## V2 Retraining Objective

Retrain the citation forecast system so the final model family is:

1. aligned to V2 family-first entities,
2. richer in legal, technology, quality, and market context,
3. reproducible end to end,
4. calibrated with subgroup accountability,
5. explainable enough for product and contest review.

## Proposed V2 Feature Schema

### Feature group A: Citation history and externality

Examples:
1. pre-as-of forward citations,
2. yearly citation velocity and acceleration,
3. unique citing families,
4. external vs self-citation share,
5. intra-family-scrubbed citation counts,
6. citing-assignee diversity.

Sources:
1. citation event marts,
2. family-aware citation marts,
3. assignee harmonization layer.

### Feature group B: Family structure and reach

Examples:
1. family member count,
2. jurisdiction spread,
3. family grant coverage,
4. family prosecution maturity,
5. family CPC breadth and entropy,
6. continuation/divisional or extended-family markers when available.

Sources:
1. `family_time`,
2. `family_members_metrics`,
3. `family_grant_metrics`,
4. `family_cpc_metrics`.

### Feature group C: Legal durability

Examples:
1. country-level active/lapsed/expired status counts,
2. renewal continuity indicators,
3. opposition/litigation flags if ready,
4. grant-lag or prosecution-speed context,
5. major-office grant breadth.

Sources:
1. `legal_status_events`,
2. grant marts,
3. OECD `grant_lag`,
4. renewal-derived signals.

### Feature group D: Technology and clustering

Examples:
1. CPC section/subclass counts,
2. CPC concentration and entropy,
3. adjacency to nearby tech clusters,
4. cluster density and competitive saturation,
5. top-cluster membership flags.

Sources:
1. `patent_tech_lens_freq`,
2. V2 cluster marts,
3. family CPC marts.

### Feature group E: Market and ownership context

Examples:
1. harmonized assignee type and size,
2. parent-group concentration,
3. market growth of the patent's tech-market slice,
4. peer filing intensity,
5. grant-rate context in the same slice.

Sources:
1. `assignee_harmonized`,
2. `corporate_tree`,
3. `tech_market_filing_grant_trends`.

### Feature group F: OECD quality context

Examples:
1. normalized `family_size`,
2. normalized `grant_lag`,
3. normalized `bwd_cits`,
4. normalized `npl_cits`,
5. normalized `claims`,
6. normalized `generality`, `originality`, `radicalness`,
7. optional explainable composites via `score_components`.

Sources:
1. `oecd_quality_indicators_family`,
2. `oecd_quality_cohort_stats`.

### Feature group G: Cohort, office, and completeness controls

Examples:
1. filing year,
2. tech field,
3. office source,
4. `many_field` overlap indicator,
5. data completeness percentage,
6. lag-warning flags.

Sources:
1. family time mart,
2. OECD cohort marts,
3. V2 reliability metadata.

## Prediction Grain Recommendation

### Recommended primary grain

Use `docdb_family_id` as the default training and inference grain for the V2 model.

### Why

1. It matches the V2 product direction.
2. It reduces duplicate-family over-representation.
3. It makes portfolio aggregation more natural.
4. It aligns the model with family-first trend, quality, and comparison logic.

### Fallback option

If family-grain rollout creates unacceptable migration risk in 5 weeks, train at application grain but add:

1. explicit family-weighting,
2. family-grouped split checks,
3. family-aware aggregation rules,
4. product labels that clarify the prediction grain.

## Recommended Modeling Strategy

### Baseline

1. LightGBM on `log1p(y)` for 3-year and 5-year targets.
2. Retain fast inference and structured explainability.

### Challengers

1. LightGBM with Poisson or Tweedie objective,
2. two-stage model:
   - classifier for `any_future_citations`,
   - regressor for positive-count magnitude.

### Selection rule

Ship the simplest model that wins on:

1. ranking quality,
2. calibration quality,
3. subgroup stability,
4. explainability,
5. inference simplicity.

## Evaluation Framework

### Core metrics

1. RMSE on `log1p(y)`,
2. MAE on raw counts,
3. Spearman rank correlation,
4. Precision@1%,
5. Precision@5%,
6. Recall@top-decile-impact.

### Calibration metrics

1. 80% interval coverage overall,
2. coverage by filing-year cohort,
3. coverage by office,
4. coverage by tech field,
5. coverage by prediction bucket.

### Product metrics

1. Stability of top contributor ranking in portfolios,
2. plausibility of segment contributions,
3. consistency with family-first platform logic,
4. quality of explanation payloads.

### Proposed ship targets

These are contest targets, not hard scientific guarantees:

1. 3-year Spearman `>= 0.33`,
2. 5-year Spearman `>= 0.33`,
3. Precision@1% improved versus current baseline or justified by much better calibration,
4. 80% interval coverage overall between `78%` and `82%`,
5. subgroup coverage no worse than `76%` to `84%` for major slices.

## V2 Training And Serving Deliverables

1. Versioned V2 feature manifest,
2. deterministic training dataset builder,
3. experiment runner,
4. calibration builder,
5. model cards for both horizons,
6. inference schema and migration plan,
7. explainability payload design,
8. rollback plan to prior model version.

## 5-Week ML Timeline

### Week 1: March 9-13, 2026

Goals:
1. Finalize target grain,
2. define feature manifest,
3. define evaluation and leakage rules,
4. choose baseline and challenger families.

Quality gates:
1. split policy approved,
2. leakage checklist approved,
3. feature groups mapped to V2 entities.

### Week 2: March 16-20, 2026

Goals:
1. Build V2 feature marts,
2. materialize training dataset,
3. run data profiling and null analysis,
4. establish baseline retraining pipeline.

Quality gates:
1. dataset is reproducible,
2. feature completeness report exists,
3. train/val/test row and family distributions are validated.

### Week 3: March 23-27, 2026

Goals:
1. Train baseline and challenger models,
2. evaluate ranking and error metrics,
3. run subgroup analysis,
4. calibrate intervals.

Quality gates:
1. candidate model shortlist produced,
2. coverage checked overall and by subgroup,
3. no leakage or major drift issues remain open.

### Week 4: March 30-April 3, 2026

Goals:
1. Select release-candidate model,
2. generate model cards,
3. integrate serving artifacts and metadata,
4. add explainability payloads.

Quality gates:
1. inference contract matches training manifest,
2. frontend can consume the new explanation fields,
3. old model fallback still works.

### Week 5: April 6-10, 2026

Goals:
1. Run final benchmark and regression suite,
2. validate cold and warm inference,
3. freeze artifacts,
4. approve or reject V2 model for release.

Quality gates:
1. final validation report signed off,
2. rollback path tested,
3. release decision made by Wednesday, April 8, 2026.

## Implementation Notes For The Current Repo

### Current code touchpoints that will likely change

1. `backend/infrastructure/repositories/forecast_feature_repo.py`
2. `backend/infrastructure/ml/model_registry.py`
3. `backend/application/services/patent_forecast_service.py`
4. `backend/application/services/portfolio_forecast_service.py`
5. `backend/domain/schemas/forecast.py`

### Expected changes

1. Replace the hardcoded 10-feature manifest with a versioned manifest loaded from model metadata.
2. Stop treating missing numeric values as silent zeros without completeness flags.
3. Expand metadata returned by forecast endpoints.
4. Add explanation payloads beyond raw feature echoes.
5. Revisit portfolio aggregation after family-grain model choice.

## Final Recommendation

Do not treat the current citation model as a small tuning problem. It is a schema-alignment problem, a reproducibility problem, and a product-trust problem.

The correct V2 move is:

1. rebuild the feature table first,
2. retrain from a reproducible pipeline,
3. evaluate ranking and calibration together,
4. expose stronger metadata and explanations,
5. ship only if the new model clears explicit gates.

## Related Detailed Operational Note

For detailed patent/family and portfolio MVP behavior, feature semantics, and filing-rate-context rules, see:

- `docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md`

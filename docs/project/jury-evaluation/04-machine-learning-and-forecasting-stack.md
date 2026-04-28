# Section 04. Machine Learning And Forecasting Stack

## Table Of Contents

1. [Purpose Of This Section](#purpose-of-this-section)
2. [What Counts As The V2 ML Stack](#what-counts-as-the-v2-ml-stack)
3. [Shared ML Governance, Reproducibility, And Release Rules](#shared-ml-governance-reproducibility-and-release-rules)
   - [1. Frozen training snapshot and split registries](#1-frozen-training-snapshot-and-split-registries)
   - [2. Why PatentIQ does not ship a direct monolithic portfolio model](#2-why-patentiq-does-not-ship-a-direct-monolithic-portfolio-model)
4. [Shared Feature-Source Boundary Across All Models](#shared-feature-source-boundary-across-all-models)
5. [Model Scope Inventory](#model-scope-inventory)
6. [Phase 03. Family Future Citation Forecast](#phase-03-family-future-citation-forecast)
   - [1. Business question and prediction grain](#1-business-question-and-prediction-grain)
   - [2. Label logic and outcome definition](#2-label-logic-and-outcome-definition)
   - [3. Features actually used, where they come from, and why](#3-features-actually-used-where-they-come-from-and-why)
   - [4. Split, training, validation, and calibration logic](#4-split-training-validation-and-calibration-logic)
   - [5. Aimed result versus obtained result](#5-aimed-result-versus-obtained-result)
   - [6. Release conclusion and safe product claim](#6-release-conclusion-and-safe-product-claim)
   - [7. How Phase 03 is wired into the app](#7-how-phase-03-is-wired-into-the-app)
7. [Phase 04. Family-Jurisdiction Lapse Risk](#phase-04-family-jurisdiction-lapse-risk)
   - [1. Business question and prediction grain](#1-business-question-and-prediction-grain-1)
   - [2. Label logic and outcome definition](#2-label-logic-and-outcome-definition-1)
   - [3. Features actually used, where they come from, and why](#3-features-actually-used-where-they-come-from-and-why-1)
   - [4. Split, training, validation, and calibration logic](#4-split-training-validation-and-calibration-logic-1)
   - [5. Aimed result versus obtained result](#5-aimed-result-versus-obtained-result-1)
   - [6. Release conclusion and safe product claim](#6-release-conclusion-and-safe-product-claim-1)
   - [7. How Phase 04 is wired into the app](#7-how-phase-04-is-wired-into-the-app)
8. [Pending-Grant Pipeline. Candidate Lane, Not Yet Sealed](#pending-grant-pipeline-candidate-lane-not-yet-sealed)
   - [1. Business question and prediction grain](#1-business-question-and-prediction-grain-2)
   - [2. Label logic and outcome definition](#2-label-logic-and-outcome-definition-2)
   - [3. Features actually used, where they come from, and why](#3-features-actually-used-where-they-come-from-and-why-2)
   - [4. Split, training, validation, and calibration logic](#4-split-training-validation-and-calibration-logic-2)
   - [5. Aimed result versus obtained result](#5-aimed-result-versus-obtained-result-2)
   - [6. Release conclusion and safe product claim](#6-release-conclusion-and-safe-product-claim-2)
   - [7. How the pending-grant lane is wired into the app](#7-how-the-pending-grant-lane-is-wired-into-the-app)
9. [Phase 06. Jurisdiction-Field Trend Forecast](#phase-06-jurisdiction-field-trend-forecast)
   - [1. Business question and prediction grain](#1-business-question-and-prediction-grain-3)
   - [2. Label logic and outcome definition](#2-label-logic-and-outcome-definition-3)
   - [3. Features actually used, where they come from, and why](#3-features-actually-used-where-they-come-from-and-why-3)
   - [4. Split, training, validation, and calibration logic](#4-split-training-validation-and-calibration-logic-3)
   - [5. Aimed result versus obtained result](#5-aimed-result-versus-obtained-result-3)
   - [6. Release conclusion and safe product claim](#6-release-conclusion-and-safe-product-claim-3)
   - [7. How Phase 06 is wired into the app](#7-how-phase-06-is-wired-into-the-app)
10. [Gold-Layer Forecast Aggregation And Serving Wiring](#gold-layer-forecast-aggregation-and-serving-wiring)
11. [Backend API And Frontend View Traceability](#backend-api-and-frontend-view-traceability)
12. [Current ML Claim Boundaries](#current-ml-claim-boundaries)
13. [Key Takeaways](#key-takeaways)

## Purpose Of This Section

Sections 01 through 03 established the data lineage, backend contract layer, and frontend workspace behavior. This section explains the predictive layer that sits on top of those foundations.

The main questions answered here are:

1. which models exist in the V2 implementation,
2. what exact feature sets they use and which marts those features come from,
3. how labels, train/validation/test splits, and calibration are built,
4. which models are sealed for MVP versus still candidate-only,
5. how model outputs are rolled up into Gold marts, backend endpoints, and frontend views.

Primary implementation references:

1. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md:1-493`
2. `docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md:1-260`
3. `etl/src/patentiq_etl/ml/phase0.py:27-116`
4. `etl/src/patentiq_etl/ml/phase03.py:16-1200`
5. `etl/src/patentiq_etl/ml/phase04.py:15-1065`
6. `etl/src/patentiq_etl/ml/phase_grant.py:15-1055`
7. `etl/src/patentiq_etl/ml/phase06.py:15-820`

## What Counts As The V2 ML Stack

The active V2 machine-learning stack is the ETL-driven model layer under `etl/src/patentiq_etl/ml/` plus the Gold, backend, and frontend wiring that consumes its outputs.

The currently relevant V2 scopes are:

1. `family_future_citation_forecast`
2. `family_jurisdiction_lapse_risk`
3. `publication_or_subfamily_grant_probability` as the pending-grant pipeline
4. `jurisdiction_field_trend_forecast`

The ML implementation is ETL-owned and reproducible. Training, calibration, model cards, and release decisions are all tracked inside the current artifact flow.

Implementation references:

1. `docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md:7-126`
2. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md:22-55`

## Shared ML Governance, Reproducibility, And Release Rules

### 1. Frozen training snapshot and split registries

PatentIQ does not treat model training as an ad hoc notebook exercise. The intended V2 contract is:

1. freeze the upstream snapshot,
2. build explicit labels,
3. build scope-specific feature tables,
4. freeze split assignment,
5. train baseline and challenger models on the same split registry,
6. calibrate on validation only,
7. promote only when reliability and subgroup behavior are acceptable.

That governance is documented in the prediction runbook and implemented first in `Phase 0`, which fingerprints upstream tables and writes a deterministic split registry for immediate forecast work.

The shared registries are:

1. `ml_feature_manifest`
2. `ml_split_registry`
3. `ml_experiment_registry`
4. `ml_calibration_registry`
5. `ml_model_registry`

This makes model artifacts auditable. Every promoted or candidate artifact is tied to:

1. training snapshot,
2. feature manifest version,
3. calibration version,
4. prediction unit,
5. promotion status.

Implementation references:

1. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md:56-147`
2. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md:148-493`
3. `etl/src/patentiq_etl/ml/phase0.py:27-116`

### 2. Why PatentIQ does not ship a direct monolithic portfolio model

The V2 design explicitly rejects a single opaque company-level forecast model for MVP. Portfolio prediction is treated as a derived bottom-up layer built from lower-level micro predictions.

The reasoning is architectural and business-facing:

1. a portfolio is a heterogeneous basket of families, branches, legal states, jurisdictions, and technology slices,
2. direct company-level modeling would hide which families or branches actually drive the result,
3. the product needs drill-down from portfolio totals back to micro contributors,
4. the backend and UI already expose that drill-down path.

So the portfolio forecast is an aggregation contract, not a separate direct model family.

Implementation references:

1. `docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md:155-260`
2. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md:33-55`
3. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md:398-493`

## Shared Feature-Source Boundary Across All Models

All V2 models consume curated Silver and Gold marts rather than raw patent tables directly. Section 01 already documented how those marts are derived from DOCDB, INPADOC, OECD-style indicator builds, family harmonization, legal-status replay, coverage logic, and Gold-serving contracts. The ML layer deliberately starts from those already-validated analytical contracts because raw-source joins alone would not guarantee:

1. family-first collapse rules,
2. point-in-time safety,
3. normalized quality indicators,
4. harmonized legal state semantics,
5. stable ownership and market context.

The most important shared model inputs are:

| Mart or artifact | Used by | Why it exists in the feature stack |
| --- | --- | --- |
| `gold_family_summary.parquet` | Phase 03, pending-grant | canonical family grain, size, owner breadth, enforceability, priority dates, jurisdiction reach |
| `silver_family_citation_metrics.parquet` | Phase 03 | clean pre-as-of citation counts, weighted citation mass, RCF-style citation quality context |
| `silver_enriched_citation_network.parquet` | Phase 03 | unique citing-family structure, citing-assignee diversity, attacker-density externality signals |
| `silver_family_oecd_quality.parquet` | Phase 03 | cohort-aware OECD-style percentiles such as quality index, generality, radicalness, science grounding |
| `silver_family_coverage_metrics.parquet` | Phase 03 | coverage stability and data quality context |
| `silver_family_status_pt.parquet` | Phase 03 | current family composite status used both as feature and interpretation context |
| `silver_family_wipo_fields.parquet` | Phase 03 | primary field slice for modeling, evaluation, and subgroup calibration |
| `silver_family_feature_snapshot_pit.parquet` | Phase 03 | leakage-safe replacement for current-state metrics at the relevant as-of boundary |
| `silver_legal_status_event_ledger.parquet` | Phase 04 | dated negative legal events used to create lapse labels |
| `silver_branch_status_history_dense.parquet` | Phase 04, pending-grant | yearly branch-state replay for active-grant and pending snapshots |
| `silver_family_feature_snapshot_pit_dense.parquet` | Phase 04, pending-grant | dense PIT-safe family context at yearly or row-exact as-of points |
| `silver_family_member_publications.parquet` | pending-grant | application-stage and grant-stage publication counts by family and jurisdiction |
| `silver_local_tech_trends_timeseries.parquet` | pending-grant, Phase 06 | local filing-level trend context by jurisdiction and field |
| `silver_global_tech_trends_timeseries.parquet` | Phase 06 | global field trend baseline used to contextualize local direction |
| `gold_market_summary_pit.parquet` | Phase 06 | segment heat-state and compact market overlays used in trend prediction |

Implementation references:

1. `etl/src/patentiq_etl/ml/phase0.py:56-76`
2. `etl/src/patentiq_etl/ml/phase03.py:149-158`
3. `etl/src/patentiq_etl/ml/phase04.py:94-100`
4. `etl/src/patentiq_etl/ml/phase_grant.py:620-627`
5. `etl/src/patentiq_etl/ml/phase06.py:100-105`

## Model Scope Inventory

| Model scope | Native prediction unit | Main product question | Current status |
| --- | --- | --- | --- |
| `family_future_citation_forecast` | `docdb_family_id` | How much future citation impact is this family likely to accumulate over `3y` and `5y`? | sealed candidate accepted for MVP, interval-first |
| `family_jurisdiction_lapse_risk` | `docdb_family_id x jurisdiction_code x as_of_date` | Which granted branches are most at risk of lapse or expiry over `12m` and `24m`? | sealed candidate accepted for MVP, risk-band-first |
| `publication_or_subfamily_grant_probability` | `docdb_family_id x jurisdiction_code x as_of_date` | Which pending branches are most likely to convert to grant soon? | candidate-only, not sealed |
| `jurisdiction_field_trend_forecast` | `jurisdiction_code x wipo_industry_code x as_of_year` | Is a market slice heating, cooling, or stable over the next `3y` and `5y`? | sealed candidate accepted for MVP, direction-band-first |

Implementation references:

1. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md:22-55`
2. `docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md:17-34`

## Phase 03. Family Future Citation Forecast

### 1. Business question and prediction grain

Phase 03 answers the family-level future-impact question:

How many additional forward citations is a canonical DOCDB family likely to accumulate in the next `3y` or `5y`, and how uncertain is that outlook?

The prediction grain is intentionally `docdb_family_id`, not publication or application grain, because V2 is family-first across product ranking, portfolio rollup, compare, and evidence views.

Implementation references:

1. `docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md:17-34`
2. `etl/src/patentiq_etl/ml/phase03.py:16-24`
3. `etl/src/patentiq_etl/ml/phase03.py:1098-1110`

### 2. Label logic and outcome definition

The label logic is leakage-safe and explicitly anchored to an as-of boundary:

1. if explicit future-label columns already exist in the citation mart, the stage uses them,
2. otherwise it derives labels from the clean citation-event network,
3. the as-of anchor is `family_earliest_priority_date + 2 years`,
4. `3y` and `5y` targets count distinct clean citing families whose first clean citation lands after the as-of date but before the horizon end,
5. out-of-bounds, intra-family, and self-citation edges are excluded when those flags exist,
6. `log1p` targets are materialized alongside raw-count targets for training.

This shows that the model is not learning from post-outcome leakage disguised as current citation volume.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase03.py:243-390`

### 3. Features actually used, where they come from, and why

The implemented Phase 03 feature vector uses a materially richer schema. The current feature set includes:

1. citation mass and momentum:
   - `family_forward_citations_clean`
   - `family_forward_citations_weighted_7y`
   - `family_rcf_score`
2. citation-network externality:
   - `unique_citing_family_count`
   - `citing_assignee_diversity`
   - `attacker_density_score`
3. family breadth and ownership context:
   - `family_size_docdb`
   - `active_jurisdiction_count`
   - `family_distinct_owner_count`
4. legal posture:
   - `family_composite_status`
   - `branch_enforceability_contribution_raw`
   - `family_overall_legal_enforceability_score`
   - `active_grant_branch_count`
5. OECD-style quality layer:
   - `quality_index_4_percentile`
   - `quality_index_6_percentile`
   - `generality_percentile`
   - `radicalness_percentile`
   - `science_grounding_percentile`
6. cohort anchor:
   - `family_earliest_priority_date`
   - derived `family_age_years`
7. completeness and PIT support:
   - `family_coverage_stability_score`
   - `data_completeness_pct`

Why these groups were chosen:

1. pre-as-of citation and network features measure already-earned external attention,
2. family breadth and ownership fields separate genuine influence from single-office narrowness,
3. legal durability features prevent the model from reading weak legal posture as equal to strong enforceable posture,
4. OECD-style percentiles add cohort-normalized quality signals that raw counts alone cannot capture,
5. completeness metrics let the serving layer caveat sparse families rather than silently overclaim.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase03.py:27-84`
2. `etl/src/patentiq_etl/ml/phase03.py:1282-1412`
3. `docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md:127-232`

### 4. Split, training, validation, and calibration logic

Phase 03 uses a time-aware family-grouped split policy:

1. `train` for older priority-year cohorts,
2. `validation` for the next time band,
3. `test` for the latest fully eligible cohorts,
4. `unassigned_recent` for recent families that should not be used as if their outcome horizon were fully known.

Concretely, the stage computes:

1. `family_forecast_cutoff_year = snapshot_year - 6`
2. `train` if `family_priority_year <= cutoff_year - 4`
3. `validation` if `family_priority_year` is in `cutoff_year - 3 .. cutoff_year - 2`
4. `test` if `family_priority_year` is in `cutoff_year - 1 .. cutoff_year`

Training and evaluation behavior:

1. baseline algorithm is `LightGBMRegressor` on `log1p(target)`,
2. a two-stage challenger is trained for breakout-tail behavior only when tail support is large enough,
3. model selection is based on validation performance, not test leakage,
4. grouped conformal interval calibration is applied with `primary_wipo_field` as the main subgroup where support allows,
5. PIT-safe replacements are applied from `silver_family_feature_snapshot_pit` before promotion-safe training.

The stage also caps sampled row counts for training speed while preserving raw split counts in the model card and manifest. Current raw and used counts are materially different, which is explicitly logged rather than hidden.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase03.py:139-147`
2. `etl/src/patentiq_etl/ml/phase03.py:1347-1412`
3. `etl/src/patentiq_etl/ml/phase03.py:1436-1465`
4. `etl/src/patentiq_etl/ml/phase03.py:822-1200`
5. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md:257-358`

### 5. Aimed result versus obtained result

The explicit Phase 03 safe-use goal is not exact-count certainty. The goal is:

1. rank future-impactful families correctly,
2. provide interval-calibrated outlooks,
3. keep subgroup reliability acceptable enough for MVP.

The clearest numeric target encoded in the training logic is interval coverage:

1. `3y` target coverage: `0.80`
2. `5y` target coverage: `0.775`

Obtained results from the live trained artifacts are:

| Horizon | Intended reading | Obtained held-out result |
| --- | --- | --- |
| `3y` | interval-first ranking and outlook | Spearman about `0.4495`; interval coverage about `0.8054` |
| `5y` | interval-first ranking and outlook | Spearman about `0.5996`; interval coverage about `0.7970` |

The broader artifact record also shows:

1. raw split sizes of about `6.41M` train, `2.31M` validation, `2.81M` test rows,
2. sampled training use of `200k/50k/50k`,
3. selected variant remained `baseline` for both horizons,
4. subgroup coverage by `primary_wipo_field` still spreads wider than the strict final-production gate.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase03.py:142-144`
2. `docs/next-phase-v2/44-patentiq-v2-phase-03-seal-decision-and-accepted-caveats.md:25-95`
3. `etl/manifests/stages/ml-phase03-family-forecast.json`
4. `etl/data/ml/model_card_family_future_citation_forecast.json`
5. `etl/data/ml/family_future_citation_forecast_release_decision.json`

### 6. Release conclusion and safe product claim

Phase 03 is accepted as a sealed MVP candidate, but not fully promoted production.

The release-safe conclusion is:

1. the model is strong enough for family-level future-impact outlook and bottom-up portfolio planning,
2. the model is not approved to claim field-uniform calibration truth,
3. the UI should emphasize range and direction before midpoint.

The release note explicitly requires:

1. interval-first presentation,
2. directional outlook language,
3. caveat metadata,
4. no claim that the point forecast is literal future truth.

Implementation references:

1. `docs/next-phase-v2/44-patentiq-v2-phase-03-seal-decision-and-accepted-caveats.md:13-129`

### 7. How Phase 03 is wired into the app

The family-serving path is direct:

1. `FamilyRepository` resolves `ml_prediction_family_future_citations.parquet`,
2. `get_family_forecasts()` fetches the latest forecast year for the selected family,
3. `FamilyService` exposes those rows under the `forecasts` section,
4. `frontend_v2` loads that section on workspace boot,
5. the family citation chronology panel overlays the future interval band and midpoint on top of observed history.

The portfolio-serving path is bottom-up:

1. Gold rollups sum family-level expected totals and intervals by owner,
2. backend portfolio services expose those rollups through `/forecast`,
3. frontend portfolio panels render the forecast interval cards, citation outlook chart, and top forecast contributors table.

Implementation references:

1. `backend_v2/infrastructure/repositories/family_repository.py:36-37`
2. `backend_v2/infrastructure/repositories/family_repository.py:913-931`
3. `backend_v2/application/services/families.py:603-641`
4. `frontend_v2/lib/api/family-v2.ts:171-193`
5. `frontend_v2/components/family/family-workspace.tsx:1693-1918`
6. `etl/src/patentiq_etl/gold/build_gold.py:481-495`
7. `backend_v2/application/services/portfolios.py:1600-1695`
8. `frontend_v2/components/portfolio/portfolio-forecast-panel.tsx:28-120`
9. `frontend_v2/components/portfolio/portfolio-citation-timeseries-panel.tsx:76-440`

## Phase 04. Family-Jurisdiction Lapse Risk

### 1. Business question and prediction grain

Phase 04 answers:

Which currently active granted family branches are most likely to lapse or expire within `12m` or `24m`, and how should that risk be surfaced safely across different offices?

The native grain is not family-only. It is `docdb_family_id x jurisdiction_code x as_of_date`, because lapse behavior depends on branch-level office context and legal chronology.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase04.py:15-33`
2. `etl/src/patentiq_etl/ml/phase04.py:633-645`

### 2. Label logic and outcome definition

The label is built from yearly active-grant snapshots joined to dated negative legal events:

1. build yearly `ACTIVE_GRANT` branch snapshots from dense branch history,
2. find the first negative event after the as-of date from the legal-event ledger,
3. mark `lapse_risk_12m_label = 1` if that first negative event occurs within `12 months`,
4. mark `lapse_risk_24m_label = 1` if it occurs within `24 months`,
5. only mark rows as observed when the horizon is fully closed by the ETL snapshot date.

This is important because branch-level legal-outcome labels are right-censored by time. The model only evaluates rows whose full outcome window is actually observable.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase04.py:720-796`

### 3. Features actually used, where they come from, and why

The Phase 04 feature set is branch-aware and legally grounded. The implemented features include:

1. branch legal state and timing:
   - `branch_state_asof`
   - `has_active_grant_asof`
   - years since last grant, lapse, and expiry events
   - `branch_stage_multiplier_asof`
   - `branch_enforceability_contribution_raw_asof`
2. family legal environment:
   - `family_composite_status_asof`
   - `active_jurisdiction_count_asof`
   - `lapsed_jurisdiction_count_asof`
   - `family_jurisdiction_count_asof`
   - `family_coverage_stability_score_asof`
   - `family_overall_legal_enforceability_score_asof`
3. strategic family context:
   - `family_blocking_power_score_asof`
   - `family_field_contribution_primary_asof`
   - `family_tech_breadth_wipo_count_asof`
   - `family_size_docdb_asof`
   - `family_rcf_score_asof`
4. citation pressure as of the same boundary:
   - clean and weighted forward citations
   - unique citing families
   - citing-assignee diversity
   - attacker density
5. office flags and age:
   - major office indicators for `EP`, `US`, `CN`, `JP`, `KR`
   - `family_age_years`

Why these groups were chosen:

1. lapse risk is primarily a branch-level legal and economic decision, so dated branch-state timing must be in the feature set,
2. a branch should be interpreted in family context because broad, durable, high-blocking families behave differently from weak narrow families,
3. office flags are essential because legal maintenance behavior and data balance differ materially by jurisdiction,
4. PIT-safe citation and blocking context provides strategic weight without contaminating the label with future information.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase04.py:50-81`
2. `etl/src/patentiq_etl/ml/phase04.py:799-893`

### 4. Split, training, validation, and calibration logic

Phase 04 uses grouped trajectory-based time splits:

1. each entity is a family-jurisdiction trajectory,
2. split assignment is based on the first active-grant year of that trajectory,
3. the latest usable `24m` cohort must still have enough positive examples to be defensible,
4. earlier cohorts become training rows, the next cohort becomes validation, the latest usable cohort becomes test,
5. more recent trajectories become `unassigned_recent`.

Training and calibration behavior:

1. baseline algorithm is `LightGBMClassifier`,
2. class imbalance is handled through `scale_pos_weight = negatives / positives`,
3. calibration candidates are `identity`, `Platt`, and `isotonic`,
4. the selected calibration method is the one with lowest validation Brier score, then log loss,
5. evaluation stores ROC AUC, PR AUC, Brier score, log loss, top-decile lift, top-risk-quintile recall, expected lapse count error, and subgroup summaries.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase04.py:463-493`
2. `etl/src/patentiq_etl/ml/phase04.py:496-701`
3. `etl/src/patentiq_etl/ml/phase04.py:958-1033`

### 5. Aimed result versus obtained result

The intended Phase 04 MVP outcome is not "perfect office-precise lapse probability everywhere." The intended safe outcome is:

1. strong branch-level risk discrimination overall,
2. usable risk ranking and banding,
3. office-aware serving rules where subgroup evidence is uneven.

Obtained live results are strong overall:

| Horizon | Obtained held-out result |
| --- | --- |
| `12m` | ROC AUC about `0.9845`; PR AUC about `0.1130`; Brier about `0.0028` |
| `24m` | ROC AUC about `0.9698`; PR AUC about `0.1047`; Brier about `0.0052` |

The stage manifest also records first-pass test metrics around:

1. `12m ROC AUC = 0.9828`
2. `24m ROC AUC = 0.9715`

The remaining limitation is subgroup office reliability. The release note states:

1. `JP` is strong,
2. `US` is moderate and should still caveat `24m`,
3. `CN`, `KR`, `EP`, `DE`, `ES`, `TW`, and other sparse offices are limited-support cohorts.

Implementation references:

1. `docs/next-phase-v2/46-patentiq-v2-phase-04-seal-decision-and-serving-contract.md:25-145`
2. `etl/manifests/stages/ml-phase04-family-jurisdiction-lapse-risk.json`
3. `etl/data/ml/family_jurisdiction_lapse_risk_release_decision.json`

### 6. Release conclusion and safe product claim

Phase 04 is accepted as a sealed MVP candidate, but not as universal office-level probability authority.

The current safe reading is:

1. overall ranking and risk banding are strong,
2. office support must be carried into serving,
3. exact probability display must be hidden or downgraded for limited-support offices,
4. this model should not be presented as automatic abandonment truth.

Implementation references:

1. `docs/next-phase-v2/46-patentiq-v2-phase-04-seal-decision-and-serving-contract.md:53-239`

### 7. How Phase 04 is wired into the app

The family workflow is:

1. `FamilyRepository` resolves `ml_prediction_family_jurisdiction_lapse_risk.parquet`,
2. `get_family_lapse_risk_rows()` returns the latest year rows,
3. `FamilyService` serializes them under `series_kind = "lapse_risk"` and adds `probability_display_allowed`,
4. the frontend family workspace loads the same `forecasts` section as citation forecast, so citation outlook and legal-risk outlook travel together.

The portfolio workflow is:

1. Gold forecast rollups sum calibrated branch probabilities into expected lapse counts,
2. backend portfolio services expose banded risk distributions and top contributors,
3. frontend forecast panels and legal/risk views use risk bands as the primary story.

Implementation references:

1. `backend_v2/infrastructure/repositories/family_repository.py:37-38`
2. `backend_v2/infrastructure/repositories/family_repository.py:933-951`
3. `backend_v2/application/services/families.py:603-641`
4. `etl/src/patentiq_etl/gold/build_gold.py:496-515`
5. `backend_v2/infrastructure/repositories/portfolio_repository.py:45-50`
6. `backend_v2/application/services/portfolios.py:1600-1695`
7. `frontend_v2/components/portfolio/portfolio-forecast-panel.tsx:34-120`

## Pending-Grant Pipeline. Candidate Lane, Not Yet Sealed

### 1. Business question and prediction grain

The pending-grant lane asks:

Which pending family-jurisdiction branches are most likely to convert to grant over `12m` or `24m`, and how should that be exposed without overclaiming reliability?

Its native prediction grain is also `docdb_family_id x jurisdiction_code x as_of_date`. That is the right grain because the product later aggregates branch-level probabilities upward into portfolio pipeline views.

Implementation references:

1. `docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md:300-314`
2. `etl/src/patentiq_etl/ml/phase_grant.py:15-29`

### 2. Label logic and outcome definition

The label is built from pending branch snapshots:

1. identify pending branch rows in dense branch history,
2. find the first future active-grant date for the same family-jurisdiction pair,
3. mark `grant_event_12m = 1` if first grant occurs within `12 months`,
4. mark `grant_event_24m = 1` if first grant occurs within `24 months`,
5. mark `observed_12m` and `observed_24m` only when the horizon is closed by the ETL snapshot date,
6. compute `pending_age_years` from the last pending event date where available.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase_grant.py:720-845`

### 3. Features actually used, where they come from, and why

The current trained feature vector uses:

1. age and cohort anchors:
   - `as_of_year`
   - `family_priority_year`
   - `family_age_years`
   - `pending_age_years`
2. field and status context:
   - `primary_wipo_field`
   - `family_composite_status_asof`
3. family scale and durability:
   - `family_size_docdb_asof`
   - `family_jurisdiction_count_asof`
   - `family_coverage_stability_score_asof`
   - `family_tech_breadth_wipo_count_asof`
4. strategic and citation context:
   - `family_blocking_power_score_asof`
   - `family_enforceability_score_asof`
   - `family_rcf_score_asof`
   - `pre_asof_forward_citations_clean`
   - `pre_asof_forward_citations_weighted`
   - `data_completeness_pct_asof`
5. prosecution volume:
   - `application_stage_publication_count`
   - `grant_stage_publication_count`
6. office-field historical priors:
   - `jurisdiction_field_grant_rate_prior_12m`
   - `jurisdiction_field_grant_rate_prior_24m`
7. local trend context:
   - `local_family_filings_asof`
   - `prior_period_local_family_filings_asof`
   - `local_growth_rate_asof`
   - `local_trend_coefficient_asof`
8. office flags:
   - `jurisdiction_is_ep`
   - `jurisdiction_is_us`
   - `jurisdiction_is_cn`
   - `jurisdiction_is_jp`
   - `jurisdiction_is_kr`
   - `jurisdiction_is_major_office`

One especially important implemented formula is the smoothed jurisdiction-field prior grant rate. For a field-office slice with observations, the stage uses:

`(field_positives + 50 * fallback_rate) / (field_observed + 50)`

where the fallback rate comes from the broader jurisdiction or global prior when needed. This is effectively a shrinkage rule that prevents tiny slices from behaving like noisy hard truths.

Why these groups were chosen:

1. pending conversion depends on age and procedural maturity,
2. family quality, blocking, and enforceability proxy examination seriousness and commercial value,
3. office-field priors encode real grant environment differences,
4. local trend context adds current market heat without reusing another model's output directly,
5. completeness lets the serving layer caveat weak cases.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase_grant.py:46-77`
2. `etl/src/patentiq_etl/ml/phase_grant.py:747-775`
3. `etl/src/patentiq_etl/ml/phase_grant.py:863-989`
4. `docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md:189-299`

### 4. Split, training, validation, and calibration logic

The pending-grant stage uses grouped family-jurisdiction trajectories:

1. split key is effectively the family-jurisdiction trajectory,
2. training is based on the first pending year of that trajectory,
3. `train <= snapshot_year - 5`
4. `validation = snapshot_year - 4`
5. `test = snapshot_year - 3`
6. more recent rows are `unassigned_recent`

Training and evaluation behavior:

1. baseline algorithm is `LightGBMClassifier`,
2. imbalance is handled with `scale_pos_weight`,
3. calibration candidates are `identity`, `Platt`, and `isotonic`,
4. the current trained artifacts selected `isotonic` for both horizons,
5. subgroup metrics are stored by office and field.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase_grant.py:283-311`
2. `etl/src/patentiq_etl/ml/phase_grant.py:419-617`
3. `etl/src/patentiq_etl/ml/phase_grant.py:1002-1032`

### 5. Aimed result versus obtained result

The planned product goal was a calibrated micro-level grant-probability lane that could safely roll up into:

1. expected likely grants,
2. grants by office,
3. grants by field,
4. contributor drill-down.

The current obtained results do not yet justify that level of strong claim:

| Horizon | Aggregate hold-out result | Real-entity audit result |
| --- | --- | --- |
| `12m` | ROC AUC about `0.6395`; PR AUC about `0.1670`; Brier about `0.0887` | ROC AUC about `0.5886`; PR AUC about `0.1699`; Brier about `0.0995` |
| `24m` | ROC AUC about `0.6600`; PR AUC about `0.3201`; Brier about `0.1569` | ROC AUC about `0.6148`; PR AUC about `0.3242`; Brier about `0.1751` |

The execution note is explicit that enrichment improved feature realism but did not improve the model enough to seal it. `JP` behaves best in the audited slice, while `CN` and `US` still overpredict materially.

Implementation references:

1. `docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md:47-123`
2. `etl/manifests/stages/ml-pending-grant-pipeline.json`
3. `etl/data/ml/model_card_pending_grant_pipeline.json`
4. `etl/data/ml/pending_grant_real_entity_audit.json`

### 6. Release conclusion and safe product claim

The current release conclusion is:

1. this is a useful candidate ranking signal,
2. it is not sealed as public-facing probability truth,
3. it should be exposed rank/percentile-first, tier second, raw probability only as subordinate caveated detail.

In other words, the pending-grant lane is part of the app, but it is intentionally disclosed as candidate-only analytics rather than sealed core forecast truth.

Implementation references:

1. `docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md:124-188`

### 7. How the pending-grant lane is wired into the app

This lane already reaches the V2 portfolio workspace, but under a caveated contract:

1. `PortfolioRepository` prefers `ml_prediction_pending_grant_pipeline.parquet` when present,
2. if the global prediction mart is missing, it can build an owner-scoped cache from current artifacts,
3. `PortfolioService` returns a `candidate_only` pending-grant section with summary, jurisdiction, field, and branch rows,
4. the frontend renders a dedicated pending-grant panel that emphasizes expected likely grants, percentile, priority tier, and shortlist ranking,
5. the panel footnote explicitly says to use rank, percentile, and tier as the primary planning cues.

Implementation references:

1. `backend_v2/infrastructure/repositories/portfolio_repository.py:45-50`
2. `backend_v2/infrastructure/repositories/portfolio_repository.py:2690-3007`
3. `backend_v2/application/services/portfolios.py:1444-1598`
4. `frontend_v2/lib/api/portfolio-v2.ts:785-863`
5. `frontend_v2/lib/api/portfolio-v2.ts:1240-1259`
6. `frontend_v2/components/portfolio/portfolio-pending-grants-panel.tsx:63-314`

## Phase 06. Jurisdiction-Field Trend Forecast

### 1. Business question and prediction grain

Phase 06 asks a market-intelligence question instead of an asset question:

For a given `jurisdiction_code x wipo_industry_code x as_of_year` slice, is the local market direction over the next `3y` or `5y` more likely to be `heating`, `cooling`, or `stable`?

This is intentionally not a family model. It is a segment-level trend model used to contextualize portfolio field exposure.

Implementation references:

1. `docs/next-phase-v2/49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md:1-120`
2. `etl/src/patentiq_etl/ml/phase06.py:15-60`

### 2. Label logic and outcome definition

The dense timeseries frame derives future direction as follows:

1. shift local family-filings counts by `3` and `5` years,
2. only treat a row as observed when the future year exists within the dataset,
3. compute the future count difference versus the current count,
4. label as `heating` if the difference is positive,
5. label as `cooling` if the difference is negative,
6. otherwise label as `stable`.

The model retains raw future counts and growth rates, but the promoted serving contract is direction-first.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase06.py:355-373`

### 3. Features actually used, where they come from, and why

The Phase 06 feature families are:

1. local trend state:
   - current local filings
   - prior-period local filings
   - local growth and trend coefficients
   - lags, acceleration, volatility
2. global field context:
   - global filings
   - global growth and trend coefficients
   - global lags and volatility
3. relative positioning:
   - local/global share
   - local-minus-global growth spread
   - local-minus-global trend spread
4. market overlays:
   - `segment_heat_state_asof`
   - `segment_family_count_asof`
   - `segment_growth_proxy_asof`
5. office indicators:
   - major office flag plus `EP`, `US`, `CN`, `JP`, `KR`

Why these groups were chosen:

1. market direction is fundamentally a temporal pattern problem, so lag and volatility terms matter,
2. local counts alone are misleading without global field context,
3. spread features help distinguish "field growing everywhere" from "this office accelerating faster than the world",
4. support and strength bands are later derived from model probabilities and training support, not guessed in the UI.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase06.py:61-97`
2. `etl/src/patentiq_etl/ml/phase06.py:340-353`
3. `docs/next-phase-v2/49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md:158-218`

### 4. Split, training, validation, and calibration logic

Phase 06 uses a grouped time split by `as_of_year`:

1. the latest years that still have a fully observed `5y` future become the evaluation anchor,
2. the two preceding years are validation,
3. the next two latest fully observed years are test,
4. newer rows are `unassigned_recent`.

Training and serving behavior:

1. baseline algorithm is `LightGBMClassifier` with three classes,
2. the stage computes probability-based `trend_strength_band`,
3. strength is `strong`, `moderate`, or `weak` based on top probability and probability margin,
4. support level is `strong`, `moderate`, or `limited` based on train rows, minority-class share, and a major-office override,
5. predictions carry both primary direction and secondary reference outputs such as growth-rate and count references.

Implementation references:

1. `etl/src/patentiq_etl/ml/phase06.py:51-60`
2. `etl/src/patentiq_etl/ml/phase06.py:376-416`
3. `etl/src/patentiq_etl/ml/phase06.py:426-589`

### 5. Aimed result versus obtained result

Phase 06 is the clearest case where the project redefined the target after empirical results. The original raw-count baselines were useful diagnostically, but not strong enough for trustworthy product claims. The project therefore moved to a direction-first contract.

The strategy comparison artifact shows why:

| Horizon | Raw-count direction accuracy | Direction-first classifier result | Conclusion |
| --- | --- | --- | --- |
| `3y` | about `0.4272` | class accuracy about `0.5416`, macro F1 about `0.5421` | direction-first is materially better |
| `5y` | about `0.7000` | class accuracy about `0.7266`, macro F1 about `0.5874` | direction-first is still better and safer |

The live model card records:

1. `3y balanced accuracy` about `0.6256`
2. `5y balanced accuracy` about `0.8631`
3. current split sizes of `8650 train / 1730 validation / 1730 test`

Implementation references:

1. `docs/next-phase-v2/49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md:102-120`
2. `etl/data/ml/phase06_strategy_comparison.json`
3. `etl/data/ml/model_card_jurisdiction_field_trend_forecast.json`
4. `etl/manifests/stages/ml-phase06-jurisdiction-field-trend-forecast.json`

### 6. Release conclusion and safe product claim

Phase 06 is accepted for MVP only under a conservative `direction_band_first` contract.

The current safe reading is:

1. use `heating`, `cooling`, and `stable` as the primary output,
2. use support level and trend strength as confidence framing,
3. treat raw count references as secondary context,
4. do not claim exact future filing-count authority.

Implementation references:

1. `docs/next-phase-v2/49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md:81-120`
2. `etl/data/ml/model_card_jurisdiction_field_trend_forecast.json`

### 7. How Phase 06 is wired into the app

Phase 06 is not shown as a separate "ML widget" page. It reaches the product through portfolio and market-context overlays:

1. ETL aggregates latest Phase 06 segment predictions into portfolio forecast segments,
2. backend market-context responses expose direction band, support level, growth-rate reference, and count reference,
3. the portfolio forecast and market-context views use those outputs to show heating and cooling exposure by field.

Implementation references:

1. `etl/src/patentiq_etl/gold/build_gold.py:516-561`
2. `etl/src/patentiq_etl/gold/build_gold.py:654-703`
3. `backend_v2/infrastructure/repositories/portfolio_repository.py:2519-2557`
4. `backend_v2/application/services/portfolios.py:1279-1342`

## Gold-Layer Forecast Aggregation And Serving Wiring

The predictive layer does not stop at raw model files. ETL converts micro predictions into Gold marts that the app can consume consistently.

The rollup logic in `build_gold.py` does three different jobs:

1. Phase 03 portfolio rollup:
   - sum family expected future citations and interval bounds
   - compute average completeness
   - compute top-contributor dependence
2. Phase 04 portfolio rollup:
   - sum calibrated branch lapse probabilities into expected lapse counts
   - compute limited-support share
   - compute average branch scoring coverage
3. Phase 06 owner exposure rollup:
   - summarize heating and cooling exposure by field mix
   - compute hotspot coverage percentages

It then writes:

1. `gold_portfolio_forecast_summary.parquet`
2. `gold_portfolio_forecast_segments.parquet`
3. `gold_portfolio_forecast_contributors.parquet`

That layer is one of the most important design choices in the system. It means the UI is not aggregating raw model outputs itself. ETL does the canonical aggregation once, with deterministic logic and coverage caveats.

Implementation references:

1. `etl/src/patentiq_etl/gold/build_gold.py:470-747`

## Backend API And Frontend View Traceability

The runtime path from trained model to user-facing screen is now explicit:

| Model lane | ETL or Gold artifact | Backend consumption | Frontend surface |
| --- | --- | --- | --- |
| Phase 03 family forecast | `ml_prediction_family_future_citations.parquet` and portfolio forecast Gold marts | `FamilyRepository.get_family_forecasts()`, `PortfolioService.get_forecast()` | family citation chronology overlay, portfolio forecast panel, portfolio citation outlook chart, compare forecast rows |
| Phase 04 lapse risk | `ml_prediction_family_jurisdiction_lapse_risk.parquet` and portfolio forecast Gold marts | `get_family_lapse_risk_rows()`, `get_owner_risk_distribution()`, portfolio forecast service | family forecast/legal section, portfolio risk-band mix, compare contributor and risk context |
| Pending-grant | `ml_prediction_pending_grant_pipeline.parquet` or owner-scoped cache | `get_owner_pending_grant_sections()` | portfolio pending-grant pipeline panel |
| Phase 06 trend | `ml_prediction_jurisdiction_field_trend_forecast.parquet`, `gold_portfolio_forecast_segments.parquet` | `get_owner_market_context()` | portfolio market-context and segment overlays |

The compare surfaces also consume forecast outputs directly. Family compare and portfolio compare both map `forecast_rows`, which means predictive outputs are not isolated to single-entity pages.

Implementation references:

1. `backend_v2/application/services/compare.py:421-485`
2. `backend_v2/application/services/compare.py:691-953`
3. `frontend_v2/lib/api/compare-v2.ts:187-201`
4. `frontend_v2/lib/api/compare-v2.ts:320-475`

## Current ML Claim Boundaries

The current solution distinguishes four different product-truth levels:

1. sealed candidate, interval-first:
   - Phase 03 family future citation forecast
2. sealed candidate, band-first:
   - Phase 04 family-jurisdiction lapse risk
3. candidate-only, rank-first:
   - pending-grant pipeline
4. sealed candidate, direction-band-first:
   - Phase 06 jurisdiction-field trend forecast

That difference is not cosmetic. It is encoded in:

1. model cards,
2. release decision notes,
3. backend caveats and support levels,
4. frontend wording and panel behavior.

So the correct standard is not "does every model pretend to be final production truth?" The correct standard is:

1. is each model technically reproducible,
2. is each model bounded by the right safe-use contract,
3. is the app honest about what is sealed, what is directional, and what remains candidate-only?

PatentIQ's V2 stack already answers those questions with explicit contracts instead of hiding them.

## Key Takeaways

1. PatentIQ's ML layer is not a disconnected experiment set. It is a governed ETL-owned artifact pipeline with explicit labels, features, splits, calibration, and promotion states.
2. The models do not train from raw patent tables directly. They train from curated Silver and Gold analytical marts whose lineage is documented in Section 01.
3. The strongest sealed MVP lanes today are Phase 03 family future citation outlook, Phase 04 lapse risk, and Phase 06 direction-first market trend.
4. Pending-grant is already wired into the portfolio workspace, but it is intentionally disclosed as candidate-only rank/percentile analytics rather than sealed probability truth.
5. Portfolio forecasts are bottom-up aggregations of micro predictions, not opaque company-level black boxes. That is why the backend and UI can show contributors, segment exposure, risk mix, and coverage caveats instead of only headline numbers.

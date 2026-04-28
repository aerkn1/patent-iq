# Reading Path And Document Map

## Purpose

Provide one ordered reading path for PatentIQ semantic and model development, so planning can move from base requirements to enriched roadmap to execution backlog without jumping between unrelated folders.

## Recommended Reading Order

### 1. Base Semantic Requirements

Read first:

- [semantic-similarity-and-vector-layer-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md)
- [semantic-mvp-without-uspto-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-mvp-without-uspto-requirements.md)

Use these for:

1. family-first semantic rules
2. vector-space separation
3. provenance rules
4. legal and chronology guardrails
5. MVP boundaries while claim coverage is incomplete

### 2. Base Forecast And Prediction Guardrails

Read second:

- [predictive-signals-and-interpretable-forecasting-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/predictive-signals-and-interpretable-forecasting-requirements.md)
- [15-patentiq-v2-prediction-training-flow-and-guardrails.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md)
- [08-citation-forecast-model-v2-retraining-report.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md)
- [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md)

Use these for:

1. allowed prediction scopes
2. training and calibration governance
3. split and leakage rules
4. portfolio aggregation rules
5. initial ship targets for family future citation forecast

### 3. Base Semantic Reliability Guardrails

Read third:

- [16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md)

Use this for:

1. semantic evaluation metrics
2. stop conditions
3. workflow-specific safe-use rules
4. MVP promotion logic

### 4. Article-driven Enrichment Layer

Read fourth:

- [README.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/README.md)
- [enriched-semantic-and-model-roadmap-from-2026-sciencedirect-findings.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-roadmap-from-2026-sciencedirect-findings.md)

Use these for:

1. justified scope expansion from recent literature
2. semantic graph and structured-summary directions
3. enriched model scope beyond the initial forecast inventory
4. future product expansion candidates

### 5. Execution Backlog

Read last:

- [enriched-semantic-and-model-implementation-runbook-backlog.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-implementation-runbook-backlog.md)

Use this for:

1. implementation phases
2. required data marts
3. expected artifacts
4. quality gates and thresholds
5. backlog order

## Practical Use

If the task is:

### semantic runtime implementation

Start with:

1. base semantic requirements
2. semantic reliability guardrails
3. runbook phases `0-2`

### family-first forecasting

Start with:

1. base forecast guardrails
2. citation forecast retraining note
3. runbook phases `0`, `3`, `4`, `5`, `8`

### longer-term research and product expansion

Start with:

1. article findings
2. enriched roadmap
3. runbook phases `6-9`

## Folder Roles

### `docs/new-feature-ideas/`

Use for:

1. core requirement notes
2. policy and design docs that are still broadly applicable across product areas

### `docs/new-feature-ideas/semantic-and-model-development/`

Use for:

1. semantic runtime planning
2. predictive model planning
3. article-driven enrichment
4. runbooks and execution backlogs specific to semantic and ML work

### `docs/ScienceDirect_articles_02Apr2026_07-45-31.440/article_findings/`

Use for:

1. article-by-article extraction notes
2. evidence source material behind the newer roadmap

## Current Recommended Execution Order

1. Phase 0: freeze inputs, fixtures, and split registries
2. Phase 1: promote semantic runtime
3. Phase 3: replace old appln-level forecast with family-first citation forecast
4. Phase 4: add lapse risk
5. Phase 5: add friction risk
6. Phase 8: derive portfolio prediction rollups from calibrated micro predictions
7. then return to the longer-range semantic topology and segment-intelligence phases

# Five-Week Roadmap

## Week 1: Foundation Freeze

### Objectives

1. Finalize scope.
2. Define canonical metrics and entities.
3. Stand up tests, fixtures, and release control basics.

### Deliverables

1. Source-to-feature traceability sheet.
2. Canonical metric contract document.
3. Small seeded demo dataset.
4. CI baseline for backend and frontend.
5. Feature flag plan for rebuilt analytics.
6. ML retraining design note: current weaknesses, target schema, and evaluation plan.

### Exit Criteria

1. Every contest metric has an owner and definition.
2. Every critical workflow has acceptance criteria.
3. Existing legacy metrics are classified as keep, rebuild, or drop.

## Week 2: Core Analytics Rebuild

### Objectives

1. Convert analytics logic to family-first defaults.
2. Add assignee harmonization baseline.
3. Rework citation-led ranking and trend logic.

### Deliverables

1. Family citation metrics and adjusted citation logic.
2. Priority-date trend backbone.
3. Filing momentum and grant mix endpoints.
4. Assignee harmonization service and basic parent mapping.
5. Updated API schemas with reliability metadata.
6. V2 training dataset spec and first robust feature marts for forecast retraining.

### Exit Criteria

1. Patent and portfolio core APIs run on rebuilt definitions.
2. Frontend can display family-default analytics without legacy assumptions.

## Week 3: Quality And Trend Reliability

### Objectives

1. Integrate OECD-compatible quality layer.
2. Add cohort normalization and caveat contracts.
3. Implement tech x market trend matrix.

### Deliverables

1. Family-level OECD indicator mart.
2. Cohort-normalized quality endpoint with `score_components`.
3. Pendency-adjusted grant-rate logic.
4. Lag and completeness metadata in trend endpoints.
5. Office-aware compatibility rules.
6. Baseline and challenger citation models trained on the V2 schema.

### Exit Criteria

1. No unsupported raw cross-cohort comparisons remain in UI/API.
2. Trend and quality analytics are reproducible and documented.

## Week 4: Strategic Workflows And Polish

### Objectives

1. Deliver the highest-value comparison and clustering workflows.
2. Add explainable AI assistance.
3. Improve report/export experience.

### Deliverables

1. Company comparison workspace.
2. Assignee-to-family comparison matrix.
3. Family and owner clustering by CPC/tech/market.
4. AI-generated cluster labels and draft insights with citations.
5. Contest-grade report/export flows.
6. Selected V2 citation model integrated with updated explainability payloads.

### Exit Criteria

1. Three polished demo workflows are stable:
   - single patent,
   - portfolio,
   - compare/market intelligence.

## Week 5: Hardening And Demo Readiness

### Objectives

1. Remove release risk.
2. Tune performance.
3. Prepare primary and fallback demo artifacts.

### Deliverables

1. Regression test pass.
2. Bug triage burn-down.
3. Warm-cache and cold-cache benchmark report.
4. Seeded demo scripts and screenshots.
5. Release candidate build and freeze.
6. Final ML validation report with calibration, subgroup checks, and rollback decision.

### Exit Criteria

1. The demo survives cache miss, partial-data, and degraded-mode scenarios.
2. Contest flows are rehearsed and documented.

## Milestone Decision Gates

### Gate 1: End of Week 1

Question:
Do we have enough definition stability to safely rebuild the stack?

### Gate 2: End of Week 2

Question:
Is the new metric foundation good enough to become default product behavior?

### Gate 3: End of Week 3

Question:
Are quality and trend caveats robust enough for judge scrutiny?

### Gate 4: End of Week 4

Question:
Do we have three compelling polished workflows, or are we still demoing disconnected features?

### Gate 5: Mid Week 5

Question:
Should any remaining feature flag stay off for the contest release?

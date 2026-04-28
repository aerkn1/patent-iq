# AI Agents Operating Model

## Purpose

Define how AI agents are used during delivery so they increase speed without reducing correctness.

## Agent Lanes

### Agent 1: Data Agent

Mission:
Own marts, normalization logic, family/entity mapping, and cohort calculations.

Inputs:
1. DuckDB and repository code,
2. OECD indicator files,
3. requirement specs.

Outputs:
1. SQL/data transformation changes,
2. validation datasets,
3. metric parity reports.

Guardrails:
1. Never change counting logic without updating contract metadata.
2. Always produce before/after sample outputs for golden cases.

### Agent 2: API Agent

Mission:
Refactor services and schemas into stable analytics contracts.

Inputs:
1. Service layer code,
2. repository outputs,
3. product contract definitions.

Outputs:
1. New response schemas,
2. endpoint refactors,
3. feature-flagged rollout paths.

Guardrails:
1. No silent breaking changes.
2. Every endpoint must declare reliability metadata when relevant.

### Agent 3: Frontend Agent

Mission:
Translate rebuilt analytics into understandable, judge-friendly workflows.

Inputs:
1. API schemas,
2. product workstream docs,
3. existing component library.

Outputs:
1. Page and component changes,
2. compare workspaces,
3. report/export UI.

Guardrails:
1. No UI that hides uncertainty.
2. Do not surface data combinations the backend does not formally support.

### Agent 4: QA Agent

Mission:
Continuously test correctness, regressions, and demo resilience.

Inputs:
1. Fixtures,
2. golden metric outputs,
3. critical user flows.

Outputs:
1. Test suites,
2. defect reports,
3. release gate status.

Guardrails:
1. Block release on metric-definition regressions.
2. Keep a minimal but strict set of smoke tests for every contest workflow.

### Agent 5: Demo Agent

Mission:
Own seeded data, contest story, backup assets, and rehearsal support.

Inputs:
1. Stable app screens,
2. export capabilities,
3. benchmark results.

Outputs:
1. Demo scripts,
2. screenshots and backups,
3. contest deck material.

Guardrails:
1. Demo should not depend on unstable live conditions.
2. Every shown claim should be reproducible in the product.

### Agent 6: Modeling Agent

Mission:
Own citation forecast retraining, model selection, calibration, explainability outputs, and inference handoff.

Inputs:
1. V2 feature marts,
2. historical citation labels,
3. evaluation targets and quality gates.

Outputs:
1. Retrained models,
2. calibration artifacts,
3. model card and validation report,
4. inference feature contract.

Guardrails:
1. No production model without leakage checks and subgroup validation.
2. No final model choice based on one metric alone.
3. No explainability claim unless the serving path can expose supporting outputs.

## Cross-Agent Handshake Rules

1. Data Agent publishes a metric definition note before API integration starts.
2. API Agent publishes sample payloads before Frontend Agent consumes them.
3. QA Agent adds goldens before feature flags are switched on by default.
4. Modeling Agent publishes a model card before inference integration begins.
5. Demo Agent only uses flows that passed the previous gate.

## Required Artifacts Per Task

Every substantial task should leave behind:

1. Definition or schema change note,
2. sample input/output,
3. validation method,
4. rollback or fallback path.

## AI Usage Policy

### Good uses

1. SQL and aggregation draft generation,
2. code refactor acceleration,
3. cluster label drafting,
4. narrative summarization with evidence links,
5. regression diff analysis.

### Bad uses

1. Final scoring without deterministic logic,
2. unsupported factual claims,
3. hiding uncertainty in natural-language summaries,
4. changing methodology without explicit approval.

## Daily Operating Rhythm

1. Morning: define target outcomes and blocking risks.
2. Midday: merge validated outputs from agent lanes.
3. End of day: run smoke tests, benchmark key paths, update gate status.

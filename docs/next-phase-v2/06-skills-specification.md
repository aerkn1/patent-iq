# Skills Specification

## Purpose

Define reusable internal skills for the 5-week delivery effort. These are not product features; they are execution accelerators for the team and AI agents.

## Skill Design Principles

1. Each skill should be narrow, reusable, and tied to a recurring workflow.
2. The skill should encode decisions the team wants repeated consistently.
3. Detailed references belong in bundled resources, not bloated skill bodies.
4. Each skill must have clear trigger conditions and expected outputs.

## Proposed Skill Set

### Skill 1: `patent-quality-gate`

Purpose:
Run metric validation for family-first analytics, OECD normalization, and trend caveats before a feature is accepted.

When to use:
1. Any metric contract change,
2. any new trend or ranking endpoint,
3. any score exposed in UI.

Required workflow:
1. Validate counting unit and family model,
2. verify raw vs adjusted citation outputs,
3. verify cohort normalization where applicable,
4. check metadata fields and caveats,
5. emit pass/fail summary.

Expected outputs:
1. Validation checklist,
2. edge-case results,
3. release-blocking issues.

Suggested bundled resources:
1. Golden fixtures,
2. sample payload contracts,
3. OECD normalization reference cases.

### Skill 2: `contest-release-runbook`

Purpose:
Guide the final release process for demo-safe builds, fallback artifacts, and gate verification.

When to use:
1. Release candidate preparation,
2. demo rehearsals,
3. contest week packaging.

Required workflow:
1. Verify build, test, and benchmark status,
2. confirm seeded demo data,
3. confirm primary and fallback demo paths,
4. confirm screenshots and exports exist,
5. confirm feature-flag decisions.

Expected outputs:
1. Go/no-go checklist,
2. final demo asset pack,
3. residual-risk summary.

Suggested bundled resources:
1. Demo script template,
2. release checklist,
3. fallback scenario playbook.

### Skill 3: `family-intelligence-contracts`

Purpose:
Standardize how new family-first analytics endpoints and schemas are designed.

When to use:
1. New patent or portfolio analytics endpoint work,
2. compare-workspace API design,
3. clustering or ranking contract additions.

Required workflow:
1. Declare entity grain,
2. declare counting unit,
3. declare reliability metadata,
4. declare evidence fields,
5. produce example response.

Expected outputs:
1. Contract skeleton,
2. example payloads,
3. compatibility notes.

Suggested bundled resources:
1. Schema templates,
2. response examples,
3. metadata glossary.

### Skill 4: `portfolio-demo-story-builder`

Purpose:
Create concise evidence-backed demo narratives for patent, portfolio, and compare workflows.

When to use:
1. Contest deck prep,
2. report/export copy,
3. judge demo rehearsal.

Required workflow:
1. Pick one workflow,
2. extract 3-5 evidence-backed claims,
3. attach caveats where needed,
4. produce short script and backup screenshot list.

Expected outputs:
1. Demo talk track,
2. visual sequence,
3. claim-to-evidence map.

Suggested bundled resources:
1. Slide outline,
2. screenshot storyboard,
3. claim review checklist.

### Skill 5: `citation-model-retrain`

Purpose:
Guide the end-to-end retraining workflow for the citation forecast models on the V2 feature schema.

When to use:
1. Building new training tables,
2. running model experiments,
3. selecting the release candidate model,
4. regenerating calibration artifacts.

Required workflow:
1. Validate feature table contract and split integrity,
2. train baseline and challenger models,
3. evaluate ranking, error, and calibration metrics,
4. run subgroup and leakage checks,
5. emit a model card and go/no-go recommendation.

Expected outputs:
1. Experiment summary,
2. selected model artifacts,
3. calibration report,
4. known limitations list.

Suggested bundled resources:
1. Feature manifest template,
2. model card template,
3. evaluation script checklist,
4. subgroup validation matrix.

## Suggested Minimal Skill Folder Shape

```text
skill-name/
├── SKILL.md
├── agents/openai.yaml
├── references/
└── assets/ or scripts/ when needed
```

## Skill Acceptance Criteria

1. The trigger condition is obvious from the description.
2. The workflow is short enough to be reused frequently.
3. The skill reduces repeated reasoning or repeated mistakes.
4. The skill has clear outputs that a reviewer can verify.

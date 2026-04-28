# Section 07. Release Packaging, Auditability, Testing, And Submission Compliance

## Table Of Contents

1. [Purpose Of This Section](#purpose-of-this-section)
2. [What Counts As A Release In PatentIQ V2](#what-counts-as-a-release-in-patentiq-v2)
3. [Current Runtime Baseline On Exact Dates](#current-runtime-baseline-on-exact-dates)
4. [Config-First ETL Release Orchestration](#config-first-etl-release-orchestration)
   - [1. Build settings are externalized](#1-build-settings-are-externalized)
   - [2. Full ETL execution order is explicit](#2-full-etl-execution-order-is-explicit)
   - [3. Release gating starts before publish](#3-release-gating-starts-before-publish)
5. [Serving Snapshot Packaging](#serving-snapshot-packaging)
   - [1. Serving is a formal ETL stage](#1-serving-is-a-formal-etl-stage)
   - [2. Current serving snapshot produced on April 25, 2026](#2-current-serving-snapshot-produced-on-april-25-2026)
   - [3. Serving audit evidence](#3-serving-audit-evidence)
6. [Full Publish Release Versus Runtime Release](#full-publish-release-versus-runtime-release)
   - [1. Full publish release](#1-full-publish-release)
   - [2. Runtime-only release manifest and upload plan](#2-runtime-only-release-manifest-and-upload-plan)
   - [3. Current live runtime release on April 26, 2026](#3-current-live-runtime-release-on-april-26-2026)
7. [Runtime Bootstrap And Environment Parity](#runtime-bootstrap-and-environment-parity)
   - [1. Local Docker Compose path](#1-local-docker-compose-path)
   - [2. Bootstrap materialization logic](#2-bootstrap-materialization-logic)
   - [3. Backend runtime resolution](#3-backend-runtime-resolution)
   - [4. Frontend runtime resolution](#4-frontend-runtime-resolution)
   - [5. Azure Container Apps parity](#5-azure-container-apps-parity)
8. [Auditability And Trace Evidence](#auditability-and-trace-evidence)
9. [Testing And Validation Surface](#testing-and-validation-surface)
   - [1. ETL tests](#1-etl-tests)
   - [2. Backend tests](#2-backend-tests)
   - [3. Frontend tests](#3-frontend-tests)
   - [4. CI and release governance workflows](#4-ci-and-release-governance-workflows)
   - [5. Target state versus current implemented state](#5-target-state-versus-current-implemented-state)
10. [Submission Compliance Mapping Against The Organizer Rules](#submission-compliance-mapping-against-the-organizer-rules)
11. [Current Caveats And Honest Gaps](#current-caveats-and-honest-gaps)
12. [Key Takeaways](#key-takeaways)

## Purpose Of This Section

Sections 01 through 06 explained how PatentIQ derives analytics, serves them through the backend, and renders them in the V2 frontend. This section answers a different documentation question:

When the team says the solution is "submission-ready", what exactly gets released, how is it packaged, how can that package be audited, what tests protect it, and how close is the repository to the contest's formal submission rules?

This section therefore focuses on:

1. release structure,
2. runtime bootstrap mechanics,
3. machine-readable audit artifacts,
4. current test coverage around release behavior,
5. compliance mapping against the organizer instructions shared by the team.

Primary implementation references:

1. `etl/scripts/run_full_build.py:29-73`
2. `etl/src/patentiq_etl/bronze/certify.py:242-397`
3. `etl/src/patentiq_etl/serving/run.py:2214-2455`
4. `etl/src/patentiq_etl/publish/run.py:34-401`
5. `etl/src/patentiq_etl/publish/runtime_release.py:45-225`
6. `etl/scripts/bootstrap_runtime_artifacts.py:14-222`
7. `etl/scripts/bootstrap_runtime_artifacts.py:271-532`
8. `backend_v2/config/settings.py:22-132`
9. `backend_v2/infrastructure/artifacts/locator.py:29-237`
10. `compose.yaml:1-70`
11. `frontend_v2/scripts/start_container.sh:4-32`
12. `azure/backend.app.yaml:12-142`
13. `azure/frontend.app.yaml:8-47`

## What Counts As A Release In PatentIQ V2

In PatentIQ V2, a release is not only a Git state or a deployed container tag. It is a synchronized artifact contract across ETL, serving, vectors, ML assets, runtime manifests, and an active pointer.

There are three related but distinct release layers:

1. The configured ETL build context.
   This is the typed `BuildSettings` object loaded from `build.yaml`, `scope.yaml`, `azure.yaml`, and `thresholds.yaml`, including release id, snapshot date, source modes, execution flags, and bounded scope definition in `etl/src/patentiq_etl/common/config.py:17-84`.

2. The full published ETL release.
   This is the staged release directory under `etl/data/releases/<release_id>/` containing `bronze`, `silver`, `gold`, `models`, `vectors`, and `serving`, written by the `publish` stage in `etl/src/patentiq_etl/publish/run.py:92-214` and `306-401`.

3. The runtime release profile.
   This is the subset of the full release that the actual application needs at startup, described by `release-manifest.json`, `active_release.json`, and `runtime-upload-plan.json`, then hydrated into `/artifacts/current` by `etl/src/patentiq_etl/publish/runtime_release.py:164-225` and `etl/scripts/bootstrap_runtime_artifacts.py:337-532`.

This distinction matters because PatentIQ separates:

1. rebuild/archive assets for reproducibility,
2. serving-safe runtime assets for application latency,
3. bootstrap metadata for local and Azure parity.

## Current Runtime Baseline On Exact Dates

The repository currently contains a concrete released runtime baseline, not just abstract design notes.

The exact release evidence is:

1. serving snapshot manifest built at `2026-04-25T20:53:57Z` with `serving_release = 2026-04-25-serving` in `etl/data/serving/serving_snapshot_manifest.json:1-110`,
2. runtime release manifest built at `2026-04-26T13:04:58+00:00` with `release_id = 2026-04-25-runtime-current` in `etl/manifests/releases/2026-04-25-runtime-current/release-manifest.json:1-186`,
3. runtime upload plan generated at the same time in `etl/manifests/releases/2026-04-25-runtime-current/runtime-upload-plan.json:1-220`.

Current runtime artifact footprint:

| Runtime artifact group | Current size | File count | Evidence | Why it matters |
| --- | --- | --- | --- | --- |
| `serving` | `95,858,533,797` bytes | `1030` files | `release-manifest.json:14-25` | main backend runtime truth |
| `vectors` | `15,701,700,428` bytes | `589` files | `release-manifest.json:20-25` | semantic search and compare runtime |
| `models` | `9,964,583,947` bytes | `99` files | `release-manifest.json:8-13` | model cards, prediction assets, and current ML directory contract |

Current runtime profile split:

1. `default` profile includes `core_serving.duckdb`, `market_serving.duckdb`, `semantic_serving.duckdb`, `publication_serving/`, the serving manifest and audit files, vector payloads, and the full `models/` directory in `release-manifest.json:29-78`.
2. `full` profile adds `analytics_serving.duckdb`, ANN manifests, ANN audit, and the `vectors/ann` directory in `release-manifest.json:79-144`.

Current semantic dependency declaration:

1. abstract semantic model: `BAAI/bge-m3`,
2. claims semantic model: `AI-Growth-Lab/PatentSBERTa`,
3. both currently have `revision: null`, which is a real and documented caveat in `release-manifest.json:158-185`.

## Config-First ETL Release Orchestration

### 1. Build settings are externalized

PatentIQ does not hardcode release scope, source families, or artifact roots inside stage logic. The ETL entrypoint loads four external configuration files and converts them into one typed runtime settings object in `etl/src/patentiq_etl/common/config.py:17-84`.

This matters because the same build system can express:

1. exact snapshot date and release id,
2. selected 10-field bounded scope,
3. source family modes such as TIP and local files,
4. Azure publishing flags and execution toggles.

The settings contract is also tested directly. `etl/tests/test_source_certification.py:8-24` asserts the live repo configuration still resolves the intended `mega_cluster_bounded` scope, 10 WIPO fields, `2007-2026` main window, `1996-2006` heritage window, and the expected PATSTAT/Register/EPAB source-mode contract.

### 2. Full ETL execution order is explicit

The canonical end-to-end ETL order is not hidden inside notebooks or ad hoc shell scripts. It is spelled out in `etl/scripts/run_full_build.py:50-73`:

1. `source-certification`
2. optional chunk planning
3. `prebronze`
4. optional heritage-support stages
5. `bronze`
6. `scope`
7. `silver`
8. `gold`
9. `ml`
10. `semantic`
11. `release-certification`
12. `publish`

After each stage, `_persist()` writes:

1. a stage stats JSON under `etl/manifests/stats/`,
2. a stage manifest JSON under `etl/manifests/stages/`,
3. a human-readable journal entry in `ETL_IMPLEMENTATION_LOG.md`,

as implemented in `etl/scripts/run_full_build.py:29-37`.

### 3. Release gating starts before publish

PatentIQ treats release validity as a data-quality and artifact-completeness problem, not only a deployment problem.

`certify_sources()` checks:

1. PATSTAT, Register, refs, and EPAB availability,
2. required-column presence,
3. 10-field scope representability,
4. degrade/fail rules for missing full-text or Register overlays,
5. configured source-access prerequisites when externalized stages are enabled,

in `etl/src/patentiq_etl/bronze/certify.py:242-349`.

`certify_release()` then checks:

1. required artifact roots exist,
2. Bronze, Silver, and Gold are non-empty parquet layers,
3. stage manifests exist before promotion,

in `etl/src/patentiq_etl/bronze/certify.py:352-397`.

This is important release evidence. The repo does not assume that if code ran once, the output is automatically releasable.

## Serving Snapshot Packaging

### 1. Serving is a formal ETL stage

Serving packaging is not performed lazily by the backend. It is a first-class ETL stage called `serving-snapshots`, exactly as the design contract requires in `docs/next-phase-v2/41-patentiq-v2-etl-serving-snapshots-packaging-contract.md:22-90`.

The implementation entrypoint `build_serving_snapshots()`:

1. reads Gold, Silver, Bronze, and ML inputs,
2. materializes domain-split serving artifacts,
3. creates serving-derived convenience tables such as `family_compare_current_serving` and `portfolio_classification_current_serving`,
4. emits `serving_snapshot_manifest.json` and `serving_snapshot_audit.json`,

as implemented in `etl/src/patentiq_etl/serving/run.py:2214-2455`.

The built serving domains are:

1. `core_serving.duckdb`
2. `analytics_serving.duckdb`
3. `semantic_serving.duckdb`
4. `market_serving.duckdb`
5. `publication_serving/`

The publication surface is intentionally a directory artifact, not one giant DuckDB file, so publication evidence can be sharded and point-looked up safely in `etl/src/patentiq_etl/serving/run.py:2248-2250` and `2257-2258`.

### 2. Current serving snapshot produced on April 25, 2026

The current live serving manifest shows five released serving domains:

| Serving artifact | Current bytes | Current tables | Evidence |
| --- | --- | --- | --- |
| `analytics_serving.duckdb` | `72,023,027,712` | `49` tables | `serving_snapshot_manifest.json:6-61` |
| `core_serving.duckdb` | `11,011,633,152` | `15` tables | `serving_snapshot_manifest.json:62-82` |
| `market_serving.duckdb` | `798,720` | `3` tables | `serving_snapshot_manifest.json:83-91` |
| `publication_serving/` | `11,916,574,065` | `4` shard families | `serving_snapshot_manifest.json:92-101` |
| `semantic_serving.duckdb` | `906,768,384` | `1` table | `serving_snapshot_manifest.json:102-108` |

This is exactly the kind of artifact packaging expected for a UI-driven analytical platform:

1. core and market stay lightweight,
2. heavy historical and detail surfaces move into `analytics_serving.duckdb`,
3. publication evidence is separately sharded,
4. semantic context is isolated from embeddings and ANN binaries.

### 3. Serving audit evidence

The serving audit file is more than a manifest. It captures per-table row and column counts.

Examples from `etl/data/serving/serving_snapshot_audit.json:1-240`:

1. `family_summary`: `17,633,618` rows in analytics, `39` columns,
2. `family_compare_pit`: `164,988,135` rows,
3. `family_oecd_quality`: `21,353,101` rows,
4. `portfolio_summary`: `3,034,400` rows,
5. `portfolio_forecast_contributors`: `17,866,740` rows,
6. `pending_grant_prediction_pipeline`: `9,665,749` rows,
7. `market_summary_pit`: `504` rows.

This audit output is a major supporting artifact because it allows direct inspection of:

1. whether page-facing marts are populated,
2. whether historical layers have realistic scale,
3. whether the serving payload looks internally consistent with the bounded scope described in Section 01.

The packaging path itself is tested. `etl/tests/test_serving_snapshots_stage.py:618-760` asserts that the serving stage writes all snapshot files, produces both manifest and audit JSONs, includes expected core and publication tables, preserves sharded publication partitions, and materializes serving-derived tables like `family_compare_current_serving`.

## Full Publish Release Versus Runtime Release

### 1. Full publish release

The `publish` stage creates a full release directory rooted at `etl/data/releases/<release_id>/`. It copies:

1. `bronze`
2. `silver`
3. `gold`
4. `models`
5. `vectors`
6. `serving`

from the working ETL tree into a staged release in `etl/src/patentiq_etl/publish/run.py:34-43` and `92-193`.

The publish stage also:

1. stages into a temporary directory first,
2. refuses overwrite unless explicit flags are enabled,
3. writes `release-manifest.json`,
4. writes `etl/manifests/releases/active_release.json`,
5. optionally uploads the release to Azure Blob,
6. writes `publish.log` and `publish.events.jsonl`,

in `etl/src/patentiq_etl/publish/run.py:15-31`, `115-190`, and `306-401`.

The publish contract is tested in `etl/tests/test_publish_release.py:73-130`, which verifies:

1. serving and nested vector artifacts are included,
2. `release-manifest.json` carries serving and semantic dependency metadata,
3. overwrite is refused by default.

### 2. Runtime-only release manifest and upload plan

PatentIQ also supports a narrower runtime-only release manifest path. This is useful when the team wants to promote the current runtime payload without restaging the full archive release again.

`prepare_runtime_release_manifest()`:

1. summarizes `serving`, `vectors`, and `models`,
2. writes `release-manifest.json`,
3. writes a runtime `active_release.json`,
4. writes `runtime-upload-plan.json`,

in `etl/src/patentiq_etl/publish/runtime_release.py:164-225`.

The upload plan enumerates every file or directory that must be transferred, including the activation pointer written last, in `etl/src/patentiq_etl/publish/runtime_release.py:79-161`.

This exactly matches the operational runbook in `docs/next-phase-v2/92-patentiq-v2-runtime-release-manual-upload-runbook.md:18-152`, which prescribes:

1. generate runtime manifest,
2. upload `releases/<release_id>/...`,
3. verify counts and bytes against `runtime-upload-plan.json`,
4. upload `manifests/active_release.json` last.

`etl/tests/test_runtime_release.py:71-132` verifies that the runtime manifest generator:

1. carries the serving release id,
2. includes publication-serving directory entries,
3. includes vector and ANN assets where appropriate,
4. currently includes `_tmp_phase08_phase04_latest_features.parquet` in the upload plan if it exists.

### 3. Current live runtime release on April 26, 2026

The current runtime release manifest is concrete and readable in `etl/manifests/releases/2026-04-25-runtime-current/release-manifest.json:1-186`.

Important current truths:

1. `release_id` is `2026-04-25-runtime-current`,
2. `artifact_root` is `releases/2026-04-25-runtime-current`,
3. `serving_release` is `2026-04-25-serving`,
4. the active bounded scope still lists the intended 10 WIPO fields,
5. the runtime contract distinguishes `default` and `full` profiles,
6. semantic Hugging Face model dependencies are declared but not pinned to specific revisions.

The current upload plan in `runtime-upload-plan.json:122-220` also proves one honest caveat: the runtime `models/` directory still contains non-runtime ML leftovers such as `_tmp_phase08_phase04_latest_features.parquet` and yearly `phase04` prediction shards. This is also documented as deliberate for now in `docs/next-phase-v2/92-patentiq-v2-runtime-release-manual-upload-runbook.md:150-152`.

## Runtime Bootstrap And Environment Parity

### 1. Local Docker Compose path

The repository now contains an implemented `compose.yaml`, not only a future deployment note.

`compose.yaml:1-70` defines:

1. `artifact-init`
2. `backend`
3. `frontend`

The compose contract wires:

1. `/artifacts` as the shared runtime volume,
2. `/hf-home` as the shared Hugging Face cache,
3. local release bootstrap by default,
4. container-local backend serving from `/artifacts/current/serving`,
5. frontend-to-backend URL injection through `NEXT_PUBLIC_API_BASE_URL`.

Important live nuance:

1. backend settings default `raw_parquet_fallback_enabled` to `False` in `backend_v2/config/settings.py:51-69`,
2. but the current compose runtime sets `PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED=true` in `compose.yaml:45-53`,
3. so the production architecture is serving-first, but the containerized local runtime still keeps a fallback path enabled for resilience.

### 2. Bootstrap materialization logic

`etl/scripts/run_artifact_init.sh:6-105` is the operator-facing wrapper around runtime hydration. It:

1. reads bootstrap env vars,
2. routes to local-release or Azure-blob mode,
3. optionally enables HF prefetch,
4. prints target, profile, and cache paths,
5. prints the final `.bootstrap-state.json`.

The underlying Python bootstrap implementation in `etl/scripts/bootstrap_runtime_artifacts.py:271-532` then:

1. resolves the release manifest from either a local active pointer or an Azure active blob,
2. validates the selected runtime profile,
3. stages files into a temporary directory,
4. writes `.bootstrap-state.json`,
5. atomically swaps `/artifacts/current` via symlink replace,
6. refuses overwrite unless explicitly enabled.

This atomic promote step is implemented in `etl/scripts/bootstrap_runtime_artifacts.py:321-334`.

Bootstrap behavior is also tested directly. `etl/tests/test_bootstrap_runtime_artifacts.py:26-72` verifies local release materialization into the mount-safe layout and symlink promotion to `current`. `etl/tests/test_bootstrap_runtime_artifacts.py:75-121` verifies Hugging Face dependency prefetch behavior.

### 3. Backend runtime resolution

The backend runtime contract is implemented in three layers:

1. configuration defaults in `backend_v2/config/settings.py:22-132`,
2. serving artifact resolution in `backend_v2/infrastructure/artifacts/locator.py:29-237`,
3. startup logging and environment normalization in `backend_v2/scripts/start_container.sh:7-58`.

The backend can resolve serving artifacts from:

1. local filesystem,
2. a remote manifest URL with cached downloads,
3. direct path or URL overrides for individual serving snapshots.

That logic is not only architectural prose. It is implemented in `ArtifactLocator.resolve_serving_manifest()` and `_resolve_snapshot()` in `backend_v2/infrastructure/artifacts/locator.py:89-207`.

The runtime resolution path is tested in `backend_v2/tests/test_artifact_locator.py:8-208`, including:

1. local manifest resolution,
2. cached remote materialization through `file:` URLs,
3. resolution of core, analytics, market, semantic, and publication serving artifacts.

### 4. Frontend runtime resolution

The frontend follows the same parity principle. The image is built once, and the runtime API base URL is injected at container start.

The runtime write step is implemented in `frontend_v2/scripts/start_container.sh:4-32`, which writes `public/runtime-config.js` from `NEXT_PUBLIC_API_BASE_URL`.

The browser-side resolution path is implemented in `frontend_v2/lib/config.ts:1-58`:

1. prefer `window.__PATENTIQ_RUNTIME_CONFIG__.apiBaseUrl`,
2. then `NEXT_PUBLIC_API_BASE_URL`,
3. then localhost in non-production development,
4. rewrite localhost to `host.docker.internal` when needed in browser-bridge mode.

The produced runtime config stub is deliberately simple in `frontend_v2/public/runtime-config.js:1`.

This design allows the same standalone frontend build in `frontend_v2/next.config.mjs:3-8` to work across local compose and Azure.

### 5. Azure Container Apps parity

The Azure deployment manifests mirror the same contract instead of inventing a different runtime shape.

`azure/backend.app.yaml:12-142` shows:

1. an `artifact-init` init container,
2. `/artifacts/current` as the backend data root,
3. `/hf-home` as the shared model cache,
4. `PATENTIQ_V2_SERVING_MANIFEST_PATH=/artifacts/current/serving/serving_snapshot_manifest.json`,
5. the same `PATENTIQ_BOOTSTRAP_*` variables used locally,
6. current live choice `PATENTIQ_BOOTSTRAP_ALLOW_UNPINNED_HF_MODELS=true`.

`azure/frontend.app.yaml:8-47` shows the same frontend image strategy, with only `NEXT_PUBLIC_API_BASE_URL` changing.

So the parity story is technically strong:

1. same backend code,
2. same frontend code,
3. same runtime manifest semantics,
4. same release pointer pattern,
5. only environment values and storage backends differ.

## Auditability And Trace Evidence

PatentIQ has multiple audit layers, each answering a different question.

1. Stage manifest JSONs answer "what stage ran and with what status?" via `etl/src/patentiq_etl/common/manifest.py:20-28`.
2. Stage stats JSONs answer "what metrics and output artifact profiles were produced?" via `etl/src/patentiq_etl/common/stats.py:11-48`.
3. The markdown ETL journal answers "how should a human understand the stage, its methods, warnings, and downstream impacts?" via `etl/src/patentiq_etl/common/journal.py:18-53`.
4. The publish event stream answers "what copy and upload operations happened during release assembly?" via `etl/src/patentiq_etl/publish/run.py:15-31` and `306-399`.
5. Serving manifest and serving audit answer "what exactly is inside the serving runtime?" via `etl/src/patentiq_etl/serving/run.py:2395-2445`.
6. Runtime release manifest and upload plan answer "what exact runtime payload should be transferred and bootstrapped?" via `etl/src/patentiq_etl/publish/runtime_release.py:175-225`.
7. Bootstrap state answers "which release was materialized into the mounted runtime and when?" via `etl/scripts/bootstrap_runtime_artifacts.py:389-407` and `505-524`.

This is closely aligned with the audit contract described in `docs/next-phase-v2/27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md:12-69` and `183-190`.

For code review, this layered audit model is important because it reduces the need to trust verbal claims. It makes it possible to inspect:

1. build configuration,
2. stage manifests,
3. stage stats,
4. release manifests,
5. serving manifests,
6. runtime upload plans,
7. bootstrap logs and state.

## Testing And Validation Surface

As of the current repository state on `2026-04-26`, the automated surface includes:

1. `29` ETL test files under `etl/tests/`,
2. `18` backend V2 test files under `backend_v2/tests/`,
3. one focused frontend Playwright smoke/accessibility spec plus support helpers under `frontend_v2/tests/e2e/`.

### 1. ETL tests

The ETL test suite includes direct coverage of release and audit machinery, not only metric builders.

Representative examples:

1. `etl/tests/test_source_certification.py:8-24` checks live settings resolve the intended bounded scope and source-mode contract.
2. `etl/tests/test_stage_stats.py:9-45` checks stage stats JSON emission and directory output profiling.
3. `etl/tests/test_serving_snapshots_stage.py:618-760` checks serving snapshot materialization, manifest shape, audit shape, and partitioned publication outputs.
4. `etl/tests/test_publish_release.py:73-130` checks full publish release packaging and overwrite safety.
5. `etl/tests/test_runtime_release.py:71-132` checks runtime release manifest generation and upload plan contents.
6. `etl/tests/test_bootstrap_runtime_artifacts.py:26-121` checks runtime materialization and Hugging Face dependency prefetch.

This means release packaging is not an untested operational side path. It is part of the implemented test surface.

### 2. Backend tests

The backend V2 tests span:

1. settings defaults,
2. artifact locator behavior,
3. repositories,
4. services,
5. endpoint forwarding and contract stability.

Representative examples:

1. `backend_v2/tests/test_settings.py:4-9` verifies base runtime defaults.
2. `backend_v2/tests/test_artifact_locator.py:8-208` verifies local and cached artifact resolution.
3. `backend_v2/tests/test_compare_endpoints.py:11-180` verifies compare endpoint parameter forwarding and response contract shape.
4. `backend_v2/tests/test_semantic_endpoints.py:11-189` verifies semantic search and compare endpoint parameter forwarding.

The backend dependency manifest is also explicit and machine-readable in `backend_v2/pyproject.toml:1-26`.

### 3. Frontend tests

The frontend test surface is smaller but purposeful. `frontend_v2/playwright.config.ts:8-38` runs a built application with a fixed base URL and controlled API base URL injection.

`frontend_v2/tests/e2e/smoke.spec.ts:55-218` covers:

1. home route,
2. portfolio entry search,
3. market workspace segment switching,
4. portfolio overview, citations, technology, and forecast tabs,
5. family workspace,
6. publication workspace,
7. family-to-publication navigation,
8. route-level accessibility checks and additional portfolio-tab accessibility checks.

This is not a full UI regression matrix, but it does cover the visible V2 surfaces that matter most.

### 4. CI and release governance workflows

The repository currently includes three GitHub Actions workflows:

1. `validate-pr-source.yml` enforces branch-flow rules: PRs to `master` must come from `dev`, and PRs to `prod` must come from `master`, as implemented in `.github/workflows/validate-pr-source.yml:1-34`.
2. `semantic-release.yml` performs release automation on `master` and then bumps the next `dev` version, as implemented in `.github/workflows/semantic-release.yml:1-115`.
3. `dev-snapshot.yml` enforces a `.dev0` suffix on the `dev` branch version, as implemented in `.github/workflows/dev-snapshot.yml:1-47`.

These workflows are governance and versioning safeguards. They are useful, but they do not yet represent a full automated quality gate for all ETL, backend, and frontend tests.

### 5. Target state versus current implemented state

The older testing strategy document still states a stronger future-state goal than the live CI now proves:

1. target `80%` code coverage,
2. testing pyramid `75% unit / 20% integration / 5% e2e`,
3. automated CI/CD test execution and coverage reports,

in `docs/project/testing_strategy.md:16-44`.

That target state should not be confused with the present implementation state.

Current reality is:

1. meaningful automated tests exist for ETL release packaging, backend contracts, and frontend smoke/accessibility,
2. release governance workflows exist,
3. but the repo does not yet expose a documented always-on full test matrix or published coverage report inside the current GitHub workflows.

This is not a failure of architecture. It is a documentation and automation maturity gap that should be described honestly.

## Submission Compliance Mapping Against The Organizer Rules

The table below maps the organizer instructions shared by the team to evidence already present in the repository and to the remaining manual work still needed before final submission.

| Organizer requirement | Evidence already present in repo | Current status | Remaining action before submission |
| --- | --- | --- | --- |
| `1. comply with the Rules of Competition and, if used, with the terms and conditions of the EPO Patent Knowledge Products and Services` | Source-mode and certification logic explicitly model TIP-backed PATSTAT/Register/EPAB plus reference inputs in `etl/src/patentiq_etl/common/config.py:17-84` and `etl/src/patentiq_etl/bronze/certify.py:242-349` | Partially evidenced | Add final legal/terms appendix confirming usage mode for each EPO source and any access restrictions |
| `2. disclose employer and affiliations` | No dedicated disclosure artifact found in current repo | Missing | Add explicit employer/affiliation appendix in Section 08 or submission root |
| `3. comply with all software/service/material terms and conditions` | Machine-readable dependency manifests exist in `etl/pyproject.toml:1-32`, `backend_v2/pyproject.toml:1-26`, and `frontend_v2/package.json:1-60` | Partially evidenced | Produce one consolidated third-party dependency and license inventory |
| `4. not infringe third-party intellectual property rights` | Data lineage, source certification, and artifact traceability are documented throughout Sections 01-07 and implemented in ETL manifests and audits | Partially evidenced | Add final provenance statement and dependency license appendix |
| `5. not contain malicious, corrupt, or damaged code or backdoors` | Startup, bootstrap, publish, and artifact resolution paths are explicit and logged in `etl/scripts/run_artifact_init.sh:6-105`, `etl/scripts/bootstrap_runtime_artifacts.py:271-532`, `etl/src/patentiq_etl/publish/run.py:306-401`, and `backend_v2/scripts/start_container.sh:21-58` | Inspection-based support, not formal proof | Run final static/security scans and include their report or summary |
| `6. not contain unlawful, illegal, fraudulent, harassing, threatening, offensive, or harmful content` | Current repo contents are technical code, configs, manifests, and documentation; no runtime content-generation corpus was found in the inspected release path | Likely satisfied | Perform final manual content review before packaging |
| `7. not disparage the Event, Sponsor, or others` | Current docs are technical and product-focused | Likely satisfied | Final editorial review before submission |
| `8. not violate law or third-party rights including data protection and privacy` | The implementation is built around patent/publication/register/legal-event sources and auditable source certification rather than personal-data workflows | Partially evidenced | Add short legal/privacy statement confirming data classes used and why they are appropriate |
| `9. include freshly developed code during the competition window and only free-of-charge dependent libraries` | Dependency manifests are present and open-source usage is machine-readable; branch and release governance workflows exist in `.github/workflows/*.yml` | Not fully evidenced from repo snapshot alone | Attach commit-history proof for the contest window and finalize the dependency-license inventory |

There is also a broader submission-completeness requirement outside the numbered rule list: the package must include source code, datasets/collateral materials, prompts where applicable, and tools used to build or generate the solution.

Current repo support for that requirement is strong but incomplete:

1. source code is present and structured,
2. data artifacts and manifests are machine-readable (`.parquet`, `.duckdb`, `.json`, `.yaml`),
3. build and runtime tools are machine-readable through `pyproject.toml`, `package.json`, Dockerfiles, `compose.yaml`, and Azure YAML,
4. prompt disclosure is not yet consolidated into one submission appendix,
5. a final commented-source pass is still advisable before packaging.

## Current Caveats And Honest Gaps

This section is intentionally explicit about unresolved items.

1. Hugging Face semantic model revisions are currently unpinned in the runtime release manifest, so normal bootstrap currently relies on `PATENTIQ_BOOTSTRAP_ALLOW_UNPINNED_HF_MODELS=true` in `release-manifest.json:158-185`, `docs/next-phase-v2/91-patentiq-v2-runtime-bootstrap-contract.md:98-100`, and `compose.yaml:12-14`.
2. The runtime upload plan still includes non-runtime ML leftovers under `models/`, including `_tmp_phase08_phase04_latest_features.parquet`, as shown in `runtime-upload-plan.json:122-220` and documented in `docs/next-phase-v2/92-patentiq-v2-runtime-release-manual-upload-runbook.md:150-152`.
3. Current container runtime enables raw parquet fallback even though backend defaults prefer serving-first, as shown by `backend_v2/config/settings.py:51-69` versus `compose.yaml:45-53` and `azure/backend.app.yaml:57-72`.
4. The older rebuild audit `docs/next-phase-v2/69-patentiq-v2-blocking-power-downstream-pit-rebuild-audit.md:21-40` records that at the time of that audit some current-serving portfolio marts were still stale; the later audit `docs/next-phase-v2/70-patentiq-v2-current-serving-rebuild-audit.md:25-74` records that the narrow gap was subsequently refreshed. Both notes should be read in sequence.
5. The current-serving audit still documents product-level caveats that are relevant to release honesty, including owner canonicalization splits, threat-matrix unknown/self rows, and a market summary PIT that stops at `2025`, in `docs/next-phase-v2/70-patentiq-v2-current-serving-rebuild-audit.md:78-203`.
6. The repo does not yet contain one consolidated employer/affiliation disclosure, prompt disclosure appendix, or final dependency-license report.
7. The contest-window "freshly developed code" proof cannot be established from source inspection alone and should be added as a release note or Git history appendix.

## Key Takeaways

PatentIQ V2 already has a real artifact-first release system, not only a UI demo.

1. ETL builds auditable Bronze, Silver, Gold, ML, semantic, and serving outputs from externalized configuration.
2. Serving packaging is a formal ETL stage that produces domain-split runtime artifacts and machine-readable manifest/audit files.
3. Full publish releases and runtime-only releases are separated cleanly, which supports both reproducibility and leaner runtime hydration.
4. Local Docker Compose and Azure Container Apps use the same runtime bootstrap contract, the same release-manifest semantics, and the same mounted artifact layout.
5. Release behavior itself is under test across ETL, backend, and frontend layers.
6. The remaining work before a contest submission is mostly packaging and compliance disclosure work, not a missing core architecture.

For the final submission package, the most important remaining additions are:

1. employer and affiliation disclosure,
2. dependency-license inventory,
3. prompt/tool disclosure appendix,
4. contest-window commit-history proof,
5. one last comment-and-editorial pass over the final submission bundle.

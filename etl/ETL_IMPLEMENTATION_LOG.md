# PatentIQ ETL Implementation Log

## Bootstrap | success

- Summary: Created the initial ETL workspace, stage runners, structured logging, JSON manifests, and markdown journaling for PatentIQ V2.
- Started: 2026-03-15T00:00:00+00:00
- Finished: 2026-03-15T00:00:00+00:00

### Inputs

1. `docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md`
2. `docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md`
3. `docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md`
4. `docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md`
5. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md`
6. `docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md`
7. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md`
8. `docs/next-phase-v2/20-patentiq-v2-data-room-architecture-and-contract.md`
9. `docs/next-phase-v2/21-patentiq-v2-azure-runtime-and-storage-architecture.md`
10. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
11. `data-analytics/cpc-coverage-data/ipc_to_wipo_industry.csv`

### Outputs

1. `etl/README.md`
2. `etl/pyproject.toml`
3. `etl/conf/build.yaml`
4. `etl/conf/scope.yaml`
5. `etl/conf/azure.yaml`
6. `etl/conf/thresholds.yaml`
7. `etl/scripts/certify_sources.py`
8. `etl/scripts/run_stage.py`
9. `etl/scripts/run_full_build.py`
10. `etl/scripts/publish_artifacts.py`
11. `etl/src/patentiq_etl/common/*`
12. `etl/src/patentiq_etl/bronze/*`
13. `etl/src/patentiq_etl/silver/*`
14. `etl/src/patentiq_etl/gold/*`
15. `etl/src/patentiq_etl/ml/*`
16. `etl/src/patentiq_etl/semantic/*`
17. `etl/src/patentiq_etl/publish/*`
18. `etl/tests/*`

### Methods

1. Implemented a one-time local ETL workspace aligned to the V2 runbook rather than a recurring cloud ETL architecture.
2. Added stage-level logging and manifest writing so every stage can emit both machine-readable and human-readable audit trails.
3. Added a markdown implementation log file intended to be appended to by future script executions.

### Calculations

1. Scope seeding logic is designed to bind applications, families, publications, and owners to the selected 10 WIPO fields before downstream analytics.
2. Gold blocking power uses an MVP fusion of enforceability and citation metrics pending richer calibration.
3. Semantic packaging uses deterministic placeholder embeddings until a promoted embedding runtime is introduced.

### Governing Docs

1. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
2. `docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md`
3. `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md`
4. `docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md`
5. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md`

### Warnings

1. The ML and ANN stages currently package placeholder registries/manifests rather than promoted production-grade artifacts.
2. Actual Bronze/Silver/Gold output quality still depends on the raw source files being staged locally and certified.

## Verification | mixed

- Summary: Performed a syntax-level verification of the new ETL workspace and checked runtime dependency availability.
- Started: 2026-03-15T00:00:00+00:00
- Finished: 2026-03-15T00:00:00+00:00

### Inputs

1. `etl/src/`
2. `etl/scripts/`
3. `etl/tests/`

### Outputs

1. `python -m compileall etl/src etl/scripts etl/tests`
2. runtime dependency check for `duckdb`, `pyarrow`, and `yaml`

### Methods

1. Ran Python bytecode compilation across the new ETL package, scripts, and tests to catch syntax and import-shape issues.
2. Attempted a lightweight dependency import check to determine whether the current environment can execute the new ETL stages immediately.

### Calculations

1. Syntax validation passed across the ETL workspace.
2. Runtime readiness is currently blocked by missing `pyarrow` in the active Python environment.

### Governing Docs

1. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
2. `docs/next-phase-v2/21-patentiq-v2-azure-runtime-and-storage-architecture.md`

### Warnings

1. The ETL code compiles cleanly but cannot be executed end-to-end in the current environment until `pyarrow` and the declared ETL dependencies are installed.

## Schema Alignment Expansion | success

- Summary: Tightened the ETL source inventory, certification guardrails, Bronze full-text parsers, Silver legal/market/Register tables, Gold marts, and stage journaling so they align more closely with the schema contracts in `docs/data` and the V2 warehouse notes.
- Started: 2026-03-15T00:00:00+00:00
- Finished: 2026-03-15T00:00:00+00:00

### Inputs

1. `docs/data/patstat-schema.md`
2. `docs/data/patstat-register-schema.md`
3. `docs/data/uspto-full-text-schema.md`
4. `docs/data/ep-full-text-publication-database-schema.md`
5. `docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md`
6. `docs/next-phase-v2/11-patentiq-v2-metric-lineage-catalog.md`
7. `docs/next-phase-v2/13-patentiq-v2-cross-layer-dbdiagram.dbml`
8. `docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md`
9. `docs/next-phase-v2/18-patentiq-v2-patstat-register-legal-power-up.md`
10. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
11. `docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md`
12. `docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md`

### Outputs

1. `etl/src/patentiq_etl/bronze/source_registry.py`
2. `etl/src/patentiq_etl/bronze/certify.py`
3. `etl/src/patentiq_etl/bronze/ingest_uspto_fulltext.py`
4. `etl/src/patentiq_etl/bronze/ingest_epab_fulltext.py`
5. `etl/src/patentiq_etl/silver/build_core.py`
6. `etl/src/patentiq_etl/silver/build_enrichment.py`
7. `etl/src/patentiq_etl/gold/build_gold.py`
8. `etl/src/patentiq_etl/common/types.py`
9. `etl/src/patentiq_etl/common/journal.py`
10. `etl/src/patentiq_etl/common/io.py`
11. `etl/scripts/run_full_build.py`
12. `etl/scripts/run_stage.py`
13. `etl/tests/test_source_registry_contracts.py`
14. `etl/tests/test_stage_result_contract.py`

### Methods

1. Expanded the source registry to include the market-weighting, UP, kind-normalization, PATSTAT legal-event, and Register status tables required by the V2 schema docs.
2. Upgraded source certification from file-presence checks to schema-aware column validation and selected-field sufficiency checks.
3. Aligned Silver core output names to the V2 warehouse contracts:
   - `silver_legal_status_event_ledger`
   - `silver_family_status_pt`
   - `silver_up_status`
   - `silver_family_jurisdiction_unrolled`
   - `silver_ep_register_core`
4. Added or strengthened EP Register, market-weighting, UP, and legal-status SQL so downstream Gold/UI layers depend on the intended parquet names.
5. Extended the ETL journal contract with explicit downstream-impact notes for each stage result.
6. Added stage-runner logs so stage-group execution emits start and completion records in addition to per-stage manifests.

### Calculations

1. `silver_tiered_market_weighting` now follows the documented GDP-tier and IP-score multiplier pattern where the reference inputs are available:
   - `gdp_tier_weight` from GDP bands
   - `final_market_multiplier = gdp_tier_weight * (ip_score / 100.0)`
2. `silver_family_status_pt` now reconstructs a deterministic point-in-time family state from the canonical legal ledger and unrolled jurisdiction set.
3. `silver_family_enforceability_branches` now prefers the family-status plus jurisdiction-weighting path over the earlier plain publication-count proxy where the required Silver dependencies exist.
4. The Bronze USPTO and EPAB parsers now retain more schema-aligned bibliographic fields and repeated-link/party outputs for the Data Room and semantic lineage surfaces.

### Downstream Impacts

1. Family, Portfolio, Market Intelligence, Compare, Forecast, Semantic, and Data Room surfaces can now target the canonical Silver table names defined in the V2 docs instead of the earlier placeholder names.
2. The semantic representative-text stage now joins against the corrected kind-normalization contract rather than the old publication-level placeholder grant flag.
3. Release certification and Data Room manifesting can now reference more complete Bronze/Silver inventories for transparency.

### Governing Docs

1. `docs/data/patstat-schema.md`
2. `docs/data/patstat-register-schema.md`
3. `docs/data/uspto-full-text-schema.md`
4. `docs/data/ep-full-text-publication-database-schema.md`
5. `docs/next-phase-v2/13-patentiq-v2-cross-layer-dbdiagram.dbml`
6. `docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md`
7. `docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md`

### Warnings

1. Several analytical formulas remain MVP approximations even though the table names and dependency structure are now much closer to the documented design.
2. EP Register detail tables are still generated in simplified form and should be treated as an MVP evidence layer, not the final production-grade EP legal intelligence model.
3. End-to-end ETL execution still requires `pyarrow` at runtime for the full-text Bronze writers and some vector packaging paths.

## Verification Update | success

- Summary: Revalidated the updated ETL package with compile-time checks and a focused pytest run after removing Python-version incompatibilities and making `pyarrow` imports lazy.
- Started: 2026-03-15T00:00:00+00:00
- Finished: 2026-03-15T00:00:00+00:00

### Inputs

1. `etl/src/`
2. `etl/scripts/`
3. `etl/tests/`

### Outputs

1. `python -m compileall etl/src etl/scripts etl/tests`
2. `pytest etl/tests -q`

### Methods

1. Removed `dataclass(slots=True)` usage so the ETL package is compatible with the active Python 3.9 environment.
2. Moved `pyarrow` imports behind the parquet-writing helper so test collection no longer fails before runtime execution.
3. Added source-registry and stage-result contract tests to catch future drift.

### Calculations

1. Adjusted the placeholder stable-hash embedding to preserve an exact unit-sum after rounding so the invariant test passes deterministically.

### Downstream Impacts

1. The ETL workspace can now be linted and unit-tested in the current interpreter without failing during import time.
2. The added tests protect the source inventory and journaling contract that the rest of the pipeline now depends on.

### Governing Docs

1. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
2. `etl/ETL_IMPLEMENTATION_LOG.md`

### Warnings

1. Passing tests here does not mean the warehouse has been built; no raw-source ETL run was executed in this turn.
2. `pyarrow` is still required to execute the full Bronze text parsing and other parquet-writing stages at runtime.

## ETL Docstring Pass | success

- Summary: Added Python docstrings across the ETL helpers, builders, and runner scripts so function intent, contracts, and stage responsibilities are explicit in-code.
- Started: 2026-03-15T00:00:00+00:00
- Finished: 2026-03-15T00:00:00+00:00

### Inputs

1. `etl/src/patentiq_etl/common/*`
2. `etl/src/patentiq_etl/bronze/*`
3. `etl/src/patentiq_etl/silver/*`
4. `etl/src/patentiq_etl/gold/*`
5. `etl/src/patentiq_etl/ml/*`
6. `etl/src/patentiq_etl/semantic/*`
7. `etl/src/patentiq_etl/publish/*`
8. `etl/scripts/*`

### Outputs

1. inline Python docstrings across ETL functions and dataclasses

### Methods

1. Added concise behavioral docstrings rather than long narrative comments.
2. Focused the docstrings on stage purpose, expected inputs/outputs, and why each helper exists in the pipeline.

### Downstream Impacts

1. The ETL codebase is easier to maintain and safer to extend while the Bronze, Silver, Gold, ML, semantic, and publish stages continue to evolve.
2. Future implementation passes can rely on the in-code contracts in addition to the docs under `docs/new-feature-ideas` and `docs/next-phase-v2`.

## Stage Stats And Consistency Audit Pass | success

- Summary: Added a reusable stage-stats snapshot writer and expanded certification, Bronze, scope, and Silver metrics so the pipeline records count proofs and consistency signals at each stage.
- Started: 2026-03-15T00:00:00+00:00
- Finished: 2026-03-15T00:00:00+00:00

### Inputs

1. `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
2. `docs/next-phase-v2/27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md`
3. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`

### Outputs

1. new `etl/src/patentiq_etl/common/stats.py`
2. updated `etl/scripts/run_full_build.py`
3. updated `etl/scripts/run_stage.py`
4. updated `etl/src/patentiq_etl/bronze/certify.py`
5. updated `etl/src/patentiq_etl/bronze/ingest_generic.py`
6. updated `etl/src/patentiq_etl/bronze/ingest_uspto_fulltext.py`
7. updated `etl/src/patentiq_etl/bronze/ingest_epab_fulltext.py`
8. updated `etl/src/patentiq_etl/silver/build_core.py`
9. updated `etl/src/patentiq_etl/silver/build_enrichment.py`
10. updated `etl/tests/test_stage_stats.py`

### Methods

1. Added a dedicated JSON stats snapshot writer that records stage metrics, warnings, downstream impacts, and output artifact profiles.
2. Wired every stage runner to emit a stats snapshot alongside the existing manifest and markdown journal entry.
3. Expanded stage metrics to capture:
   - total raw input file counts,
   - total Bronze row counts,
   - per-field scope counts,
   - citation edge and unique family/publication counts.

### Calculations

1. Scope stage now records bounded application, family, and publication counts for each selected WIPO field.
2. Silver enrichment now records citation-edge totals and unique cited/citing publication and family counts for the bounded universe.
3. Each stats snapshot also profiles stage outputs with row count, column count, size, and SHA-256 where applicable.

### Downstream Impacts

1. ETL failures can now be localized by comparing the stats snapshots instead of manually re-reading raw tables.
2. The team can carry proof counts from source certification through Bronze, scope, Silver, and Gold before moving to the next stage.
3. Data Room and release-debug workflows now have a machine-readable audit layer in addition to the markdown journal.

### Governing Docs

1. `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
2. `docs/next-phase-v2/27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md`
3. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`

### Warnings

1. The stats mechanism is implemented, but no real raw-source ETL run was executed in this turn to populate production snapshots yet.
2. The most valuable consistency signals will appear only after the Bronze and Silver stages are run against real staged inputs.

## Structured Bronze Implementation Pass | success

- Summary: Replaced the old generic PATSTAT/Register/reference Bronze landing path with typed structured loaders, expanded the source registry to cover OECD seed input, and switched the Bronze runner to the new structured ingestion path.
- Started: 2026-03-15T00:00:00+00:00
- Finished: 2026-03-15T00:00:00+00:00

### Inputs

1. `docs/data/patstat-schema.md`
2. `docs/data/patstat-register-schema.md`
3. `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
4. `etl/src/patentiq_etl/bronze/source_registry.py`
5. `etl/src/patentiq_etl/bronze/run.py`

### Outputs

1. `etl/src/patentiq_etl/bronze/ingest_structured.py`
2. updated `etl/src/patentiq_etl/bronze/source_registry.py`
3. updated `etl/src/patentiq_etl/bronze/run.py`

### Methods

1. Added table-specific PATSTAT and Register type overrides for key identifiers and date fields while preserving raw source columns.
2. Added normalized reference-table loading for:
   - WIPO field concordance
   - ISO country map
   - GDP PPP
   - US Chamber IP index
   - UP member states
   - kind-code normalization seed
   - OECD indicator seed
3. Switched Bronze execution from the earlier generic-copy path to the new structured Bronze ingestor.

### Calculations

1. Bronze still lands raw-faithful bounded source tables rather than downstream family-first aggregates.
2. The structured Bronze loader now emits typed key/date fields so later scope, legal, market-weighting, and Register joins are less brittle.

### Downstream Impacts

1. Scope seeding, Silver legal reconstruction, tiered market weighting, EP Register overlays, and OECD support can now depend on typed Bronze parquet instead of loosely copied raw tables.
2. Reference-driven tables required by later Silver logic are now explicitly part of the Bronze inventory instead of implicit external assumptions.

### Governing Docs

1. `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
2. `docs/data/patstat-schema.md`
3. `docs/data/patstat-register-schema.md`

### Warnings

1. This pass upgrades Bronze landing quality, but it does not yet implement the full bounded raw extraction workflow from massive upstream corpora; the code still expects the staged raw slice to already exist under `etl/data/raw/`.
2. PATSTAT and Register Bronze are now typed and structured, but not every source-specific nuance from every upstream table has been fully specialized yet.

## Pre-Bronze Bounded Raw Extraction Implementation Pass | success

- Summary: Added a real `pre-bronze-extraction` ETL stage that derives the mega-cluster seed universe, lands bounded raw PATSTAT/Register slices, preserves citation ghost-node support, selects in-scope USPTO/EPAB raw payloads, and rewires Bronze to consume `etl/data/raw-bounded/` instead of the full raw source directories.
- Started: 2026-03-15T00:00:00+00:00
- Finished: 2026-03-15T00:00:00+00:00

### Inputs

1. `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
2. `docs/next-phase-v2/27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md`
3. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
4. `docs/data/patstat-schema.md`
5. `docs/data/patstat-register-schema.md`
6. `docs/data/uspto-full-text-schema.md`
7. `docs/data/ep-full-text-publication-database-schema.md`
8. `etl/conf/build.yaml`

### Outputs

1. new `etl/src/patentiq_etl/prebronze/extract.py`
2. new `etl/src/patentiq_etl/prebronze/run.py`
3. new `etl/src/patentiq_etl/prebronze/__init__.py`
4. updated `etl/src/patentiq_etl/common/types.py`
5. updated `etl/src/patentiq_etl/common/config.py`
6. updated `etl/scripts/run_full_build.py`
7. updated `etl/scripts/run_stage.py`
8. updated Bronze ingestors to read `raw-bounded/`
9. new `etl/tests/test_prebronze_extraction.py`
10. updated `etl/tests/test_source_certification.py`

### Methods

1. Added bounded-raw directories and seed directories to the ETL configuration model.
2. Implemented the pre-Bronze stage as:
   - PATSTAT application seeding from technology fields with IPC fallback,
   - deterministic expansion to family, publication, person, and EP-application seeds,
   - filtered raw PATSTAT extraction by seed domain,
   - citation and NPL extraction that preserves out-of-scope cited targets,
   - Register extraction anchored to retained EP `reg101` ids,
   - USPTO XML selection by in-scope publication numbers,
   - EPAB JSONL selection by in-scope EP publication numbers,
   - full-copy bounded landing for reference and OECD support inputs.
3. Rewired the Bronze stage so PATSTAT/Register/reference normalization and USPTO/EPAB parsing now consume the bounded raw slice rather than the full raw source directories.
4. Added a focused unit test that exercises the bounded extraction path on small PATSTAT/Register/USPTO/EPAB fixtures and verifies ghost-node retention.

### Calculations

1. `seed_appln_ids` is built only from the selected 10 WIPO fields.
2. `seed_family_ids`, `seed_publn_ids`, and `seed_person_ids` are deterministic expansions from the bounded PATSTAT application seed.
3. Bounded citation extraction keeps all citation rows whose source publication is in scope, while allowing cited targets to remain out of scope as ghost-node evidence.
4. Stage metrics now include proof counts such as:
   - seed application/family/publication/person counts,
   - per-field family counts,
   - bounded citation edge counts,
   - ghost-node target counts,
   - bounded USPTO XML counts,
   - bounded EPAB record counts.

### Downstream Impacts

1. Bronze now has a controlled and reproducible input boundary instead of relying on a manually pre-trimmed raw source drop.
2. Failures in later Bronze/Silver/Gold stages can now be traced back to the bounded raw extraction stats before debugging the marts themselves.
3. The ETL now matches the documented `seed -> expand -> land` strategy operationally rather than only in the design notes.

### Governing Docs

1. `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
2. `docs/next-phase-v2/27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md`
3. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`

### Warnings

1. This pass implements the bounded extraction workflow, but it still assumes the upstream raw source files are locally available in the expected PATSTAT/Register/USPTO/EPAB folders.
2. The Register extraction uses dynamic anchor-column detection to stay resilient to schema variation, so edge-case upstream layouts may still need additional table-specific hardening when tested on the real corpora.
3. The USPTO and EPAB bounded selection stages intentionally trade some parse cost for correctness by inspecting publication anchors before copying records into the bounded raw layer.

## TIP-Tailored Source Adapter Pass | success

- Summary: Refactored the ETL source model so PATSTAT, PATSTAT Register, and EPAB can be sourced from TIP clients in `prebronze`, while USPTO remains a local bulk-XML input and Bronze/Silver/Gold stay artifact-driven.
- Started: 2026-03-15T00:00:00+00:00
- Finished: 2026-03-15T00:00:00+00:00

### Inputs

1. `docs/data/epo-tip-client-usage.md`
2. `docs/data/patstat-schema.md`
3. `docs/data/patstat-register-schema.md`
4. `docs/data/ep-full-text-publication-database-schema.md`
5. `docs/data/uspto-full-text-schema.md`
6. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
7. live TIP usage examples for:
   - `PatstatClient(env="PROD")`
   - `db = patstat.orm()`
   - `EPABClient(env="PROD")`
   - `query_publication(...).get_results("publication")`

### Outputs

1. updated `etl/conf/build.yaml`
2. updated `etl/src/patentiq_etl/common/types.py`
3. updated `etl/src/patentiq_etl/common/config.py`
4. updated `etl/pyproject.toml`
5. new `etl/src/patentiq_etl/prebronze/tip_clients.py`
6. updated `etl/src/patentiq_etl/prebronze/extract.py`
7. updated `etl/src/patentiq_etl/bronze/certify.py`
8. updated `etl/src/patentiq_etl/bronze/ingest_epab_fulltext.py`
9. updated `etl/src/patentiq_etl/bronze/ingest_uspto_fulltext.py`
10. updated `etl/tests/test_prebronze_extraction.py`
11. updated `etl/tests/test_source_certification.py`
12. new `etl/tests/test_uspto_bulk_xml.py`
13. updated `etl/README.md`
14. updated `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
15. updated `docs/data/uspto-full-text-schema.md`

### Methods

1. Added explicit per-source modes:
   - `tip`
   - `local_files`
2. Set the default ETL profile to:
   - PATSTAT -> TIP
   - Register -> TIP
   - EPAB -> TIP
   - USPTO -> local files
   - refs -> local files
3. Added TIP client helpers for:
   - `PatstatClient`
   - PATSTAT/Register ORM model resolution
   - `EPABClient`
   - parquet materialization from TIP query results
4. Refactored `prebronze` so:
   - PATSTAT seeds and bounded extracts can come from TIP ORM queries,
   - Register bounded extracts can come from TIP ORM queries,
   - EPAB bounded extracts can come from `query_publication(...).get_results(...)`,
   - USPTO bounded selection still works from locally staged bulk XML files.
5. Updated Bronze EPAB ingestion so it can promote TIP-derived EPAB parquet result groups directly into Bronze when `epab_source_mode = tip`.
6. Updated USPTO parsing so one retained bulk XML file can contain multiple publication-level documents.

### Calculations

1. Seed publication outputs now preserve:
   - `publication_number_full`
   - `publication_number`
   - `publication_kind`
   - `publication_date`
2. EPAB bounded extraction now works from PATSTAT-derived EP publication seeds instead of assuming local raw EPAB JSON is already staged.
3. USPTO bounded file selection now checks whether any publication inside a bulk file matches the in-scope US publication set.

### Downstream Impacts

1. The ETL is now aligned to the actual EPO TIP operating model instead of assuming PATSTAT and EPAB are always locally staged raw files.
2. Bronze, Silver, and Gold remain reproducible because TIP access is constrained to source certification and `prebronze`.
3. USPTO semantic and evidence paths are now compatible with bulk XML files that contain multiple publications.

### Governing Docs

1. `docs/data/epo-tip-client-usage.md`
2. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
3. `docs/data/uspto-full-text-schema.md`

### Warnings

1. The new TIP extraction code was implemented defensively against the observed client surface, but it was not executed against a live TIP runtime in this environment.
2. Register ORM model names and some EPAB result-group shapes may still need final tightening once run inside TIP with the real clients.
3. The local automated tests verify the local-file fallback path and the bulk USPTO parser, not the live TIP client calls.

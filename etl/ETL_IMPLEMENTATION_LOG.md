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

## USPTO ODP Streaming Extraction Design | success

- Summary: Documented the preferred local USPTO acquisition path as a sequential ODP stream worker that downloads one weekly APPXML ZIP at a time, parses only bounded in-scope publications, writes direct Bronze parquet outputs, records richer file-level extraction stats, and deletes ZIP and temp XML artifacts immediately after successful persistence.
- Started: 2026-03-16T00:00:00+00:00
- Finished: 2026-03-16T00:00:00+00:00

### Inputs

1. `docs/data/uspto-full-text-schema.md`
2. user-provided ODP API, rate-limit, and APPXML operational notes
3. user-provided schema examples for `v40` through `v44`
4. `etl/src/patentiq_etl/bronze/ingest_uspto_fulltext.py`
5. `etl/src/patentiq_etl/prebronze/extract.py`
6. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
7. `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
8. `docs/next-phase-v2/27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md`

### Outputs

1. `docs/data/uspto-odp-stream-extraction-pipeline.md`
2. updated `docs/data/uspto-full-text-schema.md`
3. updated `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
4. updated `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
5. updated `docs/next-phase-v2/27-patentiq-v2-stage-stats-and-data-consistency-audit-contract.md`
6. updated `etl/README.md`

### Methods

1. Aligned the planned USPTO acquisition horizon to the main `2007-2026` operating window.
2. Chose direct Bronze parquet output instead of long-lived bounded XML retention for the local ODP path.
3. Defined a file-at-a-time execution stream with revision pruning, schema detection, bounded publication filtering, direct Bronze persistence, and immediate cleanup.
4. Expanded the operational logging contract to include per-file ZIP, XML, publication-match, row-count, and cleanup metrics.

### Warnings

1. The local ODP stream worker is documented as the preferred implementation path but is not yet fully implemented in ETL code.
2. The current repo parser is still materially simpler than the full USPTO schema note and still needs explicit hardening across `v42-v46`.
3. Full parser hardening still benefits from the underlying DTD files and validation against real weekly bulk payloads even though real schema samples now cover `v42-v46`.

## USPTO Schema Sample Coverage Update | success

- Summary: Updated the USPTO documentation assumptions to reflect that real sample coverage now exists across schema versions `v42` through `v46`, which fully spans the current `2007-2026` USPTO operating horizon.
- Started: 2026-03-16T00:00:00+00:00
- Finished: 2026-03-16T00:00:00+00:00

### Inputs

1. user-provided real schema examples for `v42`
2. user-provided real schema examples for `v43`
3. user-provided real schema examples for `v44`
4. user-provided real schema examples for `v45`
5. user-provided real schema example for `v46`

### Outputs

1. updated `docs/data/uspto-odp-stream-extraction-pipeline.md`
2. updated `etl/ETL_IMPLEMENTATION_LOG.md`

### Methods

1. Removed the outdated assumption that `v45` and `v46` were still missing real sample coverage.
2. Kept the more important remaining caution in place: real weekly bulk-payload validation and DTD-backed parser hardening are still needed.

## USPTO ODP Stream Worker Implementation | success

- Summary: Implemented the local USPTO ODP stream worker, added a dedicated `prebronze-uspto-odp` stage, integrated direct Bronze parquet output with immediate ZIP/XML cleanup, enriched per-file extraction stats, and made the Bronze USPTO stage reuse direct ODP outputs when present.
- Started: 2026-03-16T00:00:00+00:00
- Finished: 2026-03-16T00:00:00+00:00

### Inputs

1. `docs/data/uspto-odp-stream-extraction-pipeline.md`
2. `docs/data/uspto-full-text-schema.md`
3. `etl/src/patentiq_etl/bronze/ingest_uspto_fulltext.py`
4. `etl/src/patentiq_etl/prebronze/extract.py`
5. user-provided ODP API and schema-version notes

### Outputs

1. `etl/src/patentiq_etl/prebronze/uspto_odp.py`
2. updated `etl/src/patentiq_etl/bronze/ingest_uspto_fulltext.py`
3. updated `etl/src/patentiq_etl/prebronze/run.py`
4. updated `etl/scripts/run_stage.py`
5. updated `etl/scripts/run_full_build.py`
6. updated `etl/src/patentiq_etl/common/io.py`
7. updated `etl/tests/test_uspto_bulk_xml.py`
8. updated `etl/tests/test_prebronze_extraction.py`

### Methods

1. Added an ODP manifest-and-download worker with revision pruning, bounded file selection, and sequential ZIP processing.
2. Split concatenated APPXML payloads into publication-level XML documents before schema detection and bounded publication filtering.
3. Wrote direct `bronze_uspto_ft_*` parquet outputs from the ODP stream path instead of retaining bounded XML.
4. Logged per-file download, schema, publication-match, row-count, and cleanup metrics to manifest stats.
5. Made the standard Bronze USPTO stage no-op successfully when the direct ODP Bronze outputs already exist.

### Verification

1. `python3 -m compileall etl/src etl/scripts etl/tests`
2. `pytest etl/tests/test_uspto_bulk_xml.py etl/tests/test_prebronze_extraction.py etl/tests/test_source_certification.py -q`

### Warnings

1. The ODP stream worker currently assumes the bounded U.S. publication seed already exists.
2. The parser hardening still needs broader real-world validation across `v42-v46` payloads even though the local execution path now exists.

## TIP USPTO Externalization Default | success

- Summary: Switched the default USPTO source mode to `odp_api`, removed the TIP-side degradation path that expected local USPTO XML files, and made the Bronze USPTO stage treat missing direct ODP outputs as a deferred external path rather than a runtime problem.
- Started: 2026-03-16T00:00:00+00:00
- Finished: 2026-03-16T00:00:00+00:00

### Outputs

1. updated `etl/conf/build.yaml`
2. updated `etl/src/patentiq_etl/bronze/certify.py`
3. updated `etl/src/patentiq_etl/bronze/ingest_uspto_fulltext.py`
4. updated `etl/README.md`
5. updated `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`

### Methods

1. Changed the default USPTO source mode from `local_files` to `odp_api`.
2. Treated missing ODP credentials in generic source certification as a deferred external path instead of a degraded TIP runtime.
3. Made the Bronze USPTO stage return success with a deferred summary when `odp_api` is configured but direct USPTO Bronze outputs have not yet been materialized.

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

## 2026-03-16 | TIP Full-Scope Chunked Execution Documentation | success

### Inputs

1. live TIP operating constraints provided during execution:
   - `4 CPU cores`
   - `32 GB RAM`
   - `30 GB local storage`
2. observed PATSTAT technology-field counts from TIP
3. existing ETL runbook and TIP client usage notes

### Files Updated

1. updated `docs/next-phase-v2/README.md`
2. updated `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
3. new `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
4. updated `docs/data/epo-tip-client-usage.md`
5. updated `etl/README.md`

### Methods

1. Documented TIP as a constrained extraction worker rather than a full warehouse runtime.
2. Defined chunk keys as:
   - `field`
   - `year bucket`
   - `table family`
3. Defined Blob as the authoritative intermediate store for full-scope extraction.
4. Defined safe worker guidance for TIP:
   - `2 workers` for core/publication families
   - `1 worker` for citation-heavy or text-heavy families

### Calculations

1. The chunking strategy assumes the primary constraint is:
   - local memory
   - local disk
   - citation fan-out
   not CPU alone
2. The documented resource envelope keeps local staging bounded by:
   - small year buckets
   - immediate upload
   - immediate local cleanup

### Downstream Impacts

1. The ETL documentation now distinguishes between:
   - TIP extraction
   - non-TIP consolidation
2. Full-scope execution is now documented as a resumable multi-chunk process instead of a monolithic `prebronze` run.
3. Azure Blob is now explicitly documented as the intermediate bounded raw store for TIP full-scope runs.

### Governing Docs

1. `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
2. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
3. `docs/data/epo-tip-client-usage.md`

### Warnings

1. This pass is documentation-only; the current ETL code does not yet implement the full TIP chunk planner, Blob-first upload cycle, or resume scheduler described in the new execution plan.

## 2026-03-16 | Azure-Oriented TIP Pipeline Revision | success

### Inputs

1. documented TIP runtime limits:
   - `4 CPU cores`
   - `32 GB RAM`
   - `30 GB local storage`
2. updated full-scope Blob-first execution plan in:
   - `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
3. observed TIP PATSTAT field counts and current ETL settings

### Files Updated

1. updated `etl/conf/build.yaml`
2. updated `etl/src/patentiq_etl/common/types.py`
3. updated `etl/src/patentiq_etl/common/config.py`
4. updated `etl/src/patentiq_etl/prebronze/tip_clients.py`
5. updated `etl/src/patentiq_etl/bronze/certify.py`
6. updated `etl/src/patentiq_etl/prebronze/extract.py`
7. updated `etl/src/patentiq_etl/prebronze/run.py`
8. new `etl/src/patentiq_etl/prebronze/plan.py`
9. updated `etl/scripts/run_stage.py`
10. updated `etl/scripts/run_full_build.py`
11. updated `etl/tests/test_source_certification.py`
12. new `etl/tests/test_tip_chunk_plan.py`
13. updated `etl/README.md`
14. updated `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`

### Methods

1. Added an explicit `execution` config block for TIP chunked export settings.
2. Added a `tip-chunk-plan` stage that writes a deterministic chunk manifest under `etl/manifests/chunks/`.
3. Added chunk planning based on:
   - selected field
   - year bucket
   - table family
4. Added best-effort year-window filtering for TIP ORM queries using string-safe year extraction from observed date-like PATSTAT fields.
5. Inserted the chunk-plan stage into the full-build runner when TIP chunked export is enabled.

### Calculations

1. Chunk ids are calculated as:
   - `field_slug__yearStart_yearEnd__table_family`
2. Year buckets are calculated from:
   - `year_window_start`
   - `year_window_end`
   - `chunk_year_span`
3. Worker recommendations are calculated from the configured `max_workers` map and emitted into the chunk plan manifest.

### Downstream Impacts

1. TIP PATSTAT source certification now reflects the configured ETL time window rather than full-history field counts.
2. The ETL now has a first concrete code path toward the Azure Blob-first TIP operating model instead of only documentation.
3. Full chunk execution, upload-after-write orchestration, and cleanup scheduling still need implementation beyond the planner stage.

### Governing Docs

1. `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
2. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
3. `etl/README.md`

### Warnings

1. This pass adds the chunk-planning stage and year-window enforcement, but it does not yet implement full chunk execution or immediate Azure upload per chunk.

## 2026-03-16 | TIP Chunked Pre-Bronze Executor | success

### Inputs

1. existing TIP chunk planning configuration
2. current monolithic TIP `prebronze` extraction logic
3. Azure Blob-first execution requirement for constrained TIP environments

### Files Updated

1. new `etl/src/patentiq_etl/prebronze/chunked.py`
2. updated `etl/src/patentiq_etl/prebronze/run.py`
3. updated `etl/README.md`

### Methods

1. Added a chunk executor that iterates planned field/year/table-family chunks.
2. Added per-chunk PATSTAT family extraction:
   - `core`
   - `publications`
   - `legal`
   - `citations`
3. Added per-chunk Register extraction from EP application seeds.
4. Added per-chunk EPAB extraction from chunk-local EP publication seeds.
5. Added optional Azure Blob upload per chunk with deterministic blob prefixes.
6. Added per-chunk manifest writing and resume-by-success semantics.
7. Added local chunk cleanup after upload verification when enabled.

### Calculations

1. Each chunk derives its own bounded scope from:
   - field
   - year bucket
   - table family
2. Chunk-local PATSTAT scope is built directly from TIP rather than from one giant persisted seed universe.

### Downstream Impacts

1. `prebronze` can now execute in a Blob-first chunked mode for TIP instead of requiring one monolithic bounded raw export.
2. Chunk manifests now provide resumability and local cleanup control for long-running TIP extraction campaigns.

### Governing Docs

1. `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
2. `etl/README.md`

### Warnings

1. Chunk execution is now implemented, but USPTO bulk XML export is not yet split by the same field/year chunk boundaries and remains surfaced as a chunk warning when relevant.

## 2026-03-16 | USPTO Chunk-Aware Pre-Bronze Export | success

### Inputs

1. current TIP chunked `prebronze` executor
2. USPTO bulk XML parser that already supports multiple publication-level documents per file
3. TIP chunk-alignment requirement for full-scope Blob-first export

### Files Updated

1. updated `etl/src/patentiq_etl/bronze/ingest_uspto_fulltext.py`
2. updated `etl/src/patentiq_etl/prebronze/chunked.py`
3. updated `etl/tests/test_uspto_bulk_xml.py`
4. updated `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
5. updated `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
6. updated `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
7. updated `docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md`
8. updated `etl/README.md`

### Methods

1. Added a filtered bulk-XML writer that rewrites a USPTO file with only the publication-level documents requested by the active chunk.
2. Replaced the old chunk warning path with real USPTO extraction inside the `publications` family of the TIP chunk executor.
3. Routed filtered USPTO outputs to a chunk-aligned `raw-bounded/uspto/...` Blob prefix instead of mixing them into the PATSTAT publication path.
4. Added a regression test proving that a multi-publication USPTO XML file can be reduced to a single in-scope publication and still be parsed by the Bronze loader.

### Calculations

1. USPTO chunk seeds are still derived from PATSTAT `US` publications inside the active field/year scope.
2. Chunk metrics now record:
   - source XML file count
   - output XML file count
   - matched document count
   - matched publication count
   - unmatched U.S. publication seed count

### Downstream Impacts

1. TIP chunk manifests can now represent PATSTAT publication rows and their matching USPTO text-provider payloads inside the same field/year chunk.
2. Bronze USPTO parsing remains publication-faithful while avoiding mixed-scope bulk XML carry-through.
3. Blob intermediate storage now holds chunk-aligned USPTO raw inputs suitable for later non-TIP Bronze consolidation.

### Governing Docs

1. `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
2. `docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md`
3. `docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md`

### Warnings

1. This pass makes USPTO extraction chunk-aware, but live TIP-plus-Azure execution still needs to be exercised in the real target environment.

## 2026-03-16 | Two-Horizon Scope Timeline Revision | success

### Inputs

1. current ETL year-window config
2. mega-cluster scope and ghost-node policy notes
3. heritage and historical-influence requirements across the March 2026 planning notes

### Files Updated

1. updated `etl/conf/build.yaml`
2. new `docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md`
3. updated `docs/next-phase-v2/README.md`
4. updated `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md`
5. updated `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
6. updated `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
7. updated `docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md`
8. updated `etl/README.md`

### Methods

1. Revised the main ETL operating window from the earlier `2006-2026` placeholder to the cleaner `2007-2026` 20-year window.
2. Introduced an explicit two-horizon policy that separates the main operating warehouse horizon from an older heritage backfill horizon.
3. Updated the scope and runbook notes so they distinguish current-state analytics from backward-looking heritage analytics.

### Calculations

1. The main ETL window is now defined as `2007-2026` inclusive.
2. The first recommended heritage backfill target is `1996-2006`.
3. TIP chunk-plan year-bucket examples were recalculated against the new main operating window.

### Downstream Impacts

1. Current operational marts should align to the `2007-2026` bounded mega-cluster.
2. Heritage and historical influence logic now has a documented path to use older mega-cluster families without polluting current-state inclusion rules.
3. The ETL and scope documentation now describe a cleaner separation between current strategic analytics and historical innovation analytics.

### Governing Docs

1. `docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md`
2. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md`
3. `docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md`

### Warnings

1. The two-horizon policy is documented and the main ETL config is aligned, but the separate heritage backfill extraction path is not yet implemented as a distinct runtime stage.

## 2026-03-16 | Two-Horizon Model Alignment In Silver And Gold | success

### Inputs

1. two-horizon scope policy
2. current single-horizon `silver_family_core` implementation
3. current Gold marts that implicitly aggregated over the full in-scope family table

### Files Updated

1. updated `etl/src/patentiq_etl/common/types.py`
2. updated `etl/src/patentiq_etl/common/config.py`
3. updated `etl/conf/build.yaml`
4. updated `etl/src/patentiq_etl/silver/build_core.py`
5. updated `etl/src/patentiq_etl/gold/build_gold.py`
6. updated `docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md`
7. updated `docs/next-phase-v2/11-patentiq-v2-metric-lineage-catalog.md`
8. updated `docs/next-phase-v2/12-patentiq-v2-database-structure-and-metric-maps.md`
9. updated `docs/next-phase-v2/13-patentiq-v2-cross-layer-dbdiagram.dbml`
10. updated `docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md`
11. updated `docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md`
12. updated `docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md`
13. updated `etl/README.md`

### Methods

1. Added explicit horizon configuration for the main ETL window and the heritage backfill window.
2. Extended `silver_family_core` with scope flags:
   - `is_main_window_family`
   - `is_heritage_backfill_family`
   - `is_out_of_bounds_ghost`
3. Updated Gold current-state marts to read only `is_main_window_family = true`.
4. Updated the main warehouse design docs so they reflect horizon flags and current-vs-heritage separation.

### Calculations

1. Main window flags are now computed from the configured `2007-2026` range.
2. Heritage backfill flags are now computed from the configured `1996-2006` range.
3. Gold current-state family, blocking, portfolio, and field-decomposition marts now explicitly filter to the main operating horizon.

### Downstream Impacts

1. The warehouse now has an explicit place to distinguish current operating families from historical-support families.
2. Current operational marts are less likely to drift when the historical backfill horizon is introduced later.
3. Heritage and historical metrics still need their own dedicated extraction/runtime path before the backfill horizon becomes populated.

### Governing Docs

1. `docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md`
2. `docs/next-phase-v2/13-patentiq-v2-cross-layer-dbdiagram.dbml`
3. `docs/next-phase-v2/11-patentiq-v2-metric-lineage-catalog.md`

### Warnings

1. The logical model is now two-horizon-aware, but the historical backfill extraction stage itself is still pending implementation.

## 2026-03-16 | Heritage Backfill Runtime And Heritage Gold Outputs | success

### Inputs

1. two-horizon scope policy
2. existing TIP chunk planner and chunk executor
3. current Gold marts lacking explicit historical-heritage summary outputs

### Files Updated

1. updated `etl/src/patentiq_etl/prebronze/plan.py`
2. updated `etl/src/patentiq_etl/prebronze/run.py`
3. updated `etl/src/patentiq_etl/prebronze/chunked.py`
4. updated `etl/scripts/run_stage.py`
5. updated `etl/scripts/run_full_build.py`
6. updated `etl/conf/build.yaml`
7. updated `etl/src/patentiq_etl/gold/build_gold.py`
8. updated `etl/tests/test_tip_chunk_plan.py`
9. updated `docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md`
10. updated `docs/next-phase-v2/11-patentiq-v2-metric-lineage-catalog.md`
11. updated `docs/next-phase-v2/12-patentiq-v2-database-structure-and-metric-maps.md`
12. updated `docs/next-phase-v2/13-patentiq-v2-cross-layer-dbdiagram.dbml`
13. updated `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
14. updated `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
15. updated `etl/README.md`

### Methods

1. Added a separate heritage chunk planner and runner for the `1996-2006` backfill horizon.
2. Kept the heritage export lighter by default through dedicated table-family and worker defaults.
3. Added stage aliases for:
   - `plan-tip-heritage-export`
   - `prebronze-heritage`
4. Added dedicated Gold heritage marts:
   - `gold_family_heritage_summary`
   - `gold_portfolio_heritage_summary`

### Calculations

1. Heritage chunk plans now use the configured `heritage_backfill_start` and `heritage_backfill_end` bounds.
2. Heritage chunk ids are prefixed with `heritage__` and upload to `raw-bounded-heritage/...`.
3. Portfolio heritage summaries aggregate the family-level heritage proxy across all families in the portfolio heritage scope and count how many come from the heritage backfill horizon.

### Downstream Impacts

1. The ETL now has a first-class runtime stage for historical backfill extraction rather than only policy documentation.
2. Current-state and historical heritage Gold outputs are now separated more cleanly.
3. A later non-TIP consolidation environment can ingest main and heritage bounded raw horizons independently.

### Governing Docs

1. `docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md`
2. `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`
3. `docs/next-phase-v2/13-patentiq-v2-cross-layer-dbdiagram.dbml`

### Warnings

1. The heritage extraction runtime now exists, but Bronze/Silver end-to-end consolidation from a separately materialized heritage bounded-raw horizon still needs a dedicated downstream merge path if you want one-command full historical builds.

## 2026-03-17 | TIP Chunk Runtime Parallelism And Live Logging | success

### Inputs

1. current TIP chunk planner and sequential chunk executor
2. TIP operating constraints:
   - `4 CPU cores`
   - `32 GB RAM`
   - `30 GB local disk`
3. need for Azure upload tuning and richer runtime visibility beyond end-of-chunk manifests

### Files Updated

1. updated `etl/conf/build.yaml`
2. updated `etl/src/patentiq_etl/prebronze/chunked.py`
3. new `etl/tests/test_tip_chunked_runtime.py`
4. updated `etl/README.md`
5. updated `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`
6. updated `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md`

### Methods

1. Replaced the fully sequential chunk loop with a bounded thread-pool scheduler.
2. Applied a global chunk concurrency cap plus family-level concurrency caps from the configured worker map.
3. Added Azure Blob upload tuning through:
   - `upload_max_concurrency`
   - `upload_max_block_size_mb`
   - `upload_max_single_put_size_mb`
4. Added live stage logging and JSONL event emission for:
   - chunk submission
   - scope readiness
   - extraction start and finish
   - blob upload start and finish
   - cleanup start and finish
   - chunk completion
5. Enriched chunk manifests with:
   - `started_at`
   - `finished_at`
   - `duration_seconds`

### Calculations

1. Main-horizon chunk execution now defaults to `tip_max_parallel_chunks = 2`.
2. Heritage chunk execution now defaults to `heritage_max_parallel_chunks = 1`.
3. Upload tuning now defaults to:
   - `upload_max_concurrency = 3`
   - `upload_max_block_size_mb = 8`
   - `upload_max_single_put_size_mb = 16`

### Downstream Impacts

1. TIP can now overlap a small number of chunk jobs without violating the intended memory and disk envelope.
2. Azure uploads no longer rely on a purely untuned one-file-at-a-time path.
3. Operators can watch real-time execution through:
   - `etl/manifests/stages/pre-bronze-chunked-export.log`
   - `etl/manifests/stages/pre-bronze-chunked-export.events.jsonl`

### Verification

1. `pytest etl/tests/test_tip_chunk_plan.py etl/tests/test_tip_chunked_runtime.py etl/tests/test_prebronze_extraction.py etl/tests/test_source_certification.py etl/tests/test_uspto_bulk_xml.py -q`
2. `python3 -m compileall etl/src etl/scripts etl/tests`

### Warnings

1. The scheduler is intentionally conservative and should not be treated as a license to run four heavy extraction families in parallel inside TIP.
2. Azure Blob multipart tuning is now wired into the ETL path, but final throughput still depends on the real network and storage-account characteristics of the target TIP environment.
<<<<<<< Updated upstream

## 2026-03-19 | TIP Blob Recovery Stage | success

### Inputs

1. successful chunk manifests with empty `uploaded_blobs`
2. preserved local chunk parquet files under `etl/data/temp/chunks`
3. deterministic chunk Blob prefix contract already used by the normal TIP executor

### Files Updated

1. updated `etl/src/patentiq_etl/prebronze/chunked.py`
2. updated `etl/src/patentiq_etl/prebronze/run.py`
3. updated `etl/scripts/run_stage.py`
4. updated `etl/tests/test_tip_chunked_runtime.py`
5. updated `etl/README.md`

### Methods

1. Added a standalone recovery stage that scans chunk manifests for:
   - `status = success`
   - empty `uploaded_blobs`
   - still-present local outputs
2. Reused the deterministic chunk Blob prefixes instead of inventing a new recovery layout.
3. Updated recovered manifests in place with the uploaded blob names and `recovered_at` timestamp.
4. Applied cleanup to recovered temp directories when `cleanup_after_upload` is enabled.

### Downstream Impacts

1. Expensive TIP chunks no longer need to be recomputed just because Blob upload was inactive during one earlier run.
2. Resume semantics can now be repaired after the fact by aligning the manifest state with the real Blob state.

### Verification

1. `pytest etl/tests/test_tip_chunked_runtime.py etl/tests/test_tip_clients.py etl/tests/test_tip_chunk_plan.py -q`
2. `python3 -m compileall etl/src etl/scripts etl/tests`

### Warnings

1. The normal chunk runner still skips any manifest with `status = success`, so recovery remains a separate stage rather than part of the default rerun path.
2. Recovery now also handles chunks that failed during Blob upload after local parquet generation, but it still assumes the preserved local outputs are trustworthy bounded chunk outputs.

## 2026-03-20 | Chunked TIP Global Seed Materialization | success

### Inputs

1. chunked TIP pre-Bronze runtime configuration
2. existing PATSTAT TIP seed builder logic
3. existing successful-chunk resume semantics

### Files Updated

1. updated `etl/src/patentiq_etl/prebronze/extract.py`
2. updated `etl/src/patentiq_etl/prebronze/chunked.py`
3. updated `etl/tests/test_tip_chunked_runtime.py`
4. updated `etl/README.md`

### Methods

1. Added an explicit global seed materialization phase at the start of chunked TIP `prebronze`.
2. Reused the existing TIP seed builder instead of introducing a second seed implementation.
3. Uploaded the resulting `_seeds/*.parquet` artifacts to the deterministic Blob seed prefix for the active horizon.
4. Reused the seed parquet set on rerun when all required seed files already exist.

### Downstream Impacts

1. `seed_us_publication_numbers.parquet` and the other bounded seed artifacts are now always available to later consumers such as the local USPTO ODP worker.
2. The chunked TIP path now matches the documented execution contract more closely because seeds are generated once up front rather than only implied by per-chunk scope building.
3. Existing restart semantics remain unchanged: already-successful chunks are still skipped on rerun.

### Verification

1. `pytest etl/tests/test_tip_chunked_runtime.py etl/tests/test_tip_chunk_plan.py etl/tests/test_tip_clients.py etl/tests/test_prebronze_extraction.py -q`
2. `python3 -m compileall etl/src etl/scripts etl/tests`

### Warnings

1. The chunk runner still skips successful chunk manifests without checking remote Blob state, so missing historical uploads still need the separate recovery stage.
=======
## tip-chunk-plan | success

- Summary: Generated the TIP chunked export plan for Blob-first full-scope extraction.
- Started: 2026-03-17T22:22:16+00:00
- Finished: 2026-03-17T22:22:16+00:00


### Outputs

1. /home/jovyan/patent-iq/etl/manifests/chunks
2. /home/jovyan/patent-iq/etl/manifests/chunks/tip_chunk_plan.json

### Artifacts

- `stats_snapshot`: `/home/jovyan/patent-iq/etl/manifests/stats/tip-chunk-plan.json`

### Methods

1. Split the configured mega-cluster scope into field and year buckets.
2. Assigned recommended worker counts per table family according to the documented TIP resource envelope.
3. Prepared deterministic chunk ids and Blob prefixes for resumable export.

### Calculations

1. Chunk ids are built from field slug + year bucket + table family.
2. Year buckets use the configured chunk span across the configured ETL year window.

### Downstream Impacts

1. This plan drives Blob-first pre-Bronze extraction instead of monolithic local bounded-raw materialization inside TIP.
2. Chunk manifests enable resume, retry, and local cleanup after verified upload.

### Governing Docs

1. docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md
3. docs/data/epo-tip-client-usage.md


### Metrics

- `chunk_plan_field_count`: `10`
- `chunk_plan_year_bucket_count`: `7`
- `chunk_plan_table_family_count`: `6`
- `chunk_plan_total_chunk_count`: `420`
- `chunk_plan_max_worker_sum`: `8`

>>>>>>> Stashed changes
## tip-blob-recovery | failed

- Summary: Recovered Blob uploads for TIP chunk manifests whose local outputs remained on disk after missing or failed Blob offload.
- Started: 2026-03-21T10:35:55+00:00
- Finished: 2026-03-21T10:35:55+00:00



### Artifacts

- `live_event_log`: `/home/jovyan/patent-iq/etl/manifests/stages/tip-blob-recovery.events.jsonl`
- `stats_snapshot`: `/home/jovyan/patent-iq/etl/manifests/stats/tip-blob-recovery.json`

### Methods

1. Scanned chunk manifests for successful or upload-failed chunks with missing or incomplete Blob upload metadata.
2. Uploaded any still-present local outputs to the deterministic chunk Blob prefixes.
3. Updated manifests with recovered uploaded_blobs entries, restored upload-failed chunks to success when appropriate, and cleaned local temp directories when configured.

### Calculations

1. Recovery eligibility requires still-present local outputs plus either a successful manifest with incomplete uploaded_blobs or a failed manifest whose warnings indicate Blob/upload timeout behavior.
2. Recovered Blob prefixes reuse the same deterministic field/year/table-family layout as the normal chunk executor.

### Downstream Impacts

1. This stage repairs interrupted or misconfigured Blob offload without rerunning expensive TIP extraction work.
2. Recovered chunk manifests become consistent with later non-TIP consolidation expectations.

### Governing Docs

1. docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. Azure blob intermediate upload is enabled but environment variable `AZURE_STORAGE_CONNECTION_STRING` is not set.

### Metrics

- `recovery_upload_max_concurrency`: `2`
- `recovery_upload_max_block_size_mb`: `4`
- `recovery_upload_max_single_put_size_mb`: `8`

## tip-blob-recovery | failed

- Summary: Recovered Blob uploads for TIP chunk manifests whose local outputs remained on disk after missing or failed Blob offload.
- Started: 2026-03-23T18:07:11+00:00
- Finished: 2026-03-23T18:07:11+00:00



### Artifacts

- `live_event_log`: `/home/jovyan/patent-iq/etl/manifests/stages/tip-blob-recovery.events.jsonl`
- `stats_snapshot`: `/home/jovyan/patent-iq/etl/manifests/stats/tip-blob-recovery.json`

### Methods

1. Scanned chunk manifests for successful or upload-failed chunks with missing or incomplete Blob upload metadata.
2. Uploaded any still-present local outputs to the deterministic chunk Blob prefixes.
3. Updated manifests with recovered uploaded_blobs entries, restored upload-failed chunks to success when appropriate, and cleaned local temp directories when configured.

### Calculations

1. Recovery eligibility requires still-present local outputs plus either a successful manifest with incomplete uploaded_blobs or a failed manifest whose warnings indicate Blob/upload timeout behavior.
2. Recovered Blob prefixes reuse the same deterministic field/year/table-family layout as the normal chunk executor.

### Downstream Impacts

1. This stage repairs interrupted or misconfigured Blob offload without rerunning expensive TIP extraction work.
2. Recovered chunk manifests become consistent with later non-TIP consolidation expectations.

### Governing Docs

1. docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. No module named 'azure'

### Metrics

- `recovery_upload_max_concurrency`: `2`
- `recovery_upload_max_block_size_mb`: `4`
- `recovery_upload_max_single_put_size_mb`: `8`

## tip-blob-recovery | success

- Summary: Recovered Blob uploads for TIP chunk manifests whose local outputs remained on disk after missing or failed Blob offload.
- Started: 2026-03-23T18:07:45+00:00
- Finished: 2026-03-23T18:18:15+00:00


### Outputs

1. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2007_2008__core.json
2. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2007_2008__epab.json
3. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2007_2008__legal.json
4. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2007_2008__publications.json
5. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2007_2008__register.json
6. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2007_2009__citations.json
7. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2009_2010__citations.json
8. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2009_2010__core.json
9. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2009_2010__epab.json
10. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2009_2010__legal.json
11. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2009_2010__publications.json
12. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2009_2010__register.json
13. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2010_2012__citations.json
14. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2011_2012__citations.json
15. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2011_2012__core.json
16. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2011_2012__epab.json
17. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2011_2012__legal.json
18. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2011_2012__publications.json
19. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2011_2012__register.json
20. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2013_2014__citations.json
21. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2013_2014__core.json
22. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2013_2014__epab.json
23. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2013_2014__legal.json
24. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2013_2014__publications.json
25. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2013_2014__register.json
26. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2013_2015__citations.json
27. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2015_2016__citations.json
28. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2015_2016__core.json
29. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2015_2016__epab.json
30. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2015_2016__legal.json
31. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2015_2016__publications.json
32. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2015_2016__register.json
33. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2016_2018__citations.json
34. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2017_2018__citations.json
35. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2017_2018__core.json
36. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2017_2018__epab.json
37. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2017_2018__legal.json
38. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2017_2018__publications.json
39. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2017_2018__register.json
40. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2019_2020__citations.json
41. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2019_2020__core.json
42. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2019_2020__epab.json
43. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2019_2020__legal.json
44. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2019_2020__publications.json
45. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2019_2020__register.json
46. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2019_2021__citations.json
47. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2021_2022__citations.json
48. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2021_2022__core.json
49. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2021_2022__epab.json
50. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2021_2022__legal.json
51. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2021_2022__publications.json
52. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2021_2022__register.json
53. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2022_2024__citations.json
54. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2023_2024__citations.json
55. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2023_2024__core.json
56. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2023_2024__epab.json
57. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2023_2024__legal.json
58. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2023_2024__publications.json
59. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2023_2024__register.json
60. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2025_2026__citations.json
61. /home/jovyan/patent-iq/etl/manifests/chunks/audio-visual-technology__2025_2026__epab.json
62. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2007_2008__citations.json
63. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2007_2008__core.json
64. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2007_2008__legal.json
65. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2007_2008__publications.json
66. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2007_2008__register.json
67. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2007_2009__citations.json
68. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2009_2010__citations.json
69. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2009_2010__core.json
70. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2009_2010__legal.json
71. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2009_2010__publications.json
72. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2009_2010__register.json
73. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2010_2012__citations.json
74. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2011_2012__citations.json
75. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2011_2012__core.json
76. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2011_2012__legal.json
77. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2011_2012__publications.json
78. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2011_2012__register.json
79. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2013_2014__citations.json
80. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2013_2014__core.json
81. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2013_2014__legal.json
82. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2013_2014__publications.json
83. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2013_2014__register.json
84. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2013_2015__citations.json
85. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2015_2016__citations.json
86. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2015_2016__core.json
87. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2015_2016__legal.json
88. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2015_2016__publications.json
89. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2015_2016__register.json
90. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2016_2018__citations.json
91. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2017_2018__citations.json
92. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2017_2018__core.json
93. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2017_2018__legal.json
94. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2017_2018__publications.json
95. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2017_2018__register.json
96. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2019_2020__citations.json
97. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2019_2020__core.json
98. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2019_2020__legal.json
99. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2019_2020__publications.json
100. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2019_2020__register.json
101. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2019_2021__citations.json
102. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2021_2022__citations.json
103. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2021_2022__core.json
104. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2021_2022__legal.json
105. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2021_2022__publications.json
106. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2021_2022__register.json
107. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2022_2024__citations.json
108. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2023_2024__citations.json
109. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2023_2024__core.json
110. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2023_2024__legal.json
111. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2023_2024__publications.json
112. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2023_2024__register.json
113. /home/jovyan/patent-iq/etl/manifests/chunks/basic-communication-processes__2025_2026__citations.json
114. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2007_2008__citations.json
115. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2007_2008__core.json
116. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2007_2008__legal.json
117. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2007_2008__publications.json
118. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2007_2008__register.json
119. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2007_2009__citations.json
120. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2009_2010__citations.json
121. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2009_2010__core.json
122. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2009_2010__legal.json
123. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2009_2010__publications.json
124. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2009_2010__register.json
125. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2010_2012__citations.json
126. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2011_2012__citations.json
127. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2011_2012__core.json
128. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2011_2012__legal.json
129. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2011_2012__publications.json
130. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2011_2012__register.json
131. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2013_2014__citations.json
132. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2013_2014__core.json
133. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2013_2014__legal.json
134. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2013_2014__publications.json
135. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2013_2014__register.json
136. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2013_2015__citations.json
137. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2013_2015__legal.json
138. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2013_2015__register.json
139. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2015_2016__citations.json
140. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2015_2016__core.json
141. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2015_2016__legal.json
142. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2015_2016__publications.json
143. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2015_2016__register.json
144. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2016_2018__core.json
145. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2016_2018__publications.json
146. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2017_2018__citations.json
147. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2017_2018__core.json
148. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2017_2018__legal.json
149. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2017_2018__publications.json
150. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2017_2018__register.json
151. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2019_2020__citations.json
152. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2019_2020__core.json
153. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2019_2020__legal.json
154. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2019_2020__publications.json
155. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2019_2020__register.json
156. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2021_2022__citations.json
157. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2021_2022__core.json
158. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2021_2022__legal.json
159. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2021_2022__publications.json
160. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2021_2022__register.json
161. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2023_2024__citations.json
162. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2023_2024__core.json
163. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2023_2024__legal.json
164. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2023_2024__publications.json
165. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2023_2024__register.json
166. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2025_2026__citations.json
167. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2025_2026__core.json
168. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2025_2026__legal.json
169. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2025_2026__publications.json
170. /home/jovyan/patent-iq/etl/manifests/chunks/computer-technology__2025_2026__register.json
171. /home/jovyan/patent-iq/etl/manifests/chunks/control__2007_2008__citations.json
172. /home/jovyan/patent-iq/etl/manifests/chunks/control__2007_2008__core.json
173. /home/jovyan/patent-iq/etl/manifests/chunks/control__2007_2008__legal.json
174. /home/jovyan/patent-iq/etl/manifests/chunks/control__2007_2008__publications.json
175. /home/jovyan/patent-iq/etl/manifests/chunks/control__2007_2008__register.json
176. /home/jovyan/patent-iq/etl/manifests/chunks/control__2009_2010__citations.json
177. /home/jovyan/patent-iq/etl/manifests/chunks/control__2009_2010__core.json
178. /home/jovyan/patent-iq/etl/manifests/chunks/control__2009_2010__legal.json
179. /home/jovyan/patent-iq/etl/manifests/chunks/control__2009_2010__publications.json
180. /home/jovyan/patent-iq/etl/manifests/chunks/control__2009_2010__register.json
181. /home/jovyan/patent-iq/etl/manifests/chunks/control__2011_2012__citations.json
182. /home/jovyan/patent-iq/etl/manifests/chunks/control__2011_2012__core.json
183. /home/jovyan/patent-iq/etl/manifests/chunks/control__2011_2012__legal.json
184. /home/jovyan/patent-iq/etl/manifests/chunks/control__2011_2012__publications.json
185. /home/jovyan/patent-iq/etl/manifests/chunks/control__2011_2012__register.json
186. /home/jovyan/patent-iq/etl/manifests/chunks/control__2013_2014__citations.json
187. /home/jovyan/patent-iq/etl/manifests/chunks/control__2013_2014__core.json
188. /home/jovyan/patent-iq/etl/manifests/chunks/control__2013_2014__legal.json
189. /home/jovyan/patent-iq/etl/manifests/chunks/control__2013_2014__publications.json
190. /home/jovyan/patent-iq/etl/manifests/chunks/control__2013_2014__register.json
191. /home/jovyan/patent-iq/etl/manifests/chunks/control__2015_2016__citations.json
192. /home/jovyan/patent-iq/etl/manifests/chunks/control__2015_2016__core.json
193. /home/jovyan/patent-iq/etl/manifests/chunks/control__2015_2016__legal.json
194. /home/jovyan/patent-iq/etl/manifests/chunks/control__2015_2016__publications.json
195. /home/jovyan/patent-iq/etl/manifests/chunks/control__2015_2016__register.json
196. /home/jovyan/patent-iq/etl/manifests/chunks/control__2017_2018__citations.json
197. /home/jovyan/patent-iq/etl/manifests/chunks/control__2017_2018__core.json
198. /home/jovyan/patent-iq/etl/manifests/chunks/control__2017_2018__legal.json
199. /home/jovyan/patent-iq/etl/manifests/chunks/control__2017_2018__publications.json
200. /home/jovyan/patent-iq/etl/manifests/chunks/control__2017_2018__register.json
201. /home/jovyan/patent-iq/etl/manifests/chunks/control__2019_2020__citations.json
202. /home/jovyan/patent-iq/etl/manifests/chunks/control__2019_2020__core.json
203. /home/jovyan/patent-iq/etl/manifests/chunks/control__2019_2020__legal.json
204. /home/jovyan/patent-iq/etl/manifests/chunks/control__2019_2020__publications.json
205. /home/jovyan/patent-iq/etl/manifests/chunks/control__2019_2020__register.json
206. /home/jovyan/patent-iq/etl/manifests/chunks/control__2021_2022__citations.json
207. /home/jovyan/patent-iq/etl/manifests/chunks/control__2021_2022__core.json
208. /home/jovyan/patent-iq/etl/manifests/chunks/control__2021_2022__legal.json
209. /home/jovyan/patent-iq/etl/manifests/chunks/control__2021_2022__publications.json
210. /home/jovyan/patent-iq/etl/manifests/chunks/control__2021_2022__register.json
211. /home/jovyan/patent-iq/etl/manifests/chunks/control__2023_2024__citations.json
212. /home/jovyan/patent-iq/etl/manifests/chunks/control__2023_2024__core.json
213. /home/jovyan/patent-iq/etl/manifests/chunks/control__2023_2024__legal.json
214. /home/jovyan/patent-iq/etl/manifests/chunks/control__2023_2024__publications.json
215. /home/jovyan/patent-iq/etl/manifests/chunks/control__2023_2024__register.json
216. /home/jovyan/patent-iq/etl/manifests/chunks/control__2025_2026__citations.json
217. /home/jovyan/patent-iq/etl/manifests/chunks/control__2025_2026__core.json
218. /home/jovyan/patent-iq/etl/manifests/chunks/control__2025_2026__legal.json
219. /home/jovyan/patent-iq/etl/manifests/chunks/control__2025_2026__publications.json
220. /home/jovyan/patent-iq/etl/manifests/chunks/control__2025_2026__register.json
221. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2007_2008__citations.json
222. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2007_2008__core.json
223. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2007_2008__legal.json
224. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2007_2008__publications.json
225. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2007_2008__register.json
226. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2007_2009__citations.json
227. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2009_2010__citations.json
228. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2009_2010__core.json
229. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2009_2010__legal.json
230. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2009_2010__publications.json
231. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2009_2010__register.json
232. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2010_2012__citations.json
233. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2011_2012__citations.json
234. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2011_2012__core.json
235. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2011_2012__legal.json
236. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2011_2012__publications.json
237. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2011_2012__register.json
238. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2013_2014__citations.json
239. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2013_2014__core.json
240. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2013_2014__legal.json
241. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2013_2014__publications.json
242. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2013_2014__register.json
243. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2013_2015__citations.json
244. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2015_2016__citations.json
245. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2015_2016__core.json
246. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2015_2016__legal.json
247. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2015_2016__publications.json
248. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2015_2016__register.json
249. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2016_2018__citations.json
250. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2017_2018__citations.json
251. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2017_2018__core.json
252. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2017_2018__legal.json
253. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2017_2018__publications.json
254. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2017_2018__register.json
255. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2019_2020__citations.json
256. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2019_2020__core.json
257. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2019_2020__legal.json
258. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2019_2020__publications.json
259. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2019_2020__register.json
260. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2019_2021__citations.json
261. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2021_2022__citations.json
262. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2021_2022__core.json
263. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2021_2022__legal.json
264. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2021_2022__publications.json
265. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2021_2022__register.json
266. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2022_2024__citations.json
267. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2023_2024__citations.json
268. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2023_2024__core.json
269. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2023_2024__legal.json
270. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2023_2024__publications.json
271. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2023_2024__register.json
272. /home/jovyan/patent-iq/etl/manifests/chunks/digital-communication__2025_2026__citations.json
273. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2007_2008__citations.json
274. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2007_2008__core.json
275. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2007_2008__legal.json
276. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2007_2008__publications.json
277. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2007_2008__register.json
278. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2009_2010__citations.json
279. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2009_2010__core.json
280. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2009_2010__legal.json
281. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2009_2010__publications.json
282. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2009_2010__register.json
283. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2011_2012__citations.json
284. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2011_2012__core.json
285. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2011_2012__legal.json
286. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2011_2012__publications.json
287. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2011_2012__register.json
288. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2013_2014__citations.json
289. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2013_2014__core.json
290. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2013_2014__legal.json
291. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2013_2014__publications.json
292. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2013_2014__register.json
293. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2015_2016__citations.json
294. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2015_2016__core.json
295. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2015_2016__legal.json
296. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2015_2016__publications.json
297. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2015_2016__register.json
298. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2017_2018__citations.json
299. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2017_2018__core.json
300. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2017_2018__legal.json
301. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2017_2018__publications.json
302. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2017_2018__register.json
303. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2019_2020__citations.json
304. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2019_2020__core.json
305. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2019_2020__legal.json
306. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2019_2020__publications.json
307. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2019_2020__register.json
308. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2021_2022__citations.json
309. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2021_2022__core.json
310. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2021_2022__legal.json
311. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2021_2022__publications.json
312. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2021_2022__register.json
313. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2023_2024__citations.json
314. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2023_2024__core.json
315. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2023_2024__legal.json
316. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2023_2024__publications.json
317. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2023_2024__register.json
318. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2025_2026__citations.json
319. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2025_2026__core.json
320. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2025_2026__legal.json
321. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2025_2026__publications.json
322. /home/jovyan/patent-iq/etl/manifests/chunks/electrical-machinery-apparatus-energy__2025_2026__register.json
323. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2007_2008__citations.json
324. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2007_2008__core.json
325. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2007_2008__legal.json
326. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2007_2008__publications.json
327. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2007_2008__register.json
328. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2009_2010__citations.json
329. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2009_2010__core.json
330. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2009_2010__legal.json
331. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2009_2010__publications.json
332. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2009_2010__register.json
333. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2021_2022__citations.json
334. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2021_2022__legal.json
335. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2021_2022__publications.json
336. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2023_2024__citations.json
337. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2023_2024__core.json
338. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2023_2024__legal.json
339. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2023_2024__publications.json
340. /home/jovyan/patent-iq/etl/manifests/chunks/it-methods-for-management__2025_2026__core.json
341. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2007_2008__core.json
342. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2007_2008__legal.json
343. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2007_2008__publications.json
344. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2009_2010__citations.json
345. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2009_2010__core.json
346. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2009_2010__legal.json
347. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2009_2010__publications.json
348. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2011_2012__citations.json
349. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2011_2012__core.json
350. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2011_2012__legal.json
351. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2011_2012__publications.json
352. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2013_2014__citations.json
353. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2013_2014__core.json
354. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2013_2014__legal.json
355. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2013_2014__publications.json
356. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2015_2016__citations.json
357. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2015_2016__core.json
358. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2015_2016__legal.json
359. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2015_2016__publications.json
360. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2017_2018__citations.json
361. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2017_2018__core.json
362. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2017_2018__legal.json
363. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2017_2018__publications.json
364. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2019_2020__citations.json
365. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2019_2020__core.json
366. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2019_2020__legal.json
367. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2019_2020__publications.json
368. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2021_2022__citations.json
369. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2021_2022__core.json
370. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2021_2022__legal.json
371. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2021_2022__publications.json
372. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2021_2022__register.json
373. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2023_2024__citations.json
374. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2023_2024__core.json
375. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2023_2024__legal.json
376. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2023_2024__publications.json
377. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2023_2024__register.json
378. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2025_2026__citations.json
379. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2025_2026__core.json
380. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2025_2026__legal.json
381. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2025_2026__publications.json
382. /home/jovyan/patent-iq/etl/manifests/chunks/measurement__2025_2026__register.json
383. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2007_2008__core.json
384. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2007_2008__legal.json
385. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2009_2010__core.json
386. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2009_2010__legal.json
387. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2009_2010__publications.json
388. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2011_2012__core.json
389. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2011_2012__legal.json
390. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2011_2012__publications.json
391. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2013_2014__core.json
392. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2013_2014__legal.json
393. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2013_2014__publications.json
394. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2015_2016__core.json
395. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2015_2016__legal.json
396. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2015_2016__publications.json
397. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2017_2018__core.json
398. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2017_2018__legal.json
399. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2017_2018__publications.json
400. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2019_2020__core.json
401. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2019_2020__legal.json
402. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2019_2020__publications.json
403. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2021_2022__core.json
404. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2021_2022__legal.json
405. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2021_2022__publications.json
406. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2023_2024__core.json
407. /home/jovyan/patent-iq/etl/manifests/chunks/semiconductors__2023_2024__legal.json
408. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2007_2008__citations.json
409. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2007_2008__core.json
410. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2007_2008__epab.json
411. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2007_2008__legal.json
412. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2007_2008__publications.json
413. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2007_2008__register.json
414. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2007_2009__citations.json
415. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2009_2010__citations.json
416. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2009_2010__core.json
417. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2009_2010__epab.json
418. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2009_2010__legal.json
419. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2009_2010__publications.json
420. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2009_2010__register.json
421. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2010_2012__citations.json
422. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2011_2012__citations.json
423. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2011_2012__core.json
424. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2011_2012__epab.json
425. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2011_2012__legal.json
426. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2011_2012__publications.json
427. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2011_2012__register.json
428. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2013_2014__citations.json
429. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2013_2014__core.json
430. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2013_2014__epab.json
431. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2013_2014__legal.json
432. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2013_2014__publications.json
433. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2013_2014__register.json
434. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2013_2015__citations.json
435. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2015_2016__citations.json
436. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2015_2016__core.json
437. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2015_2016__epab.json
438. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2015_2016__legal.json
439. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2015_2016__publications.json
440. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2015_2016__register.json
441. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2016_2018__citations.json
442. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2017_2018__citations.json
443. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2017_2018__core.json
444. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2017_2018__epab.json
445. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2017_2018__legal.json
446. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2017_2018__publications.json
447. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2017_2018__register.json
448. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2019_2020__citations.json
449. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2019_2020__core.json
450. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2019_2020__epab.json
451. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2019_2020__legal.json
452. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2019_2020__publications.json
453. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2019_2020__register.json
454. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2019_2021__citations.json
455. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2021_2022__citations.json
456. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2021_2022__core.json
457. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2021_2022__epab.json
458. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2021_2022__legal.json
459. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2021_2022__publications.json
460. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2021_2022__register.json
461. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2022_2024__citations.json
462. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2023_2024__citations.json
463. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2023_2024__core.json
464. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2023_2024__legal.json
465. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2023_2024__publications.json
466. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2023_2024__register.json
467. /home/jovyan/patent-iq/etl/manifests/chunks/telecommunications__2025_2026__citations.json

### Artifacts

- `live_event_log`: `/home/jovyan/patent-iq/etl/manifests/stages/tip-blob-recovery.events.jsonl`
- `stats_snapshot`: `/home/jovyan/patent-iq/etl/manifests/stats/tip-blob-recovery.json`

### Methods

1. Scanned chunk manifests for successful or upload-failed chunks with missing or incomplete Blob upload metadata.
2. Uploaded any still-present local outputs to the deterministic chunk Blob prefixes.
3. Updated manifests with recovered uploaded_blobs entries, restored upload-failed chunks to success when appropriate, and cleaned local temp directories when configured.

### Calculations

1. Recovery eligibility requires still-present local outputs plus either a successful manifest with incomplete uploaded_blobs or a failed manifest whose warnings indicate Blob/upload timeout behavior.
2. Recovered Blob prefixes reuse the same deterministic field/year/table-family layout as the normal chunk executor.

### Downstream Impacts

1. This stage repairs interrupted or misconfigured Blob offload without rerunning expensive TIP extraction work.
2. Recovered chunk manifests become consistent with later non-TIP consolidation expectations.

### Governing Docs

1. docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `recovery_upload_max_concurrency`: `2`
- `recovery_upload_max_block_size_mb`: `4`
- `recovery_upload_max_single_put_size_mb`: `8`
- `recovery_manifest_count`: `657`
- `recovery_recoverable_chunk_count`: `467`
- `recovery_recovered_chunk_count`: `467`
- `recovery_skipped_uploaded_chunk_count`: `189`
- `recovery_missing_output_chunk_count`: `0`
- `recovery_ineligible_failed_chunk_count`: `0`
- `recovery_uploaded_blob_count`: `2647`

## pre-bronze-chunked-export | success

- Summary: Executed chunked TIP pre-Bronze extraction with Blob-first chunk manifests and local cleanup support.
- Started: 2026-03-23T18:23:19+00:00
- Finished: 2026-03-23T18:23:50+00:00


### Outputs

1. /home/jovyan/patent-iq/etl/manifests/chunks
2. /home/jovyan/patent-iq/etl/manifests/chunks/tip_chunk_plan.json
3. /home/jovyan/patent-iq/etl/data/raw-bounded/_seeds/seed_appln_ids.parquet
4. /home/jovyan/patent-iq/etl/data/raw-bounded/_seeds/seed_family_ids.parquet
5. /home/jovyan/patent-iq/etl/data/raw-bounded/_seeds/seed_ep_appln_ids.parquet
6. /home/jovyan/patent-iq/etl/data/raw-bounded/_seeds/seed_family_field_counts.parquet
7. /home/jovyan/patent-iq/etl/data/raw-bounded/_seeds/seed_publn_ids.parquet
8. /home/jovyan/patent-iq/etl/data/raw-bounded/_seeds/seed_person_ids.parquet
9. /home/jovyan/patent-iq/etl/data/raw-bounded/_seeds/seed_us_publication_numbers.parquet
10. /home/jovyan/patent-iq/etl/data/raw-bounded/_seeds/seed_ep_publication_numbers.parquet

### Artifacts

- `live_event_log`: `/home/jovyan/patent-iq/etl/manifests/stages/pre-bronze-chunked-export.events.jsonl`
- `stats_snapshot`: `/home/jovyan/patent-iq/etl/manifests/stats/pre-bronze-chunked-export.json`

### Methods

1. Planned field/year/table-family chunks before extraction.
2. Built chunk-local bounded scope directly from TIP instead of materializing one monolithic bounded raw layer.
3. Uploaded chunk artifacts to Azure Blob when configured, then optionally cleaned local chunk temp directories.

### Calculations

1. Chunk ids are deterministic field/year/table-family keys.
2. Per-chunk scope is bounded by both selected WIPO field and configured year bucket.

### Downstream Impacts

1. Successful chunk manifests allow resumable pre-Bronze extraction across constrained TIP sessions.
2. Chunk-local Blob prefixes become the authoritative bounded raw intermediate store for later non-TIP Bronze/Silver/Gold consolidation.

### Governing Docs

1. docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md
3. docs/data/epo-tip-client-usage.md

### Warnings

1. Skipped `bronze_ref_techn_field_ipc` because no source file was found.
2. Skipped `bronze_ext_cpc_coverage` because no source file was found.
3. Skipped `bronze_ext_cpc_ipc_weights` because no source file was found.
4. Skipped `bronze_ext_iso_country_map` because no source file was found.
5. Skipped `bronze_ext_world_bank_gdp_ppp` because no source file was found.
6. Skipped `bronze_ext_us_chamber_ip_index` because no source file was found.
7. Skipped `bronze_ext_up_member_states` because no source file was found.
8. Skipped `bronze_ext_kind_code_normalization_seed` because no source file was found.
9. Skipped `bronze_ext_oecd_indicator_seed` because no source file was found.

### Metrics

- `chunk_scheduler_parallel_limit`: `2`
- `chunk_upload_max_concurrency`: `2`
- `chunk_upload_max_block_size_mb`: `4`
- `chunk_upload_max_single_put_size_mb`: `8`
- `global_seed_initial_file_count`: `4`
- `global_seed_dir`: `/home/jovyan/patent-iq/etl/data/raw-bounded/_seeds`
- `refs_uploaded_blob_count`: `0`
- `global_seed_file_count`: `8`
- `global_seed_derived_file_count`: `4`
- `chunk_total_count`: `500`
- `chunk_skipped_count`: `500`
- `chunk_failed_count`: `0`
- `chunk_degraded_count`: `0`
- `chunk_uploaded_file_count`: `0`

## tip-heritage-chunk-plan | success

- Summary: Generated the TIP heritage-backfill chunk plan for older mega-cluster family and citation support.
- Started: 2026-03-23T18:32:45+00:00
- Finished: 2026-03-23T18:32:45+00:00


### Outputs

1. /home/jovyan/patent-iq/etl/manifests/chunks
2. /home/jovyan/patent-iq/etl/manifests/chunks/tip_heritage_chunk_plan.json

### Artifacts

- `stats_snapshot`: `/home/jovyan/patent-iq/etl/manifests/stats/tip-heritage-chunk-plan.json`

### Methods

1. Split the configured mega-cluster scope into field and year buckets.
2. Assigned recommended worker counts per table family according to the documented TIP resource envelope.
3. Prepared deterministic chunk ids and Blob prefixes for resumable export.

### Calculations

1. Chunk ids are built from field slug + year bucket + table family.
2. Year buckets use the configured chunk span across the configured ETL year window.

### Downstream Impacts

1. This plan drives Blob-first pre-Bronze extraction instead of monolithic local bounded-raw materialization inside TIP.
2. Chunk manifests enable resume, retry, and local cleanup after verified upload.

### Governing Docs

1. docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md
3. docs/data/epo-tip-client-usage.md
4. docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md


### Metrics

- `chunk_plan_field_count`: `10`
- `chunk_plan_year_bucket_count`: `6`
- `chunk_plan_table_family_count`: `3`
- `chunk_plan_total_chunk_count`: `180`
- `chunk_plan_max_worker_sum`: `3`

## tip-derived-seed-backfill | success

- Summary: Backfilled canonical derived TIP seed parquet files from successful chunk outputs already present locally, already uploaded to Blob, or previously materialized as chunk-derived sidecars.
- Started: 2026-03-23T19:40:11+00:00
- Finished: 2026-03-23T20:27:28+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/_seeds/seed_publn_ids.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/_seeds/seed_person_ids.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/_seeds/seed_us_publication_numbers.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/_seeds/seed_ep_publication_numbers.parquet

### Artifacts

- `live_event_log`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stages/tip-derived-seed-backfill.events.jsonl`
- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/tip-derived-seed-backfill.json`

### Methods

1. Scanned successful chunk manifests for `core` and `publications` families.
2. Reused existing chunk-derived seed sidecars when present, otherwise derived them from local chunk parquet or downloaded Blob chunk parquet.
3. Consolidated all reachable chunk-derived sidecars into canonical seed parquet outputs for publication and person seeds.

### Calculations

1. Local successful chunk outputs take precedence over Blob fallback because they avoid redundant transfer and preserve the exact local extraction result.
2. Canonical derived seed outputs are rebuilt via DuckDB `select distinct *` across per-chunk sidecars to avoid full-universe pandas materialization on TIP.

### Downstream Impacts

1. This stage repairs mixed historical TIP states where some successful chunks were already cleaned after Blob upload while others remain only locally.
2. Rebuilt canonical seed files support later USPTO/local follow-on stages without forcing expensive chunk reruns.

### Governing Docs

1. docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `seed_backfill_manifest_count`: `658`
- `seed_backfill_transfer_max_concurrency`: `2`
- `seed_backfill_transfer_max_block_size_mb`: `4`
- `seed_backfill_transfer_max_single_put_size_mb`: `8`
- `seed_backfill_candidate_chunk_count`: `256`
- `seed_backfill_local_source_chunk_count`: `0`
- `seed_backfill_blob_source_chunk_count`: `256`
- `seed_backfill_existing_sidecar_chunk_count`: `0`
- `seed_backfill_missing_source_chunk_count`: `0`
- `seed_backfill_staged_download_count`: `256`
- `seed_backfill_sidecar_write_count`: `512`
- `seed_backfill_consolidated_seed_count`: `4`

## pre-bronze-heritage-chunked-export | success

- Summary: Executed chunked TIP heritage-backfill extraction with Blob-first chunk manifests and local cleanup support.
- Started: 2026-03-23T21:21:38+00:00
- Finished: 2026-03-24T01:23:02+00:00


### Outputs

1. /home/jovyan/patent-iq/etl/manifests/chunks
2. /home/jovyan/patent-iq/etl/manifests/chunks/tip_heritage_chunk_plan.json
3. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/seed_appln_ids.parquet
4. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/seed_family_ids.parquet
5. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/seed_ep_appln_ids.parquet
6. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/seed_family_field_counts.parquet
7. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__1996_1997__publications.json
8. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__audio-visual-technology__1996_1997__publications.parquet
9. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__audio-visual-technology__1996_1997__publications.parquet
10. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__audio-visual-technology__1996_1997__publications.parquet
11. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__1996_1997__citations.json
12. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__1998_1999__publications.json
13. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__audio-visual-technology__1998_1999__publications.parquet
14. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__audio-visual-technology__1998_1999__publications.parquet
15. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__audio-visual-technology__1998_1999__publications.parquet
16. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__1998_1999__citations.json
17. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2000_2001__publications.json
18. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__audio-visual-technology__2000_2001__publications.parquet
19. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__audio-visual-technology__2000_2001__publications.parquet
20. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__audio-visual-technology__2000_2001__publications.parquet
21. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__1996_1997__core.json
22. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__audio-visual-technology__1996_1997__core.parquet
23. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2002_2003__publications.json
24. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__audio-visual-technology__2002_2003__publications.parquet
25. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__audio-visual-technology__2002_2003__publications.parquet
26. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__audio-visual-technology__2002_2003__publications.parquet
27. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2000_2001__citations.json
28. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2004_2005__publications.json
29. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__audio-visual-technology__2004_2005__publications.parquet
30. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__audio-visual-technology__2004_2005__publications.parquet
31. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__audio-visual-technology__2004_2005__publications.parquet
32. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2006_2006__publications.json
33. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__audio-visual-technology__2006_2006__publications.parquet
34. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__audio-visual-technology__2006_2006__publications.parquet
35. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__audio-visual-technology__2006_2006__publications.parquet
36. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__1998_1999__core.json
37. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__audio-visual-technology__1998_1999__core.parquet
38. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2002_2003__citations.json
39. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__1996_1997__publications.json
40. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__telecommunications__1996_1997__publications.parquet
41. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__telecommunications__1996_1997__publications.parquet
42. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__telecommunications__1996_1997__publications.parquet
43. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__1998_1999__publications.json
44. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__telecommunications__1998_1999__publications.parquet
45. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__telecommunications__1998_1999__publications.parquet
46. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__telecommunications__1998_1999__publications.parquet
47. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2000_2001__publications.json
48. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__telecommunications__2000_2001__publications.parquet
49. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__telecommunications__2000_2001__publications.parquet
50. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__telecommunications__2000_2001__publications.parquet
51. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2004_2005__citations.json
52. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2002_2003__publications.json
53. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__telecommunications__2002_2003__publications.parquet
54. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__telecommunications__2002_2003__publications.parquet
55. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__telecommunications__2002_2003__publications.parquet
56. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2000_2001__core.json
57. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__audio-visual-technology__2000_2001__core.parquet
58. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2006_2006__citations.json
59. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2004_2005__publications.json
60. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__telecommunications__2004_2005__publications.parquet
61. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__telecommunications__2004_2005__publications.parquet
62. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__telecommunications__2004_2005__publications.parquet
63. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__1996_1997__citations.json
64. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2006_2006__publications.json
65. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__telecommunications__2006_2006__publications.parquet
66. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__telecommunications__2006_2006__publications.parquet
67. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__telecommunications__2006_2006__publications.parquet
68. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__1996_1997__publications.json
69. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__digital-communication__1996_1997__publications.parquet
70. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__digital-communication__1996_1997__publications.parquet
71. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__digital-communication__1996_1997__publications.parquet
72. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__1998_1999__citations.json
73. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__1998_1999__publications.json
74. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__digital-communication__1998_1999__publications.parquet
75. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__digital-communication__1998_1999__publications.parquet
76. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__digital-communication__1998_1999__publications.parquet
77. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2000_2001__publications.json
78. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__digital-communication__2000_2001__publications.parquet
79. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__digital-communication__2000_2001__publications.parquet
80. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__digital-communication__2000_2001__publications.parquet
81. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2000_2001__citations.json
82. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2002_2003__publications.json
83. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__digital-communication__2002_2003__publications.parquet
84. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__digital-communication__2002_2003__publications.parquet
85. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__digital-communication__2002_2003__publications.parquet
86. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2002_2003__core.json
87. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__audio-visual-technology__2002_2003__core.parquet
88. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2002_2003__citations.json
89. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2004_2005__publications.json
90. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__digital-communication__2004_2005__publications.parquet
91. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__digital-communication__2004_2005__publications.parquet
92. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__digital-communication__2004_2005__publications.parquet
93. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2006_2006__publications.json
94. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__digital-communication__2006_2006__publications.parquet
95. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__digital-communication__2006_2006__publications.parquet
96. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__digital-communication__2006_2006__publications.parquet
97. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__1996_1997__publications.json
98. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__basic-communication-processes__1996_1997__publications.parquet
99. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__basic-communication-processes__1996_1997__publications.parquet
100. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__basic-communication-processes__1996_1997__publications.parquet
101. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__1998_1999__publications.json
102. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__basic-communication-processes__1998_1999__publications.parquet
103. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__basic-communication-processes__1998_1999__publications.parquet
104. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__basic-communication-processes__1998_1999__publications.parquet
105. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2000_2001__publications.json
106. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__basic-communication-processes__2000_2001__publications.parquet
107. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__basic-communication-processes__2000_2001__publications.parquet
108. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__basic-communication-processes__2000_2001__publications.parquet
109. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2004_2005__citations.json
110. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2002_2003__publications.json
111. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__basic-communication-processes__2002_2003__publications.parquet
112. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__basic-communication-processes__2002_2003__publications.parquet
113. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__basic-communication-processes__2002_2003__publications.parquet
114. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2004_2005__publications.json
115. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__basic-communication-processes__2004_2005__publications.parquet
116. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__basic-communication-processes__2004_2005__publications.parquet
117. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__basic-communication-processes__2004_2005__publications.parquet
118. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2006_2006__publications.json
119. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__basic-communication-processes__2006_2006__publications.parquet
120. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__basic-communication-processes__2006_2006__publications.parquet
121. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__basic-communication-processes__2006_2006__publications.parquet
122. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2006_2006__citations.json
123. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2004_2005__core.json
124. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__audio-visual-technology__2004_2005__core.parquet
125. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__1996_1997__publications.json
126. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__computer-technology__1996_1997__publications.parquet
127. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__computer-technology__1996_1997__publications.parquet
128. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__computer-technology__1996_1997__publications.parquet
129. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__1996_1997__citations.json
130. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__1998_1999__publications.json
131. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__computer-technology__1998_1999__publications.parquet
132. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__computer-technology__1998_1999__publications.parquet
133. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__computer-technology__1998_1999__publications.parquet
134. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__1998_1999__citations.json
135. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2000_2001__publications.json
136. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__computer-technology__2000_2001__publications.parquet
137. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__computer-technology__2000_2001__publications.parquet
138. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__computer-technology__2000_2001__publications.parquet
139. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__audio-visual-technology__2006_2006__core.json
140. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__audio-visual-technology__2006_2006__core.parquet
141. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2000_2001__citations.json
142. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2002_2003__publications.json
143. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__computer-technology__2002_2003__publications.parquet
144. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__computer-technology__2002_2003__publications.parquet
145. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__computer-technology__2002_2003__publications.parquet
146. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2002_2003__citations.json
147. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2004_2005__publications.json
148. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__computer-technology__2004_2005__publications.parquet
149. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__computer-technology__2004_2005__publications.parquet
150. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__computer-technology__2004_2005__publications.parquet
151. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__1996_1997__core.json
152. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__telecommunications__1996_1997__core.parquet
153. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2006_2006__publications.json
154. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__computer-technology__2006_2006__publications.parquet
155. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__computer-technology__2006_2006__publications.parquet
156. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__computer-technology__2006_2006__publications.parquet
157. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2004_2005__citations.json
158. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__1996_1997__publications.json
159. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__it-methods-for-management__1996_1997__publications.parquet
160. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__it-methods-for-management__1996_1997__publications.parquet
161. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__it-methods-for-management__1996_1997__publications.parquet
162. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__1998_1999__publications.json
163. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__it-methods-for-management__1998_1999__publications.parquet
164. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__it-methods-for-management__1998_1999__publications.parquet
165. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__it-methods-for-management__1998_1999__publications.parquet
166. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2000_2001__publications.json
167. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__it-methods-for-management__2000_2001__publications.parquet
168. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__it-methods-for-management__2000_2001__publications.parquet
169. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__it-methods-for-management__2000_2001__publications.parquet
170. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2006_2006__citations.json
171. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2002_2003__publications.json
172. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__it-methods-for-management__2002_2003__publications.parquet
173. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__it-methods-for-management__2002_2003__publications.parquet
174. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__it-methods-for-management__2002_2003__publications.parquet
175. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__1996_1997__citations.json
176. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__1998_1999__core.json
177. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__telecommunications__1998_1999__core.parquet
178. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2004_2005__publications.json
179. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__it-methods-for-management__2004_2005__publications.parquet
180. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__it-methods-for-management__2004_2005__publications.parquet
181. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__it-methods-for-management__2004_2005__publications.parquet
182. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__1998_1999__citations.json
183. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2006_2006__publications.json
184. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__it-methods-for-management__2006_2006__publications.parquet
185. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__it-methods-for-management__2006_2006__publications.parquet
186. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__it-methods-for-management__2006_2006__publications.parquet
187. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2000_2001__citations.json
188. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__1996_1997__publications.json
189. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__semiconductors__1996_1997__publications.parquet
190. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__semiconductors__1996_1997__publications.parquet
191. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__semiconductors__1996_1997__publications.parquet
192. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2002_2003__citations.json
193. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__1998_1999__publications.json
194. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__semiconductors__1998_1999__publications.parquet
195. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__semiconductors__1998_1999__publications.parquet
196. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__semiconductors__1998_1999__publications.parquet
197. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2004_2005__citations.json
198. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2000_2001__publications.json
199. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__semiconductors__2000_2001__publications.parquet
200. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__semiconductors__2000_2001__publications.parquet
201. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__semiconductors__2000_2001__publications.parquet
202. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2000_2001__core.json
203. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__telecommunications__2000_2001__core.parquet
204. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2006_2006__citations.json
205. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2002_2003__publications.json
206. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__semiconductors__2002_2003__publications.parquet
207. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__semiconductors__2002_2003__publications.parquet
208. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__semiconductors__2002_2003__publications.parquet
209. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__1996_1997__citations.json
210. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2004_2005__publications.json
211. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__semiconductors__2004_2005__publications.parquet
212. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__semiconductors__2004_2005__publications.parquet
213. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__semiconductors__2004_2005__publications.parquet
214. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2006_2006__publications.json
215. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__semiconductors__2006_2006__publications.parquet
216. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__semiconductors__2006_2006__publications.parquet
217. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__semiconductors__2006_2006__publications.parquet
218. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__1998_1999__citations.json
219. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__1996_1997__publications.json
220. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__measurement__1996_1997__publications.parquet
221. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__measurement__1996_1997__publications.parquet
222. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__measurement__1996_1997__publications.parquet
223. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2002_2003__core.json
224. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__telecommunications__2002_2003__core.parquet
225. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__1998_1999__publications.json
226. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__measurement__1998_1999__publications.parquet
227. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__measurement__1998_1999__publications.parquet
228. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__measurement__1998_1999__publications.parquet
229. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2000_2001__publications.json
230. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__measurement__2000_2001__publications.parquet
231. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__measurement__2000_2001__publications.parquet
232. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__measurement__2000_2001__publications.parquet
233. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2000_2001__citations.json
234. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2002_2003__publications.json
235. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__measurement__2002_2003__publications.parquet
236. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__measurement__2002_2003__publications.parquet
237. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__measurement__2002_2003__publications.parquet
238. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2004_2005__publications.json
239. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__measurement__2004_2005__publications.parquet
240. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__measurement__2004_2005__publications.parquet
241. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__measurement__2004_2005__publications.parquet
242. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2006_2006__publications.json
243. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__measurement__2006_2006__publications.parquet
244. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__measurement__2006_2006__publications.parquet
245. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__measurement__2006_2006__publications.parquet
246. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2004_2005__core.json
247. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__telecommunications__2004_2005__core.parquet
248. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2002_2003__citations.json
249. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__1996_1997__publications.json
250. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__control__1996_1997__publications.parquet
251. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__control__1996_1997__publications.parquet
252. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__control__1996_1997__publications.parquet
253. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__1998_1999__publications.json
254. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__control__1998_1999__publications.parquet
255. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__control__1998_1999__publications.parquet
256. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__control__1998_1999__publications.parquet
257. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2000_2001__publications.json
258. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__control__2000_2001__publications.parquet
259. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__control__2000_2001__publications.parquet
260. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__control__2000_2001__publications.parquet
261. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2002_2003__publications.json
262. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__control__2002_2003__publications.parquet
263. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__control__2002_2003__publications.parquet
264. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__control__2002_2003__publications.parquet
265. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__telecommunications__2006_2006__core.json
266. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__telecommunications__2006_2006__core.parquet
267. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2004_2005__publications.json
268. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__control__2004_2005__publications.parquet
269. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__control__2004_2005__publications.parquet
270. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__control__2004_2005__publications.parquet
271. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2006_2006__publications.json
272. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__control__2006_2006__publications.parquet
273. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__control__2006_2006__publications.parquet
274. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__control__2006_2006__publications.parquet
275. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2004_2005__citations.json
276. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__1996_1997__core.json
277. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__digital-communication__1996_1997__core.parquet
278. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__1996_1997__publications.json
279. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__electrical-machinery-apparatus-energy__1996_1997__publications.parquet
280. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__electrical-machinery-apparatus-energy__1996_1997__publications.parquet
281. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__electrical-machinery-apparatus-energy__1996_1997__publications.parquet
282. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__1998_1999__publications.json
283. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__electrical-machinery-apparatus-energy__1998_1999__publications.parquet
284. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__electrical-machinery-apparatus-energy__1998_1999__publications.parquet
285. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__electrical-machinery-apparatus-energy__1998_1999__publications.parquet
286. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2006_2006__citations.json
287. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__1998_1999__core.json
288. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__digital-communication__1998_1999__core.parquet
289. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2000_2001__publications.json
290. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__electrical-machinery-apparatus-energy__2000_2001__publications.parquet
291. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__electrical-machinery-apparatus-energy__2000_2001__publications.parquet
292. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__electrical-machinery-apparatus-energy__2000_2001__publications.parquet
293. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__1996_1997__citations.json
294. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__1998_1999__citations.json
295. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2002_2003__publications.json
296. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__electrical-machinery-apparatus-energy__2002_2003__publications.parquet
297. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__electrical-machinery-apparatus-energy__2002_2003__publications.parquet
298. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__electrical-machinery-apparatus-energy__2002_2003__publications.parquet
299. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2000_2001__citations.json
300. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2004_2005__publications.json
301. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__electrical-machinery-apparatus-energy__2004_2005__publications.parquet
302. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__electrical-machinery-apparatus-energy__2004_2005__publications.parquet
303. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__electrical-machinery-apparatus-energy__2004_2005__publications.parquet
304. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2002_2003__citations.json
305. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2000_2001__core.json
306. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__digital-communication__2000_2001__core.parquet
307. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2006_2006__publications.json
308. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_publn_ids/heritage__electrical-machinery-apparatus-energy__2006_2006__publications.parquet
309. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_ep_publication_numbers/heritage__electrical-machinery-apparatus-energy__2006_2006__publications.parquet
310. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_us_publication_numbers/heritage__electrical-machinery-apparatus-energy__2006_2006__publications.parquet
311. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2004_2005__citations.json
312. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2006_2006__citations.json
313. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__1996_1997__citations.json
314. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__1998_1999__citations.json
315. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2002_2003__core.json
316. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__digital-communication__2002_2003__core.parquet
317. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2000_2001__citations.json
318. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2002_2003__citations.json
319. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2004_2005__core.json
320. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__digital-communication__2004_2005__core.parquet
321. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2004_2005__citations.json
322. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__digital-communication__2006_2006__core.json
323. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__digital-communication__2006_2006__core.parquet
324. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2006_2006__citations.json
325. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__1996_1997__citations.json
326. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__1996_1997__core.json
327. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__basic-communication-processes__1996_1997__core.parquet
328. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__1998_1999__citations.json
329. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__1998_1999__core.json
330. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__basic-communication-processes__1998_1999__core.parquet
331. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2000_2001__citations.json
332. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2002_2003__citations.json
333. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2000_2001__core.json
334. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__basic-communication-processes__2000_2001__core.parquet
335. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2004_2005__citations.json
336. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2002_2003__core.json
337. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__basic-communication-processes__2002_2003__core.parquet
338. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2006_2006__citations.json
339. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__1996_1997__citations.json
340. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2004_2005__core.json
341. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__basic-communication-processes__2004_2005__core.parquet
342. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__1998_1999__citations.json
343. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2000_2001__citations.json
344. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__basic-communication-processes__2006_2006__core.json
345. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__basic-communication-processes__2006_2006__core.parquet
346. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2002_2003__citations.json
347. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2004_2005__citations.json
348. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__1996_1997__core.json
349. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__computer-technology__1996_1997__core.parquet
350. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2006_2006__citations.json
351. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__1996_1997__citations.json
352. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__1998_1999__citations.json
353. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__1998_1999__core.json
354. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__computer-technology__1998_1999__core.parquet
355. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2000_2001__citations.json
356. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2002_2003__citations.json
357. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2000_2001__core.json
358. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__computer-technology__2000_2001__core.parquet
359. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2004_2005__citations.json
360. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2006_2006__citations.json
361. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2002_2003__core.json
362. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__computer-technology__2002_2003__core.parquet
363. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2004_2005__core.json
364. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__computer-technology__2004_2005__core.parquet
365. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__computer-technology__2006_2006__core.json
366. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__computer-technology__2006_2006__core.parquet
367. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__1996_1997__core.json
368. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__it-methods-for-management__1996_1997__core.parquet
369. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__1998_1999__core.json
370. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__it-methods-for-management__1998_1999__core.parquet
371. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2000_2001__core.json
372. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__it-methods-for-management__2000_2001__core.parquet
373. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2002_2003__core.json
374. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__it-methods-for-management__2002_2003__core.parquet
375. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2004_2005__core.json
376. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__it-methods-for-management__2004_2005__core.parquet
377. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__it-methods-for-management__2006_2006__core.json
378. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__it-methods-for-management__2006_2006__core.parquet
379. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__1996_1997__core.json
380. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__semiconductors__1996_1997__core.parquet
381. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__1998_1999__core.json
382. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__semiconductors__1998_1999__core.parquet
383. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2000_2001__core.json
384. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__semiconductors__2000_2001__core.parquet
385. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2002_2003__core.json
386. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__semiconductors__2002_2003__core.parquet
387. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2004_2005__core.json
388. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__semiconductors__2004_2005__core.parquet
389. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__semiconductors__2006_2006__core.json
390. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__semiconductors__2006_2006__core.parquet
391. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__1996_1997__core.json
392. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__measurement__1996_1997__core.parquet
393. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__1998_1999__core.json
394. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__measurement__1998_1999__core.parquet
395. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2000_2001__core.json
396. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__measurement__2000_2001__core.parquet
397. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2002_2003__core.json
398. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__measurement__2002_2003__core.parquet
399. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2004_2005__core.json
400. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__measurement__2004_2005__core.parquet
401. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__measurement__2006_2006__core.json
402. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__measurement__2006_2006__core.parquet
403. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__1996_1997__core.json
404. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__control__1996_1997__core.parquet
405. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__1998_1999__core.json
406. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__control__1998_1999__core.parquet
407. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2000_2001__core.json
408. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__control__2000_2001__core.parquet
409. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2002_2003__core.json
410. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__control__2002_2003__core.parquet
411. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2004_2005__core.json
412. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__control__2004_2005__core.parquet
413. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__control__2006_2006__core.json
414. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__control__2006_2006__core.parquet
415. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__1996_1997__core.json
416. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__electrical-machinery-apparatus-energy__1996_1997__core.parquet
417. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__1998_1999__core.json
418. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__electrical-machinery-apparatus-energy__1998_1999__core.parquet
419. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2000_2001__core.json
420. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__electrical-machinery-apparatus-energy__2000_2001__core.parquet
421. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2002_2003__core.json
422. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__electrical-machinery-apparatus-energy__2002_2003__core.parquet
423. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2004_2005__core.json
424. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__electrical-machinery-apparatus-energy__2004_2005__core.parquet
425. /home/jovyan/patent-iq/etl/manifests/chunks/heritage__electrical-machinery-apparatus-energy__2006_2006__core.json
426. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/_chunk_derived/seed_person_ids/heritage__electrical-machinery-apparatus-energy__2006_2006__core.parquet
427. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/seed_publn_ids.parquet
428. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/seed_ep_publication_numbers.parquet
429. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/seed_person_ids.parquet
430. /home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds/seed_us_publication_numbers.parquet

### Artifacts

- `live_event_log`: `/home/jovyan/patent-iq/etl/manifests/stages/pre-bronze-heritage-chunked-export.events.jsonl`
- `stats_snapshot`: `/home/jovyan/patent-iq/etl/manifests/stats/pre-bronze-heritage-chunked-export.json`

### Methods

1. Planned field/year/table-family chunks before extraction.
2. Built chunk-local bounded scope directly from TIP instead of materializing one monolithic bounded raw layer.
3. Uploaded chunk artifacts to Azure Blob when configured, then optionally cleaned local chunk temp directories.

### Calculations

1. Chunk ids are deterministic field/year/table-family keys.
2. Per-chunk scope is bounded by both selected WIPO field and configured year bucket.

### Downstream Impacts

1. Successful chunk manifests allow resumable pre-Bronze extraction across constrained TIP sessions.
2. Chunk-local Blob prefixes become the authoritative bounded raw intermediate store for later non-TIP Bronze/Silver/Gold consolidation.

### Governing Docs

1. docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md
2. docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md
4. docs/data/epo-tip-client-usage.md

### Warnings

1. Skipped `bronze_ref_techn_field_ipc` because no source file was found.
2. Skipped `bronze_ext_cpc_coverage` because no source file was found.
3. Skipped `bronze_ext_cpc_ipc_weights` because no source file was found.
4. Skipped `bronze_ext_iso_country_map` because no source file was found.
5. Skipped `bronze_ext_world_bank_gdp_ppp` because no source file was found.
6. Skipped `bronze_ext_us_chamber_ip_index` because no source file was found.
7. Skipped `bronze_ext_up_member_states` because no source file was found.
8. Skipped `bronze_ext_kind_code_normalization_seed` because no source file was found.
9. Skipped `bronze_ext_oecd_indicator_seed` because no source file was found.

### Metrics

- `chunk_scheduler_parallel_limit`: `3`
- `chunk_upload_max_concurrency`: `2`
- `chunk_upload_max_block_size_mb`: `4`
- `chunk_upload_max_single_put_size_mb`: `8`
- `global_seed_initial_file_count`: `4`
- `global_seed_dir`: `/home/jovyan/patent-iq/etl/data/raw-bounded-heritage/_seeds`
- `refs_uploaded_blob_count`: `0`
- `global_seed_file_count`: `8`
- `global_seed_derived_file_count`: `4`
- `chunk_total_count`: `180`
- `chunk_skipped_count`: `0`
- `chunk_failed_count`: `0`
- `chunk_degraded_count`: `0`
- `chunk_uploaded_file_count`: `840`


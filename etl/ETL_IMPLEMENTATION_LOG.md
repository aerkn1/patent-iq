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

## consolidate-before-bronze | success

- Summary: Downloaded Blob-backed bounded raw chunks into local staging, consolidated them into canonical bounded parquet files, and kept heritage seeds isolated from the active main seed root.
- Started: 2026-03-31T16:12:11+00:00
- Finished: 2026-03-31T16:22:30+00:00

### Inputs

1. azure-blob://patentiq-data/raw-bounded/patstat
2. azure-blob://patentiq-data/raw-bounded/register
3. azure-blob://patentiq-data/raw-bounded/epab
4. azure-blob://patentiq-data/raw-bounded/refs
5. azure-blob://patentiq-data/raw-bounded-heritage/patstat
6. azure-blob://patentiq-data/raw-bounded-heritage/seeds

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls201_appln.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls202_appln_title.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls203_appln_abstr.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls204_appln_prior.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls206_person.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls207_pers_appln.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls209_appln_ipc.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls212_citation.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls214_npl_publn.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls216_appln_contn.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls224_appln_cpc.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls230_appln_techn_field.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls228_docdb_fam_citn.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls231_inpadoc_legal_event.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls803_legal_event_code.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg101_appln.parquet
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg107_parties.parquet
19. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg111_licensee.parquet
20. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg125_appeal.parquet
21. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg130_opponent.parquet
22. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg201_proc_step.parquet
23. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg202_proc_step_text.parquet
24. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg203_proc_step_date.parquet
25. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg301_event_data.parquet
26. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg402_event_text.parquet
27. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg701_appln.parquet
28. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg731_event_data.parquet
29. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg742_event_text.parquet
30. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_publication.parquet
31. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_abstract.parquet
32. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_claims.parquet
33. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat
34. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register
35. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab
36. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs

### Artifacts

- `staging_root`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/imports`
- `heritage_seed_staging_dir`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/imports/raw-bounded-heritage/_seeds`
- `main_patstat_staging_dir`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/imports/raw-bounded/patstat`
- `heritage_patstat_staging_dir`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/imports/raw-bounded-heritage/patstat`
- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/consolidate-before-bronze.json`

### Methods

1. Downloaded the Blob-backed bounded raw prefixes needed for local Bronze/Silver/Gold preparation into a separate staging tree.
2. Merged partitioned field/year chunk parquet into one canonical local bounded parquet per logical table using DuckDB `select distinct *` deduplication.
3. Folded heritage PATSTAT parquet into the same canonical PATSTAT outputs while keeping heritage seeds in staging only.

### Calculations

1. Main PATSTAT, Register, EPAB, and refs are sourced from `raw-bounded/*` Blob prefixes.
2. Heritage PATSTAT and heritage seeds are sourced from `raw-bounded-heritage/*` Blob prefixes.
3. Canonical Bronze inputs remain the existing local bounded directories that downstream stages already read.

### Downstream Impacts

1. The local bounded raw layer becomes compatible with the non-recursive Bronze ingestors that expect one top-level parquet per logical source table.
2. Heritage history is incorporated into downstream Bronze/Silver/Gold by merging heritage PATSTAT into canonical PATSTAT outputs before Bronze runs.

### Governing Docs

1. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md
2. docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md
3. docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md

### Warnings

1. Skipped `bronze_reg403_appln_status` because no staged parquet was found for stems ['reg403_appln_status'].
2. Skipped `bronze_reg741_appln_status` because no staged parquet was found for stems ['reg741_appln_status'].
3. Skipped `bronze_ref_techn_field_ipc` because no staged parquet was found for stems ['wipo_techn_field_ipc', 'ipc_to_wipo_industry'].
4. Skipped `bronze_ext_cpc_coverage` because no staged parquet was found for stems ['cpc_coverage'].
5. Skipped `bronze_ext_cpc_ipc_weights` because no staged parquet was found for stems ['cpc_ipc_weights_2014_2025'].
6. Skipped `bronze_ext_iso_country_map` because no staged parquet was found for stems ['iso_country_map', 'country_iso_map'].
7. Skipped `bronze_ext_world_bank_gdp_ppp` because no staged parquet was found for stems ['world_bank_gdp_ppp', 'wb_gdp_ppp'].
8. Skipped `bronze_ext_us_chamber_ip_index` because no staged parquet was found for stems ['us_chamber_ip_index', 'ip_index'].
9. Skipped `bronze_ext_up_member_states` because no staged parquet was found for stems ['up_member_states', 'unitary_patent_member_states'].
10. Skipped `bronze_ext_kind_code_normalization_seed` because no staged parquet was found for stems ['kind_code_normalization', 'kind_code_normalization_seed'].
11. Skipped `bronze_ext_oecd_indicator_seed` because no staged parquet was found for stems ['oecd_indicator_seed', 'oecd_quality_indicator_seed'].

### Metrics

- `raw-bounded_patstat_blob_count`: `2043`
- `raw-bounded_patstat_reused_count`: `2043`
- `raw-bounded_register_blob_count`: `1651`
- `raw-bounded_register_reused_count`: `1651`
- `raw-bounded_epab_blob_count`: `474`
- `raw-bounded_epab_reused_count`: `474`
- `raw-bounded_refs_blob_count`: `0`
- `raw-bounded_refs_reused_count`: `0`
- `raw-bounded-heritage_patstat_blob_count`: `840`
- `raw-bounded-heritage_patstat_reused_count`: `840`
- `raw-bounded-heritage_seeds_blob_count`: `8`
- `raw-bounded-heritage_seeds_reused_count`: `8`
- `staged_blob_file_count`: `5016`
- `staged_blob_total_bytes`: `43796095433`
- `tls201_appln_source_file_count`: `188`
- `tls201_appln_bounded_count`: `36231729`
- `tls202_appln_title_source_file_count`: `188`
- `tls202_appln_title_bounded_count`: `34149771`
- `tls203_appln_abstr_source_file_count`: `188`
- `tls203_appln_abstr_bounded_count`: `32628318`
- `tls204_appln_prior_source_file_count`: `188`
- `tls204_appln_prior_bounded_count`: `12240913`
- `tls206_person_source_file_count`: `188`
- `tls206_person_bounded_count`: `25484970`
- `tls207_pers_appln_source_file_count`: `188`
- `tls207_pers_appln_bounded_count`: `132921009`
- `tls209_appln_ipc_source_file_count`: `188`
- `tls209_appln_ipc_bounded_count`: `40798728`
- `tls211_pat_publn_source_file_count`: `188`
- `tls211_pat_publn_bounded_count`: `47798843`
- `tls212_citation_source_file_count`: `187`
- `tls212_citation_bounded_count`: `27652952`
- `tls214_npl_publn_source_file_count`: `187`
- `tls214_npl_publn_bounded_count`: `5281343`
- `tls216_appln_contn_source_file_count`: `188`
- `tls216_appln_contn_bounded_count`: `1839143`
- `tls224_appln_cpc_source_file_count`: `188`
- `tls224_appln_cpc_bounded_count`: `31300011`
- `tls230_appln_techn_field_source_file_count`: `188`
- `tls230_appln_techn_field_bounded_count`: `37135004`
- `tls228_docdb_fam_citn_source_file_count`: `187`
- `tls228_docdb_fam_citn_bounded_count`: `18526500`
- `tls231_inpadoc_legal_event_source_file_count`: `127`
- `tls231_inpadoc_legal_event_bounded_count`: `138761674`
- `tls803_legal_event_code_source_file_count`: `127`
- `tls803_legal_event_code_bounded_count`: `62`
- `patstat_target_cleanup_count`: `16`
- `reg101_appln_source_file_count`: `127`
- `reg101_appln_bounded_count`: `1138403`
- `reg107_parties_source_file_count`: `127`
- `reg107_parties_bounded_count`: `7541254`
- `reg111_licensee_source_file_count`: `127`
- `reg111_licensee_bounded_count`: `4216`
- `reg125_appeal_source_file_count`: `127`
- `reg125_appeal_bounded_count`: `9921`
- `reg130_opponent_source_file_count`: `127`
- `reg130_opponent_bounded_count`: `16398`
- `reg201_proc_step_source_file_count`: `127`
- `reg201_proc_step_bounded_count`: `1195313`
- `reg202_proc_step_text_source_file_count`: `127`
- `reg202_proc_step_text_bounded_count`: `1442273`
- `reg203_proc_step_date_source_file_count`: `127`
- `reg203_proc_step_date_bounded_count`: `1446346`
- `reg301_event_data_source_file_count`: `127`
- `reg301_event_data_bounded_count`: `1675053`
- `reg402_event_text_source_file_count`: `127`
- `reg402_event_text_bounded_count`: `355`
- `reg701_appln_source_file_count`: `127`
- `reg701_appln_bounded_count`: `22860`
- `reg731_event_data_source_file_count`: `127`
- `reg731_event_data_bounded_count`: `22686`
- `reg742_event_text_source_file_count`: `127`
- `reg742_event_text_bounded_count`: `20`
- `register_target_cleanup_count`: `13`
- `refs_target_cleanup_count`: `0`
- `epab_target_cleanup_count`: `2`
- `epab_publication_source_file_count`: `101`
- `epab_publication_bounded_count`: `2696348`
- `epab_abstract_source_file_count`: `101`
- `epab_abstract_bounded_count`: `2097316`
- `epab_claims_source_file_count`: `101`
- `epab_claims_bounded_count`: `2696361`
- `patstat_consolidated_table_count`: `16`
- `register_consolidated_table_count`: `13`
- `refs_consolidated_table_count`: `0`
- `epab_consolidated_table_count`: `3`
- `consolidated_total_row_count`: `644756093`
- `heritage_seed_staging_count`: `8`
- `main_seed_dir_untouched`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/_seeds`

## repair-epab-for-semantic | success

- Summary: Repaired the staged EPAB chunk parquet into a deterministic semantic-support subset without rerunning raw EPAB extraction.
- Started: 2026-03-31T19:18:42+00:00
- Finished: 2026-03-31T19:35:15+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/temp/epab-semantic-repair/publication_chunk_001.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/temp/epab-semantic-repair/claims_chunk_001.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_publication.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_claims.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_abstract.parquet

### Artifacts

- `staged_epab_root`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/imports/raw-bounded/epab`
- `repair_temp_root`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/temp/epab-semantic-repair`
- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/repair-epab-for-semantic.json`

### Methods

1. Used only EPAB chunk folders whose publication and claims row counts aligned exactly, which allows deterministic row-order pairing.
2. Derived `publication_number_full` and synthetic `epab_doc_id` keys from EP publication rows, then retained only claim-1 payloads for semantic representative-text use.
3. Dropped unreliable EPAB abstract payloads and kept PATSTAT abstracts as the universal semantic fallback.

### Calculations

1. Safe EPAB repairability is measured from publication/claims row-count alignment per chunk.
2. Final EPAB publication rows are deduplicated by `publication_number_full`; final EPAB claims are deduplicated by a stable hash over publication, language, sequence, and text.
3. This stage intentionally produces a semantic-oriented EPAB subset, not a full historical EPAB restoration.

### Downstream Impacts

1. Bronze can continue using the existing TIP EPAB copy path because the repaired bounded EPAB files are already in Bronze-compatible shape.
2. Silver semantic representative-text generation can recover EPAB claim-1 coverage where repair is deterministic and fall back to PATSTAT abstracts elsewhere.

### Governing Docs

1. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. Skipped 4 EPAB chunk roots whose publication/claims row counts did not align.
2. EPAB abstracts were intentionally neutralized; PATSTAT abstracts remain the semantic fallback.

### Metrics

- `epab_chunk_count`: `101`
- `epab_safe_chunk_count`: `97`
- `epab_unsafe_chunk_count`: `4`
- `epab_repaired_publication_row_count_pre_dedupe`: `2149576`
- `epab_repaired_claim1_row_count_pre_dedupe`: `3429520`
- `epab_repaired_claim_dedupe_key_count`: `2763676`
- `epab_repaired_claim1_row_count`: `2763676`
- `epab_repaired_publication_row_count`: `1679816`
- `epab_repaired_abstract_row_count`: `0`

## normalize-kind-code | success

- Summary: Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.
- Started: 2026-03-31T20:03:47+00:00
- Finished: 2026-03-31T20:03:47+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_observed_pairs.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_review_queue.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/normalize-kind-code.json`

### Methods

1. Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.
2. Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.
3. Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.

### Calculations

1. Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.
2. EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.

### Downstream Impacts

1. This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.
2. Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue.

### Metrics

- `observed_pair_count`: `641`
- `seed_input_pair_count`: `9834`
- `auto_generated_pair_count`: `263`
- `review_queue_pair_count`: `263`
- `final_pair_count`: `10097`

## normalize-kind-code | success

- Summary: Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.
- Started: 2026-03-31T20:20:49+00:00
- Finished: 2026-03-31T20:20:50+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_manual_overrides.csv

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_observed_pairs.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_review_queue.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/normalize-kind-code.json`

### Methods

1. Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.
2. Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.
3. Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.

### Calculations

1. Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.
2. EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.

### Downstream Impacts

1. This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.
2. Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue.

### Metrics

- `observed_pair_count`: `641`
- `seed_input_pair_count`: `10097`
- `auto_generated_pair_count`: `0`
- `review_queue_pair_count`: `251`
- `final_pair_count`: `10097`

## normalize-kind-code | success

- Summary: Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.
- Started: 2026-03-31T20:25:38+00:00
- Finished: 2026-03-31T20:25:39+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_manual_overrides.csv

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_observed_pairs.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_review_queue.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/normalize-kind-code.json`

### Methods

1. Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.
2. Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.
3. Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.

### Calculations

1. Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.
2. EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.

### Downstream Impacts

1. This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.
2. Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue.

### Metrics

- `observed_pair_count`: `641`
- `seed_input_pair_count`: `10097`
- `auto_generated_pair_count`: `0`
- `review_queue_pair_count`: `247`
- `final_pair_count`: `10097`

## source-certification | failed

- Summary: Certified raw source availability, bridge viability, and mega-cluster sufficiency preconditions.
- Started: 2026-03-31T20:29:20+00:00
- Finished: 2026-03-31T20:29:20+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/wipo_techn_field_ipc.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/iso_country_map.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/world_bank_gdp_ppp.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/us_chamber_ip_index.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/up_member_states.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/data-analytics/cpc-coverage-data/ipc_to_wipo_industry.csv


### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/source-certification.json`

### Methods

1. Scanned local raw-source directories or TIP clients depending on the configured source mode.
2. Applied release severity classification using configured thresholds and source-family-specific rules.
3. Recorded source availability and missing-resource warnings before Bronze generation.
4. Validated required raw-source columns against the schema contracts captured in docs/data and V2 warehouse docs.

### Calculations

1. Source sufficiency is evaluated as presence plus bridge-readiness of family/application/publication identifiers.
2. Selected field sufficiency requires every configured WIPO field to remain representable downstream.

### Downstream Impacts

1. Failure here blocks Bronze ingestion and prevents the bounded mega-cluster seed from being generated safely.
2. Missing PATSTAT or weak field coverage will invalidate all downstream family, portfolio, Market Intelligence, and semantic marts.
3. Missing USPTO or EPAB will specifically degrade semantic claim-space selection while leaving abstract fallback available.

### Governing Docs

1. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md

### Warnings

1. TIP PATSTAT client could not be initialized: No module named 'epo'
2. Missing source for `bronze_ext_cpc_coverage` in `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs`.
3. Missing source for `bronze_ext_cpc_ipc_weights` in `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs`.
4. Missing source for `bronze_ext_oecd_indicator_seed` in `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs`.
5. TIP EPAB client could not be initialized: No module named 'epo'
6. USPTO is configured for external ODP extraction. API key env var `USPTO_ODP_API_KEY` is not present in this runtime, so the dedicated USPTO ODP stage is deferred.

### Metrics

- `bronze_ref_techn_field_ipc_file_count`: `1`
- `bronze_ref_techn_field_ipc_column_count`: `6`
- `bronze_ext_iso_country_map_file_count`: `1`
- `bronze_ext_iso_country_map_column_count`: `3`
- `bronze_ext_world_bank_gdp_ppp_file_count`: `1`
- `bronze_ext_world_bank_gdp_ppp_column_count`: `3`
- `bronze_ext_us_chamber_ip_index_file_count`: `1`
- `bronze_ext_us_chamber_ip_index_column_count`: `3`
- `bronze_ext_up_member_states_file_count`: `1`
- `bronze_ext_up_member_states_column_count`: `3`
- `bronze_ext_kind_code_normalization_seed_file_count`: `1`
- `bronze_ext_kind_code_normalization_seed_column_count`: `12`
- `total_input_file_count`: `6`
- `uspto_xml_file_count`: `0`
- `epab_payload_file_count`: `0`
- `uspto_odp_api_key_available`: `0`
- `uspto_externalized_from_tip`: `1`
- `uspto_runtime_stage_required`: `1`
- `selected_wipo_field_count`: `10`

## bronze | success

- Summary: Generated typed and source-aware Bronze parquet for PATSTAT, Register, and reference inputs.
- Started: 2026-03-31T21:20:29+00:00
- Finished: 2026-03-31T21:21:55+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls201_appln.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls202_appln_title.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls203_appln_abstr.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls204_appln_prior.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls206_person.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls207_pers_appln.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls209_appln_ipc.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls212_citation.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls214_npl_publn.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls216_appln_contn.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls224_appln_cpc.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls230_appln_techn_field.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls228_docdb_fam_citn.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls231_inpadoc_legal_event.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls803_legal_event_code.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg101_appln.parquet
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg403_appln_status.parquet
19. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg107_parties.parquet
20. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg111_licensee.parquet
21. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg125_appeal.parquet
22. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg130_opponent.parquet
23. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg201_proc_step.parquet
24. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg202_proc_step_text.parquet
25. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg203_proc_step_date.parquet
26. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg301_event_data.parquet
27. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg402_event_text.parquet
28. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg701_appln.parquet
29. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg731_event_data.parquet
30. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg741_appln_status.parquet
31. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg742_event_text.parquet
32. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/wipo_techn_field_ipc.parquet
33. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/iso_country_map.parquet
34. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/world_bank_gdp_ppp.parquet
35. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/us_chamber_ip_index.parquet
36. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/up_member_states.parquet
37. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/kind_code_normalization.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_title.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_abstr.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_prior.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_person.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pers_appln.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_ipc.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_npl_publn.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_contn.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_cpc.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_techn_field.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_docdb_fam_citn.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_inpadoc_legal_event.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ref_legal_event_code.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg101_appln.parquet
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg403_appln_status.parquet
19. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg107_parties.parquet
20. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg111_licensee.parquet
21. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg125_appeal.parquet
22. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg130_opponent.parquet
23. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg201_proc_step.parquet
24. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg202_proc_step_text.parquet
25. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg203_proc_step_date.parquet
26. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg301_event_data.parquet
27. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg402_event_text.parquet
28. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg701_appln.parquet
29. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg731_event_data.parquet
30. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg741_appln_status.parquet
31. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg742_event_text.parquet
32. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ref_techn_field_ipc.parquet
33. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_iso_country_map.parquet
34. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_world_bank_gdp_ppp.parquet
35. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_us_chamber_ip_index.parquet
36. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_up_member_states.parquet
37. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_kind_code_normalization_seed.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/bronze.json`

### Methods

1. Applied table-specific typing for PATSTAT and Register key/date columns while preserving source columns.
2. Normalized reference inputs to the canonical Bronze schemas required by Silver legal, market, and scope logic.

### Calculations

1. Bronze row counts reflect the landed bounded raw slice, not downstream family-first aggregates.

### Downstream Impacts

1. These Bronze parquet tables feed scope seeding, legal ledger reconstruction, market weighting, EP Register overlays, citation metrics, and OECD support layers.
2. Typing errors or missing normalized reference columns here will propagate directly into Silver joins and point-in-time analytics.

### Governing Docs

1. docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md
2. docs/data/patstat-schema.md
3. docs/data/patstat-register-schema.md

### Warnings

1. Skipped `bronze_ext_cpc_coverage` because no matching raw file was found.
2. Skipped `bronze_ext_cpc_ipc_weights` because no matching raw file was found.
3. Skipped `bronze_ext_oecd_indicator_seed` because no matching raw file was found.

### Metrics

- `bronze_patstat_appln_rows`: `36231729`
- `bronze_patstat_appln_title_rows`: `34149771`
- `bronze_patstat_appln_abstr_rows`: `32628318`
- `bronze_patstat_appln_prior_rows`: `12240913`
- `bronze_patstat_person_rows`: `25484970`
- `bronze_patstat_pers_appln_rows`: `132921009`
- `bronze_patstat_appln_ipc_rows`: `40798728`
- `bronze_patstat_pat_publn_rows`: `47798843`
- `bronze_patstat_citation_rows`: `27652952`
- `bronze_patstat_npl_publn_rows`: `5281343`
- `bronze_patstat_appln_contn_rows`: `1839143`
- `bronze_patstat_appln_cpc_rows`: `31300011`
- `bronze_patstat_appln_techn_field_rows`: `37135004`
- `bronze_patstat_docdb_fam_citn_rows`: `18526500`
- `bronze_patstat_inpadoc_legal_event_rows`: `138761674`
- `bronze_ref_legal_event_code_rows`: `62`
- `bronze_reg101_appln_rows`: `1138403`
- `bronze_reg403_appln_status_rows`: `17`
- `bronze_reg107_parties_rows`: `7541254`
- `bronze_reg111_licensee_rows`: `4216`
- `bronze_reg125_appeal_rows`: `9921`
- `bronze_reg130_opponent_rows`: `16398`
- `bronze_reg201_proc_step_rows`: `1195313`
- `bronze_reg202_proc_step_text_rows`: `1442273`
- `bronze_reg203_proc_step_date_rows`: `1446346`
- `bronze_reg301_event_data_rows`: `1675053`
- `bronze_reg402_event_text_rows`: `355`
- `bronze_reg701_appln_rows`: `22860`
- `bronze_reg731_event_data_rows`: `22686`
- `bronze_reg741_appln_status_rows`: `7`
- `bronze_reg742_event_text_rows`: `20`
- `bronze_ref_techn_field_ipc_rows`: `771`
- `bronze_ext_iso_country_map_rows`: `296`
- `bronze_ext_world_bank_gdp_ppp_rows`: `8336`
- `bronze_ext_us_chamber_ip_index_rows`: `55`
- `bronze_ext_up_member_states_rows`: `18`
- `bronze_ext_kind_code_normalization_seed_rows`: `10097`
- `bronze_total_row_count`: `637285665`

## bronze-uspto-fulltext | success

- Summary: USPTO Bronze parsing was deferred because USPTO is configured for the external ODP stream path and no direct Bronze outputs are present in this runtime.
- Started: 2026-03-31T21:21:41+00:00
- Finished: 2026-03-31T21:21:55+00:00



### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/bronze-uspto-fulltext.json`

### Methods

1. Parsed USPTO XML application/publication identifiers, abstracts, and claims.
2. Preserved publication kind and claim ordering fields required for semantic hierarchy selection.
3. Skipped bounded-XML parsing because USPTO is handled by the separate `prebronze-uspto-odp` stage when that external path is executed.

### Calculations

1. No family collapse or semantic prioritization occurs in Bronze. This stage only lands text-provider tables.

### Downstream Impacts

1. These tables feed representative claim and abstract selection in the semantic Silver stage only.
2. They must not be used to override PATSTAT or Register harmonized metadata layers downstream.

### Governing Docs

1. docs/data/uspto-full-text-schema.md
2. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `uspto_odp_outputs_present`: `0`

## bronze-epab-fulltext | success

- Summary: Parsed EPAB payloads into Bronze text-provider tables for semantic workflows.
- Started: 2026-03-31T21:21:41+00:00
- Finished: 2026-03-31T21:21:57+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_publication.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_publication.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_abstract.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_claims.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_document.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_publication.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_abstract.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_claims.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/bronze-epab-fulltext.json`

### Methods

1. Parsed EPAB publication/application anchors, abstracts, and claims from JSON payloads.
2. Preserved language and sequence fields for English-claim selection and abstract fallback.

### Calculations

1. Bronze EPAB is source-faithful and does not replace PATSTAT/Register metadata for analytical truth.

### Downstream Impacts

1. These Bronze tables feed EP grant claim selection, abstract fallback, and Data Room transparency outputs.
2. They must remain text-provider tables and not become the canonical source for classifications or parties in downstream analytics.

### Governing Docs

1. docs/data/ep-full-text-publication-database-schema.md
2. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `bronze_epab_document_rows`: `1679816`
- `bronze_epab_publication_rows`: `1679816`
- `bronze_epab_abstract_rows`: `0`
- `bronze_epab_claims_rows`: `2763676`

## scope | failed

- Summary: Built bounded-scope application, family, publication, and owner seeds for the mega-cluster universe.
- Started: 2026-03-31T21:44:03+00:00
- Finished: 2026-03-31T21:44:04+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_ipc.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_techn_field.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pers_appln.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_person.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ref_techn_field_ipc.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/scope.json`

### Methods

1. Resolved the in-scope family universe from selected WIPO field mappings before heavy downstream analytics.
2. Preferred direct PATSTAT technology-field inputs when present and fell back to IPC subclass to WIPO field concordance otherwise.
3. Bridged the in-scope applications to families, publications, and owners to create the canonical bounded universe.

### Calculations

1. An in-scope application is one whose technology-field mapping falls inside the selected 10 WIPO fields.
2. An in-scope family is any DOCDB family reachable from the in-scope application seed.
3. An in-scope portfolio owner seed is derived from applicant-side application-person links only.

### Downstream Impacts

1. These scope seeds bound every downstream family, publication, owner, and portfolio calculation in the MVP warehouse.
2. An over-broad or under-broad seed will contaminate blocking power, Market Intelligence, forecasts, semantic sampling, and Data Room counts.

### Governing Docs

1. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md
2. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md
3. docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md

### Warnings

1. Scope seeding produced zero in-scope families.

### Metrics

- `scope_appln_count`: `0`
- `scope_family_count`: `0`
- `scope_publn_count`: `0`
- `scope_owner_count`: `0`

## scope | success

- Summary: Built bounded-scope application, family, publication, and owner seeds for the mega-cluster universe.
- Started: 2026-03-31T21:45:29+00:00
- Finished: 2026-03-31T21:46:31+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_ipc.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_techn_field.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pers_appln.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_person.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ref_techn_field_ipc.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/scope.json`

### Methods

1. Resolved the in-scope family universe from selected WIPO field mappings before heavy downstream analytics.
2. Preferred direct PATSTAT technology-field inputs when present and fell back to IPC subclass to WIPO field concordance otherwise.
3. Bridged the in-scope applications to families, publications, and owners to create the canonical bounded universe.

### Calculations

1. An in-scope application is one whose technology-field mapping falls inside the selected 10 WIPO fields.
2. An in-scope family is any DOCDB family reachable from the in-scope application seed.
3. An in-scope portfolio owner seed is derived from applicant-side application-person links only.

### Downstream Impacts

1. These scope seeds bound every downstream family, publication, owner, and portfolio calculation in the MVP warehouse.
2. An over-broad or under-broad seed will contaminate blocking power, Market Intelligence, forecasts, semantic sampling, and Data Room counts.

### Governing Docs

1. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md
2. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md
3. docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md


### Metrics

- `scope_appln_count`: `32871909`
- `scope_family_count`: `21353101`
- `scope_publn_count`: `45738731`
- `scope_owner_count`: `37134586`
- `scope_appln_count__Control`: `2011050`
- `scope_family_count__Control`: `1644622`
- `scope_publn_count__Control`: `2673570`
- `scope_appln_count__Audio-visual technology`: `3449359`
- `scope_family_count__Audio-visual technology`: `2446006`
- `scope_publn_count__Audio-visual technology`: `4757897`
- `scope_appln_count__IT methods for management`: `1343950`
- `scope_family_count__IT methods for management`: `1039957`
- `scope_publn_count__IT methods for management`: `1770411`
- `scope_appln_count__Basic communication processes`: `602460`
- `scope_family_count__Basic communication processes`: `384536`
- `scope_publn_count__Basic communication processes`: `909364`
- `scope_appln_count__Measurement`: `4800151`
- `scope_family_count__Measurement`: `3924046`
- `scope_publn_count__Measurement`: `6373812`
- `scope_appln_count__Semiconductors`: `2551134`
- `scope_family_count__Semiconductors`: `1522749`
- `scope_publn_count__Semiconductors`: `3794315`
- `scope_appln_count__Electrical machinery, apparatus, energy`: `6549502`
- `scope_family_count__Electrical machinery, apparatus, energy`: `5061217`
- `scope_publn_count__Electrical machinery, apparatus, energy`: `8536504`
- `scope_appln_count__Computer technology`: `6224533`
- `scope_family_count__Computer technology`: `4490120`
- `scope_publn_count__Computer technology`: `9007569`
- `scope_appln_count__Telecommunications`: `2178969`
- `scope_family_count__Telecommunications`: `1473614`
- `scope_publn_count__Telecommunications`: `3173773`
- `scope_appln_count__Digital communication`: `3160801`
- `scope_family_count__Digital communication`: `1829831`
- `scope_publn_count__Digital communication`: `4741516`

## silver-core | success

- Summary: Built core family-first Silver entities and bounded ownership/field normalizations.
- Started: 2026-04-01T06:05:46+00:00
- Finished: 2026-04-01T06:14:49+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_ipc_cpc_canonical.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_agent_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_up_status.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_proc_step_features.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_display_ledger.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-core.json`

### Methods

1. Collapsed in-scope applications to the canonical family core.
2. Normalized publication stage semantics from publication kinds.
3. Materialized owner harmonization and WIPO field assignment as reusable Silver entities.

### Calculations

1. Grant-stage classification is inferred from publication kind prefix `B` and modifier-stage from `C`.
2. Portfolio ownership remains bounded to the in-scope family universe only.

### Downstream Impacts

1. silver_family_core and its sibling Silver tables feed all Gold family, portfolio, Market Intelligence, forecast, and semantic marts.
2. The legal ledger, family status, market weighting, and Register tables created here become the canonical support layer for downstream point-in-time analytics and EP publication evidence views.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md


### Metrics

- `silver_family_core_rows`: `21353101`
- `silver_family_member_publications_rows`: `45738731`
- `silver_kind_code_normalization_rows`: `10097`
- `silver_family_wipo_fields_rows`: `21353101`
- `silver_assignee_harmonized_rows`: `20894233`
- `silver_family_ipc_cpc_canonical_rows`: `21353101`
- `silver_tiered_market_weighting_rows`: `8336`
- `silver_up_status_rows`: `21353101`
- `silver_family_jurisdiction_unrolled_rows`: `29523316`
- `silver_legal_status_event_ledger_rows`: `153932599`
- `silver_family_status_pt_rows`: `21353101`
- `silver_ep_register_core_rows`: `1090998`
- `silver_ep_register_agent_summary_rows`: `1006327`
- `silver_ep_register_current_opposition_rows`: `1090998`
- `silver_ep_register_up_status_rows`: `2`
- `silver_ep_register_proc_step_features_rows`: `1006327`
- `silver_ep_register_display_ledger_rows`: `1273328`

## silver-enrichment | success

- Summary: Built Silver citation, coverage, enforceability, OECD-style proxy, and Market Intelligence segment layers.
- Started: 2026-04-01T06:08:01+00:00
- Finished: 2026-04-01T06:14:50+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_trend_tables.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_segments.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_timeseries.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment.json`

### Methods

1. Mapped in-scope publications to citation edges and flagged out-of-scope references as ghost-node candidates.
2. Derived market-intelligence segment tables from field-year family activity inside the bounded universe.
3. Built lightweight MVP proxies for coverage, enforceability, and quality from validated Silver dependencies.

### Calculations

1. Family adjusted citation score is an MVP proxy based on in-scope citation volume and out-of-scope citation share.
2. Market-state labels use recent family-count momentum by field-year segment.

### Downstream Impacts

1. These Silver enrichment tables feed Gold blocking power, Market Intelligence, attacker summaries, portfolio summaries, and forecast feature generation.
2. Weak citation coverage or legal weighting here directly distorts compare, portfolio, and family-level UI cards.

### Governing Docs

1. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
2. docs/new-feature-ideas/field-sliced-competitor-intelligence-and-tech-trend-requirements.md
3. docs/new-feature-ideas/parallel-global-and-local-trend-engines-requirements.md


### Metrics

- `citation_edge_count`: `30166820`
- `citation_unique_source_publication_count`: `19765529`
- `citation_unique_cited_publication_count`: `9220675`
- `citation_unique_source_family_count`: `10871882`
- `citation_unique_cited_family_count`: `4961245`
- `silver_family_citation_metrics_rows`: `10871882`
- `silver_family_trend_tables_rows`: `23816698`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `21353101`
- `silver_family_oecd_quality_rows`: `21353101`
- `silver_market_intelligence_segments_rows`: `10`
- `silver_market_intelligence_timeseries_rows`: `504`

## silver-semantic | success

- Summary: Built representative family text and semantic eligibility according to the EPAB/PATSTAT hierarchy.
- Started: 2026-04-01T06:08:14+00:00
- Finished: 2026-04-01T06:15:07+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_claims.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_abstr.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-semantic.json`

### Methods

1. Selected one representative text payload per family using EP grant claim first, then PATSTAT abstract fallback.
2. Materialized semantic sample eligibility as a bounded active-grant cohort for MVP.

### Calculations

1. Claim-space payloads exclude A-document claims and prefer claim 1 only.
2. Abstract fallback is marked explicitly through `is_abstract_fallback`.

### Downstream Impacts

1. These representative text and eligibility tables feed vector payload generation and the semantic comparison UI.
2. If empty or degraded, semantic discovery and comparison surfaces should be treated as unavailable in the app.

### Governing Docs

1. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
2. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `silver_family_text_representative_rows`: `20331702`
- `silver_semantic_sampling_eligibility_rows`: `2135310`

## scope | success

- Summary: Built bounded-scope application, family, publication, and owner seeds for the mega-cluster universe.
- Started: 2026-04-01T21:39:42+00:00
- Finished: 2026-04-01T21:40:29+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_ipc.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_techn_field.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pers_appln.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_person.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ref_techn_field_ipc.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/scope.json`

### Methods

1. Resolved the in-scope family universe from selected WIPO field mappings before heavy downstream analytics.
2. Preferred direct PATSTAT technology-field inputs when present and fell back to IPC subclass to WIPO field concordance otherwise.
3. Bridged the in-scope applications to families, publications, and owners to create the canonical bounded universe.

### Calculations

1. An in-scope application is one whose technology-field mapping falls inside the selected 10 WIPO fields.
2. An in-scope family is any DOCDB family reachable from the in-scope application seed.
3. An in-scope portfolio owner seed is derived from applicant-side application-person links only.

### Downstream Impacts

1. These scope seeds bound every downstream family, publication, owner, and portfolio calculation in the MVP warehouse.
2. An over-broad or under-broad seed will contaminate blocking power, Market Intelligence, forecasts, semantic sampling, and Data Room counts.

### Governing Docs

1. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md
2. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md
3. docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md


### Metrics

- `scope_appln_count`: `32871909`
- `scope_family_count`: `21353101`
- `scope_publn_count`: `42692835`
- `scope_owner_count`: `37134586`
- `scope_appln_count__IT methods for management`: `1343950`
- `scope_family_count__IT methods for management`: `1039957`
- `scope_publn_count__IT methods for management`: `1770411`
- `scope_appln_count__Basic communication processes`: `602460`
- `scope_family_count__Basic communication processes`: `384536`
- `scope_publn_count__Basic communication processes`: `909364`
- `scope_appln_count__Measurement`: `4800151`
- `scope_family_count__Measurement`: `3924046`
- `scope_publn_count__Measurement`: `6373812`
- `scope_appln_count__Audio-visual technology`: `3449359`
- `scope_family_count__Audio-visual technology`: `2446006`
- `scope_publn_count__Audio-visual technology`: `4757897`
- `scope_appln_count__Control`: `2011050`
- `scope_family_count__Control`: `1644622`
- `scope_publn_count__Control`: `2673570`
- `scope_appln_count__Digital communication`: `3160801`
- `scope_family_count__Digital communication`: `1829831`
- `scope_publn_count__Digital communication`: `4741516`
- `scope_appln_count__Computer technology`: `6224533`
- `scope_family_count__Computer technology`: `4490120`
- `scope_publn_count__Computer technology`: `9007569`
- `scope_appln_count__Telecommunications`: `2178969`
- `scope_family_count__Telecommunications`: `1473614`
- `scope_publn_count__Telecommunications`: `3173773`
- `scope_appln_count__Electrical machinery, apparatus, energy`: `6549502`
- `scope_family_count__Electrical machinery, apparatus, energy`: `5061217`
- `scope_publn_count__Electrical machinery, apparatus, energy`: `8536504`
- `scope_appln_count__Semiconductors`: `2551134`
- `scope_family_count__Semiconductors`: `1522749`
- `scope_publn_count__Semiconductors`: `3794315`

## silver-core | success

- Summary: Built core family-first Silver entities and bounded ownership/field normalizations.
- Started: 2026-04-01T21:40:33+00:00
- Finished: 2026-04-01T21:48:10+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_ipc_cpc_canonical.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_agent_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_up_status.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_proc_step_features.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_display_ledger.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-core.json`

### Methods

1. Collapsed in-scope applications to the canonical family core.
2. Normalized publication stage semantics from publication kinds.
3. Materialized owner harmonization and WIPO field assignment as reusable Silver entities.

### Calculations

1. Grant-stage classification is inferred from publication kind prefix `B` and modifier-stage from `C`.
2. Portfolio ownership remains bounded to the in-scope family universe only.

### Downstream Impacts

1. silver_family_core and its sibling Silver tables feed all Gold family, portfolio, Market Intelligence, forecast, and semantic marts.
2. The legal ledger, family status, market weighting, and Register tables created here become the canonical support layer for downstream point-in-time analytics and EP publication evidence views.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md


### Metrics

- `silver_family_core_rows`: `21353101`
- `silver_family_member_publications_rows`: `42692835`
- `silver_kind_code_normalization_rows`: `10097`
- `silver_family_wipo_fields_rows`: `21353101`
- `silver_assignee_harmonized_rows`: `20894233`
- `silver_family_ipc_cpc_canonical_rows`: `21353101`
- `silver_tiered_market_weighting_rows`: `8336`
- `silver_up_status_rows`: `21353101`
- `silver_family_jurisdiction_unrolled_rows`: `29523316`
- `silver_legal_status_event_ledger_rows`: `152285488`
- `silver_family_status_pt_rows`: `21353101`
- `silver_ep_register_core_rows`: `1090998`
- `silver_ep_register_agent_summary_rows`: `1006327`
- `silver_ep_register_current_opposition_rows`: `1090998`
- `silver_ep_register_up_status_rows`: `2`
- `silver_ep_register_proc_step_features_rows`: `1006327`
- `silver_ep_register_display_ledger_rows`: `1273328`

## silver-enrichment | success

- Summary: Built Silver citation, coverage, enforceability, OECD-style proxy, and Market Intelligence segment layers.
- Started: 2026-04-01T21:41:36+00:00
- Finished: 2026-04-01T21:48:10+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_trend_tables.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_segments.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_timeseries.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment.json`

### Methods

1. Mapped in-scope publications to citation edges and flagged out-of-scope references as ghost-node candidates.
2. Derived market-intelligence segment tables from field-year family activity inside the bounded universe.
3. Built lightweight MVP proxies for coverage, enforceability, and quality from validated Silver dependencies.

### Calculations

1. Family adjusted citation score is an MVP proxy based on in-scope citation volume and out-of-scope citation share.
2. Market-state labels use recent family-count momentum by field-year segment.

### Downstream Impacts

1. These Silver enrichment tables feed Gold blocking power, Market Intelligence, attacker summaries, portfolio summaries, and forecast feature generation.
2. Weak citation coverage or legal weighting here directly distorts compare, portfolio, and family-level UI cards.

### Governing Docs

1. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
2. docs/new-feature-ideas/field-sliced-competitor-intelligence-and-tech-trend-requirements.md
3. docs/new-feature-ideas/parallel-global-and-local-trend-engines-requirements.md


### Metrics

- `citation_edge_count`: `25169771`
- `citation_unique_source_publication_count`: `19765529`
- `citation_unique_cited_publication_count`: `9220675`
- `citation_unique_source_family_count`: `10871882`
- `citation_unique_cited_family_count`: `4961245`
- `silver_family_citation_metrics_rows`: `21353101`
- `silver_family_trend_tables_rows`: `23816698`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `21353101`
- `silver_family_oecd_quality_rows`: `21353101`
- `silver_market_intelligence_segments_rows`: `10`
- `silver_market_intelligence_timeseries_rows`: `504`

## silver-semantic | success

- Summary: Built representative family text and semantic eligibility according to the EPAB/PATSTAT hierarchy.
- Started: 2026-04-01T21:41:46+00:00
- Finished: 2026-04-01T21:48:14+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_claims.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_abstr.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-semantic.json`

### Methods

1. Selected one representative text payload per family using EP grant claim first, then PATSTAT abstract fallback.
2. Materialized semantic sample eligibility as a bounded active-grant cohort for MVP.

### Calculations

1. Claim-space payloads exclude A-document claims and prefer claim 1 only.
2. Abstract fallback is marked explicitly through `is_abstract_fallback`.

### Downstream Impacts

1. These representative text and eligibility tables feed vector payload generation and the semantic comparison UI.
2. If empty or degraded, semantic discovery and comparison surfaces should be treated as unavailable in the app.

### Governing Docs

1. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
2. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `silver_family_text_representative_rows`: `20295898`
- `silver_semantic_sampling_eligibility_rows`: `21353101`

## silver-core | success

- Summary: Built core family-first Silver entities and bounded ownership/field normalizations.
- Started: 2026-04-01T22:18:35+00:00
- Finished: 2026-04-01T22:26:32+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_ipc_cpc_canonical.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_agent_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_up_status.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_proc_step_features.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_display_ledger.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-core.json`

### Methods

1. Collapsed in-scope applications to the canonical family core.
2. Normalized publication stage semantics from publication kinds.
3. Materialized owner harmonization and WIPO field assignment as reusable Silver entities.

### Calculations

1. Grant-stage classification is inferred from publication kind prefix `B` and modifier-stage from `C`.
2. Portfolio ownership remains bounded to the in-scope family universe only.

### Downstream Impacts

1. silver_family_core and its sibling Silver tables feed all Gold family, portfolio, Market Intelligence, forecast, and semantic marts.
2. The legal ledger, family status, market weighting, and Register tables created here become the canonical support layer for downstream point-in-time analytics and EP publication evidence views.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md


### Metrics

- `silver_family_core_rows`: `21353101`
- `silver_family_member_publications_rows`: `42692835`
- `silver_kind_code_normalization_rows`: `10097`
- `silver_family_wipo_fields_rows`: `21353101`
- `silver_assignee_harmonized_rows`: `20894233`
- `silver_family_ipc_cpc_canonical_rows`: `21353101`
- `silver_tiered_market_weighting_rows`: `8336`
- `silver_up_status_rows`: `21353101`
- `silver_family_jurisdiction_unrolled_rows`: `29523316`
- `silver_legal_status_event_ledger_rows`: `152285488`
- `silver_family_status_pt_rows`: `21353101`
- `silver_ep_register_core_rows`: `1090998`
- `silver_ep_register_agent_summary_rows`: `1006327`
- `silver_ep_register_current_opposition_rows`: `1090998`
- `silver_ep_register_up_status_rows`: `2`
- `silver_ep_register_proc_step_features_rows`: `1006327`
- `silver_ep_register_display_ledger_rows`: `1273328`

## silver-enrichment | success

- Summary: Built Silver citation, coverage, enforceability, OECD-style proxy, and Market Intelligence segment layers.
- Started: 2026-04-01T22:19:55+00:00
- Finished: 2026-04-01T22:26:33+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_docdb_fam_citn.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_npl_publn.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges_clean.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_npl_backlinks.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_trend_tables.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_segments.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_timeseries.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment.json`

### Methods

1. Mapped PATSTAT publication and DOCDB family citation sources into bounded family citation edges and cleaned family-level impact inputs.
2. Derived market-intelligence segment tables from field-year family activity inside the bounded universe.
3. Built lightweight MVP proxies for coverage, enforceability, and quality from validated Silver dependencies.

### Calculations

1. Family adjusted citation score now uses cleaned family-level forward citation intensity with a cohort normalization fallback.
2. Market-state labels use recent family-count momentum by field-year segment.

### Downstream Impacts

1. These Silver enrichment tables feed Gold blocking power, Market Intelligence, attacker summaries, portfolio summaries, and forecast feature generation.
2. Weak citation coverage or legal weighting here directly distorts compare, portfolio, and family-level UI cards.

### Governing Docs

1. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
2. docs/new-feature-ideas/field-sliced-competitor-intelligence-and-tech-trend-requirements.md
3. docs/new-feature-ideas/parallel-global-and-local-trend-engines-requirements.md


### Metrics

- `citation_edge_count`: `17461197`
- `citation_unique_source_family_count`: `10922324`
- `citation_unique_cited_family_count`: `6019674`
- `citation_out_of_bounds_edge_count`: `3441661`
- `silver_family_citation_edges_rows`: `17461197`
- `silver_family_citation_edges_clean_rows`: `17461197`
- `silver_family_npl_backlinks_rows`: `14380370`
- `silver_family_citation_metrics_rows`: `21353101`
- `silver_family_trend_tables_rows`: `23816698`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `21353101`
- `silver_family_oecd_quality_rows`: `21353101`
- `silver_market_intelligence_segments_rows`: `10`
- `silver_market_intelligence_timeseries_rows`: `504`

## silver-semantic | success

- Summary: Built representative family text and semantic eligibility according to the EPAB/PATSTAT hierarchy.
- Started: 2026-04-01T22:20:13+00:00
- Finished: 2026-04-01T22:26:36+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_claims.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_abstr.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-semantic.json`

### Methods

1. Selected one representative text payload per family using EP grant claim first, then PATSTAT abstract fallback.
2. Materialized semantic sample eligibility as a bounded active-grant cohort for MVP.

### Calculations

1. Claim-space payloads exclude A-document claims and prefer claim 1 only.
2. Abstract fallback is marked explicitly through `is_abstract_fallback`.

### Downstream Impacts

1. These representative text and eligibility tables feed vector payload generation and the semantic comparison UI.
2. If empty or degraded, semantic discovery and comparison surfaces should be treated as unavailable in the app.

### Governing Docs

1. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
2. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `silver_family_text_representative_rows`: `20295898`
- `silver_semantic_sampling_eligibility_rows`: `21353101`

## silver-core | success

- Summary: Built core family-first Silver entities and bounded ownership/field normalizations.
- Started: 2026-04-01T22:52:58+00:00
- Finished: 2026-04-01T23:00:47+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_ipc_cpc_canonical.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_agent_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_up_status.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_proc_step_features.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_display_ledger.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-core.json`

### Methods

1. Collapsed in-scope applications to the canonical family core.
2. Normalized publication stage semantics from publication kinds.
3. Materialized owner harmonization and WIPO field assignment as reusable Silver entities.

### Calculations

1. Grant-stage classification is inferred from publication kind prefix `B` and modifier-stage from `C`.
2. Portfolio ownership remains bounded to the in-scope family universe only.

### Downstream Impacts

1. silver_family_core and its sibling Silver tables feed all Gold family, portfolio, Market Intelligence, forecast, and semantic marts.
2. The legal ledger, family status, market weighting, and Register tables created here become the canonical support layer for downstream point-in-time analytics and EP publication evidence views.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md


### Metrics

- `silver_family_core_rows`: `21353101`
- `silver_family_member_publications_rows`: `42692835`
- `silver_kind_code_normalization_rows`: `10097`
- `silver_family_wipo_fields_rows`: `21353101`
- `silver_assignee_harmonized_rows`: `20894233`
- `silver_family_ipc_cpc_canonical_rows`: `21353101`
- `silver_tiered_market_weighting_rows`: `8336`
- `silver_up_status_rows`: `21353101`
- `silver_family_jurisdiction_unrolled_rows`: `29523316`
- `silver_legal_status_event_ledger_rows`: `152285488`
- `silver_family_status_pt_rows`: `21353101`
- `silver_ep_register_core_rows`: `1090998`
- `silver_ep_register_agent_summary_rows`: `1006327`
- `silver_ep_register_current_opposition_rows`: `1090998`
- `silver_ep_register_up_status_rows`: `2`
- `silver_ep_register_proc_step_features_rows`: `1006327`
- `silver_ep_register_display_ledger_rows`: `1273328`

## silver-enrichment | success

- Summary: Built Silver citation, coverage, enforceability, OECD-style proxy, and Market Intelligence segment layers.
- Started: 2026-04-01T22:54:14+00:00
- Finished: 2026-04-01T23:00:48+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_docdb_fam_citn.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_npl_publn.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges_clean.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_npl_backlinks.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_trend_tables.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_segments.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_timeseries.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment.json`

### Methods

1. Mapped PATSTAT publication and DOCDB family citation sources into bounded family citation edges and cleaned family-level impact inputs.
2. Derived market-intelligence segment tables from field-year family activity inside the bounded universe.
3. Built lightweight MVP proxies for coverage, enforceability, and quality from validated Silver dependencies.

### Calculations

1. Family adjusted citation score now uses cleaned family-level forward citation intensity with a cohort normalization fallback.
2. Market-state labels use recent family-count momentum by field-year segment.

### Downstream Impacts

1. These Silver enrichment tables feed Gold blocking power, Market Intelligence, attacker summaries, portfolio summaries, and forecast feature generation.
2. Weak citation coverage or legal weighting here directly distorts compare, portfolio, and family-level UI cards.

### Governing Docs

1. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
2. docs/new-feature-ideas/field-sliced-competitor-intelligence-and-tech-trend-requirements.md
3. docs/new-feature-ideas/parallel-global-and-local-trend-engines-requirements.md


### Metrics

- `citation_edge_count`: `17461197`
- `citation_unique_source_family_count`: `10922324`
- `citation_unique_cited_family_count`: `6019674`
- `citation_out_of_bounds_edge_count`: `3441661`
- `silver_family_citation_edges_rows`: `17461197`
- `silver_family_citation_edges_clean_rows`: `17461197`
- `silver_family_npl_backlinks_rows`: `14380370`
- `silver_family_citation_metrics_rows`: `21353101`
- `silver_family_trend_tables_rows`: `23816698`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `21353101`
- `silver_family_oecd_quality_rows`: `21353101`
- `silver_market_intelligence_segments_rows`: `10`
- `silver_market_intelligence_timeseries_rows`: `504`

## silver-semantic | success

- Summary: Built representative family text and semantic eligibility according to the EPAB/PATSTAT hierarchy.
- Started: 2026-04-01T22:54:36+00:00
- Finished: 2026-04-01T23:00:51+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_claims.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_abstr.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_semantic_sampling_eligibility.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-semantic.json`

### Methods

1. Selected one representative text payload per family using EP grant claim first, then PATSTAT abstract fallback.
2. Materialized semantic sample eligibility as a bounded active-grant cohort for MVP.

### Calculations

1. Claim-space payloads exclude A-document claims and prefer claim 1 only.
2. Abstract fallback is marked explicitly through `is_abstract_fallback`.

### Downstream Impacts

1. These representative text and eligibility tables feed vector payload generation and the semantic comparison UI.
2. If empty or degraded, semantic discovery and comparison surfaces should be treated as unavailable in the app.

### Governing Docs

1. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
2. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `silver_family_text_representative_rows`: `20295898`
- `silver_semantic_sampling_eligibility_rows`: `21353101`

## semantic | failed

- Summary: Packaged vector payloads, embedding manifests, and ANN placeholder metadata for the MVP semantic layer.
- Started: 2026-04-01T23:31:04+00:00
- Finished: 2026-04-01T23:31:04+00:00



### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic.json`

### Methods

1. Derived claim and abstract vector payloads from the representative family text table using the active EPAB-first representative-text policy.
2. Used deterministic hash embeddings as the default local MVP embedding method until a promoted external embedding model is wired in.

### Calculations

1. Claim and abstract vector spaces remain physically separate.
2. Only bounded semantic candidates are embedded.


### Governing Docs

1. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
2. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. Representative text and semantic eligibility must exist before vector packaging.

## silver-enrichment | success

- Summary: Built Silver citation, coverage, enforceability, OECD-style proxy, and Market Intelligence segment layers.
- Started: 2026-04-02T09:29:43+00:00
- Finished: 2026-04-02T09:35:54+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_docdb_fam_citn.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_npl_publn.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges_clean.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_npl_backlinks.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_trend_tables.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_field_contributions.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_segments.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_market_intelligence_timeseries.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment.json`

### Methods

1. Mapped PATSTAT publication and DOCDB family citation sources into bounded family citation edges and cleaned family-level impact inputs.
2. Materialized a publication-dated enriched citation network with citing-side assignee, stage, market, and trend context.
3. Derived market-intelligence segment tables from field-year family activity inside the bounded universe.
4. Built lightweight MVP proxies for coverage, enforceability, and quality from validated Silver dependencies.

### Calculations

1. Family adjusted citation score now uses 7-year clean weighted forward citation influence with a cohort normalization fallback.
2. Market-state labels use recent family-count momentum by field-year segment.

### Downstream Impacts

1. These Silver enrichment tables feed Gold blocking power, Market Intelligence, attacker summaries, portfolio summaries, and forecast feature generation.
2. Weak citation coverage or legal weighting here directly distorts compare, portfolio, and family-level UI cards.

### Governing Docs

1. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
2. docs/new-feature-ideas/field-sliced-competitor-intelligence-and-tech-trend-requirements.md
3. docs/new-feature-ideas/parallel-global-and-local-trend-engines-requirements.md


### Metrics

- `citation_edge_count`: `17461197`
- `citation_unique_source_family_count`: `10922324`
- `citation_unique_cited_family_count`: `6019674`
- `citation_out_of_bounds_edge_count`: `3441661`
- `silver_family_citation_edges_rows`: `17461197`
- `silver_family_citation_edges_clean_rows`: `17461197`
- `silver_enriched_citation_network_rows`: `19602108`
- `silver_family_npl_backlinks_rows`: `14380370`
- `silver_family_citation_metrics_rows`: `21353101`
- `silver_family_trend_tables_rows`: `23816698`
- `silver_global_tech_trends_timeseries_rows`: `504`
- `silver_local_tech_trends_timeseries_rows`: `21488`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `36096788`
- `silver_family_field_contributions_rows`: `23816698`
- `silver_family_oecd_quality_rows`: `21353101`
- `silver_market_intelligence_segments_rows`: `10`
- `silver_market_intelligence_timeseries_rows`: `504`

## normalize-kind-code | success

- Summary: Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.
- Started: 2026-04-02T10:05:25+00:00
- Finished: 2026-04-02T10:05:26+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_manual_overrides.csv

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_observed_pairs.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_review_queue.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/normalize-kind-code.json`

### Methods

1. Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.
2. Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.
3. Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.

### Calculations

1. Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.
2. EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.

### Downstream Impacts

1. This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.
2. Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue.

### Metrics

- `observed_pair_count`: `641`
- `seed_input_pair_count`: `10097`
- `auto_generated_pair_count`: `0`
- `review_queue_pair_count`: `241`
- `final_pair_count`: `10097`

## bronze | success

- Summary: Generated typed and source-aware Bronze parquet for PATSTAT, Register, and reference inputs.
- Started: 2026-04-02T10:05:33+00:00
- Finished: 2026-04-02T10:08:39+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls201_appln.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls202_appln_title.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls203_appln_abstr.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls204_appln_prior.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls206_person.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls207_pers_appln.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls209_appln_ipc.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls212_citation.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls214_npl_publn.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls216_appln_contn.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls224_appln_cpc.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls230_appln_techn_field.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls228_docdb_fam_citn.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls231_inpadoc_legal_event.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls803_legal_event_code.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg101_appln.parquet
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg403_appln_status.parquet
19. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg107_parties.parquet
20. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg111_licensee.parquet
21. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg125_appeal.parquet
22. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg130_opponent.parquet
23. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg201_proc_step.parquet
24. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg202_proc_step_text.parquet
25. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg203_proc_step_date.parquet
26. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg301_event_data.parquet
27. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg402_event_text.parquet
28. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg701_appln.parquet
29. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg731_event_data.parquet
30. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg741_appln_status.parquet
31. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/register/reg742_event_text.parquet
32. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/wipo_techn_field_ipc.parquet
33. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/iso_country_map.parquet
34. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/world_bank_gdp_ppp.parquet
35. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/us_chamber_ip_index.parquet
36. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/up_member_states.parquet
37. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/kind_code_normalization.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_title.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_abstr.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_prior.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_person.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pers_appln.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_ipc.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_npl_publn.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_contn.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_cpc.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_appln_techn_field.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_docdb_fam_citn.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_inpadoc_legal_event.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ref_legal_event_code.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg101_appln.parquet
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg403_appln_status.parquet
19. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg107_parties.parquet
20. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg111_licensee.parquet
21. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg125_appeal.parquet
22. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg130_opponent.parquet
23. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg201_proc_step.parquet
24. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg202_proc_step_text.parquet
25. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg203_proc_step_date.parquet
26. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg301_event_data.parquet
27. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg402_event_text.parquet
28. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg701_appln.parquet
29. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg731_event_data.parquet
30. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg741_appln_status.parquet
31. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_reg742_event_text.parquet
32. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ref_techn_field_ipc.parquet
33. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_iso_country_map.parquet
34. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_world_bank_gdp_ppp.parquet
35. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_us_chamber_ip_index.parquet
36. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_up_member_states.parquet
37. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_kind_code_normalization_seed.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/bronze.json`

### Methods

1. Applied table-specific typing for PATSTAT and Register key/date columns while preserving source columns.
2. Normalized reference inputs to the canonical Bronze schemas required by Silver legal, market, and scope logic.

### Calculations

1. Bronze row counts reflect the landed bounded raw slice, not downstream family-first aggregates.

### Downstream Impacts

1. These Bronze parquet tables feed scope seeding, legal ledger reconstruction, market weighting, EP Register overlays, citation metrics, and OECD support layers.
2. Typing errors or missing normalized reference columns here will propagate directly into Silver joins and point-in-time analytics.

### Governing Docs

1. docs/next-phase-v2/26-patentiq-v2-mega-cluster-raw-extraction-and-bronze-bounding-strategy.md
2. docs/data/patstat-schema.md
3. docs/data/patstat-register-schema.md

### Warnings

1. Skipped `bronze_ext_cpc_coverage` because no matching raw file was found.
2. Skipped `bronze_ext_cpc_ipc_weights` because no matching raw file was found.
3. Skipped `bronze_ext_oecd_indicator_seed` because no matching raw file was found.

### Metrics

- `bronze_patstat_appln_rows`: `36231729`
- `bronze_patstat_appln_title_rows`: `34149771`
- `bronze_patstat_appln_abstr_rows`: `32628318`
- `bronze_patstat_appln_prior_rows`: `12240913`
- `bronze_patstat_person_rows`: `25484970`
- `bronze_patstat_pers_appln_rows`: `132921009`
- `bronze_patstat_appln_ipc_rows`: `40798728`
- `bronze_patstat_pat_publn_rows`: `47798843`
- `bronze_patstat_citation_rows`: `27652952`
- `bronze_patstat_npl_publn_rows`: `5281343`
- `bronze_patstat_appln_contn_rows`: `1839143`
- `bronze_patstat_appln_cpc_rows`: `31300011`
- `bronze_patstat_appln_techn_field_rows`: `37135004`
- `bronze_patstat_docdb_fam_citn_rows`: `18526500`
- `bronze_patstat_inpadoc_legal_event_rows`: `138761674`
- `bronze_ref_legal_event_code_rows`: `62`
- `bronze_reg101_appln_rows`: `1138403`
- `bronze_reg403_appln_status_rows`: `17`
- `bronze_reg107_parties_rows`: `7541254`
- `bronze_reg111_licensee_rows`: `4216`
- `bronze_reg125_appeal_rows`: `9921`
- `bronze_reg130_opponent_rows`: `16398`
- `bronze_reg201_proc_step_rows`: `1195313`
- `bronze_reg202_proc_step_text_rows`: `1442273`
- `bronze_reg203_proc_step_date_rows`: `1446346`
- `bronze_reg301_event_data_rows`: `1675053`
- `bronze_reg402_event_text_rows`: `355`
- `bronze_reg701_appln_rows`: `22860`
- `bronze_reg731_event_data_rows`: `22686`
- `bronze_reg741_appln_status_rows`: `7`
- `bronze_reg742_event_text_rows`: `20`
- `bronze_ref_techn_field_ipc_rows`: `771`
- `bronze_ext_iso_country_map_rows`: `296`
- `bronze_ext_world_bank_gdp_ppp_rows`: `8336`
- `bronze_ext_us_chamber_ip_index_rows`: `55`
- `bronze_ext_up_member_states_rows`: `18`
- `bronze_ext_kind_code_normalization_seed_rows`: `10097`
- `bronze_total_row_count`: `637285665`

## bronze-uspto-fulltext | success

- Summary: USPTO Bronze parsing was deferred because USPTO is configured for the external ODP stream path and no direct Bronze outputs are present in this runtime.
- Started: 2026-04-02T10:07:20+00:00
- Finished: 2026-04-02T10:08:39+00:00



### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/bronze-uspto-fulltext.json`

### Methods

1. Parsed USPTO XML application/publication identifiers, abstracts, and claims.
2. Preserved publication kind and claim ordering fields required for semantic hierarchy selection.
3. Skipped bounded-XML parsing because USPTO is handled by the separate `prebronze-uspto-odp` stage when that external path is executed.

### Calculations

1. No family collapse or semantic prioritization occurs in Bronze. This stage only lands text-provider tables.

### Downstream Impacts

1. These tables feed representative claim and abstract selection in the semantic Silver stage only.
2. They must not be used to override PATSTAT or Register harmonized metadata layers downstream.

### Governing Docs

1. docs/data/uspto-full-text-schema.md
2. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `uspto_odp_outputs_present`: `0`

## bronze-epab-fulltext | success

- Summary: Parsed EPAB payloads into Bronze text-provider tables for semantic workflows.
- Started: 2026-04-02T10:07:20+00:00
- Finished: 2026-04-02T10:08:52+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_publication.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_publication.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_abstract.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/epab/epab_claims.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_document.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_publication.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_abstract.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_epab_claims.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/bronze-epab-fulltext.json`

### Methods

1. Parsed EPAB publication/application anchors, abstracts, and claims from JSON payloads.
2. Preserved language and sequence fields for English-claim selection and abstract fallback.

### Calculations

1. Bronze EPAB is source-faithful and does not replace PATSTAT/Register metadata for analytical truth.

### Downstream Impacts

1. These Bronze tables feed EP grant claim selection, abstract fallback, and Data Room transparency outputs.
2. They must remain text-provider tables and not become the canonical source for classifications or parties in downstream analytics.

### Governing Docs

1. docs/data/ep-full-text-publication-database-schema.md
2. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `bronze_epab_document_rows`: `1679816`
- `bronze_epab_publication_rows`: `1679816`
- `bronze_epab_abstract_rows`: `0`
- `bronze_epab_claims_rows`: `2763676`

## silver-enrichment-kind-legal-refresh | success

- Summary: Rebuilt only the legal-weighted Silver marts after kind-code curation using existing citation and trend support outputs.
- Started: 2026-04-02T13:03:11+00:00
- Finished: 2026-04-02T13:06:35+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_field_contributions.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-kind-legal-refresh.json`

### Methods

1. Reused refreshed citation metrics and existing trend support outputs.
2. Recomputed only family coverage, enforceability branches, field contributions, and OECD proxy outputs from the current kind-code normalization layer.

### Calculations

1. Branch stage and field contribution values are refreshed from the current Silver kind-code normalization table without rebuilding the semantic layer.


### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `kindcode_refresh_affected_family_rows`: `5934204`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `36096788`
- `silver_family_field_contributions_rows`: `23816698`
- `silver_family_oecd_quality_rows`: `21353101`

## normalize-kind-code | success

- Summary: Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.
- Started: 2026-04-02T13:27:11+00:00
- Finished: 2026-04-02T13:27:12+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_manual_overrides.csv

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_observed_pairs.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_review_queue.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/normalize-kind-code.json`

### Methods

1. Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.
2. Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.
3. Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.

### Calculations

1. Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.
2. EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.

### Downstream Impacts

1. This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.
2. Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue.

### Metrics

- `observed_pair_count`: `641`
- `seed_input_pair_count`: `10097`
- `auto_generated_pair_count`: `0`
- `review_queue_pair_count`: `237`
- `final_pair_count`: `10097`

## silver-enrichment-kind-legal-refresh | success

- Summary: Rebuilt only the legal-weighted Silver marts after kind-code curation using existing citation and trend support outputs.
- Started: 2026-04-02T16:27:23+00:00
- Finished: 2026-04-02T16:29:02+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_field_contributions.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-kind-legal-refresh.json`

### Methods

1. Reused refreshed citation metrics and existing trend support outputs.
2. Recomputed only family coverage, enforceability branches, field contributions, and OECD proxy outputs from the current kind-code normalization layer.

### Calculations

1. Branch stage and field contribution values are refreshed from the current Silver kind-code normalization table without rebuilding the semantic layer.


### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `kindcode_refresh_affected_family_rows`: `6050238`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `36096788`
- `silver_family_field_contributions_rows`: `23816698`
- `silver_family_oecd_quality_rows`: `21353101`

## normalize-kind-code | success

- Summary: Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.
- Started: 2026-04-02T16:41:52+00:00
- Finished: 2026-04-02T16:41:53+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_manual_overrides.csv

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_observed_pairs.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_review_queue.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/normalize-kind-code.json`

### Methods

1. Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.
2. Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.
3. Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.

### Calculations

1. Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.
2. EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.

### Downstream Impacts

1. This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.
2. Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue.

### Metrics

- `observed_pair_count`: `641`
- `seed_input_pair_count`: `10097`
- `auto_generated_pair_count`: `0`
- `review_queue_pair_count`: `233`
- `final_pair_count`: `10097`

## silver-enrichment-kind-legal-refresh | success

- Summary: Rebuilt only the legal-weighted Silver marts after kind-code curation using existing citation and trend support outputs.
- Started: 2026-04-02T16:42:18+00:00
- Finished: 2026-04-02T17:01:13+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_field_contributions.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-kind-legal-refresh.json`

### Methods

1. Reused refreshed citation metrics and existing trend support outputs.
2. Recomputed only family coverage, enforceability branches, field contributions, and OECD proxy outputs from the current kind-code normalization layer.

### Calculations

1. Branch stage and field contribution values are refreshed from the current Silver kind-code normalization table without rebuilding the semantic layer.


### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `kindcode_refresh_affected_family_rows`: `6050238`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `36096788`
- `silver_family_field_contributions_rows`: `23816698`
- `silver_family_oecd_quality_rows`: `21353101`

## silver-core | success

- Summary: Built core family-first Silver entities and bounded ownership/field normalizations.
- Started: 2026-04-02T16:42:18+00:00
- Finished: 2026-04-02T17:03:14+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_ipc_cpc_canonical.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_agent_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_up_status.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_proc_step_features.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_display_ledger.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-core.json`

### Methods

1. Collapsed in-scope applications to the canonical family core.
2. Normalized publication stage semantics from publication kinds.
3. Materialized owner harmonization and WIPO field assignment as reusable Silver entities.

### Calculations

1. Grant-stage classification is inferred from publication kind prefix `B` and modifier-stage from `C`.
2. Portfolio ownership remains bounded to the in-scope family universe only.

### Downstream Impacts

1. silver_family_core and its sibling Silver tables feed all Gold family, portfolio, Market Intelligence, forecast, and semantic marts.
2. The legal ledger, family status, market weighting, and Register tables created here become the canonical support layer for downstream point-in-time analytics and EP publication evidence views.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md


### Metrics

- `silver_family_core_rows`: `21353101`
- `silver_family_member_publications_rows`: `42692835`
- `silver_kind_code_normalization_rows`: `10097`
- `silver_family_wipo_fields_rows`: `21353101`
- `silver_assignee_harmonized_rows`: `20894233`
- `silver_family_ipc_cpc_canonical_rows`: `21353101`
- `silver_tiered_market_weighting_rows`: `8336`
- `silver_up_status_rows`: `21353101`
- `silver_family_jurisdiction_unrolled_rows`: `29502055`
- `silver_legal_status_event_ledger_rows`: `176704214`
- `silver_family_status_pt_rows`: `21353101`
- `silver_ep_register_core_rows`: `1090998`
- `silver_ep_register_agent_summary_rows`: `1006327`
- `silver_ep_register_current_opposition_rows`: `1090998`
- `silver_ep_register_up_status_rows`: `2`
- `silver_ep_register_proc_step_features_rows`: `1006327`
- `silver_ep_register_display_ledger_rows`: `1273328`

## silver-enrichment-kind-refresh | success

- Summary: Rebuilt the refreshed kind-code-dependent citation weighting layer; legal-weighted marts should then be refreshed through the incremental legal refresh stage.
- Started: 2026-04-02T16:46:08+00:00
- Finished: 2026-04-02T17:03:17+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_npl_publn.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_npl_backlinks.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_trend_tables.parquet
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
19. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
20. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-kind-refresh.json`

### Methods

1. Reused stable citation-edge, NPL, trend, and coverage support outputs from the latest Silver enrichment run.
2. Recomputed only the kind-code-dependent citation weighting layer and left legal-weighted marts to the dedicated incremental legal refresh stage.

### Calculations

1. Citing-stage multipliers in the enriched citation network are refreshed from the current Silver kind-code normalization table.
2. Use the follow-on silver-kind-legal-refresh stage to merge refreshed branch, field-contribution, and OECD rows for the affected families.

### Downstream Impacts

1. This refresh path is intended for iterative kind-code curation where the stable support outputs have not changed.
2. Use the full silver-enrichment stage if citation edges, trend tables, or coverage support outputs are absent or stale for other reasons.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `silver_enriched_citation_network_rows`: `19602108`
- `silver_family_citation_metrics_rows`: `21353101`

## normalize-kind-code | success

- Summary: Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.
- Started: 2026-04-02T19:12:23+00:00
- Finished: 2026-04-02T19:12:24+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_manual_overrides.csv

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_observed_pairs.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_review_queue.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/normalize-kind-code.json`

### Methods

1. Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.
2. Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.
3. Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.

### Calculations

1. Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.
2. EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.

### Downstream Impacts

1. This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.
2. Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue.

### Metrics

- `observed_pair_count`: `641`
- `seed_input_pair_count`: `10097`
- `auto_generated_pair_count`: `0`
- `review_queue_pair_count`: `224`
- `final_pair_count`: `10097`

## silver-enrichment-kind-legal-refresh | success

- Summary: Rebuilt only the legal-weighted Silver marts after kind-code curation using existing citation and trend support outputs.
- Started: 2026-04-02T19:15:31+00:00
- Finished: 2026-04-02T19:31:57+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_field_contributions.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-kind-legal-refresh.json`

### Methods

1. Reused refreshed citation metrics and existing trend support outputs.
2. Recomputed only family coverage, enforceability branches, field contributions, and OECD proxy outputs from the current kind-code normalization layer.

### Calculations

1. Branch stage and field contribution values are refreshed from the current Silver kind-code normalization table without rebuilding the semantic layer.


### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `kindcode_refresh_affected_family_rows`: `6077939`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `36096788`
- `silver_family_field_contributions_rows`: `23816698`
- `silver_family_oecd_quality_rows`: `21353101`

## silver-core | success

- Summary: Built core family-first Silver entities and bounded ownership/field normalizations.
- Started: 2026-04-02T19:12:38+00:00
- Finished: 2026-04-02T19:33:29+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_ipc_cpc_canonical.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_agent_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_up_status.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_proc_step_features.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_display_ledger.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-core.json`

### Methods

1. Collapsed in-scope applications to the canonical family core.
2. Normalized publication stage semantics from publication kinds.
3. Materialized owner harmonization and WIPO field assignment as reusable Silver entities.

### Calculations

1. Grant-stage classification is inferred from publication kind prefix `B` and modifier-stage from `C`.
2. Portfolio ownership remains bounded to the in-scope family universe only.

### Downstream Impacts

1. silver_family_core and its sibling Silver tables feed all Gold family, portfolio, Market Intelligence, forecast, and semantic marts.
2. The legal ledger, family status, market weighting, and Register tables created here become the canonical support layer for downstream point-in-time analytics and EP publication evidence views.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md


### Metrics

- `silver_family_core_rows`: `21353101`
- `silver_family_member_publications_rows`: `42692835`
- `silver_kind_code_normalization_rows`: `10097`
- `silver_family_wipo_fields_rows`: `21353101`
- `silver_assignee_harmonized_rows`: `20894233`
- `silver_family_ipc_cpc_canonical_rows`: `21353101`
- `silver_tiered_market_weighting_rows`: `8336`
- `silver_up_status_rows`: `21353101`
- `silver_family_jurisdiction_unrolled_rows`: `29502055`
- `silver_legal_status_event_ledger_rows`: `176704214`
- `silver_family_status_pt_rows`: `21353101`
- `silver_ep_register_core_rows`: `1090998`
- `silver_ep_register_agent_summary_rows`: `1006327`
- `silver_ep_register_current_opposition_rows`: `1090998`
- `silver_ep_register_up_status_rows`: `2`
- `silver_ep_register_proc_step_features_rows`: `1006327`
- `silver_ep_register_display_ledger_rows`: `1273328`

## silver-enrichment-kind-refresh | success

- Summary: Rebuilt the refreshed kind-code-dependent citation weighting layer; legal-weighted marts should then be refreshed through the incremental legal refresh stage.
- Started: 2026-04-02T19:15:14+00:00
- Finished: 2026-04-02T19:33:31+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_npl_publn.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_npl_backlinks.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_trend_tables.parquet
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
19. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
20. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-kind-refresh.json`

### Methods

1. Reused stable citation-edge, NPL, trend, and coverage support outputs from the latest Silver enrichment run.
2. Recomputed only the kind-code-dependent citation weighting layer and left legal-weighted marts to the dedicated incremental legal refresh stage.

### Calculations

1. Citing-stage multipliers in the enriched citation network are refreshed from the current Silver kind-code normalization table.
2. Use the follow-on silver-kind-legal-refresh stage to merge refreshed branch, field-contribution, and OECD rows for the affected families.

### Downstream Impacts

1. This refresh path is intended for iterative kind-code curation where the stable support outputs have not changed.
2. Use the full silver-enrichment stage if citation edges, trend tables, or coverage support outputs are absent or stale for other reasons.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `silver_enriched_citation_network_rows`: `19602108`
- `silver_family_citation_metrics_rows`: `21353101`

## normalize-kind-code | success

- Summary: Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.
- Started: 2026-04-02T20:26:09+00:00
- Finished: 2026-04-02T20:26:10+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_manual_overrides.csv

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_observed_pairs.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_review_queue.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/normalize-kind-code.json`

### Methods

1. Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.
2. Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.
3. Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.

### Calculations

1. Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.
2. EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.

### Downstream Impacts

1. This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.
2. Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue.

### Metrics

- `observed_pair_count`: `641`
- `seed_input_pair_count`: `10097`
- `auto_generated_pair_count`: `0`
- `review_queue_pair_count`: `216`
- `final_pair_count`: `10097`

## silver-enrichment-kind-legal-refresh | success

- Summary: Rebuilt only the legal-weighted Silver marts after kind-code curation using existing citation and trend support outputs.
- Started: 2026-04-02T20:27:36+00:00
- Finished: 2026-04-02T21:02:21+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_field_contributions.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-kind-legal-refresh.json`

### Methods

1. Reused refreshed citation metrics and existing trend support outputs.
2. Recomputed only family coverage, enforceability branches, field contributions, and OECD proxy outputs from the current kind-code normalization layer.

### Calculations

1. Branch stage and field contribution values are refreshed from the current Silver kind-code normalization table without rebuilding the semantic layer.


### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `kindcode_refresh_affected_family_rows`: `6077939`
- `silver_family_coverage_metrics_rows`: `21353101`
- `silver_family_enforceability_branches_rows`: `36088232`
- `silver_family_field_contributions_rows`: `23816698`
- `silver_family_oecd_quality_rows`: `21353101`

## silver-core | success

- Summary: Built core family-first Silver entities and bounded ownership/field normalizations.
- Started: 2026-04-02T20:26:17+00:00
- Finished: 2026-04-02T21:11:41+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_ipc_cpc_canonical.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_agent_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_up_status.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_proc_step_features.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_display_ledger.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-core.json`

### Methods

1. Collapsed in-scope applications to the canonical family core.
2. Normalized publication stage semantics from publication kinds.
3. Materialized owner harmonization and WIPO field assignment as reusable Silver entities.

### Calculations

1. Grant-stage classification is inferred from publication kind prefix `B` and modifier-stage from `C`.
2. Portfolio ownership remains bounded to the in-scope family universe only.

### Downstream Impacts

1. silver_family_core and its sibling Silver tables feed all Gold family, portfolio, Market Intelligence, forecast, and semantic marts.
2. The legal ledger, family status, market weighting, and Register tables created here become the canonical support layer for downstream point-in-time analytics and EP publication evidence views.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md


### Metrics

- `silver_family_core_rows`: `21353101`
- `silver_family_member_publications_rows`: `42692835`
- `silver_kind_code_normalization_rows`: `10097`
- `silver_family_wipo_fields_rows`: `21353101`
- `silver_assignee_harmonized_rows`: `20894233`
- `silver_family_ipc_cpc_canonical_rows`: `21353101`
- `silver_tiered_market_weighting_rows`: `8336`
- `silver_up_status_rows`: `21353101`
- `silver_family_jurisdiction_unrolled_rows`: `29502055`
- `silver_legal_status_event_ledger_rows`: `176704214`
- `silver_family_status_pt_rows`: `21353101`
- `silver_ep_register_core_rows`: `1090998`
- `silver_ep_register_agent_summary_rows`: `1006327`
- `silver_ep_register_current_opposition_rows`: `1090998`
- `silver_ep_register_up_status_rows`: `2`
- `silver_ep_register_proc_step_features_rows`: `1006327`
- `silver_ep_register_display_ledger_rows`: `1273328`

## silver-enrichment-kind-refresh | success

- Summary: Rebuilt the refreshed kind-code-dependent citation weighting layer; legal-weighted marts should then be refreshed through the incremental legal refresh stage.
- Started: 2026-04-02T20:29:53+00:00
- Finished: 2026-04-02T21:11:44+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_npl_publn.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_npl_backlinks.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_trend_tables.parquet
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
19. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
20. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-kind-refresh.json`

### Methods

1. Reused stable citation-edge, NPL, trend, and coverage support outputs from the latest Silver enrichment run.
2. Recomputed only the kind-code-dependent citation weighting layer and left legal-weighted marts to the dedicated incremental legal refresh stage.

### Calculations

1. Citing-stage multipliers in the enriched citation network are refreshed from the current Silver kind-code normalization table.
2. Use the follow-on silver-kind-legal-refresh stage to merge refreshed branch, field-contribution, and OECD rows for the affected families.

### Downstream Impacts

1. This refresh path is intended for iterative kind-code curation where the stable support outputs have not changed.
2. Use the full silver-enrichment stage if citation edges, trend tables, or coverage support outputs are absent or stale for other reasons.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `silver_enriched_citation_network_rows`: `19602108`
- `silver_family_citation_metrics_rows`: `21353101`

## normalize-kind-code | success

- Summary: Completed the pre-Bronze kind-code normalization seed from observed publication kinds, preserved manual rows, and emitted a review queue for remaining DOCDB curation work.
- Started: 2026-04-02T21:17:06+00:00
- Finished: 2026-04-02T21:17:06+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/patstat/tls211_pat_publn.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_manual_overrides.csv

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_observed_pairs.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/kind_code_normalization_review_queue.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/normalize-kind-code.json`

### Methods

1. Read the consolidated PATSTAT publication table and aggregated the observed `(publn_auth, publn_kind)` pairs inside the local bounded universe.
2. Preserved existing kind-code seed rows from `etl/data/raw/refs` and overlaid any explicit manual overrides when present.
3. Filled missing observed pairs with deterministic office-aware or prefix-aware rules so Bronze can ingest a complete normalization seed before Silver.

### Calculations

1. Observed pair counts and first/last seen dates are computed from the consolidated `tls211_pat_publn` table.
2. EP `B2` is elevated to `OPPOSITION_SURVIVOR` and EP `C0` to `UNITARY_GRANT`; remaining missing pairs use prefix-based defaults.

### Downstream Impacts

1. This stage replaces ad hoc Silver runtime fallback with an explicit raw reference seed that Bronze can ingest deterministically.
2. Any remaining `OTHER` or auto-generated rows are surfaced in a review queue before Bronze/Silver rather than being hidden in downstream logic.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. The normalized kind-code seed is operationally complete for Bronze, but some observed pairs still rely on auto-generated or `OTHER` mappings and remain in the review queue.

### Metrics

- `observed_pair_count`: `641`
- `seed_input_pair_count`: `10097`
- `auto_generated_pair_count`: `0`
- `review_queue_pair_count`: `214`
- `final_pair_count`: `10097`

## silver-core | success

- Summary: Built core family-first Silver entities and bounded ownership/field normalizations.
- Started: 2026-04-02T21:17:22+00:00
- Finished: 2026-04-02T21:25:01+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_family_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_ipc_cpc_canonical.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_core.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_agent_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_current_opposition.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_up_status.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_proc_step_features.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_ep_register_display_ledger.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-core.json`

### Methods

1. Collapsed in-scope applications to the canonical family core.
2. Normalized publication stage semantics from publication kinds.
3. Materialized owner harmonization and WIPO field assignment as reusable Silver entities.

### Calculations

1. Grant-stage classification is inferred from publication kind prefix `B` and modifier-stage from `C`.
2. Portfolio ownership remains bounded to the in-scope family universe only.

### Downstream Impacts

1. silver_family_core and its sibling Silver tables feed all Gold family, portfolio, Market Intelligence, forecast, and semantic marts.
2. The legal ledger, family status, market weighting, and Register tables created here become the canonical support layer for downstream point-in-time analytics and EP publication evidence views.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md


### Metrics

- `silver_family_core_rows`: `21353101`
- `silver_family_member_publications_rows`: `42692835`
- `silver_kind_code_normalization_rows`: `10097`
- `silver_family_wipo_fields_rows`: `21353101`
- `silver_assignee_harmonized_rows`: `20894233`
- `silver_family_ipc_cpc_canonical_rows`: `21353101`
- `silver_tiered_market_weighting_rows`: `8336`
- `silver_up_status_rows`: `21353101`
- `silver_family_jurisdiction_unrolled_rows`: `29502055`
- `silver_legal_status_event_ledger_rows`: `176704214`
- `silver_family_status_pt_rows`: `21353101`
- `silver_ep_register_core_rows`: `1090998`
- `silver_ep_register_agent_summary_rows`: `1006327`
- `silver_ep_register_current_opposition_rows`: `1090998`
- `silver_ep_register_up_status_rows`: `2`
- `silver_ep_register_proc_step_features_rows`: `1006327`
- `silver_ep_register_display_ledger_rows`: `1273328`

## silver-enrichment-kind-refresh | success

- Summary: Rebuilt the refreshed kind-code-dependent citation weighting layer; legal-weighted marts should then be refreshed through the incremental legal refresh stage.
- Started: 2026-04-02T21:19:27+00:00
- Finished: 2026-04-02T21:25:04+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_publn_seed.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_citation.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_pat_publn.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_patstat_npl_publn.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_edges.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_npl_backlinks.parquet
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_trend_tables.parquet
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
19. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
20. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-kind-refresh.json`

### Methods

1. Reused stable citation-edge, NPL, trend, and coverage support outputs from the latest Silver enrichment run.
2. Recomputed only the kind-code-dependent citation weighting layer and left legal-weighted marts to the dedicated incremental legal refresh stage.

### Calculations

1. Citing-stage multipliers in the enriched citation network are refreshed from the current Silver kind-code normalization table.
2. Use the follow-on silver-kind-legal-refresh stage to merge refreshed branch, field-contribution, and OECD rows for the affected families.

### Downstream Impacts

1. This refresh path is intended for iterative kind-code curation where the stable support outputs have not changed.
2. Use the full silver-enrichment stage if citation edges, trend tables, or coverage support outputs are absent or stale for other reasons.

### Governing Docs

1. docs/new-feature-ideas/kind-code-normalization-and-tiered-market-weighting-build-guide.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `silver_enriched_citation_network_rows`: `19602108`
- `silver_family_citation_metrics_rows`: `21353101`

## build-oecd-indicator-seed | success

- Summary: Built a family-first OECD indicator seed in wide family-level raw form from existing Silver citation, field, and family layers without rerunning Bronze.
- Started: 2026-04-03T06:07:53+00:00
- Finished: 2026-04-03T06:19:40+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_npl_backlinks.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_seed.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/build-oecd-indicator-seed.json`

### Methods

1. Used family-first collapse and deduplicated family-to-family citation pools rather than patent-level averaging.
2. Anchored OECD cohort normalization on `family_priority_year x primary_wipo_field` and forward-citation windows on `family_earliest_publication_date`.
3. Materialized a scalable wide family-level raw indicator seed; normalized cohort-stat projection is deferred until a downstream consumer requires it.

### Calculations

1. Computed `fwd_cits5`, `fwd_cits7`, `generality`, `originality`, `radicalness`, `bwd_cits`, `npl_cits`, and `science_grounding` at family grain.
2. Preserved raw values and truncation flags per indicator in the wide seed.
3. Marked fixed-window forward-citation rows as truncation-sensitive when the family publication anchor is too recent for a complete observation window.

### Downstream Impacts

1. The rich seed can later feed Bronze or direct Silver/Gold benchmark overlays without recomputing the citation pools.
2. Recent-cohort forward-window indicators remain usable but are explicitly marked as truncation-sensitive.

### Governing Docs

1. docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md
2. docs/new-feature-ideas/oecd-indicator-seed-build-spec.md
3. docs/oecd-patent-quality/oecd-patent-quality-definitions-and-feature-mapping.md


### Metrics

- `oecd_indicator_seed_rows`: `21353101`
- `oecd_indicator_seed_indicator_count`: `8`
- `oecd_indicator_seed_family_count`: `21353101`

## build-oecd-indicator-cohort-stats | success

- Summary: Built the OECD cohort-stat companion from the wide raw family-level OECD seed.
- Started: 2026-04-03T08:14:33+00:00
- Finished: 2026-04-03T08:14:55+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_cohort_stats.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/build-oecd-indicator-cohort-stats.json`

### Methods

1. Read the existing wide family-level OECD seed rather than recomputing the citation and field joins.
2. Aggregated cohort statistics by `family_priority_year x primary_wipo_field x indicator_name`.
3. Used approximate quantiles for cohort percentiles to keep local generation tractable on the bounded mega-cluster slice.

### Calculations

1. Computed cohort size, mean, standard deviation, and percentile checkpoints for the core OECD indicator set.
2. Kept the cohort companion separate from the raw seed so normalized benchmarking can be added later without changing the base family-level artifact.

### Downstream Impacts

1. This companion enables cohort-relative interpretation and future percentile/z-score derivation without rerunning the raw OECD seed build.
2. Portfolio hit-rate and top-decile OECD views can now be built from the current local artifact set.

### Governing Docs

1. docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md
2. docs/new-feature-ideas/oecd-indicator-seed-build-spec.md


### Metrics

- `oecd_indicator_cohort_rows`: `3968`

## build-oecd-indicator-cohort-stats | success

- Summary: Built the OECD cohort-stat companion from the wide raw family-level OECD seed.
- Started: 2026-04-03T08:17:39+00:00
- Finished: 2026-04-03T08:18:02+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_cohort_stats.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/build-oecd-indicator-cohort-stats.json`

### Methods

1. Read the existing wide family-level OECD seed rather than recomputing the citation and field joins.
2. Aggregated cohort statistics by `family_priority_year x primary_wipo_field x indicator_name`.
3. Used approximate quantiles for cohort percentiles to keep local generation tractable on the bounded mega-cluster slice.

### Calculations

1. Computed cohort size, mean, standard deviation, and percentile checkpoints for the core OECD indicator set.
2. Kept the cohort companion separate from the raw seed so normalized benchmarking can be added later without changing the base family-level artifact.

### Downstream Impacts

1. This companion enables cohort-relative interpretation and future percentile/z-score derivation without rerunning the raw OECD seed build.
2. Portfolio hit-rate and top-decile OECD views can now be built from the current local artifact set.

### Governing Docs

1. docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md
2. docs/new-feature-ideas/oecd-indicator-seed-build-spec.md


### Metrics

- `oecd_indicator_cohort_rows`: `3968`

## build-oecd-indicator-seed | success

- Summary: Built a family-first OECD indicator seed in wide family-level raw form from existing Silver citation, field, family-size, and grant-lag layers without rerunning Bronze.
- Started: 2026-04-03T08:32:40+00:00
- Finished: 2026-04-03T08:36:50+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_npl_backlinks.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_enriched_citation_network.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_appln_seed.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_seed.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/build-oecd-indicator-seed.json`

### Methods

1. Used family-first collapse and deduplicated family-to-family citation pools rather than patent-level averaging.
2. Anchored OECD cohort normalization on `family_priority_year x primary_wipo_field` and forward-citation windows on `family_earliest_publication_date`.
3. Computed family-level grant lag from the first granted member publication minus that member application filing date.
4. Kept the raw seed wide and family-grain so richer normalized or Bronze-facing projections can be materialized separately.

### Calculations

1. Computed `fwd_cits5`, `fwd_cits7`, `generality`, `originality`, `radicalness`, `bwd_cits`, `npl_cits`, `science_grounding`, `family_size`, and `grant_lag` at family grain.
2. Preserved raw values and truncation flags per indicator in the wide seed.
3. Marked fixed-window forward-citation rows as truncation-sensitive when the family publication anchor is too recent for a complete observation window.

### Downstream Impacts

1. The rich seed can feed Bronze or direct Silver/Gold benchmark overlays without recomputing the citation pools.
2. Recent-cohort forward-window indicators remain usable but are explicitly marked as truncation-sensitive.

### Governing Docs

1. docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md
2. docs/new-feature-ideas/oecd-indicator-seed-build-spec.md
3. docs/oecd-patent-quality/oecd-patent-quality-definitions-and-feature-mapping.md


### Metrics

- `oecd_indicator_seed_rows`: `21353101`
- `oecd_indicator_seed_indicator_count`: `10`
- `oecd_indicator_seed_family_count`: `21353101`

## build-oecd-indicator-cohort-stats | success

- Summary: Built the OECD cohort-stat companion from the wide raw family-level OECD seed.
- Started: 2026-04-03T08:37:10+00:00
- Finished: 2026-04-03T08:37:37+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_cohort_stats.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/build-oecd-indicator-cohort-stats.json`

### Methods

1. Read the existing wide family-level OECD seed rather than recomputing the citation and field joins.
2. Aggregated cohort statistics by `family_priority_year x primary_wipo_field x indicator_name`.
3. Used approximate quantiles for cohort percentiles to keep local generation tractable on the bounded mega-cluster slice.

### Calculations

1. Computed cohort size, mean, standard deviation, and percentile checkpoints for the OECD base indicator set including `family_size` and `grant_lag`.
2. Kept the cohort companion separate from the raw seed so normalized benchmarking can be added later without changing the base family-level artifact.

### Downstream Impacts

1. This companion enables cohort-relative interpretation and later percentile/z-score derivation without rerunning the raw OECD seed build.
2. Portfolio hit-rate and top-decile OECD views can now be built from the current local artifact set.

### Governing Docs

1. docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md
2. docs/new-feature-ideas/oecd-indicator-seed-build-spec.md


### Metrics

- `oecd_indicator_cohort_rows`: `4944`
- `oecd_indicator_cohort_indicator_count`: `10`

## build-oecd-indicator-longform | success

- Summary: Built the normalized long-form OECD indicator projection, including explicit family-first composite variants.
- Started: 2026-04-03T08:40:21+00:00
- Finished: 2026-04-03T08:51:37+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_cohort_stats.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_longform.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/build-oecd-indicator-longform.json`

### Methods

1. Expanded the wide family-level OECD seed into one row per `family x indicator` for downstream benchmarking and Bronze-compatible projections.
2. Computed exact within-cohort percentile ranks and z-scores by `family_priority_year x primary_wipo_field x indicator_name`.
3. Built `quality_index_4` and `quality_index_6` as explicit family-first composite variants with the claims component omitted and labeled in-schema.

### Calculations

1. Percentile rank is the canonical exposed normalized value; z-score is preserved for analytical use.
2. Grant-lag normalization is inverted so faster grants receive higher normalized scores.
3. Composite rows are built from normalized components only and carry explicit component policy metadata.

### Downstream Impacts

1. This artifact can feed Bronze/Silver OECD overlays and direct portfolio benchmarking without recomputing cohort windows.
2. The long-form shape supports explainable indicator drilldowns and future Bronze-compatible ingestion.

### Governing Docs

1. docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md
2. docs/new-feature-ideas/oecd-indicator-seed-build-spec.md


### Metrics

- `oecd_indicator_longform_rows`: `240090134`
- `oecd_indicator_longform_indicator_count`: `12`

## silver-oecd-refresh | success

- Summary: Rebuilt only the Silver OECD family mart from the normalized OECD long-form artifact and existing legal/citation support tables.
- Started: 2026-04-03T08:58:57+00:00
- Finished: 2026-04-03T09:04:58+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-oecd-refresh.json`

### Methods

1. Preferred the normalized OECD long-form projection when present and fell back to the legacy proxy formula only if the richer artifact was unavailable.
2. Reused existing Silver coverage, citation, and enforceability outputs rather than rerunning the full legal refresh.

### Calculations

1. Pivoted the OECD long-form indicators back to one row per family and preserved the legacy proxy columns for compatibility.
2. Exposed richer raw and percentile OECD fields alongside `oecd_quality_percentile` and `oecd_quality_proxy_score`.

### Downstream Impacts

1. Gold, ML, and portfolio quality overlays can now consume richer OECD-style family signals without a full Silver rerun.

### Governing Docs

1. docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md
2. docs/new-feature-ideas/oecd-indicator-seed-build-spec.md


### Metrics

- `silver_family_oecd_quality_rows`: `21353101`

## build-oecd-indicator-bronze-projection | success

- Summary: Projected the richer OECD long-form artifact into the Bronze-facing reference contract and landed the typed Bronze parquet directly.
- Started: 2026-04-03T09:18:07+00:00
- Finished: 2026-04-03T09:22:19+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw/refs/oecd_indicator_longform.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/raw-bounded/refs/oecd_quality_indicator_seed.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/bronze/bronze_ext_oecd_indicator_seed.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/build-oecd-indicator-bronze-projection.json`

### Methods

1. Read the normalized OECD long-form artifact rather than recomputing family metrics again.
2. Used percentile rank as the canonical `indicator_value` for the Bronze-facing contract while preserving raw and z-score companions.
3. Wrote both the bounded reference source file and the Bronze parquet directly so future Bronze reruns have a stable OECD input.

### Calculations

1. Projected one row per `family x indicator` with normalized value, raw value, z-score, cohort size, and component metadata.

### Downstream Impacts

1. This closes the Bronze contract gap for the OECD indicator seed without disturbing the richer raw family-level seed artifacts.

### Governing Docs

1. docs/new-feature-ideas/oecd-indicator-seed-build-spec.md
2. docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md


### Metrics

- `oecd_indicator_bronze_projection_rows`: `240090134`

## silver-enrichment-legal-status-refresh | success

- Summary: Rebuilt coverage and incrementally refreshed legal-weighted Silver marts for families affected by dated lapse/expiry events after legal-ledger date repair.
- Started: 2026-04-03T17:14:03+00:00
- Finished: 2026-04-03T17:36:54+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_field_contributions.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-legal-status-refresh.json`

### Methods

1. Rebuilt family coverage metrics from the repaired current family-status snapshot.
2. Merged refreshed enforceability, field-contribution, and OECD rows only for families touched by dated lapse/expiry events.

### Calculations

1. Affected-family slice is derived from current Silver legal-ledger rows with dated lapse/expiry events on or before the snapshot date.
2. This refresh path is intended to propagate legal-state fixes without rerunning the semantic or citation-edge layers.


### Governing Docs

1. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `silver_family_coverage_metrics_rows`: `21353101`
- `legal_status_refresh_affected_family_rows`: `1000157`
- `silver_family_enforceability_branches_rows`: `36096788`
- `silver_family_field_contributions_rows`: `23816698`
- `silver_family_oecd_quality_rows`: `21353101`

## silver-oecd-refresh | success

- Summary: Rebuilt only the Silver OECD family mart from the normalized OECD long-form artifact and existing legal/citation support tables.
- Started: 2026-04-03T17:21:11+00:00
- Finished: 2026-04-03T17:39:33+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-oecd-refresh.json`

### Methods

1. Preferred the normalized OECD long-form projection when present and fell back to the legacy proxy formula only if the richer artifact was unavailable.
2. Reused existing Silver coverage, citation, and enforceability outputs rather than rerunning the full legal refresh.

### Calculations

1. Pivoted the OECD long-form indicators back to one row per family and preserved the legacy proxy columns for compatibility.
2. Exposed richer raw and percentile OECD fields alongside `oecd_quality_percentile` and `oecd_quality_proxy_score`.

### Downstream Impacts

1. Gold, ML, and portfolio quality overlays can now consume richer OECD-style family signals without a full Silver rerun.

### Governing Docs

1. docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md
2. docs/new-feature-ideas/oecd-indicator-seed-build-spec.md


### Metrics

- `silver_family_oecd_quality_rows`: `21353101`

## silver-enrichment-legal-status-refresh | success

- Summary: Rebuilt coverage and incrementally refreshed legal-weighted Silver marts for families affected by dated lapse/expiry events after legal-ledger date repair.
- Started: 2026-04-03T18:10:22+00:00
- Finished: 2026-04-03T18:44:27+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_core.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_wipo_fields.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_tiered_market_weighting.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_up_status.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_member_publications.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_kind_code_normalization.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_field_contributions.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-enrichment-legal-status-refresh.json`

### Methods

1. Rebuilt family coverage metrics from the repaired current family-status snapshot.
2. Merged refreshed enforceability, field-contribution, and OECD rows only for families touched by dated lapse/expiry events.

### Calculations

1. Affected-family slice is derived from current Silver legal-ledger rows with dated lapse/expiry events on or before the snapshot date.
2. This refresh path is intended to propagate legal-state fixes without rerunning the semantic or citation-edge layers.


### Governing Docs

1. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `silver_family_coverage_metrics_rows`: `21353101`
- `legal_status_refresh_affected_family_rows`: `1000157`
- `silver_family_enforceability_branches_rows`: `36096788`
- `silver_family_field_contributions_rows`: `23816698`
- `silver_family_oecd_quality_rows`: `21353101`

## silver-history-refresh | success

- Summary: Rebuilt Silver legal-history sidecars in family buckets from the replayable legal ledger.
- Started: 2026-04-03T19:29:28+00:00
- Finished: 2026-04-03T19:35:41+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-history-refresh.json`

### Methods

1. Partitioned families into deterministic buckets and replayed yearly branch state per bucket.
2. Derived dense yearly family history from compact branch-state deltas rather than one monolithic all-family query.

### Calculations

1. Branch history remains change-point based plus current year.
2. Family history is expanded yearly from the earliest observed branch-history year to the build snapshot year.


### Governing Docs

1. docs/new-feature-ideas/blocking-power-lifecycle-and-point-in-time-scoring-requirements.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `silver_branch_status_history_rows`: `76203840`
- `silver_family_status_history_rows`: `240834180`
- `history_refresh_bucket_count`: `16`

## silver-history-refresh | success

- Summary: Rebuilt Silver legal-history sidecars in family buckets from the replayable legal ledger.
- Started: 2026-04-03T19:41:14+00:00
- Finished: 2026-04-03T19:47:26+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-history-refresh.json`

### Methods

1. Partitioned families into deterministic buckets and replayed yearly branch state per bucket.
2. Derived dense yearly family history from compact branch-state deltas rather than one monolithic all-family query.

### Calculations

1. Branch history remains change-point based plus current year.
2. Family history is expanded yearly from the earliest observed branch-history year to the build snapshot year.


### Governing Docs

1. docs/new-feature-ideas/blocking-power-lifecycle-and-point-in-time-scoring-requirements.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `silver_branch_status_history_rows`: `76203835`
- `silver_family_status_history_rows`: `240834180`
- `history_refresh_bucket_count`: `16`

## silver-history-refresh | success

- Summary: Rebuilt Silver legal-history sidecars in family buckets from the replayable legal ledger.
- Started: 2026-04-03T19:49:33+00:00
- Finished: 2026-04-03T19:55:46+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-history-refresh.json`

### Methods

1. Partitioned families into deterministic buckets and replayed yearly branch state per bucket.
2. Derived dense yearly family history from compact branch-state deltas rather than one monolithic all-family query.

### Calculations

1. Branch history remains change-point based plus current year.
2. Family history is expanded yearly from the earliest observed branch-history year to the build snapshot year, with current-year rows anchored to silver_family_status_pt.


### Governing Docs

1. docs/new-feature-ideas/blocking-power-lifecycle-and-point-in-time-scoring-requirements.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `silver_branch_status_history_rows`: `76203835`
- `silver_family_status_history_rows`: `240834180`
- `history_refresh_bucket_count`: `16`

## silver-history-refresh | success

- Summary: Rebuilt Silver legal-history sidecars in family buckets from the replayable legal ledger.
- Started: 2026-04-03T20:10:53+00:00
- Finished: 2026-04-03T20:20:13+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_jurisdiction_unrolled.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_legal_status_event_ledger.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_branch_status_history_dense.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-history-refresh.json`

### Methods

1. Partitioned families into deterministic buckets and replayed yearly branch state per bucket.
2. Derived dense yearly branch and family history from compact branch-state deltas rather than one monolithic all-family query.

### Calculations

1. Branch history remains change-point based plus current year, with a separate dense branch-year expansion artifact.
2. Family history is expanded yearly from the earliest observed branch-history year to the build snapshot year, with current-year rows anchored to silver_family_status_pt.


### Governing Docs

1. docs/new-feature-ideas/blocking-power-lifecycle-and-point-in-time-scoring-requirements.md
2. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md


### Metrics

- `silver_branch_status_history_rows`: `76203835`
- `silver_branch_status_history_dense_rows`: `386481639`
- `silver_family_status_history_rows`: `240834180`
- `history_refresh_bucket_count`: `16`

## silver-owner-refresh | success

- Summary: Rebuilt Silver family-owner bridge and deterministic primary-owner table from the scoped owner seed.
- Started: 2026-04-03T20:43:34+00:00
- Finished: 2026-04-03T20:46:59+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_scope_owner_seed.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_assignee_harmonized.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-owner-refresh.json`

### Methods

1. Aggregated the scoped owner seed into one reusable row per family-owner combination.
2. Selected the primary family owner deterministically by scoped application coverage with stable lexical tie-breaks.

### Calculations

1. Owner harmonization uses UNKNOWN_OWNER only for blank or degenerate normalized names.
2. Primary-owner ranking prefers non-UNKNOWN_OWNER owners, then highest owner_scope_appln_count, then harmonized/display-name tie-breaks.


### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md


### Metrics

- `silver_family_owner_bridge_rows`: `27840126`
- `silver_assignee_harmonized_rows`: `20894233`

## gold | success

- Summary: Built Gold family, portfolio, Market Intelligence, attacker, history, and semantic-context marts from note-aligned Silver contracts.
- Started: 2026-04-03T21:56:57+00:00
- Finished: 2026-04-03T22:48:08+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_overview.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_segments.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_heritage_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_summary_rows`: `17633618`
- `gold_family_blocking_power_rows`: `17633618`
- `gold_family_blocking_power_timeseries_rows`: `152148100`
- `gold_family_field_contributions_timeseries_rows`: `172227934`
- `gold_family_field_contributions_rows`: `172227934`
- `gold_portfolio_summary_rows`: `3034400`
- `gold_portfolio_field_timeseries_rows`: `5520241`
- `gold_portfolio_threat_matrix_rows`: `15269449`
- `gold_market_intelligence_overview_rows`: `1`
- `gold_market_intelligence_segments_rows`: `10`
- `gold_market_intelligence_timeseries_rows`: `504`
- `gold_semantic_match_context_rows`: `20295898`
- `gold_family_attacker_summary_rows`: `6334292`
- `gold_portfolio_forecast_summary_rows`: `3034400`
- `gold_family_heritage_summary_rows`: `21353101`
- `gold_portfolio_heritage_summary_rows`: `3852589`

## gold | success

- Summary: Built Gold family, portfolio, Market Intelligence, attacker, history, and semantic-context marts from note-aligned Silver contracts.
- Started: 2026-04-03T23:11:40+00:00
- Finished: 2026-04-03T23:55:19+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_overview.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_segments.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_heritage_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_summary_rows`: `17633618`
- `gold_family_blocking_power_rows`: `17633618`
- `gold_family_blocking_power_timeseries_rows`: `152145173`
- `gold_family_field_contributions_timeseries_rows`: `172223907`
- `gold_family_field_contributions_rows`: `172223907`
- `gold_portfolio_summary_rows`: `3034400`
- `gold_portfolio_field_timeseries_rows`: `5520241`
- `gold_portfolio_threat_matrix_rows`: `15269449`
- `gold_market_intelligence_overview_rows`: `1`
- `gold_market_intelligence_segments_rows`: `10`
- `gold_market_intelligence_timeseries_rows`: `504`
- `gold_semantic_match_context_rows`: `20295898`
- `gold_family_attacker_summary_rows`: `6334292`
- `gold_portfolio_forecast_summary_rows`: `3034400`
- `gold_family_heritage_summary_rows`: `21353101`
- `gold_portfolio_heritage_summary_rows`: `3852589`

## gold-family-metrics | success

- Summary: Built Gold family blocking, attacker, and heritage marts from note-aligned Silver legal and citation contracts.
- Started: 2026-04-04T06:02:23+00:00
- Finished: 2026-04-04T06:02:45+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-metrics.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_blocking_power_rows`: `17633618`
- `gold_family_attacker_summary_rows`: `6334292`
- `gold_family_heritage_summary_rows`: `21353101`

## gold-history-fields | success

- Summary: Built Gold field-contribution history marts from replay-aligned Silver branch and field history.
- Started: 2026-04-04T06:18:17+00:00
- Finished: 2026-04-04T06:22:39+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-history-fields.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_field_contributions_timeseries_rows`: `172223907`
- `gold_family_field_contributions_rows`: `172223907`

## gold-history-blocking | success

- Summary: Built Gold blocking-power history marts from replay-aligned Silver legal and citation history.
- Started: 2026-04-04T06:23:55+00:00
- Finished: 2026-04-04T06:29:47+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-history-blocking.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_blocking_power_timeseries_rows`: `152145173`

## gold-family-summary | success

- Summary: Built the Gold family summary mart from note-aligned Silver family, legal, owner, and OECD contracts.
- Started: 2026-04-04T08:30:32+00:00
- Finished: 2026-04-04T10:12:05+00:00



### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-summary.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md

### Warnings

1. Built partial family summary buckets (16/32); final gold_family_summary merge not written yet.

## gold-family-summary | success

- Summary: Built the Gold family summary mart from note-aligned Silver family, legal, owner, and OECD contracts.
- Started: 2026-04-04T08:30:32+00:00
- Finished: 2026-04-04T10:12:05+00:00



### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-summary.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md

### Warnings

1. Built partial family summary buckets (16/32); final gold_family_summary merge not written yet.

## gold-family-summary | success

- Summary: Built the Gold family summary mart from note-aligned Silver family, legal, owner, and OECD contracts.
- Started: 2026-04-04T10:12:18+00:00
- Finished: 2026-04-04T11:55:09+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-summary.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_summary_rows`: `17633618`

## gold-family-summary | success

- Summary: Built the Gold family summary mart from note-aligned Silver family, legal, owner, and OECD contracts.
- Started: 2026-04-04T10:12:18+00:00
- Finished: 2026-04-04T11:55:09+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-summary.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_summary_rows`: `17633618`

## gold-family-summary | success

- Summary: Built the Gold family summary mart from note-aligned Silver family, legal, owner, and OECD contracts.
- Started: 2026-04-04T17:47:46+00:00
- Finished: 2026-04-04T17:47:47+00:00



### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-summary.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md

### Warnings

1. Built partial family summary buckets (0/32); final gold_family_summary merge not written yet.

## gold-portfolio | success

- Summary: Built Gold portfolio marts from the family-owner bridge and Gold family/history contracts.
- Started: 2026-04-04T17:48:20+00:00
- Finished: 2026-04-04T18:04:09+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_heritage_summary.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_portfolio_field_timeseries_rows`: `5520241`
- `gold_portfolio_summary_rows`: `3034400`
- `gold_portfolio_threat_matrix_rows`: `15269449`
- `gold_portfolio_heritage_summary_rows`: `3852589`
- `gold_portfolio_forecast_summary_rows`: `3034400`

## gold-market-semantic | success

- Summary: Built Gold Market Intelligence and semantic-context marts from note-aligned Silver and Gold family outputs.
- Started: 2026-04-04T17:48:20+00:00
- Finished: 2026-04-04T18:04:09+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_segments.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_overview.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-semantic.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_market_intelligence_segments_rows`: `10`
- `gold_market_intelligence_timeseries_rows`: `504`
- `gold_market_intelligence_overview_rows`: `1`
- `gold_semantic_match_context_rows`: `20295898`

## ml-phase0-foundation | success

- Summary: Built a frozen training snapshot manifest, immediate family-forecast split registry, and semantic evaluation fixtures.
- Started: 2026-04-04T20:23:21+00:00
- Finished: 2026-04-04T20:23:48+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_fixture_registry.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_pair_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/training_snapshot_manifest.json

### Artifacts

- `training_snapshot_manifest`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/training_snapshot_manifest.json`
- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase0-foundation.json`

### Methods

1. Fingerprinted canonical Silver and Gold source marts with row counts, file size, and modified-time metadata for reproducibility.
2. Built a deterministic family-first split registry for the immediate family citation forecast scope using priority-year time bands.
3. Bootstrapped semantic evaluation fixtures and compare pairs from the live family semantic context while preserving legal-status expectations.

### Calculations

1. Family forecast split assignment uses main-window family rows from Gold family summary and places recent unlabeled cohorts into an explicit holdout bucket.
2. Semantic fixtures intentionally cover claim-backed, abstract-backed, dead, pending, and partially-lapsed families to test both retrieval and legal gating behavior.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-implementation-runbook-backlog.md
2. docs/new-feature-ideas/semantic-and-model-development/phases/phase-00-freeze-inputs-and-eval-fixtures.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md


### Metrics

- `ml_split_registry_rows`: `17633618`
- `semantic_eval_fixture_registry_rows`: `500`
- `semantic_eval_pair_registry_rows`: `97`
- `training_snapshot_source_table_count`: `9`

## ml-phase0-foundation | success

- Summary: Built a frozen training snapshot manifest, immediate family-forecast split registry, and semantic evaluation fixtures.
- Started: 2026-04-04T20:16:17+00:00
- Finished: 2026-04-04T20:24:37+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_fixture_registry.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_pair_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/training_snapshot_manifest.json

### Artifacts

- `training_snapshot_manifest`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/training_snapshot_manifest.json`
- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase0-foundation.json`

### Methods

1. Fingerprinted canonical Silver and Gold source marts with row counts, file size, and modified-time metadata for reproducibility.
2. Built a deterministic family-first split registry for the immediate family citation forecast scope using priority-year time bands.
3. Bootstrapped semantic evaluation fixtures and compare pairs from the live family semantic context while preserving legal-status expectations.

### Calculations

1. Family forecast split assignment uses main-window family rows from Gold family summary and places recent unlabeled cohorts into an explicit holdout bucket.
2. Semantic fixtures intentionally cover claim-backed, abstract-backed, dead, pending, and partially-lapsed families to test both retrieval and legal gating behavior.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-implementation-runbook-backlog.md
2. docs/new-feature-ideas/semantic-and-model-development/phases/phase-00-freeze-inputs-and-eval-fixtures.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md


### Metrics

- `ml_split_registry_rows`: `17633618`
- `semantic_eval_fixture_registry_rows`: `500`
- `semantic_eval_pair_registry_rows`: `97`
- `training_snapshot_source_table_count`: `9`

## ml-phase0-foundation | success

- Summary: Built a frozen training snapshot manifest, immediate family-forecast split registry, and semantic evaluation fixtures.
- Started: 2026-04-04T20:26:23+00:00
- Finished: 2026-04-04T20:27:11+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_text_representative.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_citation_metrics.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_coverage_metrics.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_enforceability_branches.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_fixture_registry.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/semantic_eval_pair_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/training_snapshot_manifest.json

### Artifacts

- `training_snapshot_manifest`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/training_snapshot_manifest.json`
- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase0-foundation.json`

### Methods

1. Fingerprinted canonical Silver and Gold source marts with row counts, file size, and modified-time metadata for reproducibility.
2. Built a deterministic family-first split registry for the immediate family citation forecast scope using priority-year time bands.
3. Bootstrapped semantic evaluation fixtures and compare pairs from the live family semantic context while preserving legal-status expectations.

### Calculations

1. Family forecast split assignment uses main-window family rows from Gold family summary and places recent unlabeled cohorts into an explicit holdout bucket.
2. Semantic fixtures intentionally cover claim-backed, abstract-backed, dead, pending, and partially-lapsed families to test both retrieval and legal gating behavior.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/enriched-semantic-and-model-implementation-runbook-backlog.md
2. docs/new-feature-ideas/semantic-and-model-development/phases/phase-00-freeze-inputs-and-eval-fixtures.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md


### Metrics

- `ml_split_registry_rows`: `17633618`
- `semantic_eval_fixture_registry_rows`: `600`
- `semantic_eval_pair_registry_rows`: `144`
- `training_snapshot_source_table_count`: `9`

## semantic | success

- Summary: Built chunked family-first semantic vector artifacts, exact-scan runtime manifests, and query fixtures for the Phase 01 semantic foundation.
- Started: 2026-04-04T20:38:11+00:00
- Finished: 2026-04-04T21:07:33+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_embedding_manifest.json
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic.json`

### Methods

1. Generated separate claim and abstract vector spaces from family representative text using a local lexical-hash embedding fallback.
2. Joined legal, chronology, OECD, and blocking context directly into the vector payloads so retrieval results can carry deterministic overlays.
3. Materialized a query registry from Phase 00 semantic fixtures to support repeatable retrieval evaluation and backend integration.

### Calculations

1. Claims and abstracts remain physically separated as vector_claims and vector_abstract spaces.
2. Vector packaging is limited to semantic candidates already marked in the bounded Silver semantic eligibility mart.
3. ANN remains unbuilt in this local phase; the runtime contract is exact-scan-ready and records this explicitly in the manifests.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md
2. docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md
3. docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md
4. docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md

### Warnings

1. No promoted external embedding model is configured locally; Phase 01 uses lexical_hash_embedding_v1 as the runtime-safe fallback.

### Metrics

- `vec_family_embeddings_claims_rows`: `3`
- `vec_family_embeddings_abstracts_rows`: `2004951`
- `vec_query_registry_rows`: `600`
- `claim_duplicate_family_rate`: `0.0`
- `abstract_duplicate_family_rate`: `0.0`
- `claim_legal_status_join_completeness`: `1.0`
- `abstract_legal_status_join_completeness`: `1.0`
- `claim_chronology_join_completeness`: `1.0`
- `abstract_chronology_join_completeness`: `5e-06`
- `claim_blocking_context_completeness`: `1.0`
- `abstract_blocking_context_completeness`: `5e-06`
- `query_anchor_claim_coverage`: `0.02`
- `query_anchor_abstract_coverage`: `1.0`

## semantic | success

- Summary: Built family-first semantic vector artifacts and query fixtures for the promoted dual semantic runtime.
- Started: 2026-04-04T22:07:58+00:00
- Finished: 2026-04-04T22:09:24+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_embedding_manifest.json
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic.json`

### Methods

1. Generated separate vector_claims and vector_abstract payloads from representative family text.
2. Used BGE-M3 for abstract embeddings and PatentSBERTa for claim embeddings when the promoted dual runtime is enabled, otherwise kept the lexical fallback for local regression use.
3. Materialized one semantic base parquet first, then encoded in bucketed slices to avoid repeated large joins.

### Calculations

1. Claims and abstracts remain physically separated and explicitly labeled by vector space.
2. Only semantic candidates already marked in the Silver eligibility mart are embedded.
3. Current runtime remains dense-only; ANN is still exact-scan compatible and recorded as such in manifests.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md
2. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md
3. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md
4. docs/new-feature-ideas/semantic-and-model-development/bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md

### Warnings

1. Semantic bucket row limiting was enabled for this run, so the outputs represent a bounded smoke sample, not a full corpus release.
2. Semantic run was intentionally bounded to a subset of buckets, so final merged vector artifacts were not rewritten.

### Metrics

- `semantic_base_rows`: `2004954`
- `encoded_claim_bucket_rows`: `0`
- `encoded_abstract_bucket_rows`: `256`
- `claim_bucket_files_present`: `16`
- `abstract_bucket_files_present`: `16`
- `vec_family_embeddings_claims_rows`: `0`
- `vec_family_embeddings_abstracts_rows`: `0`
- `vec_query_registry_rows`: `600`
- `claim_duplicate_family_rate`: `None`
- `abstract_duplicate_family_rate`: `None`
- `claim_legal_status_join_completeness`: `None`
- `abstract_legal_status_join_completeness`: `None`
- `claim_chronology_join_completeness`: `None`
- `abstract_chronology_join_completeness`: `None`
- `claim_blocking_context_completeness`: `None`
- `abstract_blocking_context_completeness`: `None`
- `query_anchor_claim_coverage`: `None`
- `query_anchor_abstract_coverage`: `None`

## semantic | success

- Summary: Built family-first semantic vector artifacts and query fixtures for the promoted dual semantic runtime.
- Started: 2026-04-04T22:15:28+00:00
- Finished: 2026-04-04T22:17:13+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_embedding_manifest.json
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic.json`

### Methods

1. Generated separate vector_claims and vector_abstract payloads from representative family text.
2. Used BGE-M3 for abstract embeddings and PatentSBERTa for claim embeddings when the promoted dual runtime is enabled, otherwise kept the lexical fallback for local regression use.
3. Materialized one semantic base parquet first, then encoded in bucketed slices to avoid repeated large joins.

### Calculations

1. Claims and abstracts remain physically separated and explicitly labeled by vector space.
2. Only semantic candidates already marked in the Silver eligibility mart are embedded.
3. Current runtime remains dense-only; ANN is still exact-scan compatible and recorded as such in manifests.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md
2. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md
3. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md
4. docs/new-feature-ideas/semantic-and-model-development/bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md

### Warnings

1. Semantic bucket row limiting was enabled for this run, so the outputs represent a bounded smoke sample, not a full corpus release.
2. Semantic run was intentionally bounded to a subset of buckets, so final merged vector artifacts were not rewritten.

### Metrics

- `semantic_base_rows`: `2135310`
- `encoded_claim_bucket_rows`: `0`
- `encoded_abstract_bucket_rows`: `256`
- `claim_bucket_files_present`: `16`
- `abstract_bucket_files_present`: `16`
- `vec_family_embeddings_claims_rows`: `0`
- `vec_family_embeddings_abstracts_rows`: `0`
- `vec_query_registry_rows`: `600`
- `claim_duplicate_family_rate`: `None`
- `abstract_duplicate_family_rate`: `None`
- `claim_legal_status_join_completeness`: `None`
- `abstract_legal_status_join_completeness`: `None`
- `claim_chronology_join_completeness`: `None`
- `abstract_chronology_join_completeness`: `None`
- `claim_blocking_context_completeness`: `None`
- `abstract_blocking_context_completeness`: `None`
- `query_anchor_claim_coverage`: `None`
- `query_anchor_abstract_coverage`: `None`

## semantic | success

- Summary: Built family-first semantic vector artifacts and query fixtures for the promoted dual semantic runtime.
- Started: 2026-04-05T07:28:28+00:00
- Finished: 2026-04-05T07:30:14+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_embedding_manifest.json
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic.json`

### Methods

1. Generated separate vector_claims and vector_abstract payloads from representative family text.
2. Used BGE-M3 for abstract embeddings and PatentSBERTa for claim embeddings when the promoted dual runtime is enabled, otherwise kept the lexical fallback for local regression use.
3. Materialized one semantic base parquet first, then encoded in bucketed slices to avoid repeated large joins.

### Calculations

1. Claims and abstracts remain physically separated and explicitly labeled by vector space.
2. Only semantic candidates already marked in the Silver eligibility mart are embedded.
3. Current runtime remains dense-only; ANN is still exact-scan compatible and recorded as such in manifests.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md
2. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md
3. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md
4. docs/new-feature-ideas/semantic-and-model-development/bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md

### Warnings

1. Semantic bucket row limiting was enabled for this run, so the outputs represent a bounded smoke sample, not a full corpus release.
2. Semantic run was intentionally bounded to a subset of buckets, so final merged vector artifacts were not rewritten.

### Metrics

- `semantic_base_rows`: `2135310`
- `encoded_claim_bucket_rows`: `0`
- `encoded_abstract_bucket_rows`: `256`
- `claim_bucket_files_present`: `16`
- `abstract_bucket_files_present`: `16`
- `vec_family_embeddings_claims_rows`: `0`
- `vec_family_embeddings_abstracts_rows`: `0`
- `vec_query_registry_rows`: `600`
- `claim_duplicate_family_rate`: `None`
- `abstract_duplicate_family_rate`: `None`
- `claim_legal_status_join_completeness`: `None`
- `abstract_legal_status_join_completeness`: `None`
- `claim_chronology_join_completeness`: `None`
- `abstract_chronology_join_completeness`: `None`
- `claim_blocking_context_completeness`: `None`
- `abstract_blocking_context_completeness`: `None`
- `query_anchor_claim_coverage`: `None`
- `query_anchor_abstract_coverage`: `None`

## semantic | success

- Summary: Built family-first semantic vector artifacts and query fixtures for the promoted dual semantic runtime.
- Started: 2026-04-05T07:56:43+00:00
- Finished: 2026-04-05T07:56:59+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_embedding_manifest.json
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic.json`

### Methods

1. Generated separate vector_claims and vector_abstract payloads from representative family text.
2. Used BGE-M3 for abstract embeddings and PatentSBERTa for claim embeddings when the promoted dual runtime is enabled, otherwise kept the lexical fallback for local regression use.
3. Materialized one semantic base parquet first, then encoded in bucketed slices to avoid repeated large joins.

### Calculations

1. Claims and abstracts remain physically separated and explicitly labeled by vector space.
2. Only semantic candidates already marked in the Silver eligibility mart are embedded.
3. Current runtime remains dense-only; ANN is still exact-scan compatible and recorded as such in manifests.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md
2. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md
3. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md
4. docs/new-feature-ideas/semantic-and-model-development/bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md

### Warnings

1. Semantic run was intentionally bounded to a subset of buckets, so final merged vector artifacts were not rewritten.
2. Semantic metadata and query registry writes were skipped for this subset worker run.

### Metrics

- `claim_bucket_files_present`: `0`
- `abstract_bucket_files_present`: `0`
- `vec_family_embeddings_claims_rows`: `0`
- `vec_family_embeddings_abstracts_rows`: `0`
- `vec_query_registry_rows`: `0`
- `claim_duplicate_family_rate`: `None`
- `abstract_duplicate_family_rate`: `None`
- `claim_legal_status_join_completeness`: `None`
- `abstract_legal_status_join_completeness`: `None`
- `claim_chronology_join_completeness`: `None`
- `abstract_chronology_join_completeness`: `None`
- `claim_blocking_context_completeness`: `None`
- `abstract_blocking_context_completeness`: `None`
- `query_anchor_claim_coverage`: `None`
- `query_anchor_abstract_coverage`: `None`

## semantic | success

- Summary: Built family-first semantic vector artifacts and query fixtures for the promoted dual semantic runtime.
- Started: 2026-04-05T11:07:21+00:00
- Finished: 2026-04-05T11:09:55+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_embedding_manifest.json
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic.json`

### Methods

1. Generated separate vector_claims and vector_abstract payloads from representative family text.
2. Used BGE-M3 for abstract embeddings and PatentSBERTa for claim embeddings when the promoted dual runtime is enabled, otherwise kept the lexical fallback for local regression use.
3. Materialized one semantic base parquet first, then encoded in bucketed slices to avoid repeated large joins.

### Calculations

1. Claims and abstracts remain physically separated and explicitly labeled by vector space.
2. Only semantic candidates already marked in the Silver eligibility mart are embedded.
3. Current runtime remains dense-only; ANN is still exact-scan compatible and recorded as such in manifests.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md
2. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md
3. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md
4. docs/new-feature-ideas/semantic-and-model-development/bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md

### Warnings

1. Semantic bucket row limiting was enabled for this run, so the outputs represent a bounded smoke sample, not a full corpus release.
2. Semantic run was intentionally bounded to a subset of buckets, so final merged vector artifacts were not rewritten.
3. Semantic metadata and query registry writes were skipped for this subset worker run.

### Metrics

- `embedding_device`: `mps`
- `encoded_claim_bucket_rows`: `0`
- `encoded_abstract_bucket_rows`: `2048`
- `claim_bucket_files_present`: `1`
- `abstract_bucket_files_present`: `1`
- `vec_family_embeddings_claims_rows`: `0`
- `vec_family_embeddings_abstracts_rows`: `0`
- `vec_query_registry_rows`: `0`
- `claim_duplicate_family_rate`: `None`
- `abstract_duplicate_family_rate`: `None`
- `claim_legal_status_join_completeness`: `None`
- `abstract_legal_status_join_completeness`: `None`
- `claim_chronology_join_completeness`: `None`
- `abstract_chronology_join_completeness`: `None`
- `claim_blocking_context_completeness`: `None`
- `abstract_blocking_context_completeness`: `None`
- `query_anchor_claim_coverage`: `None`
- `query_anchor_abstract_coverage`: `None`

## semantic | success

- Summary: Built family-first semantic vector artifacts and query fixtures for the promoted dual semantic runtime.
- Started: 2026-04-05T11:20:57+00:00
- Finished: 2026-04-05T11:22:56+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_embedding_manifest.json
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic.json`

### Methods

1. Generated separate vector_claims and vector_abstract payloads from representative family text.
2. Used BGE-M3 for abstract embeddings and PatentSBERTa for claim embeddings when the promoted dual runtime is enabled, otherwise kept the lexical fallback for local regression use.
3. Materialized one semantic base parquet first, then encoded in bucketed slices to avoid repeated large joins.

### Calculations

1. Claims and abstracts remain physically separated and explicitly labeled by vector space.
2. Only semantic candidates already marked in the Silver eligibility mart are embedded.
3. Current runtime remains dense-only; ANN is still exact-scan compatible and recorded as such in manifests.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md
2. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md
3. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md
4. docs/new-feature-ideas/semantic-and-model-development/bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md

### Warnings

1. Semantic bucket row limiting was enabled for this run, so the outputs represent a bounded smoke sample, not a full corpus release.
2. Semantic run was intentionally bounded to a subset of buckets, so final merged vector artifacts were not rewritten.
3. Semantic metadata and query registry writes were skipped for this subset worker run.

### Metrics

- `embedding_device`: `mps`
- `encoded_claim_bucket_rows`: `2048`
- `encoded_abstract_bucket_rows`: `0`
- `claim_bucket_files_present`: `1`
- `abstract_bucket_files_present`: `1`
- `vec_family_embeddings_claims_rows`: `0`
- `vec_family_embeddings_abstracts_rows`: `0`
- `vec_query_registry_rows`: `0`
- `claim_duplicate_family_rate`: `None`
- `abstract_duplicate_family_rate`: `None`
- `claim_legal_status_join_completeness`: `None`
- `abstract_legal_status_join_completeness`: `None`
- `claim_chronology_join_completeness`: `None`
- `abstract_chronology_join_completeness`: `None`
- `claim_blocking_context_completeness`: `None`
- `abstract_blocking_context_completeness`: `None`
- `query_anchor_claim_coverage`: `None`
- `query_anchor_abstract_coverage`: `None`

## semantic | success

- Summary: Built family-first semantic vector artifacts and query fixtures for the promoted dual semantic runtime.
- Started: 2026-04-05T11:46:00+00:00
- Finished: 2026-04-05T11:47:55+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_embedding_manifest.json
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic.json`

### Methods

1. Generated separate vector_claims and vector_abstract payloads from representative family text.
2. Used BGE-M3 for abstract embeddings and PatentSBERTa for claim embeddings when the promoted dual runtime is enabled, otherwise kept the lexical fallback for local regression use.
3. Materialized one semantic base parquet first, then encoded in bucketed slices to avoid repeated large joins.

### Calculations

1. Claims and abstracts remain physically separated and explicitly labeled by vector space.
2. Only semantic candidates already marked in the Silver eligibility mart are embedded.
3. Current runtime remains dense-only; ANN is still exact-scan compatible and recorded as such in manifests.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md
2. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-model-selection-decision.md
3. docs/new-feature-ideas/semantic-and-model-development/semantic-embedding-candidate-shortlist-and-benchmark-plan.md
4. docs/new-feature-ideas/semantic-and-model-development/bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md

### Warnings

1. Semantic bucket row limiting was enabled for this run, so the outputs represent a bounded smoke sample, not a full corpus release.
2. Semantic run was intentionally bounded to a subset of buckets, so final merged vector artifacts were not rewritten.
3. Semantic metadata and query registry writes were skipped for this subset worker run.

### Metrics

- `embedding_device`: `mps`
- `encoded_claim_bucket_rows`: `2048`
- `encoded_abstract_bucket_rows`: `0`
- `claim_bucket_files_present`: `1`
- `abstract_bucket_files_present`: `1`
- `vec_family_embeddings_claims_rows`: `0`
- `vec_family_embeddings_abstracts_rows`: `0`
- `vec_query_registry_rows`: `0`
- `claim_duplicate_family_rate`: `None`
- `abstract_duplicate_family_rate`: `None`
- `claim_legal_status_join_completeness`: `None`
- `abstract_legal_status_join_completeness`: `None`
- `claim_chronology_join_completeness`: `None`
- `abstract_chronology_join_completeness`: `None`
- `claim_blocking_context_completeness`: `None`
- `abstract_blocking_context_completeness`: `None`
- `query_anchor_claim_coverage`: `None`
- `query_anchor_abstract_coverage`: `None`

## semantic-abstract-phase-00 | success

- Summary: Built abstracts semantic phase artifact 1/10.
- Started: 2026-04-05T15:33:40+00:00
- Finished: 2026-04-05T15:34:23+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/phases/abstracts/vec_family_embeddings_abstracts_phase_00_of_10.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic-abstract-phase-00.json`

### Methods

1. Materialized or reused the semantic base parquet, then encoded one deterministic phase partition.
2. Persisted resumable chunk checkpoints before merging the finished phase artifact.

### Calculations

1. Phase partitions are deterministic by docdb_family_id modulo phase_count.
2. Only rows with usable text for the requested vector space are encoded in the phase artifact.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md


### Metrics

- `embedding_device`: `mps`
- `phase_id`: `0`
- `phase_count`: `10`
- `phase_chunk_files_present`: `2`
- `encoded_rows`: `512`
- `merged_rows`: `512`
- `duplicate_family_rows`: `0`
- `duplicate_family_rate`: `0.0`
- `embedding_dim_min`: `1024`
- `embedding_dim_max`: `1024`

## semantic-abstract-phase-00 | success

- Summary: Built abstracts semantic phase artifact 1/10.
- Started: 2026-04-06T05:59:41+00:00
- Finished: 2026-04-06T06:00:19+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/phases/abstracts/vec_family_embeddings_abstracts_phase_00_of_10.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic-abstract-phase-00.json`

### Methods

1. Materialized or reused the semantic base parquet, then encoded one deterministic phase partition.
2. Persisted resumable chunk checkpoints before merging the finished phase artifact.

### Calculations

1. Phase partitions are deterministic by docdb_family_id modulo phase_count.
2. Only rows with usable text for the requested vector space are encoded in the phase artifact.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md


### Metrics

- `embedding_device`: `mps`
- `phase_id`: `0`
- `phase_count`: `10`
- `phase_chunk_files_present`: `169`
- `encoded_rows`: `0`
- `merged_rows`: `209884`
- `duplicate_family_rows`: `40960`
- `duplicate_family_rate`: `0.195155`
- `embedding_dim_min`: `1024`
- `embedding_dim_max`: `1024`

## semantic-claim-phase-00 | success

- Summary: Built claims semantic phase artifact 1/3.
- Started: 2026-04-06T06:15:55+00:00
- Finished: 2026-04-06T07:48:09+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/phases/claims/vec_family_embeddings_claims_phase_00_of_03.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic-claim-phase-00.json`

### Methods

1. Materialized or reused the semantic base parquet, then encoded one deterministic phase partition.
2. Persisted resumable chunk checkpoints before merging the finished phase artifact.

### Calculations

1. Phase partitions are deterministic by docdb_family_id modulo phase_count.
2. Only rows with usable text for the requested vector space are encoded in the phase artifact.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md


### Metrics

- `embedding_device`: `mps`
- `phase_id`: `0`
- `phase_count`: `3`
- `phase_chunk_files_present`: `133`
- `encoded_rows`: `135575`
- `merged_rows`: `135575`
- `duplicate_family_rows`: `0`
- `duplicate_family_rate`: `0.0`
- `embedding_dim_min`: `768`
- `embedding_dim_max`: `768`

## semantic-claim-phase-01 | success

- Summary: Built claims semantic phase artifact 2/3.
- Started: 2026-04-06T08:24:26+00:00
- Finished: 2026-04-06T10:01:03+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/phases/claims/vec_family_embeddings_claims_phase_01_of_03.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic-claim-phase-01.json`

### Methods

1. Materialized or reused the semantic base parquet, then encoded one deterministic phase partition.
2. Persisted resumable chunk checkpoints before merging the finished phase artifact.

### Calculations

1. Phase partitions are deterministic by docdb_family_id modulo phase_count.
2. Only rows with usable text for the requested vector space are encoded in the phase artifact.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md


### Metrics

- `embedding_device`: `mps`
- `phase_id`: `1`
- `phase_count`: `3`
- `phase_chunk_files_present`: `133`
- `encoded_rows`: `136121`
- `merged_rows`: `136121`
- `duplicate_family_rows`: `0`
- `duplicate_family_rate`: `0.0`
- `embedding_dim_min`: `768`
- `embedding_dim_max`: `768`

## semantic-claim-phase-02 | success

- Summary: Built claims semantic phase artifact 3/3.
- Started: 2026-04-06T10:20:58+00:00
- Finished: 2026-04-06T11:56:05+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/phases/claims/vec_family_embeddings_claims_phase_02_of_03.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic-claim-phase-02.json`

### Methods

1. Materialized or reused the semantic base parquet, then encoded one deterministic phase partition.
2. Persisted resumable chunk checkpoints before merging the finished phase artifact.

### Calculations

1. Phase partitions are deterministic by docdb_family_id modulo phase_count.
2. Only rows with usable text for the requested vector space are encoded in the phase artifact.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md


### Metrics

- `embedding_device`: `mps`
- `phase_id`: `2`
- `phase_count`: `3`
- `phase_chunk_files_present`: `132`
- `encoded_rows`: `134943`
- `merged_rows`: `134943`
- `duplicate_family_rows`: `0`
- `duplicate_family_rate`: `0.0`
- `embedding_dim_min`: `768`
- `embedding_dim_max`: `768`

## semantic-ann | success

- Summary: Built HNSW ANN snapshots for the promoted semantic payloads and audited exact-vs-ANN agreement.
- Started: 2026-04-06T12:18:16+00:00
- Finished: 2026-04-06T12:26:50+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_claims_hnsw.bin
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_claims_family_ids.npy
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_abstracts_hnsw.bin
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_abstracts_family_ids.npy
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_exact_vs_ann_audit.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic-ann.json`

### Methods

1. Loaded the promoted semantic payloads from the canonical vector parquet paths.
2. Built separate cosine HNSW snapshots for abstract and claim corpora.
3. Audited ANN recall against exact top-k search using the semantic query registry where anchor coverage exists.

### Calculations

1. Claims use a higher ef_construction default than abstracts to preserve legal/technical specificity during ANN approximation.
2. Abstract query audit is evaluated only on the subset of registry anchors present in the current partial MVP abstract corpus.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md


### Metrics

- `claim_payload_count`: `406639`
- `abstract_payload_count`: `168924`
- `claim_embedding_dim`: `768`
- `abstract_embedding_dim`: `1024`
- `claim_exact_vs_ann_recall_at_10`: `0.989`
- `abstract_exact_vs_ann_recall_at_10`: `1.0`
- `query_anchor_claim_coverage`: `1.0`
- `query_anchor_abstract_coverage`: `0.008`

## semantic-ann | success

- Summary: Built HNSW ANN snapshots for the promoted semantic payloads and audited exact-vs-ANN agreement.
- Started: 2026-04-06T12:25:26+00:00
- Finished: 2026-04-06T12:34:33+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_claims_hnsw.bin
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_claims_family_ids.npy
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_abstracts_hnsw.bin
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_abstracts_family_ids.npy
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_exact_vs_ann_audit.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic-ann.json`

### Methods

1. Loaded the promoted semantic payloads from the canonical vector parquet paths.
2. Built separate cosine HNSW snapshots for abstract and claim corpora.
3. Audited ANN recall against exact top-k search using the semantic query registry where anchor coverage exists.

### Calculations

1. Claims use a higher ef_construction default than abstracts to preserve legal/technical specificity during ANN approximation.
2. Abstract query audit is evaluated only on the subset of registry anchors present in the current partial MVP abstract corpus.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md


### Metrics

- `claim_payload_count`: `406639`
- `abstract_payload_count`: `168924`
- `claim_embedding_dim`: `768`
- `abstract_embedding_dim`: `1024`
- `claim_exact_vs_ann_recall_at_10`: `0.99375`
- `abstract_exact_vs_ann_recall_at_10`: `1.0`
- `query_anchor_claim_coverage`: `1.0`
- `query_anchor_abstract_coverage`: `0.008`

## semantic-ann | success

- Summary: Built HNSW ANN snapshots for the promoted semantic payloads and audited exact-vs-ANN agreement.
- Started: 2026-04-06T12:31:59+00:00
- Finished: 2026-04-06T12:41:57+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_claims.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_family_embeddings_abstracts.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_query_registry.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_claims_hnsw.bin
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_claims_family_ids.npy
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_abstracts_hnsw.bin
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/ann/vec_ann_abstracts_family_ids.npy
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_index_manifest.json
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors/vec_ann_exact_vs_ann_audit.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/semantic-ann.json`

### Methods

1. Loaded the promoted semantic payloads from the canonical vector parquet paths.
2. Built separate cosine HNSW snapshots for abstract and claim corpora.
3. Audited ANN recall against exact top-k search using the semantic query registry where anchor coverage exists.

### Calculations

1. Claims use a higher ef_construction default than abstracts to preserve legal/technical specificity during ANN approximation.
2. Abstract query audit is evaluated only on the subset of registry anchors present in the current partial MVP abstract corpus.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-01-semantic-runtime-foundation.md


### Metrics

- `claim_payload_count`: `406639`
- `abstract_payload_count`: `168924`
- `claim_embedding_dim`: `768`
- `abstract_embedding_dim`: `1024`
- `claim_exact_vs_ann_recall_at_10`: `0.989062`
- `abstract_exact_vs_ann_recall_at_10`: `1.0`
- `claim_corpus_sample_exact_vs_ann_recall_at_10`: `0.992188`
- `abstract_corpus_sample_exact_vs_ann_recall_at_10`: `0.994531`
- `query_anchor_claim_coverage`: `1.0`
- `query_anchor_abstract_coverage`: `0.008`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-06T21:18:16+00:00
- Finished: 2026-04-06T21:19:04+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md


### Metrics

- `ml_label_family_future_citations_rows`: `0`
- `ml_feature_family_future_citations_rows`: `17633618`
- `ml_split_registry_rows`: `17633618`
- `ml_experiment_registry_rows`: `6`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-06T21:30:31+00:00
- Finished: 2026-04-06T21:32:22+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md

### Warnings

1. Phase 03 labels were derived from `silver_enriched_citation_network` using `family_earliest_priority_date + 2 years` as `as_of_date`; current-state structural features remain provisional until explicit point-in-time feature snapshots are added.

### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `11772956`
- `ml_experiment_registry_rows`: `6`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.4433162364084222`
- `phase03_3y_interval_coverage_80pct`: `0.85146`
- `phase03_5y_spearman`: `0.5987730933684785`
- `phase03_5y_interval_coverage_80pct`: `0.0552`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-06T21:33:56+00:00
- Finished: 2026-04-06T21:35:41+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md

### Warnings

1. Phase 03 labels were derived from `silver_enriched_citation_network` using `family_earliest_priority_date + 2 years` as `as_of_date`; current-state structural features remain provisional until explicit point-in-time feature snapshots are added.

### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `11772956`
- `ml_experiment_registry_rows`: `6`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.4462442786110408`
- `phase03_3y_interval_coverage_80pct`: `0.8459`
- `phase03_5y_spearman`: `0.5930727725590689`
- `phase03_5y_interval_coverage_80pct`: `0.819695664656905`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## ml-phase03-family-forecast | failed

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-07T09:37:16+00:00
- Finished: 2026-04-07T09:37:33+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md

### Warnings

1. Phase 03 labels were derived from `silver_enriched_citation_network` using `family_earliest_priority_date + 2 years` as `as_of_date`; current-state structural features remain provisional until explicit point-in-time feature snapshots are added.
2. Promotion-safe Phase 03 requires `silver_family_feature_snapshot_pit.parquet` whenever labels are derived from citation events. Run `silver-pit` before `ml-phase03-family-forecast`, or explicitly enable `execution.phase03_allow_current_state_fallback=true` for exploratory candidate runs only.

### Metrics

- `ml_label_family_future_citations_rows`: `11772956`

## silver-pit | success

- Summary: Built silver_family_feature_snapshot_pit.parquet with point-in-time safe features for each in-scope family at as_of_date = priority_date + 2 years.
- Started: 2026-04-07T09:53:07+00:00
- Finished: 2026-04-07T09:53:27+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-pit.json`

### Methods

1. Legal state (composite_status, active_jurisdiction_count, active_grant_branch_count, lapsed_jurisdiction_count) derived from silver_family_status_history at the nearest snapshot_year <= as_of_year.
2. Pre-as_of citation metrics (forward_citations_clean, weighted, unique_citing_family_count, citing_assignee_diversity, attacker_density_score) derived from silver_enriched_citation_network filtering citation_date <= as_of_date.
3. Blocking power (family_blocking_power_score_asof, family_enforceability_score_asof) derived from gold_family_blocking_power_timeseries at the nearest snapshot before as_of_year.
4. Primary field contribution derived from gold_family_field_contributions_timeseries at as_of_year.
5. family_size_docdb_asof and family_tech_breadth_wipo_count_asof are structural approximations from current-state tables (do not backproject these for historical UI views).

### Calculations

1. as_of_date = CAST(family_earliest_priority_date AS DATE) + INTERVAL '2 years'.
2. data_completeness_pct_asof is the fraction of 10 tracked PIT columns that are non-null before COALESCE defaults are applied.

### Downstream Impacts

1. ml-phase03-family-forecast: replaces current-state leakage features with PIT equivalents when this table is present.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md


### Metrics

- `silver_family_feature_snapshot_pit_rows`: `17633618`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-07T09:53:48+00:00
- Finished: 2026-04-07T09:55:28+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.
4. Applied point-in-time feature enrichment from `silver_family_feature_snapshot_pit`; replaced leakage-sensitive citation counts, network externalities, and legal-state columns with pre-as_of_date equivalents; recomputed data_completeness_pct from enriched values.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md

### Warnings

1. Phase 03 labels were derived from `silver_enriched_citation_network` using `family_earliest_priority_date + 2 years` as `as_of_date`; current-state structural features remain provisional until explicit point-in-time feature snapshots are added.

### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `11772956`
- `ml_experiment_registry_rows`: `6`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.46310957963212346`
- `phase03_3y_interval_coverage_80pct`: `0.84194`
- `phase03_5y_spearman`: `0.6188226919447776`
- `phase03_5y_interval_coverage_80pct`: `0.7780429594272077`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## silver-pit | success

- Summary: Built silver_family_feature_snapshot_pit.parquet with point-in-time safe features for each in-scope family at as_of_date = priority_date + 2 years.
- Started: 2026-04-07T10:16:28+00:00
- Finished: 2026-04-07T10:18:24+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_audit.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-pit.json`

### Methods

1. Legal state (composite_status, active_jurisdiction_count, active_grant_branch_count, lapsed_jurisdiction_count) derived from silver_family_status_history at the nearest snapshot_year <= as_of_year.
2. Pre-as_of citation metrics (forward_citations_clean, weighted, unique_citing_family_count, citing_assignee_diversity, attacker_density_score) derived from silver_enriched_citation_network filtering citation_date <= as_of_date.
3. Blocking power (family_blocking_power_score_asof, family_enforceability_score_asof) derived from gold_family_blocking_power_timeseries at the nearest snapshot before as_of_year.
4. Primary field contribution and WIPO breadth derived from gold_family_field_contributions_timeseries at the nearest snapshot_year <= as_of_year.
5. family_size_docdb_asof derived from distinct appln_id values in silver_family_member_publications with publn_date <= as_of_date.
6. family_jurisdiction_count_asof derived from silver_branch_status_history_dense at the nearest snapshot_year <= as_of_year.
7. family_coverage_stability_score_asof = active_jurisdiction_count_asof / family_jurisdiction_count_asof.
8. A persisted JSON audit is written beside the PIT parquet to validate anchor-date correctness, uniqueness, and basic value sanity.

### Calculations

1. as_of_date = CAST(family_earliest_priority_date AS DATE) + INTERVAL '2 years'.
2. family_rcf_score_asof = pre_asof_forward_citations_weighted / cohort_average_pre_asof_forward_citations_weighted within the same as_of_year.
3. data_completeness_pct_asof is the fraction of 12 tracked PIT columns that are non-null before COALESCE defaults are applied.

### Downstream Impacts

1. ml-phase03-family-forecast: replaces current-state leakage features with PIT equivalents when this table is present.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md


### Metrics

- `silver_family_feature_snapshot_pit_rows`: `17633618`
- `silver_family_feature_snapshot_pit_future_anchor_rows`: `1193145`
- `silver_family_feature_snapshot_pit_duplicate_family_year_keys`: `0`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-07T10:18:31+00:00
- Finished: 2026-04-07T10:20:13+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.
4. Applied point-in-time feature enrichment from `silver_family_feature_snapshot_pit`; replaced leakage-sensitive citation counts, network externalities, and legal-state columns with pre-as_of_date equivalents; replaced family_rcf_score, family_size_docdb, and family_coverage_stability_score with PIT-safe variants; recomputed data_completeness_pct from enriched values.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md

### Warnings

1. Phase 03 labels were derived from `silver_enriched_citation_network` using `family_earliest_priority_date + 2 years` as `as_of_date`; current-state structural features remain provisional until explicit point-in-time feature snapshots are added.

### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `11772956`
- `ml_experiment_registry_rows`: `6`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.45392649324740886`
- `phase03_3y_interval_coverage_80pct`: `0.80602`
- `phase03_5y_spearman`: `0.6012240614528171`
- `phase03_5y_interval_coverage_80pct`: `0.8210081497132509`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-07T10:21:06+00:00
- Finished: 2026-04-07T10:22:42+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.
4. Applied point-in-time feature enrichment from `silver_family_feature_snapshot_pit`; replaced leakage-sensitive citation counts, network externalities, and legal-state columns with pre-as_of_date equivalents; replaced family_rcf_score, family_size_docdb, and family_coverage_stability_score with PIT-safe variants; recomputed data_completeness_pct from enriched values.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md


### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `11772956`
- `ml_experiment_registry_rows`: `6`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.44849503024302617`
- `phase03_3y_interval_coverage_80pct`: `0.80608`
- `phase03_5y_spearman`: `0.5881328163227821`
- `phase03_5y_interval_coverage_80pct`: `0.8245920745920746`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-07T10:53:47+00:00
- Finished: 2026-04-07T10:55:32+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.
4. Applied point-in-time feature enrichment from `silver_family_feature_snapshot_pit`; replaced leakage-sensitive citation counts, network externalities, and legal-state columns with pre-as_of_date equivalents; replaced family_rcf_score, family_size_docdb, and family_coverage_stability_score with PIT-safe variants; recomputed data_completeness_pct from enriched values.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md


### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `11772956`
- `ml_experiment_registry_rows`: `6`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.45807497752483095`
- `phase03_3y_interval_coverage_80pct`: `0.80632`
- `phase03_5y_spearman`: `0.5927538395867741`
- `phase03_5y_interval_coverage_80pct`: `0.8263297090802233`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-07T11:06:30+00:00
- Finished: 2026-04-07T11:08:10+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.
4. Applied point-in-time feature enrichment from `silver_family_feature_snapshot_pit`; replaced leakage-sensitive citation counts, network externalities, and legal-state columns with pre-as_of_date equivalents; replaced family_rcf_score, family_size_docdb, and family_coverage_stability_score with PIT-safe variants; recomputed data_completeness_pct from enriched values.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md


### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `11772956`
- `ml_experiment_registry_rows`: `6`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.4564041269335929`
- `phase03_3y_interval_coverage_80pct`: `0.81532`
- `phase03_5y_spearman`: `0.6100395999400557`
- `phase03_5y_interval_coverage_80pct`: `0.7872846108140226`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-07T11:17:53+00:00
- Finished: 2026-04-07T11:19:34+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.
4. Applied point-in-time feature enrichment from `silver_family_feature_snapshot_pit`; replaced leakage-sensitive citation counts, network externalities, and legal-state columns with pre-as_of_date equivalents; replaced family_rcf_score, family_size_docdb, and family_coverage_stability_score with PIT-safe variants; recomputed data_completeness_pct from enriched values.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md


### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `11772956`
- `ml_experiment_registry_rows`: `6`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.45400446467412797`
- `phase03_3y_interval_coverage_80pct`: `0.79314`
- `phase03_5y_spearman`: `0.614405119327523`
- `phase03_5y_interval_coverage_80pct`: `0.8010008831321754`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## gold-family-compare-pit | success

- Summary: Built the family compare PIT serving mart from the audited family PIT core and current summary metadata.
- Started: 2026-04-07T11:34:20+00:00
- Finished: 2026-04-07T11:34:35+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_compare_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-compare-pit.json`

### Methods

1. Used only observed point-in-time family rows for historical compare serving.
2. Kept current owner, field, and OECD metadata explicitly labeled as current-only side metadata.
3. Materialized one row per family and observed year with a latest-observed-year flag for compare and report flows.

### Calculations

1. Family active-jurisdiction share is recomputed from point-in-time jurisdiction counts.
2. Historical-safe metrics come from the PIT core rather than current-state summary marts.

### Downstream Impacts

1. This mart is the safe family-level source for historical compare, time-slice report sections, and year-aware family evidence payloads.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md
3. docs/next-phase-v2/38-patentiq-v2-report-generation-use-cases-and-contract.md


### Metrics

- `gold_family_compare_pit_rows`: `16440473`

## gold-portfolio-summary-pit | success

- Summary: Built the portfolio PIT summary mart by aggregating family compare PIT rows through the current owner bridge with explicit historical caveats.
- Started: 2026-04-07T11:37:26+00:00
- Finished: 2026-04-07T11:37:49+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio-summary-pit.json`

### Methods

1. Aggregated only historical-safe family PIT rows into year-keyed portfolio summaries.
2. Reused the current owner bridge as a historical membership approximation and labeled that caveat explicitly.
3. Focused the first release on legal, blocking, coverage, and concentration signals rather than forcing unsupported historical field-mix claims.

### Calculations

1. Portfolio top-family dependence is measured as the maximum family blocking share within each owner-year slice.
2. Portfolio active-family count is derived from point-in-time active-jurisdiction presence rather than current family status.

### Downstream Impacts

1. This mart is the first safe source for portfolio over-time comparison, historical report sections, and legal-attrition context before Phase 04 predictions arrive.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md
3. docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md


### Metrics

- `gold_portfolio_summary_pit_rows`: `5115232`

## silver-pit-dense | success

- Summary: Built silver_family_feature_snapshot_pit_dense.parquet with observed family-year PIT rows for historical compare, reports, and portfolio-over-time product behavior.
- Started: 2026-04-07T11:55:22+00:00
- Finished: 2026-04-07T12:29:38+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense_audit.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-pit-dense.json`

### Methods

1. Generated one observed PIT row per family and as_of_year from family_priority_year through snapshot_year.
2. For each year, legal, blocking, field, citation, and coverage metrics are taken from the latest history or event evidence available at or before that year-end.
3. The current snapshot year uses snapshot_date rather than synthetic year-end so current-year product views stay aligned with the actual ETL snapshot.
4. A persisted JSON audit is written beside the dense PIT parquet to validate uniqueness, year range, multi-year family coverage, and value sanity.

### Calculations

1. as_of_date = MAKE_DATE(as_of_year, 12, 31) except for the current snapshot year where as_of_date = snapshot_date.
2. family_rcf_score_asof is normalized within the same as_of_year and primary field cohort.
3. data_completeness_pct_asof is the fraction of 12 tracked PIT columns that are non-null before COALESCE defaults are applied.

### Downstream Impacts

1. gold-family-compare-pit: should use this dense PIT layer when present for current-vs-selected-year family comparisons.
2. Historical compare and report flows can now use family-year rows rather than one anchored checkpoint per family.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md
3. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md


### Metrics

- `silver_family_feature_snapshot_pit_dense_rows`: `164988135`
- `silver_family_feature_snapshot_pit_dense_duplicate_family_year_keys`: `0`
- `silver_family_feature_snapshot_pit_dense_families_with_multiple_year_rows`: `17633618`

## gold-family-compare-pit | success

- Summary: Built the family compare PIT serving mart from the audited family PIT core and current summary metadata.
- Started: 2026-04-07T12:30:07+00:00
- Finished: 2026-04-07T12:36:27+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_compare_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-compare-pit.json`

### Methods

1. Consumed the dense family-year PIT layer for multi-year historical compare behavior.
2. Used only observed point-in-time family rows for historical compare serving.
3. Kept current owner, field, and OECD metadata explicitly labeled as current-only side metadata.
4. Materialized one row per family and observed year with a latest-observed-year flag for compare and report flows.

### Calculations

1. Family active-jurisdiction share is recomputed from point-in-time jurisdiction counts.
2. Historical-safe metrics come from the PIT core rather than current-state summary marts.

### Downstream Impacts

1. This mart is the safe family-level source for historical compare, time-slice report sections, and year-aware family evidence payloads.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md
3. docs/next-phase-v2/38-patentiq-v2-report-generation-use-cases-and-contract.md


### Metrics

- `gold_family_compare_pit_rows`: `164988135`

## gold-portfolio-summary-pit | success

- Summary: Built the portfolio PIT summary mart by aggregating family compare PIT rows through the current owner bridge with explicit historical caveats.
- Started: 2026-04-07T12:43:07+00:00
- Finished: 2026-04-07T12:48:01+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio-summary-pit.json`

### Methods

1. Aggregated only historical-safe family PIT rows into year-keyed portfolio summaries.
2. Reused the current owner bridge as a historical membership approximation and labeled that caveat explicitly.
3. Focused the first release on legal, blocking, coverage, and concentration signals rather than forcing unsupported historical field-mix claims.

### Calculations

1. Portfolio top-family dependence is measured as the maximum family blocking share within each owner-year slice.
2. Portfolio active-family count is derived from point-in-time active-jurisdiction presence rather than current family status.

### Downstream Impacts

1. This mart is the first safe source for portfolio over-time comparison, historical report sections, and legal-attrition context before Phase 04 predictions arrive.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md
3. docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md


### Metrics

- `gold_portfolio_summary_pit_rows`: `36127659`

## gold-market-summary-pit | success

- Summary: Built the market PIT summary mart from year-safe market timeseries, dense family compare PIT, and current-owner caveated family membership.
- Started: 2026-04-07T13:08:19+00:00
- Finished: 2026-04-07T13:26:54+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-summary-pit.json`

### Methods

1. Started from the year-safe market-intelligence timeseries and retained one row per segment and year.
2. Joined dense family compare PIT with family field-contribution timeseries to derive blocking and active-family density by segment-year.
3. Used the current family owner from the family compare PIT as a historical owner proxy and labeled that caveat explicitly.

### Calculations

1. Segment growth index is computed from family-count change versus the prior year when prior-year count exists.
2. Segment blocking density is a weighted average of family blocking power using field base fractions as segment participation weights.
3. Segment field balance is the average family allocation share to the segment, higher when families are more concentrated in that field.

### Downstream Impacts

1. This mart is the safe historical source for Market Intelligence year-slice cards, league tables, and segment detail drawers.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_market_summary_pit_rows`: `504`

## gold-portfolio-compare-pit | success

- Summary: Built the portfolio compare PIT mart from dense portfolio PIT summaries and year-safe field-mix support where available.
- Started: 2026-04-07T13:33:27+00:00
- Finished: 2026-04-07T13:33:38+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_compare_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio-compare-pit.json`

### Methods

1. Started from the dense portfolio summary PIT so legal, blocking, and concentration metrics stay historical-safe.
2. Joined field-mix metrics only for years actually present in the portfolio field timeseries.
3. Kept historical owner truth and historical field-mix support explicitly caveated when source coverage is unavailable.

### Calculations

1. Portfolio legal durability index is measured as active-family share within the historical owner-year proxy slice.
2. Portfolio field breadth is the count of positive active-family fields in the supported field-timeseries year.
3. Portfolio field concentration is calculated as HHI over active-family field shares, with top-field share surfaced separately.

### Downstream Impacts

1. This mart is the compare-oriented source for portfolio year-slice views, radar overlays, and report compare tables.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md


### Metrics

- `gold_portfolio_compare_pit_rows`: `36127659`

## gold-market-leaderboard-pit | success

- Summary: Built the market leaderboard PIT mart for segment-year family and owner rankings with explicit historical owner caveats.
- Started: 2026-04-07T13:47:20+00:00
- Finished: 2026-04-07T14:00:59+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_leaderboard_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-leaderboard-pit.json`

### Methods

1. Derived family leaderboard rows from year-safe family field-contribution timeseries joined to dense family compare PIT.
2. Derived owner leaderboard rows by aggregating current-owner replay across in-segment family-year rows.
3. Ranked families and owners separately within each segment-year slice and capped each leaderboard to a compact top set.

### Calculations

1. Family leaderboard ranking uses family blocking power first, then weighted field participation as a tiebreaker.
2. Owner leaderboard share is measured against the segment active-family count from the market summary PIT.
3. Owner average blocking is computed over the current-owner replay family set inside the segment-year slice.

### Downstream Impacts

1. This mart supports selected-year segment leader tables and owner presence panels without requiring ad hoc ranking logic in the backend.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_market_leaderboard_pit_rows`: `0`

## gold-market-leaderboard-pit | success

- Summary: Built the market leaderboard PIT mart for segment-year family and owner rankings with explicit historical owner caveats.
- Started: 2026-04-07T14:00:48+00:00
- Finished: 2026-04-07T14:09:57+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_leaderboard_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-leaderboard-pit.json`

### Methods

1. Derived family leaderboard rows from year-safe family field-contribution timeseries joined to dense family compare PIT.
2. Derived owner leaderboard rows by aggregating current-owner replay across in-segment family-year rows.
3. Ranked families and owners separately within each segment-year slice and capped each leaderboard to a compact top set.

### Calculations

1. Family leaderboard ranking uses family blocking power first, then weighted field participation as a tiebreaker.
2. Owner leaderboard share is measured against the segment active-family count from the market summary PIT.
3. Owner average blocking is computed over the current-owner replay family set inside the segment-year slice.

### Downstream Impacts

1. This mart supports selected-year segment leader tables and owner presence panels without requiring ad hoc ranking logic in the backend.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_market_leaderboard_pit_rows`: `7600`

## gold-market-summary-pit | success

- Summary: Built the market PIT summary mart from year-safe market timeseries, dense family compare PIT, and current-owner caveated family membership.
- Started: 2026-04-07T14:14:42+00:00
- Finished: 2026-04-07T14:16:00+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-summary-pit.json`

### Methods

1. Started from the year-safe market-intelligence timeseries and retained one row per segment and year.
2. Joined dense family compare PIT with family field-contribution timeseries to derive blocking and active-family density by segment-year.
3. Used the current family owner from the family compare PIT as a historical owner proxy and labeled that caveat explicitly.

### Calculations

1. Segment growth index is computed from family-count change versus the prior year when prior-year count exists.
2. Segment blocking density is a weighted average of family blocking power using field base fractions as segment participation weights.
3. Segment field balance is the average family allocation share to the segment, higher when families are more concentrated in that field.

### Downstream Impacts

1. This mart is the safe historical source for Market Intelligence year-slice cards, league tables, and segment detail drawers.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_market_summary_pit_rows`: `504`

## ml-phase04-family-jurisdiction-lapse-risk | success

- Summary: Built Phase 04 branch-aware label, feature, and split artifacts with registry-preserving scaffold metadata.
- Started: 2026-04-07T14:34:50+00:00
- Finished: 2026-04-07T14:34:53+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_jurisdiction_lapse_risk.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_jurisdiction_lapse_risk.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_jurisdiction_lapse_risk.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase04-family-jurisdiction-lapse-risk.json`

### Methods

1. Derived family-jurisdiction lapse labels from dated lapse/expiry events after each yearly active-grant branch snapshot.
2. Joined dense branch history with dense family PIT metrics to keep first-pass Phase 04 features year-safe.
3. Assigned one grouped time split per family-jurisdiction trajectory using the latest fully observed 24m year.

### Calculations

1. 12m and 24m labels are only treated as observed when the horizon closes by the ETL snapshot date.
2. Branch-level timing features use the lag between as_of_date and last grant/lapse/expiry events.
3. Current-state-only legal enrichments are intentionally excluded from the initial promotion feature set.


### Governing Docs

1. docs/next-phase-v2/45-patentiq-v2-phase-04-family-jurisdiction-lapse-risk-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md


### Metrics

- `ml_label_family_jurisdiction_lapse_risk_rows`: `157525345`
- `ml_feature_family_jurisdiction_lapse_risk_rows`: `97347045`
- `ml_split_registry_rows`: `24970099`
- `ml_experiment_registry_rows`: `8`
- `ml_model_registry_rows`: `4`
- `ml_calibration_registry_rows`: `4`

## ml-phase04-family-jurisdiction-lapse-risk | success

- Summary: Built Phase 04 branch-aware label, feature, and split artifacts with registry-preserving scaffold metadata.
- Started: 2026-04-07T14:41:20+00:00
- Finished: 2026-04-07T14:41:23+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_jurisdiction_lapse_risk.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_jurisdiction_lapse_risk.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_jurisdiction_lapse_risk.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase04-family-jurisdiction-lapse-risk.json`

### Methods

1. Derived family-jurisdiction lapse labels from dated lapse/expiry events after each yearly active-grant branch snapshot.
2. Joined dense branch history with dense family PIT metrics to keep first-pass Phase 04 features year-safe.
3. Assigned one grouped time split per family-jurisdiction trajectory using the latest fully observed 24m year.

### Calculations

1. 12m and 24m labels are only treated as observed when the horizon closes by the ETL snapshot date.
2. Branch-level timing features use the lag between as_of_date and last grant/lapse/expiry events.
3. Current-state-only legal enrichments are intentionally excluded from the initial promotion feature set.


### Governing Docs

1. docs/next-phase-v2/45-patentiq-v2-phase-04-family-jurisdiction-lapse-risk-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md


### Metrics

- `ml_label_family_jurisdiction_lapse_risk_rows`: `151930838`
- `ml_feature_family_jurisdiction_lapse_risk_rows`: `97347045`
- `ml_split_registry_rows`: `24970099`
- `ml_experiment_registry_rows`: `8`
- `ml_model_registry_rows`: `4`
- `ml_calibration_registry_rows`: `4`

## ml-phase04-family-jurisdiction-lapse-risk | success

- Summary: Built Phase 04 branch-aware label, feature, and split artifacts with registry-preserving scaffold metadata.
- Started: 2026-04-07T14:48:27+00:00
- Finished: 2026-04-07T14:48:29+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_jurisdiction_lapse_risk.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_jurisdiction_lapse_risk.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_jurisdiction_lapse_risk.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase04-family-jurisdiction-lapse-risk.json`

### Methods

1. Derived family-jurisdiction lapse labels from dated lapse/expiry events after each yearly active-grant branch snapshot.
2. Joined dense branch history with dense family PIT metrics to keep first-pass Phase 04 features year-safe.
3. Assigned one grouped time split per family-jurisdiction trajectory using the latest fully observed 24m year.

### Calculations

1. 12m and 24m labels are only treated as observed when the horizon closes by the ETL snapshot date.
2. Branch-level timing features use the lag between as_of_date and last grant/lapse/expiry events.
3. Current-state-only legal enrichments are intentionally excluded from the initial promotion feature set.


### Governing Docs

1. docs/next-phase-v2/45-patentiq-v2-phase-04-family-jurisdiction-lapse-risk-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md


### Metrics

- `ml_label_family_jurisdiction_lapse_risk_rows`: `151930838`
- `ml_feature_family_jurisdiction_lapse_risk_rows`: `97347045`
- `ml_split_registry_rows`: `24970099`
- `ml_experiment_registry_rows`: `8`
- `ml_model_registry_rows`: `4`
- `ml_calibration_registry_rows`: `4`

## ml-phase04-family-jurisdiction-lapse-risk | success

- Summary: Built Phase 04 branch-aware label, feature, split, and baseline-training artifacts with registry-preserving metadata.
- Started: 2026-04-07T15:04:58+00:00
- Finished: 2026-04-07T15:05:01+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_jurisdiction_lapse_risk.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_jurisdiction_lapse_risk.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_jurisdiction_lapse_risk.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_12m_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_24m_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase04-family-jurisdiction-lapse-risk.json`

### Methods

1. Derived family-jurisdiction lapse labels from dated lapse/expiry events after each yearly active-grant branch snapshot.
2. Joined dense branch history with dense family PIT metrics to keep first-pass Phase 04 features year-safe.
3. Assigned one grouped time split per family-jurisdiction trajectory using the latest fully observed 24m year.
4. Trained sampled LightGBM classifier baselines and selected validation-best probability calibration per horizon.

### Calculations

1. 12m and 24m labels are only treated as observed when the horizon closes by the ETL snapshot date.
2. Branch-level timing features use the lag between as_of_date and last grant/lapse/expiry events.
3. Current-state-only legal enrichments are intentionally excluded from the initial promotion feature set.


### Governing Docs

1. docs/next-phase-v2/45-patentiq-v2-phase-04-family-jurisdiction-lapse-risk-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md


### Metrics

- `ml_label_family_jurisdiction_lapse_risk_rows`: `151930838`
- `ml_feature_family_jurisdiction_lapse_risk_rows`: `97347045`
- `ml_split_registry_rows`: `24970099`
- `ml_experiment_registry_rows`: `8`
- `ml_model_registry_rows`: `4`
- `ml_calibration_registry_rows`: `4`
- `phase04_12m_roc_auc`: `nan`
- `phase04_12m_pr_auc`: `nan`
- `phase04_12m_brier_score`: `0.0`
- `phase04_24m_roc_auc`: `nan`
- `phase04_24m_pr_auc`: `nan`
- `phase04_24m_brier_score`: `2.419313058216061e-10`

## ml-phase04-family-jurisdiction-lapse-risk | success

- Summary: Built Phase 04 branch-aware label, feature, split, and baseline-training artifacts with registry-preserving metadata.
- Started: 2026-04-07T15:15:50+00:00
- Finished: 2026-04-07T15:15:53+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_jurisdiction_lapse_risk.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_jurisdiction_lapse_risk.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_jurisdiction_lapse_risk.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_12m_model.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_24m_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase04-family-jurisdiction-lapse-risk.json`

### Methods

1. Derived family-jurisdiction lapse labels from dated lapse/expiry events after each yearly active-grant branch snapshot.
2. Joined dense branch history with dense family PIT metrics to keep first-pass Phase 04 features year-safe.
3. Assigned one grouped time split per family-jurisdiction trajectory using the latest fully observed 24m year.
4. Trained sampled LightGBM classifier baselines and selected validation-best probability calibration per horizon.

### Calculations

1. 12m and 24m labels are only treated as observed when the horizon closes by the ETL snapshot date.
2. Branch-level timing features use the lag between as_of_date and last grant/lapse/expiry events.
3. Current-state-only legal enrichments are intentionally excluded from the initial promotion feature set.


### Governing Docs

1. docs/next-phase-v2/45-patentiq-v2-phase-04-family-jurisdiction-lapse-risk-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md


### Metrics

- `ml_label_family_jurisdiction_lapse_risk_rows`: `151930838`
- `ml_feature_family_jurisdiction_lapse_risk_rows`: `97347045`
- `ml_split_registry_rows`: `24970099`
- `ml_experiment_registry_rows`: `8`
- `ml_model_registry_rows`: `4`
- `ml_calibration_registry_rows`: `4`
- `phase04_12m_roc_auc`: `0.9854587838811208`
- `phase04_12m_pr_auc`: `0.11962410366073237`
- `phase04_12m_brier_score`: `0.002569726569718946`
- `phase04_24m_roc_auc`: `0.9711444793067384`
- `phase04_24m_pr_auc`: `0.11645043511949263`
- `phase04_24m_brier_score`: `0.005286176439050758`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-07T17:58:57+00:00
- Finished: 2026-04-07T18:01:17+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_breakout_classifier.txt
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_breakout_tail_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_bundle.json
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_breakout_classifier.txt
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_breakout_tail_model.txt
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_bundle.json
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.
4. Applied point-in-time feature enrichment from `silver_family_feature_snapshot_pit`; replaced leakage-sensitive citation counts, network externalities, and legal-state columns with pre-as_of_date equivalents; replaced family_rcf_score, family_size_docdb, and family_coverage_stability_score with PIT-safe variants; recomputed data_completeness_pct from enriched values.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md


### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `11772956`
- `ml_experiment_registry_rows`: `8`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.4565249237970863`
- `phase03_3y_interval_coverage_80pct`: `0.79686`
- `phase03_5y_spearman`: `0.5967673087990223`
- `phase03_5y_interval_coverage_80pct`: `0.7959916242895603`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## ml-phase03-family-forecast | success

- Summary: Built deterministic Phase 03 family-future-citation label, feature, split, and registry scaffolding for family-first forecast training.
- Started: 2026-04-07T18:30:38+00:00
- Finished: 2026-04-07T18:39:48+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_future_citations.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_future_citations.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase03.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_future_citation_forecast.json
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_breakout_classifier.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_breakout_tail_model.txt
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_model.txt
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_3y_bundle.json
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_breakout_classifier.txt
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_breakout_tail_model.txt
16. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_model.txt
17. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_5y_bundle.json
18. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_future_citation_forecast_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase03-family-forecast.json`

### Methods

1. Materialized leakage-safe Phase 03 label and feature tables at `docdb_family_id` grain from current Silver and Gold marts.
2. Built a grouped time split registry aligned to family priority year and recent-cohort holdout rules.
3. Wrote placeholder experiment, model, and calibration registries so training can proceed under an explicit TDD contract rather than ad hoc scripts.
4. Applied point-in-time feature enrichment from `silver_family_feature_snapshot_pit`; replaced leakage-sensitive citation counts, network externalities, and legal-state columns with pre-as_of_date equivalents; replaced family_rcf_score, family_size_docdb, and family_coverage_stability_score with PIT-safe variants; recomputed data_completeness_pct from enriched values.

### Calculations

1. Future citation labels preserve raw and log1p targets for 3y and 5y horizons.
2. Feature completeness remains explicit via `data_completeness_pct` rather than collapsing all missing numeric values to zero.


### Governing Docs

1. docs/new-feature-ideas/semantic-and-model-development/phases/phase-03-family-future-citation-forecast-v2.md
2. docs/next-phase-v2/08-citation-forecast-model-v2-retraining-report.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md
4. docs/next-phase-v2/42-patentiq-v2-phase-03-family-future-citation-forecast-execution-plan.md


### Metrics

- `ml_label_family_future_citations_rows`: `11772956`
- `ml_feature_family_future_citations_rows`: `11772956`
- `ml_split_registry_rows`: `27944510`
- `ml_split_registry_phase03_rows`: `11772956`
- `ml_experiment_registry_rows`: `8`
- `ml_model_registry_rows`: `2`
- `ml_calibration_registry_rows`: `2`
- `phase03_3y_spearman`: `0.4495002937134462`
- `phase03_3y_interval_coverage_80pct`: `0.80536`
- `phase03_5y_spearman`: `0.5995602733201085`
- `phase03_5y_interval_coverage_80pct`: `0.79701230228471`
- `phase03_sampled_training`: `1.0`
- `phase03_train_rows_raw`: `6409400.0`
- `phase03_train_rows_used`: `200000.0`
- `phase03_validation_rows_raw`: `2314420.0`
- `phase03_validation_rows_used`: `50000.0`
- `phase03_test_rows_raw`: `2809372.0`
- `phase03_test_rows_used`: `50000.0`

## ml-phase04-family-jurisdiction-lapse-risk | success

- Summary: Built Phase 04 branch-aware label, feature, split, and baseline-training artifacts with registry-preserving metadata.
- Started: 2026-04-07T18:45:59+00:00
- Finished: 2026-04-07T18:46:01+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_family_jurisdiction_lapse_risk.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_family_jurisdiction_lapse_risk.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase04.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_family_jurisdiction_lapse_risk.json
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_12m_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_24m_model.txt
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/family_jurisdiction_lapse_risk_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase04-family-jurisdiction-lapse-risk.json`

### Methods

1. Derived family-jurisdiction lapse labels from dated lapse/expiry events after each yearly active-grant branch snapshot.
2. Joined dense branch history with dense family PIT metrics to keep first-pass Phase 04 features year-safe.
3. Assigned one grouped time split per family-jurisdiction trajectory using the latest fully observed 24m year.
4. Trained sampled LightGBM classifier baselines and selected validation-best probability calibration per horizon.

### Calculations

1. 12m and 24m labels are only treated as observed when the horizon closes by the ETL snapshot date.
2. Branch-level timing features use the lag between as_of_date and last grant/lapse/expiry events.
3. Current-state-only legal enrichments are intentionally excluded from the initial promotion feature set.


### Governing Docs

1. docs/next-phase-v2/45-patentiq-v2-phase-04-family-jurisdiction-lapse-risk-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md


### Metrics

- `ml_label_family_jurisdiction_lapse_risk_rows`: `151930838`
- `ml_feature_family_jurisdiction_lapse_risk_rows`: `97347045`
- `ml_split_registry_rows`: `24970099`
- `ml_split_registry_phase04_rows`: `13197143`
- `ml_experiment_registry_rows`: `10`
- `ml_model_registry_rows`: `4`
- `ml_calibration_registry_rows`: `4`
- `phase04_12m_roc_auc`: `0.9827997855811244`
- `phase04_12m_pr_auc`: `0.12142728609508663`
- `phase04_12m_brier_score`: `0.00303720718626948`
- `phase04_24m_roc_auc`: `0.9715023234033948`
- `phase04_24m_pr_auc`: `0.11726776657391866`
- `phase04_24m_brier_score`: `0.005308691908264898`

## ml-phase06-jurisdiction-field-trend-forecast | success

- Summary: Built Phase 06 jurisdiction-field trend labels, features, split registry, baseline forecasts, and calibration metadata.
- Started: 2026-04-07T19:28:23+00:00
- Finished: 2026-04-07T19:28:30+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_jurisdiction_field_trend_future.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_jurisdiction_field_trend_forecast.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase06.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_jurisdiction_field_trend_forecast.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_jurisdiction_field_trend_forecast.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase06-jurisdiction-field-trend-forecast.json`

### Methods

1. Built a dense jurisdiction-field-year grid from local and global trend timeseries.
2. Derived lag, acceleration, volatility, and market-context features.
3. Trained LightGBM baseline regressors on horizon-safe grouped time splits.
4. Calibrated interval outputs with validation residual quantiles.

### Calculations

1. Targets are future local family filing counts at 3-year and 5-year horizons.
2. Prediction rows are emitted interval-first and retain observed-horizon flags.


### Governing Docs

1. docs/next-phase-v2/48-patentiq-v2-post-phase-04-prioritization-and-next-execution-path.md
2. docs/next-phase-v2/49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md


### Metrics

- `label_rows`: `25950`
- `feature_rows`: `25950`
- `split_rows`: `25950`
- `prediction_rows`: `51900`
- `3y_direction_accuracy`: `0.5017341040462427`
- `3y_interval_coverage_80pct`: `0.7491329479768786`
- `3y_mape_all`: `11.84358199145901`
- `5y_direction_accuracy`: `0.7635838150289017`
- `5y_interval_coverage_80pct`: `0.7884393063583816`
- `5y_mape_all`: `181.20963084732625`

## ml-phase06-jurisdiction-field-trend-forecast | success

- Summary: Built Phase 06 jurisdiction-field trend labels, features, split registry, baseline forecasts, and calibration metadata.
- Started: 2026-04-07T19:29:18+00:00
- Finished: 2026-04-07T19:29:23+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_jurisdiction_field_trend_future.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_jurisdiction_field_trend_forecast.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase06.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_jurisdiction_field_trend_forecast.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_jurisdiction_field_trend_forecast.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase06-jurisdiction-field-trend-forecast.json`

### Methods

1. Built a dense jurisdiction-field-year grid from local and global trend timeseries.
2. Derived lag, acceleration, volatility, and market-context features.
3. Trained LightGBM baseline regressors on horizon-safe grouped time splits.
4. Calibrated interval outputs with validation residual quantiles.

### Calculations

1. Targets are future local family filing counts at 3-year and 5-year horizons.
2. Prediction rows are emitted interval-first and retain observed-horizon flags.


### Governing Docs

1. docs/next-phase-v2/48-patentiq-v2-post-phase-04-prioritization-and-next-execution-path.md
2. docs/next-phase-v2/49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md


### Metrics

- `label_rows`: `16435`
- `feature_rows`: `16435`
- `split_rows`: `16435`
- `prediction_rows`: `32870`
- `3y_direction_accuracy`: `0.42716763005780345`
- `3y_interval_coverage_80pct`: `0.7277456647398844`
- `3y_mape_all`: `13.825853949629128`
- `5y_direction_accuracy`: `0.7`
- `5y_interval_coverage_80pct`: `0.7682080924855491`
- `5y_mape_all`: `189.47232171353048`

## ml-phase06-jurisdiction-field-trend-forecast | success

- Summary: Built Phase 06 jurisdiction-field trend labels, features, split registry, direction-first baseline predictions, and band-calibration metadata.
- Started: 2026-04-07T20:00:14+00:00
- Finished: 2026-04-07T20:00:23+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_jurisdiction_field_trend_future.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_jurisdiction_field_trend_forecast.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase06.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_jurisdiction_field_trend_forecast.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/jurisdiction_field_trend_forecast_direction_calibration.json
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_jurisdiction_field_trend_forecast.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase06-jurisdiction-field-trend-forecast.json`

### Methods

1. Built a dense jurisdiction-field-year grid from local and global trend timeseries.
2. Derived lag, acceleration, volatility, and market-context features.
3. Trained LightGBM multiclass direction baselines on horizon-safe grouped time splits.
4. Assigned direction, strength, and support bands from class probabilities and train-support thresholds.

### Calculations

1. Labels retain raw-count, growth, and direction fields, but the promoted serving semantics are direction-first.
2. Prediction rows are emitted with direction, strength, and support fields plus secondary count references.


### Governing Docs

1. docs/next-phase-v2/48-patentiq-v2-post-phase-04-prioritization-and-next-execution-path.md
2. docs/next-phase-v2/49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md


### Metrics

- `label_rows`: `16435`
- `feature_rows`: `16435`
- `split_rows`: `16435`
- `prediction_rows`: `32870`
- `3y_class_accuracy`: `0.5416184971098266`
- `3y_balanced_accuracy`: `0.6256237703897015`
- `3y_macro_f1`: `0.5421183525674148`
- `5y_class_accuracy`: `0.7265895953757225`
- `5y_balanced_accuracy`: `0.8631260277073224`
- `5y_macro_f1`: `0.5873721893570805`

## ml-phase06-jurisdiction-field-trend-forecast | success

- Summary: Built Phase 06 jurisdiction-field trend labels, features, split registry, direction-first baseline predictions, and band-calibration metadata.
- Started: 2026-04-07T20:05:50+00:00
- Finished: 2026-04-07T20:06:00+00:00

### Inputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_local_tech_trends_timeseries.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_global_tech_trends_timeseries.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet

### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_jurisdiction_field_trend_future.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_jurisdiction_field_trend_forecast.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase06.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_prediction_jurisdiction_field_trend_forecast.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/jurisdiction_field_trend_forecast_direction_calibration.json
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_jurisdiction_field_trend_forecast.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-phase06-jurisdiction-field-trend-forecast.json`

### Methods

1. Built a dense jurisdiction-field-year grid from local and global trend timeseries.
2. Derived lag, acceleration, volatility, and market-context features.
3. Trained LightGBM multiclass direction baselines on horizon-safe grouped time splits.
4. Assigned direction, strength, and support bands from class probabilities and train-support thresholds.

### Calculations

1. Labels retain raw-count, growth, and direction fields, but the promoted serving semantics are direction-first.
2. Prediction rows are emitted with direction, strength, and support fields plus secondary count references.


### Governing Docs

1. docs/next-phase-v2/48-patentiq-v2-post-phase-04-prioritization-and-next-execution-path.md
2. docs/next-phase-v2/49-patentiq-v2-phase-06-jurisdiction-field-trend-forecast-execution-plan.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md


### Metrics

- `label_rows`: `16435`
- `feature_rows`: `16435`
- `split_rows`: `16435`
- `prediction_rows`: `32870`
- `3y_class_accuracy`: `0.5416184971098266`
- `3y_balanced_accuracy`: `0.6256237703897015`
- `3y_macro_f1`: `0.5421183525674148`
- `5y_class_accuracy`: `0.7265895953757225`
- `5y_balanced_accuracy`: `0.8631260277073224`
- `5y_macro_f1`: `0.5873721893570805`

## gold-portfolio | success

- Summary: Built Gold portfolio marts from the family-owner bridge and Gold family/history contracts.
- Started: 2026-04-07T20:44:44+00:00
- Finished: 2026-04-07T20:59:50+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_heritage_summary.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_portfolio_prediction_rollup.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_contributors.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_portfolio_field_timeseries_rows`: `5520241`
- `gold_portfolio_summary_rows`: `3034400`
- `gold_portfolio_threat_matrix_rows`: `15269449`
- `gold_portfolio_heritage_summary_rows`: `3852589`
- `ml_portfolio_prediction_rollup_rows`: `3034400`
- `gold_portfolio_forecast_summary_rows`: `3034400`
- `gold_portfolio_forecast_segments_rows`: `11040482`
- `gold_portfolio_forecast_contributors_rows`: `17866740`

## ml-pending-grant-pipeline | success

- Summary: Materialized pending-grant label, feature, and split contracts for the next Phase 08 extension.
- Started: 2026-04-07T21:57:48+00:00
- Finished: 2026-04-07T21:57:50+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_pending_grant_event.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_pending_grant_pipeline.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase_grant.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_pending_grant_pipeline.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-pending-grant-pipeline.json`

### Methods

1. Built branch-grain pending-grant labels from dense branch history by checking future grant conversion within 12m and 24m horizons.
2. Joined family PIT-safe context and publication-stage counts to create the first pending-grant feature scaffold.
3. Wrote phase-specific split registry and placeholder registry/model-card artifacts without training a live model yet.

### Calculations

1. Observed-horizon flags require the as-of row to have a fully observable 12m or 24m window by the ETL snapshot date.
2. Pending-age is measured from the last pending event date when available.


### Governing Docs

1. docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md
2. docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md


### Metrics

- `ml_label_pending_grant_event_rows`: `93347403`
- `ml_feature_pending_grant_pipeline_rows`: `93347403`
- `ml_split_registry_phase_grant_rows`: `93347403`
- `pending_grant_observed_12m_rows`: `74015905`
- `pending_grant_observed_24m_rows`: `64881761`

## ml-pending-grant-pipeline | success

- Summary: Materialized pending-grant label, feature, and split artifacts and trained first baseline pending-grant classifiers when split sizes were sufficient.
- Started: 2026-04-08T07:31:17+00:00
- Finished: 2026-04-08T07:31:20+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_pending_grant_event.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_pending_grant_pipeline.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase_grant.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_pending_grant_pipeline.json
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_12m_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_24m_model.txt
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-pending-grant-pipeline.json`

### Methods

1. Built branch-grain pending-grant labels from dense branch history by checking future grant conversion within 12m and 24m horizons.
2. Joined family PIT-safe context and publication-stage counts to create the first pending-grant feature scaffold.
3. Sampled split-aligned pending snapshots to train first 12m and 24m LightGBM baseline grant-probability models with validation-time calibration selection.

### Calculations

1. Observed-horizon flags require the as-of row to have a fully observable 12m or 24m window by the ETL snapshot date.
2. Pending-age is measured from the last pending event date when available.


### Governing Docs

1. docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md
2. docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md


### Metrics

- `ml_label_pending_grant_event_rows`: `93347403`
- `ml_feature_pending_grant_pipeline_rows`: `93347403`
- `ml_split_registry_phase_grant_rows`: `93347403`
- `pending_grant_observed_12m_rows`: `74015905`
- `pending_grant_observed_24m_rows`: `64881761`
- `pending_grant_12m_roc_auc`: `0.9962887385977773`
- `pending_grant_12m_pr_auc`: `0.8489725905894858`
- `pending_grant_12m_brier_score`: `0.005760928692438487`
- `pending_grant_24m_roc_auc`: `0.9989797963236232`
- `pending_grant_24m_pr_auc`: `0.9688290062191814`
- `pending_grant_24m_brier_score`: `0.005115810373689656`

## ml-pending-grant-pipeline | success

- Summary: Materialized pending-grant label, feature, and split artifacts and trained first baseline pending-grant classifiers when split sizes were sufficient.
- Started: 2026-04-08T07:41:11+00:00
- Finished: 2026-04-08T07:41:14+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_pending_grant_event.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_pending_grant_pipeline.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase_grant.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_pending_grant_pipeline.json
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_12m_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_24m_model.txt
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-pending-grant-pipeline.json`

### Methods

1. Built branch-grain pending-grant labels from dense branch history by checking future grant conversion within 12m and 24m horizons.
2. Joined family PIT-safe context and publication-stage counts to create the first pending-grant feature scaffold.
3. Sampled split-aligned pending snapshots to train first 12m and 24m LightGBM baseline grant-probability models with validation-time calibration selection.

### Calculations

1. Observed-horizon flags require the as-of row to have a fully observable 12m or 24m window by the ETL snapshot date.
2. Pending-age is measured from the last pending event date when available.


### Governing Docs

1. docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md
2. docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md


### Metrics

- `ml_label_pending_grant_event_rows`: `93347403`
- `ml_feature_pending_grant_pipeline_rows`: `93347403`
- `ml_split_registry_phase_grant_rows`: `93347403`
- `pending_grant_observed_12m_rows`: `74015905`
- `pending_grant_observed_24m_rows`: `64881761`
- `pending_grant_12m_roc_auc`: `0.6458783007770416`
- `pending_grant_12m_pr_auc`: `0.18687252398502663`
- `pending_grant_12m_brier_score`: `0.08914891953093323`
- `pending_grant_24m_roc_auc`: `0.6555293858125568`
- `pending_grant_24m_pr_auc`: `0.33159218721986716`
- `pending_grant_24m_brier_score`: `0.1570057345910732`

## silver-pit-classification-dense | success

- Summary: Built silver_family_classification_pit_dense.parquet with dense family-year WIPO/CPC classification membership for family, portfolio, and market chronology surfaces.
- Started: 2026-04-08T08:43:57+00:00
- Finished: 2026-04-08T08:48:32+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_classification_pit_dense_audit.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-pit-classification-dense.json`

### Methods

1. Uses silver_family_feature_snapshot_pit_dense as the family-year backbone so classification rows stay aligned with the existing PIT grain.
2. Replays stable family-level WIPO and CPC membership across family PIT years rather than inferring dated code mutations.
3. Derives CPC sections, subclasses, and main groups from canonical family CPC symbols.
4. Writes a persisted JSON audit beside the parquet to validate dense PIT parity, uniqueness, and classification coverage.

### Calculations

1. covered_wipo_fields_asof and primary_wipo_field_asof come from silver_family_wipo_fields and are replayed across PIT years.
2. cpc_main_groups_asof normalizes CPC symbols to main-group form by replacing the subgroup suffix with '/00'.
3. classification_visibility_policy = stable_family_classification_replay and historical_classification_truth_supported = false for this first implementation.

### Downstream Impacts

1. gold_family_classification_mix_pit can use this as the family-year classification basis.
2. gold_portfolio_classification_mix_pit can aggregate this with explicit current-owner replay caveats.
3. gold_market_cpc_trend_pit can use the same CPC/WIPO chronology for CPC-within-field trends and PIT importance views.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
3. docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md
4. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md
5. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `silver_family_classification_pit_dense_rows`: `164988135`
- `silver_family_classification_pit_dense_duplicate_family_year_keys`: `0`
- `silver_family_classification_pit_dense_rows_with_cpc_main_groups`: `93283467`

## gold-family-classification-mix-pit | success

- Summary: Built the family classification PIT summary mart from the dense family-year classification backbone.
- Started: 2026-04-08T09:02:04+00:00
- Finished: 2026-04-08T09:07:15+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_mix_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-classification-mix-pit.json`

### Methods

1. Started from silver_family_classification_pit_dense so the mart stays aligned with the dense family-year PIT grain.
2. Kept reusable WIPO and CPC arrays for UI drill-down while materializing summary fields for family cards and compare views.
3. Made the stable classification replay policy explicit instead of implying dated code-mutation truth.

### Calculations

1. Classification concentration HHI uses equal-share membership across CPC main groups in the first stable-replay implementation.
2. Classification entropy uses the natural log of the CPC main-group count under the same equal-share assumption.
3. Classification breadth band is derived from CPC main-group count: unknown, focused, balanced, diversified.

### Downstream Impacts

1. This mart is the family-level classification source for chronological CPC/WIPO UI sections and later portfolio and market classification rollups.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
3. docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md


### Metrics

- `gold_family_classification_mix_pit_rows`: `164988135`

## gold-family-classification-mix-pit | success

- Summary: Built the family classification PIT summary mart from the dense family-year classification backbone.
- Started: 2026-04-08T09:08:09+00:00
- Finished: 2026-04-08T09:10:47+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_mix_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-classification-mix-pit.json`

### Methods

1. Started from silver_family_classification_pit_dense so the mart stays aligned with the dense family-year PIT grain.
2. Kept reusable WIPO and CPC arrays for UI drill-down while materializing summary fields for family cards and compare views.
3. Made the stable classification replay policy explicit instead of implying dated code-mutation truth.

### Calculations

1. Classification concentration HHI uses equal-share membership across CPC main groups in the first stable-replay implementation.
2. Classification entropy uses the natural log of the CPC main-group count under the same equal-share assumption.
3. Classification breadth band is derived from CPC main-group count: unknown, focused, balanced, diversified.

### Downstream Impacts

1. This mart is the family-level classification source for chronological CPC/WIPO UI sections and later portfolio and market classification rollups.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
3. docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md


### Metrics

- `gold_family_classification_mix_pit_rows`: `164988135`

## gold-portfolio-classification-mix-pit | success

- Summary: Built the portfolio classification PIT mart by aggregating family-year classification membership through the current owner bridge.
- Started: 2026-04-08T09:16:19+00:00
- Finished: 2026-04-08T09:38:24+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_classification_mix_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio-classification-mix-pit.json`

### Methods

1. Started from the family classification mix PIT and family compare PIT so owner-year classification rows stay aligned with historical-safe family-year context.
2. Aggregated WIPO-field and CPC-main-group membership separately into one owner-year classification mart.
3. Kept current-owner replay caveats explicit rather than implying true historical ownership.

### Calculations

1. Portfolio family share within a classification is the fraction of owner-year families carrying that classification membership.
2. Portfolio active-family share within a classification is measured against owner-year active-family count.
3. Classification rank within owner-year is ordered by family count, then active-family share, then code.

### Downstream Impacts

1. This mart supports chronological portfolio CPC/WIPO exposure, gain/loss views, and later market-classification rollups.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
3. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md


### Metrics

- `gold_portfolio_classification_mix_pit_rows`: `174375803`

## gold-market-cpc-trend-pit | success

- Summary: Built the market CPC trend PIT mart from family-year classification visibility and family compare context.
- Started: 2026-04-08T19:40:53+00:00
- Finished: 2026-04-08T19:43:00+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_cpc_trend_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-cpc-trend-pit.json`

### Methods

1. Started from the family classification mix PIT and grouped visible CPC main groups by primary WIPO field and year.
2. Avoided inventing a many-to-many CPC-to-WIPO mapping by using the family primary WIPO field as the market segment basis.
3. Joined market summary PIT only for segment heat-state context, while deriving family-count denominators directly from the family-year basis.

### Calculations

1. CPC family share within segment is measured against the family-year segment basis, not against summed CPC memberships.
2. CPC growth index uses prior-year family-count change within the same WIPO-field and CPC pair.
3. CPC heat state is banded from growth: heating above 10 percent, cooling below negative 10 percent, otherwise stable.

### Downstream Impacts

1. This mart powers CPC drill-downs inside market WIPO segments and feeds the global CPC importance PIT layer.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md
3. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_market_cpc_trend_pit_rows`: `862969`

## gold-cpc-importance-pit | success

- Summary: Built the CPC importance PIT mart from the market CPC trend layer.
- Started: 2026-04-08T19:43:17+00:00
- Finished: 2026-04-08T19:43:17+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_cpc_importance_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-cpc-importance-pit.json`

### Methods

1. Aggregated CPC presence across WIPO segments into one CPC-year row per main group.
2. Weighted blocking and enforceability by CPC family count so large segments matter proportionally.
3. Scored CPC importance from family share, segment breadth, blocking, enforceability, and positive growth contribution.

### Calculations

1. CPC global family share is measured against the total family classification basis across all WIPO segments in the year.
2. CPC segment presence share is the fraction of WIPO segments where the CPC appears in that year.
3. Importance band is derived from the composite score: strategic above 0.55, core above 0.30, otherwise emerging.

### Downstream Impacts

1. This mart supports year-slice CPC ranking cards and importance drill-downs in Market Intelligence.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_cpc_importance_pit_rows`: `152753`

## gold-cpc-importance-pit | success

- Summary: Built the CPC importance PIT mart from the market CPC trend layer.
- Started: 2026-04-08T19:45:25+00:00
- Finished: 2026-04-08T19:45:25+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_cpc_importance_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-cpc-importance-pit.json`

### Methods

1. Aggregated CPC presence across WIPO segments into one CPC-year row per main group.
2. Weighted blocking and enforceability by CPC family count so large segments matter proportionally.
3. Scored CPC importance from family share, segment breadth, blocking, enforceability, and positive growth contribution.

### Calculations

1. CPC global family share is measured against the total family classification basis across all WIPO segments in the year.
2. CPC segment presence share is the fraction of WIPO segments where the CPC appears in that year.
3. Importance band is derived from the composite score: strategic above 0.55, core above 0.30, otherwise emerging.

### Downstream Impacts

1. This mart supports year-slice CPC ranking cards and importance drill-downs in Market Intelligence.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_cpc_importance_pit_rows`: `152753`

## gold-market-cpc-trend-pit | success

- Summary: Built the market CPC trend PIT mart from family-year classification visibility and family compare context.
- Started: 2026-04-08T19:47:09+00:00
- Finished: 2026-04-08T19:49:13+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_cpc_trend_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-cpc-trend-pit.json`

### Methods

1. Started from the family classification mix PIT and grouped visible CPC main groups by primary WIPO field and year.
2. Avoided inventing a many-to-many CPC-to-WIPO mapping by using the family primary WIPO field as the market segment basis.
3. Joined market summary PIT only for segment heat-state context, while deriving family-count denominators directly from the family-year basis.

### Calculations

1. CPC family share within segment is measured against the family-year segment basis, not against summed CPC memberships.
2. CPC growth index uses prior-year family-count change within the same WIPO-field and CPC pair.
3. CPC heat state is banded from growth: heating above 10 percent, cooling below negative 10 percent, otherwise stable.

### Downstream Impacts

1. This mart powers CPC drill-downs inside market WIPO segments and feeds the global CPC importance PIT layer.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/57-patentiq-v2-classification-first-seen-visibility-audit-and-upgrade-plan.md
3. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_market_cpc_trend_pit_rows`: `862969`

## gold-cpc-importance-pit | success

- Summary: Built the CPC importance PIT mart from the market CPC trend layer.
- Started: 2026-04-08T19:49:35+00:00
- Finished: 2026-04-08T19:49:36+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_cpc_importance_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-cpc-importance-pit.json`

### Methods

1. Aggregated CPC presence across WIPO segments into one CPC-year row per main group.
2. Weighted blocking and enforceability by CPC family count so large segments matter proportionally.
3. Scored CPC importance from family share, segment breadth, blocking, enforceability, and positive growth contribution.

### Calculations

1. CPC global family share is measured against the total family classification basis across all WIPO segments in the year.
2. CPC segment presence share is the fraction of WIPO segments where the CPC appears in that year.
3. Importance band is derived from the composite score: strategic above 0.55, core above 0.30, otherwise emerging.

### Downstream Impacts

1. This mart supports year-slice CPC ranking cards and importance drill-downs in Market Intelligence.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_cpc_importance_pit_rows`: `152753`

## ml-pending-grant-pipeline | success

- Summary: Materialized pending-grant label, feature, and split artifacts and trained first baseline pending-grant classifiers when split sizes were sufficient.
- Started: 2026-04-08T21:08:00+00:00
- Finished: 2026-04-08T21:08:10+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_pending_grant_event.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_pending_grant_pipeline.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase_grant.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_pending_grant_pipeline.json
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_12m_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_24m_model.txt
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-pending-grant-pipeline.json`

### Methods

1. Built branch-grain pending-grant labels from dense branch history by checking future grant conversion within 12m and 24m horizons.
2. Joined family PIT-safe context and publication-stage counts to create the first pending-grant feature scaffold.
3. Sampled split-aligned pending snapshots to train first 12m and 24m LightGBM baseline grant-probability models with validation-time calibration selection.

### Calculations

1. Observed-horizon flags require the as-of row to have a fully observable 12m or 24m window by the ETL snapshot date.
2. Pending-age is measured from the last pending event date when available.


### Governing Docs

1. docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md
2. docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md


### Metrics

- `ml_label_pending_grant_event_rows`: `93347403`
- `ml_feature_pending_grant_pipeline_rows`: `93347403`
- `ml_split_registry_phase_grant_rows`: `93347403`
- `pending_grant_observed_12m_rows`: `74015905`
- `pending_grant_observed_24m_rows`: `64881761`
- `pending_grant_12m_roc_auc`: `0.6386844283833993`
- `pending_grant_12m_pr_auc`: `0.16795010043304615`
- `pending_grant_12m_brier_score`: `0.08936263759827406`
- `pending_grant_24m_roc_auc`: `0.6736843727892121`
- `pending_grant_24m_pr_auc`: `0.33229906039053775`
- `pending_grant_24m_brier_score`: `0.15684801460752817`

## ml-pending-grant-pipeline | success

- Summary: Materialized pending-grant label, feature, and split artifacts and trained first baseline pending-grant classifiers when split sizes were sufficient.
- Started: 2026-04-08T21:48:37+00:00
- Finished: 2026-04-08T21:48:41+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_label_pending_grant_event.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_pending_grant_pipeline.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_split_registry_phase_grant.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_experiment_registry.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_model_registry.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_calibration_registry.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_feature_manifest.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/model_card_pending_grant_pipeline.json
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_12m_model.txt
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_24m_model.txt
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/pending_grant_pipeline_calibration.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/ml-pending-grant-pipeline.json`

### Methods

1. Built branch-grain pending-grant labels from dense branch history by checking future grant conversion within 12m and 24m horizons.
2. Joined family PIT-safe context and publication-stage counts to create the first pending-grant feature scaffold.
3. Sampled split-aligned pending snapshots to train first 12m and 24m LightGBM baseline grant-probability models with validation-time calibration selection.

### Calculations

1. Observed-horizon flags require the as-of row to have a fully observable 12m or 24m window by the ETL snapshot date.
2. Pending-age is measured from the last pending event date when available.


### Governing Docs

1. docs/next-phase-v2/55-patentiq-v2-pending-grant-pipeline-execution-plan.md
2. docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md
3. docs/next-phase-v2/15-patentiq-v2-prediction-training-flow-and-guardrails.md


### Metrics

- `ml_label_pending_grant_event_rows`: `93347403`
- `ml_feature_pending_grant_pipeline_rows`: `93347403`
- `ml_split_registry_phase_grant_rows`: `93347403`
- `pending_grant_observed_12m_rows`: `74015905`
- `pending_grant_observed_24m_rows`: `64881761`
- `pending_grant_12m_roc_auc`: `0.6394576583398613`
- `pending_grant_12m_pr_auc`: `0.1669747356742301`
- `pending_grant_12m_brier_score`: `0.08874634589296647`
- `pending_grant_24m_roc_auc`: `0.6600185905047047`
- `pending_grant_24m_pr_auc`: `0.3201084678815563`
- `pending_grant_24m_brier_score`: `0.1569449701451074`

## gold-family-metrics | success

- Summary: Built Gold family blocking, attacker, and heritage marts from note-aligned Silver legal and citation contracts.
- Started: 2026-04-09T14:15:43+00:00
- Finished: 2026-04-09T14:20:54+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_summary.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_timeseries_pit.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-metrics.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_blocking_power_rows`: `17633618`
- `gold_family_attacker_summary_rows`: `6334292`
- `gold_family_citation_summary_rows`: `17633618`
- `gold_family_citation_timeseries_pit_rows`: `164988135`
- `gold_family_heritage_summary_rows`: `21353101`

## gold-family-metrics | success

- Summary: Built Gold family blocking, attacker, and heritage marts from note-aligned Silver legal and citation contracts.
- Started: 2026-04-09T14:23:34+00:00
- Finished: 2026-04-09T14:24:21+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_summary.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_timeseries_pit.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-metrics.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_blocking_power_rows`: `17633618`
- `gold_family_attacker_summary_rows`: `6334292`
- `gold_family_citation_summary_rows`: `17633618`
- `gold_family_citation_timeseries_pit_rows`: `164988135`
- `gold_family_heritage_summary_rows`: `21353101`

## gold-market-semantic | success

- Summary: Built Gold Market Intelligence and semantic-context marts from note-aligned Silver and Gold family outputs.
- Started: 2026-04-09T15:04:48+00:00
- Finished: 2026-04-09T15:06:07+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_segments.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_overview.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_citation_trend_pit.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_citation_pressure_by_jurisdiction_pit.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_attacker_leaderboard_pit.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-semantic.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_market_intelligence_segments_rows`: `10`
- `gold_market_intelligence_timeseries_rows`: `504`
- `gold_market_intelligence_overview_rows`: `1`
- `gold_market_citation_trend_pit_rows`: `295`
- `gold_market_citation_pressure_by_jurisdiction_pit_rows`: `6064`
- `gold_market_attacker_leaderboard_pit_rows`: `4771191`
- `gold_semantic_match_context_rows`: `20295898`

## gold-market-semantic | success

- Summary: Built Gold Market Intelligence and semantic-context marts from note-aligned Silver and Gold family outputs.
- Started: 2026-04-09T15:07:11+00:00
- Finished: 2026-04-09T15:09:51+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_segments.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_overview.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_citation_trend_pit.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_citation_pressure_by_jurisdiction_pit.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_attacker_leaderboard_pit.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-semantic.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_market_intelligence_segments_rows`: `10`
- `gold_market_intelligence_timeseries_rows`: `504`
- `gold_market_intelligence_overview_rows`: `1`
- `gold_market_citation_trend_pit_rows`: `294`
- `gold_market_citation_pressure_by_jurisdiction_pit_rows`: `6063`
- `gold_market_attacker_leaderboard_pit_rows`: `4771190`
- `gold_semantic_match_context_rows`: `20295898`

## gold-portfolio-classification-jurisdiction-pit | failed

- Summary: Built the portfolio WIPO-CPC-jurisdiction PIT mart by replaying family slice rows through the current owner bridge.
- Started: 2026-04-09T15:29:56+00:00
- Finished: 2026-04-09T15:29:56+00:00



### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio-classification-jurisdiction-pit.json`

### Methods

1. Started from the family classification-jurisdiction PIT mart and aggregated through the family-owner bridge at owner-year slice grain.
2. Kept owner replay caveats explicit rather than implying native historical owner truth.
3. Normalized citation pressure inside each owner-year so slice comparisons are readable without pretending cross-owner comparability.

### Calculations

1. Portfolio family share in slice is the owner-year family count in the slice divided by total owner-year family count.
2. Portfolio citation pressure index scales slice-average pre-as-of forward citations to the strongest slice within the same owner-year.
3. Slice rank within owner-year is ordered by family count, then active family count, then blocking density, then slice keys.

### Downstream Impacts

1. This mart supports portfolio classification-geography leaderboards, CPC-by-jurisdiction views, and field-cluster evidence tables.

### Governing Docs

1. docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md
2. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
3. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md

### Warnings

1. Missing required inputs for gold-portfolio-classification-jurisdiction-pit: ['/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_jurisdiction_pit.parquet']

## gold-market-cpc-jurisdiction-trend-pit | failed

- Summary: Built the market WIPO-CPC-jurisdiction PIT mart from family slice evidence.
- Started: 2026-04-09T15:29:57+00:00
- Finished: 2026-04-09T15:29:57+00:00



### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-cpc-jurisdiction-trend-pit.json`

### Methods

1. Started from the family classification-jurisdiction PIT mart so market slice rows inherit the same replay-safe family-year semantics.
2. Aggregated families by WIPO field, CPC main group, jurisdiction, and year, then lagged each slice for year-over-year growth.
3. Normalized citation pressure inside each year so slice rankings remain readable without pretending absolute comparability across years.

### Calculations

1. Family share within slice basis is measured against the same WIPO-field and jurisdiction basis for the same year.
2. Growth index compares current slice family count against prior-year family count in the same WIPO-CPC-jurisdiction slice.
3. Slice rank within year is ordered by family count, then blocking density, then slice keys.

### Downstream Impacts

1. This mart supports market CPC-by-jurisdiction leaderboards, growth views, and future UI drill-downs across field, CPC, and office slices.

### Governing Docs

1. docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md
2. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
3. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md

### Warnings

1. Missing required input for gold-market-cpc-jurisdiction-trend-pit: /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_jurisdiction_pit.parquet

## gold-family-metrics | success

- Summary: Built Gold family blocking, attacker, and heritage marts from note-aligned Silver legal and citation contracts.
- Started: 2026-04-09T23:11:07+00:00
- Finished: 2026-04-09T23:13:13+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_summary.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_timeseries_pit.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-metrics.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_blocking_power_rows`: `17633618`
- `gold_family_attacker_summary_rows`: `6334292`
- `gold_family_citation_summary_rows`: `17633618`
- `gold_family_citation_timeseries_pit_rows`: `164988135`
- `gold_family_heritage_summary_rows`: `21353101`

## gold-history-blocking | success

- Summary: Built Gold blocking-power history marts from replay-aligned Silver legal and citation history.
- Started: 2026-04-09T23:13:21+00:00
- Finished: 2026-04-09T23:16:06+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-history-blocking.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_blocking_power_timeseries_rows`: `152145173`

## gold-family-classification-jurisdiction-pit | success

- Summary: Built the family WIPO-CPC-jurisdiction PIT mart from classification replay and dense branch history.
- Started: 2026-04-09T23:55:14+00:00
- Finished: 2026-04-10T00:07:34+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_jurisdiction_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-classification-jurisdiction-pit.json`

### Methods

1. Started from the family classification mix PIT and joined dense branch-year replay so technology and jurisdiction slices stay aligned to the same family-year grain.
2. Exploded WIPO-field and CPC-main-group membership into one row per family, year, field, CPC, and jurisdiction slice.
3. Kept replay caveats explicit by preserving classification-history support flags instead of implying dated code-mutation truth.

### Calculations

1. Jurisdiction support level reuses the current office support policy map and defaults to limited where no explicit support policy exists.
2. Active status is read from the branch-history replay for the same family, jurisdiction, and year.
3. Blocking, enforceability, and pre-as-of citation columns are carried from the family compare PIT for the same family-year.

### Downstream Impacts

1. This mart is the ranking-ready family evidence layer for WIPO x CPC x jurisdiction chronology and downstream portfolio and market slice rollups.

### Governing Docs

1. docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md
2. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
3. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md


### Metrics

- `gold_family_classification_jurisdiction_pit_rows`: `566936693`

## gold-family-summary | success

- Summary: Built the Gold family summary mart from note-aligned Silver family, legal, owner, and OECD contracts.
- Started: 2026-04-10T05:54:37+00:00
- Finished: 2026-04-10T06:33:26+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-summary.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_summary_rows`: `17633618`

## gold-portfolio | success

- Summary: Built Gold portfolio marts from the family-owner bridge and Gold family/history contracts.
- Started: 2026-04-10T07:53:43+00:00
- Finished: 2026-04-10T08:20:37+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_summary.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_timeseries.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_attacker_momentum.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_pressure_by_field.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_pressure_by_jurisdiction.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_heritage_summary.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_portfolio_prediction_rollup.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_contributors.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_portfolio_citation_summary_rows`: `21945507`
- `gold_portfolio_citation_timeseries_rows`: `21945507`
- `gold_portfolio_attacker_momentum_rows`: `6016882`
- `gold_portfolio_citation_pressure_by_field_rows`: `2052577`
- `gold_portfolio_citation_pressure_by_jurisdiction_rows`: `2000661`
- `gold_portfolio_field_timeseries_rows`: `5520241`
- `gold_portfolio_summary_rows`: `3034400`
- `gold_portfolio_threat_matrix_rows`: `15269449`
- `gold_portfolio_heritage_summary_rows`: `3852589`
- `ml_portfolio_prediction_rollup_rows`: `3034400`
- `gold_portfolio_forecast_summary_rows`: `3034400`
- `gold_portfolio_forecast_segments_rows`: `11040482`
- `gold_portfolio_forecast_contributors_rows`: `17866740`

## gold-market-summary-pit | success

- Summary: Built the market PIT summary mart from year-safe market timeseries, dense family compare PIT, and current-owner caveated family membership.
- Started: 2026-04-10T08:22:20+00:00
- Finished: 2026-04-10T08:23:14+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_summary_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-market-summary-pit.json`

### Methods

1. Started from the year-safe market-intelligence timeseries and retained one row per segment and year.
2. Joined dense family compare PIT with family field-contribution timeseries to derive blocking and active-family density by segment-year.
3. Used the current family owner from the family compare PIT as a historical owner proxy and labeled that caveat explicitly.

### Calculations

1. Segment growth index is computed from family-count change versus the prior year when prior-year count exists.
2. Segment blocking density is a weighted average of family blocking power using field base fractions as segment participation weights.
3. Segment field balance is the average family allocation share to the segment, higher when families are more concentrated in that field.

### Downstream Impacts

1. This mart is the safe historical source for Market Intelligence year-slice cards, league tables, and segment detail drawers.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md


### Metrics

- `gold_market_summary_pit_rows`: `504`

## gold-family-citation-chronology | success

- Summary: Built a standalone family citation chronology mart directly from the citation event ledger without rebuilding the broader family Gold bundle.
- Started: 2026-04-12T17:25:00+00:00
- Finished: 2026-04-12T17:28:39+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_chronology.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-citation-chronology.json`

### Methods

1. Derived yearly family chronology from the clean citation event ledger rather than sparse PIT feature anchors.
2. Kept the existing PIT citation-timeseries mart untouched so downstream portfolio readers can migrate separately.
3. Anchored chronology rows to family priority year, citation years, and the current snapshot year for families with any citation activity.

### Calculations

1. Cumulative forward weighted citations follow the PIT-safe clean-edge-weight definition used in family historical features.
2. Early-window 5y and 7y counts follow family-level first-citation timing semantics at the citing-family grain.

### Downstream Impacts

1. Family chronology can migrate to this mart immediately without changing portfolio citation aggregation behavior.

### Governing Docs

1. docs/next-phase-v2/81-patentiq-v2-family-citation-chronology-standalone-audit.md
2. docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md


### Metrics

- `gold_family_citation_chronology_rows`: `30759429`

## gold-history-fields | success

- Summary: Built Gold field-contribution history marts from replay-aligned Silver branch and field history.
- Started: 2026-04-24T07:26:54+00:00
- Finished: 2026-04-24T08:05:54+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-history-fields.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_field_contributions_timeseries_rows`: `172223907`
- `gold_family_field_contributions_rows`: `172223907`

## gold-family-metrics | success

- Summary: Built Gold family blocking, attacker, and heritage marts from note-aligned Silver legal and citation contracts.
- Started: 2026-04-24T10:05:29+00:00
- Finished: 2026-04-24T10:06:22+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_summary.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_citation_timeseries_pit.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-metrics.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_blocking_power_rows`: `17633618`
- `gold_family_attacker_summary_rows`: `6334292`
- `gold_family_citation_summary_rows`: `17633618`
- `gold_family_citation_timeseries_pit_rows`: `164988135`
- `gold_family_heritage_summary_rows`: `21353101`

## gold-history-blocking | success

- Summary: Built Gold blocking-power history marts from replay-aligned Silver legal and citation history.
- Started: 2026-04-24T10:06:24+00:00
- Finished: 2026-04-24T10:09:11+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-history-blocking.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_family_blocking_power_timeseries_rows`: `152145173`

## gold-portfolio | success

- Summary: Built Gold portfolio marts from the family-owner bridge and Gold family/history contracts.
- Started: 2026-04-24T10:09:13+00:00
- Finished: 2026-04-24T10:34:40+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_summary.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_family_leaderboard.parquet
3. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_timeseries.parquet
4. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_attacker_momentum.parquet
5. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_pressure_by_field.parquet
6. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_citation_pressure_by_jurisdiction.parquet
7. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_filing_timeseries.parquet
8. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet
9. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet
10. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet
11. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_heritage_summary.parquet
12. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml/ml_portfolio_prediction_rollup.parquet
13. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet
14. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_segments.parquet
15. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_contributors.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio.json`

### Methods

1. Composed Gold marts from canonical Silver outputs rather than recomputing Bronze semantics in Gold.
2. Used deterministic primary-owner identity for family display and family-owner bridge membership for portfolio aggregation.
3. Anchored current-state Gold time-series rows to the current Gold/Silver snapshots to preserve exact parity while keeping historical rows replay-driven.

### Calculations

1. Family blocking power fuses current legal enforceability and adjusted citation score while retaining both raw components.
2. Portfolio rollups aggregate from family-level truth only and keep denominators bounded to the mega-cluster family universe.
3. Family and branch history-facing marts reuse Silver history sidecars rather than replaying legal events directly in Gold.

### Downstream Impacts

1. These Gold marts are the page-facing contracts for Family, Portfolio, Market Intelligence, Compare, Forecast, and Semantic UI workspaces.
2. Any drift here changes API payload shape and the values exposed to ranking, portfolio, and history surfaces.

### Governing Docs

1. docs/next-phase-v2/10-patentiq-v2-bronze-silver-gold-knowledge-tree.md
2. docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md
3. docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md


### Metrics

- `gold_portfolio_citation_summary_rows`: `21945507`
- `gold_portfolio_citation_family_leaderboard_rows`: `17274410`
- `gold_portfolio_citation_timeseries_rows`: `21945507`
- `gold_portfolio_attacker_momentum_rows`: `6016882`
- `gold_portfolio_citation_pressure_by_field_rows`: `2052577`
- `gold_portfolio_citation_pressure_by_jurisdiction_rows`: `2000661`
- `gold_portfolio_filing_timeseries_rows`: `5326177`
- `gold_portfolio_field_timeseries_rows`: `5520241`
- `gold_portfolio_summary_rows`: `3034400`
- `gold_portfolio_threat_matrix_rows`: `15269449`
- `gold_portfolio_heritage_summary_rows`: `3852589`
- `ml_portfolio_prediction_rollup_rows`: `3034400`
- `gold_portfolio_forecast_summary_rows`: `3034400`
- `gold_portfolio_forecast_segments_rows`: `11040482`
- `gold_portfolio_forecast_contributors_rows`: `17866740`

## silver-pit-dense | success

- Summary: Built silver_family_feature_snapshot_pit_dense.parquet with observed family-year PIT rows for historical compare, reports, and portfolio-over-time product behavior.
- Started: 2026-04-24T10:34:42+00:00
- Finished: 2026-04-24T11:36:17+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense.parquet
2. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_feature_snapshot_pit_dense_audit.json

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/silver-pit-dense.json`

### Methods

1. Generated one observed PIT row per family and as_of_year from family_priority_year through snapshot_year.
2. For each year, legal, blocking, field, citation, and coverage metrics are taken from the latest history or event evidence available at or before that year-end.
3. The current snapshot year uses snapshot_date rather than synthetic year-end so current-year product views stay aligned with the actual ETL snapshot.
4. A persisted JSON audit is written beside the dense PIT parquet to validate uniqueness, year range, multi-year family coverage, and value sanity.

### Calculations

1. as_of_date = MAKE_DATE(as_of_year, 12, 31) except for the current snapshot year where as_of_date = snapshot_date.
2. family_rcf_score_asof is normalized within the same as_of_year and primary field cohort.
3. data_completeness_pct_asof is the fraction of 12 tracked PIT columns that are non-null before COALESCE defaults are applied.

### Downstream Impacts

1. gold-family-compare-pit: should use this dense PIT layer when present for current-vs-selected-year family comparisons.
2. Historical compare and report flows can now use family-year rows rather than one anchored checkpoint per family.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md
3. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md


### Metrics

- `silver_family_feature_snapshot_pit_dense_rows`: `164988135`
- `silver_family_feature_snapshot_pit_dense_duplicate_family_year_keys`: `0`
- `silver_family_feature_snapshot_pit_dense_families_with_multiple_year_rows`: `17633618`

## gold-family-compare-pit | success

- Summary: Built the family compare PIT serving mart from the audited family PIT core and current summary metadata.
- Started: 2026-04-24T11:36:19+00:00
- Finished: 2026-04-24T11:37:40+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_compare_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-compare-pit.json`

### Methods

1. Consumed the dense family-year PIT layer for multi-year historical compare behavior.
2. Used only observed point-in-time family rows for historical compare serving.
3. Kept current owner, field, and OECD metadata explicitly labeled as current-only side metadata.
4. Materialized one row per family and observed year with a latest-observed-year flag for compare and report flows.

### Calculations

1. Family active-jurisdiction share is recomputed from point-in-time jurisdiction counts.
2. Historical-safe metrics come from the PIT core rather than current-state summary marts.

### Downstream Impacts

1. This mart is the safe family-level source for historical compare, time-slice report sections, and year-aware family evidence payloads.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md
3. docs/next-phase-v2/38-patentiq-v2-report-generation-use-cases-and-contract.md


### Metrics

- `gold_family_compare_pit_rows`: `164988135`

## gold-family-classification-mix-pit | success

- Summary: Built the family classification PIT summary mart from the dense family-year classification backbone.
- Started: 2026-04-24T11:37:42+00:00
- Finished: 2026-04-24T11:40:27+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_mix_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-classification-mix-pit.json`

### Methods

1. Started from silver_family_classification_pit_dense so the mart stays aligned with the dense family-year PIT grain.
2. Kept reusable WIPO and CPC arrays for UI drill-down while materializing summary fields for family cards and compare views.
3. Made the stable classification replay policy explicit instead of implying dated code-mutation truth.

### Calculations

1. Classification concentration HHI uses equal-share membership across CPC main groups in the first stable-replay implementation.
2. Classification entropy uses the natural log of the CPC main-group count under the same equal-share assumption.
3. Classification breadth band is derived from CPC main-group count: unknown, focused, balanced, diversified.

### Downstream Impacts

1. This mart is the family-level classification source for chronological CPC/WIPO UI sections and later portfolio and market classification rollups.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
3. docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md


### Metrics

- `gold_family_classification_mix_pit_rows`: `164988135`

## gold-family-classification-jurisdiction-pit | success

- Summary: Built the family WIPO-CPC-jurisdiction PIT mart from classification replay and dense branch history.
- Started: 2026-04-24T11:40:28+00:00
- Finished: 2026-04-24T12:01:57+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_classification_jurisdiction_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-family-classification-jurisdiction-pit.json`

### Methods

1. Started from the family classification mix PIT and joined dense branch-year replay so technology and jurisdiction slices stay aligned to the same family-year grain.
2. Exploded WIPO-field and CPC-main-group membership into one row per family, year, field, CPC, and jurisdiction slice.
3. Kept replay caveats explicit by preserving classification-history support flags instead of implying dated code-mutation truth.

### Calculations

1. Jurisdiction support level reuses the current office support policy map and defaults to limited where no explicit support policy exists.
2. Active status is read from the branch-history replay for the same family, jurisdiction, and year.
3. Blocking, enforceability, and pre-as-of citation columns are carried from the family compare PIT for the same family-year.

### Downstream Impacts

1. This mart is the ranking-ready family evidence layer for WIPO x CPC x jurisdiction chronology and downstream portfolio and market slice rollups.

### Governing Docs

1. docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md
2. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
3. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md


### Metrics

- `gold_family_classification_jurisdiction_pit_rows`: `566936693`

## gold-portfolio-summary-pit | success

- Summary: Built the portfolio PIT summary mart by aggregating family compare PIT rows through the current owner bridge with explicit historical caveats.
- Started: 2026-04-24T12:01:59+00:00
- Finished: 2026-04-24T12:07:18+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio-summary-pit.json`

### Methods

1. Aggregated only historical-safe family PIT rows into year-keyed portfolio summaries.
2. Reused the current owner bridge as a historical membership approximation and labeled that caveat explicitly.
3. Focused the first release on legal, blocking, coverage, and concentration signals rather than forcing unsupported historical field-mix claims.

### Calculations

1. Portfolio top-family dependence is measured as the maximum family blocking share within each owner-year slice.
2. Portfolio active-family count is derived from point-in-time active-jurisdiction presence rather than current family status.

### Downstream Impacts

1. This mart is the first safe source for portfolio over-time comparison, historical report sections, and legal-attrition context before Phase 04 predictions arrive.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md
3. docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md


### Metrics

- `gold_portfolio_summary_pit_rows`: `36127659`

## gold-portfolio-compare-pit | success

- Summary: Built the portfolio compare PIT mart from dense portfolio PIT summaries and year-safe field-mix support where available.
- Started: 2026-04-24T12:07:21+00:00
- Finished: 2026-04-24T12:07:32+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_compare_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio-compare-pit.json`

### Methods

1. Started from the dense portfolio summary PIT so legal, blocking, and concentration metrics stay historical-safe.
2. Joined field-mix metrics only for years actually present in the portfolio field timeseries.
3. Kept historical owner truth and historical field-mix support explicitly caveated when source coverage is unavailable.

### Calculations

1. Portfolio legal durability index is measured as active-family share within the historical owner-year proxy slice.
2. Portfolio field breadth is the count of positive active-family fields in the supported field-timeseries year.
3. Portfolio field concentration is calculated as HHI over active-family field shares, with top-field share surfaced separately.

### Downstream Impacts

1. This mart is the compare-oriented source for portfolio year-slice views, radar overlays, and report compare tables.

### Governing Docs

1. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
2. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md


### Metrics

- `gold_portfolio_compare_pit_rows`: `36127659`

## gold-portfolio-classification-mix-pit | success

- Summary: Built the portfolio classification PIT mart by aggregating family-year classification membership through the current owner bridge.
- Started: 2026-04-24T12:07:34+00:00
- Finished: 2026-04-24T13:29:11+00:00


### Outputs

1. /Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_classification_mix_pit.parquet

### Artifacts

- `stats_snapshot`: `/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats/gold-portfolio-classification-mix-pit.json`

### Methods

1. Started from the family classification mix PIT and family compare PIT so owner-year classification rows stay aligned with historical-safe family-year context.
2. Aggregated WIPO-field and CPC-main-group membership separately into one owner-year classification mart.
3. Kept current-owner replay caveats explicit rather than implying true historical ownership.

### Calculations

1. Portfolio family share within a classification is the fraction of owner-year families carrying that classification membership.
2. Portfolio active-family share within a classification is measured against owner-year active-family count.
3. Classification rank within owner-year is ordered by family count, then active-family share, then code.

### Downstream Impacts

1. This mart supports chronological portfolio CPC/WIPO exposure, gain/loss views, and later market-classification rollups.

### Governing Docs

1. docs/next-phase-v2/56-patentiq-v2-classification-pit-and-cpc-market-intelligence-execution-plan.md
2. docs/next-phase-v2/43-patentiq-v2-point-in-time-feature-layer-plan.md
3. docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md


### Metrics

- `gold_portfolio_classification_mix_pit_rows`: `158766274`


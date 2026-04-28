# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Layout

```
patent-iq/
├── etl/          # Local deterministic ETL pipeline (primary data engineering work)
├── backend/      # FastAPI service (layered: api/v1 → application/services → infrastructure → domain)
├── frontend/     # Next.js 16 app (do NOT modify unless explicitly asked)
├── prototype/    # Vite + React 18 sandbox for UI prototyping (do NOT modify unless explicitly asked)
└── docs/         # Architecture & requirements docs; new drafts go in docs/new-feature-ideas/
```

**Do not modify `frontend/` or `backend/` unless explicitly asked.**

---

## ETL Commands

All commands run from `etl/`:

```bash
# Install
poetry install

# Run a named stage
python scripts/run_stage.py <stage_name>

# Full pipeline order
python scripts/certify_sources.py
python scripts/run_stage.py certify
python scripts/run_stage.py prebronze        # or prebronze-heritage / prebronze-uspto-odp
python scripts/run_stage.py consolidate-before-bronze
python scripts/run_stage.py bronze
python scripts/run_stage.py scope
python scripts/run_stage.py silver
python scripts/run_stage.py gold
python scripts/run_stage.py ml
python scripts/run_stage.py semantic
python scripts/run_stage.py certify-release
python scripts/publish_artifacts.py

# Granular refresh stages (silver)
python scripts/run_stage.py silver-kind-refresh
python scripts/run_stage.py silver-legal-status-refresh
python scripts/run_stage.py silver-owner-refresh
python scripts/run_stage.py silver-oecd-refresh
python scripts/run_stage.py silver-history-refresh

# Granular gold stages
python scripts/run_stage.py gold-family-summary
python scripts/run_stage.py gold-family-metrics
python scripts/run_stage.py gold-history-blocking
python scripts/run_stage.py gold-portfolio
python scripts/run_stage.py gold-market-semantic

# ML stages
python scripts/run_stage.py ml-phase0-foundation
python scripts/run_stage.py ml-phase03-family-forecast

# Semantic stages
python scripts/run_stage.py semantic-abstract-phase-00
python scripts/run_stage.py semantic-claim-phase-00
python scripts/run_stage.py semantic-claim-phase-01
python scripts/run_stage.py semantic-ann

# OECD indicator stages
python scripts/run_stage.py build-oecd-indicator-seed
python scripts/run_stage.py build-oecd-indicator-cohort-stats
python scripts/run_stage.py build-oecd-indicator-longform
python scripts/run_stage.py build-oecd-indicator-bronze-projection

# Recovery (missed Azure Blob uploads)
python scripts/run_stage.py recover-tip-blob-uploads

# Tests
python -m pytest tests/ -v
python -m pytest tests/test_<name>.py -v   # single test file
```

---

## Backend Commands

```bash
cd backend
poetry install
poetry run uvicorn main:app --reload --port 8000
poetry run pytest tests/
```

---

## Prototype Commands

```bash
cd prototype
npm install
npm run dev   # http://localhost:5174 (or 5175)
npm run build
```

---

## ETL Architecture

**Data flow**: `Raw sources → Pre-Bronze → Bronze → Scope → Silver → Gold → ML / Semantic → Azure publish`

**Data layers** (under `etl/data/`):
- `raw/` — source files as-delivered
- `raw-bounded/` — bounded extracts from TIP (PATSTAT/Register/EPAB) and ODP (USPTO)
- `bronze/` — source-preserving Parquet (no schema changes)
- `silver/` — normalized analytical tables (core + enrichment)
- `gold/` — product marts queried by backend
- `ml/` — trained model artifacts and manifests
- `vectors/` — semantic embeddings and ANN indices

**Source adapters** (`etl/src/patentiq_etl/prebronze/`):
- PATSTAT / Register / EPAB → TIP client (chunked when `tip_chunked_export_enabled = true`)
- USPTO → ODP API (`prebronze-uspto-odp` stage)
- Refs → local files

**Stage tracking**: every stage writes to `etl/manifests/stages/<stage>.json` (result) and `etl/manifests/stats/<stage>.json` (row counts). Logs go to `etl/manifests/stages/<stage>.log`. All runs must also update `etl/ETL_IMPLEMENTATION_LOG.md`.

**Config**: `etl/conf/build.yaml` — controls scope (2007–2026 main, 1996–2006 heritage), snapshot date, source modes, chunking, and Azure upload tuning.

**Key source modules**:
- `etl/src/patentiq_etl/bronze/` — ingestion (structured, EPAB fulltext, USPTO)
- `etl/src/patentiq_etl/silver/build_core.py`, `build_enrichment.py`
- `etl/src/patentiq_etl/gold/build_gold.py`
- `etl/src/patentiq_etl/ml/phase0.py`, `phase03.py`
- `etl/src/patentiq_etl/semantic/`
- `etl/src/patentiq_etl/common/` — config, logging, manifest helpers, types

**SQL templates** live in `etl/sql/{bronze,silver,gold,checks}/`.

---

## Backend Architecture

Layered FastAPI service (`backend/`):
- `api/v1/` — route handlers (thin, delegate to services)
- `application/services/` — business logic
- `infrastructure/` — DuckDB queries, ML registry, caching, repositories
- `domain/` — Pydantic schemas and domain errors

Backend queries the gold/silver DuckDB tables produced by ETL.

---

## Domain Invariants

- **Family is the primary analytics unit** — never aggregate at publication level.
- **Bifurcated metrics**: Current Blocking Power (blue, enforceability) ≠ Historical Heritage (amber, citation influence). Never mix these two.
- **Scope**: 10 WIPO fields mega-cluster — always respect scope boundaries.
- **Trend locality**: LOCAL trend engine for enforceability metrics; GLOBAL trend engine for landscaping. Never mix in the same metric.
- **Point-in-time**: all legal/blocking metrics must support a configurable snapshot date.
- **Forecast content** must be labeled with a warning banner — never present as factual current data.

Full consistency rules (CR-01 through CR-30) are in `docs/new-feature-ideas/march-2026-family-legal-analytics-master-index.md`.

---

## Coding Conventions

**Python** (ETL, backend): 4-space indent, `snake_case` files/functions/variables, `PascalCase` classes, explicit typing on public interfaces.

**TypeScript/React** (frontend, prototype): strict TS, `PascalCase` components, `camelCase` variables/functions, `kebab-case` filenames.

**Commits**: Conventional Commits (`feat:`, `fix:`, `chore:`, `feat!:` for breaking changes). Branch flow: `dev` → `master` → `prod`; PRs to `master` must come from `dev`.

---

## Key Docs

| Topic | File |
|---|---|
| ETL runbook | `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md` |
| Metrics & guardrails | `docs/next-phase-v2/14-patentiq-v2-metrics-generation-flow-and-guardrails.md` |
| Semantic flow | `docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md` |
| DB schema & metric maps | `docs/next-phase-v2/12-patentiq-v2-database-structure-and-metric-maps.md` |
| Chunked TIP execution | `docs/next-phase-v2/28-patentiq-v2-tip-chunked-full-scope-execution-plan.md` |
| Heritage backfill policy | `docs/next-phase-v2/29-patentiq-v2-two-horizon-scope-and-heritage-backfill-policy.md` |
| Feature requirements index | `docs/new-feature-ideas/march-2026-family-legal-analytics-master-index.md` |

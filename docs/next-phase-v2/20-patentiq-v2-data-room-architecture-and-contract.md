# PatentIQ V2 Data Room Architecture And Contract

## Purpose

Define the implementation contract for the in-app `Data Room` so PatentIQ can expose:

1. source transparency,
2. warehouse lineage,
3. metric explainability,
4. model evidence,
5. semantic evidence,
6. downloadable read-only artifacts

without exposing raw cloud storage as the primary user interface.

## Core Product Role

The Data Room is the platform's:

1. evidence room,
2. methodology wiki,
3. artifact catalog,
4. reproducibility surface.

It should feel like a guided research room, not a bucket browser.

## Top-Level Information Architecture

The Data Room should expose these top-level sections:

1. `Overview`
2. `Sources`
3. `Pipeline`
4. `Datasets`
5. `Metrics`
6. `Models`
7. `Semantic`
8. `Manifests`

## Page Tree

### `Overview`

Should show:
1. active release id,
2. build date,
3. current scope and year range,
4. semantic sampling flag,
5. active model versions,
6. active vector/index versions,
7. top-level row-count summary.

### `Sources`

Per-source pages for:
1. PATSTAT,
2. PATSTAT Register,
3. USPTO full text,
4. EPAB,
5. OECD / WIPO / market references,
6. optional client-input layer where enabled.

### `Pipeline`

Sub-pages for:
1. Raw sources,
2. Bronze,
3. Silver,
4. Gold,
5. Models,
6. Semantic artifacts.

### `Datasets`

Searchable catalog of downloadable approved artifacts.

### `Metrics`

Wiki pages for major metric families.

### `Models`

Model cards and training/evaluation evidence.

### `Semantic`

Embedding, retrieval, and sampling documentation.

### `Manifests`

Release manifests, dataset pointers, checksums, and active artifact pointers.

## Wiki Page Template

Every Data Room wiki page should support these blocks:

1. `What It Is`
2. `Why It Exists`
3. `Scope`
4. `Inputs`
5. `Method`
6. `Outputs`
7. `Guardrails`
8. `Where It Appears In The App`
9. `Downloadable Artifacts`

## Read-Only Contract

The Data Room must be fully read-only for normal users and juries.

That means:

1. no edits to manifests,
2. no edits to warehouse files,
3. no hidden admin mutation endpoints,
4. downloads allowed only for approved artifacts.

## Backend Contract

The backend should expose a small read-only API surface for the Data Room.

### Required endpoints

1. `GET /api/v1/data-room/overview`
2. `GET /api/v1/data-room/catalog`
3. `GET /api/v1/data-room/catalog/{dataset_id}`
4. `GET /api/v1/data-room/schema/{dataset_id}`
5. `GET /api/v1/data-room/wiki/{page_id}`
6. `GET /api/v1/data-room/manifests`
7. `GET /api/v1/data-room/download/{dataset_id}`

### Endpoint behavior

1. endpoints must be read-only,
2. backend should read manifests/catalogs from Blob,
3. backend may issue controlled read-only download links,
4. backend should never expose unapproved temp artifacts.

## Dataset Catalog Contract

The backend should publish or hydrate a `data_catalog.json` manifest.

### Suggested schema

```json
{
  "release_id": "mvp-2026-03-15",
  "datasets": [
    {
      "dataset_id": "gold_family_blocking_power",
      "layer": "gold",
      "path": "gold/gold_family_blocking_power.parquet",
      "description": "Family-level blocking power mart",
      "row_count": 742381,
      "size_bytes": 18349211,
      "schema_ref": "schemas/gold_family_blocking_power.json",
      "downloadable": true,
      "scope_type": "mega_cluster_bounded",
      "semantic_sampling_flag": false
    }
  ]
}
```

## Blob Layout For The Data Room

The default MVP design should use a single authoritative artifact store, not two full duplicated warehouses.

### Single authoritative store

```text
patentiq-data/
  manifests/
    active_release.json
    active_models.json
    active_vectors.json
    data_catalog.json
  schemas/
  wiki/
  bronze/
  silver/
  gold/
  models/
  vectors/
  releases/
    mvp-2026-03-15/
      manifest.json
      pointers.json
  exports/
    approved-bundles/
```

### Data Room interpretation

The Data Room should primarily use:
1. `data_catalog.json` as the approved artifact registry,
2. `schemas/` for schema previews,
3. `wiki/` for methodology pages,
4. the same `bronze/`, `silver/`, `gold/`, `models/`, and `vectors/` paths for approved downloads.

Optional duplicate files should be created only for:
1. redacted copies,
2. contest handoff bundles,
3. explicit zip exports,
4. cases where access-control separation is required.

## Allowed Downloads

Recommended downloads:

1. approved Bronze Parquet outputs,
2. approved Silver Parquet outputs,
3. approved Gold marts,
4. model cards and metadata,
5. vector manifests and metadata,
6. schema files,
7. methodology docs.

Usually avoid direct download of:

1. temp build files,
2. local scratch outputs,
3. internal caches,
4. unapproved raw upstream dumps if licensing is unclear.

Default rule:
1. approved downloads should point to the single authoritative artifact store where possible,
2. duplicated export copies should be the exception, not the baseline design.

## Frontend Contract

### Suggested UI pattern

Use a left-nav + content-view workspace.

Primary surfaces:
1. summary cards,
2. wiki content panel,
3. dataset table,
4. schema preview panel,
5. download action panel.

### Suggested tabs

1. `Wiki`
2. `Catalog`
3. `Downloads`

## Relationship To Existing V2 Docs

This document operationalizes:

1. [10-patentiq-v2-bronze-silver-gold-knowledge-tree.md](./10-patentiq-v2-bronze-silver-gold-knowledge-tree.md)
2. [11-patentiq-v2-metric-lineage-catalog.md](./11-patentiq-v2-metric-lineage-catalog.md)
3. [14-patentiq-v2-metrics-generation-flow-and-guardrails.md](./14-patentiq-v2-metrics-generation-flow-and-guardrails.md)
4. [15-patentiq-v2-prediction-training-flow-and-guardrails.md](./15-patentiq-v2-prediction-training-flow-and-guardrails.md)
5. [16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md](./16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md)
6. [17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md](./17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md)

## Delivery Priority

### P0

1. Overview
2. Sources
3. Pipeline
4. Datasets
5. Manifests

### P1

1. Metrics wiki
2. Models room
3. Semantic room
4. controlled downloads

### P2

1. richer search/filter
2. release diff views
3. comparative artifact views

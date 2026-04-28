# PatentIQ V2 Data Room Page Contract

## Purpose

Define the concrete page contract for the `Data Room` workspace so it becomes an auditable in-app research room built from live artifacts, manifests, schemas, and methodology pages.

This note operationalizes:

1. [20-patentiq-v2-data-room-architecture-and-contract.md](../20-patentiq-v2-data-room-architecture-and-contract.md)
2. [22-patentiq-v2-backend-frontend-application-architecture.md](../22-patentiq-v2-backend-frontend-application-architecture.md)
3. [23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md](../23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md)
4. [patentiq-v2-page-ideas.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/patentiq-v2-page-ideas.md)

## Primary Question

`What data, methods, metrics, models, and semantic artifacts power the current PatentIQ release, and how can the user verify them?`

## Product Role

The Data Room is:

1. evidence room,
2. methodology wiki,
3. approved artifact catalog,
4. release reproducibility surface.

It is not:

1. a storage browser,
2. an engineering admin console,
3. a mutable settings workspace.

## Actual Data Inputs

## Manifests and release artifacts

1. stage manifests under [etl/manifests/stages](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stages)
2. stats snapshots under [etl/manifests/stats](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/manifests/stats)
3. model and vector metadata under:
   - [etl/data/ml](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/ml)
   - [etl/data/vectors](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/vectors)

## Approved datasets to expose

Examples of high-value catalog entries:

1. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
2. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
3. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
4. [gold_market_intelligence_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_segments.parquet)
5. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
6. approved Silver marts
7. approved model cards
8. vector manifests and index manifests

## Methodology content

Sources:

1. `docs/next-phase-v2`
2. `docs/new-feature-ideas`
3. approved wiki-style note set exported by backend

## Page Layout

Use a persistent left navigation with a content pane and contextual right rail.

On desktop:

1. left navigation for sections,
2. main content pane for wiki/catalog,
3. right rail for release badges, downloads, and schema preview.

On mobile:

1. left navigation becomes slide-over,
2. right rail becomes stacked panels under the content.

## Section Order

1. `Overview`
2. `Sources`
3. `Pipeline`
4. `Datasets`
5. `Metrics`
6. `Models`
7. `Semantic`
8. `Manifests`

## Component Contract

## 1. `DataRoomOverviewHero`

Purpose:

1. summarize the active release,
2. make current scope obvious,
3. surface integrity and freshness.

Display:

1. release id
2. snapshot date
3. scope badges
4. active model versions
5. active semantic runtime/version
6. top row-count summary for Bronze/Silver/Gold/ML/Vector layers

Best representation:

1. compact hero cards plus a small release metadata strip

## 2. `DataRoomNavigationTree`

Purpose:

1. make the Data Room feel like a research workspace,
2. allow deep reading without losing orientation.

Nodes:

1. Overview
2. Sources
3. Pipeline
4. Datasets
5. Metrics
6. Models
7. Semantic
8. Manifests

## 3. `DatasetCatalogTable`

Best representation:

1. searchable, filterable, paginated table

Columns:

1. dataset id
2. layer
3. description
4. row count
5. scope type
6. downloadable flag
7. freshness / release badge

Why table:

1. the catalog is factual and scan-heavy,
2. users need sortable row-count and layer views,
3. downloadability and scope must be visible in one place.

## 4. `DatasetSchemaPreview`

Best representation:

1. side-panel or drawer showing:
   - field name
   - type
   - meaning note
   - example value

This should feel like a compact warehouse browser, not a raw JSON dump.

## 5. `PipelineLineageView`

Best representation:

1. stepper or layered swimlane view:
   - sources
   - Bronze
   - Silver
   - Gold
   - models
   - vectors

Each layer card should include:

1. what it does,
2. key artifacts,
3. links to methodology,
4. stage status badges.

## 6. `WikiArticleView`

Use the same template for Metrics, Models, Semantic, and Sources pages.

Required blocks:

1. `What It Is`
2. `Why It Exists`
3. `Scope`
4. `Inputs`
5. `Method`
6. `Outputs`
7. `Guardrails`
8. `Where It Appears In The App`
9. `Downloadable Artifacts`

## 7. `ModelCardGallery`

Best representation:

1. cards for each promoted model family

Each card shows:

1. model scope
2. prediction unit
3. training snapshot
4. primary metrics
5. calibration status
6. release status
7. link to full card

## 8. `SemanticMethodCard`

Required content:

1. abstract model id/version
2. claim model id/version
3. vector-space policy
4. sampling policy
5. ANN policy
6. caveats about claim coverage and abstract fallback

## 9. `ManifestViewer`

Best representation:

1. prettified JSON viewer with badges and checksum blocks

Supported manifests:

1. stage manifests
2. stats manifests
3. vector manifests
4. training snapshot manifest
5. active release pointers

## Backend Contract

## Overview endpoint

`GET /api/v1/data-room/overview`

Returns:

1. release metadata
2. scope summary
3. promoted model/vector summary
4. top-level row-count cards

## Section endpoints

1. `GET /api/v1/data-room/catalog`
2. `GET /api/v1/data-room/catalog/{dataset_id}`
3. `GET /api/v1/data-room/schema/{dataset_id}`
4. `GET /api/v1/data-room/wiki/{page_id}`
5. `GET /api/v1/data-room/manifests`
6. `GET /api/v1/data-room/download/{dataset_id}`

## Representation Rules

1. No raw storage path should be the primary UX.
2. Downloads must be approved and read-only.
3. Temp files and scratch outputs must never appear in normal catalog results.
4. Schema previews should be human-readable, not backend-internal only.
5. Every model and semantic card must show caveats.

## Degraded Mode

If full wiki/catalog generation is not ready:

1. keep `Overview`, `Datasets`, and `Manifests`,
2. expose methodology pages from existing markdown notes,
3. hide unsupported deep schema examples rather than rendering broken placeholders.

## Best Visual Language

Recommended direction:

1. library / dossier aesthetic,
2. dense but calm layout,
3. emphasis on verification over ornament,
4. clear evidence badges and scope chips,
5. avoid dashboard-style score clutter.

## UI-Hub Alignment

This page should stay mostly flat.

Good uses:

1. subtle section transitions,
2. polished dossier-style navigation,
3. lightweight motion for opening schema previews and manifest panels.

Avoid:

1. heavy 3D treatment,
2. cinematic transitions that slow reading,
3. decorative dashboard effects on factual catalog tables.

The page should feel like:

1. a guided research room,
2. a methodology library,
3. a reproducibility dossier,

not a product-marketing scene.

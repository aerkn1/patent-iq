# PatentIQ V2 Storage Sizing Estimate

## Purpose

Provide a practical storage-sizing estimate for the PatentIQ V2 warehouse and sidecars under the bounded `10-field mega-cluster` MVP scope.

This note is intended for:

1. infrastructure planning,
2. local and shared environment sizing,
3. deciding whether raw USPTO / EPAB long text should be retained in the analytical store,
4. understanding the storage impact of sampled versus full semantic embeddings.

It is a planning estimate, not a measured production bill.

## Source Anchors

This estimate is anchored to:

1. [mega-cluster-dataset-scope-and-boundary-governance-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/mega-cluster-dataset-scope-and-boundary-governance-requirements.md)
2. [17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md](./17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md)
3. [10-patentiq-v2-bronze-silver-gold-knowledge-tree.md](./10-patentiq-v2-bronze-silver-gold-knowledge-tree.md)
4. [13-patentiq-v2-cross-layer-dbdiagram.dbml](./13-patentiq-v2-cross-layer-dbdiagram.dbml)
5. [14-patentiq-v2-metrics-generation-flow-and-guardrails.md](./14-patentiq-v2-metrics-generation-flow-and-guardrails.md)
6. [16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md](./16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md)
7. [08-citation-forecast-model-v2-retraining-report.md](./08-citation-forecast-model-v2-retraining-report.md)
8. [data_validation.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/data/data_validation.md)
9. [databases.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/data/databases.md)
10. [data_requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/data/data_requirements.md)

## Core Scope Assumption

The estimate assumes:

1. PatentIQ MVP remains bounded to the selected 10 WIPO mega-cluster fields,
2. the in-scope family universe lands in the rough range of `~0.5M` to `~1.0M` families,
3. the semantic layer remains sampled for MVP at roughly `5%` to `10%` of eligible active-grant families,
4. PATSTAT Register remains an EP-only overlay,
5. ghost nodes remain sparse stubs rather than full copied families,
6. Parquet remains the authoritative analytical storage layer,
7. DuckDB, vector indexes, and model artifacts are treated as additional working/storage overhead.

Current operating note:
1. if USPTO full text remains unavailable, the active semantic MVP should assume EPAB claims plus PATSTAT abstract fallback,
2. this lowers text-retention and claim-space storage pressure relative to the original full-source semantic plan.

## Why The Estimate Is A Range

The range is intentionally broad because storage will move materially based on:

1. whether Bronze retains only the fields needed for analytics or full source-preserving raw payloads,
2. whether USPTO and EPAB retain only claims and abstracts or also full descriptions,
3. how many point-in-time snapshots are retained,
4. whether vector embeddings stay sampled or expand to full corpus,
5. whether environments duplicate Parquet, DuckDB working files, and vector indexes locally.

## Legacy Versus V2 Scale

Older repository planning notes include smaller, earlier-scope estimates such as:

1. `~500K` patents / families,
2. `~5M` citation records,
3. total analytical Parquet in the sub-GB range for a much narrower EPO-centric slice.

Those older estimates are useful as a lower anchor, but they do **not** include the current V2 scope with:

1. family-first global mega-cluster extraction,
2. richer Silver and Gold marts,
3. PATSTAT Register overlays,
4. sampled semantic embeddings,
5. EPAB full-text support and optional USPTO availability.

## Scenario Anchors

Use these three planning scenarios:

| Scenario | In-Scope Families | Interpretation |
|---|---:|---|
| Low | `~500K` | conservative bounded extraction |
| Base | `~750K` | most practical planning scenario |
| High | `~1.0M` | upper MVP planning envelope |

These family counts imply, approximately:

| Derived Volume | Low | Base | High |
|---|---:|---:|---:|
| family-member publications | `~2.0M` | `~3.5M` | `~5.5M` |
| citation edges kept for bounded analytics | `~5M` | `~9M` | `~15M` |
| legal-event rows in scope | `~2M` | `~4M` | `~8M` |
| CPC / IPC rows | `~3M` | `~5M` | `~8M` |
| eligible sampled semantic families | `~25K-50K` | `~40K-75K` | `~50K-100K` |

These are planning heuristics only. They are sufficient for infrastructure budgeting.

## Storage Surfaces

PatentIQ should be budgeted across four separate storage surfaces:

1. `authoritative Parquet lake`
2. `DuckDB working database and temp files`
3. `vector store / ANN indexes`
4. `model artifacts, manifests, and evaluation outputs`

The authoritative Parquet lake is the primary sizing baseline. Everything else is overhead on top.

## Estimated Storage By Layer

### Lean MVP

Lean MVP assumes:

1. Bronze stores raw PATSTAT / Register faithfully,
2. EPAB Bronze plus optional USPTO Bronze stores the semantic text path needed for claims and abstracts,
3. full long descriptions are **not** broadly materialized into the analytical layer,
4. vectors stay sampled.

| Layer / Table Group | Low | Base | High |
|---|---:|---:|---:|
| Bronze PATSTAT bounded slice | `8 GB` | `15 GB` | `25 GB` |
| Bronze PATSTAT Register overlay | `0.5 GB` | `1.5 GB` | `4 GB` |
| Bronze EPAB text providers plus optional USPTO text providers, claims + abstracts + bridge metadata | `1.5 GB` | `4 GB` | `8 GB` |
| Silver core normalization tables | `4 GB` | `8 GB` | `15 GB` |
| Silver citation / coverage / trend / OECD / forecast tables | `4 GB` | `8 GB` | `15 GB` |
| Gold marts and timeseries | `1.5 GB` | `3 GB` | `6 GB` |
| ML feature tables and model artifacts | `0.5 GB` | `1.5 GB` | `4 GB` |
| Sampled vector store + ANN index | `0.5 GB` | `1.5 GB` | `3 GB` |
| **Total Lean MVP** | **`21 GB`** | **`43.5 GB`** | **`82 GB`** |

### Full-Text-Heavy MVP

This variant assumes Bronze also retains large raw description payloads from USPTO and EPAB more aggressively.

| Additional Full-Text Retention | Low | Base | High |
|---|---:|---:|---:|
| raw descriptions / rich text payloads / large XML-derived text bodies | `12 GB` | `25 GB` | `50 GB` |

| Total With Heavy Raw Text | Low | Base | High |
|---|---:|---:|---:|
| Lean MVP subtotal | `21 GB` | `43.5 GB` | `82 GB` |
| heavy raw text add-on | `12 GB` | `25 GB` | `50 GB` |
| **Total Full-Text-Heavy MVP** | **`33 GB`** | **`68.5 GB`** | **`132 GB`** |

## Recommended Planning Numbers

For actual infrastructure budgeting, use these planning numbers:

### Authoritative analytical storage

1. `minimum serious budget`: `50 GB`
2. `recommended MVP budget`: `80 GB` to `120 GB`
3. `safe budget with raw text retained`: `120 GB` to `150 GB`

### With DuckDB working copies and temp overhead

If one environment keeps:

1. Parquet lake,
2. local DuckDB materializations,
3. temp sort / join spill space,
4. sampled vector indexes,

then plan for:

1. `working environment reserve`: `100 GB` to `150 GB`

### With snapshots and rebuild headroom

If you retain:

1. one current snapshot,
2. one prior snapshot,
3. rebuild scratch space,

then plan for:

1. `shared environment reserve`: `150 GB` to `250 GB`

## Table-Group Interpretation

### Bronze PATSTAT bounded slice

This bucket covers:

1. applications,
2. publications,
3. citations,
4. NPL,
5. classifications,
6. legal events,
7. family links.

This remains the largest non-text storage driver.

### Bronze PATSTAT Register

This bucket is meaningful but not dominant.

It remains comparatively small because:

1. it is EP-only,
2. it is a read-only overlay,
3. it does not become a new cross-office analytical spine.

### Bronze USPTO / EPAB full text

This bucket is the most variable.

If you retain only:

1. claim text,
2. abstract text,
3. bridging metadata,

the cost is moderate.

If you also retain:

1. full description text,
2. richer embedded raw bodies,
3. duplicated XML-derived artifacts,

the cost rises sharply.

### Silver tables

Silver is not as small as it first appears because it contains:

1. family core,
2. family-publication bridge,
3. field mappings,
4. cleaned citation edges,
5. enriched citation network,
6. point-in-time legal snapshots,
7. branch enforceability,
8. trend engines,
9. forecast tables,
10. representative family text.

### Gold marts

Gold remains relatively small because:

1. it is aggregated,
2. it is family- and portfolio-facing,
3. it stores output marts rather than raw graph detail.

The main Gold growth drivers are:

1. time-series snapshots,
2. field timeseries,
3. portfolio timeseries,
4. semantic match context if persisted broadly.

### Vector storage

Vector storage is small in sampled MVP and becomes meaningful only later.

Approximate rule:

1. sampled MVP vectors are usually low-single-digit GB,
2. full-corpus vectors plus ANN indexes can quickly become `5 GB` to `20+ GB`.

## What Is Not Included

These estimates do **not** include:

1. the full raw global PATSTAT delivery footprint,
2. archival copies of every source release,
3. large observability / logging retention,
4. object-store replication overhead,
5. CI artifact retention,
6. container image storage.

For reference, the full upstream PATSTAT universe is far larger than the bounded MVP warehouse and should be treated separately.

## Most Important Design Levers

If storage starts to drift above the target, the highest-leverage controls are:

1. keep semantic vectors sampled in MVP,
2. store only the text required for representative claim / abstract generation in the analytical spine,
3. avoid duplicating full descriptions into Silver or Gold,
4. do not materialize unnecessary point-in-time snapshots,
5. keep ghost nodes as stubs rather than full family objects,
6. compress Parquet aggressively and co-sort by key analytical columns.

## Practical Recommendation

For PatentIQ V2 MVP, the safest single-number recommendation is:

`budget 120 GB per serious environment`

That is enough room for:

1. the bounded mega-cluster warehouse,
2. PATSTAT Register overlays,
3. sampled semantic embeddings,
4. USPTO / EPAB text retention,
5. rebuild and temp headroom.

If you expect:

1. heavy raw-description retention,
2. duplicate local materializations,
3. more than one active snapshot,

then budget:

`150 GB to 250 GB`

## Short Answer

For the current PatentIQ V2 architecture and 10-field mega-cluster scope:

1. expect roughly `40 GB` to `80 GB` for a healthy lean MVP warehouse,
2. expect roughly `70 GB` to `130 GB` if you retain raw USPTO / EPAB long text more aggressively,
3. reserve around `120 GB` for a serious single environment,
4. reserve `150 GB` to `250 GB` if you want comfortable rebuild and snapshot headroom.

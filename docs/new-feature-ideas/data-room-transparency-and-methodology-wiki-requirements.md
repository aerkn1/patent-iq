# Data Room Transparency And Methodology Wiki Requirements

## Source

User-provided implementation guidance captured on March 15, 2026.

## Purpose

Define the in-app `Data Room` contract for PatentIQ so juries, evaluators, and advanced users can inspect the data, methodology, model evidence, and semantic evidence used by the platform in a read-only and downloadable form.

## Core Principle

The Data Room should act as the platform's:

1. transparency layer,
2. reproducibility layer,
3. methodology wiki,
4. downloadable evidence room.

It must not be a loose file dump without structure or explanations.

## DRW-01: The App Should Include A Dedicated In-App Data Room

Requirement:
PatentIQ should expose a first-class in-app `Data Room` page or workspace rather than forcing users to browse cloud storage directly.

Rationale:
1. preserves a polished contest experience,
2. keeps all evidence inside the product narrative,
3. allows controlled read-only access with explanations and caveats.

## DRW-02: The Data Room Must Be Read-Only

Requirement:
All Data Room content must be viewable and downloadable, but not editable through the app by normal users or juries.

Implications:
1. no write operations to shared warehouse artifacts,
2. no mutation of released manifests,
3. no implicit admin tooling mixed into the evidence room.

## DRW-03: The Data Room Must Expose The Full Raw-To-Gold Story

Requirement:
The Data Room should let users inspect how PatentIQ moves from source data to platform outputs.

Minimum pipeline visibility:
1. source systems,
2. Bronze outputs,
3. Silver outputs,
4. Gold marts,
5. model artifacts,
6. semantic/vector artifacts.

## DRW-04: The Data Room Must Include Wiki-Style Methodology Pages

Requirement:
Each major sub-room should include wiki-style explanatory pages describing:
1. what the data or metric is,
2. where it comes from,
3. how it is transformed,
4. what guardrails apply,
5. what the scope limitations are,
6. where it appears in the product.

## DRW-05: The Data Room Must Be Organized Into Sub-Rooms

Requirement:
The Data Room should include at least these sub-rooms:
1. `Overview`
2. `Sources`
3. `Pipeline`
4. `Datasets`
5. `Metrics`
6. `Models`
7. `Semantic`
8. `Manifests`

## DRW-06: Overview Must Show The Active Release And Scope

Requirement:
The `Overview` room should show:
1. active release id,
2. build date,
3. source snapshot dates,
4. scope definition such as 10-field mega-cluster,
5. semantic sampling status,
6. active model versions,
7. active vector/index versions,
8. headline family/publication/citation counts.

## DRW-07: Sources Room Must Explain Every Upstream Source

Requirement:
The `Sources` room should provide per-source wiki pages for:
1. PATSTAT,
2. PATSTAT Register,
3. USPTO full text,
4. EPAB,
5. OECD / WIPO / market reference inputs,
6. optional client-provided data if enabled.

Each page should explain:
1. what the source is,
2. what fields/tables are used,
3. what role it plays,
4. what is not used,
5. any scope or licensing caveats,
6. whether the source is active, degraded, or absent in the current release.

## DRW-08: Pipeline Room Must Explain Bronze, Silver, And Gold

Requirement:
The `Pipeline` room should show the end-to-end transformation path:

`Raw -> Bronze -> Silver -> Gold -> Models / Semantic`

For each layer it should explain:
1. intended purpose,
2. example tables,
3. allowed logic,
4. forbidden logic,
5. downstream dependencies.

## DRW-09: Datasets Room Must Be A Read-Only Catalog

Requirement:
The `Datasets` room should expose a searchable, filterable catalog of approved downloadable artifacts.

Minimum dataset metadata:
1. dataset name,
2. layer,
3. description,
4. row count,
5. size,
6. schema link,
7. manifest/build version,
8. download link.

## DRW-10: Metrics Room Must Explain Metric Derivation

Requirement:
The `Metrics` room should include wiki pages for the major score and analytic families, including at least:
1. blocking power,
2. overall legal enforceability,
3. citation impact,
4. heritage,
5. OECD metrics,
6. weighted reach,
7. coverage stability,
8. tech breadth.

Each metric page should show:
1. definition,
2. input tables,
3. formula role,
4. scope caveats,
5. UI usage.

## DRW-11: Models Room Must Explain Prediction Training And Safety

Requirement:
The `Models` room should expose model cards and training evidence for all prediction scopes used in MVP.

Each model page should show:
1. target definition,
2. training grain,
3. feature tables,
4. model type,
5. calibration method,
6. evaluation metrics,
7. safe-for-MVP conditions,
8. limitations,
9. downloadable artifacts or metadata where appropriate.

## DRW-12: Semantic Room Must Explain Embeddings And Retrieval

Requirement:
The `Semantic` room should explain:
1. representative text hierarchy,
2. source selection rules,
3. claim versus abstract vector spaces,
4. embedding model/version,
5. ANN/index method,
6. chronology/legal gating,
7. semantic sampling policy,
8. fallback flags such as `is_abstract_fallback`,
9. current corpus coverage by text provenance,
10. whether USPTO full text is absent from the current semantic build.

## DRW-13: Manifests Room Must Expose Active Artifact Pointers

Requirement:
The `Manifests` room should expose read-only build and release manifests, including:
1. active data release manifest,
2. active model manifest,
3. active vector manifest,
4. checksums,
5. row counts,
6. build versions,
7. scope metadata.

## DRW-14: Downloads Must Be Approved And Scope-Labeled

Requirement:
The Data Room should expose downloads only for approved artifacts, with clear labels indicating:
1. whether the file is Bronze, Silver, Gold, Model, or Vector,
2. whether the artifact is bounded to the mega-cluster,
3. whether the semantic layer is sampled,
4. whether ghost nodes influenced related citation outputs.

## DRW-15: The Data Room Must Not Rely On Raw Cloud Storage Browsing

Requirement:
Users should not need direct blob-container browsing to understand the platform.

Implementation preference:
1. backend serves a read-only catalog API,
2. frontend renders the Data Room from manifests and schemas,
3. downloads may use controlled read-only links under backend mediation.

## DRW-15A: The Data Room Should Prefer A Single Artifact Store Over Duplicated Blobs

Requirement:
The Data Room should, by default, reference approved artifacts from the same primary Blob or ADLS artifact store used by the application.

Preferred pattern:
1. one authoritative artifact store for Bronze, Silver, Gold, models, vectors, and manifests,
2. one Data Room catalog and wiki layer that points to approved files in that same store,
3. optional duplicate bundles only for explicitly approved export packages, redacted copies, or contest-specific handoff archives.

The Data Room should not require full warehouse duplication unless there is a clear access-control or redaction reason.

## DRW-16: Wiki Pages Should Use A Standard Template

Requirement:
Every wiki-style Data Room page should use a consistent structure:
1. `What It Is`
2. `Why It Exists`
3. `Scope`
4. `Inputs`
5. `Method`
6. `Outputs`
7. `Guardrails`
8. `Where It Appears In The App`
9. `Downloadable Artifacts`

## DRW-17: The Data Room Must Keep Product Claims Auditable

Requirement:
Any major product claim shown in demos or reports should be traceable through the Data Room to:
1. source lineage,
2. metric methodology,
3. model evidence where predictive,
4. semantic retrieval evidence where embedding-driven.

## Relationship To Existing Notes

This note extends and operationalizes:
1. `predictive-signals-and-interpretable-forecasting-requirements.md`
2. `semantic-similarity-and-vector-layer-requirements.md`
3. `mega-cluster-dataset-scope-and-boundary-governance-requirements.md`
4. `patstat-methodology-compliance-requirements.md`
5. `client-provided-data-financial-intelligence-requirements.md`

## Delivery Priority

### P0

1. Data Room page exists in-app,
2. read-only dataset catalog exists,
3. pipeline and metric wiki pages exist,
4. manifests are exposed,
5. scope metadata is visible.

### P1

1. full model cards and semantic cards,
2. downloadable approved artifacts,
3. schema previews and sample rows.

### P2

1. richer search/filter inside the Data Room,
2. comparative release diff views,
3. richer downloadable bundles.

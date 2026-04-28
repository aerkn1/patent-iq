# Section 00. Business Definition, Scope, And Evaluation Lens

## Table Of Contents

1. [Purpose Of This Section](#purpose-of-this-section)
2. [Executive Definition Of PatentIQ](#executive-definition-of-patentiq)
3. [The Business Problem PatentIQ Solves](#the-business-problem-patentiq-solves)
4. [The Decisions PatentIQ Is Designed To Support](#the-decisions-patentiq-is-designed-to-support)
5. [Who The Product Is For](#who-the-product-is-for)
6. [Current Product Baseline](#current-product-baseline)
7. [Scope Coverage Summary](#scope-coverage-summary)
8. [Why The Scope Is Intentionally Bounded](#why-the-scope-is-intentionally-bounded)
   - [1. The project is meant to be a coherent intelligence platform, not a loose widget set](#1-the-project-is-meant-to-be-a-coherent-intelligence-platform-not-a-loose-widget-set)
   - [2. The patent family is the main economic and analytical unit](#2-the-patent-family-is-the-main-economic-and-analytical-unit)
   - [3. The MVP is a bounded mega-cluster, not a universal global estate](#3-the-mvp-is-a-bounded-mega-cluster-not-a-universal-global-estate)
   - [4. Current-state analytics and deep history are separated on purpose](#4-current-state-analytics-and-deep-history-are-separated-on-purpose)
   - [5. Source breadth is selective rather than indiscriminate](#5-source-breadth-is-selective-rather-than-indiscriminate)
   - [6. Semantic search is intentionally sampled and grant-focused in MVP](#6-semantic-search-is-intentionally-sampled-and-grant-focused-in-mvp)
   - [7. Transparency is part of the product, not an afterthought](#7-transparency-is-part-of-the-product-not-an-afterthought)
9. [In-Scope Coverage](#in-scope-coverage)
10. [What Is Explicitly Out Of Scope Or Deferred](#what-is-explicitly-out-of-scope-or-deferred)
11. [Interpretation Rules](#interpretation-rules)
12. [How To Read The Rest Of This Dossier](#how-to-read-the-rest-of-this-dossier)
13. [Key Takeaways](#key-takeaways)

## Purpose Of This Section

This opening section explains what PatentIQ is in business terms, what problem it is actually solving, why the current release is deliberately bounded, and how the rest of the technical dossier should be interpreted.

That framing is necessary because PatentIQ should not be judged as:

1. a generic patent search website,
2. an unrestricted mirror of the global patent system,
3. a collection of disconnected charts,
4. an opaque machine-learning demo.

It should be judged as a bounded, evidence-oriented patent intelligence platform whose purpose is to convert large upstream patent datasets into explainable family, portfolio, market, comparison, and forecast decisions.

Where this section explains why a scope boundary exists, that rationale is either directly documented in the V2 notes or is a clearly stated business interpretation of the implemented repository shape.

Primary implementation references:

1. `etl/README.md:1-18`
2. `docs/next-phase-v2/01-scope-and-release-definitions.md:3-138`
3. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md:17-171`
4. `etl/conf/build.yaml:1-95`
5. `etl/conf/scope.yaml:1-14`

## Executive Definition Of PatentIQ

At the highest level, PatentIQ is a patent intelligence system for turning raw patent, legal, text, and reference data into decision-ready analysis.

The original product vision describes PatentIQ as an AI-powered patent intelligence platform combining technical, legal, financial, and predictive dimensions with licensing-oriented insight. That broader business ambition remains useful context, but the current documented V2 runtime is narrower and more concrete: it focuses on the contest-critical intelligence core that is actually implemented in the repository.

That current V2 core is:

1. family-first patent intelligence,
2. harmonized owner and portfolio intelligence,
3. market and trend intelligence over a bounded technology universe,
4. evidence-first publication drilldown,
5. compare workflows,
6. forecast and semantic augmentation,
7. transparency, caveat, and release metadata.

Implementation references:

1. `docs/project/main_project.md:15-30`
2. `docs/next-phase-v2/01-scope-and-release-definitions.md:7-43`
3. `backend_v2/README.md:3-21`
4. `frontend_v2/README.md:5-18`

## The Business Problem PatentIQ Solves

Patent data is abundant, but decision-ready patent intelligence is not. Raw patent systems are strong at storage and retrieval, but weak at giving a fast, trustworthy answer to questions such as:

1. Which families actually matter in this technology space?
2. What does a company's strategically relevant in-scope portfolio look like?
3. Where is the market or filing momentum moving?
4. Which families are influential, durable, risky, or weakening?
5. How should citations, legal state, market reach, and quality signals be read together rather than separately?
6. Which similar assets should an analyst inspect next?

PatentIQ addresses that problem by creating one bounded analytical environment where:

1. the patent family is the anchor object,
2. owner rollups are harmonized,
3. legal and citation evidence are replayed into consistent contracts,
4. market and quality indicators are derived in a traceable way,
5. machine-learning outputs are attached only after the warehouse logic is stable,
6. the UI consumes page-shaped contracts instead of rebuilding analytics ad hoc.

This is the practical difference between a dataset and an intelligence product. A dataset stores facts. PatentIQ is designed to connect those facts into an auditable decision surface.

## The Decisions PatentIQ Is Designed To Support

The current contest-oriented scope is designed to support a specific class of business and analytical decisions:

1. single-family evaluation,
2. owner portfolio assessment inside the bounded technology universe,
3. competitor and peer comparison,
4. market and field trend interpretation,
5. evidence-backed publication review,
6. predictive prioritization,
7. semantic discovery and similarity-led exploration.

The scope note describes these as product workflows rather than isolated metrics. That distinction matters. The product is not trying to prove that it can calculate one score. It is trying to prove that it can support a complete reasoning workflow from source data to analyst-facing conclusion.

Implementation references:

1. `docs/next-phase-v2/01-scope-and-release-definitions.md:17-43`
2. `docs/next-phase-v2/01-scope-and-release-definitions.md:58-127`
3. `frontend_v2/README.md:7-18`
4. `backend_v2/README.md:13-21`

## Who The Product Is For

The older PRD identifies four primary user groups:

1. IP portfolio managers,
2. patent attorneys,
3. technology transfer offices,
4. IP investors.

That user framing is still directionally valid, but the currently implemented V2 runtime is most directly aligned with the first and fourth decision patterns:

1. evaluating the strength and composition of in-scope family portfolios,
2. comparing owners and market positions,
3. understanding evidence behind family-level and publication-level claims,
4. using forecast and semantic signals as prioritization support rather than as autonomous judgment.

In business terms, PatentIQ is best understood as an analyst acceleration product. It reduces the amount of manual stitching required between family data, legal data, market proxies, text evidence, and model outputs.

Implementation references:

1. `docs/project/main_project.md:24-30`
2. `docs/project/main_project.md:63-143`
3. `docs/next-phase-v2/01-scope-and-release-definitions.md:17-43`

## Current Product Baseline

The current implementation baseline is the V2 stack:

1. `etl/` for source extraction, bounded raw data, Bronze, Silver, Gold, ML, vectors, and serving packaging,
2. `backend_v2/` for page-shaped API contracts,
3. `frontend_v2/` for the workspace-first UI.

This point is operational, not cosmetic. Reading a different stack as canonical would distort both the architecture and the implementation status.

Implementation references:

1. `etl/README.md:1-18`
2. `backend_v2/README.md:3-21`
3. `frontend_v2/README.md:5-18`

## Scope Coverage Summary

The current implemented business scope can be summarized as follows:

| Scope dimension | Current implemented boundary | Why this boundary exists |
| --- | --- | --- |
| Product baseline | `etl/` + `backend_v2/` + `frontend_v2/` | keeps the documentation aligned to the live V2 architecture |
| Canonical asset unit | patent family first, with publication drilldown | avoids treating jurisdictional publication fragments as independent strategic assets |
| Portfolio meaning | harmonized owner's in-scope mega-cluster families | prevents the UI from implying a universal worldwide estate that the MVP does not ingest |
| Technology universe | 10 selected WIPO fields defined in `etl/conf/scope.yaml` | creates a bounded but still strategically dense technology environment |
| Time universe | main window `2007-2026`, heritage backfill `1996-2006` | separates current-state product analytics from historical support logic |
| Source systems | PATSTAT, PATSTAT Register, EPAB, and local reference files | provides bibliographic, legal, publication-text, and enrichment coverage without uncontrolled source sprawl |
| Semantic universe | `10%` vector sample, active grants only | proves discovery and comparison workflows without full-mega-cluster embedding cost |
| Delivery model | workspace-first frontend over page-shaped backend contracts | turns analytics into user-readable decisions rather than raw table exposure |
| Transparency model | caveat metadata, scope metadata, manifests, and methodology disclosures | makes claims auditable and traceable across the stack |

The authoritative live field list is the one enforced by the ETL scope config and source-certification test:

1. Audio-visual technology
2. Telecommunications
3. Digital communication
4. Basic communication processes
5. Computer technology
6. IT methods for management
7. Semiconductors
8. Measurement
9. Control
10. Electrical machinery, apparatus, energy

Implementation references:

1. `etl/conf/scope.yaml:1-14`
2. `etl/conf/build.yaml:1-12`
3. `etl/conf/build.yaml:22-42`
4. `etl/conf/build.yaml:92-95`
5. `etl/tests/test_source_certification.py:8-24`
6. `etl/src/patentiq_etl/common/config.py:36-49`

## Why The Scope Is Intentionally Bounded

The bounded scope is not a weakness or an omission. It is a design choice that makes the product technically defensible and business-legible.

### 1. The project is meant to be a coherent intelligence platform, not a loose widget set

The release goal note is explicit: the objective is to ship a coherent intelligence platform rather than a loose collection of analytics widgets.

That means the documentation should emphasize cross-layer consistency:

1. the same family-first logic in ETL, backend, and frontend,
2. the same scope boundary in portfolio, market, compare, and semantic views,
3. the same caveat discipline in metrics, model outputs, and evidence pages.

Implementation references:

1. `docs/next-phase-v2/01-scope-and-release-definitions.md:3-16`
2. `backend_v2/README.md:5-12`
3. `frontend_v2/README.md:5-18`

### 2. The patent family is the main economic and analytical unit

The V2 scope and cluster definitions place family-first counting and ranking at the center of the product.

Business rationale:

1. a single invention is often represented by many publication records across offices and stages,
2. strategic ownership, legal reach, and citation influence are more meaningful at family level than at isolated publication level,
3. portfolio decisions become misleading if publication duplicates are treated as separate core assets.

Publication-level detail is still essential, but it is used as evidence and drilldown, not as the default strategic denominator.

Implementation references:

1. `docs/next-phase-v2/01-scope-and-release-definitions.md:9-16`
2. `docs/next-phase-v2/01-scope-and-release-definitions.md:60-69`
3. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md:39-45`

### 3. The MVP is a bounded mega-cluster, not a universal global estate

One of the most important interpretation rules in the entire project is that PatentIQ MVP does not operate on a universal global patent estate.

It operates on a bounded 10-field mega-cluster family universe, and portfolios mean the harmonized owner's family set within that in-scope universe.

Business rationale:

1. this is large enough to validate family, citation, market, OECD, and semantic logic under realistic cross-field conditions,
2. it is bounded enough to remain computationally and operationally deliverable,
3. it keeps portfolio and comparison metrics honest by preventing unseen out-of-scope assets from silently contaminating denominators.

This is also why ghost-node handling exists. Out-of-bounds citation entities may still influence citation math, but they are not promoted into full first-class portfolio assets.

Implementation references:

1. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md:17-29`
2. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md:46-75`
3. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md:85-149`
4. `etl/conf/scope.yaml:1-14`

### 4. Current-state analytics and deep history are separated on purpose

The build config uses two horizon rules:

1. a main operating window from `2007` to `2026`,
2. a separate heritage backfill from `1996` to `2006`.

This matters because PatentIQ needs both:

1. a current-state analytical universe that the UI can explain cleanly,
2. historical support for older influential families and citation heritage effects.

Separating those horizons prevents one of the most common patent-analytics mistakes: mixing present-state comparability and long-tail historical influence into one unlabeled number.

Implementation references:

1. `etl/conf/build.yaml:2-7`
2. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md:34-45`
3. `etl/tests/test_source_certification.py:13-16`

### 5. Source breadth is selective rather than indiscriminate

PatentIQ deliberately combines a small number of source families with high analytical leverage:

1. PATSTAT for family, publication, citation, classification, and person structures,
2. PATSTAT Register for EP legal and procedural context,
3. EPAB for text evidence used in semantic representation,
5. curated reference inputs for market, jurisdiction, kind-code, and OECD-style enrichment.

Business rationale:

1. each source family plays a distinct role,
2. source proliferation without role clarity would reduce explainability,
3. the layered ETL only works cleanly when upstream source purpose is explicit.

Implementation references:

1. `etl/conf/build.yaml:15-17`
2. `etl/conf/build.yaml:19-19`
3. `backend_v2/README.md:7-11`

### 6. Semantic search is intentionally sampled and grant-focused in MVP

The current build config sets:

1. `vector_sample_pct = 0.1`
2. `active_grant_only_for_semantic = true`

This means the semantic layer is intentionally not a full-corpus claim-faithful global search engine.

Business rationale:

1. the contest release needs to prove semantic discovery and comparison, not solve universal freedom-to-operate search,
2. active granted families provide a stronger evidence base for similarity-led review,
3. bounded sampling keeps the semantic layer reproducible, affordable, and clearly labelable.

Implementation references:

1. `etl/conf/build.yaml:8-13`
2. `docs/next-phase-v2/01-scope-and-release-definitions.md:129-138`

### 7. Transparency is part of the product, not an afterthought

The backend V2 principles require explicit caveat and support metadata in strategic responses. The application also uses methodology disclosures, manifests, and traceable artifact packaging as part of its transparency model.

That is a business choice as much as a technical one. Patent analytics products become risky when users cannot inspect scope, formulas, model limits, or source provenance. PatentIQ is intentionally designed so those claims remain inspectable.

Implementation references:

1. `backend_v2/README.md:5-12`
2. `docs/new-feature-ideas/data-room-transparency-and-methodology-wiki-requirements.md:7-20`
3. `docs/new-feature-ideas/data-room-transparency-and-methodology-wiki-requirements.md:42-64`
4. `docs/new-feature-ideas/data-room-transparency-and-methodology-wiki-requirements.md:140-175`

## In-Scope Coverage

The following are in scope, implemented, and important to evaluate:

1. bounded raw acquisition and layered ETL,
2. Bronze, Silver, Gold, and serving snapshot logic,
3. family-first intelligence contracts,
4. harmonized owner and portfolio analytics,
5. legal, citation, market, and OECD-style quality derivations,
6. publication evidence pages,
7. compare workflows,
8. machine-learning prediction stacks and their evaluation logic,
9. semantic search and similarity infrastructure within the sampled MVP boundary,
10. backend page contracts and frontend workspace wiring,
11. auditability, release packaging, and evidence-oriented metadata.

In practical terms, the project should be read as one coherent analytical system from source ingestion to UI-facing interpretation.

Implementation references:

1. `docs/next-phase-v2/01-scope-and-release-definitions.md:7-127`
2. `backend_v2/README.md:13-21`
3. `frontend_v2/README.md:7-18`

## What Is Explicitly Out Of Scope Or Deferred

The scope note also names several important exclusions. These are not accidental gaps. They are consciously deferred so the contest release can remain coherent:

1. full claim-faithful cross-jurisdiction semantic retrieval rollout,
2. multilingual query builder,
3. SEP and standards-body mapping,
4. full litigation expansion beyond the currently available signals,
5. inventor-level analytics,
6. full interactive network mapping.

The correct interpretation is not that PatentIQ claims to have solved those areas already. The correct interpretation is that the team narrowed the contest release to the highest-value and most defensible core.

Implementation references:

1. `docs/next-phase-v2/01-scope-and-release-definitions.md:129-138`

## Interpretation Rules

The following rules should be applied throughout the rest of the documentation:

1. `portfolio` means the harmonized owner's in-scope mega-cluster family set, not the owner's universal worldwide patent estate.
2. `family` is the canonical strategic asset; publication detail is evidence and drilldown.
3. out-of-bounds citation entities may influence citation-side math through ghost-node handling, but they are not full in-scope analytics objects.
4. OECD-style metrics are evidence-backed contextual indicators, not magical universal truth scores.
5. semantic outputs must be read with sampling and chronology guardrails.
6. caveat metadata is not cosmetic; it is part of the product contract.
7. the right evaluation question is whether the system is coherent and truthful inside its declared scope, not whether it already models the entire patent universe.

Implementation references:

1. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md:50-75`
2. `docs/next-phase-v2/17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md:85-149`
3. `backend_v2/README.md:5-12`
4. `etl/conf/build.yaml:11-12`

## How To Read The Rest Of This Dossier

The rest of this documentation should be read in this order:

1. Section 01 explains how raw sources become Bronze, Silver, Gold, and serving artifacts.
2. Section 02 explains how `backend_v2` turns those artifacts into page-shaped contracts.
3. Section 03 explains how `frontend_v2` turns those contracts into workspaces and interaction flows.
4. Section 04 explains the prediction stack, training logic, metrics, and product integration.
5. Section 05 explains the vector and compare intelligence stack.
6. Section 06 ties visible UI elements back to formulas, marts, and backend fields.
7. Section 07 explains release packaging, auditability, and submission compliance.

This order is intentional. The project only makes sense when UI claims are read as downstream of data contracts, and model claims are read as downstream of warehouse logic.

## Key Takeaways

PatentIQ should be understood as a bounded patent intelligence platform, not as a generic patent browser and not as a universal estate model.

Its central business promise is that it can take a strategically relevant technology universe, transform it into explainable family and portfolio intelligence, and expose that intelligence through auditable workspaces, model outputs, and evidence trails.

The bounded scope is therefore part of the product's rigor. It is what makes the analytics interpretable, the backend contracts stable, the UI trustworthy, and the submission defensible under code review.

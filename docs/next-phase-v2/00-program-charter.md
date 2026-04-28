# Program Charter

## Mission

Deliver a contest-ready PatentIQ release in 5 weeks that upgrades the current app into a complete patent intelligence platform with durable accuracy, explainability, and demo reliability.

## Delivery Window

- Start: Monday, March 9, 2026
- Code freeze target: Wednesday, April 8, 2026
- Final validation and demo packaging: Thursday, April 9, 2026 to Friday, April 10, 2026

## Core Outcome

By release, PatentIQ must support an end-to-end flow:

1. Search patent or portfolio,
2. Inspect family-first intelligence,
3. Compare assignees/families/technology segments,
4. Read market and quality signals with caveats,
5. Export a clear report or demo artifact.

## Non-Negotiable Product Principles

1. Family-first is the default analytics mode.
2. Publication/application-level views remain drill-down only.
3. Trends use earliest family priority date unless explicitly labeled otherwise.
4. Citation metrics expose raw and adjusted variants.
5. Recent trends must disclose lag and completeness.
6. OECD-derived quality metrics must be cohort-normalized before product comparison use.
7. Composite scores must expose components and methodology.
8. AI-generated insights must link back to evidence.

## Release Strategy

### What must happen

1. Rebuild the metric foundation before adding new UI surfaces.
2. Preserve a narrow set of polished workflows instead of many shallow ones.
3. Replace misleading or weak legacy logic instead of layering new screens on top of it.
4. Ship with feature flags and known-fallback behavior.

### What must not happen

1. No silent metric-definition changes without UI/API labeling.
2. No black-box AI scoring.
3. No raw cross-cohort OECD comparison in the product.
4. No contest-critical flow left untested.

## Program Priorities

### P0: Required for contest viability

1. Family-aware citation, ranking, and trend logic.
2. Assignee harmonization and parent-rollup baseline.
3. Tech x market trend matrix with grant-rate reliability rules.
4. OECD quality layer with explainability.
5. Citation forecast model retraining on the V2 feature schema.
6. Comparison workflows for company and assignee/family analysis.
7. Reporting, export, and seeded demo readiness.

### P1: Strong differentiators if they fit the schedule

1. Explainable family/owner clustering by tech/market/CPC.
2. AI-assisted insight drafting and cluster labeling.
3. Prosecution timeline basics.

### P2: Defer unless data is already clean and nearly product-ready

1. SEP declaration mapping.
2. Standards mapping.
3. Full inventor-entity resolution.
4. Advanced interactive graph mapping.

## Governance Model

1. One source of truth for metric definitions.
2. One owner per workstream.
3. Weekly ship/no-ship decisions at milestone gates.
4. No new scope enters after Week 3 without explicit replacement of existing scope.

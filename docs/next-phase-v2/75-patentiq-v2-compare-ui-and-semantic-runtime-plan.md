# PatentIQ V2 Compare UI And Semantic Runtime Plan

## Purpose

Define the practical execution order for the missing V2 `compare` and `semantic` surfaces.

The key decision is simple:

1. metric compare is ready to productize now,
2. semantic search and semantic compare are only partially ready because the data artifacts exist but the backend runtime does not.

This note separates those two tracks so implementation order stays grounded in what the repository can already support.

Primary references:

1. [16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md)
2. [22-patentiq-v2-backend-frontend-application-architecture.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/22-patentiq-v2-backend-frontend-application-architecture.md)
3. [40-patentiq-v2-backend-serving-runtime-config-and-cloud-local-parity.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/40-patentiq-v2-backend-serving-runtime-config-and-cloud-local-parity.md)
4. [71-patentiq-v2-peer-banding-and-compare-ranking-policy.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/71-patentiq-v2-peer-banding-and-compare-ranking-policy.md)
5. [73-patentiq-v2-enterprise-frontend-structure-blueprint.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/73-patentiq-v2-enterprise-frontend-structure-blueprint.md)

## Current Readiness Snapshot

### Compare

Already present:

1. backend routes in `/api/v1/compare/families` and `/api/v1/compare/portfolios`
2. compare service logic in `backend_v2/application/services/compare.py`
3. compare PIT marts already built and audited
4. peer-banding rules already documented

Missing:

1. compare routes in `frontend_v2`
2. compare-specific API client and typed response mapping
3. user entry points from the main navigation and workspaces

Conclusion:

1. compare is `application-ready on the backend, UI-missing on the frontend`

### Semantic

Already present:

1. semantic context mart
2. semantic serving DuckDB snapshot
3. ANN files and manifests under `etl/data/vectors/ann`
4. semantic evaluation fixtures and replay audits

Missing:

1. semantic route layer in `backend_v2`
2. semantic runtime loader for the serving DuckDB and ANN artifacts
3. semantic service/repository boundary
4. local/Azure parity runtime wiring for semantic serving
5. frontend semantic search and semantic compare pages

Conclusion:

1. semantic is `artifact-ready but not serving-ready`

## Product Decision

Execution must proceed in two tracks with strict order:

1. deliver `metric compare` views now,
2. deliver `semantic runtime` next,
3. only then build `semantic search` and `semantic compare` pages.

Reasoning:

1. compare already has stable backend contracts and usable business semantics,
2. semantic would otherwise force placeholder UI or unstable ad hoc contracts,
3. backend runtime parity must be solved before semantic is exposed as a product feature.

## Track A: Compare UI Implementation

### Scope

Deliver these routes in `frontend_v2`:

1. `/compare`
2. `/compare/families`
3. `/compare/portfolios`

### UX Requirements

#### A. Compare landing

Must:

1. explain the split between family compare and portfolio compare
2. let the user enter the compare workflows without going through hidden query params
3. make it clear that current compare is peer-banded analytics compare, not semantic compare

#### B. Family compare page

Must:

1. accept two family ids
2. call `/api/v1/compare/families`
3. present the three current lenses:
   - blocking posture
   - legal durability
   - citation heritage
4. show same-cohort versus cross-cohort interpretation explicitly
5. surface compare caveats before analyst overclaim risk appears

#### C. Portfolio compare page

Must:

1. accept two owner ids
2. use owner suggestion search rather than hardcoded owners
3. call `/api/v1/compare/portfolios`
4. present the three current lenses:
   - blocking footprint
   - elite family density
   - crown-jewel strength
5. show cross-scale caveats and density suppression when present
6. show top-family support rows side by side

### Navigation Requirements

Add:

1. top-level `Compare` navigation item in V2
2. landing-page compare entry card
3. family-page compare shortcut with the current family prefilled as the left entity
4. portfolio-page compare shortcut with the current owner prefilled as the left entity

### Contract Requirements

Frontend client layer must formalize:

1. compare identity
2. compare caveats
3. family compare lens rows
4. portfolio compare lens rows
5. portfolio top-family preview rows

The frontend must not treat compare rows as one undifferentiated dump.

## Track B: Semantic Runtime Implementation

This is the next build step after compare UI, not part of the current UI-only pass.

### Minimum Backend Work

Create a semantic serving boundary in `backend_v2`:

1. artifact locator support for:
   - `semantic_serving.duckdb`
   - ANN index binaries
   - ANN family id arrays
   - ANN manifest JSON
2. semantic repository layer
3. semantic service layer
4. route layer

### Minimum API Surface

Recommended first semantic endpoints:

1. `POST /api/v1/semantic/search`
2. `GET /api/v1/semantic/families/{family_id}/neighbors`
3. `POST /api/v1/semantic/compare/families`

Portfolio semantic compare should wait until family semantic compare is stable.

### Required Response Metadata

Every semantic response must include:

1. vector space
2. text provenance
3. abstract-fallback versus claim-grade coverage signal
4. legal/status enrichment
5. semantic caveats that keep discovery distinct from legal proof

## Execution Order

### Phase 1

1. add this plan note
2. add compare client types and API wrappers
3. add compare routes and pages in `frontend_v2`
4. add navigation and deep-link entry points
5. validate with existing compare backend tests plus frontend lint/typecheck

### Phase 2

1. implement semantic runtime in `backend_v2`
2. validate local and Azure-compatible artifact resolution
3. expose semantic APIs
4. build semantic search UI
5. build family semantic compare UI

### Phase 3

1. add portfolio semantic compare
2. add semantic result audit views and transparency panels

## Acceptance Criteria

### Compare

Ready when:

1. a user can open family and portfolio compare from visible V2 navigation
2. family compare renders the three current lenses with caveats
3. portfolio compare renders the three current lenses and top-family preview rows
4. compare entry can start from live family ids and harmonized owner ids
5. no compare UI depends on hardcoded demo entities

### Semantic

Ready when:

1. semantic routes exist in `backend_v2`
2. local and Azure use the same semantic runtime code path
3. semantic search returns enriched family hits with provenance metadata
4. family semantic compare is auditable and caveated
5. only then is semantic exposed as a first-class UI workspace

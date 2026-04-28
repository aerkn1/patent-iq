# PatentIQ V2 Compare And Semantic Workspace Contract

## Purpose

Define concrete page contracts for:

1. the compare workspace,
2. the semantic search / compare workspace,
3. the interaction between vector retrieval, legal context, and family-first explanation.

This contract also aligns to:

1. [patentiq-v2-page-ideas.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/patentiq-v2-page-ideas.md)
2. [creative-frontend-notes.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/creative-frontend-notes.md)

## Primary Questions

### Compare workspace

`How do two families or two portfolios differ structurally, legally, strategically, and in future outlook?`

### Semantic workspace

`What is semantically close, why is it close, and is it strategically relevant under the current legal and scope context?`

## Actual Data Inputs

## Compare inputs

1. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
2. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
3. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
4. [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
5. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)

## Semantic inputs

1. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
2. [silver_family_status_pt.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_pt.parquet)
3. [silver_family_oecd_quality.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_oecd_quality.parquet)
4. Phase 01 vector artifacts when promoted
5. later Phase 02 rollups and abstention registries

## Compare Workspace Layout

1. `CompareSelector`
2. `EntityIdentityStrip`
3. `CompareSummaryCards`
4. `FieldOverlapMatrix`
5. `BlockingAndStatusContrast`
6. `ForecastContrast`
7. `SemanticOverlapPanel`
8. `EvidenceAndCaveatsFooter`

## Compare Components

## 1. `CompareSelector`

Supports:

1. family vs family
2. portfolio vs portfolio
3. family vs portfolio in a constrained comparison mode

## 2. `CompareSummaryCards`

Best representation:

1. side-by-side mirrored cards

Dimensions:

1. size
2. blocking
3. legal state
4. heritage
5. future outlook

## 3. `FieldOverlapMatrix`

Best representation:

1. matrix or mirrored heat strip by WIPO field

Purpose:

1. quickly show overlap, divergence, and whitespace.

## 4. `BlockingAndStatusContrast`

Best representation:

1. two score ladders plus delta callouts

Use:

1. blocking score
2. active branch counts
3. status mix
4. citation context

## 5. `ForecastContrast`

Show:

1. `3y` and `5y` side-by-side
2. interval overlap
3. top projected contributors

## 6. `SemanticOverlapPanel`

This should be explicit about vector space.

Show:

1. claim-space overlap
2. abstract-space overlap
3. provenance labels
4. abstention or caveat flag when unsupported

Never show:

1. one unlabeled blended semantic score

## Semantic Workspace Layout

1. `SemanticSearchHeader`
2. `VectorSpaceSwitcher`
3. `QueryComposer`
4. `ResultList`
5. `ResultDetailSidePanel`
6. `SemanticCompareRollup`
7. `EvidenceAndMethodFooter`

## Semantic Components

## 1. `SemanticSearchHeader`

Must show:

1. vector-space currently active
2. corpus scope
3. sampling status
4. claim-coverage caveat when in claim mode

## 2. `VectorSpaceSwitcher`

Modes:

1. `Abstract Discovery`
2. `Claim Similarity`

This is one of the most important controls in the page.

## 3. `QueryComposer`

Allows:

1. free-text query
2. family anchor query
3. later portfolio compare anchor

## 4. `ResultList`

Best representation:

1. evidence-rich cards, not bare ranks

Each result card should show:

1. family id
2. owner
3. primary field
4. semantic similarity
5. blocking score
6. OECD percentile
7. current family status
8. provenance badge
9. abstract-fallback badge where applicable

## 5. `ResultDetailSidePanel`

Shows:

1. representative text excerpt
2. overlap rationale
3. legal and chronology context
4. link to family page

## 6. `SemanticCompareRollup`

For family-to-family and portfolio-to-portfolio compare:

1. overlap score
2. divergence zones
3. unsupported areas
4. confidence band

## 7. `TimeSliceCompareMode`

The compare workspace should also support comparing the same entity across time, not just entity A vs entity B.

Supported modes:

1. family `year A vs year B`
2. family `selected year vs current`
3. portfolio `year A vs year B`
4. portfolio `selected year vs current`
5. optional `current vs projected` compare for forecast-aware portfolio views

Best representation:

1. mirrored summary cards
2. compare radar for normalized profile shape
3. delta table with absolute values and signed change
4. time-aligned mini timelines beneath the compare header

Recommended radar axes for time-slice compare:

1. blocking power percentile
2. legal durability / active state
3. field breadth or contribution intensity
4. coverage breadth
5. threat intensity or citation influence proxy where year-safe
6. projected influence only in `current vs projected` mode

Rules:

1. radar belongs here more naturally than on single-entity pages
2. max overlays: `3`
3. all axes must use stable `0..100` scaling
4. if a chosen year lacks enough historical metrics, render compare bars and delta chips instead of radar
5. current-only metrics such as present-day OECD quality must not be back-projected into older years without explicit historical derivation

## Backend Contract

### Compare

1. `GET /api/v1/compare/families`
2. `GET /api/v1/compare/portfolios`

### 2026-04-10 compare contract update

Current backend-v2 compare implementation now exposes the first real portfolio compare payload at:

1. `GET /api/v1/compare/portfolios?left_owner_id=...&right_owner_id=...&top_family_limit=...`

Current response behavior:

1. returns three `lens` rows:
   - `mass`
   - `density`
   - `crown_jewel`
2. each lens row carries:
   - raw metric value for left and right owners
   - peer-bucket percentile for left and right owners
   - qualitative band for left and right owners
   - peer bucket labels
   - same-bucket vs cross-scale compare mode
3. returns `top_family_preview` support rows for both compared owners
4. `GET /api/v1/compare/families?left_family_id=...&right_family_id=...` now returns the first real family compare payload
5. family compare currently returns three `lens` rows:
   - `blocking_posture`
   - `legal_durability`
   - `citation_heritage`
6. each family lens row carries:
   - raw metric value for left and right families
   - cohort-relative percentile for left and right families
   - qualitative band for left and right families
   - cohort labels
   - same-cohort vs cross-cohort compare mode
7. family compare uses band-first comparison when cohorts differ across field, lifecycle stage, or priority-year grouping

Important rule:

1. portfolio compare bands are peer-relative within portfolio-size buckets,
2. they are not interchangeable with CPC / WIPO / jurisdiction market ranks,
3. top-family preview rows are supporting evidence for cross-scale interpretation rather than a final top-10 / top-10% crown-jewel contract,
4. family compare percentiles are cohort-relative and must not be presented as a universal family league table across unrelated fields or vintages.

### Semantic

1. `GET /api/v1/semantic/search`
2. `GET /api/v1/semantic/families/{family_id}/neighbors`
3. `GET /api/v1/semantic/compare/families`
4. `GET /api/v1/semantic/compare/portfolios`

## UI Rules

1. semantic results must dedupe to `docdb_family_id`
2. chronology and legal context must appear before strategic interpretation
3. claim-backed and abstract-backed hits must remain visibly separate
4. sampled-corpus mode must be disclosed in page metadata
5. any whitespace narrative must be caveated if claim coverage is weak
6. time-slice compare must expose which metrics are true historical values versus current-only overlays

## UI-Hub Alignment

Compare workspace:

1. mirrored comparison headers and overlap illumination are encouraged,
2. raw-vs-normalized transitions can be animated,
3. matrices and unit labels must remain flat and explicit.

Semantic workspace:

1. may use a semantic-neighborhood or result-space visualization,
2. should keep query composer and result list flat,
3. should use a right-side evidence panel for rationale, provenance, and legal context.

Both pages should keep the UI-Hub rule:

1. strong side panels for evidence and caveats,
2. one authored visual centerpiece at most,
3. no decorative motion in high-reading-load panels.

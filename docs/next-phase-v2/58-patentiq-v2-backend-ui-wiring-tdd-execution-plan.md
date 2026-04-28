# PatentIQ V2 Backend And UI Wiring TDD Execution Plan

## Goal

Define the cleanest implementation path for turning the now-sealed ETL, PIT, and ML-semantic outputs into real backend endpoints and frontend pages.

This note fixes:

1. the implementation order,
2. the shared backend and frontend patterns,
3. the TDD workflow,
4. the page-by-page rollout strategy,
5. the documentation rule for every wiring action.

## Current Read

The data and model side is now sufficient for MVP wiring.

Ready now:

1. Gold PIT serving marts
2. sealed `Phase 03`
3. sealed `Phase 04`
4. sealed `Phase 06`
5. `Phase 08 core` portfolio rollups
6. family / portfolio / market classification PIT marts
7. market CPC trend and CPC importance marts

Not public-serving yet:

1. pending-grant raw probability outputs
2. Phase 05 friction branch
3. true historical owner-truth extensions
4. jurisdiction-sliced CPC market trend
5. true dated CPC mutation history

So the implementation target is:

1. backend/UI wiring for sealed artifacts first,
2. feature-gated internal support for candidate-only branches second,
3. no premature new ETL or model lanes during page wiring.

## Frontend Split Decision

The current repository now preserves the old UI as:

1. [frontend_v1](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v1)

The clean V2 implementation target is:

1. [frontend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2)

Decision:

1. build new V2 pages only in `frontend_v2`,
2. keep `frontend_v1` as reference and fallback during migration,
3. preserve [backend](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend) as the legacy/reference backend,
4. build the clean V2 API in [backend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2),
5. do not let new V2 page contracts accrete inside the legacy backend by default.

## Current Implementation Status

The clean V2 runtime scaffold is now in place in [backend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2).

Implemented:

1. shared runtime settings in [backend_v2/config/settings.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/config/settings.py)
2. clean FastAPI app entrypoint in [backend_v2/main.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/main.py)
3. page-shaped route groups in:
   - [backend_v2/api/v1/portfolios.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/api/v1/portfolios.py)
   - [backend_v2/api/v1/families.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/api/v1/families.py)
   - [backend_v2/api/v1/publications.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/api/v1/publications.py)
   - [backend_v2/api/v1/market_intelligence.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/api/v1/market_intelligence.py)
   - [backend_v2/api/v1/compare.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/api/v1/compare.py)
   - [backend_v2/api/v1/data_room.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/api/v1/data_room.py)
4. V2-only schemas under [backend_v2/domain/schemas](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/domain/schemas)
5. service/repository seams under:
   - [backend_v2/application/services](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/application/services)
   - [backend_v2/infrastructure/repositories](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/repositories)
6. smoke tests in [backend_v2/tests](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/tests)

## KISS Architectural Rule

Keep the V2 backend as a clean `modular monolith`.

Do:

1. use thin FastAPI routers,
2. use page-shaped application services,
3. use repository/adaptor classes for parquet access,
4. keep frontend calls inside typed API client functions,
5. keep page state owned by the page or a narrow feature component.

Do not:

1. put SQL in route files,
2. let frontend fetch parquet-shaped low-level data directly,
3. introduce cross-page custom hook sprawl too early,
4. create a separate backend microservice for each workspace,
5. mix legacy V1 response shapes into `backend_v2`.

## Wiring Principles

### 1. Page contract first

Every page implementation must start from the corresponding page contract note, not from ad hoc UI guesses.

### 2. Overview first, sections second

For each page:

1. implement `overview` endpoint first,
2. return enough for shell render and hero section,
3. split heavy sections into dedicated endpoints,
4. lazy-load those sections in the frontend.

### 3. Typed DTOs only

Backend must expose typed response schemas for:

1. overview payloads,
2. section payloads,
3. filter/query parameter contracts,
4. caveat and support metadata.

Frontend must consume:

1. typed API client functions,
2. typed domain DTOs under the active V2 frontend app,
3. page-specific view adapters only when needed.

### 4. Coverage and caveat metadata is mandatory

Any endpoint using:

1. `Phase 03`,
2. `Phase 04`,
3. `Phase 06`,
4. portfolio replay history,
5. classification replay / first-seen visibility,

must carry the relevant caveat/support fields through to the frontend.

### 5. TDD at the service contract boundary

The primary test loop should be:

1. repository test,
2. service test,
3. route/schema test,
4. frontend type integration,
5. page render test for non-trivial components.

Do not start with fully styled UI before the service and contract tests exist.

## Recommended Implementation Order

### Stage A. Shared backend serving foundations

Build once in `backend_v2` before page-by-page work:

1. runtime config cleanup
2. common DuckDB snapshot/artifact resolver
3. common page error contract
4. common support / caveat schema fragments
5. common pagination / filter DTOs where needed
6. repository test harness

Required backend cleanups:

1. move hardcoded runtime assumptions into config objects,
2. standardize `/api/v1/...` prefixing,
3. keep route handlers thin and consistent,
4. normalize error envelopes,
5. keep V2 response models separate from legacy backend contracts.

### Stage B. Shared frontend foundations

Build once before page rollout:

1. environment-driven API base config
2. typed fetch wrapper
3. shared query-state helpers
4. shared loading / error / empty-state components
5. page-shell layout primitives
6. badge / caveat / support chip primitives

Immediate cleanup needed:

1. remove hardcoded ngrok-first API config from the legacy client in [frontend_v1/lib/api.ts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v1/lib/api.ts)
2. move API base resolution to env-driven config with local-safe fallback
3. group client functions by workspace rather than one growing file
4. align frontend types to V2 page DTOs instead of older V1 forecast-only types

These shared foundations should now land in:

1. [frontend_v2/lib/config.ts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/lib/config.ts)
2. [frontend_v2/lib/api/core.ts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/lib/api/core.ts)
3. `frontend_v2/lib/api/*`
4. `frontend_v2/lib/types/*`

### Stage C. Backend and UI page rollout

Implement page-by-page in this order:

1. `Portfolio`
2. `Family`
3. `Market Intelligence`
4. `Publication`
5. `Compare`
6. `Data Room`

Why this order:

1. `Portfolio` exercises sealed Phase `03/04/06` and coverage policy together,
2. `Family` exercises the family-first core and publication drill path,
3. `Market Intelligence` exercises the new CPC trend and importance marts,
4. `Publication` is evidence-heavy but lower leverage than portfolio/family,
5. `Compare` should reuse already-proven family/portfolio page blocks,
6. `Data Room` can land after the core product surfaces are stable.

## Backend Pattern

### Route grouping

Target route groups:

1. `families`
2. `publications`
3. `portfolios`
4. `market_intelligence`
5. `compare`
6. `data_room`
7. `stats`

### Service pattern

Each page/workspace should have:

1. one overview service method,
2. one method per heavy section,
3. repositories with single-purpose query responsibilities,
4. zero formatting logic in repositories beyond direct row-to-dto mapping.

Recommended shape:

1. `application/services/<workspace>_service.py`
2. `domain/schemas/<workspace>.py`
3. `infrastructure/repositories/<workspace>_<slice>_repo.py`
4. `api/v1/<workspace>.py`

### Data access pattern

Prefer:

1. small repository methods with explicit SQL,
2. one mart or one tightly-related mart set per method,
3. post-query mapping in service layer only when unavoidable.

Avoid:

1. one repository that knows every mart,
2. service methods that concatenate many unrelated SQL fragments,
3. frontend-specific labels being embedded inside SQL.

## Frontend Pattern

### Client pattern

Preferred frontend client split:

1. `frontend_v2/lib/api/core.ts`
2. `frontend_v2/lib/api/portfolios.ts`
3. `frontend_v2/lib/api/families.ts`
4. `frontend_v2/lib/api/publications.ts`
5. `frontend_v2/lib/api/market-intelligence.ts`
6. `frontend_v2/lib/api/compare.ts`
7. `frontend_v2/lib/api/data-room.ts`

### Type pattern

Preferred type split:

1. `frontend_v2/lib/types/portfolio-v2.ts`
2. `frontend_v2/lib/types/family-v2.ts`
3. `frontend_v2/lib/types/publication-v2.ts`
4. `frontend_v2/lib/types/market-intelligence-v2.ts`
5. `frontend_v2/lib/types/compare-v2.ts`
6. `frontend_v2/lib/types/common-v2.ts`

### Page composition rule

For each page:

1. shell route component loads overview,
2. heavy sections are feature components,
3. feature components call page-section endpoints,
4. shared primitives live under `frontend_v2/components/ui`,
5. domain feature components live under feature folders, not in `ui`.

## TDD Workflow

For every page or shared backend slice:

1. define/adjust the contract note first,
2. add backend schema tests,
3. add repository/service tests with fixture parquets,
4. add route tests,
5. implement backend,
6. add frontend DTO typing,
7. add page/component tests for non-trivial logic,
8. implement UI,
9. update the implementation note with what landed.

### Minimum backend test stack

1. repository-level tests under `backend/tests/`
2. service contract tests under `backend/tests/`
3. API route tests using FastAPI test client

### Minimum frontend test stack

1. component tests for filtering/stateful rendering
2. view-model adapter tests when transformation logic is non-trivial
3. no snapshot-only testing as the primary safety net

## Page-by-page Execution Detail

### 1. Portfolio page

Start here because it consumes the most sealed value.

Backend sequence:

1. `GET /api/v1/portfolios/{owner_id}/overview`
2. `GET /api/v1/portfolios/{owner_id}/forecast-summary`
3. `GET /api/v1/portfolios/{owner_id}/forecast-segments`
4. `GET /api/v1/portfolios/{owner_id}/forecast-contributors`
5. `GET /api/v1/portfolios/{owner_id}/classification-exposure`

Frontend sequence:

1. header + summary cards
2. coverage and caveat panel
3. forecast panel
4. contributor table
5. classification exposure panel

### 2. Family page

Backend sequence:

1. `GET /api/v1/families/{family_id}/overview`
2. `GET /api/v1/families/{family_id}/trajectory`
3. `GET /api/v1/families/{family_id}/classification-footprint`
4. `GET /api/v1/families/{family_id}/lapse-risk`
5. `GET /api/v1/families/{family_id}/evidence`

Frontend sequence:

1. identity + summary rail
2. trajectory
3. classification footprint
4. lapse-risk strip
5. evidence section

### 3. Market Intelligence page

Backend sequence:

1. `GET /api/v1/market-intelligence/overview`
2. `GET /api/v1/market-intelligence/segments`
3. `GET /api/v1/market-intelligence/segments/{segment_key}`
4. `GET /api/v1/market-intelligence/cpc-trends`
5. `GET /api/v1/market-intelligence/cpc-importance`

Frontend sequence:

1. state ribbon
2. segment league table
3. selected segment drawer
4. CPC-within-field panel
5. CPC importance leaderboard

### 4. Publication page

Backend sequence:

1. `GET /api/v1/publications/{publication_id}/overview`
2. `GET /api/v1/publications/{publication_id}/text`
3. `GET /api/v1/publications/{publication_id}/legal-timeline`
4. `GET /api/v1/publications/{publication_id}/family-context`

### 5. Compare page

Build on top of the already-stable family and portfolio DTOs.

### 6. Data Room page

Build after the core pages are consuming the production-serving contracts cleanly.

## Candidate-only Branch Rule

Pending-grant must not be wired as a normal public MVP panel yet.

If implemented before sealing, it must be:

1. feature-gated,
2. rank/percentile-first,
3. clearly labeled candidate-only,
4. excluded from public executive rollups.

## Documentation Rule

Every backend/UI implementation action must update at least one of:

1. the page contract,
2. the execution note for the relevant phase,
3. the implementation log / README index,
4. a dedicated backend/UI wiring note when a new shared pattern is introduced.

Recommended action log for each implemented slice:

1. what endpoint landed,
2. what service/repository files changed,
3. what tests were added,
4. what contract note was updated,
5. what caveats remain.

## Immediate Next Move

The best first implementation slice is:

1. shared backend config cleanup,
2. shared `frontend_v2` API config cleanup,
3. portfolio V2 overview + forecast summary wiring with TDD,
4. then portfolio sections one by one.

This is the cleanest path because it:

1. starts from the most valuable sealed artifact set,
2. forces coverage and caveat handling early,
3. establishes the backend/client/component pattern before the other pages reuse it.

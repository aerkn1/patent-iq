# PatentIQ V2 Backend V2 Split Decision And Clean Architecture

## Purpose

Record the decision to preserve the current backend as legacy/reference and create a clean `backend_v2` target driven directly by the V2 contracts.

## Decision

The repository now treats backend runtime targets as:

1. [backend](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend) as the legacy/reference backend
2. [backend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2) as the clean V2 backend target

Rationale:

1. V2 page contracts are materially different from the current V1 surface
2. V2 needs page-shaped DTOs and route groups instead of accreting more V1 compatibility logic
3. the frontend already moved to a clean [frontend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2)
4. a clean backend split keeps V2 implementation readable and testable

## Source Inputs

The `backend_v2` structure should be driven by:

1. [22-patentiq-v2-backend-frontend-application-architecture.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/22-patentiq-v2-backend-frontend-application-architecture.md)
2. [23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md)
3. [30-patentiq-v2-market-intelligence-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md)
4. [32-patentiq-v2-family-and-publication-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md)
5. [33-patentiq-v2-portfolio-and-forecast-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md)
6. relevant `docs/new-feature-ideas/*` notes that define product scope and evidence expectations

## Initial Backend V2 Shape

The clean scaffold now exists in [backend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2) with:

1. shared runtime settings
2. page-shaped route groups
3. V2-only schemas
4. application services per workspace
5. parquet-oriented repository seams
6. thin FastAPI routers

## Route Groups

`backend_v2` should own these groups from the start:

1. `portfolios`
2. `families`
3. `publications`
4. `market-intelligence`
5. `compare`
6. `data-room`
7. `stats`

## Contract Rules

1. overview endpoints first
2. section endpoints second
3. every strategic response carries caveat/support metadata
4. V2 routers should not emit legacy V1 response shapes
5. DuckDB/parquet access stays behind repositories
6. frontend consumes only typed page DTOs

## First Real Vertical

The first full V2 vertical should still be `Portfolio`, because it exercises:

1. Phase 08 core portfolio outputs
2. Phase 03/04/06 sealed artifacts
3. coverage and caveat metadata
4. the page-contract pattern used later by Family and Market Intelligence

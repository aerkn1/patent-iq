# PatentIQ V2 Detailed Page Contracts Index

## Purpose

Collect the concrete page contracts that extend the baseline workspace definitions into implementation-ready UX and backend page-shape guidance.

Read these alongside:

1. [04-product-and-ui-workstreams.md](../04-product-and-ui-workstreams.md)
2. [22-patentiq-v2-backend-frontend-application-architecture.md](../22-patentiq-v2-backend-frontend-application-architecture.md)
3. [23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md](../23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md)
4. [README.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/README.md)
5. [patentiq-v2-page-ideas.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/patentiq-v2-page-ideas.md)
6. [creative-frontend-notes.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/UI-Hub/creative-frontend-notes.md)

## Detailed Contracts

1. [30-patentiq-v2-market-intelligence-page-contract.md](./30-patentiq-v2-market-intelligence-page-contract.md)
2. [31-patentiq-v2-data-room-page-contract.md](./31-patentiq-v2-data-room-page-contract.md)
3. [32-patentiq-v2-family-and-publication-page-contract.md](./32-patentiq-v2-family-and-publication-page-contract.md)
4. [33-patentiq-v2-portfolio-and-forecast-page-contract.md](./33-patentiq-v2-portfolio-and-forecast-page-contract.md)
5. [34-patentiq-v2-compare-and-semantic-workspace-contract.md](./34-patentiq-v2-compare-and-semantic-workspace-contract.md)

## Why These Exist

The baseline UX note defines:

1. which workspaces exist,
2. which backend services should serve them,
3. which top-level components are expected.

These detailed contracts add:

1. actual Gold/Silver data bindings,
2. section order,
3. component behavior,
4. caveat and degraded-mode rules,
5. page-specific interpretation guidance,
6. UI-Hub-aligned creative vs flat treatment rules,
7. compare-oriented time-slice patterns for family and portfolio history where the history marts support them.

## Implementation Order

Recommended build order:

1. Family and Publication
2. Portfolio and Forecast
3. Market Intelligence
4. Compare and Semantic
5. Data Room

Why:

1. family and portfolio pages are nearest to current backend/frontend structure,
2. market and semantic depend more on the new Gold and vector contracts,
3. Data Room benefits from stable manifests and approved catalog wiring.

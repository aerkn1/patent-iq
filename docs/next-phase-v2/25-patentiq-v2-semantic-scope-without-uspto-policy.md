# PatentIQ V2 Semantic Scope Without USPTO Policy

## Purpose

Define the operating semantic MVP for PatentIQ V2 when USPTO full text is not available, but EPAB and PATSTAT abstract fallback remain available.

## Decision

PatentIQ V2 should keep the semantic layer, but re-scope it from a full claim-faithful cross-jurisdiction promise to a maximum viable `EPAB + PATSTAT` semantic discovery and comparison layer.

## Product Positioning

PatentIQ should continue to support:
1. family-to-family semantic search,
2. family-to-family semantic compare,
3. portfolio-to-portfolio semantic compare,
4. text-to-family semantic discovery,
5. semantic context panels in family and compare pages.

PatentIQ should defer or explicitly downgrade:
1. semantic FTO radar,
2. broad legal-threat positioning,
3. strong claim-faithful whitespace and collision mapping,
4. any wording that implies universal claim-text coverage.

## Corpus Policy

The semantic corpus should use this deterministic hierarchy:
1. English EP granted `B` Claim 1 from EPAB,
2. else English PATSTAT abstract fallback.

That means:
1. USPTO is no longer part of the active representative text hierarchy,
2. the semantic layer becomes mixed-provenance by design,
3. provenance and fallback metadata become mandatory for safe UI and Data Room use.

## Vector-Space Policy

The MVP should keep vector-space separation, but with revised semantics:
1. `vector_abstract` is the primary global space,
2. `vector_claims` is secondary and EPAB-backed only,
3. claim-space must not be presented as globally complete.

## Mandatory Transparency

Every semantic result or summary surface must preserve:
1. `text_provenance`,
2. `text_source_type`,
3. `is_abstract_fallback`,
4. semantic corpus mode or coverage caveat where relevant.

The Data Room must state clearly:
1. USPTO full text is absent from the semantic corpus,
2. EPAB claim text is present where available,
3. PATSTAT abstract fallback is used elsewhere,
4. claim-oriented workflows are narrower than the original full-source plan.

## Backend And UI Implications

Backend contracts should:
1. return provenance and fallback metadata in semantic responses,
2. treat semantic retrieval as discovery rather than legal proof,
3. expose coverage caveats for claim-space retrieval.

UI contracts should:
1. emphasize family discovery and compare value,
2. label EP claim-enriched results explicitly,
3. suppress legal-grade wording for the semantic MVP.

## ETL Implications

Representative text generation should:
1. stop waiting on USPTO availability,
2. prefer EPAB English grant Claim 1,
3. fall back to PATSTAT English abstract,
4. emit coverage metrics proving how much of the semantic corpus is claim-backed versus abstract-backed.

## Relationship To Existing Notes

This policy refines:
1. [16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md](./16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md)
2. [20-patentiq-v2-data-room-architecture-and-contract.md](./20-patentiq-v2-data-room-architecture-and-contract.md)
3. [21-patentiq-v2-azure-runtime-and-storage-architecture.md](./21-patentiq-v2-azure-runtime-and-storage-architecture.md)
4. [23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md](./23-patentiq-v2-ux-page-contracts-and-backend-wiring-baseline.md)
5. [24-patentiq-v2-local-etl-and-artifact-build-runbook.md](./24-patentiq-v2-local-etl-and-artifact-build-runbook.md)

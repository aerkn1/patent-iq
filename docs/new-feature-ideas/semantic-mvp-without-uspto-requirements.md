# Semantic MVP Without USPTO Requirements

## Source

User-guided semantic-scope recalibration captured on March 30, 2026.

## Purpose

Define the maximum viable and defensible semantic scope for PatentIQ when USPTO full text is unavailable, while EPAB and PATSTAT abstract fallback remain available.

## Core Principle

PatentIQ should keep the semantic layer, but re-scope it to match the actual text corpus strength.

That means:
1. semantic discovery and comparison remain in scope,
2. EP claim-enriched retrieval is allowed where EPAB claim text exists,
3. PATSTAT abstract fallback remains the broad cross-jurisdiction floor,
4. workflows that depend on broad claim-faithful U.S. coverage must be deferred or explicitly downgraded.

## Current Operating Assumption

The current semantic corpus should assume:
1. no usable USPTO full-text provider in the MVP build,
2. EPAB claim and abstract coverage for EP publications,
3. PATSTAT English abstract fallback for the broader family universe.

## Required Semantic Scope

### SMU-01: Keep Family-Level Semantic Discovery

Requirement:
PatentIQ should keep these semantic workflows available:
1. `text_to_family_semantic_search` as exploratory discovery,
2. `family_to_family_semantic_search`,
3. `family_to_family_semantic_compare`,
4. `portfolio_to_portfolio_semantic_compare`.

Rationale:
1. these workflows still produce value with EPAB claim text plus PATSTAT abstract fallback,
2. they align with family-first analytics,
3. they can remain auditable through provenance and fallback flags.

### SMU-02: Defer Claim-Heavy Threat Or FTO Positioning

Requirement:
PatentIQ should not market the semantic layer as a broad cross-jurisdiction FTO or legal-threat engine while USPTO full text is absent.

Implications:
1. semantic FTO radar should be deferred or disabled,
2. strong claim-faithful whitespace and collision mapping should be deferred,
3. any surviving claim-oriented workflow must be labeled as EP-claim-enriched rather than global.

## Representative Text Policy

### SMU-03: Replace The Original Global Text Hierarchy

Requirement:
The representative text hierarchy should become:
1. English EP granted `B` Claim 1 from EPAB,
2. else English PATSTAT abstract fallback.

Rules:
1. `A`-document claims remain excluded from claim-oriented workflows,
2. if no usable EPAB claim exists, the family must fall back to abstract-based representation,
3. fallback state must remain visible in downstream marts, vectors, APIs, and UI.

### SMU-04: Provenance Must Become A First-Class Semantic Signal

Requirement:
Every semantic payload must expose:
1. `text_provenance`,
2. `text_source_type`,
3. `is_abstract_fallback`,
4. whether the family is claim-backed or abstract-backed.

Rationale:
1. the corpus is now mixed-strength rather than uniformly claim-driven,
2. users must be able to distinguish EP-claim-backed retrieval from abstract-only retrieval,
3. the Data Room must be able to explain semantic limitations honestly.

## Vector-Space Policy

### SMU-05: Abstract Space Remains The Primary Global Space

Requirement:
`vector_abstract` should become the default MVP semantic space for global family discovery and comparison.

Rationale:
1. it can cover a much broader in-scope family universe,
2. it avoids overstating claim-level comparability where only abstracts exist,
3. it provides the best consistent retrieval baseline without USPTO.

### SMU-06: Claim Space Becomes EPAB-Backed And Secondary

Requirement:
`vector_claims` may still exist, but it must be treated as:
1. EPAB-backed,
2. narrower-coverage,
3. secondary to abstract space for generic search,
4. unsuitable for global legal-risk claims.

Implications:
1. claim-space result sets must carry stronger coverage caveats,
2. claim-space should not be the default for general text-to-family retrieval,
3. UI copy should not imply universal claim-semantic coverage.

## Product And UX Rules

### SMU-07: Safe Semantic Product Claim

Requirement:
The semantic layer should be positioned as:
1. family-level semantic discovery,
2. semantic comparison,
3. EP claim-enriched retrieval where available,
4. abstract-fallback semantic context elsewhere.

The semantic layer should not be positioned as:
1. legal infringement proof,
2. full cross-jurisdiction claim-semantic FTO search,
3. uniform claim-faithful whitespace mapping.

### SMU-08: The UI Must Surface Coverage And Caveats

Requirement:
Semantic-facing UI should show:
1. text provenance,
2. abstract fallback status,
3. semantic corpus mode,
4. coverage caveat when claim-space is partial or EP-only.

## Data Room Requirements

### SMU-09: Data Room Must Explain The Missing USPTO Layer

Requirement:
The Data Room semantic section must explicitly state:
1. USPTO full text is absent from the current MVP semantic corpus,
2. EPAB claim text is used where available,
3. PATSTAT English abstract fallback fills the remaining coverage,
4. claim-space workflows are narrower and more caveated than the original full-source design.

## Relationship To Existing Notes

This note updates and constrains:
1. `semantic-similarity-and-vector-layer-requirements.md`
2. `data-room-transparency-and-methodology-wiki-requirements.md`
3. `ui-workspace-and-page-contract-requirements.md`
4. `docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md`
5. `docs/next-phase-v2/24-patentiq-v2-local-etl-and-artifact-build-runbook.md`

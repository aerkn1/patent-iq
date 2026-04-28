# UI Workspace And Page Contract Requirements

## Source

User-provided implementation guidance captured on March 15, 2026.

## Purpose

Define the workspace-level UX and page-contract rules for PatentIQ so the frontend and backend can evolve around consistent page questions, drill-down paths, and evidence-linked APIs rather than scattered widget-first development.

## Core Principle

PatentIQ should be a guided family-first intelligence workspace, not a loose collection of charts.

That means:
1. each page must answer a primary analytical question,
2. each page must be backed by a page-shaped backend contract,
3. each strategic insight must have a drill-down path to evidence or methodology.

## UX-01: Portfolio, Family, And Publication Must Form The Core Drill-Down Chain

Requirement:
The primary analytical drill-down should be:

`Portfolio -> Family -> Publication`

Interpretation:
1. `portfolio` is the strategic owner-level workspace,
2. `family` is the default analytical unit,
3. `publication` is the evidence and provenance unit.

## UX-02: Publication Must Be A Drill-Down Scope, Not The Top-Level Default

Requirement:
Publication-level pages should exist, but publication should not replace family as the main analytical unit.

## UX-03: The Product Must Expose Stable Top-Level Workspaces

Requirement:
The top-level product should include at least:
1. `Portfolio`
2. `Lookup / Explore`
3. `Compare`
4. `Forecasts`
5. `Market Intelligence`
6. `Data Room`

## UX-04: Market Intelligence Must Be A First-Class Workspace

Requirement:
The product should expose a separate `Market Intelligence` workspace that explains point-in-time technology-market conditions across the mega-cluster.

This workspace should answer questions such as:
1. which fields, segments, or clusters are rising,
2. which are cooling,
3. where concentration is highest,
4. where whitespace still exists,
5. where the owner’s portfolio is over- or under-aligned.

## UX-05: Every Workspace Needs A Page-Level Overview Contract

Requirement:
Every major page should have a single overview contract for above-the-fold rendering.

The overview contract should include:
1. identity block,
2. key summary cards,
3. top-level caveats,
4. first section or first-tab payload,
5. links or ids for deeper drill-down sections.

## UX-06: Heavy Sections Must Hydrate Separately

Requirement:
Below-the-fold sections such as long tables, timeseries, text bodies, or semantic result tables should load through separate section endpoints rather than bloating the initial page payload.

## UX-07: Scores Must Always Show Their Components

Requirement:
Any page that shows major scores such as blocking power, enforceability, citation impact, heritage, or forecasts must visibly expose:
1. key components,
2. caveats,
3. evidence or methodology links.

## UX-08: Every Workspace Must Link To The Data Room

Requirement:
Each strategic workspace should expose a clear path to:
1. metric methodology,
2. source lineage,
3. model card where relevant,
4. semantic methodology where relevant.

## UX-09: Market Context Must Support Portfolio Interpretation

Requirement:
Portfolio pages should include relevant market-condition context, but those metrics must be clearly labeled as external context rather than owner-owned metrics.

## UX-10: Market Intelligence Must Remain Distinct From Portfolio State

Requirement:
The `Market Intelligence` workspace should present the condition of the technology-market landscape itself, not just the owner’s exposure to it.

Interpretation:
1. `Market Intelligence` is the product-facing workspace name,
2. `field`, `segment`, and `cluster` are valid underlying analysis dimensions inside that workspace,
3. the product should avoid making `cluster conditions` the primary public-facing label for the whole workspace.

## UX-11: Data Room Must Be Read-Only And Downloadable

Requirement:
The Data Room should remain:
1. read-only,
2. downloadable for approved artifacts,
3. wiki-backed for methodology explanations.

## UX-12: Backend Contracts Must Be Workspace-Shaped

Requirement:
The backend should not expose only low-level table-driven APIs.

Instead it should expose workspace/page contracts such as:
1. portfolio overview,
2. family overview,
3. publication overview,
4. market intelligence overview,
5. compare overview,
6. forecast overview,
7. Data Room overview.

## Relationship To Existing Notes

This note operationalizes:
1. `data-room-transparency-and-methodology-wiki-requirements.md`
2. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
3. `predictive-signals-and-interpretable-forecasting-requirements.md`
4. `semantic-similarity-and-vector-layer-requirements.md`
5. `mega-cluster-dataset-scope-and-boundary-governance-requirements.md`

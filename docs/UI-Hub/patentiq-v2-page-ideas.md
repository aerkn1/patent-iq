# PatentIQ V2 Page Ideas

## Purpose

Propose a clearer page and workspace structure for the next version of PatentIQ using the direction already established in:

- `docs/next-phase-v2/04-product-and-ui-workstreams.md`
- `docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md`
- `docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md`
- `docs/new-feature-ideas/march-2026-family-legal-analytics-master-index.md`
- `docs/new-feature-ideas/optimum-product-gap-analysis-architecture-requirements.md`
- `docs/new-feature-ideas/interactive-patent-mapping-requirements.md`
- `docs/new-feature-ideas/client-provided-data-financial-intelligence-requirements.md`
- `docs/new-feature-ideas/market-analysis-additional-features-nonoverlap.md`

## Design Rules

1. The product should behave like a guided intelligence workspace, not a loose dashboard.
2. `docdb_family_id` should be the default analysis entity wherever possible.
3. Every major score should expose components, caveats, and source evidence.
4. Current-state legal questions and historical influence questions must stay visibly separated.
5. Semantic retrieval is a discovery layer, not proof.
6. Forecasts should be shown as explicit future expectations with uncertainty, not as current-state facts.

## Proposed Top-Level Navigation

1. `Home`
2. `Search`
3. `Families`
4. `Portfolios`
5. `Compare`
6. `Markets`
7. `Forecasts`
8. `Workspaces`
9. `Reports`

This intentionally removes the old licensing-first feel and makes the navigation align with the V2 workstreams.

## Creative UI Placement Rules

Creative 3D and motion should be used as a product communication tool, not as decoration layered over dense analytics.

### Good uses

1. orienting the user in a new workspace,
2. explaining a hard analytical distinction,
3. revealing one high-value insight gradually,
4. making a demo-critical transition memorable,
5. showing spatial relationships such as clusters, overlaps, coverage, and concentration.

### Bad uses

1. core search forms,
2. dense result tables,
3. controls-heavy analyst workflows,
4. any panel that already has high reading load,
5. pages where motion would weaken trust or scan speed.

### UI constraints

1. One major animated centerpiece per page is enough.
2. Core evidence cards and tables should remain flat and fast.
3. Every creative section should have a static fallback for lower-power devices.
4. Motion must clarify one concept, not just create “premium feel.”

## Proposed Core Pages

## 1. Home: Intelligence Workspace

### Role

Be the guided entry point for active investigations, saved work, and high-signal alerts.

### Key modules

1. recent workspaces and saved sets,
2. query resume panel,
3. high-priority legal or expiry alerts,
4. newly detected forecast movers,
5. market hot-spot tiles,
6. methodology and data completeness banner.

### Why it belongs

Supports the V2 direction to move from a loose analytics dashboard to a guided intelligence workspace.

### Creative UI opportunities

1. A lightweight 3D or 2.5D “intelligence field” hero showing active investigations, hot clusters, and recent alerts as one living scene.
2. A scroll-guided explainer showing the shift from publication noise to family-first intelligence.
3. Animated transitions from alert cards into the destination workspace so the homepage feels like a launchpad, not a dead dashboard.
4. Borrow the second video’s hero pattern: one large center object plus four floating support elements for `Search`, `Families`, `Markets`, and `Forecasts`.

### Keep flat

1. alert lists,
2. saved work tables,
3. methodology banners,
4. operational status cards.

## 2. Search: Hybrid Search Workspace

### Role

Unify keyword, filter, semantic, and natural-language discovery in one page.

### Key modules

1. keyword plus filter query builder,
2. multilingual conversational query planner,
3. hybrid result mode switch: `family` vs `publication`,
4. semantic evidence passages,
5. chronology and legal context side panel,
6. save-to-workspace actions.

### Why it belongs

Directly aligns with semantic retrieval requirements, hybrid retrieval direction, and the need for a reusable search workspace.

### Creative UI opportunities

1. A semantic-intent hero where the query resolves into clustered concept groups before results load.
2. A result-space visualization showing how the selected family sits among nearby semantic neighbors.
3. A subtle animated handoff from free-text intent into structured query clauses, making the query planner feel intelligent but still auditable.
4. A small floating-support-object pattern can be used here, but the core search workspace should still stay mostly flat.

### Keep flat

1. the main query builder,
2. result rows,
3. filters,
4. provenance and legal context panels.

## 3. Family Page: Canonical Family Intelligence

### Role

Make the family the default deep-dive object in the product.

### Key modules

1. family summary card,
2. member publication drill-down,
3. raw vs adjusted citation panels,
4. legal-status timeline and point-in-time state,
5. OECD-backed quality and explainability card,
6. top citing applicants and attacker leaderboard,
7. semantic nearest-neighbor section,
8. forecast panel with 3-year and 5-year outlook plus drivers.

### Why it belongs

This is the clearest expression of family-first analytics, explainability, and forecast serving semantics.

### Creative UI opportunities

1. A “family constellation” view where member publications and jurisdictions orbit a central canonical family card.
2. A scroll-synced transition between `historical influence` and `current blocking power`, making the distinction visually obvious.
3. A jurisdiction coverage object or layered map that lights up active territory and fades inactive or lapsed territory.
4. A 3D depth treatment for the legal-status timeline so filings, grants, oppositions, and expiry milestones feel sequential and spatial.
5. A “selected work” style module, inspired by the second video, where the main family card stays central while the right-side panel swaps citation, legal, semantic, or forecast evidence.

### Keep flat

1. evidence tables,
2. member publication lists,
3. raw vs adjusted metric tables,
4. forecast caveat text.

## 4. Portfolio Page: Portfolio Intelligence Workspace

### Role

Replace the old portfolio page with a family-first strategic operating view.

### Key modules

1. top families ranking,
2. filing momentum and grant-mix views,
3. concentration and diversification cards,
4. CPC and field share trend views,
5. forecast rollup built bottom-up from families,
6. crown-jewel families section,
7. reliability banner for incomplete cohorts,
8. optional client-enriched overlays.

### Why it belongs

Matches the V2 portfolio workstream and the forecast V2 aggregation contract.

### Creative UI opportunities

1. A concentration scene where top families orbit the portfolio center and settle into ranked contributors.
2. A portfolio “surface” or layered terrain showing strength by CPC, market, or jurisdiction slice.
3. A cinematic forecast reveal for total future influence, then concentration risk, then top family drivers.
4. An animated patent-cliff or revenue-at-risk story section for optional client-enriched overlays.
5. A bento-style executive grid with one embedded 3D widget is a strong fit here, following the second video’s “3D plus flat cards” pattern.

### Keep flat

1. portfolio rankings,
2. exportable action tables,
3. cohort-reliability banners,
4. owner and assignee metadata grids.

## 5. Compare: Comparison Workspace

### Role

Put all comparative intelligence patterns into one consistent surface.

### Comparison modes

1. owner vs owner,
2. family vs family,
3. portfolio vs portfolio,
4. assignee x family matrix,
5. peer-by-CPC exploration.

### Key modules

1. normalized comparison headers,
2. unit and methodology guardrails,
3. shared vs divergent cluster views,
4. overlap and whitespace summaries,
5. legal and forecast comparison rails,
6. export-ready comparison cards.

### Why it belongs

This is explicitly required by the V2 comparison workstream and the non-overlapping market features note.

### Creative UI opportunities

1. A split-stage comparison hero where two entities occupy mirrored spaces and overlap zones illuminate between them.
2. A scrubbed “raw vs normalized” transition that visually explains why two entities reorder after adjustment.
3. A semantic whitespace field where shared territory stays centered and opportunity gaps appear around the edges.

### Keep flat

1. comparison matrices,
2. methodology caveats,
3. unit labels,
4. drill-down tables.

## 6. Markets: Market And Cluster Intelligence

### Role

Become the flagship exploration surface for trend, cluster, and competitive-intelligence workflows.

### Key modules

1. tech x market filing and grant matrix,
2. explainable cluster labels,
3. top assignee share by cluster,
4. adjusted citation intensity by cluster,
5. field-sliced competitor views,
6. global trend vs local trend split,
7. joint family plus owner clustering pivoted by technology, market, CPC, or assignee.

### Why it belongs

This consolidates the market, cluster, and competitor intelligence threads into one defensible exploration area.

### Creative UI opportunities

1. This is one of the best pages for heavy creative treatment.
2. A 3D cluster atlas where technology domains appear as regions that can be rotated, filtered, and expanded.
3. A market globe or layered territory map that shows global versus local trend divergence.
4. A depth-based competitor field where dominant assignees rise visually within each cluster.
5. A cinematic transition from macro market map into one cluster’s evidence cards and leaderboards.
6. The globe widget pattern from the second video is directly reusable here for high-level market coverage views.

### Keep flat

1. cluster evidence cards,
2. top-assignee tables,
3. methodology and label-rationale panels.

## 7. Forecasts: Predictive Decision Support

### Role

Create a dedicated place for future-looking signals so they are never confused with descriptive current-state metrics.

### Key modules

1. family-level future citation forecast,
2. portfolio-level future influence rollup,
3. expected grant pipeline,
4. lapse and reach-loss outlook,
5. friction exposure,
6. hotspot and cooling-market exposure,
7. confidence band, completeness, and caveat panel,
8. top positive and negative drivers.

### Why it belongs

The forecast notes are detailed enough that this should be a first-class workspace, not a tab buried inside another page.

### Creative UI opportunities

1. A forecast “trajectory” scene showing current state, expected future range, and uncertainty band as a guided path.
2. Driver cards that animate toward or away from the main prediction to show positive and negative pressure.
3. A portfolio forecast composition reveal where the total forecast decomposes into top families and risk concentrations.
4. A timeline section that visually separates present-known facts from future-expected outcomes.
5. A “swap the screen content while the main object stays fixed” pattern from the second video could work well for rotating between forecast horizons, driver groups, or scenario views.

### Keep flat

1. confidence tables,
2. calibration notes,
3. prediction metadata,
4. caveat and completeness blocks.

## 8. Mapping: Interactive Patent Mapping Workspace

### Role

Provide a graph-driven investigation mode for family relationships, influence patterns, and risk clusters.

### Key modules

1. map project setup,
2. map mode switch: `single_landscape`, `multi_landscape`, `family_map`, `interconnection_map`,
3. age- and tech-normalized citation scoring,
4. family expansion and collapse,
5. portfolio evolution timeline,
6. risk, influence, and opportunity overlays,
7. annotation and export tools.

### Why it belongs

This is a strong demo surface and a good communication artifact for judges, clients, and strategy reviews.

### Creative UI opportunities

1. This is the strongest native fit for 3D or pseudo-3D graph interaction.
2. Family and citation interconnection maps can use depth to separate relationship types, time layers, or legal states.
3. A timeline scrubber can animate network growth, conflict zones, and newly appearing nodes.
4. Risk, influence, and opportunity overlays can recolor the same graph without changing its underlying structure.
5. For heavier graph pages, use explicit loader states and responsive scene presets, following the second video’s canvas-loading and device-size approach.

### Keep flat

1. annotation sidebars,
2. export settings,
3. evidence appendices,
4. node detail tables.

## 9. Workspaces: Saved Investigation Folders

### Role

Give the product memory and collaboration.

### Key modules

1. saved entity sets across patents, families, owners, and portfolios,
2. notes, tags, and annotations,
3. snapshots with dated metric captures,
4. share permissions,
5. saved semantic searches and trigger filters,
6. watchlist-style alert rules.

### Why it belongs

Multiple notes point toward saved sets, projects, and collaboration primitives. This should be explicit, not implicit.

### Creative UI opportunities

1. Minimal by default.
2. Use tasteful motion for transitions between saved snapshots, annotations, and watch states.
3. Small 3D preview cards can show what type of workspace this is: compare, mapping, market, or forecast.
4. A flat bento summary with one embedded 3D preview widget is acceptable; anything more is too much for a management page.

### Keep flat

1. lists,
2. notes,
3. tags,
4. sharing controls.

## 10. Reports: Evidence-Backed Storytelling

### Role

Turn analysis into a contest-ready and client-ready narrative artifact.

### Key modules

1. executive summary blocks,
2. methodology and caveat appendix,
3. screenshot-safe cards and tables,
4. comparison summary pages,
5. evidence references and metric provenance,
6. export presets for demo flows.

### Why it belongs

This matches the V2 export and demo storytelling workstream.

### Creative UI opportunities

1. A motion-rich report cover or intro screen for live demo mode.
2. Scroll-based chapter transitions between portfolio, compare, market, and forecast findings.
3. Screenshot-safe “hero evidence cards” with subtle motion in the app, but clean static export states.

### Keep flat

1. exported PDFs,
2. appendices,
3. methodology sections,
4. evidence tables.

## Optional Advanced Pages

## 11. Legal Coverage Workspace

Focus:

1. prosecution timeline,
2. jurisdiction coverage map,
3. UP and UPC exposure,
4. current enforceability vs historical legal history,
5. upcoming deadlines and change triggers.

This page becomes especially valuable once legal-event marts are in place.

### Creative UI opportunities

1. A territory coverage map that lights active rights and dims expired or lapsed coverage.
2. A prosecution tunnel or layered timeline showing progression from filing to grant to expiry-related events.
3. A point-in-time rewind interaction so users can scrub historical legal state safely.

## 12. Financial Intelligence Workspace

Focus:

1. revenue-at-risk timelines,
2. prune-zone and maintenance savings scenarios,
3. R&D efficiency by WIPO field,
4. client-side CSV enrichment flows,
5. public-metric provenance plus client-enriched labels.

This should remain optional and clearly separated from the public-data core.

### Creative UI opportunities

1. Revenue-at-risk cliff animations are a strong fit here.
2. A scenario slider can animate maintenance savings, prune zones, and exposure shifts over time.
3. Use motion sparingly because financial users will prioritize clarity over visual spectacle.
4. Use the second video’s hybrid layout pattern here as well: one animated focal widget, everything else flat and legible.

## Recommended Release Shape

### MVP Top-Level Pages

1. `Home`
2. `Search`
3. `Family`
4. `Portfolio`
5. `Compare`
6. `Markets`
7. `Workspaces`
8. `Reports`

### Phase-2 Pages

1. `Forecasts`
2. `Mapping`
3. `Legal Coverage`
4. `Financial Intelligence`

## Suggested Page Relationships

1. Search resolves inputs to families and hands off into Family, Compare, or Workspaces.
2. Family pages can launch Compare, Forecasts, Mapping, or save into Workspaces.
3. Portfolio pages can launch Markets, Compare, Reports, and optional Financial Intelligence overlays.
4. Markets can launch Family detail, owner comparison, or Workspaces.
5. Reports should be creatable from Family, Portfolio, Compare, Markets, and Mapping.

## UI Notes For The Frontend Team

1. Add a persistent analysis mode indicator for `family-first` vs any fallback publication view.
2. Keep counting-unit labels visible in comparison tables and chart headers.
3. Show caveat metadata inline, not hidden behind docs-only explanations.
4. Separate current-state panels from future-state panels visually and verbally.
5. Avoid oversized navigation depth; use workspace-level subnavigation within each major page.
6. Use strong side panels for evidence, methodology, and drill-downs rather than scattering caveats across the page.
7. The best pages for significant 3D investment are `Markets`, `Mapping`, `Family`, and selected sections of `Portfolio` and `Forecasts`.
8. `Search`, `Workspaces`, and dense `Reports` surfaces should stay mostly flat with restrained motion.
9. Prefer the second video’s hybrid model for most product surfaces: one authored 3D section, then flat cards, grids, and evidence panels.
10. Use `Leva` or an equivalent control surface during development to tune scene transforms before hard-coding responsive presets.

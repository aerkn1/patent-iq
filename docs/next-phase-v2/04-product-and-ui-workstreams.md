# Product And UI Workstreams

## Product Direction

The frontend should stop acting like a loose analytics dashboard and start acting like a guided intelligence workspace.

## Workstream 1: Navigation And Workflow Consolidation

### Goals

1. Keep only high-confidence top-level destinations.
2. Reduce duplicated panels and inconsistent terms.
3. Make family-first mode obvious in the product.

### Tasks

1. Remove or demote weak legacy licensing-first navigation.
2. Introduce a consistent analysis mode indicator.
3. Standardize labels for patent, family, owner, portfolio, and market slices.
4. Show metric caveats inline rather than in hidden documentation.

## Workstream 2: Patent Intelligence Experience

### Goals

1. Present single-patent intelligence as family-aware and explainable.
2. Preserve drill-down into member publications.

### Tasks

1. Add family summary card.
2. Show raw vs adjusted citation panels.
3. Add quality/explainability panel with OECD-backed context.
4. Add family member and citing-applicant drill-downs.

## Workstream 3: Portfolio Intelligence Experience

### Goals

1. Reframe the portfolio page around top families, filing momentum, stage mix, and concentration.
2. Make trends defensible under scrutiny.

### Tasks

1. Add top families ranking and family-level citation evolution.
2. Add filing momentum and grant-mix visuals.
3. Add CPC share trend and concentration cards.
4. Add reliability banner for incomplete cohorts.

## Workstream 4: Comparison Workspaces

### Goals

1. Create product surfaces that make competitive intelligence obvious.
2. Compare owners, families, and tech segments in one consistent pattern.

### Tasks

1. Build company comparison workspace.
2. Build assignee-to-family comparison matrix.
3. Add peer-by-CPC exploration.
4. Add family-vs-family or patent-vs-family comparison summary.

## Workstream 5: Market Intelligence

### Goals

1. Turn point-in-time market and field-condition analytics into a contest differentiator.
2. Keep every insight tied to evidence and methodology.

### Tasks

1. Add `Market Intelligence` workspace with point-in-time field, segment, cluster, and jurisdiction conditions.
2. Add tech x market filing/grant trend matrix.
3. Add explainable market-state labels and badges such as rising/cooling/stable.
4. Support pivots by technology, market, CPC, assignee, and jurisdiction.
5. Show top assignee share, blocking density, citation intensity, and whitespace/saturation across market slices.

## Workstream 6: Export And Demo Storytelling

### Goals

1. Produce artifacts judges can understand quickly.
2. Preserve traceability from narrative claims to evidence.

### Tasks

1. Build report layout with summary, methodology, evidence appendix.
2. Add one-click demo export states for key workflows.
3. Prepare screenshot-safe cards and tables.
4. Support degraded-mode fallback when some data layers are unavailable.

## Workstream 7: Data Room And Methodology Transparency

### Goals

1. Make PatentIQ auditable and contest-friendly.
2. Let judges inspect data, lineage, metrics, models, and semantic evidence without leaving the app.

### Tasks

1. Build the in-app `Data Room` workspace.
2. Add wiki-style methodology pages for sources, pipeline, metrics, models, and semantic layers.
3. Add read-only dataset catalog with schema previews and downloads.
4. Surface active manifests, scope metadata, and build/version badges.
5. Keep the Data Room read-only and clearly separated from normal analysis workflows.

## UI Acceptance Rules

1. No chart without caveat metadata where caveats apply.
2. No score without interpretation and underlying components.
3. No cluster label without evidence or label rationale.
4. No comparison table that mixes counting units silently.

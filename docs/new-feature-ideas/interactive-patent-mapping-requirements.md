# Feature Idea: Interactive Patent Mapping Workspace (IPVision-Informed)

## Source
- Page: [IPVision - Interactive Patent Mapping](https://www.ipvisioninc.com/interactive-patent-mapping/)
- Accessed: March 5, 2026

## Goal
Convert key interactive patent mapping principles into concrete product requirements for PatentIQ.

## Key Nuances Extracted
1. Patent importance must be evaluated in context, not by raw citation counts alone.
2. Mapping should support multiple analysis modes:
   - Single patent landscape map
   - Multi-patent/full landscape map
   - Patent family map
   - Patent interconnection map
3. Citation influence should be normalized by patent age and technology segment (relative citation frequency concept).
4. Family analysis should capture continuations, divisionals, priority links, and foreign counterparts.
5. Mapping is decision-focused: identify patent risk, relevance, and strategy options.
6. Multi-patent mapping should show portfolio evolution over time.
7. Visual maps are not only analytical tools; they are communication artifacts for strategic reporting.

## Product Requirements

### PRD-IPM-01: Mapping Project Setup
**Requirement**
Allow users to define seed patents, technology scope, jurisdiction, and time window before generating a map.

**Acceptance Criteria**
1. Users can create/save a map project with versioned scope settings.
2. Required setup fields are validated before map generation.
3. Users can duplicate prior setups for iterative analysis.

### PRD-IPM-02: Multi-Mode Mapping Engine
**Requirement**
Support four map modes: `single_landscape`, `multi_landscape`, `family_map`, `interconnection_map`.

**Acceptance Criteria**
1. Users can switch map modes without rebuilding the project.
2. Each mode renders the correct node/edge semantics.
3. Drill-down from node to patent/family details is available.

### PRD-IPM-03: Contextual Citation Scoring
**Requirement**
Implement age- and technology-normalized citation scoring to complement raw citation totals.

**Acceptance Criteria**
1. Every patent node exposes raw and normalized citation metrics.
2. Normalization method and peer group are transparent.
3. Rankings can be toggled between raw and normalized views.

### PRD-IPM-04: Patent Family Resolution
**Requirement**
Resolve family structures across priority, continuation, divisional, and international relationships.

**Acceptance Criteria**
1. Family graph groups related filings and grants into a coherent cluster.
2. Users can expand/collapse family members.
3. Cross-jurisdiction relationships are visible and filterable.

### PRD-IPM-05: Portfolio Evolution Timeline
**Requirement**
Provide a timeline layer to analyze how citation and relationship networks evolve from a seed set.

**Acceptance Criteria**
1. Users can scrub by year/date range.
2. Map highlights newly added nodes/edges per period.
3. Changes can be exported as a delta summary.

### PRD-IPM-06: Risk/Relevance Strategy Overlay
**Requirement**
Overlay actionable insights for risk hotspots, influential assets, and strategic relevance.

**Acceptance Criteria**
1. Nodes receive risk/relevance tags with evidence links.
2. Users can filter map by strategy view (`risk`, `influence`, `opportunity`).
3. Summary panel translates map patterns into recommended actions.

### PRD-IPM-07: Interactive Graph UX
**Requirement**
Deliver performant, analyst-friendly interactions (zoom, pan, neighborhood expansion, filtering).

**Acceptance Criteria**
1. Graph supports zoom/pan/select with stable performance.
2. Users can isolate ego-network around selected patents.
3. Filters (jurisdiction, assignee, date, legal status) update graph in-session.

### PRD-IPM-08: Reporting and Collaboration
**Requirement**
Enable exportable, narrative-ready outputs from map states.

**Acceptance Criteria**
1. Current map view exports to image/PDF plus data appendix.
2. Report includes assumptions and scoring methodology.
3. Comments/annotations can be attached to nodes and saved by revision.

## Inferred Requirements (Not Explicitly Stated on Page)
1. Explainability metadata for every score and map relationship.
2. Snapshot versioning to reproduce past analyses.
3. Role-based access for internal/external sharing.

## MVP Scope (Suggested)
1. PRD-IPM-01 Mapping Project Setup
2. PRD-IPM-02 Multi-Mode Mapping Engine
3. PRD-IPM-03 Contextual Citation Scoring
4. PRD-IPM-04 Patent Family Resolution
5. PRD-IPM-07 Interactive Graph UX
6. PRD-IPM-08 Reporting and Collaboration (basic export)


# Additional Market-Driven Features (Non-Overlapping Set)

## Scope
These items were filtered to avoid overlap with existing definitions in:
- `patent-landscape-analysis-requirements.md`
- `interactive-patent-mapping-requirements.md`
- `patent-expert-findings-revised-definitions.md`

## Cross-Cutting Constraints
1. Use family-level aggregation as default for analytics outputs.
2. Use family earliest priority date for trend timelines and cohorting.
3. Exclude intra-family self-citations from impact/scoring metrics.
4. Show both raw and adjusted citation metrics where exclusions apply.
5. Treat family size/jurisdiction spread as a value-intent signal, not standalone value proof.

## Net-New Feature Definitions

### MKT-01: Multi-Field Semantic Retrieval
Definition: Add vector/semantic search across `title`, `abstract`, `description`, and `claims` at publication and family granularity.

Non-overlap note: Existing docs define boolean/search strategy and mapping workflows, but do not define embedding-based retrieval.

Key requirements:
1. Hybrid retrieval (`keyword + semantic`) with weight tuning.
2. Result mode switch: `publication` vs `family`.
3. Source scope filter: `EPO`, `USPTO`, or combined corpus.

### MKT-02: Semantic Similarity & Text-to-Patent Matching
Definition: Let users compare documents semantically (patent-to-patent, patent-to-text) and retrieve nearest matches for a user-provided text brief.

Non-overlap note: Existing “compare patents” is metric-based; this adds embedding-based similarity.

Key requirements:
1. Input supports patent ID(s) or free text.
2. Output includes similarity score and top semantic evidence passages.
3. Works at publication and family levels.

### MKT-03: Rule-Based Ranking Filters (Date Triggers)
Definition: Add ranking filters driven by temporal/legal conditions (example: “expiring within 30 days”).

Non-overlap note: Existing ranking, trend, and stage-mix features do not include trigger-style deadline filters.

Key requirements:
1. Preset filters (`expires_30d`, `expires_90d`, `recent_grant`, `status_changed`).
2. Sort by urgency and impact score.
3. Saved filter presets per user/workspace.

### MKT-04: Prosecution Timeline View
Definition: Add an event timeline per patent/family from earliest priority filing through publication, grant, legal events, and expiry milestones.

Non-overlap note: Existing timeline definitions focus on citation/network evolution, not legal/prosecution chronology.

Key requirements:
1. Unified timeline with jurisdiction-specific events.
2. Milestone deltas (days between key stages).
3. Portfolio rollup view of upcoming timeline events.

### MKT-05: User Track Folders / Workspaces
Definition: Allow users to create named workspaces (track folders) containing patents, families, and portfolios for ongoing analysis.

Non-overlap note: Existing docs mention watchlists and analysis projects; this adds user-curated cross-entity collections with reusable context.

Key requirements:
1. Add/remove entities to folders with notes and tags.
2. Save snapshots of metrics at time of capture.
3. Share folder read-only/edit with team members.

### MKT-06: Multilingual Conversational Query Builder Agent
Definition: Let users describe search intent in any language (for example, “Find patents about drones and batteries”), then auto-generate and iteratively refine an English patent query with synonyms, IPC/CPC classes, and jurisdiction filters.

Non-overlap note: Existing docs cover boolean query editing and AI copilot support, but do not define end-to-end multilingual NL-to-query agent behavior with iterative constraint editing.

Key requirements:
1. Accept natural-language prompts in multiple languages and normalize to a canonical English query plan.
2. Auto-suggest synonyms, controlled vocabulary terms, IPC/CPC candidates, and searchable query clauses.
3. Support conversational refinement commands: add/remove keywords, classes, jurisdictions, assignees, inventors, filing-date windows, and status filters.
4. Show full generated query string and rationale before execution (editable by user).
5. Preserve query revision history for reproducibility and auditability.

### MKT-07: Assignee-to-Family Comparison Matrix
Definition: Add a comparison workspace that analyzes assignees/owners and patent families in the same frame, so users can compare which families anchor each owner, where owners compete in the same segments, and where portfolio coverage diverges.

Non-overlap note: Existing docs define company comparison, CPC peer exploration, and family ranking, but do not define a direct assignee x family comparison surface.

Key requirements:
1. Compare selected assignees across owned families, top family clusters, filing/grant mix, and adjusted citation impact.
2. Show overlap modes for `shared ownership`, `same CPC/market competition`, and `portfolio gaps`.
3. Support drill-down from assignee summary to family set to member patents/publications.

### MKT-08: Joint Family + Owner Clustering by Tech/Market/CPC
Definition: Cluster patent families and assignees/owners into shared technology and market groups using CPC/IPC tags, semantic text similarity, and geography/market signals.

Non-overlap note: Existing landscape docs mention technology clustering and tech x market trend analytics, but do not define a joint family-plus-owner clustering model with explainable cluster labels.

Key requirements:
1. Cluster at family-first granularity, then roll up assignees by family membership share within each cluster.
2. Each cluster exposes explainable labels from dominant CPCs, keywords, and market/jurisdiction metadata.
3. Users can pivot the same cluster set by `technology`, `market`, `CPC`, or `assignee`.
4. Each cluster shows concentration metrics such as family count, top-assignee share, grant rate, and adjusted citation intensity.

## Priority Suggestion
1. **P0**: MKT-01, MKT-02, MKT-06
2. **P1**: MKT-07, MKT-08, MKT-03, MKT-04
3. **P2**: MKT-05

## Overlap Mapping Update (March 7, 2026)
Input idea: `tech and market based trend analytics based on total filing/granting rates`.

Mapping result: **Not net-new** (overlaps existing definitions).
1. `R-11`: tech-domain trend layer,
2. `R-17`: application vs granted mix,
3. `R-18` + `R-20`: filing trend backbone using family-priority date,
4. `PMC-05` + `PMC-16`: pendency-adjusted grant-rate methodology and endpoint contract.

## Overlap Mapping Update (March 7, 2026, Assignee-Family Comparison)
Input idea: `assignee/patent-family comparison between patent-families and assignees` and `classifying/clustering the families and assignee/owners under similar/same tech/market/cpc sections`.

Mapping result: **Partially overlapping, refined into net-new additions**.
1. Overlaps with `PRD-PLA-04` for assignee leaderboard and technology cluster map.
2. Overlaps with `R-08`, `R-09`, and `R-23` for company comparison, CPC peer exploration, and tech-level family ranking.
3. Overlaps with `PMC-16` where clustered views need to align with tech x market trend slices.
4. Net-new scope is captured by `MKT-07` and `MKT-08`: explicit assignee x family comparison and joint family-owner clustering contracts.

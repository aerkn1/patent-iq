# Scope And Release Definitions

## Release Goal

Ship a coherent intelligence platform rather than a loose collection of analytics widgets.

## Contest Release Scope

### Intelligence foundation

1. Family-first counting and ranking.
2. Family-aware citations and adjusted citation transparency.
3. Earliest-priority-date trend backbone.
4. Legal status and renewal context.
5. Assignee harmonization and basic corporate rollup.

### Product workflows

1. Single patent intelligence.
2. Portfolio intelligence.
3. Company comparison workspace.
4. Assignee-to-family comparison matrix.
5. Tech and market trend exploration.
6. Family and owner clustering by CPC/tech/market.
7. Exportable report and demo narrative output.

### Reliability layer

1. `counting_unit`
2. `family_model`
3. `lag_warning`
4. `data_completeness_pct`
5. `overlap_policy`
6. `score_components`
7. `cohort_key`

### ML intelligence layer

1. Rebuilt citation prediction feature table aligned to V2 entities.
2. Retrained 3-year and 5-year forecast models.
3. Calibrated uncertainty intervals with subgroup coverage checks.
4. Explainable feature contribution outputs for UI and QA review.

## Scope Mapped To Source Requirements

### Core rebuild set

1. `R-02`, `R-03`, `R-04`, `R-12`, `R-14`, `R-20`, `R-21`, `R-22`
2. `DAP-01`, `DAP-02`, `DAP-03`, `DAP-05`, `DAP-06`, `DAP-07`, `DAP-11`, `DAP-12`, `DAP-13`
3. `PMC-01`, `PMC-04`, `PMC-05`, `PMC-06`, `PMC-09`, `PMC-13`, `PMC-14`, `PMC-16`

### Contest differentiator set

1. `R-05`, `R-08`, `R-09`, `R-11`, `R-13`, `R-17`, `R-18`, `R-19`, `R-23`
2. `MKT-07`, `MKT-08`
3. `PRD-PLA-04`, `PRD-PLA-07`, `PRD-PLA-09`

## Product Definition Clusters

### Cluster A: Family Intelligence Core

Definition:
Patent and portfolio analytics operate at family level by default and explain the relationship between family breadth, citations, status, and trend.

Includes:
1. Top cited families,
2. Family citation evolution,
3. Family ranking within CPC/tech clusters,
4. Family drill-down to publications.

### Cluster B: Assignee Intelligence Core

Definition:
Assignee analytics represent harmonized ownership, parent-rollup, and owner-level comparison against family assets and technology segments.

Includes:
1. Assignee harmonization,
2. Parent entity rollups,
3. Company comparison workspace,
4. Assignee-to-family comparison matrix,
5. Ranked citing applicants.

### Cluster C: Trend And Market Intelligence

Definition:
All trend surfaces must combine family-priority chronology, market context, and explicit lag/pendency caveats.

Includes:
1. Filing momentum,
2. Application vs granted mix,
3. CPC share evolution,
4. Tech x market filing/grant trend matrix,
5. Data completeness and lag warnings.

### Cluster D: Quality And Explainability

Definition:
OECD-style indicators are available as evidence-backed context, not opaque truth scores.

Includes:
1. Cohort-normalized quality indicators,
2. Component-level explanations,
3. Office-specific availability rules,
4. Cross-cohort comparison restrictions.

### Cluster E: Insight And Export Layer

Definition:
The platform converts analysis outputs into narrative-ready artifacts without hiding uncertainty.

Includes:
1. AI-assisted insight draft,
2. Cluster labels with evidence,
3. Report export,
4. Demo-ready summary cards and evidence appendix.

### Cluster F: Forecast And Model Intelligence

Definition:
Citation forecasting must be retrained on richer, family-aware, market-aware, and quality-aware features so the prediction layer reflects the same product logic as the rest of the platform.

Includes:
1. V2 feature marts,
2. family-aware and legal-aware signals,
3. OECD-normalized quality features,
4. cohort-aware validation and calibration,
5. explainable prediction outputs.

## Explicit Deferrals

The following are outside contest-critical scope unless almost complete by Week 4:

1. Full claim-faithful cross-jurisdiction semantic retrieval rollout,
2. Multilingual query builder,
3. SEP and standards-body mapping,
4. Full litigation expansion beyond existing available signals,
5. Inventor-level analytics,
6. Full interactive network mapping.

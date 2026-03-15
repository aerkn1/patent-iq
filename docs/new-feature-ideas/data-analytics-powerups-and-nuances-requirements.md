# Data Analytics Power-Ups & Nuances (Professional-Grade Patent Intelligence)

## Scope
This document translates additional data-analytics nuances into implementation-ready requirements for PatentIQ.

## Essential Data Power-Ups

### DAP-01: Global Legal Status Layer (INPADOC)
Definition: Enrich each family with country-level legal status (`active`, `expired`, `lapsed`, `pending`) across major jurisdictions.

Why it matters: Detect strategic retreat (example: EP still alive while US/CN family members are lapsed).

### DAP-02: Standardized Assignee / Corporate Tree Layer
Definition: Normalize assignee names and link subsidiaries to parent entities (corporate tree resolution).

Why it matters: Prevent fragmented portfolio analytics across legal entities.

### DAP-03: Citation Metadata Layer (Forward & Backward)
Definition: Store structured citation graph metadata for forward/backward citations at publication and family levels, including assignee of citing/cited entity.

Why it matters: Forward citations proxy value; backward citations proxy technical crowdedness.

### DAP-04: Renewal / Maintenance Fee Layer
Definition: Add renewal-payment continuity signals by jurisdiction and family age.

Why it matters: Continued payment is a strong commercial-importance signal.

## Critical Data Collection Nuances

### DAP-05: Explicit Family Model Selection
Definition: Support and label analytics by selected family model:
1. `DOCDB_SIMPLE` for strict invention-level R&D analysis.
2. `INPADOC_EXTENDED` for legal/strategic relationship analysis.

Constraint: No mixed-family-model aggregation in the same KPI/chart unless explicitly dual-reported.

### DAP-06: 18-Month Publication Black-Hole Handling
Definition: Add mandatory UI and metric logic for publication lag bias.

Requirements:
1. Disclaimer on recent-year trend charts.
2. Optional projected/nowcast line for incomplete periods.
3. “Data completeness %” indicator per year.

### DAP-07: Self-Citation Scrubbing (Company-Level)
Definition: Exclude company self-citations from impact scoring by default, with toggle to view raw.

Constraint: Combine with intra-family exclusion already defined in prior docs.

## Advanced Intelligence Mapping

### DAP-08: SEP Declaration Mapping
Definition: Link families to Standard Essential Patent declarations (for example, ETSI).

Output: SEP flag, declared standard, and confidence level.

### DAP-09: Litigation History Mapping
Definition: Attach litigation/opposition history to patent families.

Output: case count, jurisdictions, latest outcome status, risk score contribution.

### DAP-10: Technical Standards Mapping
Definition: Map patent families to standards bodies/spec references (for example, IEEE, 3GPP where applicable).

Output: standards coverage graph and dominance indicators by portfolio.

## OECD Patent Quality Dataset Integration

### DAP-11: OECD Quality Indicator Layer
Definition: Ingest OECD-style quality indicators (scope, family size, grant lag, backward/NPL citations, claims, forward citations, breakthrough, generality, originality, radicalness, renewal, quality index composites) as a benchmark layer.

Why it matters: Provides a tested external methodology for cohort-aware quality analytics and comparative scoring.

Constraints:
1. backward patent citations and backward NPL citations must remain separately stored and labeled,
2. patent-citation metrics feed crowdedness, dependency, and patent-network impact logic,
3. backward NPL metrics feed science-grounding and research-intensity interpretation,
4. NPL references must not be silently blended into current blocking-power citation impact.

### DAP-12: Cohort Normalization Contract (Filing Year + Tech Field)
Definition: Require all OECD-derived metrics to support cohort-normalized values by `(filing, tech_field)`.

Requirements:
1. Expose both raw value and cohort-relative percentile/z-score.
2. Label office source (`EPO`, `USPTO`) and cohort sample size.
3. Block unsupported cross-cohort direct comparisons in UI/API.

### DAP-13: OECD Usage Cautions
Definition: Apply strict caveats when using OECD indicators in product scoring.

Rules:
1. Recent-year forward citation and grant-lag indicators are lag-biased (timeliness/truncation).
2. `many_field=1` implies non-exclusive field assignment; field totals may exceed unique totals.
3. `quality_index_4` and `quality_index_6` are composite proxies and must remain explainable by components.
4. `renewal` must be interpreted together with jurisdiction legal-status events before strategic conclusions.

## Cross-Cutting Implementation Rules
1. Family-level analytics is default; publication-level is drill-down.
2. Trend baselines use earliest family priority date.
3. Show both raw and adjusted citations (self/intra-family scrubbed).
4. Every KPI must show data provenance and family model label.

## Priority Suggestion
1. **P0**: DAP-01, DAP-02, DAP-03, DAP-05, DAP-06, DAP-07, DAP-12
2. **P1**: DAP-04, DAP-09, DAP-11
3. **P2**: DAP-08, DAP-10, DAP-13

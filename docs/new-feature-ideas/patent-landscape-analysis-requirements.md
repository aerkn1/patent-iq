# Feature Idea: Patent Landscape Analysis Workspace (2025 Guide-Informed)

## Source
- Article: [PatSnap - The Definitive Guide to Patent Landscape Analysis (2025)](https://www.patsnap.com/resources/blog/articles/patent-landscape-analysis-guide-2025/)
- Accessed: March 5, 2026

## Goal
Translate the key nuances of modern patent landscape analysis into concrete product requirements for PatentIQ.

## Key Nuances Extracted
1. Patent landscape analysis is a strategic workflow, not a single report; it requires iterative refinement of scope, search strategy, and insights.
2. Scope definition is critical: objective, market/technology boundary, geography, and time window materially change outcomes.
3. Data quality drives trust: deduplication, legal-status normalization, family-level grouping, and relevance filtering are mandatory.
4. Analysis must combine quantitative and qualitative views:
   - Filing trends over time
   - Geographic concentration
   - Top assignees/inventors
   - Technology clustering and whitespace detection
   - Citation influence and legal status context
5. Competitive intelligence and freedom-to-operate use cases require alerting and ongoing monitoring, not one-off snapshots.
6. Stakeholders need narrative-ready outputs (executive summary + evidence) for R&D planning, licensing, and M&A decisions.
7. AI support is valuable when it accelerates classification, summarization, and insight generation while keeping analyst control.
8. Actionability matters: findings must map to decisions (invest, design-around, partner, acquire, defend, or abandon).

## Product Requirements

### PRD-PLA-01: Analysis Setup Wizard
**Requirement**
Provide a guided setup that captures analysis objective, technology keywords, CPC/IPC filters, assignee scope, jurisdictions, and date range.

**Acceptance Criteria**
1. User can create an analysis project with all required scope fields.
2. System blocks run if mandatory fields are missing.
3. Project configuration is versioned so users can compare scope revisions.

### PRD-PLA-02: Search Strategy Builder
**Requirement**
Support boolean query building with previewed recall/precision signals and reusable templates.

**Acceptance Criteria**
1. Query editor supports boolean operators and field-specific search.
2. Preview shows estimated result volume before full run.
3. Users can save, duplicate, and baseline query versions.

### PRD-PLA-03: Patent Data Quality Layer
**Requirement**
Implement automatic family deduplication, legal-status harmonization, and confidence scoring on relevance.

**Acceptance Criteria**
1. Family-level and publication-level views are both available.
2. Legal status is normalized into a consistent taxonomy.
3. Every record displays a relevance/confidence score with traceable rationale.

### PRD-PLA-04: Multi-Dimensional Analytics
**Requirement**
Deliver standard landscape views: filing trend, jurisdiction heatmap, assignee leaderboard, technology cluster map, and citation network.

**Acceptance Criteria**
1. Dashboard includes all five default views.
2. All charts are filter-linked and update within a single interaction cycle.
3. Users can drill from any visualization to underlying patent sets.

### PRD-PLA-05: Whitespace & Saturation Detection
**Requirement**
Identify under-patented areas (whitespace) and crowded zones (saturation) by combining taxonomy coverage and filing density.

**Acceptance Criteria**
1. Platform computes whitespace score per cluster/topic.
2. User can inspect supporting patents for each score.
3. Methodology notes are visible for auditability.

### PRD-PLA-06: Competitor & Watchlist Monitoring
**Requirement**
Enable persistent watchlists for companies, inventors, and technologies with alerting on material changes.

**Acceptance Criteria**
1. Users can define watchlists with configurable triggers.
2. Alerts fire for new filings, status changes, and citation spikes.
3. Alert digest is available in-app and exportable.

### PRD-PLA-07: AI Copilot for Analyst Workflow
**Requirement**
Add AI-assisted claim/theme summarization, cluster labeling, and “insight draft” generation with source traceability.

**Acceptance Criteria**
1. AI outputs always link to source patents/evidence.
2. Analyst can accept/edit/reject each AI suggestion.
3. No insight can be exported without evidence references.

### PRD-PLA-08: Decision Mapping Layer
**Requirement**
Convert findings into recommended strategic actions with confidence and risk flags.

**Acceptance Criteria**
1. System supports decision tags: `invest`, `design-around`, `license`, `partner`, `acquire`, `defend`, `deprioritize`.
2. Each recommendation includes evidence summary and risk notes.
3. Users can track decision outcomes over time.

### PRD-PLA-09: Reporting & Collaboration
**Requirement**
Generate executive-ready reports that include narrative summary, key charts, assumptions, and appendix evidence.

**Acceptance Criteria**
1. One-click report generation for PDF/slide-compatible format.
2. Reports include explicit assumptions and methodology section.
3. Comments and approvals are tracked per report revision.

### PRD-PLA-10: Continuous Landscape Refresh
**Requirement**
Support scheduled reruns with delta analysis to maintain “living landscape” visibility.

**Acceptance Criteria**
1. Users can set refresh cadence (weekly/monthly/quarterly).
2. Delta view highlights added/removed/changed records and insights.
3. Historical snapshots remain accessible for comparison.

## Non-Functional Requirements
1. Explainability: Every metric and AI insight must expose contributing evidence.
2. Performance: Standard dashboard interactions should complete within target SLA (to be defined by engineering benchmark).
3. Governance: Role-based access and export controls for sensitive analyses.
4. Reproducibility: Identical query + scope + snapshot should yield reproducible outputs.

## MVP Scope (Suggested)
1. PRD-PLA-01 Analysis Setup Wizard
2. PRD-PLA-02 Search Strategy Builder
3. PRD-PLA-03 Data Quality Layer
4. PRD-PLA-04 Multi-Dimensional Analytics
5. PRD-PLA-09 Reporting (basic)

## Phase 2 Scope (Suggested)
1. PRD-PLA-05 Whitespace Detection (advanced scoring)
2. PRD-PLA-06 Monitoring + alert intelligence
3. PRD-PLA-07 AI Copilot
4. PRD-PLA-08 Decision mapping and outcome tracking
5. PRD-PLA-10 Continuous refresh automation

## Success Metrics
1. Time-to-first-insight reduction (% vs current workflow).
2. Analyst hours saved per landscape study.
3. Precision@top-N for relevance and cluster assignment.
4. Percentage of insights accepted by analysts without major rework.
5. Executive report turnaround time.


# PatentIQ V2 Report Generation Use Cases And Contract

## Purpose

Define the report-generation capabilities PatentIQ V2 should support, how those reports should be composed from current Silver/Gold and future model outputs, how client-enriched overlays fit into the report system, and how the UI and backend should expose report generation.

This note treats report generation as a `first-class product workflow`, not as an afterthought export button.

---

## 1. Core Position

PatentIQ V2 should support report generation because:

1. users need shareable outputs for executives, counsel, and strategy teams,
2. the platform is increasingly evidence-first and family-first,
3. methodology and caveat transparency are already core V2 requirements,
4. jury/demo settings benefit strongly from polished, exportable intelligence summaries.

Reports should never be:

1. raw screenshots of UI pages,
2. unstructured PDF dumps,
3. context-free score sheets,
4. silently client-enriched without disclosure.

Reports should be:

1. structured,
2. evidence-backed,
3. versioned,
4. provenance-aware,
5. explicit about assumptions and caveats.

---

## 2. Supported Report Families

PatentIQ V2 should support at least the following report families.

## 2.1 Family Intelligence Report

Purpose:

1. explain the current and historical strategic profile of a single family,
2. provide a compact invention dossier,
3. support diligence, strategy review, and internal briefing.

## 2.2 Publication Evidence Report

Purpose:

1. support a publication-level legal/evidence drilldown,
2. anchor a family report in a specific representative publication when needed,
3. support register/legal review.

## 2.3 Portfolio Intelligence Report

Purpose:

1. summarize a company / assignee portfolio,
2. highlight top families, strengths, weaknesses, and concentration,
3. support management and strategic review.

## 2.4 Compare Report

Purpose:

1. compare family vs family,
2. compare portfolio vs portfolio,
3. compare the same entity across time,
4. support board or investment-style side-by-side review.

## 2.5 Market Intelligence Report

Purpose:

1. summarize the state of a field or market segment,
2. show trend direction, segment temperature, leaders, and crowding,
3. support innovation and strategy planning.

## 2.6 Semantic Search / Similarity Report

Purpose:

1. capture semantic search results for a query or anchor family,
2. preserve the legal/status context around retrieved neighbors,
3. support research and analyst review.

## 2.7 Forecast Report

Purpose:

1. explain `3y` and `5y` future influence predictions,
2. show drivers, intervals, and caveats,
3. support product strategy and portfolio planning.

## 2.8 Client-Enriched Executive Report

Purpose:

1. combine public patent intelligence with optional client inputs,
2. support revenue-at-risk, pruning ROI, and R&D efficiency workflows,
3. clearly disclose all client-provided assumptions and inputs.

---

## 3. Export Modes

PatentIQ should support more than one report mode.

## 3.1 On-Screen Share View

Characteristics:

1. lightweight,
2. browser-friendly,
3. permalink-based,
4. good for review sessions.

## 3.2 Print / PDF Report

Characteristics:

1. paginated,
2. boardroom / jury / counsel friendly,
3. includes methodology appendix,
4. optimized for clean printing and sharing.

## 3.3 Structured Export Package

Characteristics:

1. JSON + selected CSV tables + metadata,
2. useful for downstream client workflows,
3. should include provenance and version stamps.

## 3.4 Slide-Friendly Executive Summary

Characteristics:

1. condensed headline cards,
2. fewer tables,
3. narrative-first,
4. still caveated and sourced.

This can be a specialized presentation-oriented variant of the PDF report.

---

## 4. Report Composition Principles

Every report should be built from the same base principles.

## 4.1 Evidence First

Every major interpretation should be traceable back to:

1. current metrics,
2. history outputs,
3. supporting tables,
4. source/provenance metadata.

## 4.2 Caveats Always Visible

If the underlying data has limitations, the report must say so.

Examples:

1. sampled semantic corpus,
2. claim-backed vs abstract-backed semantic coverage,
3. historical metrics vs current-only metrics,
4. client-enriched assumptions,
5. missing family linkage,
6. incomplete forecast coverage.

## 4.3 Versioned Outputs

Every report should be stamped with:

1. report type,
2. generation timestamp,
3. Gold release id,
4. model release id if used,
5. semantic release id if used,
6. client dataset id if used.

## 4.4 Family-First Default

Where possible:

1. reports should center on family-level interpretation,
2. publication-level details should appear as evidence drilldown.

---

## 5. Current Data Support By Report Type

## 5.1 Strongly Supported Now

1. Family intelligence report
2. Publication evidence report
3. Portfolio intelligence report
4. Compare report
5. Market intelligence report
6. Partial semantic report on currently available semantic artifacts
7. Partial forecast report once Phase 03 serving is promoted

## 5.2 Supported As Client-Enriched Overlay

1. Revenue-at-risk report
2. Pruning ROI report
3. R&D efficiency report
4. Executive business overlay report

## 5.3 Not Yet Strong Enough As Current Native Report

1. direct monetary valuation report
2. licensing-value report
3. damages or DCF report

These should remain out of the V2 core reporting contract until dedicated data/model support exists.

---

## 6. Report Type 1: Family Intelligence Report

## Inputs

Public inputs:

1. [gold_family_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_summary.parquet)
2. [gold_family_blocking_power.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power.parquet)
3. [gold_family_heritage_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_heritage_summary.parquet)
4. [gold_family_attacker_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_attacker_summary.parquet)
5. [gold_family_blocking_power_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_blocking_power_timeseries.parquet)
6. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)
7. [silver_family_status_history.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_status_history.parquet)

Optional model inputs later:

1. family forecast outputs
2. semantic similarity context

## Section Order

1. cover / identity
2. executive summary
3. current profile
4. legal and coverage state
5. field and market footprint
6. trajectory over time
7. evidence tables
8. caveats and methodology

## Best Components

1. headline KPI strip
2. current-vs-history cards
3. dual-timeseries chart
4. ranked field contribution table
5. legal timeline summary
6. family member publication table
7. methodology appendix card

## Output

1. PDF dossier
2. shareable HTML report
3. JSON export for downstream systems

---

## 7. Report Type 2: Publication Evidence Report

## Inputs

1. publication-level bibliographic sources
2. EP register evidence marts where applicable
3. family context joins

## Section Order

1. publication identity
2. bibliographic evidence
3. claims / abstract evidence
4. legal timeline
5. family context
6. provenance

## Use

This should be a narrower, evidence-heavy report rather than a broad strategic report.

---

## 8. Report Type 3: Portfolio Intelligence Report

## Inputs

1. [gold_portfolio_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_summary.parquet)
2. [gold_portfolio_threat_matrix.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_threat_matrix.parquet)
3. [gold_portfolio_forecast_summary.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_forecast_summary.parquet)
4. [gold_portfolio_field_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_portfolio_field_timeseries.parquet)
5. [silver_family_owner_bridge.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/silver/silver_family_owner_bridge.parquet)

## Section Order

1. portfolio identity and scope
2. executive summary
3. top families
4. field and momentum profile
5. threat and attacker profile
6. forecast and concentration
7. drilldown tables
8. caveats and methodology

## Best Components

1. portfolio KPI header
2. top family ranked table
3. field exposure treemap or bar chart
4. concentration and fragility cards
5. threat matrix slice
6. forecast contributor table
7. compare-over-time appendix

## Output

1. board-style PDF
2. strategy review HTML report
3. JSON + CSV package

---

## 9. Report Type 4: Compare Report

## Supported Compare Modes

1. family vs family
2. portfolio vs portfolio
3. family `current vs selected year`
4. portfolio `current vs selected year`
5. `current vs projected` when forecast is active

## Inputs

Use the same underlying marts as the family and portfolio reports, plus history marts.

## Section Order

1. compare header
2. mirrored summary cards
3. normalized profile comparison
4. delta tables
5. supporting timeseries
6. evidence-by-entity
7. methodology and caveats

## Best Components

1. mirrored KPI cards
2. radar for compare mode only
3. delta tables
4. aligned timeseries charts
5. side-by-side evidence tables

## Rules

1. no radar for single-entity reports,
2. radar is allowed here because compare is the point,
3. historical axes must use only historically supportable metrics.

---

## 10. Report Type 5: Market Intelligence Report

## Inputs

1. [gold_market_intelligence_overview.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_overview.parquet)
2. [gold_market_intelligence_segments.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_segments.parquet)
3. [gold_market_intelligence_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_market_intelligence_timeseries.parquet)
4. [gold_family_field_contributions_timeseries.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_family_field_contributions_timeseries.parquet)

## Section Order

1. executive market state
2. segment ranking and temperature
3. historical trend
4. leader entities and families
5. crowding / threat context
6. methodology and field definitions

## Best Components

1. overview cards
2. ranked segment table
3. segment state chart
4. trend lines
5. leader tables

---

## 11. Report Type 6: Semantic Search / Similarity Report

## Inputs

1. semantic query or anchor family
2. [gold_semantic_match_context.parquet](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/gold/gold_semantic_match_context.parquet)
3. current semantic embedding release and ANN metadata

## Section Order

1. query definition
2. corpus scope and vector space used
3. retrieved neighbors
4. legal/status and blocking context
5. overlap rationale
6. caveats about corpus coverage

## Rules

1. must disclose `claim-backed` vs `abstract-backed`,
2. must disclose sampled or partial corpus mode,
3. must not imply legal infringement conclusions from semantic similarity alone.

---

## 12. Report Type 7: Forecast Report

## Inputs

1. Phase 03 family forecast outputs
2. supporting family summary and history marts

## Section Order

1. forecast scope
2. `3y` and `5y` prediction summary
3. driver explanation
4. current vs projected state
5. interval and caveat interpretation
6. supporting tables

## Best Components

1. horizon switch summary
2. driver chips / ranked contribution table
3. current-vs-projected compare
4. uncertainty band explanation

## Rules

1. forecast must remain family-first,
2. portfolio forecast reports must remain bottom-up,
3. confidence / interval information is mandatory.

---

## 13. Report Type 8: Client-Enriched Executive Report

## Inputs

Public inputs:

1. family, portfolio, market, and forecast marts as applicable

Client inputs:

1. product-to-family mapping
2. annual revenue by product/product line
3. maintenance-cost scenario values
4. R&D spend by year and WIPO field

## Section Order

1. executive summary
2. public patent intelligence baseline
3. client-enriched overlay insights
4. revenue / pruning / efficiency modules
5. assumptions and provenance
6. caveats

## Best Components

1. scenario cards
2. revenue cliff chart
3. prune-zone table
4. field efficiency matrix
5. client input schema summary

## Rules

1. every enriched result must be labeled `Client-Enriched`,
2. assumptions must be visible,
3. unresolved mappings must be disclosed,
4. results must never look like public-data-native metrics.

---

## 14. Report Generation Flow

## 14.1 User Flow

Typical user flow:

1. user selects entity / scope,
2. user optionally enters compare mode or client-enriched mode,
3. user chooses report type,
4. user selects format:
   - HTML
   - PDF
   - structured export
5. system composes the report from current release artifacts,
6. user downloads or shares the result.

## 14.2 Backend Flow

Recommended backend steps:

1. resolve canonical entity or scope,
2. load current release manifest,
3. load the correct repositories for the requested report,
4. assemble a report view model,
5. attach provenance / caveats / version stamps,
6. render HTML,
7. optionally convert to PDF,
8. optionally emit a structured JSON export package.

## 14.3 Report View Model

Report generation should rely on a dedicated backend report layer, not raw page scraping.

Recommended V2 backend structure:

1. `backend/v2/application/services/reporting/`
2. `backend/v2/domain/schemas/reporting/`
3. `backend/v2/api/routes/reports.py`

---

## 15. Backend Contract

Recommended endpoint family:

1. `GET /api/v2/reports/families/{family_id}`
2. `GET /api/v2/reports/publications/{publication_id}`
3. `GET /api/v2/reports/portfolios/{portfolio_id}`
4. `POST /api/v2/reports/compare`
5. `POST /api/v2/reports/semantic`
6. `POST /api/v2/reports/forecast`
7. `POST /api/v2/reports/client-enriched`

Recommended response modes:

1. JSON report payload
2. HTML render payload
3. PDF generation job reference
4. export package manifest

## Required Metadata In Every Report Payload

1. `report_type`
2. `generated_at`
3. `release_version`
4. `gold_release`
5. `model_release` where applicable
6. `semantic_release` where applicable
7. `client_dataset_ids` where applicable
8. `caveats[]`
9. `methodology_refs[]`

---

## 16. UI Contract Implications

Report generation should be represented consistently across the UI.

## 16.1 Entry Points

Add report actions to:

1. family page header
2. publication page evidence footer
3. portfolio page header
4. compare workspace toolbar
5. market intelligence toolbar
6. semantic workspace toolbar
7. client-enriched dashboards

## 16.2 Report Composer Drawer

Add a shared component:

1. `ReportComposerDrawer`

Inputs:

1. report type
2. entity/scope
3. format
4. section toggle set
5. horizon selector if forecast-driven
6. compare year selectors when relevant
7. inclusion of methodology appendix

## 16.3 Report Preview

Before export, users should see a lightweight preview of:

1. title
2. included sections
3. caveats
4. release version
5. whether the report is client-enriched

## 16.4 Data Room Linkage

Every report should link back to supporting methodology and provenance in the Data Room:

1. model cards
2. release manifests
3. client dataset cards
4. semantic corpus coverage notes

---

## 17. Report Design Rules

## 17.1 Visual Rules

Reports should use:

1. clean typography,
2. restrained color,
3. strong section hierarchy,
4. tables and charts optimized for print readability.

Avoid:

1. overly interactive-only designs in printable outputs,
2. decorative motion-dependent storytelling,
3. charts without exact values where values matter.

## 17.2 Compare Visual Rules

For compare reports:

1. mirrored sections are preferred,
2. compare radar is allowed,
3. exact delta tables must sit next to the radar,
4. time-slice compare should be clearly labeled.

## 17.3 Client-Enriched Visual Rules

For enriched reports:

1. show a `Client-Enriched` badge in the header,
2. show an `Assumptions` panel near the start,
3. show an `Input Coverage` panel before conclusions,
4. never blur the line between public and client-supplied data.

---

## 18. Format-Specific Guidance

## 18.1 HTML Share Report

Use for:

1. live demos
2. internal review
3. shareable links

Needs:

1. responsive layout
2. printable stylesheet
3. version/caveat footer

## 18.2 PDF

Use for:

1. jury demo packs
2. management review
3. counsel / diligence packet

Needs:

1. page breaks
2. repeated footer with report metadata
3. appendix section

## 18.3 Structured Export

Use for:

1. enterprise data handoff
2. internal BI flows
3. client-local enrichment continuation

Should include:

1. `report.json`
2. optional tables as CSV
3. `provenance.json`
4. `release-manifest.json` reference

---

## 19. Current MVP Recommendation

For the next usable V2 report system, start with:

1. Family intelligence report
2. Portfolio intelligence report
3. Compare report
4. Client-enriched executive report

Why:

1. these are the strongest current data-backed use cases,
2. they align with the new UI contracts,
3. they are the most compelling for jury/demo presentation.

Secondary:

1. market report
2. semantic report
3. forecast report

These should follow as semantic and forecast serving become fully promoted.

---

## 20. Final Recommendation

Report generation should be treated as a native V2 capability.

PatentIQ V2 should generate:

1. family reports,
2. portfolio reports,
3. compare reports,
4. market reports,
5. semantic reports,
6. forecast reports,
7. client-enriched executive reports,

with:

1. explicit provenance,
2. methodology references,
3. release versioning,
4. caveat visibility,
5. optional PDF / HTML / structured export modes.

That makes the product significantly stronger for:

1. demo presentation,
2. executive decision support,
3. legal/strategy review,
4. client-facing analysis,
5. future enterprise packaging.

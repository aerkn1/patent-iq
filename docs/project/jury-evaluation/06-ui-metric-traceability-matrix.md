# Section 06. UI Metric Traceability Matrix

## Table Of Contents

1. [Purpose Of This Section](#purpose-of-this-section)
2. [What This Section Traces](#what-this-section-traces)
3. [Traceability Rules Used For The Matrix](#traceability-rules-used-for-the-matrix)
   - [1. The UI does not invent metrics](#1-the-ui-does-not-invent-metrics)
   - [2. Tooltips and methodology notes are part of the analytical contract](#2-tooltips-and-methodology-notes-are-part-of-the-analytical-contract)
   - [3. Score-first, evidence-first, and discovery-first pages are intentionally different](#3-score-first-evidence-first-and-discovery-first-pages-are-intentionally-different)
   - [4. Some payload fields are intentionally hidden or de-emphasized in the UI](#4-some-payload-fields-are-intentionally-hidden-or-de-emphasized-in-the-ui)
4. [Route-Level Traceability Overview](#route-level-traceability-overview)
5. [Family Workspace Metric Traceability](#family-workspace-metric-traceability)
   - [1. Overview rail and family profile](#1-overview-rail-and-family-profile)
   - [2. Legal, publication, and citation panels](#2-legal-publication-and-citation-panels)
6. [Publication Workspace Traceability](#publication-workspace-traceability)
7. [Portfolio Workspace Metric Traceability](#portfolio-workspace-metric-traceability)
   - [1. Executive summary rail and hidden count cards](#1-executive-summary-rail-and-hidden-count-cards)
   - [2. Coverage context and executive previews](#2-coverage-context-and-executive-previews)
   - [3. Citation, field, and forecast tabs](#3-citation-field-and-forecast-tabs)
8. [Market Workspace Metric Traceability](#market-workspace-metric-traceability)
   - [1. Market-wide chronology](#1-market-wide-chronology)
   - [2. Field league table and selected-field summary](#2-field-league-table-and-selected-field-summary)
   - [3. Jurisdiction, CPC, application, and grant drilldowns](#3-jurisdiction-cpc-application-and-grant-drilldowns)
9. [Compare Workspace Traceability](#compare-workspace-traceability)
   - [1. Family compare](#1-family-compare)
   - [2. Portfolio compare](#2-portfolio-compare)
   - [3. Family time-slice compare](#3-family-time-slice-compare)
10. [Semantic Workspace Traceability](#semantic-workspace-traceability)
11. [Tooltip And Methodology Disclosure Pattern](#tooltip-and-methodology-disclosure-pattern)
12. [Current Interpretation Rules](#current-interpretation-rules)
13. [Key Takeaways](#key-takeaways)

## Purpose Of This Section

Sections 01 through 05 explained the layered data foundation, backend/API contracts, frontend workspace architecture, forecasting stack, and semantic stack. This section answers a narrower but critical traceability question:

When a card, table, chart, or tooltip appears in the V2 user interface, which backend contract field produced it, which Gold or Silver artifact feeds it, and how should that output be interpreted safely?

This section is therefore the bridge between:

1. formula and mart lineage in Section 01,
2. API contract shape in Section 02,
3. actual frontend rendering behavior in Section 03,
4. ML and semantic overlays in Sections 04 and 05.

Primary implementation references:

1. `docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md:1-214`
2. `docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md:1-214`
3. `docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md:1-260`
4. `docs/next-phase-v2/ui-contracts/34-patentiq-v2-compare-and-semantic-workspace-contract.md:1-260`
5. `docs/next-phase-v2/11-patentiq-v2-metric-lineage-catalog.md:1-317`
6. `docs/next-phase-v2/12-patentiq-v2-database-structure-and-metric-maps.md:1-431`
7. `docs/next-phase-v2/67-patentiq-v2-derived-metric-formula-alignment-audit.md:1-274`

## What This Section Traces

Each traceability entry below answers five questions:

1. which route or workspace surface appears in the UI,
2. which frontend adapter and component consume the payload,
3. which backend endpoint and contract key provide the value,
4. which Gold, Silver, or serving artifact is the main source,
5. which tooltip, note, or caveat controls correct interpretation.

This section does not restate every formula in full. For the derivation math behind blocking power, OECD-style quality percentiles, citation lethality, coverage stability, or market-state rollups, use Section 01 together with the lineage catalog and alignment audit above. Here the goal is traceability from metric origin to visible UI.

## Traceability Rules Used For The Matrix

### 1. The UI does not invent metrics

The V2 UI is contract-driven. Frontend adapters map backend JSON payloads into typed props, but they do not recalculate core business metrics.

Examples:

1. family summary cards are passed through from `summary_cards` into `FamilySummaryCard[]` by `frontend_v2/lib/api/family-v2.ts:140-168`,
2. portfolio summary cards, citation summaries, forecast contributors, and pending-grant rows are typed and mapped in `frontend_v2/lib/api/portfolio-v2.ts:271-870`,
3. compare rows preserve `display_kind`, notes, winners, and deltas in `frontend_v2/lib/api/compare-v2.ts:151-215`,
4. semantic result rows preserve similarity, blocking, OECD, provenance, and fallback flags in `frontend_v2/lib/api/semantic-v2.ts:176-207`,
5. publication overview and section payloads are mapped as factual document evidence in `frontend_v2/lib/api/publication-v2.ts:86-167`.

### 2. Tooltips and methodology notes are part of the analytical contract

In PatentIQ, tooltips are not decorative. They often carry the only short-form statement of metric scope, denominator, or intended interpretation.

Examples:

1. family blocking and heritage cards attach tooltip text from the backend service in `backend_v2/application/services/families.py:269-299` and render them in `frontend_v2/components/family/family-workspace.tsx:251-281`,
2. market metric tooltips are explicitly centralized in `frontend_v2/components/market/market-workspace.tsx:188-235`,
3. portfolio coverage bars explain denominator and model coverage in `frontend_v2/components/portfolio/portfolio-coverage-panel.tsx:58-153`,
4. compare methodology notes are rendered directly from `meta.caveats` in `frontend_v2/components/compare/compare-rendering.tsx:937-958`,
5. semantic caveats are shown as a dedicated methodology disclosure in `frontend_v2/components/semantic/semantic-workspace.tsx:613-633`.

### 3. Score-first, evidence-first, and discovery-first pages are intentionally different

Not every page uses the same metric style:

1. `family`, `portfolio`, `market`, and `compare` are analytical workspaces with scored metrics, bands, and cohort context,
2. `publication` is intentionally evidence-first and avoids synthetic strength scoring,
3. `semantic` is discovery-first and candidate-only, with coverage and provenance caveats emphasized over hard ranking claims.

This difference is enforced in code:

1. publication overview caveats explicitly state `publication_evidence_first` in `backend_v2/application/services/publications.py:165-185`,
2. semantic search explicitly states exact-ranking, payload-scope, and non-legal-proof caveats in `backend_v2/application/services/semantic.py:127-196` and `225-328`.

### 4. Some payload fields are intentionally hidden or de-emphasized in the UI

This section distinguishes between:

1. fields returned by a backend contract,
2. fields actively shown in the default UI surface.

Important examples:

1. portfolio overview returns count cards such as `In-Scope Families`, `Primary-Owner Families`, and `Semantic Candidate Families`, but the summary rail hides them in `frontend_v2/components/portfolio/portfolio-summary-cards.tsx:59-77`,
2. semantic search returns multiple summary cards, but the current page shows only the `searchable_families` scope card via `visibleScopeCards` in `frontend_v2/components/semantic/semantic-workspace.tsx:262-265`,
3. market endpoints return section metadata like `metric_basis`, `scope_basis`, `sum_safe`, and `overlap_policy`; these are part of the API contract even when a particular panel emphasizes the rendered rows instead of every metadata field.

## Route-Level Traceability Overview

| Route or workspace | Frontend adapter and page wiring | Main backend contracts | Main marts or serving artifacts | Primary interpretation mode |
| --- | --- | --- | --- | --- |
| Family | `frontend_v2/lib/api/family-v2.ts:140-194`, `frontend_v2/components/family/family-workspace.tsx:251-425` | `/api/v1/families/{id}/overview`, `/api/v1/families/{id}/{section}` | `gold_family_summary`, `gold_family_blocking_power`, `gold_family_heritage_summary`, `gold_family_compare_pit`, `silver_family_oecd_quality`, `silver_family_citation_metrics` | family-first scored analytics with methodology notes |
| Publication | `frontend_v2/lib/api/publication-v2.ts:86-167`, `frontend_v2/components/publication/publication-workspace.tsx:125-291` | `/api/v1/publications/{id}/overview`, `/api/v1/publications/{id}/{section}` | `publication_evidence_serving`, `silver_family_member_publications`, application/title/abstract bounded slices, EPAB claim fallback | evidence-first document facts |
| Portfolio | `frontend_v2/lib/api/portfolio-v2.ts:271-870` plus portfolio panels | `/api/v1/portfolios/*` overview, families, fields, citations, forecast, pending-grants | `gold_portfolio_summary`, `gold_portfolio_forecast_summary`, `gold_portfolio_threat_matrix`, `gold_family_summary`, `gold_family_blocking_power`, `silver_family_owner_bridge` | owner-level rollup with forecast and coverage overlays |
| Market | `frontend_v2/lib/api/market-v2.ts:21-225`, `frontend_v2/components/market/market-workspace.tsx:1214-2075` | `/api/v1/market-intelligence/workspace` plus overview-history, leading-jurisdictions, segment detail routes | `gold_market_intelligence_overview`, `gold_market_summary_pit`, `gold_market_intelligence_segments`, `gold_market_intelligence_timeseries`, market CPC and citation Gold marts | bounded landscape analytics with market-state and drilldown layers |
| Compare | `frontend_v2/lib/api/compare-v2.ts:121-260`, `frontend_v2/components/compare/compare-rendering.tsx:381-958` | `/api/v1/compare/families`, `/api/v1/compare/portfolios`, `/api/v1/compare/families/{id}/timeslice` | compare-safe family and portfolio serving marts, forecast summaries, supporting field and legal rows | side-by-side decision support, not one blended score |
| Semantic | `frontend_v2/lib/api/semantic-v2.ts:124-260`, `frontend_v2/components/semantic/semantic-workspace.tsx:155-638` | `/api/v1/semantic/search/families`, `/api/v1/semantic/suggestions/families`, `/api/v1/semantic/compare/families` | vector payloads, `gold_semantic_match_context`, semantic serving, family overlays | discovery-first candidate workflow with provenance and payload coverage caveats |

## Family Workspace Metric Traceability

### 1. Overview rail and family profile

The family page is the clearest example of a score-first, family-first V2 contract. The backend builds the overview payload in `backend_v2/application/services/families.py:244-441`, the adapter maps it in `frontend_v2/lib/api/family-v2.ts:140-168`, and the page renders it in `frontend_v2/components/family/family-workspace.tsx:251-425`.

| UI surface | Frontend binding | Backend contract key or label | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- | --- |
| Summary rail card | `summaryCards -> SummaryRail` in `family-workspace.tsx:251-281` | `blocking_power` / `Blocking Power` from `family_ui_blocking_power_score` in `families.py:269-276` | `gold_family_blocking_power`, current compare-serving overlay from `family_compare_current_serving`, joined in `family_repository.py:243-342` | current blocking posture, not a legal validity opinion; tooltip explicitly says it comes from the rebuilt blocking mart |
| Summary rail card | same | `family_size` / `Family Size` in `families.py:277-282` | `gold_family_summary` | DOCDB family-member count; pure count metric |
| Summary rail card | same | `active_reach` / `Active Reach` in `families.py:283-288` | current family summary and compare-serving context | active jurisdictions or active grant branches visible in current summary context |
| Summary rail card | same | `heritage` / `Heritage` in `families.py:289-298` | `gold_family_heritage_summary` plus cohort banding | peer percentile of heritage score inside priority-year and primary-field cohort; tooltip includes raw heritage score |
| Family profile panel | `overviewMetrics` read by label in `family-workspace.tsx:367-425` | `Primary owner`, `Status`, `Earliest priority date` | family overview context in `family_repository.py:243-342` | descriptive identity facts |
| Family profile panel | same | `Quality index 6`, `OECD quality index`, `Generality percentile`, `Originality percentile`, `Radicalness percentile`, `Science grounding percentile` in `families.py:352-397` | `silver_family_oecd_quality`, joined via `family_repository.py:280-287` and `325-332` | OECD-style indicators are cohort-relative and should be read as normalized comparative quality signals, not raw citation counts |
| Family profile panel | same | `Legal durability percentile`, `Raw legal enforceability proxy`, `Current active jurisdiction share` in `families.py:398-412` | blocking and compare-serving context | percentile, raw score, and share are different scales and should not be collapsed into one number |
| Family profile panel | same | `Raw family citation count`, `Weighted forward citations` in `families.py:413-422` | `gold_family_heritage_summary`, `silver_family_citation_metrics` | raw count and weighted citation score are intentionally both shown because one is descriptive volume and the other is quality-adjusted trajectory context |

For formula lineage behind these overview metrics, use:

1. Section 01 of this dossier,
2. `docs/next-phase-v2/11-patentiq-v2-metric-lineage-catalog.md:1-317`,
3. `docs/next-phase-v2/67-patentiq-v2-derived-metric-formula-alignment-audit.md:1-274`.

### 2. Legal, publication, and citation panels

Below the overview rail, the family page breaks into legal, publication, and citation evidence panels. These are still family-first, but each panel has its own scope rules.

| UI panel | Visible widget or columns | Backend section and fields | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- | --- |
| `Branch-state mix` | tracked jurisdictions, lead branch state, state-band count and chart in `family-workspace.tsx:498-535` | `/api/v1/families/{id}/legal` section summary and status-history rows from `families.py:483-518` | family legal rows and status history from repository legal-footprint accessors | branch-state mix is descriptive family-footprint composition, not office ranking |
| `Jurisdiction legal footprint` | chart and table with `Jurisdiction`, `Branch state`, `Family legal share`, `Legal contribution`, `Strength band`, `Last event` in `family-workspace.tsx:538-668` | legal rows from `get_family_jurisdiction_legal_rows()` plus contribution caveat in `families.py:483-518` | family legal contribution rows from the family repository legal layer | backend caveat states this view is contribution-based within the family only, not a universal 0-100 office truth |
| `Legal history` | chart or table over active jurisdictions, active grant branches, lapsed jurisdictions, opposed branches in `family-workspace.tsx:930-980` | legal status-history series from `families.py:501-510` | compare-safe historical family status layer | this is PIT history for the same family, separate from current overview cards |
| `Publication mix` | application and grant rows by office in `family-workspace.tsx:803-864` | publication section rows | `silver_family_member_publications` | visible page slice of family-member publication evidence |
| `Top cited publications` | family-member publication ranking in `family-workspace.tsx:867-928` | citation/publication section rows | citation and member-publication layers | publication-level citation ranking is subordinate to the family-level summary, not a separate product grain |
| `Top citing owners` | toggle between `Pressure` and `Citations` in `family-workspace.tsx:671-800` | citation-owner rows with `citation_lethality_sum`, `citing_family_count`, `cited_member_count` | citation network and lethality overlays | tooltip explicitly defines pressure as threat-weighted clean citations; this is not the same as raw citation count |
| `Methodology` | caveat disclosure in `family-workspace.tsx:284-310` | `meta.caveats` from overview or section responses | backend service caveats | family view interpretation depends on these notes, especially contribution-based legal rows and forecast-coverage limits |

## Publication Workspace Traceability

The publication page is the strictest evidence-first page in the V2 stack. The backend states this explicitly in `backend_v2/application/services/publications.py:165-185`, the adapter preserves factual cards and facts in `frontend_v2/lib/api/publication-v2.ts:107-167`, and the UI renders support, text, timeline, and register panels in `frontend_v2/components/publication/publication-workspace.tsx:125-291`.

| UI surface | Backend contract | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| Summary cards `Office`, `Kind code`, `Stage`, `Publication date`, `Filing date`, `Register evidence`, `Text evidence` | `summary_cards` in `publications.py:62-98` | `publication_evidence_serving`, `silver_family_member_publications`, application/title/abstract evidence, EP Register overlay | factual document metadata only |
| `Source and support` disclosure | text availability plus `meta.caveats` rendered in `publication-workspace.tsx:125-163` | `text_availability`, `register_evidence`, and caveats from `publications.py:114-185` | support context is part of the contract and explains why a text or register row exists or is missing |
| `Abstract and claims` | `/text` section rendered in `publication-workspace.tsx:167-212` | title, abstract, and claim rows from `publications.py:202-240` | PATSTAT title and abstract are bounded evidence; Claim 1 is EP-only EPAB-backed when available |
| `Legal and register timeline` | `/legal-timeline` section rendered in `publication-workspace.tsx:215-259` | chronology rows from publication service | publication-level legal and procedure milestones | timeline is evidence, not a score |
| `Register evidence` | `/register-evidence` section rendered in `publication-workspace.tsx:262-291` | EP Register evidence only | EP-scoped evidence should not be generalized to non-EP authorities |

The underlying repository boundary is explicit:

1. `publication_evidence_serving` is preferred when present in `publication_repository.py:127-140`,
2. publication member lookup comes from that serving table or the family-member publication parquet in `publication_repository.py:172-237`,
3. title, filing date, abstract, and claim retrieval are resolved through serving-first with raw fallback in `publication_repository.py:239-430`.

## Portfolio Workspace Metric Traceability

### 1. Executive summary rail and hidden count cards

The portfolio page aggregates family-level analytics to current-owner scope. The overview payload is built in `backend_v2/application/services/portfolios.py:399-550`, mapped in `frontend_v2/lib/api/portfolio-v2.ts:271-555`, and rendered by summary cards and executive panels in the portfolio workspace.

| UI surface | Backend contract key | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| Returned but hidden overview cards | `portfolio_family_count_within_mega_cluster`, `portfolio_primary_owner_family_count`, `semantic_candidate_family_count` in `portfolios.py:399-417` | `gold_portfolio_summary`, `silver_family_owner_bridge` | these are valid contract fields but intentionally removed from the default summary rail in `portfolio-summary-cards.tsx:59-77` |
| Visible summary card | `portfolio_total_mass_score` / `Granted Blocking Mass` in `portfolios.py:418-432` | `gold_portfolio_summary` with peer-bucket metadata | peer-relative percentile card built from raw mass plus peer band |
| Visible summary card | `portfolio_current_threat_score` / `Granted Threat Mass` in `portfolios.py:433-447` | `gold_portfolio_summary`, threat overlays | current market-facing threat mass, not a forward forecast |
| Visible summary card | `portfolio_heritage_score` / `Citation Heritage Mass` in `portfolios.py:448-462` | `gold_portfolio_summary`, heritage rollups | portfolio-level heritage rollup, again peer-relative in display banding |
| Summary-card renderer | tooltip, caveat, band label, percentile, bucket label in `portfolio-summary-cards.tsx:22-55` | adapter mapping in `portfolio-v2.ts:271-300` | the card caption and percentile metadata must be read together with the raw value |

The backend caveats attached to this overview are not optional. They explicitly warn about:

1. current-owner replay,
2. mixed metric scales,
3. count-scope differences,
4. peer-relative bands,
5. executive metric withholding.

Those caveats are produced in `backend_v2/application/services/portfolios.py:479-515`.

### 2. Coverage context and executive previews

The portfolio page exposes not only current summary metrics, but also whether model-driven overlays actually cover the visible portfolio.

| UI surface | Backend contract | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| `Coverage context` denominator, support level, and coverage bars in `portfolio-coverage-panel.tsx:80-155` | `meta.coverage` mapped into `coverage` in `portfolio-v2.ts:534-553` | forecast summary marts and model-coverage metadata | this panel should be read before over-trusting any citation, lapse, or market-direction overlay |
| Coverage bars | `Citation forecast family coverage`, `Lapse-risk family coverage`, `Market-direction family coverage` in `portfolio-coverage-panel.tsx:83-109` | ML coverage rollups | each bar is a coverage share, not a score or success metric |
| Methodology disclosure | `contributionMethod` and `coverageCaveatText` in `portfolio-coverage-panel.tsx:81-153` | backend coverage metadata | denominator logic is explicit and should be cited in methodology explanations |
| `Blocking leader families`, `Top field concentration`, `Top citing owners` in `portfolio-overview-brief.tsx:32-153` | family preview, field rows, threat rows from overview-adjacent endpoints | `gold_family_summary`, `gold_family_blocking_power`, portfolio field rows, threat matrix | these are previews that direct the analyst to drilldowns; they do not replace the full tables |

### 3. Citation, field, and forecast tabs

| UI panel | Backend contract and mapping | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| `Citation summary` cards in `portfolio-citation-summary-panel.tsx:24-93` | `get_citation_summary()` keys mapped in `portfolio-v2.ts:600-627` from `portfolios.py:691-742` | citation summary rollups over portfolio family scope | mixes forward, backward, NPL, and diversity metrics; each has different semantics |
| `Citation chronology` in `portfolio-citation-timeseries-panel.tsx:76-260` | historical rows from `portfolio-v2.ts:629-643` plus forecast intervals from `mapForecastFromSections()` in `portfolio-v2.ts:413-483` | historical citation marts plus Phase 03 portfolio forecast summary | observed history and forecast interval are shown together but remain separate layers |
| `Families` tab tables | `get_families()` rows in `portfolios.py:572-628`, mapped in `portfolio-v2.ts:318-333` | `gold_family_summary`, `gold_family_blocking_power`, owner bridge | family rollup view for current portfolio membership |
| `Fields` tab | field rows and timeseries from `portfolios.py:630-689`, mapped in `portfolio-v2.ts:335-357` and `595-598` | field and field-timeseries rollups | field share and hotspot direction are owner-scoped rollups, not market-global values |
| `Pending-grant pipeline` in `portfolio-pending-grants-panel.tsx:84-319` | pending-grant response rows mapped in `portfolio-v2.ts:791-870` | candidate-only grant model outputs plus family overlays | directional planning aid only; footer explicitly says rank, percentile, and tier matter more than exact grant counts |
| Pending-grant branch table | `Rank`, `Family`, `Jurisdiction`, `Field`, `Priority`, `Grant probability`, `Percentile`, `Blocking` | branch rows from pending-grant contract | model output plus current family context | combines model probability with family blocking context; it is not a merged score |

Portfolio citation caveats are especially important. The service warns that portfolio citation summaries are replayed through current owner-family membership and that backward/NPL views are current-summary-first in `backend_v2/application/services/portfolios.py:726-742`. The filing chronology likewise warns about priority-year anchoring and current-owner replay in `backend_v2/application/services/portfolios.py:871-897`.

## Market Workspace Metric Traceability

The market page is a bounded landscape workspace, not a whole-world patent dashboard. The backend constructs the current workspace in `backend_v2/application/services/market_intelligence.py:131-306`, adapters fetch the workspace and drilldown sections in `frontend_v2/lib/api/market-v2.ts:21-225`, and the UI renders market-wide and selected-field layers in `frontend_v2/components/market/market-workspace.tsx:1214-2075`.

The repository artifact boundary is explicit in `backend_v2/infrastructure/repositories/market_intelligence_repository.py:13-67`, which lists the main Gold and Silver marts consumed by the workspace.

### 1. Market-wide chronology

| UI surface | Backend fields | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| `Market-wide chronology` banner and count cards in `market-workspace.tsx:1214-1385` | `market_family_count_asof`, `owner_count_asof`, `pending_family_count_asof`, `fully_active_family_count_asof`, `partially_lapsed_family_count_asof`, `dead_family_count_asof`, `avg_blocking_power_score_asof`, `avg_enforceability_score_asof`, `avg_forward_citations_clean_asof`, `top_owner_share_asof` | derived market overview history from `gold_family_compare_pit` plus served segment set in `market_intelligence_repository.py:168-260` | market-wide rollups are bounded to the approved field universe, not global totals |
| Tooltips for these cards | `MARKET_METRIC_TOOLTIPS` in `market-workspace.tsx:188-235` | frontend label layer | each tooltip defines the denominator and latest-year meaning |
| Historical chronology mode switch | stacked mix or count charts in `market-workspace.tsx:1322-1379` | same overview-history response | mix view shows shares; count view shows absolute family counts; they should not be conflated |

The backend also states the uniqueness rule directly: market-wide yearly rollups use the bounded 10-field primary WIPO assignment so the workspace can serve a unique family universe without overlapping segment totals in `backend_v2/application/services/market_intelligence.py:308-325`.

### 2. Field league table and selected-field summary

| UI surface | Visible columns or labels | Backend workspace fields | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- | --- |
| `Field league table` in `market-workspace.tsx:1676-1694` | `Field`, `State`, `Families`, `Momentum`, `Blocking`, `Crowding`, `Spark` from `segmentColumns` in `market-workspace.tsx:1386-1442` | `workspace.segments` from `get_workspace()` in `market_intelligence.py:131-306` | `gold_market_intelligence_segments`, `gold_market_intelligence_timeseries` | this is the primary selection surface for choosing a field, not a claim that every metric shares one scale |
| `Selected field summary` in `market-workspace.tsx:1926-2055` | `Field scale`, `Active share`, `Competitive pressure`, `Top owner share`, `Defensive posture`, `Active jurisdiction share`, `Field balance`, `Momentum`, `Latest year`, `Current families`, `Market median`, `Vs market median` | selected-segment summary inside workspace payload | segment current-state Gold marts plus field timeseries | combines current-state and chronology context, but explicitly keeps them separate through labels and tooltips |
| `Field rationale` narrative card in `market-workspace.tsx:2058-2070` | state rationale headline, detail, evidence | selected segment rationale from backend workspace | market-state contract | qualitative narrative is still backed by structured evidence rows |

### 3. Jurisdiction, CPC, application, and grant drilldowns

| UI drilldown | Backend contract | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| `Leading jurisdictions by field` table and pie in `market-workspace.tsx:1696-1857` | `/leading-jurisdictions` section from `market_intelligence.py:327-350` | jurisdiction leaderboard marts in the market repository | backend marks `sum_safe=False` and warns about office-coded geography; jurisdiction rows across fields should not be naively summed |
| `Jurisdictions` table for selected field | columns `Jurisdiction`, `Citations`, `Owners`, `Pressure`, `Year` in `market-workspace.tsx:1443-1469` | selected segment `top_jurisdictions` | `gold_market_citation_pressure_by_jurisdiction_pit` | citing-side geography is separate from protection-footprint geography |
| CPC table | `CPC main group`, `Share`, `Growth`, `Blocking`, `Heat` in `market-workspace.tsx:1470-1503` | selected segment `top_cpcs` and CPC routes | `gold_market_cpc_trend_pit`, `gold_market_cpc_jurisdiction_trend_pit` | directional composition, not literal whole-world CPC dominance |
| Field-footprint-by-jurisdiction table | `Jurisdiction`, `Families`, `Active`, `Field share`, `CPC groups` in `market-workspace.tsx:1504-1530` | selected segment `field_jurisdictions` | `gold_family_classification_jurisdiction_pit` | protection-footprint lens, not citation lens |
| Applications and grants drilldowns | fetched by `fetchMarketSegmentApplicationsGrants()` and `fetchMarketSegmentGrantMix()` in `market-v2.ts:168-225` | market segment routes | `silver_family_member_publications`, `silver_ep_register_up_status`, `silver_up_status`, grant mix Gold marts | descriptive market activity and grant-state overlays, not forecast promises |

## Compare Workspace Traceability

The compare workspace intentionally avoids a single blended winner score. The adapter preserves winner, winner basis, notes, and display kind in `frontend_v2/lib/api/compare-v2.ts:151-215`, while `frontend_v2/components/compare/compare-rendering.tsx:381-958` renders summary cards, contrast rows, field overlap, forecast rows, support rows, and methodology notes as separate panels.

### 1. Family compare

| Compare surface | Backend contract | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| Summary cards `Family size`, `Blocking posture`, `Legal durability score`, `Citation heritage`, `3y citation outlook` in `compare.py:811-870` | family compare summary cards | compare-safe family serving, blocking, heritage, and forecast overlays | each card is a separate lens with its own winner basis |
| Contrast rows `Current status`, `Active jurisdictions`, `OECD quality proxy`, `Data completeness` in `compare.py:872-914` | family compare contrast rows | compare-safe family context | supporting evidence, not the primary headline score |
| Field overlap and support rows | `CompareFieldOverlapRows`, `CompareSupportRows`, `CompareMethodology` in `compare-rendering.tsx:501-958` | field rows and top jurisdiction previews | overlap depth and legal support rows are explanatory evidence for the card-level comparison |

### 2. Portfolio compare

| Compare surface | Backend contract | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| Compare lenses `mass`, `density`, `crown_jewel` in `compare.py:1005-1162` | portfolio compare row set | `gold_portfolio_summary` plus peer-bucket context | portfolio compare is deliberately multi-lens; no single blended score exists |
| Summary cards `Families in scope`, `Blocking footprint`, `Elite family density`, `Heritage depth`, `3y future citations` in `compare.py:1249-1311` | summary cards | summary and forecast marts | some cards are peer-relative, others are raw or forecast-midpoint values |
| Contrast rows `Crown-jewel strength`, `Current threat score`, `Active families`, `Pending families`, `Abandoned / lapsed families` in `compare.py:1313-1369` | contrast rows | portfolio summary, status counts, forecast overlays | side-by-side operational context after the main lenses |
| Support rows linking back to families | top-family preview and forecast contributors in `compare.py:1374-1415` | owner family drilldowns, forecast contributors | compare is traceable back to concrete family contributors |

### 3. Family time-slice compare

| Compare surface | Backend contract | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| Summary cards `Family size`, `Blocking power`, `Legal durability`, `Distinct citing families`, `Field breadth` in `compare.py:1581-1632` | time-slice summary cards | `gold_family_compare_pit` and related family detail layers | compares the same family across two years, not two different families |
| Contrast rows `Observed status`, `Active jurisdictions`, `Active grant branches`, `Lapsed jurisdictions`, `Coverage stability`, `Attacker density`, `Data completeness` in `compare.py:1634-1703` | time-slice contrast rows | historical family PIT rows | each metric is as-of-year specific and should be read with year badges |
| Forecast rows `Weighted citation trajectory`, `RCF trajectory` in `compare.py:1709-1739` | historical trajectory rows | historical citation and RCF fields | explicitly historical, not forward forecast intervals |
| Time-slice profile | normalized 0-100 profile rendering in `compare-rendering.tsx:825-867` | normalized compare dimensions | profile is a comparative visualization layer over raw rows, not a new underlying metric source |

## Semantic Workspace Traceability

Semantic search is a search-first, candidate-only workspace. The backend search contract is built in `backend_v2/application/services/semantic.py:14-197`, mapped in `frontend_v2/lib/api/semantic-v2.ts:163-251`, and rendered in `frontend_v2/components/semantic/semantic-workspace.tsx:155-638`.

| UI surface | Backend contract | Main source artifacts | Interpretation rule |
| --- | --- | --- | --- |
| Search controls and URL state | family id, vector space, same-field, exclude-same-owner in `semantic-workspace.tsx:160-325` | `/api/v1/semantic/search/families` | vector payloads plus semantic match context | user is choosing a retrieval scope, not altering the underlying metric formulas |
| Search scope cards | `Searchable families`, `Context coverage`, claim-backed or abstract-fallback count, retrieval mode in `semantic.py:69-102` | summary cards | vector payload manifests and semantic space summary | current page intentionally shows only searchable-family scope card by default in `semantic-workspace.tsx:262-265` |
| Query context and anchor text | `Anchor family`, `Vector space`, `Primary field`, `Owner`, anchor text excerpt in `semantic.py:104-175` and `semantic-workspace.tsx:417-460` | anchor row from vector payload | provenance matters because abstract and claim spaces are not blended |
| Ranked semantic neighbors | result rows preserve `semantic_similarity`, `family_ui_blocking_power_score`, `oecd_quality_percentile`, `text_provenance`, fallback flags in `semantic-v2.ts:193-207`, rendered in `semantic-workspace.tsx:554-609` | vector payload row plus family overlays | semantic similarity is shown alongside blocking and OECD context, but they remain separate metrics |
| Methodology disclosure | semantic caveats rendered in `semantic-workspace.tsx:613-633` | `meta.caveats` from `semantic.py:127-196` | payload coverage, exact ranking, free-text gap, and abstract fallback rules all limit what can be claimed from the result |

Semantic family compare is also present in the backend contract, even though the active UI is still search-first:

1. summary cards `Abstract similarity`, `Claim similarity`, `Primary field relation`, `Owner relation` are built in `backend_v2/application/services/semantic.py:238-267`,
2. compare rows keep abstract and claim overlap separate in `backend_v2/application/services/semantic.py:269-286`,
3. the service caveats explicitly state that semantic similarity is a discovery signal, not legal proof, in `backend_v2/application/services/semantic.py:298-314`.

## Tooltip And Methodology Disclosure Pattern

Across the active V2 UI, there is a consistent disclosure pattern:

1. backend services attach `meta.caveats`, support levels, coverage, and often tooltip strings,
2. adapters preserve those values with minimal transformation,
3. components render them as tooltip pills, support panels, methodology disclosures, or caveat accordions.

This pattern appears in:

1. family `CaveatPanel` in `frontend_v2/components/family/family-workspace.tsx:284-310`,
2. publication `Source and support` panel in `frontend_v2/components/publication/publication-workspace.tsx:125-163`,
3. portfolio coverage methodology disclosure in `frontend_v2/components/portfolio/portfolio-coverage-panel.tsx:142-153`,
4. compare methodology panel in `frontend_v2/components/compare/compare-rendering.tsx:937-958`,
5. semantic scope and caveats disclosure in `frontend_v2/components/semantic/semantic-workspace.tsx:613-633`.

The explanation of a metric is distributed across:

1. the visible label,
2. the numeric field,
3. the tooltip,
4. the backend caveat block,
5. the underlying mart lineage.

Ignoring any of those layers can lead to misreading the product.

## Current Interpretation Rules

Use the following rules when reading the V2 UI against the codebase:

1. Do not assume two metrics on the same page share one scale. Counts, shares, raw mass scores, percentiles, and model midpoints appear together but are not interchangeable.
2. Treat tooltips and caveats as part of the contract. They often define denominator, cohort, or scope limits.
3. Distinguish current-state PIT metrics from historical PIT metrics and from forecast overlays. The UI intentionally separates these, especially on family, portfolio, market, and compare pages.
4. Read portfolio history with the owner-replay caveat in mind. Current owner-family scope is still used where full owner-by-year truth is unavailable.
5. Read publication pages as factual evidence pages. They intentionally do not score individual publications.
6. Read semantic similarity as a retrieval signal, not legal proof or infringement proof.
7. Read market drilldowns as bounded-mega-cluster analytics. Jurisdiction and field rows are not whole-world patent totals.
8. Read pending-grant output as directional candidate logic. The UI itself says rank, percentile, and tier should dominate interpretation.

## Key Takeaways

The V2 UI is not a disconnected presentation layer. It is a contract-driven rendering of the same Gold, Silver, serving, and model artifacts documented in earlier sections.

The most important traceability truths are:

1. family, portfolio, market, compare, and semantic pages all map back to explicit page-shaped backend contracts,
2. those backend contracts are sourced from named Gold and Silver marts, not ad hoc request-time raw joins,
3. tooltips, support notes, and caveats are deliberately used to prevent analytical overclaim,
4. the publication page remains evidence-first, while semantic and pending-grant views remain explicitly caveated candidate workflows,
5. any visible metric in the UI can be traced back to a contract key, repository file, mart, and lineage document without reverse-engineering the whole codebase manually.

# Section 08. Worked Example Walkthroughs

## Table Of Contents

1. [Purpose Of This Section](#purpose-of-this-section)
2. [Example Record Set Used In This Appendix](#example-record-set-used-in-this-appendix)
3. [How To Use This Walkthrough](#how-to-use-this-walkthrough)
4. [Portfolio Walkthrough: TOYOTA MOTOR CORPORATION](#portfolio-walkthrough-toyota-motor-corporation)
   - [1. Entry route and tab model](#1-entry-route-and-tab-model)
   - [2. Overview tab](#2-overview-tab)
   - [3. Families tab](#3-families-tab)
   - [4. Fields tab](#4-fields-tab)
   - [5. Citation tab](#5-citation-tab)
   - [6. Forecast tab](#6-forecast-tab)
5. [Family Walkthrough: DOCDB Family 51225930](#family-walkthrough-docdb-family-51225930)
   - [1. Entry route and tab model](#1-entry-route-and-tab-model-1)
   - [2. Publications tab](#2-publications-tab)
   - [3. Legal tab](#3-legal-tab)
   - [4. Fields tab](#4-fields-tab-1)
   - [5. Citation tab](#5-citation-tab-1)
6. [Publication Walkthrough: EP2259376B1](#publication-walkthrough-ep2259376b1)
   - [1. Entry route and page model](#1-entry-route-and-page-model)
   - [2. Summary cards](#2-summary-cards)
   - [3. Abstract and claims](#3-abstract-and-claims)
   - [4. Family members](#4-family-members)
   - [5. Legal timeline and register evidence](#5-legal-timeline-and-register-evidence)
   - [6. Support details and caveats](#6-support-details-and-caveats)
7. [Market Walkthrough Anchored To The Same Family](#market-walkthrough-anchored-to-the-same-family)
   - [1. Entry route and selected segment](#1-entry-route-and-selected-segment)
   - [2. Overview section](#2-overview-section)
   - [3. Analysis section: Competition tab](#3-analysis-section-competition-tab)
   - [4. Analysis section: Jurisdictions & Grants tab](#4-analysis-section-jurisdictions--grants-tab)
   - [5. Analysis section: Technology tab](#5-analysis-section-technology-tab)
8. [Cross-Route Continuity Shown By The Example](#cross-route-continuity-shown-by-the-example)
9. [Interpretation Caveats For This Example](#interpretation-caveats-for-this-example)
10. [Key Takeaways](#key-takeaways)

## Purpose Of This Section

The earlier sections explain the architecture, lineage, formulas, backend contracts, and UI traceability. This appendix adds one concrete reading path through the application so the same logic can be seen in action from:

1. portfolio,
2. family,
3. publication,
4. market.

The goal is not to prove one company or one family is uniquely special. The goal is to show how one real example moves through the implemented routes, tabs, contracts, and drilldowns without changing analytical rules between screens.

Primary implementation references:

1. `frontend_v2/components/portfolio/portfolio-primary-tabs.tsx:19-49`
2. `frontend_v2/components/portfolio/portfolio-workspace.tsx:87-140`
3. `frontend_v2/components/family/family-workspace.tsx:36-60`
4. `frontend_v2/components/family/family-workspace.tsx:2105-2115`
5. `frontend_v2/components/publication/publication-workspace.tsx:167-292`
6. `frontend_v2/components/publication/publication-workspace.tsx:462-547`
7. `frontend_v2/components/market/market-workspace.tsx:305-339`
8. `frontend_v2/components/market/market-workspace.tsx:1499-2025`
9. `frontend_v2/lib/api/market-v2.ts:22-40`

## Example Record Set Used In This Appendix

This appendix uses the current snapshot rows observed directly in:

1. `etl/data/gold/gold_portfolio_summary.parquet`
2. `etl/data/gold/gold_family_summary.parquet`
3. `etl/data/silver/silver_family_member_publications.parquet`
4. `etl/data/serving/market_serving.duckdb`

The concrete anchors are:

1. portfolio: `TOYOTA MOTOR CORPORATION`
   `owner_name_harmonized = TOYOTA_MOTOR_CORPORATION`
   `portfolio_family_count_within_mega_cluster = 52,264`
   `portfolio_active_grant_family_count = 22,167`
   `semantic_candidate_family_count = 52,069`
   `portfolio_total_mass_score = 1947.202189`
   `portfolio_current_threat_score = 1029.091899`
2. family: `51225930`
   `owner_name_display = TOYOTA MOTOR CORPORATION`
   `family_composite_status = fully_active`
   `primary_wipo_field = Electrical machinery, apparatus, energy`
   `covered_wipo_fields = [Electrical machinery, apparatus, energy, Measurement]`
   `active_jurisdiction_count = 5`
   `active_grant_branch_count = 5`
   `family_market_coverage_weight_raw = 1.4`
   `family_coverage_stability_score = 0.714286`
   `is_semantic_candidate = true`
3. publication: `EP2259376B1`
   `pat_publn_id = 468630914`
   `appln_id = 267542107`
   `publn_auth = EP`
   `publn_kind = B1`
   `publn_date = 2016-10-05`
   `is_grant_stage = true`
4. family publication set:
   `publication_count = 16`
   offices present: `CA, CN, EP, JP, KR, US, WO`
5. market segment anchored to the family primary field:
   `segment_id = Electrical machinery, apparatus, energy`
   `market_state = rising`
   `total_family_count = 5,061,217`
   `latest_year = 2025`
   `latest_comparable_year = 2023`
   `latest_year_incomplete = true`
   `snapshot_date = 2026-03-15`

These numbers are snapshot-specific and will move when the release artifacts are rebuilt. The walkthrough logic should remain stable even when the counts refresh.

## How To Use This Walkthrough

The recommended reading sequence is:

1. open the Toyota portfolio and read it as the broad owner context,
2. drill from portfolio scale to family `51225930`,
3. drill from family scope to publication `EP2259376B1`,
4. pivot from the family primary field into the market workspace.

That sequence mirrors the intended analytical workflow:

1. owner-level posture first,
2. family-level evidence second,
3. document-level proof third,
4. field-level market context last.

## Portfolio Walkthrough: TOYOTA MOTOR CORPORATION

### 1. Entry route and tab model

Start at:

1. `/portfolio/TOYOTA_MOTOR_CORPORATION`

The portfolio workspace exposes five tabs:

1. `Overview`
2. `Families`
3. `Fields`
4. `Citation`
5. `Forecast`

Those labels are declared in `frontend_v2/components/portfolio/portfolio-primary-tabs.tsx:19-45`. The runtime accepts the same tab keys through the `tab` query param and defaults to `executive` when no tab is provided, as shown in `frontend_v2/components/portfolio/portfolio-workspace.tsx:87-133`.

For this example, the page should be read as a very large in-scope owner surface. The selected family `51225930` is not the portfolio itself. It is one family inside a Toyota portfolio row that currently carries 52,264 in-scope families in the bounded mega-cluster.

### 2. Overview tab

The overview tab renders five executive surfaces:

1. `PortfolioStatusDistributionPanel`
2. `PortfolioOverviewBrief`
3. `PortfolioFilingStrengthPanel`
4. `PortfolioStatusChronologyPanel`
5. `PortfolioJurisdictionUnlockPanel`

That composition is explicit in `frontend_v2/components/portfolio/portfolio-executive-tab.tsx:37-75`.

For the Toyota example, this tab should be used to answer four questions before opening any single family:

1. how large is the current in-scope estate,
2. how much of it is still active versus lapsed or dead,
3. how the filing base accumulated over time,
4. whether the current legal footprint is broadening or narrowing.

This is the right starting point because the later family example is easier to interpret when it is placed inside Toyota's larger owner context rather than read as an isolated patent family.

### 3. Families tab

Open:

1. `/portfolio/TOYOTA_MOTOR_CORPORATION?tab=families`

This tab is intentionally simple at the top level: it renders `PortfolioTopFamiliesTable` with search, status, primary-field, sort, and pagination controls, as shown in `frontend_v2/components/portfolio/portfolio-families-tab.tsx:22-56`.

For this example, the Families tab is where the walkthrough pivots from owner scale to the focal family:

1. use the ranking and filter controls to narrow the Toyota family set,
2. locate family `51225930`,
3. open the family route from that row.

This tab is important because it proves that the family walkthrough is not a disconnected demo identifier. It is part of the current Toyota in-scope portfolio.

### 4. Fields tab

Open:

1. `/portfolio/TOYOTA_MOTOR_CORPORATION?tab=fields`

This tab renders:

1. field cluster rail,
2. field exposure panel,
3. classification panel,
4. field timeseries panel,
5. field threats panel,
6. field citation-families panel,

as declared in `frontend_v2/components/portfolio/portfolio-fields-tab.tsx:44-110`.

For the current family example, this tab is the bridge into market logic:

1. family `51225930` has `primary_wipo_field = Electrical machinery, apparatus, energy`,
2. it also carries secondary coverage in `Measurement`,
3. the market walkthrough should therefore anchor first on `Electrical machinery, apparatus, energy`,
4. the secondary `Measurement` field can be used later as an adjacent interpretation check if needed.

If the owner-specific field timeseries is sparse, the tab may show the classification fallback note. That is not a defect. It is an explicit fallback path in `frontend_v2/components/portfolio/portfolio-fields-tab.tsx:77-89`.

### 5. Citation tab

Open:

1. `/portfolio/TOYOTA_MOTOR_CORPORATION?tab=citations`

This tab is the densest portfolio screen. It renders:

1. citation summary,
2. citation timeseries plus forecast contributors,
3. citation quality panel,
4. cited families panel,
5. top attackers panel,
6. CPC citation panel,
7. field panel,
8. jurisdiction panel,

as shown in `frontend_v2/components/portfolio/portfolio-citations-tab.tsx:77-215`.

For the Toyota example, this tab should be read in two layers:

1. portfolio-level incoming influence and pressure,
2. field-specific attack patterns that later help explain why family `51225930` matters.

The practical reading order is:

1. use the citation summary and chronology to understand Toyota's broader citation posture,
2. inspect the attacker, field, and jurisdiction slices to see where external pressure is concentrated,
3. compare that concentration with the focal family's primary field before drilling into the family page.

This tab is also where the owner-level citation forecast contributors are shown. That means the portfolio can be read as both a current-state citation surface and a forward-looking citation-risk surface without changing routes.

### 6. Forecast tab

Open:

1. `/portfolio/TOYOTA_MOTOR_CORPORATION?tab=forecast`

This tab renders only `PortfolioPendingGrantsPanel`, as shown in `frontend_v2/components/portfolio/portfolio-forecast-tab.tsx:18-40`.

That design is important for correct interpretation:

1. the tab is portfolio-level,
2. it is pending-grant candidate oriented,
3. it is not a detail view for already granted publications.

In this example, publication `EP2259376B1` is already grant-stage and family `51225930` is currently `fully_active`. Therefore the forecast tab should not be expected to spotlight this family directly. Its purpose is different: it shows which Toyota candidate families may add future enforceable footprint if they grant.

## Family Walkthrough: DOCDB Family 51225930

### 1. Entry route and tab model

Start at:

1. `/family/51225930`

The family workspace exposes four tabs:

1. `Publications`
2. `Legal`
3. `Fields`
4. `Citation`

Those labels are declared in `frontend_v2/components/family/family-workspace.tsx:36-60`. The family workspace defaults to `publications` in local component state, not in the URL, as shown in `frontend_v2/components/family/family-workspace.tsx:2105-2107`.

This matters operationally:

1. portfolio and market tabs are URL-driven,
2. family tab selection is local-state driven,
3. publication has no tab bar at all and is a continuous evidence page.

### 2. Publications tab

On first load, the family workspace opens the Publications tab. The tab renders:

1. `PublicationStagePanel`
2. `Member publications` data table
3. pagination and publication drill-through links

as shown in `frontend_v2/components/family/family-workspace.tsx:2314-2333`.

For family `51225930`, this is the first hard evidence surface:

1. the current family publication set contains 16 publications,
2. those publications span `CA, CN, EP, JP, KR, US, WO`,
3. `EP2259376B1` is one of the member publications and is the focal publication for the next walkthrough.

This tab should be used to answer:

1. which offices the family actually touched,
2. how many visible publication stages exist,
3. which concrete publication should be opened when document-level proof is needed.

### 3. Legal tab

Open the Legal tab inside the family workspace.

The tab renders:

1. `BranchStateMixPanel`
2. `JurisdictionFootprintPanel`
3. `LegalHistorySparkline`
4. `BlockingTrajectoryPanel`

as shown in `frontend_v2/components/family/family-workspace.tsx:2335-2348`.

For family `51225930`, the current anchor row already tells the user what this tab should broadly confirm:

1. `family_composite_status = fully_active`
2. `active_jurisdiction_count = 5`
3. `active_grant_branch_count = 5`

So the Legal tab should be read as the detailed proof layer behind those summary signals:

1. which branches are active,
2. how much of the family legal share sits in each jurisdiction,
3. whether the historical trend is stable or eroding,
4. how the legal state and blocking trajectory align.

### 4. Fields tab

Open the Fields tab inside the family workspace.

The tab renders:

1. `FieldFootprintPanel`
2. `ClassificationMapPanel`
3. `FieldTrajectoryPanel`
4. `CurrentFieldContributionPanel`

as shown in `frontend_v2/components/family/family-workspace.tsx:2350-2359`.

This tab is the cleanest place to connect the family example to the market example:

1. the family primary field is `Electrical machinery, apparatus, energy`,
2. the family also covers `Measurement`,
3. the market walkthrough should therefore start from the primary field,
4. the secondary field exists to show that the family is not always single-field pure.

This tab is also the best place to explain why PatentIQ uses field footprint rather than only raw CPC codes at the family reading level. The family page first gives a portfolio-safe, field-level interpretation surface. Only later, in the market Technology tab, does the walkthrough descend into CPC-group detail.

### 5. Citation tab

Open the tab labeled `Citation`.

The family evidence tab renders:

1. citation summary,
2. citation chronology,
3. top citing owners,
4. top cited family members,
5. citing families,

as shown in `frontend_v2/components/family/family-workspace.tsx:2361-2492`.

This is the main evidence layer for family `51225930` as an influential or pressured family:

1. the citation summary gives the high-level forward and backward footprint,
2. the chronology shows whether citation accumulation is still active,
3. top citing owners show who is interacting with the family,
4. top cited family members show which individual publications carry the citation burden,
5. the citing-families table shows the external family set citing into this family.

Important drill-through behavior is implemented directly here:

1. top cited family-member rows link to `/publication/<publication_number_full>` in `frontend_v2/components/family/family-workspace.tsx:2391-2404`,
2. citing-family rows link to `/family/<citing_docdb_family_id>` in `frontend_v2/components/family/family-workspace.tsx:2455-2464`.

For this example, the practical reading rule is:

1. use Publications when the question is "which documents belong to the family?",
2. use Citation when the question is "which members carry the forward-citation burden and who is citing them?"

## Publication Walkthrough: EP2259376B1

### 1. Entry route and page model

Start at:

1. `/publication/EP2259376B1`

The publication entry page itself describes this route as an evidence workspace for register facts, text evidence, and family-member navigation in `frontend_v2/app/(workspace)/publication/page.tsx:4-14`.

This page does not have tab navigation. It is a continuous evidence surface built from:

1. summary cards,
2. text preview,
3. family-member navigation,
4. legal timeline,
5. register evidence,
6. support details,

as shown by the rendered layout in `frontend_v2/components/publication/publication-workspace.tsx:462-547`.

For this example, the anchor publication row is:

1. `EP2259376B1`
2. `appln_id = 267542107`
3. `docdb_family_id = 51225930`
4. `publn_date = 2016-10-05`
5. `is_grant_stage = true`

### 2. Summary cards

The summary rail is generated from `overview.summaryCards`, with a few intentional rules:

1. `register_evidence` and `text_coverage` are removed from the visible card rail,
2. `application_id` may be inserted when needed,

as shown in `frontend_v2/components/publication/publication-workspace.tsx:463-487`.

For `EP2259376B1`, the summary rail should be treated as the fastest confirmation surface for:

1. office and kind,
2. filing or publication dates,
3. direct family connection,
4. application identity where available.

### 3. Abstract and claims

The `Abstract and claims` panel is rendered by `TextPreviewCard` in `frontend_v2/components/publication/publication-workspace.tsx:167-213`.

This panel carries two strong rules:

1. abstract and claim 1 are shown separately,
2. each one has its own `Available` or `Missing` status pill.

That means the page does not silently assume text completeness. For this example, this panel should be used to inspect the document-level technical description behind the family and field assignments already seen on the family page.

### 4. Family members

The `Family members` surface sits beside the text preview and links both backward and sideways:

1. it links back to `/family/51225930`,
2. it lists sibling publications inside the same family,
3. it shows their office, kind, and date,

as shown in `frontend_v2/components/publication/publication-workspace.tsx:500-537`.

For this example, this panel is where the user confirms that `EP2259376B1` is one document inside a 16-publication family rather than a standalone asset.

### 5. Legal timeline and register evidence

The page then renders:

1. `Legal and register timeline`
2. `Register evidence`

through `TimelinePanel` and `RegisterPanel` in `frontend_v2/components/publication/publication-workspace.tsx:215-292` and `540-541`.

These two panels answer different questions:

1. the timeline is chronological and event-oriented,
2. the register panel is factual and state-oriented.

For `EP2259376B1`, this is the correct place to inspect procedural and register-level proof behind the grant-stage interpretation.

### 6. Support details and caveats

The page ends with `SupportDetails`, driven by combined support levels and caveats from the publication overview and sections in `frontend_v2/components/publication/publication-workspace.tsx:543-547`.

This is important because the publication route is evidence-first, not score-first:

1. it tells the user what evidence is present,
2. it does not hide missing support,
3. it keeps caveat display on the same page as the evidence.

## Market Walkthrough Anchored To The Same Family

### 1. Entry route and selected segment

The market example should be anchored to the family primary field:

1. `Electrical machinery, apparatus, energy`

There are two equivalent ways to open it:

1. start at `/market`, then select the field from the overview table or analysis filter,
2. open the fully resolved route directly:
   `/market?state=rising&section=analysis&tab=competition&segment=Electrical%20machinery%2C%20apparatus%2C%20energy`

The market workspace reads the route query params:

1. `state`
2. `segment`
3. `section`
4. `tab`

in `frontend_v2/components/market/market-workspace.tsx:305-324`, then maps the selected field and state to backend API params `market_state` and `segment_id` through `frontend_v2/lib/api/market-v2.ts:22-40`.

The current segment anchor row shows:

1. `market_state = rising`
2. `total_family_count = 5,061,217`
3. `latest_year = 2025`
4. `latest_comparable_year = 2023`
5. `latest_year_incomplete = true`

That last pair matters. The analysis controls explicitly warn that state labels default to the latest comparable year even when newer priority years are incomplete, as stated in `frontend_v2/components/market/market-workspace.tsx:1735-1771`.

### 2. Overview section

Without explicit query params, the market page defaults to the `overview` section and uses the field league table as its primary selection surface. The section buttons and overview layout are defined in:

1. `frontend_v2/components/market/market-workspace.tsx:985-1018`
2. `frontend_v2/components/market/market-workspace.tsx:1499-1553`

The overview reading order should be:

1. `Market-wide chronology`
2. `Field league table`
3. `Leading jurisdictions by field`

The chronology surface includes:

1. current family and owner counts,
2. lifecycle mix,
3. counts-versus-mix toggle,
4. crowding and signal cards,

as shown in `frontend_v2/components/market/market-workspace.tsx:1019-1194`.

The field league table then becomes the selection surface for the exact field row. Clicking the field name writes the `segment` query param, as shown in `frontend_v2/components/market/market-workspace.tsx:1195-1213`.

For this example, the correct league-table row is `Electrical machinery, apparatus, energy`, because that is the primary field on family `51225930`.

### 3. Analysis section: Competition tab

Open:

1. `/market?state=rising&section=analysis&tab=competition&segment=Electrical%20machinery%2C%20apparatus%2C%20energy`

The analysis section begins with:

1. market filters,
2. selected-field drilldown header,
3. selected-field summary drawer,
4. evidence-tab bar,

as shown in `frontend_v2/components/market/market-workspace.tsx:1732-1978`.

Before using any tab-specific evidence, read the selected-field summary drawer. It exposes:

1. field scale,
2. competitive pressure,
3. defensive posture,
4. momentum,
5. field rationale,

as shown in `frontend_v2/components/market/market-workspace.tsx:1796-1955`.

Then read the Competition tab itself. It renders:

1. citation pressure chronology,
2. top owner presence,
3. top families in selected field,
4. top citing owners,
5. top citing jurisdictions,

as shown in `frontend_v2/components/market/market-analysis-competition.tsx:350-465`.

This tab is the closest market-level analogue to the family Citation tab:

1. the family page answers what happens around one family,
2. the market Competition tab answers what happens around the whole field that family belongs to.

It also completes the navigation loop:

1. owner leaderboard rows link back to portfolio routes in `frontend_v2/components/market/market-analysis-competition.tsx:174-217`,
2. top-family leaderboard rows link back to family routes in `frontend_v2/components/market/market-analysis-competition.tsx:225-250`.

### 4. Analysis section: Jurisdictions & Grants tab

Open:

1. `/market?state=rising&section=analysis&tab=jurisdictions&segment=Electrical%20machinery%2C%20apparatus%2C%20energy`

This tab renders:

1. `Field footprint by jurisdiction`
2. `Grant mix by office`
3. `Applications and grants by jurisdiction`

as shown in `frontend_v2/components/market/market-analysis-jurisdictions.tsx:57-240`.

This tab is the right follow-up after the family Legal tab because it changes the question:

1. family Legal asks where this one family is durable,
2. market Jurisdictions & Grants asks how the entire field is distributed and granting across offices.

The `Applications and grants by jurisdiction` panel also has its own jurisdiction filter and chart/table toggle, which makes it useful for testing whether a family's office footprint is typical for its field or unusually concentrated.

### 5. Analysis section: Technology tab

Open:

1. `/market?state=rising&section=analysis&tab=technology&segment=Electrical%20machinery%2C%20apparatus%2C%20energy`

This tab renders:

1. Technology filters
2. Top CPC groups in selected field
3. Top owners by CPC main group
4. Most citing owners by selected CPC
5. CPC geography within field

as shown in `frontend_v2/components/market/market-analysis-technology.tsx:51-420`.

This is the deepest technical decomposition in the walkthrough:

1. the family Fields tab gives field-level interpretation,
2. the market Technology tab decomposes that field into CPC-group structure,
3. the CPC owner and citing-owner tables show who dominates and who pressures each technical slice,
4. the CPC geography panel shows how that structure changes by jurisdiction.

Use this tab when the user needs to explain not just that family `51225930` belongs to `Electrical machinery, apparatus, energy`, but which subtechnical pockets inside that field are most structurally important.

## Cross-Route Continuity Shown By The Example

This example proves that the current application is one connected analytical system rather than separate pages with duplicated logic.

The continuity chain is:

1. Toyota portfolio route establishes owner-level scope and ranking context.
2. The portfolio Families tab provides the drilldown path into family `51225930`.
3. The family Publications tab provides the drilldown path into publication `EP2259376B1`.
4. The family Fields tab provides the pivot into the market segment `Electrical machinery, apparatus, energy`.
5. The market Competition tab can link back out to family and portfolio routes from the selected-field leaderboards.

That means one example can move in both directions:

1. top-down from owner to family to publication,
2. sideways from family to market,
3. bottom-up from market leaderboards back into owner and family pages.

## Interpretation Caveats For This Example

The following caveats should be kept explicit while using this appendix:

1. the portfolio Forecast tab is not a detail page for family `51225930`; it is a portfolio-level pending-grant candidate surface,
2. the family workspace keeps tab state locally, so deep links into a non-default family tab are not URL-stable in the same way as portfolio or market routes,
3. the publication route is evidence-first and intentionally avoids score-style synthesis,
4. the market segment state should be interpreted using latest comparable year logic rather than blindly reading incomplete priority years,
5. the family primary field is the correct main market anchor, but the same family also touches `Measurement`, so some neighboring field interpretations may still be relevant.

## Key Takeaways

This worked example shows the intended application flow clearly:

1. `TOYOTA MOTOR CORPORATION` is the owner-level entry point.
2. `51225930` is the family-level analytical anchor inside that portfolio.
3. `EP2259376B1` is the document-level proof surface inside that family.
4. `Electrical machinery, apparatus, energy` is the market-level field anchor derived from that family.

Using those four anchors together demonstrates how PatentIQ connects:

1. owner scale,
2. family durability,
3. publication evidence,
4. field-level market context,

without changing data contracts or analytical rules between routes.

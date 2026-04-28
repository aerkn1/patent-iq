# March 2026 Family / Legal / Analytics Master Index

## Purpose

This index groups the March 8, 2026 requirements notes added to `docs/new-feature-ideas` and defines the consistency rules that must govern implementation across them.

## What This Index Solves

The March 8 notes cover overlapping concerns:

1. family-first counting,
2. kind-code semantics,
3. UP / UPC treatment,
4. legal-status timelines,
5. historical vs current influence,
6. blocking-power decay,
7. jurisdiction weighting and normalization.

Without a grouping layer, engineering could implement these notes in isolation and create contradictory logic. This index is the consistency contract.

## Grouped Streams

## Stream A: Family-First Analytics Core

These files define the core entity logic for default analytics.

1. `family-level-collapse-and-metric-calculation-requirements.md`
2. `patent-kind-codes-and-document-lifecycle-representation-requirements.md`
3. `citation-semantics-and-tech-field-mapping-requirements.md`
4. `score-dimensionality-and-citation-weighting-requirements.md`
5. `citation-event-ledger-and-attacker-leaderboard-requirements.md`

Primary responsibility:
1. collapse lifecycle documents into `docdb_family_id`,
2. ensure family is the default analytics unit,
3. define which document layer contributes which signal,
4. define family-level citation semantics and tech-field mapping,
5. define 4D-versus-3D dimensionality boundaries for score families,
6. define citation-event threat tracking and attacker leaderboards.

## Stream B: UP / UPC / Territorial Coverage

These files define how UP and UPC effects alter coverage, risk, and family breadth.

1. `unitary-patent-and-upc-representation-requirements.md`

Primary responsibility:
1. detect UP status,
2. unroll UP geography,
3. model UPC centralized risk,
4. prevent `C0` inflation in trend and citation analytics.

## Stream C: Legal Status Lifecycle And Point-In-Time State

These files define how current and historical legal reality is reconstructed.

1. `legal-status-lifecycle-and-point-in-time-analytics-requirements.md`
2. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`

Primary responsibility:
1. maintain append-only legal event history,
2. derive composite family status,
3. separate current enforceability from historical influence,
4. rebuild scores at any requested date.

## Stream D: Global Jurisdiction Normalization And Weighted Reach

These files define how raw jurisdiction and kind-code data becomes reliable global analytics.

1. `global-legal-status-normalization-and-influence-evaluation-requirements.md`
2. `kind-code-normalization-and-tiered-market-weighting-build-guide.md`
3. `wipo-field-contribution-timeseries-requirements.md`
4. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
5. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`
6. `blocking-power-score-normalization-and-percentile-ranking-requirements.md`
7. `blocking-power-market-citation-fusion-requirements.md`
8. `parallel-global-and-local-trend-engines-requirements.md`
9. `global-vs-local-trend-role-allocation-requirements.md`

Primary responsibility:
1. normalize country + kind code into universal stages,
2. create tiered market weighting,
3. support weighted reach and weighted blocking-value metrics,
4. handle “ghost influence” and bifurcated portfolio logic,
5. support field-level heritage vs enforceability contribution timeseries,
6. support competitor leaderboards and tech-trend-weighted field dominance,
7. support monthly field-collision snapshots for competitor discovery,
8. support jurisdiction-by-field localized trend weighting for higher-precision enforceability scoring,
9. support raw-versus-normalized blocking-power score separation,
10. support explicit market-plus-citation fusion before UI normalization,
11. support parallel global and local trend engines plus global-local arbitrage analysis,
12. support explicit role allocation between macro global trends, local valuation trends, and heritage-context trends.

## Stream E: OECD Quality And Nature Of Innovation

These files define how OECD patent-quality methodology enriches the platform with cohort-safe quality, diversity, and breakthrough-style signals.

1. `oecd-quality-nature-of-innovation-requirements.md`
2. `oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`
3. `portfolio-size-normalization-and-crown-jewel-ranking-requirements.md`

Primary responsibility:
1. add a `nature_of_innovation` dimension,
2. enrich citation quality with fixed-window and diversity-aware metrics,
3. enrich heritage with originality and radicalness logic,
4. expose explainable OECD-style innovation tags,
5. enforce collapse-first family-level OECD calculation and hit-rate portfolio rollups,
6. define portfolio size normalization, crown-jewel ranking, and size-versus-quality comparison views.

## Stream F: Client-Enriched Financial Intelligence

These files define optional client-provided business-data integrations that convert the platform from pure patent intelligence into business and financial intelligence without requiring raw sensitive ERP uploads.

1. `client-provided-data-financial-intelligence-requirements.md`

Primary responsibility:
1. define low-risk aggregated client input contracts,
2. support revenue-at-risk, pruning ROI, and R&D efficiency workflows,
3. preserve optional client-side DuckDB/WASM execution patterns,
4. keep client-enriched outputs clearly separated from core public-data metrics.

## Stream G: Predictive Signals And Forecasting

These files define the interpretable forecasting layer that extends the platform from descriptive and diagnostic analytics into bounded predictive decision support.

1. `predictive-signals-and-interpretable-forecasting-requirements.md`

Primary responsibility:
1. define grant, lapse, friction, and trend forecasts,
2. preserve calibration and horizon guardrails,
3. store deterministic forecast outputs in silver-layer tables,
4. keep forecasts clearly separated from current-state metrics.

## Stream H: Semantic Similarity And Vector Retrieval

These files define how semantic retrieval and vector similarity should integrate with the family-first legal analytics stack without bypassing chronology, enforceability, or family-collapse rules.

1. `semantic-similarity-and-vector-layer-requirements.md`

Primary responsibility:
1. define semantic FTO and whitespace workflows,
2. enforce claim-versus-abstract vector-space separation,
3. enforce representative-family embedding collapse,
4. require chronology and legal-context joins on semantic results,
5. define backend vector-search to deterministic analytics join patterns.

## Stream I: Dataset Scope And Boundary Governance

These files define how the MVP dataset boundary should be selected, labeled, and enforced so the platform can operate as a mathematically valid sector-bounded intelligence environment.

1. `mega-cluster-dataset-scope-and-boundary-governance-requirements.md`

Primary responsibility:
1. define the 10-field mega-cluster dataset scope,
2. define out-of-bounds ghost-node handling for citation math,
3. enforce sector-bounded portfolio denominators and labels,
4. define semantic sampling guardrails for the MVP,
5. define scope metadata required by UI and API contracts.

## Stream J: PATSTAT Register EP Legal Power-Up

These files define how PATSTAT Register may enrich EP and UP procedural truth in the MVP without contaminating the global family-first and 4D scoring math.

1. `patstat-register-read-only-legal-power-up-requirements.md`

Primary responsibility:
1. define PATSTAT Register as an EP-only read-only legal overlay,
2. define permitted Bronze and Silver Register ingestion scope,
3. define Level 2 family badges and Level 3 publication evidence usage,
4. define the EP-special grant-model exception,
5. ban Register-driven drift in cross-office blocking-power and portfolio percentile logic.

## Stream K: Data Room Transparency And Methodology Wiki

These files define how PatentIQ should expose its data, methodology, models, and semantic evidence in a read-only in-app transparency layer.

1. `data-room-transparency-and-methodology-wiki-requirements.md`

Primary responsibility:
1. define the in-app Data Room as a read-only transparency surface,
2. define wiki-style methodology pages,
3. define dataset catalog and downloadable artifact rules,
4. define model and semantic evidence visibility,
5. preserve traceability from app claims to source/data/methodology evidence.

## Stream L: UI Workspace And Page Contracts

These files define how the product should structure its top-level workspaces, page-level questions, drill-down hierarchy, and page-shaped backend contracts.

1. `ui-workspace-and-page-contract-requirements.md`

Primary responsibility:
1. define top-level workspaces,
2. define portfolio-family-publication drill-down,
3. define Market Intelligence as a first-class workspace,
4. define page-shaped backend contracts,
5. align frontend UX with family-first analytics and Data Room transparency.

## Consistency Rules

## CR-01: Family Is The Default Counting Unit

Across all grouped notes:
1. the default innovation entity is the family,
2. publication/document counts are diagnostic only,
3. lifecycle records must not create extra invention counts.

## CR-02: Document-Level Logic Exists Only To Feed Family-Level Analytics

Document-level records are still required, but their role is:
1. choosing the right text source,
2. reconstructing legal events,
3. tracing citations,
4. selecting enforceable vs pending evidence.

They are not the default reporting unit.

## CR-03: B-Level Rights Drive Enforceability

For legal and blocking workflows:
1. `B`-level signals are primary,
2. `A`-level signals are pending/research indicators only,
3. `C`-level signals are legal modifiers layered on top of grants.

## CR-04: UP Expansion Happens Before Territorial Metrics

If UP/C0 is present:
1. detect it first,
2. unroll participating states,
3. then compute raw breadth and weighted reach,
4. but do not let that expansion create extra filing events.

## CR-05: Current And Historical Questions Must Not Share The Same Filter

When the product answers:
1. current legal threat,
2. current blocking power,
3. current active breadth,

it must use current or requested point-in-time activity filters.

When it answers:
1. historical innovation,
2. prior-art relevance,
3. historical citation influence,
4. R&D momentum,

it must keep dead families in scope.

## CR-06: Event History Is The Source Of Truth For Time-Varying Metrics

Any metric that changes with:
1. grant,
2. lapse,
3. revocation,
4. renewal,
5. opposition,
6. expiry,

must be reconstructable from the legal-status event mart, not a flat overwritten status field.

## CR-07: Raw Breadth And Weighted Reach Must Coexist

Do not collapse these into one metric.

1. raw breadth answers “how many jurisdictions?”
2. weighted reach answers “how commercially important are those jurisdictions?”

Both must remain visible in the data model.

## CR-08: Historical Influence And Current Blocking Power Must Be Separate Pillars

At portfolio level:
1. historical influence can include dead but foundational assets,
2. current blocking power must exclude dead rights,
3. dashboards must label the distinction explicitly.

The same separation must also hold for:
1. citation views,
2. WIPO field-contribution views,
3. portfolio influence versus enforceability charts.

## CR-09: Office-Specific Semantics Must Be Normalized Before Aggregation

Never aggregate raw kind codes globally without first mapping them through:

1. a jurisdiction-aware kind-code normalization layer,
2. a universal stage model,
3. office-aware semantics for value/resilience multipliers.

## CR-10: EP B2 And Similar Resilience Signals Must Not Be Lost

If the data shows a survived challenge signal such as EP `B2`, the legal-strength and blocking-power models must preserve that uplift after family rollup.

## CR-11: Geographic Breadth And Tech Breadth Must Stay Separate

1. geographic breadth describes territorial enforceability,
2. tech breadth describes sector reach via WIPO fields or equivalent clusters,
3. one must never be used as a synonym for the other.

## CR-12: WIPO Field Contribution Must Support Two Lines

For field-level contribution analytics:
1. enforceability contribution must use active legal stage and market weighting,
2. heritage contribution must use citation-weighted historical influence,
3. both lines must remain queryable and separately explainable.

## CR-13: Competitor Intelligence Must Be Field-Sliced

1. overall portfolio score is not enough for competitor discovery,
2. leaderboards must be computed inside specific WIPO/CPC fields,
3. current threats rank by enforceability,
4. pioneers rank by heritage.

## CR-14: Overall Blocking Power Must Be Bottom-Up

1. compute field-specific contributions first,
2. apply field trend multipliers at the field level,
3. then sum them to get overall blocking power.

## CR-15: Competitor Discovery Must Use Snapshotable Field Collisions

1. competitor discovery must be based on assignee collisions inside a specific field,
2. default storage should support monthly point-in-time snapshots,
3. leaderboards should query prebuilt field marts rather than raw document joins on the UI path.

## CR-16: Localized Jurisdiction-Tech Weighting Refines Global Field Trends

1. global field trend coefficients remain valid as the base model,
2. jurisdiction-by-field coefficients are the preferred higher-precision extension for enforceability scoring,
3. any fallback from local to global coefficients must be explicit in metadata and marts.

## CR-17: Raw Scores And UI Scores Must Be Separate

1. raw blocking-power scores are the unbounded mathematical outputs,
2. UI blocking-power scores should be percentile-ranked normalized outputs,
3. min-max scaling must not be used for the main UI metric,
4. normalization cohort and method metadata must be preserved.

## CR-18: 4D Jurisdiction Logic Applies Only To Enforceability-Side Metrics

1. jurisdiction-aware 4D logic applies to enforceability and current threat metrics,
2. heritage and historical citation influence remain global family-field 3D metrics,
3. geographic citation weighting, if used, should be applied through the citing side rather than by fragmenting the cited family’s heritage output.

## CR-19: Final Blocking Power Must Fuse Market Threat And Citation Impact

1. final blocking power must not be legal-footprint-only,
2. market-threat math and adjusted citation impact must be fused at family level,
3. percentile normalization applies after the fusion step, not before.

## CR-20: Global And Local Trend Engines Must Coexist

1. global tech trends remain a first-class engine for macro market intelligence,
2. local jurisdiction-tech trends remain a first-class engine for valuation and blocking analysis,
3. the product should support comparing global and local growth to detect geographic arbitrage and whitespace.

## CR-21: Trend Layers Must Respect Their Metric Roles

1. current enforceability and blocking-power scoring should use local trend reality,
2. macro landscaping should use global trend reality,
3. heritage may use global trend context but must not inherit local enforceability weighting,
4. global-local deltas belong in hotspot and arbitrage views rather than being silently folded into local blocking power.

## CR-22: OECD Quality Signals Enrich But Do Not Replace Core Taxonomy

1. OECD quality indicators depend on field mapping and cohort context,
2. they must not replace CPC/IPC/WIPO taxonomy,
3. they should enrich citation, breadth, and heritage interpretation with generality, originality, radicalness, and truncation-aware windows.

## CR-23: OECD Metrics Must Be Calculated Family-First

1. do not calculate OECD quality metrics at patent level and average them up,
2. collapse and deduplicate the citation pool at family level first,
3. normalize OECD metrics against family-level cohorts,
4. portfolio rollups should prefer hit-rate or density metrics over simple means.

## CR-24: Forward Citations Must Support Threat-Network Analytics

1. forward citations should be storable as dated citing-side events,
2. attacker leaderboards should use citing-side lethality rather than count alone,
3. portfolio threat matrices should be able to aggregate citing assignee, jurisdiction, field, and time.

## CR-25: Portfolio Ranking Must Separate Mass, Density, And Crown Jewels

1. do not rank portfolios using only total summed mass,
2. do not rank portfolios using only averages or medians,
3. expose distinct views for total mass, hit-rate density, and crown-jewel strength,
4. compare startup and giant portfolios using top-tier subsets when the goal is size-agnostic weapon comparison.

## CR-26: Client-Enriched Financial Analytics Must Remain Optional And Segregated

1. client-provided business inputs are optional overlays, not core required data,
2. public patent metrics must remain computable without client financial data,
3. client-enriched outputs should preserve assumption and provenance labels,
4. local-only DuckDB/WASM execution should be preferred when sensitive data must not touch the server.

## CR-27: Predictive Signals Must Be Interpretable And Separated From Current Reality

1. predictive outputs must be labeled as forecasts rather than current truth,
2. bounded probabilities require calibration,
3. short-horizon time-series forecasts require explicit horizon limits,
4. heavy model training should run offline while DuckDB serves deterministic forecast outputs.

## CR-28: Predictive Signals Must Be Executed Bottom-Up At Their Native Grain

1. do not predict an entire portfolio as one undifferentiated entity when the underlying risk is local,
2. grant probability should execute at publication or sub-family grain before assignee rollup,
3. lapse risk should execute at family-jurisdiction grain before portfolio rollup,
4. friction risk should execute at family grain with jurisdiction-aware evidence before portfolio rollup,
5. trend momentum forecasting should execute at jurisdiction-field grain and then be compared against portfolio coverage,
6. every portfolio-level forecast KPI must remain drillable to the exact micro-level scored rows that produced it.

## CR-29: Semantic Retrieval Must Respect Family Collapse, Claim Scope, And Chronology

1. semantic retrieval should deduplicate and rank results at family level rather than publication level,
2. enforceability workflows must prefer claim-oriented vectors while landscape workflows may use abstract-oriented vectors,
3. representative-family text selection must follow a deterministic hierarchy rather than embedding every family member,
4. semantic matches must always be intersected with chronology and legal status before they are shown as strategic threats or opportunities,
5. semantic similarity is a discovery signal and must not be presented as legal infringement proof by itself.

## CR-30: Dataset Scope Must Be Explicit, Bounded, And Preserved In Denominators

1. the MVP analysis universe should be treated as a bounded mega-cluster rather than a universal global patent estate,
2. portfolio denominators must use only in-scope families unless a separate universal layer exists,
3. out-of-bounds citations must be preserved as ghost nodes for citation and OECD math without fabricating full in-scope analytics for them,
4. UI and API labels must explicitly declare sector-bounded scope,
5. semantic and client-data modules must honor the same scope boundary rather than silently assuming universal coverage.

## CR-31: PATSTAT Register Must Remain An EP-Only Read-Only Legal Overlay

1. PATSTAT Register may enrich EP application detail, family badges, and publication evidence surfaces,
2. PATSTAT Register may feed isolated EP-special predictive features,
3. PATSTAT Register must not alter cross-office family blocking-power percentiles,
4. PATSTAT Register must not alter portfolio percentile rankings or crown-jewel density math.

## CR-32: PATSTAT Register And INPADOC Must Follow A Dual-Clock Hierarchy

1. for EP publication-detail and EP Register evidence views, Register procedural status may override INPADOC when they conflict,
2. for global family ranking and cross-office comparability, Register detail must remain an overlay rather than a hidden score booster,
3. override provenance must remain visible in marts and UI metadata.

## CR-33: PATSTAT Register Must Bubble Up Carefully From `appln_id` To Family

1. Register data is native to `appln_id`, not `docdb_family_id`,
2. family-level marts may expose EP-specific flags such as active opposition or lead agent,
3. those flags must not overwrite the canonical global family state,
4. the UI should distinguish global family truth from EP member procedural truth.

## CR-34: Semantic Text Selection Must Use The Global Full-Text Hierarchy

1. semantic representative text should prefer U.S. grant Claim 1 from USPTO full text,
2. then English EP grant Claim 1 from EPAB,
3. then English PATSTAT abstract fallback if no usable U.S. or EP grant claims exist,
4. `A`-document claims must not power FTO or infringement workflows,
5. USPTO and EPAB full-text sources must act as text providers only rather than replacing PATSTAT and Register metadata layers.

## Recommended Engineering Read Order

1. `family-level-collapse-and-metric-calculation-requirements.md`
2. `patent-kind-codes-and-document-lifecycle-representation-requirements.md`
3. `unitary-patent-and-upc-representation-requirements.md`
4. `legal-status-lifecycle-and-point-in-time-analytics-requirements.md`
5. `citation-semantics-and-tech-field-mapping-requirements.md`
6. `global-legal-status-normalization-and-influence-evaluation-requirements.md`
7. `kind-code-normalization-and-tiered-market-weighting-build-guide.md`
8. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
9. `wipo-field-contribution-timeseries-requirements.md`
10. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
11. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`
12. `blocking-power-score-normalization-and-percentile-ranking-requirements.md`
13. `blocking-power-market-citation-fusion-requirements.md`
14. `parallel-global-and-local-trend-engines-requirements.md`
15. `global-vs-local-trend-role-allocation-requirements.md`
16. `oecd-quality-nature-of-innovation-requirements.md`
17. `oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`
18. `citation-event-ledger-and-attacker-leaderboard-requirements.md`
19. `portfolio-size-normalization-and-crown-jewel-ranking-requirements.md`
20. `client-provided-data-financial-intelligence-requirements.md`
21. `predictive-signals-and-interpretable-forecasting-requirements.md`
22. `semantic-similarity-and-vector-layer-requirements.md`
23. `mega-cluster-dataset-scope-and-boundary-governance-requirements.md`
24. `patstat-register-read-only-legal-power-up-requirements.md`
25. `data-room-transparency-and-methodology-wiki-requirements.md`
26. `ui-workspace-and-page-contract-requirements.md`

## Implementation Order Recommendation

### Phase 1: Entity And Event Correctness

1. family collapse,
2. kind-code preservation,
3. legal-status event mart,
4. point-in-time filters.

### Phase 2: Jurisdiction And Market Normalization

1. kind-code normalization table,
2. UP unrolling,
3. tiered market weighting,
4. weighted reach calculations.

### Phase 3: Strategic Metrics

1. adjusted citation impact,
2. opposition resilience,
3. current blocking power,
4. historical influence pillar,
5. bifurcated portfolio dashboards,
6. WIPO field contribution timeseries,
7. market-threat and adjusted-citation component generation,
8. fused raw absolute blocking-power generation,
9. percentile-ranked UI normalization,
10. parallel global and local trend engines,
11. global-versus-local role allocation across valuation and landscape modules,
12. OECD quality enrichment and nature-of-innovation descriptors,
13. family-first OECD calculation and portfolio hit-rate rollups,
14. citation-event threat network and attacker leaderboards,
15. portfolio size normalization and crown-jewel ranking views,
16. client-enriched financial intelligence workflows,
17. predictive signals and forecast overlays,
18. semantic retrieval and chronology-safe vector matching,
19. mega-cluster scope enforcement and ghost-node handling,
20. field-sliced competitor intelligence,
21. PATSTAT Register EP legal power-up overlays.
22. Data Room transparency and methodology-wiki surfaces.
23. page-shaped frontend/backend workspace contracts and market-intelligence routing.

## Files Included In This Group

1. `blocking-power-lifecycle-and-point-in-time-scoring-requirements.md`
2. `family-level-collapse-and-metric-calculation-requirements.md`
3. `global-legal-status-normalization-and-influence-evaluation-requirements.md`
4. `kind-code-normalization-and-tiered-market-weighting-build-guide.md`
5. `legal-status-lifecycle-and-point-in-time-analytics-requirements.md`
6. `patent-kind-codes-and-document-lifecycle-representation-requirements.md`
7. `citation-semantics-and-tech-field-mapping-requirements.md`
8. `score-dimensionality-and-citation-weighting-requirements.md`
9. `unitary-patent-and-upc-representation-requirements.md`
10. `wipo-field-contribution-timeseries-requirements.md`
11. `field-sliced-competitor-intelligence-and-tech-trend-requirements.md`
12. `jurisdiction-tech-trend-and-localized-blocking-power-requirements.md`
13. `blocking-power-score-normalization-and-percentile-ranking-requirements.md`
14. `blocking-power-market-citation-fusion-requirements.md`
15. `parallel-global-and-local-trend-engines-requirements.md`
16. `global-vs-local-trend-role-allocation-requirements.md`
17. `oecd-quality-nature-of-innovation-requirements.md`
18. `oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`
19. `citation-event-ledger-and-attacker-leaderboard-requirements.md`
20. `portfolio-size-normalization-and-crown-jewel-ranking-requirements.md`
21. `client-provided-data-financial-intelligence-requirements.md`
22. `predictive-signals-and-interpretable-forecasting-requirements.md`
23. `semantic-similarity-and-vector-layer-requirements.md`
24. `mega-cluster-dataset-scope-and-boundary-governance-requirements.md`
25. `patstat-register-read-only-legal-power-up-requirements.md`
26. `data-room-transparency-and-methodology-wiki-requirements.md`
27. `ui-workspace-and-page-contract-requirements.md`

## Final Consistency Summary

The grouped notes are consistent if engineering implements them with the following invariant order:

1. normalize document lifecycle,
2. collapse to family,
3. reconstruct legal state by date,
4. unroll UP geography,
5. normalize jurisdiction + kind code,
6. compute raw breadth, weighted reach, and tech breadth,
7. split historical influence from current blocking power,
8. keep heritage global and enforceability jurisdiction-aware,
9. compute field-level heritage and enforceability contributions,
10. add localized jurisdiction-tech coefficients where data coverage supports them,
11. calculate market-threat and adjusted-citation component scores,
12. fuse them into raw absolute blocking-power scores,
13. normalize UI scores via percentile-ranked peer cohorts,
14. preserve both global and local trend engines and compute their deltas,
15. apply the correct role allocation for local valuation, global landscaping, and heritage context,
16. enrich scores with OECD quality and nature-of-innovation descriptors,
17. compute OECD metrics with collapse-first family pipelines and hit-rate portfolio rollups,
18. build citation-event threat ledgers and attacker leaderboards,
19. build portfolio mass, hit-rate, and crown-jewel rollups,
20. layer optional client-enriched financial analytics on top of the public patent engine,
21. execute predictive models at their native micro-level grains and persist traceable outputs,
22. layer calibrated predictive signals on top of deterministic marts,
23. add family-level semantic retrieval and chronology-safe vector matching,
24. enforce mega-cluster dataset boundaries, ghost nodes, and scope-aware denominators,
25. build field-sliced competitor leaderboards and trend coefficients,
26. add EP-only PATSTAT Register overlays and EP-special predictive features without touching percentile math,
27. expose read-only Data Room evidence, methodology wiki pages, and approved artifact catalogs,
28. structure the product around stable workspaces and page-shaped backend contracts,
29. roll up to harmonized owner entities.

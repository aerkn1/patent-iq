# PatentIQ V2 UI Serving Silver/Gold Boundary Audit

## Purpose

Broaden the earlier portfolio-only metric audit into a full UI-serving boundary audit for:

1. `Family`
2. `Publication`
3. `Portfolio`
4. `Market`

The goal is to define a stable representation rule:

1. what should remain raw evidence in `Silver`,
2. what may exist in `Silver` as analytic inputs but must not be served directly as UI truth,
3. what must be normalized, stage-aware, PIT-safe, and UI-safe in `Gold`.

This audit also applies the same rule to citation representation across:

1. family,
2. filing/publication,
3. portfolio,
4. market.

This note should become the canonical reference for the upcoming Silver/Gold refactor rather than treating the portfolio issues as isolated anomalies.

Related notes:

1. [11-patentiq-v2-metric-lineage-catalog.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/11-patentiq-v2-metric-lineage-catalog.md)
2. [32-patentiq-v2-family-and-publication-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/32-patentiq-v2-family-and-publication-page-contract.md)
3. [30-patentiq-v2-market-intelligence-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/30-patentiq-v2-market-intelligence-page-contract.md)
4. [33-patentiq-v2-portfolio-and-forecast-page-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/ui-contracts/33-patentiq-v2-portfolio-and-forecast-page-contract.md)
5. [61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/61-patentiq-v2-portfolio-current-state-audit-and-remediation-plan.md)
6. [62-patentiq-v2-portfolio-executive-metric-sensibility-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/62-patentiq-v2-portfolio-executive-metric-sensibility-audit.md)
7. [37-patentiq-v2-client-input-overlays-applicability-and-ui-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/37-patentiq-v2-client-input-overlays-applicability-and-ui-contract.md)

---

## 1. Governing Boundary Rule

### 1.1 Silver responsibility

`Silver` should hold:

1. raw evidence,
2. deterministic entity-level facts,
3. event ledgers,
4. chronology-safe raw counts,
5. bridge tables and coverage tables,
6. analytic intermediate features that are useful for modeling and downstream aggregation.

`Silver` should not be treated as final UI truth for:

1. bounded scores,
2. percentile-like cards,
3. lifecycle-aware strength labels,
4. support-banded predictions,
5. normalized cross-entity comparisons,
6. score-like historical overlays.

### 1.2 Gold responsibility

`Gold` should hold:

1. serving-safe aggregates,
2. stage-aware and status-aware metrics,
3. bounded indices and percentiles,
4. PIT-safe historical summaries,
5. endpoint-ready portfolio/market/family representations,
6. caveated prediction and support metadata for UI.

### 1.3 Exception rule

Not every UI-visible value needs to be promoted to `Gold`.

Some product surfaces are evidence-first by nature and may remain directly Silver-backed:

1. publication bibliographic detail,
2. legal/register event timelines,
3. raw evidence tables,
4. provenance rows,
5. drill-down ledgers.

The key rule is:

1. `Silver` may power evidence surfaces,
2. `Silver` should not power polished strategic-score surfaces directly.

---

## 2. Current Serving Reality By Surface

### 2.1 Family

Current contract expects a mixed stack:

1. `gold_family_summary`
2. `gold_family_blocking_power`
3. `gold_family_blocking_power_timeseries`
4. `gold_family_field_contributions`
5. `gold_family_field_contributions_timeseries`
6. `gold_family_heritage_summary`
7. supporting Silver legal, coverage, publication, OECD, and citation marts

Current backend-v2 repository is materially under-scoped and currently points only to:

1. `gold_family_summary.parquet`
2. `gold_family_classification_mix_pit.parquet`
3. family forecast model outputs
4. family lapse-risk model outputs

This means the family contract is conceptually Gold-first, but the serving codebase still has partial family coverage and will need the broader refactor.

### 2.2 Publication

Current contract is evidence-first.

Current backend-v2 repository is Silver-backed:

1. `silver_family_member_publications.parquet`
2. `silver_ep_register_core.parquet`

This is mostly correct semantically. Publication pages should remain evidence-forward rather than being forced into synthetic Gold scorecards.

### 2.3 Portfolio

Current portfolio contract is heavily Gold-oriented but still depends on Silver owner bridges and some family-level Silver-derived inputs flowing into Gold.

Current backend-v2 portfolio surfaces already consume multiple Gold marts, but earlier audits showed that some executive metrics inherit unstable family-level inputs.

Portfolio is therefore the clearest example of why:

1. Silver-derived analytics are useful,
2. but Gold normalization and gating must be stricter before UI exposure.

### 2.4 Market

Current backend-v2 market repository is Gold-heavy:

1. `gold_market_summary_pit.parquet`
2. `gold_market_intelligence_timeseries.parquet`
3. `gold_market_cpc_trend_pit.parquet`
4. `gold_cpc_importance_pit.parquet`

This is directionally correct, but the market surface still needs an audit to ensure:

1. current overlays are not mislabeled as PIT,
2. concentration and importance scores are treated as indices, not probabilities,
3. any family-level contamination does not silently propagate upward.

---

## 3. Serving Classification Framework

Every UI-facing metric or table should be classified into exactly one of these groups.

### 3.1 `SilverRawEvidence`

Use directly in UI when the UI is intentionally evidentiary.

Examples:

1. publication metadata,
2. claims/abstract text,
3. EP register facts,
4. legal event timelines,
5. citation event ledger rows,
6. family member publication rows.

### 3.2 `SilverAnalyticIntermediate`

Useful for ETL, modeling, and derived logic, but not for direct polished-card serving.

Examples:

1. `family_adjusted_citation_score_raw`,
2. branch-level enforceability contribution raw,
3. raw market weight sums,
4. raw field fractions,
5. cohort-relative citation ratios,
6. unbounded mass sums before calibration.

### 3.3 `GoldServingMetric`

Safe to present in UI once documented and caveated.

Examples:

1. family summary counts,
2. portfolio status splits,
3. market segment counts,
4. PIT-safe classification shares,
5. risk bands,
6. interval-first forecast summaries.

### 3.4 `GoldNeedsRebuild`

Already in Gold, but not yet semantically safe enough for direct UI use.

Examples already identified:

1. pending-family-inflated blocking power,
2. portfolio executive metrics derived from that blocking logic,
3. any current-overlay mart presented as historical PIT,
4. any unbounded aggregate still labeled as a normalized score.

### 3.5 Citation-specific boundary rule

Citation data needs a stricter version of the same boundary because the product uses citations for:

1. raw proof and drill-down,
2. strategic influence scoring,
3. threat ranking,
4. portfolio summaries,
5. field and market pressure views,
6. PIT model features.

The citation rule is:

1. raw citation events, cleaned edges, and dated citation facts belong in `Silver`,
2. weighted citation totals, cohort-relative citation transforms, and citation lethality ingredients may exist in `Silver` as analytic intermediates,
3. any citation value shown as a score, rank, band, index, or executive summary belongs in `Gold`,
4. any citation chronology shown as PIT must come from dated event ledgers or as-of-safe snapshot inputs.

Current primary citation artifacts:

1. `silver_family_citation_edges`
2. `silver_family_citation_edges_clean`
3. `silver_enriched_citation_network`
4. `silver_family_citation_metrics`
5. `silver_family_feature_snapshot_pit`

Current primary citation-serving consumers:

1. `gold_family_blocking_power`
2. `gold_family_blocking_power_timeseries`
3. `gold_family_heritage_summary`
4. `gold_family_attacker_summary`
5. `gold_portfolio_threat_matrix`
6. `gold_portfolio_forecast_summary`

Primary current citation risk:

1. `family_adjusted_citation_score_raw` is acting both as a modeling intermediate and as a de facto serving influence score, which is semantically unsafe.

---

## 4. Family Surface Audit

## 4.1 Family UI sections that need serving-safe outputs

Per the family page contract, the family page needs:

1. identity and status,
2. blocking power and explainability,
3. legal and coverage state,
4. field and market footprint,
5. trajectory over time,
6. classification footprint,
7. evidence rows,
8. forecast/risk overlays.

## 4.2 Family data classes

### Safe as direct evidence or factual status

These may remain Silver-backed or Silver-derived and can be shown directly:

1. `silver_family_status_pt`
2. `silver_family_status_history`
3. `silver_branch_status_history_dense`
4. `silver_family_member_publications`
5. `silver_family_coverage_metrics`
6. `silver_family_wipo_fields`
7. `silver_enriched_citation_network` for ledger-style evidence only

### Must not be served directly as polished strategic cards

These are analytically useful but should not appear as final UI truth:

1. `family_adjusted_citation_score_raw`
2. raw branch enforceability contribution
3. raw field heritage contribution scores
4. unbounded citation lethality accumulations
5. any raw or fallback OECD proxy that is not explicitly normalized for serving

### Citation-specific family rule

Family citation representation should split into three lanes:

1. `Evidence lane`
   - raw citing-family or citing-publication proof rows from `silver_enriched_citation_network`
2. `Summary lane`
   - current forward, backward, and NPL citation summaries
3. `Strategic lane`
   - heritage, attacker ranking, blocking contribution, and forecast eligibility

Only the first lane should be directly Silver-served.

The second and third lanes should be Gold-owned or rebuilt into Gold-ready summaries.

### Must be Gold-owned

These should be computed and documented in Gold:

1. `family_ui_blocking_power_score`
2. `family_raw_absolute_blocking_power`
3. family blocking trajectory
4. family field contribution trajectory
5. family summary scorecards and explainability panels
6. current-vs-selected-year family compare metrics

## 4.3 Critical family findings

1. `pending_emerging` families currently receive extremely high blocking-power UI scores due to unstable citation-driven normalization rather than legal enforceability.
2. This violates the intended lifecycle semantics that pending families may have low emerging strategic signal but should not surface as top current blockers.
3. Family Gold must split:
   - `blocking_power`
   - `emerging_influence`
4. Family Gold must apply:
   - stage gating,
   - denominator floors,
   - winsorization or caps,
   - minimum observation-age constraints,
   - explicit support metadata where history is sparse.

## 4.4 Family refactor decisions

Keep in Silver:

1. event ledgers,
2. status histories,
3. coverage facts,
4. member publication evidence,
5. CPC/WIPO membership facts,
6. raw citation metrics.

Move normalization responsibility to Gold for:

1. blocking power,
2. strategic influence,
3. citation-derived strength descriptors,
4. family compare axes,
5. explainability panels that imply final judgment.

Citation-specific family decisions:

1. keep forward citation ledgers, cleaned citation edges, raw counts, backward patent counts, backward NPL counts, and self/intra-family flags in Silver,
2. treat `family_forward_citations_weighted`, `family_adjusted_citation_score_raw`, and fallback OECD citation blends as Silver analytic intermediates only,
3. promote family citation summary cards, heritage summaries, attacker leaderboards, citation influence bands, and PIT-safe citation chronology into Gold.

---

## 5. Publication Surface Audit

## 5.1 Publication UI role

The publication page answers:

1. what exact document-level evidence exists,
2. what stage/kind/office the document belongs to,
3. what legal/register evidence supports the family story.

This is not a score-first workspace.

## 5.2 Publication data classes

Safe as direct Silver-backed UI evidence:

1. `silver_family_member_publications`
2. `silver_ep_register_core`
3. publication text and claims/abstract availability
4. register/legal timeline events
5. provenance/source availability flags

Citation-specific filing/publication rule:

1. filing/publication citation should remain evidence-first,
2. raw citing/cited document relationships, citation dates, citing jurisdiction, citing assignee, and proof rows are safe as Silver evidence,
3. document-level “strength” or “threat” scores should not be shown unless a dedicated Gold publication-citation contract is introduced later.

Gold is optional for:

1. family-context summary references,
2. derived publication coverage badges,
3. curated evidence summaries if needed later.

## 5.3 Publication findings

1. Publication should remain the clearest evidence-first exception to the Gold-first rule.
2. A publication page should not invent synthetic “publication strength” scores unless there is a real Gold contract for them.
3. If summary badges are added, they should remain factual:
   - office,
   - kind/stage,
   - linked family,
   - legal/register coverage present,
   - representative text available.
4. Citation at filing/publication level should be treated as proof and provenance, not as the unit of strategic headline scoring.

## 5.4 Publication refactor decisions

Keep Silver-first:

1. bibliographic data,
2. timeline evidence,
3. register evidence,
4. provenance,
5. text evidence.

For filing/publication citation specifically:

1. keep raw citation evidence in Silver,
2. expose citation rows with filters and provenance,
3. avoid Gold scorecards unless a dedicated publication-citation serving contract is introduced later.

Use Gold only for:

1. family-context side panels,
2. strategic context inherited from family, not document-native scoring.

---

## 6. Portfolio Surface Audit

## 6.1 Portfolio UI sections that need serving-safe outputs

Portfolio now includes:

1. executive,
2. families,
3. citations,
4. field clusters,
5. threats,
6. forecast,
7. classification,
8. compare.

## 6.2 Portfolio data classes

Safe or mostly safe in current form:

1. family counts,
2. active/pending/abandoned status splits,
3. active grant family count,
4. semantic candidate count,
5. paginated family rows,
6. citation evidence tables,
7. threat tables after self/unknown-owner exclusions,
8. classification PIT shares,
9. compare metadata with explicit replay caveats.

Gold metrics that require relabeling or caveats:

1. `portfolio_total_mass_score`
2. `portfolio_current_threat_score`
3. `portfolio_heritage_score`

Citation-specific portfolio rule:

Portfolio citation representation should use four lanes:

1. `Evidence`
   - attacker drill-down proof rows
2. `Summary`
   - forward, backward, and NPL citation aggregates
3. `Threat`
   - citing-assignee, jurisdiction, and field-ranked pressure views
4. `Forecast`
   - interval-first future citation outputs

Current backend-v2 already serves this area through:

1. `/citation-summary`
2. `/citation-timeseries`
3. `/citation-attackers`
4. `/citation-fields`
5. `/citation-jurisdictions`

Only the first lane should ever be directly Silver-driven.

The other three lanes should be Gold-owned or derived from dedicated Gold summary marts built from Silver citation evidence.

Gold metrics already identified as unsafe pending upstream rebuild:

1. `portfolio_avg_blocking_power_within_mega_cluster`
2. `portfolio_hit_rate_top_decile`
3. `portfolio_crown_jewel_index`

Silver inputs that must not leak into UI without Gold normalization:

1. raw owner bridge counts treated as historical truth without caveat,
2. family-level unstable citation ratios,
3. family-level blocking power contaminated by pending-family overinflation.

## 6.3 Portfolio findings

1. Portfolio issues are downstream consequences of family-layer serving problems.
2. Portfolio PIT is selective, not uniform:
   - classification PIT is real enough for serving with replay caveat,
   - compare PIT is valid with replay caveat,
   - current field and market overlays are not the same as true historical portfolio chronology.
3. Citation surfaces are available and should remain evidence-plus-summary rather than being compressed into a single synthetic score.
4. Portfolio citation chronology should come from dated event ledgers or PIT-safe family snapshot inputs, not from current-only overlays.
5. Portfolio citation mass concepts are valid, but they should remain explicitly labeled as aggregates or indices unless rebuilt into bounded serving metrics.

## 6.4 Portfolio refactor decisions

Keep as Gold serving lanes:

1. counts and ratios,
2. field/current overlay summaries,
3. classification PIT,
4. compare PIT,
5. forecast interval/risk outputs,
6. citation summary aggregates built from Silver evidence into Gold rollups where appropriate.

Rebuild upstream before re-promoting to executive:

1. average blocking power,
2. top-decile hit rate,
3. crown jewel index.

For portfolio citation specifically:

1. keep attacker drill-down and raw collision evidence tied to Silver ledgers,
2. formalize Gold portfolio citation summary marts for forward, backward/NPL, attacker momentum, field pressure, and jurisdiction pressure,
3. keep forecast citation outputs interval-first and support-scoped,
4. do not expose raw citation mass sums as if they were normalized portfolio quality scores.

---

## 7. Market Surface Audit

## 7.1 Market UI sections that need serving-safe outputs

Per the market contract, the page needs:

1. landscape ribbon,
2. segment league table,
3. state map,
4. momentum and breadth panel,
5. blocking and saturation panel,
6. owner presence overlays,
7. CPC within field trend,
8. CPC importance leaderboard.

## 7.2 Market data classes

Appropriate Gold-owned surfaces:

1. segment counts and state counts,
2. market segment league tables,
3. segment size and state maps,
4. PIT timeseries by WIPO field,
5. CPC trend PIT,
6. CPC importance PIT,
7. trend direction or state bands from Phase 06 contract.

Silver or family-derived inputs that should remain hidden behind Gold:

1. family-level raw blocking and citation features,
2. raw field fractions,
3. raw enforceability contribution sums,
4. current-overlay joins that are not actual PIT.

Citation-specific market rule:

Market citation representation should answer:

1. which fields are attracting more outside attention,
2. which jurisdictions are generating field pressure,
3. which citing owners are colliding inside a field,
4. how citation pressure changes over time.

For that reason:

1. field-level or market-level citation event slices stay in Silver,
2. market citation state, density, and trend outputs belong in Gold,
3. any market citation chronology shown in UI must be derived from dated citation events or as-of-safe snapshots.

## 7.3 Market findings

1. Market is already closer to the correct Gold-first serving pattern than portfolio.
2. The main risk is not raw Silver leakage; it is semantic overstatement:
   - current overlays shown as historical chronology,
   - importance indices read like certainty scores,
   - derived state labels presented without support metadata.
3. CPC trend and importance surfaces are appropriate Gold outputs, but they should stay explicitly indexed, ranked, and PIT-scoped rather than probability-framed.
4. Citation-derived market crowdedness or heat should be treated as an index or trend descriptor, not as exact market truth.

## 7.4 Market refactor decisions

Keep Gold-first:

1. segment-level state and trend outputs,
2. PIT market summaries,
3. CPC trend and importance ladders.

Add serving rules:

1. distinguish `current overlay` from `historical PIT`,
2. show scope and snapshot metadata on all market tabs,
3. label importance as rank/index, not truth probability,
4. ensure upstream family blocking corrections flow into market blocking-density views.

For market citation specifically:

1. keep raw field/jurisdiction citation evidence in Silver,
2. build Gold market citation summary or trend marts where UI needs compact leaderboard or heat-state outputs,
3. do not let raw citation lethality sums surface as market “scores” without normalization and labeling.

---

## 8. Citation Cross-Surface Audit

## 8.1 Family citation

Recommended serving split:

1. `SilverRawEvidence`
   - citation event ledger rows,
   - cleaned citation edges,
   - citing assignee/jurisdiction/date proof
2. `SilverAnalyticIntermediate`
   - weighted forward citation totals,
   - cohort-relative citation ratios,
   - raw citation lethality accumulations
3. `GoldServingMetric`
   - family citation summary cards,
   - heritage summary,
   - attacker leaderboard,
   - PIT-safe citation chronology
4. `GoldNeedsRebuild`
   - any family citation influence score that still reuses unstable cohort ratios without stage gating

## 8.2 Filing or publication citation

Recommended serving split:

1. `SilverRawEvidence`
   - document-level citing/cited rows,
   - dates,
   - assignees,
   - jurisdictions,
   - source provenance
2. `SilverAnalyticIntermediate`
   - document-level weighted citation features, if later added
3. `GoldServingMetric`
   - only if a dedicated publication-citation summary contract is introduced later
4. `GoldNeedsRebuild`
   - any document-level strategic score presented without a proper Gold contract

## 8.3 Portfolio citation

Recommended serving split:

1. `SilverRawEvidence`
   - drill-down attacker proof rows
2. `SilverAnalyticIntermediate`
   - owner-aggregated raw citation mass or lethality totals before normalization
3. `GoldServingMetric`
   - citation summary cards,
   - attacker leaderboards,
   - field/jurisdiction pressure summaries,
   - interval-first future citation outlook
4. `GoldNeedsRebuild`
   - any portfolio citation aggregate shown as a normalized score without explicit index semantics

## 8.4 Market citation

Recommended serving split:

1. `SilverRawEvidence`
   - field/jurisdiction citation event slices
2. `SilverAnalyticIntermediate`
   - raw crowdedness or lethality accumulations
3. `GoldServingMetric`
   - market citation heat summaries,
   - field citation trend views,
   - owner pressure leaderboards,
   - PIT-safe citation density trends
4. `GoldNeedsRebuild`
   - any market heat metric that is current-only but presented as PIT

---

## 9. Cross-Surface Refactor Matrix

## 9.1 What should remain in Silver

1. entity bridges and owner links,
2. publication and register evidence,
3. legal event histories,
4. citation event ledgers,
5. raw citation counts and raw weighted counts,
6. raw field membership facts,
7. raw coverage and jurisdiction facts,
8. model feature tables and cohort context fields.

## 9.2 What should move out of Silver-as-serving-truth

1. cohort-normalized citation scores used as if they were final UI strength scores,
2. raw enforceability contribution sums shown as final strategic metrics,
3. current-overlay field summaries shown as PIT chronology,
4. score-like proxies that are only fallback feature constructions,
5. any raw index that users would reasonably read as a bounded comparative score.

## 9.3 What must be rebuilt or formalized in Gold

1. family blocking power and family emerging influence split,
2. family trajectory and compare metrics,
3. portfolio executive metrics derived from corrected family Gold,
4. explicit Gold citation summary marts for family and portfolio UI,
5. clearer market overlay vs market PIT contracts,
6. support metadata and caveat flags attached to all model-backed UI surfaces.

---

## 10. Recommended Execution Order

1. formalize this boundary in the metric lineage catalog,
2. rebuild family blocking and citation-serving semantics first,
3. rebuild portfolio executive metrics from corrected family Gold,
4. add explicit Gold citation-summary marts for family and portfolio where UI needs compact summary cards,
5. keep publication evidence Silver-first,
6. relabel market overlays vs true PIT and verify CPC/market indices after upstream family corrections,
7. update backend-v2 repositories so each surface reads from the intended layer rather than whatever artifact is merely available.

The citation-specific implementation plan for this sequence is documented in [64-patentiq-v2-citation-serving-refactor-execution-plan.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/64-patentiq-v2-citation-serving-refactor-execution-plan.md).

---

## 11. Acceptance Criteria

The refactor is successful when:

1. no polished strategic UI card is backed directly by unstable Silver analytic intermediates,
2. evidence-first publication views remain fast and factual without needless Gold indirection,
3. family `pending_emerging` rows do not appear as top current blockers,
4. portfolio executive cards use only serving-safe counts, ratios, or rebuilt Gold indices,
5. market tabs distinguish present overlays from true chronology,
6. every UI-facing metric can be labeled as:
   - `SilverRawEvidence`,
   - `SilverAnalyticIntermediate`,
   - `GoldServingMetric`,
   - or `GoldNeedsRebuild`,
7. backend-v2 and frontend-v2 contracts can consume the outputs without extra per-page reinterpretation logic,
8. citation ledgers remain drill-down capable in Silver while citation scores, ranks, and trend summaries are promoted into explicit Gold serving contracts.

# PatentIQ V2 Metrics Generation Flow And Guardrails

## Purpose

Define the safest end-to-end metric-generation flow for PatentIQ V2 so that:

1. Bronze sources are loaded without semantic loss,
2. Silver metrics are generated in dependency-safe order,
3. Gold marts are produced only after upstream validations pass,
4. every step declares:
   - input tables,
   - output tables,
   - generated metrics,
   - core formulas,
   - sanity checks,
   - stop-conditions,
   - downstream blast radius if the step is wrong.

This document is the operational companion to:

1. [10-patentiq-v2-bronze-silver-gold-knowledge-tree.md](./10-patentiq-v2-bronze-silver-gold-knowledge-tree.md)
2. [11-patentiq-v2-metric-lineage-catalog.md](./11-patentiq-v2-metric-lineage-catalog.md)
3. [12-patentiq-v2-database-structure-and-metric-maps.md](./12-patentiq-v2-database-structure-and-metric-maps.md)
4. [13-patentiq-v2-cross-layer-dbdiagram.dbml](./13-patentiq-v2-cross-layer-dbdiagram.dbml)

## Execution Contract

The metric pipeline must follow these rules:

1. never skip a guardrail and continue downstream,
2. never recalculate a Gold metric directly from Bronze if a Silver dependency exists,
3. never mix patent citations and NPL citations in current blocking-power impact,
4. never calculate family metrics by averaging document-level outputs when the method requires collapse-first family logic,
5. never build point-in-time Gold marts from current-state-only inputs,
6. never build portfolio or compare views before family-level tables pass validation,
7. never treat the MVP portfolio universe as a universal patent estate when the warehouse is bounded to the mega-cluster,
8. never promote out-of-bounds citation families into full family analytics objects unless they are explicitly ingested,
9. every material table should expose:
   - `method_version`
   - `snapshot_date` or `snapshot_year` where relevant
   - `data_completeness_pct` when lag matters
   - row counts and validation summary in the ETL log.
10. PATSTAT Register may sharpen EP procedural truth, but it must remain a read-only legal power-up that does not alter cross-office blocking-power and portfolio percentile math.
11. USPTO full text and EPAB full text may enrich the semantic layer, but they must remain text providers only and must not overwrite globally harmonized PATSTAT or Register metadata for classifications, citations, parties, or legal truth.

## Stage 0: External Reference Staging

### Goal

Load and validate the non-PATSTAT reference inputs that later control normalization, weighting, and field mapping.

### Inputs

Tables:

1. `bronze_ext_iso_country_map`
2. `bronze_ext_world_bank_gdp_ppp`
3. `bronze_ext_us_chamber_ip_index`
4. `bronze_ext_up_member_states`
5. `bronze_ext_kind_code_normalization_seed`
6. `bronze_ext_oecd_indicator_seed`
7. `bronze_ref_country`
8. `bronze_ref_legal_event_code`
9. `bronze_ref_techn_field_ipc`
10. `bronze_ref_ipc_nace2`

### Outputs

No downstream analytical metrics yet. This stage only certifies reference readiness.

### Guardrails

1. ISO mapping must have no duplicate `iso2` keys.
2. GDP and IP index tables must have one row per jurisdiction-year.
3. `bronze_ext_up_member_states` must contain the exact active UP member-state set used by the chosen methodology version.
4. `bronze_ext_kind_code_normalization_seed` must contain office-aware mappings, not generic `B2` semantics.
5. `bronze_ref_techn_field_ipc` must resolve all intended WIPO 35 mapping codes.

### Stop Conditions

Stop if:

1. any `iso2` or `iso3` collisions are present,
2. key reference tables are empty,
3. kind-code seed is missing major offices used in scope,
4. WIPO concordance coverage is too low for the target mega-cluster.

### Downstream Failure Impact

If wrong here, the following become untrustworthy:

1. `silver_kind_code_normalization`
2. `silver_tiered_market_weighting`
3. `silver_family_wipo_fields`
4. `silver_family_enforceability_branches`
5. all blocking-power, coverage, field, and portfolio marts.

## Stage 1: Bronze PATSTAT Ingestion

### Goal

Land the raw PATSTAT tables with source fidelity.

### Inputs

1. `bronze_patstat_appln`
2. `bronze_patstat_appln_title`
3. `bronze_patstat_appln_abstr`
4. `bronze_patstat_appln_prior`
5. `bronze_patstat_person`
6. `bronze_patstat_pers_appln`
7. `bronze_patstat_appln_ipc`
8. `bronze_patstat_appln_cpc`
9. `bronze_patstat_pat_publn`
10. `bronze_patstat_citation`
11. `bronze_patstat_npl_publn`
12. `bronze_patstat_docdb_fam_citn`
13. `bronze_patstat_appln_techn_field`
14. `bronze_patstat_inpadoc_legal_event`

### Guardrails

1. no duplicate primary keys in ingested Bronze tables,
2. `bronze_patstat_appln.docdb_family_id` must be populated for the in-scope set,
3. `bronze_patstat_pat_publn.appln_id` must resolve back to `bronze_patstat_appln`,
4. `bronze_patstat_citation.pat_publn_id` must resolve to `bronze_patstat_pat_publn`,
5. `bronze_patstat_citation.cited_npl_publn_id` must not be dropped if present,
6. legal event dates must parse correctly,
7. no destructive filtering of dead, lapsed, abandoned, opposed, or out-of-scope-linked records.

### Stop Conditions

Stop if referential integrity failure exceeds threshold for:

1. application-publication linkage,
2. publication-citation linkage,
3. application-family linkage,
4. legal-event application linkage.

### Downstream Failure Impact

If wrong here, the entire warehouse is structurally compromised.

## Stage 1A: Bronze Full-Text Ingestion For Semantic Workflows

### Goal

Land the raw USPTO and EPAB full-text sources needed for representative family text selection without polluting the global metadata spine.

### Inputs

1. `bronze_uspto_ft_document`
2. `bronze_uspto_ft_biblio_application`
3. `bronze_uspto_ft_abstract`
4. `bronze_uspto_ft_claims`
5. `bronze_epab_document`
6. `bronze_epab_publication`
7. `bronze_epab_application`
8. `bronze_epab_abstract`
9. `bronze_epab_claims`

### Guardrails

1. every full-text row must preserve the source publication or application identifiers needed to bridge back to PATSTAT family members,
2. `A` and `B` kind codes must be parsed correctly because the semantic hierarchy depends on them,
3. claim sequence and language fields must be preserved exactly as delivered,
4. XML/JSON text must be landed losslessly in Bronze before later sanitization,
5. USPTO and EPAB classifications, citations, and party metadata must not be promoted into the global analytical spine from this ingestion path,
6. ingestion must remain source-faithful and should not pre-collapse families in Bronze.

### Stop Conditions

Stop if:

1. publication identifiers cannot be bridged back to PATSTAT family members at acceptable coverage,
2. kind-code parsing is unreliable,
3. claims or abstract payloads are truncated or malformed,
4. language or claim-order metadata is missing for a material share of EPAB records.

### Downstream Failure Impact

Wrong here corrupts:

1. `silver_family_text_representative`,
2. vector provenance,
3. claim-space semantic FTO workflows,
4. abstract-space whitespace maps.

## Stage 2: Family Anchor Construction

### Inputs

1. `bronze_patstat_appln`
2. `bronze_patstat_appln_prior`

### Build

Create:

1. `silver_family_core`

### Generated Metrics

1. `family_earliest_priority_date`
2. `family_priority_year`
3. `family_size_docdb`

### Core Logic

1. group by `docdb_family_id`,
2. resolve the earliest valid priority-linked filing date,
3. set `family_priority_year = EXTRACT(YEAR FROM family_earliest_priority_date)`,
4. carry `inpadoc_family_id` and family size fields.

### Guardrails

1. one row per `docdb_family_id`,
2. no null `family_earliest_priority_date` for in-scope families unless explicitly quarantined,
3. `family_priority_year` must equal the year portion of the anchor date,
4. family size must be non-negative and within plausible PATSTAT range.

### Stop Conditions

Stop if:

1. duplicate family rows are produced,
2. anchor dates drift materially from PATSTAT earliest filing fields,
3. family count collapses unexpectedly relative to Bronze.

### Downstream Failure Impact

Wrong here corrupts:

1. all cohort normalization,
2. trend anchors,
3. OECD cohort logic,
4. time-series filing metrics,
5. every family-level mart.

## Stage 3: Family Publication Bridge

### Inputs

1. `bronze_patstat_appln`
2. `bronze_patstat_pat_publn`

### Build

Create:

1. `silver_family_member_publications`

### Generated Metrics / Flags

1. `family_member_publication_count`
2. `is_application_stage`
3. `is_grant_stage`
4. `is_modifier_stage`

### Core Logic

1. join publications to applications,
2. inherit `docdb_family_id`,
3. keep jurisdiction and kind-code lineage intact,
4. classify lifecycle stage per publication.

### Guardrails

1. every row must resolve to one `docdb_family_id`,
2. publication-stage flags must be mutually coherent,
3. `C0` must remain visible as modifier-stage evidence,
4. no lifecycle documents may be deduplicated out at this stage.

### Downstream Failure Impact

Wrong here corrupts:

1. legal normalization,
2. representative text selection,
3. citation edge collapse,
4. UP detection,
5. family member detail pages.

## Stage 4: Assignee Harmonization

### Inputs

1. `bronze_patstat_person`
2. `bronze_patstat_pers_appln`

### Build

Create:

1. `silver_assignee_harmonized`

### Generated Metrics / Keys

1. `harmonized_owner_id`
2. `ultimate_parent_name`

### Core Logic

1. attach applicant/person records to applications,
2. normalize raw names,
3. collapse variants where defensible,
4. retain raw names for auditability.

### Guardrails

1. raw and normalized names must both be preserved,
2. harmonization must be versioned,
3. high-confidence parent rollup must be separable from weak heuristics,
4. no many-to-many explosion per application without explicit ownership-share logic.

### Downstream Failure Impact

Wrong here corrupts:

1. self-citation scrubbing,
2. portfolio rollups,
3. attacker leaderboards,
4. compare surfaces,
5. client overlay joins by owner.

## Stage 5: Kind-Code Normalization

### Inputs

1. `silver_family_member_publications`
2. `bronze_ext_kind_code_normalization_seed`

### Build

Create:

1. `silver_kind_code_normalization`

### Generated Metrics

1. `branch_universal_stage`
2. `branch_stage_multiplier`
3. `is_enforceable`
4. `legal_status_proxy`

### Core Logic

1. map `jurisdiction_code + kind_code` to office-aware universal stage,
2. preserve special handling for:
   - EP `B2`
   - EP `C0`
   - US `B1/B2`
3. expose enforceability and modifier semantics.

### Guardrails

1. never interpret `B2` generically across offices,
2. `C0` must be treated as UP registration logic, not a new invention,
3. pending-stage and grant-stage classifications must be mutually exclusive,
4. all in-scope offices must resolve to a stage or be quarantined.

### Downstream Failure Impact

Wrong here corrupts:

1. legal event interpretation,
2. blocking-power branch math,
3. opposition signals,
4. representative text hierarchy,
5. enforceable-only filters.

## Stage 6: Tiered Market Weighting

### Inputs

1. `bronze_ext_world_bank_gdp_ppp`
2. `bronze_ext_us_chamber_ip_index`
3. `bronze_ext_iso_country_map`

### Build

Create:

1. `silver_tiered_market_weighting`

### Generated Metrics

1. `gdp_tier_weight`
2. `ip_score`
3. `final_market_multiplier`

### Core Logic

Apply the agreed multiplier formula:

`final_market_multiplier = gdp_tier_weight * (ip_score / 100.0)`

using default penalties where the methodology requires them.

### Guardrails

1. no duplicate jurisdiction-year rows,
2. every in-scope jurisdiction must resolve to a market multiplier or explicit fallback,
3. the multiplier distribution must be reviewed for outliers,
4. UP member states must still be weighted individually after unrolling.

### Downstream Failure Impact

Wrong here corrupts:

1. weighted reach,
2. branch enforceability,
3. market threat,
4. local citation lethality,
5. jurisdiction rankings.

## Stage 7: UP Detection And Jurisdiction Unrolling

### Inputs

1. `silver_family_member_publications`
2. `bronze_patstat_inpadoc_legal_event`
3. `bronze_ext_up_member_states`

### Build

Create:

1. `silver_up_status`
2. `silver_family_jurisdiction_unrolled`

### Generated Metrics

1. `has_up_registration`
2. `up_member_state_count`
3. jurisdiction set after UP expansion

### Core Logic

1. detect UP via `C0` or qualifying legal event,
2. expand UP to participating member states,
3. keep classic validations and non-UP jurisdictions,
4. deduplicate the final jurisdiction set.

### Guardrails

1. UP expansion must not inflate filing counts,
2. UP expansion must happen before breadth and coverage calculations,
3. no duplicate jurisdiction entries after expansion,
4. UK, ES, CH and other non-UP validations must remain independent where present.

### Downstream Failure Impact

Wrong here corrupts:

1. raw breadth,
2. weighted reach,
3. active coverage,
4. coverage stability,
5. blocking-power geography and UPC risk interpretation.

## Stage 8: Legal Event Ledger

### Inputs

1. `bronze_patstat_inpadoc_legal_event`
2. `silver_kind_code_normalization`
3. `silver_family_member_publications`
4. `silver_up_status`

### Build

Create:

1. `silver_legal_status_event_ledger`

### Generated Metrics / Flags

1. `is_grant_event`
2. `is_lapse_event`
3. `is_opposition_event`
4. `is_expiry_event`
5. `is_up_event`

### Core Logic

1. normalize event semantics by office,
2. attach events to family and jurisdiction,
3. preserve the full ledger by date,
4. retain catastrophic `UP/UPC` style single-point risk markers.

### Guardrails

1. never overwrite event history with one final status,
2. event dates must remain monotonic per branch where required,
3. negative-state transitions must not delete prior active history,
4. opposition and survival logic must remain reconstructible.

### Downstream Failure Impact

Wrong here corrupts:

1. point-in-time state,
2. family composite status,
3. coverage stability,
4. blocking-power time series,
5. lapse and friction forecasts.

## Stage 8A: PATSTAT Register EP Overlay

### Goal

Load and resolve EP-only PATSTAT Register overlays for publication evidence, family badges, and the isolated EP-special grant model.

### Inputs

1. `bronze_reg101_appln`
2. `bronze_reg107_parties`
3. `bronze_reg111_licensee`
4. `bronze_reg125_appeal`
5. `bronze_reg130_opponent`
6. `bronze_reg201_proc_step`
7. `bronze_reg202_proc_step_text`
8. `bronze_reg203_proc_step_date`
9. `bronze_reg301_event_data`
10. `bronze_reg402_event_text`
11. `bronze_reg701_appln`
12. `bronze_reg731_event_data`
13. `bronze_reg741_appln_status`
14. `bronze_reg742_event_text`
15. `bronze_patstat_appln`
16. `silver_family_member_publications`
17. `silver_legal_status_event_ledger`

### Build

Create:

1. `silver_ep_register_core`
2. `silver_ep_register_agent_summary`
3. `silver_ep_register_current_opposition`
4. `silver_ep_register_up_status`
5. `silver_ep_register_proc_step_features`
6. `silver_ep_register_display_ledger`

### Generated Metrics

1. `register_record_present`
2. `ep_register_lead_agent_name`
3. `ep_opposition_active`
4. `ep_opponent_names`
5. `ep_appeal_active`
6. `ep_register_is_unitary_patent`
7. `ep_proc_step_maturity_score`
8. `ep_display_status_text`
9. `status_source`
10. `status_source_priority`
11. `register_override_flag`

### Core Logic

1. join PATSTAT Global to Register by `appln_id`,
2. restrict the join to the EP procedural universe,
3. extract agent data from `reg107_parties where type = 'AGENT'`,
4. extract opposition state and names from latest or current `reg130_opponent` rows,
5. extract appeal state from `reg125_appeal`,
6. extract UP truth from `reg701` / `reg731` / `reg741`,
7. extract procedural-step features from `reg201` / `reg202` / `reg203` / `reg301`,
8. resolve EP detail-display status using Register-over-INPADOC source priority where applicable.

### Guardrails

1. Register joins must never apply to non-EP applications.
2. Register-derived fields must not feed `silver_family_enforceability_branches`.
3. Register-derived fields must not directly alter `gold_family_blocking_power`.
4. Register-derived fields must not directly alter `gold_portfolio_summary`.
5. The canonical family state must remain separate from EP member procedural state.
6. MVP opposition extraction should use current or final state and `IS_LATEST` patterns rather than full chronology replay.
7. Any EP detail-status override must preserve provenance through `status_source` metadata.

### Stop Conditions

Stop if:

1. `appln_id` linkage between PATSTAT Global and Register is materially incomplete for EP applications,
2. Register-derived status silently changes global family labels,
3. Register features appear in blocking-power branch tables,
4. opposition extraction requires unsupported chronology reconstruction to complete MVP outputs.

### Downstream Failure Impact

Wrong here corrupts:

1. EP publication evidence views,
2. family-level EP procedural badges,
3. UP detail interpretation,
4. the isolated EP-special grant model,
5. trust in legal-status provenance.

## Stage 9: Point-In-Time Family Status

### Inputs

1. `silver_legal_status_event_ledger`
2. `silver_family_jurisdiction_unrolled`

### Build

Create:

1. `silver_family_status_pt`

### Generated Metrics

1. `family_composite_status`
2. `active_jurisdiction_count`
3. `active_grant_branch_count`
4. `lapsed_jurisdiction_count`
5. `opposed_branch_count`
6. `has_any_active_grant`
7. `is_dead_family`

### Core Logic

1. reconstruct the state at each `snapshot_date`,
2. classify family as:
   - `fully_active`
   - `pending_emerging`
   - `under_fire`
   - `partially_lapsed`
   - `dead`

### Guardrails

1. snapshot reconstruction must be deterministic,
2. a family cannot be both `dead` and `has_any_active_grant = true`,
3. current-state queries and historical queries must use the same ledger source,
4. snapshot row counts must align with family coverage expectations.

### Downstream Failure Impact

Wrong here corrupts:

1. all current-vs-historical separations,
2. current blocking-power gating,
3. current weighted reach,
4. current competitor leaderboards,
5. legal risk interpretations.

## Stage 10: Technical Code Canonicalization

### Inputs

1. `bronze_patstat_appln_ipc`
2. `bronze_patstat_appln_cpc`

### Build

Create:

1. `silver_family_ipc_cpc_canonical`

### Generated Metrics / Structures

1. canonical IPC-compatible code set per family

### Core Logic

1. collect all IPC/CPC from all family members,
2. truncate CPC to IPC-compatible structure,
3. merge IPC and canonicalized CPC,
4. deduplicate at technical-code level.

### Guardrails

1. no raw CPC-only branching into competing taxonomies,
2. duplicated cross-jurisdiction codes must collapse,
3. source counts should be preserved for audit,
4. code canonicalization must be stable across reruns.

### Downstream Failure Impact

Wrong here corrupts:

1. WIPO field mapping,
2. tech breadth,
3. field fractions,
4. trend coefficients,
5. field-level blocking-power slices,
6. OECD field-diversity metrics.

## Stage 11: WIPO Field Mapping

### Inputs

1. `silver_family_ipc_cpc_canonical`
2. `bronze_ref_techn_field_ipc`

### Build

Create:

1. `silver_family_wipo_fields`

### Generated Metrics

1. `family_tech_breadth_wipo_count`
2. `family_field_fraction`
3. `wipo_field`

### Core Logic

1. map canonical IPC-compatible codes to WIPO fields,
2. deduplicate again at WIPO field level,
3. count unique fields,
4. set `family_field_fraction = 1 / family_tech_breadth_wipo_count`.

### Guardrails

1. no family may have `family_field_fraction` values that sum materially above 1.0 within the same method version,
2. if WIPO mapping fails for a code, quarantine it and report coverage,
3. primary and fractional views must remain derivable from the same base table.

### Downstream Failure Impact

Wrong here corrupts:

1. field leaderboards,
2. field trends,
3. field-level blocking power,
4. OECD generality/originality,
5. compare views,
6. semantic whitespace overlays.

## Stage 12: Patent Citation Graph Construction

### Inputs

1. `bronze_patstat_citation`
2. `bronze_patstat_docdb_fam_citn`
3. `silver_family_member_publications`

### Build

Create:

1. `silver_family_citation_edges`

### Generated Structures

1. patent-family citation edges

### Core Logic

1. map citing publications to citing families,
2. map cited documents/applications to cited families,
3. preserve citing date, office, and kind-code context,
4. keep this graph patent-only.

### Guardrails

1. NPL references must not enter `silver_family_citation_edges`,
2. duplicate family-family edges from multiple document members must remain reconstructible until the clean step,
3. cited families outside the extracted mega-cluster must remain representable as ghost-node/out-of-bounds references where required.

### Downstream Failure Impact

Wrong here corrupts:

1. citation impact,
2. RCF,
3. attacker leaderboard,
4. friction forecast,
5. heritage and OECD downstream metrics.

## Stage 13: NPL Backlink Construction

### Inputs

1. `bronze_patstat_citation`
2. `bronze_patstat_npl_publn`
3. `silver_family_member_publications`

### Build

Create:

1. `silver_family_npl_backlinks`

### Generated Metrics / Structures

1. family-to-NPL backlink registry
2. `npl_citation_count`
3. `science_linkage_flag`

### Core Logic

1. collapse citing publications to canonical family,
2. keep `cited_npl_publn_id` distinct from patent citations,
3. aggregate to family-level NPL backlink counts.

### Guardrails

1. never convert NPL into fake patent-family nodes,
2. NPL rows must remain separate from blocking-power citation tables,
3. bibliography identifiers must remain traceable.

### Downstream Failure Impact

Wrong here corrupts:

1. science-grounding,
2. OECD overlays,
3. quality descriptors,
4. any NPL-aware diagnostics.

## Stage 14: Patent Citation Cleaning

### Inputs

1. `silver_family_citation_edges`
2. `silver_assignee_harmonized`

### Build

Create:

1. `silver_family_citation_edges_clean`

### Generated Flags / Metrics

1. `is_self_citation`
2. `is_intra_family_citation`
3. `is_out_of_bounds`
4. `clean_edge_weight`

### Core Logic

1. flag and remove intra-family citation noise,
2. flag and remove self-citations by default,
3. preserve out-of-bounds edge identity for ghost-node math.

### Guardrails

1. self-citation scrubbing must be toggleable but default-on for impact scoring,
2. ghost-node edges must not disappear from heritage/OECD computations if required,
3. cleaned edge counts must never exceed raw edge counts.

### Downstream Failure Impact

Wrong here corrupts:

1. adjusted citation impact,
2. attacker ranking,
3. blocking-power fusion,
4. OECD field-distribution logic,
5. friction forecast features.

## Stage 15: Citation Metric Generation

### Inputs

1. `silver_family_citation_edges_clean`
2. `silver_family_npl_backlinks`
3. `silver_family_core`
4. `silver_family_wipo_fields`

### Build

Create:

1. `silver_family_citation_metrics`

### Generated Metrics

1. `family_forward_citations_raw`
2. `family_forward_citations_clean`
3. `family_forward_citations_weighted`
4. `family_backward_citations_clean`
5. `family_backward_npl_citation_count`
6. `family_rcf_score`
7. `family_fwd_cits5`
8. `family_fwd_cits7`
9. `family_science_grounding_score`

### Core Logic

1. count clean forward and backward patent-family citations,
2. weight forward patent citations using citing-side lethality context where enabled,
3. compute `family_rcf_score` against the cohort average,
4. compute fixed-window citation windows,
5. compute separate NPL count and science-grounding score from `silver_family_npl_backlinks`.

### Guardrails

1. `family_adjusted_citation_score_raw` must only depend on patent-family forward citations,
2. backward NPL must never be blended into blocking-power impact,
3. cohort sample sizes must be checked before publishing `family_rcf_score`,
4. fixed-window metrics must respect observation windows.

### Downstream Failure Impact

Wrong here corrupts:

1. blocking-power fusion,
2. heritage interpretation,
3. forecast features,
4. hidden-gems screens,
5. current-vs-historical citation views.

## Stage 16: Enriched Citation Network

### Inputs

1. `silver_family_citation_edges_clean`
2. `silver_assignee_harmonized`
3. `silver_kind_code_normalization`
4. `silver_tiered_market_weighting`
5. trend tables

### Build

Create:

1. `silver_enriched_citation_network`

### Generated Metrics

1. `citation_lethality_score`
2. `citing_assignee_name`
3. `citing_jurisdiction_code`

### Core Logic

1. enrich each clean patent citation edge with citing-side assignee, stage, market, and trend context,
2. produce the event-level threat network used by leaderboards and friction logic.

### Guardrails

1. event dates must remain citation-publication dates,
2. citing-side stage and market weights must resolve cleanly,
3. no edge may exist without both citing and cited family ids unless explicitly ghosted.

### Downstream Failure Impact

Wrong here corrupts:

1. attacker leaderboard,
2. threat network,
3. friction forecast,
4. weighted citation impact if derived from enriched edges.

## Stage 17: Trend Engine Generation

### Inputs

1. `silver_family_core`
2. `silver_family_wipo_fields`
3. `silver_family_jurisdiction_unrolled`

### Build

Create:

1. `silver_global_tech_trends_timeseries`
2. `silver_local_tech_trends_timeseries`

### Generated Metrics

1. `global_field_trend_coefficient`
2. `local_field_trend_coefficient`

### Core Logic

1. global counts by `snapshot_year x wipo_field`,
2. local counts by `snapshot_year x jurisdiction_code x wipo_field`,
3. compute YoY growth coefficients,
4. enforce point-in-time publication-lag caveats.

### Guardrails

1. family count basis must use family anchors, not publication counts,
2. `C0` must not create fake filing spikes,
3. trend coefficients must not divide by zero silently,
4. localized coefficients must fall back explicitly when coverage is insufficient.

### Downstream Failure Impact

Wrong here corrupts:

1. enforceability branches,
2. field competitiveness,
3. hotspot maps,
4. trend forecasts,
5. localized blocking-power valuation.

## Stage 18: Coverage Metric Generation

### Inputs

1. `silver_family_jurisdiction_unrolled`
2. `silver_family_status_pt`
3. `silver_tiered_market_weighting`

### Build

Create:

1. `silver_family_coverage_metrics`

### Generated Metrics

1. `family_raw_breadth_jurisdiction_count`
2. `family_active_breadth_jurisdiction_count`
3. `family_weighted_market_reach_score`
4. `family_coverage_stability_score`

### Core Logic

1. count distinct jurisdictions after UP expansion,
2. restrict active views using point-in-time status,
3. compute weighted reach from active jurisdiction weights,
4. compute stability as a durability proxy over the active branch set.

### Guardrails

1. raw breadth and weighted reach must remain separate,
2. current-state coverage must not include dead branches,
3. coverage stability must not be treated as direct blocking-power impact.

### Downstream Failure Impact

Wrong here corrupts:

1. family summary cards,
2. coverage risk views,
3. blocking-power diagnostics,
4. portfolio reach comparisons.

## Stage 19: Branch Enforceability Generation

### Inputs

1. `silver_family_status_pt`
2. `silver_kind_code_normalization`
3. `silver_tiered_market_weighting`
4. `silver_family_wipo_fields`
5. `silver_local_tech_trends_timeseries`

### Build

Create:

1. `silver_family_enforceability_branches`

### Generated Metrics

1. `branch_enforceability_contribution_raw`
2. `branch_coefficient_mode`

### Core Logic

For each `family x snapshot x jurisdiction x field` branch:

`branch_enforceability_contribution_raw = branch_stage_multiplier * final_market_multiplier * family_field_fraction * local_field_trend_coefficient * active_branch_flag`

### Guardrails

1. no branch contribution for inactive/dead branches in current-state views,
2. field fractions must sum coherently within family,
3. fallback trend mode must be labeled as:
   - `localized`
   - `global_fallback`
   - `mixed`
4. office-specific stage semantics must already be normalized before this step.

### Downstream Failure Impact

Wrong here corrupts:

1. `family_market_threat_score_raw`
2. `family_overall_legal_enforceability_score`
3. jurisdiction contributions,
4. field contributions,
5. current threat leaderboards,
6. blocking-power time series.

## Stage 20: OECD / Nature-Of-Innovation Metric Generation

### Inputs

1. `silver_family_citation_edges_clean`
2. `silver_family_npl_backlinks`
3. `silver_family_wipo_fields`
4. `silver_family_core`
5. `bronze_ext_oecd_indicator_seed` where used

### Build

Create:

1. `silver_family_oecd_quality`

### Generated Metrics

1. `family_generality_score`
2. `family_originality_score`
3. `family_radicalness_score`
4. `family_backward_npl_citation_count`
5. `family_science_grounding_score`
6. `oecd_quality_percentile`

### Core Logic

1. compute generality from forward-citing field diversity,
2. compute originality from backward patent-family field diversity,
3. compute radicalness from outside-field dependence,
4. carry NPL metrics separately as science-grounding rather than blocking-power impact.

### Guardrails

1. collapse-first family citation pooling is mandatory,
2. do not average patent-level OECD metrics up to family,
3. any blended patent-plus-NPL originality variant must be explicitly labeled,
4. cohort normalization must use `family_priority_year + technology field`.

### Downstream Failure Impact

Wrong here corrupts:

1. heritage views,
2. quality tags,
3. compare screens,
4. hit-rate rollups,
5. hidden-gems quality filters,
6. forecast features using OECD metrics.

## Stage 20A: Representative Family Text Generation

### Inputs

1. `silver_family_member_publications`
2. `silver_kind_code_normalization`
3. `silver_family_core`
4. `bronze_uspto_ft_claims`
5. `bronze_uspto_ft_abstract`
6. `bronze_epab_claims`
7. `bronze_epab_abstract`
8. `bronze_patstat_appln_abstr`

### Build

Create:

1. `silver_family_text_representative`

### Generated Metrics

1. `representative_appln_id`
2. `representative_publn_id`
3. `representative_stage`
4. `representative_claim_1_en`
5. `representative_abstract_en`
6. `text_provenance`
7. `is_abstract_fallback`

### Core Logic

Apply the deterministic text hierarchy:

1. U.S. granted `B` Claim 1 from USPTO full text,
2. else English EP granted `B` Claim 1 from EPAB,
3. else English abstract fallback from PATSTAT `tls203_appln_abstr`.

During selection and extraction:

1. reject `A`-document claims for FTO or infringement-oriented claim-space embeddings,
2. extract Claim 1 only for MVP,
3. sanitize XML/HTML tags, line breaks, and inline reference numerals where safe,
4. preserve provenance and fallback reason.

### Guardrails

1. exactly one representative text selection per `docdb_family_id`,
2. claim-space selection must never silently fall back from `B` claims to `A` claims,
3. abstract fallback must set `is_abstract_fallback = TRUE`,
4. provenance must identify the exact text source such as `USPTO_US...B2`, `EPAB_EP...B1`, or `PATSTAT_ABSTRACT`,
5. text sanitization must be deterministic and versioned.

### Stop Conditions

Stop if:

1. multiple text candidates tie without deterministic resolution,
2. claim-order parsing is unreliable for USPTO or EPAB,
3. abstract fallback rate is too high for the intended claim-space MVP workflows.

### Downstream Failure Impact

Wrong here corrupts:

1. `vec_family_embeddings`,
2. semantic FTO,
3. semantic prior-art search,
4. semantic comparison rollups,
5. whitespace and collision mapping.

## Stage 20B: Vector Payload Enrichment

### Inputs

1. `silver_family_text_representative`
2. `silver_family_core`
3. `silver_family_wipo_fields`
4. `gold_family_blocking_power`

### Build

Populate:

1. `vec_family_embeddings`
2. `gold_semantic_match_context`

### Generated Metrics

1. `earliest_priority_timestamp`
2. `wipo_field`
3. `overall_bp_percentile`
4. `text_provenance`
5. `is_abstract_fallback`

### Core Logic

1. attach chronology anchor from `silver_family_core`,
2. attach field context from `silver_family_wipo_fields`,
3. attach `overall_bp_percentile` only for abstract-space whitespace overlays and post-retrieval context,
4. keep `vector_claims` and `vector_abstract` as separate payload spaces.

### Guardrails

1. `overall_bp_percentile` must not influence the embedding itself,
2. `vector_claims` payloads must originate from granted U.S. or EP Claim 1 text unless clearly marked as abstract fallback,
3. `vector_abstract` payloads may use abstract fallback globally,
4. chronology fields must remain joinable before any prior-art or infringement-style labeling.

### Stop Conditions

Stop if:

1. vector payloads cannot be joined back to family-level chronology and legal context,
2. blocking-power context is being injected into embedding generation rather than post-retrieval display,
3. claim and abstract spaces are being blended into one opaque registry.

### Downstream Failure Impact

Wrong here corrupts:

1. semantic search payload integrity,
2. chronology gating,
3. whitespace map color-coding,
4. semantic compare explainability.

## Stage 21: Predictive Silver Generation

### Inputs

1. `silver_family_citation_metrics`
2. `silver_family_oecd_quality`
3. `silver_family_status_pt`
4. `silver_family_enforceability_branches`
5. `silver_legal_status_event_ledger`
6. trend tables
7. `silver_ep_register_proc_step_features` for the isolated EP-special grant model only

### Build

Create:

1. `silver_grant_probability_forecast`
2. `silver_lapse_risk_forecast`
3. `silver_friction_risk_forecast`
4. `silver_ep_grant_probability_forecast`

### Generated Metrics

1. `grant_probability_pct`
2. `lapse_risk_pct`
3. `friction_risk_pct`
4. `grant_probability_pct` from the EP-special model for eligible EP applications

### Guardrails

1. all forecasts must run at native micro-grain before portfolio aggregation,
2. probabilities must be calibrated,
3. no leakage from post-outcome features,
4. forecast tables must remain clearly separate from descriptive truth tables,
5. Register-derived features must remain isolated inside the EP-special grant model,
6. EP-special outputs must not alter blocking-power or portfolio percentile marts.

### Downstream Failure Impact

Wrong here corrupts:

1. family forecast cards,
2. portfolio forecast rollups,
3. risk queues,
4. contest demo claims about predictive reliability.

## Stage 22: Gold Family Summary

### Inputs

1. `silver_family_core`
2. `silver_assignee_harmonized`
3. `silver_family_status_pt`
4. `silver_family_coverage_metrics`
5. `silver_family_wipo_fields`
6. `silver_family_oecd_quality`

### Build

Create:

1. `gold_family_summary`

### Guardrails

1. Gold summary must not recompute Silver logic,
2. current vs historical labels must be explicit,
3. scope labels must remain visible.

### Downstream Failure Impact

Wrong here corrupts the entire family page and all compare/search summaries.

## Stage 23: Gold Blocking Power

### Inputs

1. `silver_family_enforceability_branches`
2. `silver_family_citation_metrics`

### Build

Create:

1. `gold_family_blocking_power`

### Generated Metrics

1. `family_market_threat_score_raw`
2. `family_adjusted_citation_score_raw`
3. `family_raw_absolute_blocking_power`
4. `family_ui_blocking_power_score`
5. `family_overall_legal_enforceability_score`

### Core Logic

1. sum branch contributions to get `family_market_threat_score_raw`,
2. derive `family_adjusted_citation_score_raw` from adjusted patent-family forward influence,
3. fuse:

`family_raw_absolute_blocking_power = (w_market * family_market_threat_score_raw) + (w_citation * family_adjusted_citation_score_raw)`

4. percentile-rank within the valid cohort for `family_ui_blocking_power_score`.

### Guardrails

1. citation side must remain patent-family only,
2. `family_ui_blocking_power_score` must never be min-max scaled,
3. raw and normalized scores must both be retained,
4. `family_overall_legal_enforceability_score` and `family_adjusted_citation_score_raw` must be exposed as separate components,
5. NPL must not enter this fusion.

### Downstream Failure Impact

Wrong here corrupts:

1. family blocking-power tab,
2. crown-jewel ranking,
3. competitor leaderboards,
4. pruning logic,
5. financial overlays tied to blocking power.

## Stage 24: Gold Blocking Power Time Series

### Inputs

1. `gold_family_blocking_power`
2. `silver_legal_status_event_ledger`
3. branch history and citation history

### Build

Create:

1. `gold_family_blocking_power_timeseries`

### Guardrails

1. score must rebuild from time-appropriate state rather than current state replay,
2. event markers must align with score movements,
3. expiry must force enforceability to zero at end-of-life.

### Downstream Failure Impact

Wrong here corrupts:

1. point-in-time analysis,
2. lifecycle visuals,
3. strategic-retreat and patent-cliff narratives.

## Stage 25: Gold Family Field Contributions

### Inputs

1. `silver_family_enforceability_branches`
2. `silver_family_citation_metrics`
3. `silver_family_wipo_fields`

### Build

Create:

1. `gold_family_field_contributions_timeseries`

### Generated Metrics

1. `family_field_enforceability_contribution_score`
2. `family_field_heritage_contribution_score`

### Guardrails

1. field contributions must be generated field-first, not split from a generic total after the fact,
2. current enforceability and heritage must remain separate,
3. field fractions must remain stable within family snapshots.

### Downstream Failure Impact

Wrong here corrupts:

1. field decomposition of blocking power,
2. competitor field rankings,
3. WIPO field heatmaps,
4. compare views.

## Stage 26: Gold Attacker Summary

### Inputs

1. `silver_enriched_citation_network`

### Build

Create:

1. `gold_family_attacker_summary`

### Guardrails

1. rank by citation lethality as well as count,
2. preserve drill-down to event-level proof,
3. snapshot filters must apply before aggregation.

### Downstream Failure Impact

Wrong here corrupts:

1. threat network,
2. attacker leaderboard,
3. friction interpretation.

## Stage 27: Gold Portfolio Marts

### Inputs

1. `gold_family_blocking_power`
2. `gold_family_field_contributions_timeseries`
3. `silver_family_oecd_quality`
4. `silver_assignee_harmonized`
5. `silver_enriched_citation_network`

### Build

Create:

1. `gold_portfolio_field_timeseries`
2. `gold_portfolio_summary`
3. `gold_portfolio_threat_matrix`

### Generated Metrics

1. `portfolio_field_enforceability_score`
2. `portfolio_field_heritage_score`
3. `portfolio_total_mass_score`
4. `portfolio_hit_rate_top_decile`
5. `portfolio_crown_jewel_index`
6. `portfolio_opposition_rate`

### Guardrails

1. all portfolio metrics must aggregate from family-level truth,
2. denominators must remain in-scope to the mega-cluster,
3. portfolio hit rates must never use universal unseen portfolio size,
4. threat matrix must remain time-slice aware.

### Downstream Failure Impact

Wrong here corrupts:

1. portfolio page,
2. compare page,
3. executive dashboard,
4. crown-jewel and hit-rate narratives.

## Stage 28: Gold Forecast Summaries

### Inputs

1. predictive Silver tables
2. family and portfolio identity tables

### Build

Create:

1. `gold_family_forecast_summary`
2. `gold_portfolio_forecast_summary`

### Guardrails

1. forecast rollups must remain drillable to native prediction grain,
2. forecast tables must be clearly labeled as forecasts, not current-state truth,
3. probabilities and counts must carry model version and as-of date.

### Downstream Failure Impact

Wrong here corrupts:

1. pending threat workflows,
2. lapse-risk views,
3. demo credibility for predictive features.

## Stage 29: Gold Semantic Match Context

### Inputs

1. vector sidecar outputs
2. `gold_family_summary`
3. `gold_family_blocking_power`
4. `silver_family_status_pt`

### Build

Create:

1. `gold_semantic_match_context`

### Guardrails

1. semantic search remains candidate generation only,
2. chronology gating must be applied before legal interpretation,
3. only representative family text should drive family-level retrieval.

### Downstream Failure Impact

Wrong here corrupts:

1. semantic FTO,
2. whitespace mapping,
3. semantic threat surfaces.

## Final Release Gate

The metric pipeline is only release-ready when the following all pass:

1. Bronze row-count and PK/FK audits,
2. family count parity against expected in-scope family universe,
3. kind-code coverage audit by office,
4. WIPO field coverage audit,
5. patent citation vs NPL separation audit,
6. UP unrolling audit,
7. point-in-time reconstruction audit,
8. blocking-power recomputation parity on a gold fixture set,
9. portfolio rollup parity on a gold fixture set,
10. forecast calibration checks,
11. semantic chronology checks.

## Minimal Build Order Summary

If the team needs the shortest safe execution order, use this:

1. Stage 0-1: references and Bronze ingestion
2. Stage 2-5: family, publication, assignee, and kind-code foundations
3. Stage 6-9: market weighting, UP logic, legal ledger, point-in-time status
4. Stage 10-11: technical canonicalization and WIPO mapping
5. Stage 12-16: patent citations, NPL backlinks, cleaned citation metrics, enriched network
6. Stage 17-20: trends, coverage, branch enforceability, OECD quality
7. Stage 21-29: forecasts, family Gold marts, portfolio Gold marts, semantic context

No Gold metric should be published unless every upstream guardrail for the metrics it consumes has passed.

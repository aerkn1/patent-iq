# PatentIQ V2 Bronze / Silver / Gold Knowledge Tree

## Purpose

Define the concrete PatentIQ V2 data architecture using:

1. PATSTAT source tables from [patstat-schema.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/data/patstat-schema.md)
2. current DuckDB catalog objects from [database-schema-v1.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/data/database-schema/database-schema-v1.md)
3. metric and methodology requirements from `docs/new-feature-ideas`

This document fixes the naming of:

1. Bronze source tables
2. Silver normalized entities and reusable feature tables
3. Gold product marts and scores

It also states which current v1 views can seed or partially backfill the V2 build.

## Layer Rules

Scope rule:
- the V2 MVP warehouse should be interpreted as a `mega-cluster-bounded` analytics environment rather than a universal global patent estate
- `silver_family_core` is therefore the canonical mega-cluster family universe with explicit horizon flags
- owner and portfolio rollups should aggregate only over that in-scope family universe unless explicitly labeled otherwise
- out-of-bounds citation families may persist as ghost-node stubs for network math without becoming full family objects
- PATSTAT Register, when present, is an EP-only legal power-up and must not alter cross-office family blocking-power or portfolio percentile math

`Bronze`
- raw truth
- source-preserving
- office-specific semantics not yet normalized
- no destructive filtering of dead / lapsed / abandoned records

`Silver`
- family-first normalization
- reusable, method-level analytical tables
- legal, citation, field, ownership, and trend logic lives here
- no UI-only percentile presentation logic unless the result is explicitly a reusable feature

`Gold`
- product-facing marts
- point-in-time summaries
- rankings
- rollups
- time-series surfaces
- explainable score outputs used directly by API and UI

## Naming Convention

Recommended prefixes:

- `bronze_patstat_*` for raw PATSTAT-derived tables
- `bronze_ext_*` for external economic, legal, or taxonomy reference inputs
- `silver_*` for normalized entities and reusable metric tables
- `gold_*` for product marts
- `vec_*` for vector / embedding registries
- `ml_*` for offline model artifacts

## Bronze Layer

## A. Core PATSTAT Bronze

### `bronze_patstat_appln`

Primary source:
- `tls201_appln`

Core columns consumed:
- `appln_id`
- `appln_auth`
- `appln_kind`
- `appln_filing_date`
- `appln_filing_year`
- `earliest_filing_date`
- `earliest_filing_year`
- `earliest_publn_date`
- `granted`
- `docdb_family_id`
- `inpadoc_family_id`
- `docdb_family_size`
- `nb_citing_docdb_fam`
- `nb_applicants`
- `nb_inventors`

Current v1 nearest sources:
- `main.patent_core`
- `main.patent_family_enriched`
- `main.ml_training_table`

### `bronze_patstat_appln_title`

Primary source:
- `tls202_appln_title`

Use:
- representative English family title selection
- semantic abstract/title retrieval

### `bronze_patstat_appln_abstr`

Primary source:
- `tls203_appln_abstr`

Use:
- semantic abstract embedding
- descriptive family summaries

## A1. Semantic Full-Text Bronze

These tables are text providers for the semantic layer. They must not replace PATSTAT and Register as the harmonized source of classifications, citations, parties, or legal-state metadata.

### `bronze_uspto_ft_document`
### `bronze_uspto_ft_biblio_application`
### `bronze_uspto_ft_abstract`
### `bronze_uspto_ft_claims`

Primary sources:
- USPTO full-text XML

Use:
- U.S. publication identity
- sanitized English abstract extraction
- sanitized Claim 1 extraction for granted U.S. `B` documents

Constraint:
- do not reuse USPTO full-text classifications, party tables, or citation metadata in the semantic pipeline because PATSTAT already owns those normalized layers

### `bronze_epab_document`
### `bronze_epab_publication`
### `bronze_epab_application`
### `bronze_epab_abstract`
### `bronze_epab_claims`

Primary sources:
- EP Full Text Publication Database (`EPAB`)

Use:
- EP publication identity
- English abstract extraction
- English Claim 1 extraction for granted EP `B` documents

Constraint:
- do not reuse EPAB classifications, party tables, or citation metadata in the semantic pipeline because PATSTAT and Register already own those normalized layers

### `bronze_patstat_appln_prior`

Primary source:
- `tls204_appln_prior`

Use:
- earliest priority chain validation
- family anchor reconstruction

### `bronze_patstat_person`

Primary source:
- `tls206_person`

Core columns consumed:
- `person_id`
- `person_name`
- `person_ctry_code`
- `doc_std_name`
- `psn_id`
- `psn_name`
- `han_id`
- `han_name`
- `psn_sector`

### `bronze_patstat_pers_appln`

Primary source:
- `tls207_pers_appln`

Use:
- applicant / inventor extraction
- assignee ownership lineage

### `bronze_patstat_appln_ipc`

Primary source:
- `tls209_appln_ipc`

Use:
- canonical IPC stream
- CPC-to-IPC unification target

### `bronze_patstat_pat_publn`

Primary source:
- `tls211_pat_publn`

Core columns consumed:
- `pat_publn_id`
- `publn_auth`
- `publn_nr`
- `publn_kind`
- `publn_date`
- `appln_id`

Use:
- publication lifecycle
- kind-code interpretation
- citation-document mapping
- `C0` / UP detection at publication level

### `bronze_patstat_citation`

Primary source:
- `tls212_citation`

Use:
- document citation edge extraction
- source-preserving distinction between patent citations and NPL references
- backward NPL detection through `cited_npl_publn_id`

### `bronze_patstat_npl_publn`

Primary source:
- `tls214_npl_publn`

Use:
- raw non-patent literature bibliography registry
- family-level backward NPL lineage
- science-grounding and research-intensity features
- OECD and quality overlays that must remain separate from patent-collision impact

### `bronze_patstat_appln_contn`

Primary source:
- `tls216_appln_contn`

Use:
- continuation / divisional awareness

### `bronze_patstat_appln_cpc`

Primary source:
- `tls224_appln_cpc`

Current v1 nearest sources:
- `main.raw_family_cpc`
- `main.family_cpc`
- `main.family_cpc_metrics`

### `bronze_patstat_docdb_fam_citn`

Primary source:
- `tls228_docdb_fam_citn`

Use:
- family-level citation skeleton

### `bronze_patstat_appln_nace2`

Primary source:
- `tls229_appln_nace2`

Use:
- optional industry overlays

### `bronze_patstat_appln_techn_field`

Primary source:
- `tls230_appln_techn_field`

Use:
- PATSTAT WIPO field references

### `bronze_patstat_inpadoc_legal_event`

Primary source:
- `tls231_inpadoc_legal_event`

Use:
- legal event truth for:
  - grant
  - lapse
  - abandonment
  - opposition
  - expiry
  - UP / UPC logic

## A2. PATSTAT Register Bronze

These tables are optional for the global warehouse but mandatory for the EP legal power-up path.

Rule:
- PATSTAT Register is an EP-only procedural overlay
- Register-derived fields may enrich EP publication evidence and EP-special grant modeling
- Register-derived fields must not change the global 4D scoring tensors or percentile marts

### `bronze_reg101_appln`

Primary source:
- `reg101_appln`

Use:
- EP application anchor for Register joins
- linkage from `appln_id` into the Register universe

### `bronze_reg107_parties`

Primary source:
- `reg107_parties`

Use:
- lead agent / outside counsel extraction
- applicant / inventor / agent role inspection for EP detail

### `bronze_reg111_licensee`

Primary source:
- `reg111_licensee`

Use:
- EP registered-license overlay

### `bronze_reg125_appeal`

Primary source:
- `reg125_appeal`

Use:
- EP appeal-state overlay for challenged rights

### `bronze_reg130_opponent`

Primary source:
- `reg130_opponent`

Use:
- current or final EP opposition state
- opponent names
- opponent agent names

MVP scope limit:
- prefer `IS_LATEST`-based extraction rather than full opposition chronology replay

### `bronze_reg201_proc_step`
### `bronze_reg202_proc_step_text`
### `bronze_reg203_proc_step_date`

Primary sources:
- `reg201_proc_step`
- `reg202_proc_step_text`
- `reg203_proc_step_date`

Use:
- EP prosecution-maturity feature generation
- EP-special grant-probability modeling
- EP procedural timeline display

### `bronze_reg301_event_data`
### `bronze_reg402_event_text`

Primary sources:
- `reg301_event_data`
- `reg402_event_text`

Use:
- EP procedural event timeline
- EP display-ledger overrides when needed

### `bronze_reg701_appln`
### `bronze_reg731_event_data`
### `bronze_reg741_appln_status`
### `bronze_reg742_event_text`

Primary sources:
- `reg701_appln`
- `reg731_event_data`
- `reg741_appln_status`
- `reg742_event_text`

Use:
- definitive Unitary Patent procedural truth for EP detail and UP evidence views
- UP-specific status and event overlays

## B. Reference Bronze

### `bronze_ref_country`
- `tls801_country`

### `bronze_ref_legal_event_code`
- `tls803_legal_event_code`

### `bronze_ref_techn_field_ipc`
- `tls901_techn_field_ipc`

### `bronze_ref_ipc_nace2`
- `tls902_ipc_nace2`

## C. External Bronze

### `bronze_ext_iso_country_map`
### `bronze_ext_world_bank_gdp_ppp`
### `bronze_ext_us_chamber_ip_index`
### `bronze_ext_up_member_states`
### `bronze_ext_kind_code_normalization_seed`
### `bronze_ext_oecd_indicator_seed`

Current implementation note:
- the OECD seed is planned as a family-level long-form indicator artifact projected into the Bronze reference contract
- see:
  - `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`
  - `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`

## D. Current V1 Inputs Worth Reusing

These are not true Bronze, but they can bootstrap V2:

- `main.patent_core`
- `main.family_members`
- `main.family_members_metrics`
- `main.family_grants`
- `main.family_grant_metrics`
- `main.family_cpc`
- `main.family_cpc_metrics`
- `main.owner_reference`
- `main.patent_citation_events_core`
- `main.patent_citation_events_yearly`
- `main.patent_citation_metrics`
- `main.ml_training_table`

## Silver Layer

### `silver_family_core`
- family anchor table
- one row per `docdb_family_id`
- carries scope-horizon flags used to separate current-state and heritage logic

Built from:
- `bronze_patstat_appln`
- `bronze_patstat_appln_prior`

Outputs:
- `docdb_family_id`
- `inpadoc_family_id`
- `family_earliest_priority_date`
- `family_priority_year`
- `is_main_window_family`
- `is_heritage_backfill_family`
- `is_out_of_bounds_ghost`
- `family_size_docdb`

Rule:
- current-state marts should roll over `is_main_window_family = true`
- heritage-oriented marts may additionally include `is_heritage_backfill_family = true`

### `silver_family_member_publications`
- family-to-publication bridge

Built from:
- `bronze_patstat_pat_publn`
- `bronze_patstat_appln`

### `silver_assignee_harmonized`

Built from:
- `bronze_patstat_person`
- `bronze_patstat_pers_appln`

Outputs:
- `harmonized_owner_id`
- `ultimate_parent_name`

### `silver_kind_code_normalization`

Built from:
- `bronze_ext_kind_code_normalization_seed`
- office-aware PATSTAT publication evidence

Outputs:
- `universal_stage`
- `stage_multiplier`
- `is_enforceable`
- `legal_status_proxy`

### `silver_tiered_market_weighting`

Built from:
- `bronze_ext_world_bank_gdp_ppp`
- `bronze_ext_us_chamber_ip_index`
- `bronze_ext_iso_country_map`

Outputs:
- `gdp_tier_weight`
- `ip_score`
- `final_market_multiplier`

### `silver_up_status`

Built from:
- `bronze_patstat_pat_publn`
- `bronze_patstat_inpadoc_legal_event`
- `bronze_ext_up_member_states`

### `silver_family_jurisdiction_unrolled`

Built from:
- `silver_family_member_publications`
- `silver_up_status`

Outputs:
- jurisdiction set after UP expansion

### `silver_legal_status_event_ledger`

Built from:
- `bronze_patstat_inpadoc_legal_event`
- `silver_kind_code_normalization`
- `silver_family_member_publications`

Constraint:
- this remains the canonical cross-office legal ledger for global family analytics
- PATSTAT Register may override it only in EP publication-detail display marts, not in cross-office percentile scoring

### `silver_family_status_pt`

Built from:
- `silver_legal_status_event_ledger`
- `silver_family_jurisdiction_unrolled`

Outputs:
- `family_composite_status`
- `active_jurisdiction_count`
- `has_any_active_grant`
- `is_dead_family`

Constraint:
- family status remains the global family truth
- Register-derived EP flags may bubble up as overlays but must not overwrite the canonical family label

### `silver_ep_register_core`

Built from:
- `bronze_reg101_appln`
- `bronze_reg111_licensee`
- `bronze_patstat_appln`
- `silver_family_member_publications`

Outputs:
- EP Register presence flags
- EP application identity in the Register universe
- `register_record_present`
- `ep_registered_license_flag`
- `ep_licensee_names`

### `silver_ep_register_agent_summary`

Built from:
- `bronze_reg107_parties`
- `silver_ep_register_core`

Outputs:
- `ep_register_lead_agent_name`
- `ep_register_lead_agent_country`
- `ep_register_agent_customer_id`

### `silver_ep_register_current_opposition`

Built from:
- `bronze_reg130_opponent`
- `bronze_reg125_appeal`
- `silver_ep_register_core`

Outputs:
- `ep_opposition_active`
- `ep_opposition_status_text`
- `ep_opponent_names`
- `ep_opponent_agent_names`
- `ep_appeal_active`
- `ep_appeal_result_text`

### `silver_ep_register_up_status`

Built from:
- `bronze_reg701_appln`
- `bronze_reg731_event_data`
- `bronze_reg741_appln_status`
- `silver_ep_register_core`

Outputs:
- `ep_register_is_unitary_patent`
- `ep_register_up_status_code`
- `ep_register_up_status_text`

Constraint:
- this is the strongest EP procedural source for UP evidence display
- it must not silently alter cross-office percentile ranking logic

### `silver_ep_register_proc_step_features`

Built from:
- `bronze_reg201_proc_step`
- `bronze_reg202_proc_step_text`
- `bronze_reg203_proc_step_date`
- `bronze_reg301_event_data`
- `silver_ep_register_core`

Outputs:
- `ep_proc_step_maturity_score`
- `ep_search_report_mailed_date`
- `ep_latest_proc_phase_code`
- `ep_latest_proc_result_code`
- `ep_proc_time_limit_days`

Purpose:
- Level 3 EP procedural timeline
- isolated EP-special grant-model feature supply

### `silver_ep_register_display_ledger`

Built from:
- `silver_ep_register_core`
- `silver_ep_register_current_opposition`
- `silver_ep_register_up_status`
- `silver_ep_register_proc_step_features`
- `silver_legal_status_event_ledger`

Outputs:
- `ep_display_status_text`
- `status_source`
- `status_source_priority`
- `register_override_flag`

Rule:
- this table is for EP publication-detail and evidence views
- it must not feed `silver_family_enforceability_branches`

### `silver_family_ipc_cpc_canonical`

Built from:
- `bronze_patstat_appln_ipc`
- `bronze_patstat_appln_cpc`

### `silver_family_wipo_fields`

Built from:
- `silver_family_ipc_cpc_canonical`
- `bronze_ref_techn_field_ipc`

Outputs:
- `wipo_field`
- `field_fraction`
- `family_tech_breadth_wipo_count`

### `silver_family_citation_edges`

Built from:
- `bronze_patstat_citation`
- `bronze_patstat_docdb_fam_citn`
- `silver_family_member_publications`

Rule:
- this table contains patent-family citation edges only
- NPL references must not be merged into the patent collision graph

### `silver_family_npl_backlinks`

Built from:
- `bronze_patstat_citation`
- `bronze_patstat_npl_publn`
- `silver_family_member_publications`

Outputs:
- `docdb_family_id`
- `citing_appln_id`
- `cited_npl_publn_id`
- `npl_citation_count`
- `science_linkage_flag`

Purpose:
- preserve backward NPL linkage at family level without polluting patent-collision metrics
- support science-grounding, research-intensity, and OECD-style quality overlays

### `silver_family_citation_edges_clean`

Built from:
- `silver_family_citation_edges`
- `silver_assignee_harmonized`

### `silver_family_citation_metrics`

Built from:
- `silver_family_citation_edges_clean`
- `silver_family_core`
- `silver_family_wipo_fields`

Outputs:
- `family_forward_citations_raw`
- `family_forward_citations_clean`
- `family_forward_citations_weighted`
- `family_backward_citations_clean`
- `family_backward_npl_citation_count`
- `family_rcf_score`
- `family_fwd_cits5`
- `family_fwd_cits7`
- `family_science_grounding_score`

Method note:
- windowed forward metrics and weighted citation impact use the family publication anchor, with priority-date fallback only when publication dating is unavailable

### `silver_enriched_citation_network`

Built from:
- `silver_family_citation_edges_clean`
- `silver_assignee_harmonized`
- `silver_kind_code_normalization`
- `silver_tiered_market_weighting`
- trend tables

Outputs:
- `citation_lethality_score`
- `citing_assignee_name`
- `citing_jurisdiction_code`
- `citation_date`
- `clean_edge_weight`

Method note:
- the event ledger is publication-dated and the lethality score is citing-side weighted, not cited-side weighted

### `silver_global_tech_trends_timeseries`
### `silver_local_tech_trends_timeseries`

Built from:
- `silver_family_core`
- `silver_family_wipo_fields`
- `silver_family_jurisdiction_unrolled`

Outputs:
- global and localized trend coefficients

### `silver_family_coverage_metrics`

Built from:
- `silver_family_jurisdiction_unrolled`
- `silver_family_status_pt`
- `silver_tiered_market_weighting`

Outputs:
- `family_raw_breadth_jurisdiction_count`
- `family_weighted_market_reach_score`
- `family_coverage_stability_score`

### `silver_family_enforceability_branches`

Built from:
- `silver_family_status_pt`
- `silver_kind_code_normalization`
- `silver_tiered_market_weighting`
- `silver_family_wipo_fields`
- `silver_local_tech_trends_timeseries`

Outputs:
- one row per `family x snapshot x jurisdiction x field`
- `branch_enforceability_contribution_raw`
- `branch_coefficient_mode`

### `silver_family_oecd_quality`

Built from:
- `silver_family_citation_edges_clean`
- `silver_family_npl_backlinks`
- `silver_family_wipo_fields`
- `silver_family_core`

Outputs:
- `family_generality_score`
- `family_originality_score`
- `family_radicalness_score`
- `family_backward_npl_citation_count`
- `family_science_grounding_score`

### `silver_family_text_representative`

Built from:
- `bronze_epab_claims`
- `bronze_epab_abstract`
- `bronze_patstat_appln_abstr`
- `silver_family_member_publications`
- `silver_kind_code_normalization`
- `silver_family_core`

Deterministic hierarchy:
1. English EP granted `B` Claim 1 from EPAB,
2. PATSTAT English abstract fallback if no usable EP grant claim exists.

Outputs:
- `representative_appln_id`
- `representative_publn_id`
- `representative_stage`
- `representative_claim_1_en`
- `representative_abstract_en`
- `text_provenance`
- `is_abstract_fallback`

Rules:
- `A`-document claims must not be used for claim-oriented `vector_claims`
- Claim extraction should use Claim 1 only for MVP
- XML/markup sanitization is mandatory before embedding

### Predictive Silver
- `silver_grant_probability_forecast`
- `silver_lapse_risk_forecast`
- `silver_friction_risk_forecast`

Register-assisted predictive sidecar:
- `silver_ep_grant_probability_forecast`
  - trained only for EP applications using `silver_ep_register_proc_step_features`
  - may roll up into portfolio pending-threat surfaces only after prediction
  - must remain isolated from non-EP grant models

## Vector Sidecar

### `vec_family_embeddings`

Built from:
- `silver_family_text_representative`
- embedding model pipeline

Outputs:
- `docdb_family_id`
- `vector_space`
- `representative_appln_id`
- `representative_publn_id`
- `text_provenance`
- `is_abstract_fallback`
- `earliest_priority_timestamp`
- `wipo_field`
- `overall_bp_percentile` where required for abstract-space whitespace overlays

## Gold Layer

### `gold_family_summary`
### `gold_family_heritage_summary`

Built from:
- `silver_family_core`
- `silver_assignee_harmonized`
- `silver_family_status_pt`
- `silver_family_coverage_metrics`
- `silver_family_wipo_fields`
- `silver_family_oecd_quality`

### `gold_family_blocking_power`

Built from:
- `silver_family_enforceability_branches`
- `silver_family_citation_metrics`

Outputs:
- `family_market_threat_score_raw`
- `family_adjusted_citation_score_raw`
- `family_raw_absolute_blocking_power`
- `family_ui_blocking_power_score`
- `family_overall_legal_enforceability_score`

### `gold_family_blocking_power_timeseries`
### `gold_family_field_contributions_timeseries`
### `gold_family_attacker_summary`
### `gold_portfolio_field_timeseries`
### `gold_portfolio_summary`
### `gold_portfolio_heritage_summary`
### `gold_portfolio_threat_matrix`
### `gold_family_forecast_summary`
### `gold_portfolio_forecast_summary`
### `gold_semantic_match_context`
### `gold_family_ep_register_badges`
### `gold_publication_ep_register_evidence`

Register Gold constraint:
- these marts are evidence and UI-overlay marts
- they must not be reused as hidden inputs to percentile-ranking or blocking-power generation

Heritage Gold rule:
- heritage-oriented Gold marts may include `is_heritage_backfill_family = true`
- current-state Gold marts must remain restricted to `is_main_window_family = true`

## Minimum V2 Warehouse Skeleton

### Bronze
- `bronze_patstat_appln`
- `bronze_patstat_appln_title`
- `bronze_patstat_appln_abstr`
- `bronze_patstat_appln_prior`
- `bronze_patstat_person`
- `bronze_patstat_pers_appln`
- `bronze_patstat_appln_ipc`
- `bronze_patstat_appln_cpc`
- `bronze_patstat_pat_publn`
- `bronze_patstat_citation`
- `bronze_patstat_npl_publn`
- `bronze_patstat_docdb_fam_citn`
- `bronze_patstat_appln_techn_field`
- `bronze_patstat_inpadoc_legal_event`
- `bronze_uspto_ft_document`
- `bronze_uspto_ft_abstract`
- `bronze_uspto_ft_claims`
- `bronze_epab_document`
- `bronze_epab_abstract`
- `bronze_epab_claims`
- `bronze_reg101_appln`
- `bronze_reg107_parties`
- `bronze_reg111_licensee`
- `bronze_reg125_appeal`
- `bronze_reg130_opponent`
- `bronze_reg201_proc_step`
- `bronze_reg202_proc_step_text`
- `bronze_reg203_proc_step_date`
- `bronze_reg301_event_data`
- `bronze_reg402_event_text`
- `bronze_reg701_appln`
- `bronze_reg731_event_data`
- `bronze_reg741_appln_status`
- `bronze_reg742_event_text`
- `bronze_ref_techn_field_ipc`
- `bronze_ref_legal_event_code`
- `bronze_ext_world_bank_gdp_ppp`
- `bronze_ext_us_chamber_ip_index`
- `bronze_ext_iso_country_map`
- `bronze_ext_up_member_states`
- `bronze_ext_kind_code_normalization_seed`

### Silver
- `silver_family_core`
- `silver_family_member_publications`
- `silver_assignee_harmonized`
- `silver_kind_code_normalization`
- `silver_tiered_market_weighting`
- `silver_up_status`
- `silver_family_jurisdiction_unrolled`
- `silver_legal_status_event_ledger`
- `silver_family_status_pt`
- `silver_family_ipc_cpc_canonical`
- `silver_family_wipo_fields`
- `silver_family_citation_edges`
- `silver_family_citation_edges_clean`
- `silver_family_npl_backlinks`
- `silver_family_citation_metrics`
- `silver_enriched_citation_network`
- `silver_global_tech_trends_timeseries`
- `silver_local_tech_trends_timeseries`
- `silver_family_coverage_metrics`
- `silver_family_enforceability_branches`
- `silver_family_oecd_quality`
- `silver_family_text_representative`
- `silver_ep_register_core`
- `silver_ep_register_agent_summary`
- `silver_ep_register_current_opposition`
- `silver_ep_register_up_status`
- `silver_ep_register_proc_step_features`
- `silver_ep_register_display_ledger`
- `silver_grant_probability_forecast`
- `silver_ep_grant_probability_forecast`
- `silver_lapse_risk_forecast`
- `silver_friction_risk_forecast`

### Gold
- `gold_family_summary`
- `gold_family_blocking_power`
- `gold_family_blocking_power_timeseries`
- `gold_family_field_contributions_timeseries`
- `gold_family_attacker_summary`
- `gold_portfolio_field_timeseries`
- `gold_portfolio_summary`
- `gold_portfolio_threat_matrix`
- `gold_family_forecast_summary`
- `gold_portfolio_forecast_summary`
- `gold_semantic_match_context`
- `gold_family_ep_register_badges`
- `gold_publication_ep_register_evidence`

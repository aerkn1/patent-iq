# PatentIQ V2 Metric Lineage Catalog

## Purpose

Fix the exact lineage of the core PatentIQ metrics from Bronze to Silver to Gold.

Each metric below defines:

1. canonical metric name
2. Bronze inputs
3. Silver producer tables
4. formula / transformation logic
5. Gold consumers

## 1. Entity Anchor Metrics

### `family_earliest_priority_date`

Bronze:
- `bronze_patstat_appln.earliest_filing_date`
- `bronze_patstat_appln.docdb_family_id`
- `bronze_patstat_appln_prior`

Silver producer:
- `silver_family_core`

Formula:
- minimum valid priority-linked filing date within the canonical family

### `family_priority_year`

Formula:
- `EXTRACT(YEAR FROM family_earliest_priority_date)`

Used by:
- cohort normalization
- R&D momentum anchors
- OECD cohort definitions

### `is_main_window_family`

Silver producer:
- `silver_family_core`

Formula:
- `family_priority_year between 2007 and 2026` under the current MVP scope policy

Use:
- current-state portfolio views
- blocking power
- forecast and semantic eligibility baselines

### `is_heritage_backfill_family`

Silver producer:
- `silver_family_core`

Formula:
- `family_priority_year between 1996 and 2006` for the first historical backfill horizon

Use:
- heritage contribution
- pioneer rankings
- historical citation-influence support

## 2. Family Structure Metrics

### `family_size_docdb`

Bronze:
- `bronze_patstat_appln.docdb_family_size`

Silver producer:
- `silver_family_core`

### `family_member_publication_count`

Bronze:
- `bronze_patstat_pat_publn`

Silver producer:
- `silver_family_member_publications`

Use:
- evidence only
- never the default innovation count

## 3. Legal Stage Metrics

### `branch_universal_stage`

Bronze:
- `bronze_patstat_pat_publn.publn_auth`
- `bronze_patstat_pat_publn.publn_kind`
- `bronze_ext_kind_code_normalization_seed`

Silver producer:
- `silver_kind_code_normalization`

Formula:
- office-aware lookup by `jurisdiction_code + kind_code`

### `branch_stage_multiplier`

Silver producer:
- `silver_kind_code_normalization.stage_multiplier`

Illustrative semantics:
- pending application = low
- standard grant = baseline enforceability
- opposition survivor = elevated resilience
- `C0` / UP = modifier with territorial effect

## 4. Coverage Metrics

### `family_raw_breadth_jurisdiction_count`

Bronze:
- publication authorities
- legal events
- UP member-state expansion

Silver producer:
- `silver_family_jurisdiction_unrolled`
- `silver_family_coverage_metrics`

Formula:
- count distinct jurisdictions after UP expansion and deduplication

### `family_weighted_market_reach_score`

Bronze:
- jurisdiction set
- GDP/IP weighting references

Silver producer:
- `silver_tiered_market_weighting`
- `silver_family_coverage_metrics`

Formula:
- sum `final_market_multiplier` across active jurisdictions

### `family_coverage_stability_score`

Silver producer:
- `silver_family_coverage_metrics`

Formula:
- durability proxy based on active-branch retention relative to total branch set

## 5. Technical Breadth Metrics

### `family_tech_breadth_wipo_count`

Bronze:
- `bronze_patstat_appln_ipc`
- `bronze_patstat_appln_cpc`
- `bronze_ref_techn_field_ipc`

Silver producer:
- `silver_family_ipc_cpc_canonical`
- `silver_family_wipo_fields`

Formula:
1. collect all IPC/CPC across family
2. truncate CPC to IPC-compatible structure
3. dedupe codes
4. join WIPO concordance
5. dedupe WIPO fields
6. count unique WIPO fields

### `family_field_fraction`

Silver producer:
- `silver_family_wipo_fields.field_fraction`

Formula:
- `1 / family_tech_breadth_wipo_count`

## 6. Citation Metrics

### `family_forward_citations_raw`

Bronze:
- `bronze_patstat_citation`
- `bronze_patstat_docdb_fam_citn`

Silver producer:
- `silver_family_citation_edges`
- `silver_family_citation_metrics`

Formula:
- count distinct citing families before cleaning

### `family_forward_citations_clean`

Silver producer:
- `silver_family_citation_edges_clean`
- `silver_family_citation_metrics`

Formula:
- forward citations after removing:
  - intra-family citations
  - self-citations where possible

### `family_forward_citations_weighted`

Silver producer:
- `silver_enriched_citation_network`
- `silver_family_citation_metrics`

Formula:
- sum weighted incoming citation edges

Where citing-side weights may use:
- citing stage multiplier
- citing jurisdiction market weight
- citing field trend coefficient
- active status

Constraint:
- this metric must be built from patent-family citation edges only
- NPL references must not feed current blocking-power collision impact

### `family_rcf_score`

Silver producer:
- `silver_family_citation_metrics`

Formula:
- `family_forward_citations_weighted / cohort_average_forward_citations_weighted`

Cohort:
- `family_priority_year + primary_wipo_field`

### `family_backward_npl_citation_count`

Bronze:
- `bronze_patstat_citation.cited_npl_publn_id`
- `bronze_patstat_npl_publn`

Silver producer:
- `silver_family_npl_backlinks`
- `silver_family_citation_metrics`
- `silver_family_oecd_quality`

Formula:
- count backward NPL references after collapsing the citing publications to the canonical family

Use:
- science-grounding
- research-intensity descriptors
- OECD-style quality overlays

### `family_science_grounding_score`

Silver producer:
- `silver_family_npl_backlinks`
- `silver_family_citation_metrics`
- `silver_family_oecd_quality`

Definition:
- normalized indicator describing how strongly the family is grounded in non-patent scientific literature

Rule:
- this score must remain separate from current blocking-power impact

### `family_adjusted_citation_score_raw`

Canonical V2 definition:
- cohort-normalized clean weighted forward influence
- typically implemented via `family_rcf_score`

Constraint:
- this score must use adjusted patent-family forward citations
- backward NPL references must not be blended into this blocking-power component

## 7. OECD / Nature Of Innovation Metrics

### `family_generality_score`

Silver producer:
- `silver_family_oecd_quality`

Formula:
- `1 - SUM((share of forward-citing families by WIPO field)^2)`

### `family_originality_score`

Silver producer:
- `silver_family_oecd_quality`

Formula:
- `1 - SUM((share of backward-cited families by WIPO field)^2)`

Default interpretation rule:
- compute from backward patent-family citations unless a blended patent-plus-NPL variant is explicitly labeled

### `family_radicalness_score`

Silver producer:
- `silver_family_oecd_quality`

Recommended V2 rule:
- share of backward-cited knowledge drawn from outside the family’s primary field

Extension rule:
- an NPL-aware radicalness companion may be added later, but it must not silently replace the default patent-network version

### `family_fwd_cits5`
### `family_fwd_cits7`

Silver producer:
- `silver_family_citation_metrics`
- `silver_family_oecd_quality`

Formula:
- clean forward citations accumulated within 5-year / 7-year windows from family anchor

## 8. Legal Status Metrics

### `family_composite_status`

Silver producer:
- `silver_family_status_pt`

Possible values:
- `fully_active`
- `pending_emerging`
- `under_fire`
- `partially_lapsed`
- `dead`

### `family_has_any_active_grant`

Silver producer:
- `silver_family_status_pt`

Formula:
- true if at least one active enforceable grant-stage branch exists at snapshot date

### `ep_display_status_text`

Silver producer:
- `silver_ep_register_display_ledger`

Bronze inputs:
- `bronze_reg101_appln`
- `bronze_reg301_event_data`
- `bronze_reg741_appln_status`
- `bronze_patstat_inpadoc_legal_event`

Formula:
- EP detail-display status resolved through source-priority logic where PATSTAT Register may override INPADOC for EP publication evidence views

Constraint:
- display-only override
- must not silently replace canonical cross-office family status in percentile marts

### `status_source_priority`

Silver producer:
- `silver_ep_register_display_ledger`

Values:
- `register_override`
- `register_only`
- `inpadoc_only`
- `inpadoc_fallback`

### `ep_opposition_active`

Silver producer:
- `silver_ep_register_current_opposition`

Bronze inputs:
- `bronze_reg130_opponent`

Formula:
- true when an EP application has a latest or current opposition state indicating an active opposition

MVP rule:
- use latest or current opposition rows rather than reconstructing the full multi-year chronology

### `ep_opponent_names`

Silver producer:
- `silver_ep_register_current_opposition`

Formula:
- ordered distinct array of current or final opponent names from Register opposition records

### `ep_appeal_active`

Silver producer:
- `silver_ep_register_current_opposition`

Bronze inputs:
- `bronze_reg125_appeal`

Formula:
- true when the current EP appeal state is open or unresolved at the display snapshot

### `ep_register_lead_agent_name`

Silver producer:
- `silver_ep_register_agent_summary`

Bronze inputs:
- `bronze_reg107_parties`

Formula:
- preferred latest EP Register party where `TYPE = 'AGENT'`

### `ep_register_is_unitary_patent`

Silver producer:
- `silver_ep_register_up_status`

Bronze inputs:
- `bronze_reg701_appln`
- `bronze_reg741_appln_status`
- `bronze_reg731_event_data`

Formula:
- true when Register UP records confirm a Unitary Patent registration or equivalent active UP status

Constraint:
- this is the strongest EP-side procedural truth for detail display
- it does not, by itself, modify cross-office blocking-power percentiles

### `ep_registered_license_flag`

Silver producer:
- `silver_ep_register_core`

Bronze inputs:
- `bronze_reg111_licensee`

Formula:
- true when at least one active or valid Register license record exists for the EP application

### `ep_proc_step_maturity_score`

Silver producer:
- `silver_ep_register_proc_step_features`

Bronze inputs:
- `bronze_reg201_proc_step`
- `bronze_reg202_proc_step_text`
- `bronze_reg203_proc_step_date`
- `bronze_reg301_event_data`

Definition:
- heuristic or model-ready summary of how far the EP application has progressed through prosecution

Use:
- EP-special grant model only

Constraint:
- must not feed global blocking-power or portfolio percentile math

## 9. Trend Metrics

### `global_field_trend_coefficient`

Silver producer:
- `silver_global_tech_trends_timeseries`

Formula:
- `1 + ((filings_t - filings_t-1) / filings_t-1)`

### `local_field_trend_coefficient`

Silver producer:
- `silver_local_tech_trends_timeseries`

Formula:
- `1 + ((local_filings_t - local_filings_t-1) / local_filings_t-1)`

## 10. Branch-Level Enforceability Metrics

### `branch_enforceability_contribution_raw`

Silver producer:
- `silver_family_enforceability_branches`

Formula:

`branch_enforceability_contribution_raw = branch_stage_multiplier * final_market_multiplier * family_field_fraction * local_field_trend_coefficient * active_branch_flag`

### `branch_coefficient_mode`

Silver producer:
- `silver_family_enforceability_branches.branch_coefficient_mode`

Values:
- `localized`
- `global_fallback`
- `mixed`

## 11. Family-Level Current Threat Metrics

### `family_market_threat_score_raw`

Silver producer:
- `silver_family_enforceability_branches`

Gold producer:
- `gold_family_blocking_power`

Formula:
- sum of `branch_enforceability_contribution_raw` across all active jurisdiction x field branches

### `family_overall_legal_enforceability_score`

Gold producer:
- `gold_family_blocking_power`

Definition:
- family-facing product rollup of `family_market_threat_score_raw`

### `family_raw_absolute_blocking_power`

Gold producer:
- `gold_family_blocking_power`

Formula:

`family_raw_absolute_blocking_power = (w_market * family_market_threat_score_raw) + (w_citation * family_adjusted_citation_score_raw)`

Default MVP:
- `w_market = 0.5`
- `w_citation = 0.5`

### `family_ui_blocking_power_score`

Gold producer:
- `gold_family_blocking_power`

Formula:
- percentile rank of `family_raw_absolute_blocking_power` within the correct field-time cohort

## 12. Family-Field Metrics

### `family_field_enforceability_contribution_score`

Gold producer:
- `gold_family_field_contributions_timeseries`

Formula:
- sum of branch enforceability contributions inside a single `family x field x snapshot`

### `family_field_heritage_contribution_score`

Gold producer:
- `gold_family_field_contributions_timeseries`

Formula:
- `family_field_fraction * family_adjusted_citation_score_raw`

Scope rule:
- may use `silver_family_core.is_main_window_family = true`
- and may additionally include `silver_family_core.is_heritage_backfill_family = true` when the historical backfill horizon is present

## 13. Attacker And Threat-Network Metrics

### `citation_lethality_score`

Silver producer:
- `silver_enriched_citation_network`

Formula:
- citing-side weighted threat score using:
  - citing stage strength
  - citing jurisdiction value
  - citing field trend coefficient

### `family_top_attacker_score`

Gold producer:
- `gold_family_attacker_summary`

Formula:
- aggregate `citation_lethality_score` by citing assignee

## 14. Portfolio Metrics

### `portfolio_total_mass_score`

Gold producer:
- `gold_portfolio_summary`

Formula:
- sum family blocking-power values across in-scope active families

### `portfolio_hit_rate_top_decile`

Gold producer:
- `gold_portfolio_summary`

Formula:
- proportion of portfolio families in the top decile of their cohort

### `portfolio_crown_jewel_index`

Gold producer:
- `gold_portfolio_summary`

Formula:
- sum of top `N` family scores in target field / scope

### `portfolio_opposition_rate`

Gold producer:
- `gold_portfolio_summary`

Formula:
- `granted families with opposition event / total granted families`

### `portfolio_field_enforceability_score`

Gold producer:
- `gold_portfolio_field_timeseries`

Formula:
- sum of family field enforceability contributions by harmonized owner and snapshot

### `portfolio_field_heritage_score`

Gold producer:
- `gold_portfolio_field_timeseries`

Formula:
- sum of family field heritage contributions by harmonized owner and snapshot

Scope rule:
- heritage rollups must remain separate from current active portfolio rollups and may include the heritage backfill horizon

### `family_heritage_score`

Gold producer:
- `gold_family_heritage_summary`

Formula:
- current MVP implementation uses `family_adjusted_citation_score_raw` as the family-level heritage proxy

Scope rule:
- may include both main-window and heritage-backfill families

### `portfolio_total_heritage_score`

Gold producer:
- `gold_portfolio_heritage_summary`

Formula:
- sum of `family_heritage_score` across all families included in the portfolio heritage scope

## 15. Predictive Metrics

### `grant_probability_pct`

Silver producer:
- `silver_grant_probability_forecast`

Feature inputs:
- assignee historical grant rate
- field grant rate
- jurisdiction
- family size
- claim count
- months since filing

EP-special extension:
- `silver_ep_grant_probability_forecast` may add:
  - `ep_proc_step_maturity_score`
  - `ep_search_report_mailed_date`
  - `ep_latest_proc_phase_code`
  - `ep_latest_proc_result_code`

Constraint:
- these Register-derived features must remain isolated inside the EP-special model

### `lapse_risk_pct`

Silver producer:
- `silver_lapse_risk_forecast`

Feature inputs:
- branch age
- renewal horizon
- blocking power
- citation velocity
- local trend coefficient

### `friction_risk_pct`

Silver producer:
- `silver_friction_risk_forecast`

Feature inputs:
- citation velocity
- attacker concentration
- generality
- radicalness

## 16. Semantic Text And Vector Payload Metrics

### `text_provenance`

Silver producer:
- `silver_family_text_representative`

Bronze inputs:
- `bronze_uspto_ft_claims`
- `bronze_epab_claims`
- `bronze_patstat_appln_abstr`

Definition:
- deterministic identifier of the text artifact selected for embedding, such as a USPTO grant publication, EPAB grant publication, or PATSTAT abstract fallback

### `is_abstract_fallback`

Silver producer:
- `silver_family_text_representative`

Formula:
- true when no usable U.S. or EP grant Claim 1 exists and the semantic layer falls back to English abstract text

Constraint:
- this flag must remain visible to the vector payload and the UI because abstract fallback is weaker than granted-claim provenance for FTO-style workflows

### `representative_claim_1_en`

Silver producer:
- `silver_family_text_representative`

Definition:
- sanitized English Claim 1 selected through the semantic hierarchy

Hierarchy:
1. U.S. granted `B` Claim 1 from USPTO full text
2. English EP granted `B` Claim 1 from EPAB

Guardrail:
- application-stage `A`-document claims must not be used in the claim-space FTO flow

### `representative_abstract_en`

Silver producer:
- `silver_family_text_representative`

Definition:
- sanitized English abstract selected from USPTO, EPAB, or PATSTAT fallback sources

### `earliest_priority_timestamp`

Vector producer:
- `vec_family_embeddings`

Source dependency:
- `silver_family_core.family_earliest_priority_date`

Definition:
- chronology payload used by the vector layer to split semantic matches into prior art, peers, followers, and later threats

### `overall_bp_percentile`

Vector producer:
- `vec_family_embeddings`

Source dependency:
- `gold_family_blocking_power.family_ui_blocking_power_score`

Definition:
- current blocking-power percentile cached into the abstract vector payload when the backend needs fast whitespace-map overlays

Constraint:
- this is a serving-side scalar payload, not a text-selection input

## 17. Shortest Dependency Tree

1. `tls201_appln`, `tls211_pat_publn`, `tls231_inpadoc_legal_event`, `tls224_appln_cpc`, `tls212_citation`
2. `silver_kind_code_normalization`, `silver_tiered_market_weighting`, `silver_family_wipo_fields`, `silver_local_tech_trends_timeseries`, `silver_family_citation_metrics`
3. `silver_family_enforceability_branches`
4. `family_market_threat_score_raw`
5. `family_adjusted_citation_score_raw`
6. `family_raw_absolute_blocking_power`
7. `family_ui_blocking_power_score`

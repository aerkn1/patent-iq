# PATSTAT Register Read-Only Legal Power-Up Requirements

## Source

User-provided implementation guidance captured on March 14, 2026.

## Purpose

Define how PatentIQ should incorporate PATSTAT Register into the MVP without corrupting the global family-first and 4D scoring architecture.

## Executive Summary

PATSTAT Register adds hyper-granular procedural truth for:
1. classic EP applications,
2. Euro-PCT entries in the European phase,
3. Unitary Patent registration and status.

For the 5-week MVP, this integration must be treated as a:

`read-only EP legal power-up`

Meaning:
1. Register data may enrich EP publication and family evidence views,
2. Register data may feed a separate EP-special grant-prediction model,
3. Register data must not change the global 4D scoring tensors,
4. Register data must not change family blocking-power percentiles,
5. Register data must not change portfolio percentile rankings or mass rollups.

## Why This Matters

Register coverage is materially deeper for Europe than for other offices.

If Register-derived procedural certainty is allowed to flow into the global scoring engine, EP-heavy families will be systematically advantaged against US, CN, JP, or KR families simply because PatentIQ does not have equivalent prosecution-depth data for those systems in the MVP.

Therefore:
1. PATSTAT Register is allowed as a legal and procedural evidence overlay,
2. PATSTAT Register is allowed as an EP-only predictive feature source,
3. PATSTAT Register is banned from global cross-office percentile math.

## Premium MVP Value-Adds

## PRR-01: Surgical Opposition And Appeal Analytics

Requirement:
PatentIQ should use PATSTAT Register opposition and appeal tables to expose who is attacking an EP right and what the current or final opposition state is.

Primary tables:
1. `reg130_opponent`
2. `reg125_appeal`

MVP output:
1. `ep_opposition_active`
2. `ep_opposition_status_text`
3. `ep_opponent_names`
4. `ep_opponent_agent_names`
5. `ep_appeal_active`
6. `ep_appeal_result_text`

UI target:
1. publication evidence tab,
2. family-level EP warning badges.

## PRR-02: Outside Counsel Intelligence

Requirement:
PatentIQ should extract the prosecuting or lead outside counsel from Register party data.

Primary table:
1. `reg107_parties`

MVP rule:
Filter `TYPE = 'AGENT'` and prefer the latest or active representative where available.

MVP output:
1. `ep_register_lead_agent_name`
2. `ep_register_lead_agent_country`
3. `ep_register_agent_customer_id`

UI target:
1. family scorecard metadata,
2. publication evidence view.

## PRR-03: Definitive UP / UPC Procedural Ground Truth

Requirement:
When PATSTAT Register UP tables are available, PatentIQ should treat them as the strongest procedural source for UP registration state.

Primary tables:
1. `reg701_appln`
2. `reg731_event_data`
3. `reg741_appln_status`

MVP output:
1. `ep_register_is_unitary_patent`
2. `ep_register_up_status_code`
3. `ep_register_up_status_text`
4. `ep_register_up_event_latest_date`

Constraint:
This improves EP/UP evidence surfaces and EP legal interpretation, but it must not silently replace the family’s global analytical identity.

## PRR-04: Hyper-Accurate EP Grant Forecasting

Requirement:
PATSTAT Register procedural steps may feed a dedicated EP-special grant model.

Primary tables:
1. `reg201_proc_step`
2. `reg202_proc_step_text`
3. `reg203_proc_step_date`
4. `reg301_event_data`

MVP output:
1. `ep_proc_step_maturity_score`
2. `ep_search_report_mailed_date`
3. `ep_latest_proc_phase_code`
4. `ep_latest_proc_result_code`
5. `ep_proc_time_limit_days`

Constraint:
These features are allowed only in the isolated `EP-special` grant model and must not leak into non-EP grant models.

## MVP Integration Scope

## PRR-05: Bronze Register Ingestion Scope

Requirement:
The MVP Bronze layer should ingest the following PATSTAT Register tables as raw source-preserving Parquets:

Core and party tables:
1. `bronze_reg101_appln`
2. `bronze_reg107_parties`
3. `bronze_reg111_licensee`

Procedural tables:
1. `bronze_reg201_proc_step`
2. `bronze_reg202_proc_step_text`
3. `bronze_reg203_proc_step_date`
4. `bronze_reg301_event_data`
5. `bronze_reg402_event_text`

Legal-friction tables:
1. `bronze_reg130_opponent`
2. `bronze_reg125_appeal`

UP-specific tables:
1. `bronze_reg701_appln`
2. `bronze_reg731_event_data`
3. `bronze_reg741_appln_status`
4. `bronze_reg742_event_text`

## PRR-06: Silver Register Overlay Tables

Requirement:
The MVP Silver layer should create EP-specific overlay tables keyed by `appln_id` and joined back to the family only after the EP application state is resolved.

Recommended tables:
1. `silver_ep_register_core`
2. `silver_ep_register_agent_summary`
3. `silver_ep_register_current_opposition`
4. `silver_ep_register_up_status`
5. `silver_ep_register_proc_step_features`
6. `silver_ep_register_display_ledger`

## PRR-07: Gold Register UI Surfaces

Requirement:
PATSTAT Register should primarily feed detail and evidence surfaces rather than cross-office percentile marts.

Recommended Gold marts:
1. `gold_family_ep_register_badges`
2. `gold_publication_ep_register_evidence`

## Strict Guardrails

## PRR-08: Asymmetry Trap Ban

Requirement:
PATSTAT Register data must never modify:
1. `raw_enforceability_tensors`,
2. `family_raw_absolute_blocking_power`,
3. `family_ui_blocking_power_score`,
4. portfolio percentile or crown-jewel ranking outputs.

## PRR-09: Family-Collapse Paradox Must Be Preserved

Requirement:
Register data operates at `appln_id` grain and must not overwrite canonical family truth.

Implementation rule:
1. bubble EP-specific procedural flags up only as additive overlay fields,
2. preserve the family’s global status separately,
3. label UI outputs as:
   - `global_family_status`
   - `ep_member_register_status`

## PRR-10: Double-Clock Resolution Hierarchy

Requirement:
PatentIQ must treat INPADOC and PATSTAT Register as two parallel clocks for EP applications.

Resolution rule:
1. for EP publication-detail and EP Register UI display, PATSTAT Register procedural status overrides INPADOC where they conflict,
2. for global family scoring and cross-office ranking, the canonical legal ledger must remain method-consistent and must not let Register detail distort cross-office comparability,
3. any override must be traceable with `status_source = 'register_override'`.

## PRR-11: MVP Opposition Scope Limit

Requirement:
For the 5-week MVP, PATSTAT Register opposition ingestion should only support:
1. current or final opposition state,
2. opponent names,
3. opponent agent names,
4. core filing and status dates.

Implementation rule:
Prefer `IS_LATEST = TRUE` rows where available.

## PRR-12: EP-Special Predictive Isolation

Requirement:
Register-derived procedural features may feed only the isolated EP-special grant model.

Prohibited:
1. mixing Register features into non-EP grant models,
2. using Register features in blocking-power scoring,
3. using Register features in portfolio percentile math,
4. using Register features to boost European families in cross-office enforceability ranking.

## Bronze To Silver To UI Flow

## PRR-13: EP-Only Join Rule

Requirement:
Silver Register ETL must join PATSTAT Global to PATSTAT Register through:

`tls201_appln.appln_id = reg101_appln.appln_id`

Constraint:
Apply this join only when the application is in the EP / EPO procedural universe.

## PRR-14: Silver Feature Extraction Rules

Requirement:
The Register overlay layer should extract at least:

From `reg107_parties`:
1. `ep_register_lead_agent_name`
2. `ep_register_lead_agent_country`

From `reg130_opponent`:
1. `ep_opposition_active`
2. `ep_opponent_names`
3. `ep_opposition_status_text`

From `reg125_appeal`:
1. `ep_appeal_active`
2. `ep_appeal_result_text`

From `reg111_licensee`:
1. `ep_registered_license_flag`
2. `ep_licensee_names`

From `reg741_appln_status`:
1. `ep_register_is_unitary_patent`
2. `ep_register_up_status_text`

From `reg201_proc_step` and `reg301_event_data`:
1. `ep_proc_step_maturity_score`
2. `ep_latest_proc_phase_code`
3. `ep_latest_proc_result_code`
4. `ep_search_report_mailed_date`

## PRR-15: Portfolio Visibility Rule

Requirement:
PATSTAT Register must remain mostly invisible at portfolio percentile level.

Allowed exception:
1. EP-special grant-forecast outputs may roll up into portfolio pending-threat forecasts after they have already been scored at native EP application grain.

## PRR-16: Family And Publication UI Rule

Requirement:
Register data should surface in:

Level 2 family scorecards:
1. EP opposition badge,
2. UP registration badge,
3. registered license badge,
4. lead outside counsel.

Level 3 publication evidence view:
1. dedicated `EP Register` tab,
2. procedural milestone timeline,
3. current or final opposition state,
4. appeal state,
5. responsible agents and counterparties.

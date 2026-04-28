# PatentIQ V2 PATSTAT Register Legal Power-Up

## Purpose

Define how PATSTAT Register should be incorporated into the V2 MVP as an EP-only legal and procedural enhancement layer.

## Core Contract

PATSTAT Register is:
1. an EP, Euro-PCT, and UP procedural source,
2. a read-only legal power-up for MVP,
3. a valid source for EP-special grant-model features,
4. not a permitted hidden booster for global family blocking-power or portfolio percentiles.

## Allowed Product Uses

1. publication-level `EP Register` evidence tab,
2. family-level badges for EP opposition, UP registration, license, and lead outside counsel,
3. EP-special grant forecasting,
4. EP-specific legal explainability.

## Prohibited Product Uses

1. altering `gold_family_blocking_power.family_ui_blocking_power_score`,
2. altering `gold_portfolio_summary` percentiles or crown-jewel density,
3. altering global 4D tensors because Europe has richer procedural metadata than other offices in MVP,
4. relabeling the whole family based only on one EP application state.

## Bronze Ingestion Scope

Required raw tables:
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

## Silver Overlay Tables

Recommended tables:
1. `silver_ep_register_core`
2. `silver_ep_register_agent_summary`
3. `silver_ep_register_current_opposition`
4. `silver_ep_register_up_status`
5. `silver_ep_register_proc_step_features`
6. `silver_ep_register_display_ledger`

Join rule:
`bronze_patstat_appln.appln_id = bronze_reg101_appln.appln_id`

Restriction:
apply only inside the EP procedural universe.

## Gold Surfaces

Recommended Gold marts:
1. `gold_family_ep_register_badges`
2. `gold_publication_ep_register_evidence`

These marts are detail and evidence marts. They are not percentile-ranking marts.

## Dual-Clock Hierarchy

For EP detail surfaces:
1. Register procedural status may override INPADOC for display,
2. override provenance must be stored as metadata,
3. the global scoring path must remain Register-neutral.

## MVP Scope Limit

For `reg130_opponent`, MVP should only ship:
1. current or final opposition state,
2. opponent names,
3. opponent agent names,
4. key dates.

Deep multi-party chronology is deferred.

## EP-Special Grant Model

Allowed Register feature families:
1. search-report milestones,
2. exam-phase codes,
3. prosecution time-limit signals,
4. event-sequence maturity signals.

Constraint:
These features must stay isolated inside the EP-special grant model and must not be copied into non-EP models.

## Required Metadata

Every Register-derived Silver or Gold table should preserve:
1. `register_record_present`
2. `status_source`
3. `status_source_priority`
4. `register_snapshot_date`
5. `method_version`

## Delivery Rule

If a Register-derived field creates ambiguity between:
1. global family truth,
2. EP application procedural truth

the system must show both, with clear labels, rather than collapsing them into one misleading status string.

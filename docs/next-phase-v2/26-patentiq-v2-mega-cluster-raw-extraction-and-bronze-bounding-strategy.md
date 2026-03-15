# PatentIQ V2 Mega-Cluster Raw Extraction And Bronze Bounding Strategy

## Purpose

Define how PatentIQ should obtain the bounded raw source slice for the 10-field mega-cluster before Bronze parquet generation.

This note answers:

1. what should be extracted from each source family,
2. where filtering is allowed before Bronze,
3. what must remain source-faithful inside Bronze,
4. how ghost-node citation and OECD support rows are preserved,
5. how the raw bounded universe supports Silver and Gold without loading the full global corpus.

This note complements:

1. [17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md](./17-patentiq-v2-mega-cluster-scope-and-ghost-node-clarification.md)
2. [24-patentiq-v2-local-etl-and-artifact-build-runbook.md](./24-patentiq-v2-local-etl-and-artifact-build-runbook.md)
3. [patstat-schema.md](../data/patstat-schema.md)
4. [patstat-register-schema.md](../data/patstat-register-schema.md)
5. [uspto-full-text-schema.md](../data/uspto-full-text-schema.md)
6. [ep-full-text-publication-database-schema.md](../data/ep-full-text-publication-database-schema.md)

## Governing Rule

PatentIQ should not:

1. load the full global PATSTAT or EPAB corpus into Bronze for the MVP,
2. apply final family-first analytical scoring logic directly inside Bronze,
3. discard out-of-scope citation targets that are required for ghost-node-aware citation and OECD math.

The correct pattern is:

`seed -> expand -> land`

Meaning:

1. derive the initial in-scope application seed,
2. expand to the bounded family, publication, person, and EP procedural universe,
3. land those rows into source-faithful Bronze parquet tables.

## Stage A: PATSTAT Seed Extraction

### Primary Seed

Build `seed_appln_ids` from:

1. `tls230_appln_techn_field` where available,
2. otherwise `tls209_appln_ipc + tls901_techn_field_ipc` fallback.

Keep only applications that map into the selected 10 WIPO fields.

### Family Expansion

Build `seed_family_ids` from:

1. `tls201_appln`
2. `seed_appln_ids -> docdb_family_id`

### Publication Expansion

Build `seed_publn_ids` from:

1. `tls211_pat_publn`
2. all publications whose `appln_id` belongs to `seed_appln_ids`

### Person Expansion

Build `seed_person_ids` from:

1. `tls207_pers_appln`
2. all persons linked to `seed_appln_ids`

This raw seed universe becomes the extraction boundary for the major PATSTAT Bronze tables.

## Stage B: PATSTAT Bronze Extraction Rules

### Application-Bounded Tables

Extract all rows where `appln_id` is in the bounded seed for:

1. `bronze_patstat_appln_title`
2. `bronze_patstat_appln_abstr`
3. `bronze_patstat_appln_prior`
4. `bronze_patstat_appln_ipc`
5. `bronze_patstat_appln_cpc`
6. `bronze_patstat_appln_techn_field`
7. `bronze_patstat_inpadoc_legal_event`
8. `bronze_patstat_appln_contn`

### Family-Bounded Tables

Extract all rows where `docdb_family_id` is in the bounded seed for:

1. `bronze_patstat_appln`

This allows family-first Silver logic to work from a bounded but raw-faithful family universe.

### Publication-Bounded Tables

Extract all rows where `appln_id` is in the bounded seed for:

1. `bronze_patstat_pat_publn`

### Person-Bounded Tables

Extract all rows where:

1. `appln_id` is in scope for `bronze_patstat_pers_appln`
2. `person_id` is in the expanded bounded set for `bronze_patstat_person`

## Stage C: Citation And Ghost-Node Extraction Rules

Citation extraction must be source-bounded on the source side, but not fully bounded on the target side.

### Citation Table

For `bronze_patstat_citation`:

1. retain every row where the source `pat_publn_id` is in `seed_publn_ids`,
2. do not require the cited publication to be in scope.

This preserves out-of-scope citation targets as ghost-node evidence.

### Family Citation Table

For `bronze_patstat_docdb_fam_citn`:

1. retain rows where the source family is in `seed_family_ids`,
2. preserve the cited family even if it is outside the in-scope mega-cluster.

### NPL Table

For `bronze_patstat_npl_publn`:

1. retain only NPL rows actually referenced by the retained bounded citation slice.

## Stage D: PATSTAT Register Extraction Rules

Register extraction should only cover EP applications that already belong to the bounded PATSTAT universe.

### EP Register Seed

Build `seed_ep_appln_ids` from bounded PATSTAT applications where:

1. `appln_auth = 'EP'`
2. or the bounded family contains an EP member required for publication/legal detail.

### Core Register Extraction

Extract:

1. `bronze_reg101_appln`
2. `bronze_reg403_appln_status`

for rows whose `appln_id` is in `seed_ep_appln_ids`.

### Register-ID Expansion

From retained `reg101.id` values, expand to:

1. `bronze_reg107_parties`
2. `bronze_reg111_licensee`
3. `bronze_reg125_appeal`
4. `bronze_reg130_opponent`
5. `bronze_reg201_proc_step`
6. `bronze_reg202_proc_step_text`
7. `bronze_reg203_proc_step_date`
8. `bronze_reg301_event_data`
9. `bronze_reg402_event_text`

### UP Register Expansion

For retained EP Register anchors, extract:

1. `bronze_reg701_appln`
2. `bronze_reg731_event_data`
3. `bronze_reg741_appln_status`
4. `bronze_reg742_event_text`

only where the rows map to bounded in-scope applications.

## Stage E: USPTO Raw Extraction Rules

USPTO raw XML should not be parsed globally for the MVP.

### Seed

Build `seed_us_publication_numbers` from bounded PATSTAT publications where:

1. `publn_auth = 'US'`

### Extraction Rule

Retain or parse only USPTO XML files whose publication anchor matches:

1. the in-scope US publication universe

Then land:

1. `bronze_uspto_ft_document`
2. `bronze_uspto_ft_biblio_application`
3. `bronze_uspto_ft_abstract`
4. `bronze_uspto_ft_claims`
5. optional link and party support tables

## Stage F: EPAB Raw Extraction Rules

EPAB should follow the same bounded-publication pattern.

### Seed

Build `seed_ep_publication_numbers` from bounded PATSTAT publications where:

1. `publn_auth = 'EP'`

### Extraction Rule

Retain or parse only EPAB records whose publication/application anchors match the bounded EP publication slice.

Then land:

1. `bronze_epab_document`
2. `bronze_epab_publication`
3. `bronze_epab_application`
4. `bronze_epab_abstract`
5. `bronze_epab_claims`
6. optional pct, designated-state, priority, parent, divisional, and party tables

## Stage G: Reference And OECD Inputs

Reference tables should be copied in full into Bronze, not scope-filtered.

Keep full Bronze copies for:

1. `bronze_ref_techn_field_ipc`
2. `bronze_ref_legal_event_code`
3. `bronze_ext_iso_country_map`
4. `bronze_ext_world_bank_gdp_ppp`
5. `bronze_ext_us_chamber_ip_index`
6. `bronze_ext_up_member_states`
7. `bronze_ext_kind_code_normalization_seed`
8. `bronze_ext_oecd_indicator_seed`

These are small and are used as reusable reference overlays across the bounded universe.

## Bronze Filtering Policy

### Allowed In Bronze

Allowed:

1. physical extraction bounding to the mega-cluster raw universe,
2. seed-based selection of applications, families, publications, and persons,
3. ghost-node preservation for cited/citing targets,
4. typed casting and source-faithful column handling.

### Not Allowed In Bronze

Not allowed:

1. family-first scoring,
2. final legal-state interpretation,
3. final market-weighting composition,
4. final semantic representative-document selection,
5. portfolio or Market Intelligence aggregation.

## Table-Level Outcome

By the end of Bronze extraction:

1. PATSTAT entity tables are bounded but raw-faithful,
2. Register tables are bounded to in-scope EP applications,
3. USPTO and EPAB are bounded to in-scope publication members,
4. citation and OECD support rows preserve required out-of-scope ghost-node evidence,
5. reference tables remain globally complete.

## Why This Strategy Is Correct

This approach gives PatentIQ:

1. bounded storage cost,
2. deterministic reproducibility,
3. enough evidence for citation, OECD, semantic, and legal logic,
4. no silent pollution from the full global source universe,
5. no premature analytical distortion inside Bronze.

## Done Criteria

The Bronze extraction strategy is considered implemented when:

1. every required Bronze table has a defined raw extraction boundary,
2. all 10 selected WIPO fields are representable before Silver starts,
3. ghost-node citation targets remain preserved where required,
4. EP Register is bounded to in-scope EP cases only,
5. USPTO and EPAB are bounded to in-scope publication members only,
6. reference/OECD inputs are copied fully and typed correctly,
7. the extraction method is recorded in manifests and ETL logs.

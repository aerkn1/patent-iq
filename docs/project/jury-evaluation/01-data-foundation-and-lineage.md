# Section 01. Data Foundation, Sources, And Layered Lineage

## Table Of Contents

1. [Purpose Of This Section](#purpose-of-this-section)
2. [Current Runtime Boundary](#current-runtime-boundary)
3. [Data Sources Used By PatentIQ](#data-sources-used-by-patentiq)
   - [1. Primary patent data sources](#1-primary-patent-data-sources)
   - [2. Reference and external enrichment sources](#2-reference-and-external-enrichment-sources)
4. [Why The Pipeline Is Layered](#why-the-pipeline-is-layered)
   - [Bronze solves source fidelity](#bronze-solves-source-fidelity)
   - [Silver solves semantic normalization](#silver-solves-semantic-normalization)
   - [Gold solves product serving](#gold-solves-product-serving)
   - [Serving solves runtime delivery](#serving-solves-runtime-delivery)
5. [End-To-End ETL Stage Flow](#end-to-end-etl-stage-flow)
6. [Scope Definition And Bounded Universe](#scope-definition-and-bounded-universe)
   - [1. Field scope](#1-field-scope)
   - [2. Time scope](#2-time-scope)
   - [3. Snapshot policy](#3-snapshot-policy)
7. [Bronze Layer: Source-Preserving Structured Inputs](#bronze-layer-source-preserving-structured-inputs)
8. [Silver Layer: Canonical Analytical Contracts](#silver-layer-canonical-analytical-contracts)
   - [1. Scope seeding builds the bounded universe](#1-scope-seeding-builds-the-bounded-universe)
   - [2. `silver_family_core` defines the family anchor contract](#2-silver_family_core-defines-the-family-anchor-contract)
   - [3. `silver_family_member_publications` normalizes publication-stage evidence](#3-silver_family_member_publications-normalizes-publication-stage-evidence)
   - [4. Owner harmonization is deterministic and family-first](#4-owner-harmonization-is-deterministic-and-family-first)
   - [5. Kind-code normalization creates universal legal stages](#5-kind-code-normalization-creates-universal-legal-stages)
   - [6. WIPO field breadth and field fraction](#6-wipo-field-breadth-and-field-fraction)
   - [7. Market weighting converts jurisdiction reach into weighted reach](#7-market-weighting-converts-jurisdiction-reach-into-weighted-reach)
   - [8. UP expansion and jurisdiction unrolling](#8-up-expansion-and-jurisdiction-unrolling)
   - [9. Legal event ledger and family point-in-time status](#9-legal-event-ledger-and-family-point-in-time-status)
   - [10. Citation cleaning and enriched citation network](#10-citation-cleaning-and-enriched-citation-network)
   - [11. Citation metrics and heritage metrics](#11-citation-metrics-and-heritage-metrics)
   - [12. Global and local trend tables](#12-global-and-local-trend-tables)
   - [13. Coverage metrics](#13-coverage-metrics)
   - [14. Enforceability and market threat](#14-enforceability-and-market-threat)
   - [15. OECD-style quality layer](#15-oecd-style-quality-layer)
   - [16. OECD component metrics explicitly carried by the warehouse](#16-oecd-component-metrics-explicitly-carried-by-the-warehouse)
   - [16.1 Exact methodology documents for the longform artifact](#161-exact-methodology-documents-for-the-longform-artifact)
   - [16.2 Exact formulas used in the implemented build](#162-exact-formulas-used-in-the-implemented-build)
9. [Gold Layer: Product Marts Used By Backend And UI](#gold-layer-product-marts-used-by-backend-and-ui)
   - [1. `gold_family_summary`](#1-gold_family_summary)
   - [2. `gold_family_blocking_power`](#2-gold_family_blocking_power)
   - [3. Historical blocking and PIT-safe comparison marts](#3-historical-blocking-and-pit-safe-comparison-marts)
   - [4. `gold_portfolio_summary`](#4-gold_portfolio_summary)
   - [5. Market intelligence Gold marts](#5-market-intelligence-gold-marts)
   - [6. Semantic context mart](#6-semantic-context-mart)
10. [Serving Snapshots: Backend-Ready Delivery Layer](#serving-snapshots-backend-ready-delivery-layer)
11. [Why Bronze, Silver, And Gold Are Necessary In This Project](#why-bronze-silver-and-gold-are-necessary-in-this-project)
   - [Bronze is necessary because the source systems are heterogeneous](#bronze-is-necessary-because-the-source-systems-are-heterogeneous)
   - [Silver is necessary because the business logic is cross-source](#silver-is-necessary-because-the-business-logic-is-cross-source)
   - [Gold is necessary because the product is page-shaped](#gold-is-necessary-because-the-product-is-page-shaped)
   - [Serving is necessary because runtime and build responsibilities must stay separate](#serving-is-necessary-because-runtime-and-build-responsibilities-must-stay-separate)
12. [Key Takeaways](#key-takeaways)

## Purpose Of This Section

This section explains the most important technical backbone of PatentIQ: how raw patent data is obtained, narrowed to the product scope, normalized into reusable analytical contracts, and finally materialized into Gold marts and serving snapshots that power the user interface.

The main question this section answers is:

How does PatentIQ go from large external patent sources to trusted, explainable, UI-facing analytics?

The answer is not one query and not one model. It is a controlled data pipeline with explicit stage boundaries, deterministic outputs, and layered contracts.

Primary implementation references:

1. `etl/README.md:1-123`
2. `etl/scripts/run_stage.py:10-209`
3. `etl/src/patentiq_etl/common/config.py:17-82`
4. `etl/conf/build.yaml:1-93`
5. `etl/conf/scope.yaml:1-14`

## Current Runtime Boundary

The current runtime is a V2 stack built on top of the ETL warehouse:

1. `etl/` produces Bronze, Silver, Gold, ML, semantic, and serving artifacts.
2. `backend_v2/` consumes Gold or serving-layer artifacts and exposes page-shaped FastAPI contracts.
3. `frontend_v2/` consumes those V2 APIs and renders the current workspaces.

This matters because the ETL outputs, backend contracts, and frontend workspaces are intended to be read as one connected runtime.

Implementation references:

1. `etl/README.md:1-18`
2. `backend_v2/README.md:1-18`
3. `frontend_v2/README.md:1-15`

## Data Sources Used By PatentIQ

PatentIQ combines patent master data, legal data, publication/full-text data, and reference datasets. The default ETL source modes are configured in `etl/conf/build.yaml`.

### 1. Primary patent data sources

| Source family | Purpose in PatentIQ | Configured source mode | Main Bronze examples |
| --- | --- | --- | --- |
| PATSTAT Global | family anchors, applications, publications, citations, IPC/CPC, person links | `tip` | `bronze_patstat_appln`, `bronze_patstat_pat_publn`, `bronze_patstat_citation`, `bronze_patstat_docdb_fam_citn`, `bronze_patstat_appln_ipc`, `bronze_patstat_appln_cpc` |
| PATSTAT Register | EP procedure, opposition, parties, UP and procedural evidence | `tip` | `bronze_reg101_appln`, `bronze_reg107_parties`, `bronze_reg201_proc_step`, `bronze_reg731_event_data`, `bronze_reg741_appln_status` |
| EP Full Text / EPAB | abstracts and claims for semantic representation | `tip` | `bronze_epab_document`, `bronze_epab_publication`, `bronze_epab_claims`, `bronze_epab_abstract` |

### 2. Reference and external enrichment sources

| Reference source | Why it exists |
| --- | --- |
| ISO country map | converts market and jurisdiction datasets into consistent office/country keys |
| World Bank GDP PPP | provides market-size proxy used in tiered market weighting |
| U.S. Chamber IP Index | provides IP environment score used to scale market reach |
| UP member states | expands EP unitary grant coverage into member-state level reach |
| kind-code normalization seed | maps office-specific kind codes into universal lifecycle stages |
| WIPO field concordance | maps IPC/CPC to the selected WIPO industry fields |
| OECD indicator seed / longform artifacts | enriches or substitutes research-quality indicators |

The source-mode configuration is explicit:

1. `patstat_source_mode: "tip"`
2. `register_source_mode: "tip"`
3. `epab_source_mode: "tip"`
4. `refs_source_mode: "local_files"`

Implementation references:

1. `etl/conf/build.yaml:15-17`
2. `etl/conf/build.yaml:19-19`
3. `etl/README.md:27-58`
4. `etl/src/patentiq_etl/common/config.py:24-29`

## Why The Pipeline Is Layered

PatentIQ is not using Bronze, Silver, and Gold because it is fashionable. It uses the layered model because each layer solves a different technical problem:

### Bronze solves source fidelity

Bronze keeps the extracted source tables in structured Parquet form with minimal business reinterpretation. This preserves traceability back to PATSTAT, Register, EPAB, and reference files.

### Silver solves semantic normalization

Silver converts source-specific tables into canonical family-first contracts:

1. owner harmonization,
2. family anchors,
3. legal status replay,
4. jurisdiction expansion,
5. citation cleaning,
6. trend coefficients,
7. coverage, enforceability, and quality metrics.

This is the layer where source heterogeneity becomes product-ready analytical meaning.

### Gold solves product serving

Gold materializes page-shaped marts and ranking tables so the backend and UI do not have to recompute expensive multi-join analytics on every request. Gold is also where cohort-relative scores and compare-ready views are prepared.

### Serving solves runtime delivery

The backend does not rebuild analytical logic. Instead, ETL packages certified Gold and selected Silver outputs into serving DuckDB snapshots that the API can load deterministically.

Implementation references:

1. `etl/README.md:5-18`
2. `etl/README.md:102-123`
3. `docs/next-phase-v2/41-patentiq-v2-etl-serving-snapshots-packaging-contract.md:1-117`
4. `etl/src/patentiq_etl/serving/run.py:705-852`

## End-To-End ETL Stage Flow

The ETL runner wires the complete pipeline as named stages. The major flow is:

1. source certification,
2. prebronze extraction planning and export,
3. Bronze generation,
4. scope seeding,
5. Silver core and enrichment,
6. Gold marts,
7. ML and semantic artifact production,
8. serving snapshot packaging,
9. release certification and publish.

This is not merely documentation prose; the stage names are directly registered in the runner.

Implementation references:

1. `etl/scripts/run_stage.py:88-209`
2. `etl/README.md:19-39`

## Scope Definition And Bounded Universe

One of the most important design decisions in PatentIQ is that the warehouse is intentionally bounded. It is not trying to ingest every patent in every field indiscriminately. Instead, the MVP focuses on a selected 10-field mega-cluster and a defined time policy.

### 1. Field scope

The selected WIPO fields are:

1. Audio-visual technology
2. Telecommunications
3. Digital communication
4. Basic communication processes
5. Computer technology
6. IT methods for management
7. Semiconductors
8. Measurement
9. Control
10. Electrical machinery, apparatus, energy

### 2. Time scope

The main operating window is:

1. `2007-2026` for current product analytics

The heritage backfill horizon is:

1. `1996-2006` for older influential families that still matter to historical influence and heritage calculations

### 3. Snapshot policy

The current configured ETL snapshot date is:

1. `2026-03-15`

This date matters because several current-state tables, PIT tables, and serving artifacts are anchored to it.

Implementation references:

1. `etl/conf/scope.yaml:1-14`
2. `etl/conf/build.yaml:2-10`
3. `etl/README.md:15-18`
4. `etl/src/patentiq_etl/common/config.py:36-49`

## Bronze Layer: Source-Preserving Structured Inputs

Bronze is the first durable layer after bounded extraction. It stores source-shaped Parquet outputs such as:

1. PATSTAT application, publication, citation, classification, and person tables,
2. Register procedural and status tables,
3. EPAB abstract and claim tables,
4. external reference tables used later for normalization.

Examples visible in the current repo include:

1. `etl/data/bronze/bronze_patstat_appln.parquet`
2. `etl/data/bronze/bronze_patstat_pat_publn.parquet`
3. `etl/data/bronze/bronze_patstat_citation.parquet`
4. `etl/data/bronze/bronze_patstat_docdb_fam_citn.parquet`
5. `etl/data/bronze/bronze_patstat_inpadoc_legal_event.parquet`
6. `etl/data/bronze/bronze_epab_claims.parquet`
7. `etl/data/bronze/bronze_ext_world_bank_gdp_ppp.parquet`
8. `etl/data/bronze/bronze_ext_kind_code_normalization_seed.parquet`

The business logic deliberately starts in earnest after Bronze, not before. This keeps source certification and later reprocessing manageable.

## Silver Layer: Canonical Analytical Contracts

Silver is the most important engineering layer in the project because it converts raw source tables into a reusable, family-first analytical warehouse.

### 1. Scope seeding builds the bounded universe

`build_scope_seed()` creates four canonical seed tables:

1. `silver_scope_appln_seed`
2. `silver_scope_family_seed`
3. `silver_scope_publn_seed`
4. `silver_scope_owner_seed`

The logic is:

1. prefer direct PATSTAT technology-field mapping when present,
2. otherwise fall back to IPC-to-WIPO concordance,
3. keep only applications inside the selected 10 WIPO fields,
4. collapse those applications into DOCDB families,
5. bridge families to publications and applicant-side persons.

This is the boundary-defining step for the rest of the product. If it is wrong, every downstream family, portfolio, and market metric becomes wrong.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_core.py:218-492`

### 2. `silver_family_core` defines the family anchor contract

`silver_family_core` computes the canonical family identity fields:

1. `family_earliest_priority_date`
2. `family_priority_year`
3. `is_main_window_family`
4. `is_heritage_backfill_family`
5. `family_size_docdb`

Core rules:

1. priority year is extracted from the minimum family priority date,
2. main-window families are priority years between `2007` and `2026`,
3. heritage-backfill families are priority years between `1996` and `2006`.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_core.py:557-576`

### 3. `silver_family_member_publications` normalizes publication-stage evidence

Each in-scope publication is retained with stage flags:

1. `is_application_stage`
2. `is_grant_stage`
3. `is_modifier_stage`

The current default classification is derived from publication-kind prefixes:

1. `A*` application stage,
2. `B*` grant stage,
3. `C*` modifier stage.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_core.py:578-597`

### 4. Owner harmonization is deterministic and family-first

PatentIQ does not expose raw applicant strings directly as the ownership contract. It creates:

1. `silver_family_owner_bridge`
2. `silver_assignee_harmonized`

The harmonized owner key is uppercase, punctuation-cleaned, and underscore-normalized. Primary owner selection within a family is based on application coverage and controlled fallback rules.

This is important because the UI and portfolio analytics need one stable owner key for aggregation, even when raw names vary.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_core.py:69-85`
2. `etl/src/patentiq_etl/silver/build_core.py:87-215`
3. `etl/src/patentiq_etl/silver/build_core.py:401-449`

### 5. Kind-code normalization creates universal legal stages

Office-specific publication kinds are converted into reusable stage semantics in `silver_kind_code_normalization`.

When no curated seed is available, the fallback rules include:

1. `C0` => `UNITARY_GRANT`
2. EP `B2` => `OPPOSITION_SURVIVOR`
3. `B*` => `STANDARD_GRANT`
4. `A*` => `PENDING_APPLICATION`
5. `C*` => `POST_GRANT_MODIFIER`

The same table also defines:

1. `stage_multiplier`
2. `is_enforceable`
3. `legal_status_proxy`

Fallback multipliers currently used in code are:

1. `UNITARY_GRANT = 1.0`
2. `OPPOSITION_SURVIVOR = 3.0`
3. `STANDARD_GRANT = 1.0`
4. `PENDING_APPLICATION = 0.2`
5. `POST_GRANT_MODIFIER = 0.8`

Implementation references:

1. `etl/src/patentiq_etl/silver/build_core.py:599-689`

### 6. WIPO field breadth and field fraction

`silver_family_wipo_fields` converts family classification coverage into a compact field contract:

1. `covered_wipo_fields`
2. `primary_wipo_field`
3. `family_tech_breadth_wipo_count`
4. `family_field_fraction`

The key formula is:

`family_field_fraction = 1 / family_tech_breadth_wipo_count`

This fraction is later used to allocate family-level influence and enforceability across multiple technology fields without double counting.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_core.py:690-707`

### 7. Market weighting converts jurisdiction reach into weighted reach

`silver_tiered_market_weighting` combines market size and IP environment strength.

GDP tier rules are:

1. GDP PPP `>= 5T` => weight `5.0`
2. GDP PPP `>= 1T` => weight `3.0`
3. GDP PPP `>= 100B` => weight `1.0`
4. otherwise => weight `0.2`

The final multiplier is:

`final_market_multiplier = gdp_tier_weight * (ip_score / 100)`

If IP scores are missing, the code defaults to `25.0`. If reference tables are missing entirely, a heuristic office bucket fallback is used.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_core.py:773-901`

### 8. UP expansion and jurisdiction unrolling

`silver_family_jurisdiction_unrolled` expands EP unitary grant coverage into member-state level reach. The expansion rule is triggered by `C0` publication evidence and joined against the UP member-state reference table.

This is important because a unitary grant should not be treated as a single undifferentiated EP row when the business question is market reach.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_core.py:903-1003`

### 9. Legal event ledger and family point-in-time status

PatentIQ creates a unified legal event ledger by combining:

1. publication-derived events,
2. INPADOC legal events,
3. normalized event dates,
4. inferred event types such as grant, lapse, expiry, opposition, and unitary events.

Then `silver_family_status_pt` derives current family status using branch replay logic. The family composite status is:

1. `under_fire`
2. `partially_lapsed`
3. `fully_active`
4. `pending_emerging`
5. `dead`

This is one of the most important contracts in the system because active/lapsed/pending semantics influence coverage, blocking power, forecasts, and UI messaging.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_core.py:1005-1229`
2. `etl/src/patentiq_etl/silver/build_core.py:1232-1305`

### 10. Citation cleaning and enriched citation network

PatentIQ builds multiple citation layers:

1. raw family citation edges,
2. cleaned family citation edges,
3. an enriched citation network with business context.

Cleaning removes:

1. intra-family citations,
2. detectable self-citations based on harmonized owner identity.

The enriched network attaches:

1. citing stage multiplier,
2. citing market multiplier,
3. local or global field trend coefficient,
4. a composite `citation_lethality_score`.

The formula is:

`citation_lethality_score = clean_edge_weight * citing_stage_multiplier * citing_market_multiplier * clipped_trend_coefficient`

where the trend coefficient is clipped into `[0.5, 3.0]`.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_enrichment.py:931-979`
2. `etl/src/patentiq_etl/silver/build_enrichment.py:1127-1236`

### 11. Citation metrics and heritage metrics

`silver_family_citation_metrics` is where raw edge counts become reusable family-level influence indicators.

Important derived metrics include:

1. `family_forward_citations_raw`
2. `family_forward_citations_clean`
3. `family_forward_citations_weighted`
4. `family_fwd_cits5`
5. `family_fwd_cits7`
6. `family_backward_npl_citation_count`
7. `family_science_grounding_score`
8. `family_rcf_score`
9. `family_adjusted_citation_score_raw`

Key formulas:

1. `family_science_grounding_score = ln(1 + family_backward_npl_citation_count)`
2. `family_forward_citations_weighted` is the sum of clean 7-year citation lethality
3. `family_rcf_score = family_forward_citations_weighted / cohort_avg_forward_citations_weighted`
4. the cohort is `family_priority_year + primary_wipo_field`

This is the project’s main heritage and influence backbone. It is later reused in blocking power, heritage summaries, forecasts, and citation UI sections.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_enrichment.py:1241-1408`

### 12. Global and local trend tables

PatentIQ does not treat technology momentum as global only. It creates:

1. `silver_global_tech_trends_timeseries`
2. `silver_local_tech_trends_timeseries`

Each computes growth and a trend coefficient from family counts over time. The coefficient is bounded below at `0.1`.

This is why later scores can distinguish:

1. a field that is globally rising,
2. a field that is specifically rising in a given jurisdiction,
3. a field with weak local evidence, where the code falls back to the global signal.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_enrichment.py:1020-1113`

### 13. Coverage metrics

`silver_family_coverage_metrics` turns geography and status into family-level coverage indicators.

Important outputs:

1. `family_jurisdiction_count`
2. `active_jurisdiction_count`
3. `active_grant_branch_count`
4. `lapsed_jurisdiction_count`
5. `family_market_coverage_weight_raw`
6. `family_coverage_stability_score`

The key stability formula is:

`family_coverage_stability_score = active_jurisdiction_count / family_jurisdiction_count`

Implementation references:

1. `etl/src/patentiq_etl/silver/build_enrichment.py:1491-1531`

### 14. Enforceability and market threat

`silver_family_enforceability_branches` is one of the most important analytical tables in the entire project. It works at family x jurisdiction x field grain and calculates how much enforceable strength a family has in each relevant market/technology slice.

The core contribution formula is:

`branch_enforceability_contribution_raw = branch_stage_multiplier * final_market_multiplier * family_field_fraction * local_or_global_trend_coefficient * active_grant_gate`

Important nuances:

1. active branches get full legal effect,
2. pending branches are down-weighted,
3. unitary grants are handled explicitly,
4. local trend is used when evidence is strong enough,
5. mixed or global fallback is used when local support is thinner.

This table is later rolled up as both legal enforceability and current market threat.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_enrichment.py:1532-1761`

### 15. OECD-style quality layer

`silver_family_oecd_quality` prefers longform OECD indicator artifacts when available. When they are not, the code creates a defensible proxy.

The exact governing note stack for the longform OECD artifact is:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`
2. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`
3. `docs/new-feature-ideas/oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`
4. `docs/new-feature-ideas/oecd-quality-nature-of-innovation-requirements.md`
5. `docs/oecd-patent-quality/oecd-patent-quality-definitions-and-feature-mapping.md`
6. `docs/next-phase-v2/67-patentiq-v2-derived-metric-formula-alignment-audit.md`

These notes match the implemented build order in `oecd_seed.py`:

1. build `oecd_indicator_seed.parquet` as the wide family-level raw base,
2. build `oecd_indicator_cohort_stats.parquet` as the normalization companion,
3. build `oecd_indicator_longform.parquet` as the normalized longform artifact,
4. project that longform artifact into the bounded/Bronze-facing OECD reference contract,
5. pivot the longform artifact into `silver_family_oecd_quality`.

Implementation references:

1. `etl/src/patentiq_etl/prebronze/oecd_seed.py:79-390`
2. `etl/src/patentiq_etl/prebronze/oecd_seed.py:394-484`
3. `etl/src/patentiq_etl/prebronze/oecd_seed.py:487-752`
4. `etl/src/patentiq_etl/silver/build_enrichment.py:34-167`

Proxy formula:

`oecd_quality_proxy_score = family_adjusted_citation_score_raw + 0.5 * family_grant_publication_count + 0.1 * branch_enforceability_contribution_raw`

This is important for interpretation: the system distinguishes between a fully sourced OECD-style indicator and a structured internal proxy when source completeness differs.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_enrichment.py:34-167`
2. `etl/src/patentiq_etl/silver/build_enrichment.py:1836-1885`

### 16. OECD component metrics explicitly carried by the warehouse

Yes, PatentIQ carries more than one OECD-style quality signal. The current Silver OECD mart is designed to preserve multiple component indicators, not just one composite quality value.

More precisely, the project already contains upstream OECD build logic that materializes `etl/data/raw/refs/oecd_indicator_longform.parquet`. When that precomputed longform artifact is present, `silver_family_oecd_quality` pivots it and carries these component metrics into the main Silver quality mart:

1. `family_generality_score`
2. `family_generality_percentile`
3. `family_originality_score`
4. `family_originality_percentile`
5. `family_radicalness_score`
6. `family_radicalness_percentile`
7. `family_backward_npl_citation_count`
8. `family_backward_npl_citation_percentile`
9. `family_science_grounding_score`
10. `family_science_grounding_percentile`
11. `family_fwd_cits5`
12. `family_fwd_cits5_percentile`
13. `family_fwd_cits7`
14. `family_fwd_cits7_percentile`
15. `family_size_docdb`
16. `family_size_percentile`
17. `family_grant_lag_days`
18. `family_grant_lag_speed_percentile`
19. `family_quality_index_4_score`
20. `family_quality_index_4_policy`
21. `family_quality_index_6_score`
22. `family_quality_index_6_policy`

### 16.1 Exact methodology documents for the longform artifact

The most directly relevant design document is:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`

That note explicitly defines:

1. the implemented artifact set, including `oecd_indicator_longform.parquet`,
2. the build inputs,
3. the family-first grain policy,
4. the default indicator set,
5. the cohort-stat normalization layer,
6. the composite-index policy.

The note that fixes the main methodological choices behind those formulas is:

1. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`

That note locks:

1. family-first collapse-before-math behavior,
2. cohort normalization by `family_priority_year x primary_wipo_field`,
3. publication-window logic for `fwd_cits5` and `fwd_cits7`,
4. diversity-metric formulas,
5. family-first composite-index policy,
6. grant-lag inversion during normalization.

The note that most directly explains why the family-first calculation order is mandatory is:

1. `docs/new-feature-ideas/oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`

This note explicitly prohibits:

1. computing generality, originality, or radicalness at patent level and averaging upward,
2. keeping duplicate cross-jurisdiction citation relationships in the citation pool,
3. using simple means as the default portfolio-level OECD rollup.

### 16.2 Exact formulas used in the implemented build

The current implementation in `etl/src/patentiq_etl/prebronze/oecd_seed.py` follows the documented family-first formulas closely.

#### `fwd_cits5`

Definition in notes:

1. count distinct clean forward-citing families whose first clean citation lands within 5 years of the family publication anchor.

Implemented build rule:

1. the family anchor is `family_earliest_publication_date` with fallback to `family_earliest_priority_date`,
2. the build counts clean deduplicated family relationships inside `anchor_date + interval '5 years'`.

Code reference:

1. `etl/src/patentiq_etl/prebronze/oecd_seed.py:137-176`
2. `etl/src/patentiq_etl/prebronze/oecd_seed.py:181-192`
3. `etl/src/patentiq_etl/prebronze/oecd_seed.py:239-247`

Method references:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`
2. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`

#### `fwd_cits7`

Same rule as `fwd_cits5`, but with the 7-year window.

Code reference:

1. `etl/src/patentiq_etl/prebronze/oecd_seed.py:239-247`

Method references:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`
2. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`

#### `generality`

Documented formula:

`generality = 1 - SUM(share_of_forward_citing_field^2)`

Implemented build rule:

1. build the deduplicated forward family pool,
2. group it by the citing family primary WIPO field,
3. compute the inverse concentration score over that field distribution.

Code reference:

1. `etl/src/patentiq_etl/prebronze/oecd_seed.py:248-267`

Method references:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`
2. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`
3. `docs/new-feature-ideas/oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`

#### `originality`

Documented formula:

`originality = 1 - SUM(share_of_backward_cited_field^2)`

Implemented build rule:

1. use only backward patent-family citations,
2. deduplicate at family relationship level,
3. group backward-cited families by their primary WIPO field,
4. compute the same inverse concentration score over that field distribution.

Code reference:

1. `etl/src/patentiq_etl/prebronze/oecd_seed.py:197-213`
2. `etl/src/patentiq_etl/prebronze/oecd_seed.py:268-287`

Method references:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`
2. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`
3. `docs/new-feature-ideas/oecd-family-first-calculation-and-portfolio-hit-rate-requirements.md`

#### `radicalness`

Documented default formula:

`outside_field_backward_share = backward_cited_families_outside_field_set / all_deduplicated_backward_cited_families`

Implemented build rule:

1. compare each backward-cited family field against the focal family field set,
2. score `0.0` when the cited field is inside the focal field set,
3. score `1.0` when it is outside,
4. take the average over the deduplicated backward family pool.

In implementation terms, this average is the outside-field backward share.

Code reference:

1. `etl/src/patentiq_etl/prebronze/oecd_seed.py:288-303`

Method references:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`
2. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`
3. `docs/new-feature-ideas/oecd-quality-nature-of-innovation-requirements.md`

#### `grant_lag`

Documented rule:

1. compute family-level grant lag from granted member evidence at family grain,
2. then normalize it against the family cohort,
3. invert the normalization so faster grants score higher.

Implemented raw formula:

`grant_lag_days = MIN(publn_date - appln_filing_date)` across granted family members

The build only considers publications whose normalized universal stage is one of:

1. `STANDARD_GRANT`
2. `OPPOSITION_SURVIVOR`
3. `UNITARY_GRANT`

Then, during longform normalization, `grant_lag` is inverted by ordering on negative raw value and by using the reversed z-score formula.

Code reference:

1. `etl/src/patentiq_etl/prebronze/oecd_seed.py:216-233`
2. `etl/src/patentiq_etl/prebronze/oecd_seed.py:530-537`

Method references:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`
2. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`

#### `quality_index_4`

Documented current family-first policy:

1. use normalized `fwd_cits5`,
2. normalized `family_size`,
3. normalized `generality`,
4. omit claims and label the omission explicitly.

Implemented formula:

`quality_index_4 = mean(percentile_rank(fwd_cits5), percentile_rank(family_size), percentile_rank(generality))`

This is marked with:

1. `is_proxy = true`
2. `component_policy = 'claims_omitted_family_first_variant'`

Code reference:

1. `etl/src/patentiq_etl/prebronze/oecd_seed.py:609-639`

Method references:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`
2. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`
3. `docs/next-phase-v2/67-patentiq-v2-derived-metric-formula-alignment-audit.md`

#### `quality_index_6`

Documented current family-first policy:

1. start from the current `quality_index_4` family-first variant logic,
2. add normalized `bwd_cits`,
3. add normalized `grant_lag`,
4. keep the claims omission explicit.

Implemented formula:

`quality_index_6 = mean(percentile_rank(fwd_cits5), percentile_rank(family_size), percentile_rank(generality), percentile_rank(bwd_cits), percentile_rank(grant_lag))`

This is also marked with:

1. `is_proxy = true`
2. `component_policy = 'claims_omitted_family_first_variant'`

Code reference:

1. `etl/src/patentiq_etl/prebronze/oecd_seed.py:641-677`

Method references:

1. `docs/new-feature-ideas/oecd-indicator-seed-build-spec.md`
2. `docs/new-feature-ideas/oecd-indicator-seed-method-review-and-design.md`
3. `docs/next-phase-v2/67-patentiq-v2-derived-metric-formula-alignment-audit.md`

So the lineage is:

1. upstream OECD indicator build stages compute and materialize the longform artifact,
2. `silver_family_oecd_quality` pivots that artifact into the canonical Silver family-quality contract,
3. Gold marts then carry selected quality fields forward into backend- and UI-facing outputs.

This means the project architecture distinguishes between:

1. component indicators, such as originality or radicalness,
2. percentile-normalized versions of those indicators,
3. composite quality indices, such as quality-index-4 and quality-index-6,
4. a final promoted quality field used by downstream marts, currently `oecd_quality_percentile`.

This is important because it shows that PatentIQ does not reduce patent quality to one opaque number. Instead, it preserves multiple interpretable dimensions and only then derives a promoted quality signal for downstream consumption.

At the current documentation stage, Section 01 establishes that these metrics exist in the lineage and where they enter the Silver and Gold warehouse. In later sections, they should be mapped in more detail to:

1. backend response payloads,
2. UI cards, tables, and tooltips,
3. methodology disclosures,
4. any narrative explanations shown to end users.

Implementation references:

1. `etl/src/patentiq_etl/silver/build_enrichment.py:49-110`
2. `etl/src/patentiq_etl/gold/build_gold.py:1053-1065`
3. `etl/src/patentiq_etl/prebronze/oecd_seed.py:487-686`

## Gold Layer: Product Marts Used By Backend And UI

Gold converts Silver contracts into product-facing marts. This is the layer most closely tied to what appears in the UI and the backend APIs.

### 1. `gold_family_summary`

`gold_family_summary` is the canonical current family profile mart. It merges:

1. family anchors,
2. owner summary,
3. WIPO field summary,
4. family status,
5. coverage summary,
6. OECD/quality summary,
7. semantic eligibility flags.

This is the main current-state family record used by downstream pages and derived marts.

Implementation references:

1. `etl/src/patentiq_etl/gold/build_gold.py:1040-1078`

### 2. `gold_family_blocking_power`

This mart contains the project’s headline competitive-strength score. The raw blocking score is built from four ideas:

1. legal gate,
2. current market threat,
3. historical citation heritage,
4. technology breadth bonus.

Constants defined in code:

1. market weight = `0.65`
2. citation weight = `0.35`
3. pending-stage gate = `0.15`
4. breadth step = `0.05`
5. breadth max bonus = `0.15`

Formula:

`family_raw_absolute_blocking_power = stage_gate * ((market_threat_score_raw * 0.65) + (ln(1 + citation_raw) * 0.35)) * breadth_multiplier`

where:

1. `stage_gate = 1.0` if the family has any active grant,
2. `stage_gate = 0.15` if the family is only `pending_emerging`,
3. otherwise the gate is `0.0`,
4. `breadth_multiplier = min(1.15, 1 + max(breadth - 1, 0) * 0.05)`.

The UI-facing score is not raw. It is cohort-relative:

`family_ui_blocking_power_score = percent_rank within primary_wipo_field * 100`

This distinction is essential:

1. raw blocking power is additive and used in portfolio mass calculations,
2. UI blocking power is percentile-based and used for readable within-field comparisons.

Implementation references:

1. `etl/src/patentiq_etl/gold/build_gold.py:55-101`
2. `etl/src/patentiq_etl/gold/build_gold.py:1100-1141`

### 3. Historical blocking and PIT-safe comparison marts

PatentIQ also materializes historical-safe blocking and compare layers rather than pretending that only today’s state matters. The blocking timeseries and compare PIT marts reconstruct family condition by year using legal history, citation accumulation, and point-in-time feature replay.

Implementation references:

1. `etl/src/patentiq_etl/gold/build_gold.py:1389-1458`
2. `etl/src/patentiq_etl/gold/build_gold.py:2760-2872`
3. `etl/src/patentiq_etl/silver/build_pit.py:1147-1261`

### 4. `gold_portfolio_summary`

Portfolio summary is not a simple count of owned families. It aggregates family-level competitive strength into owner-level portfolio intelligence.

Important derived metrics include:

1. `portfolio_family_count_within_mega_cluster`
2. `portfolio_avg_blocking_power_within_mega_cluster`
3. `portfolio_active_grant_family_count`
4. `semantic_candidate_family_count`
5. `portfolio_total_mass_score`
6. `portfolio_hit_rate_top_decile`
7. `portfolio_crown_jewel_index`
8. `portfolio_opposition_rate`
9. `portfolio_current_threat_score`
10. `portfolio_heritage_score`

Key formulas:

1. `portfolio_avg_blocking_power_within_mega_cluster = avg(family_ui_blocking_power_score)`
2. `portfolio_total_mass_score = sum(active family raw blocking power)`
3. `portfolio_hit_rate_top_decile = share of family_ui_blocking_power_score >= 90`
4. `portfolio_crown_jewel_index = sum(raw blocking power of top 10 active families by owner)`
5. `portfolio_current_threat_score = sum(active family market threat score)`
6. `portfolio_heritage_score = sum(family_adjusted_citation_score_raw)`

This is why portfolio cards in the UI can meaningfully distinguish size, concentration, strength, and heritage instead of showing one-dimensional counts only.

Implementation references:

1. `etl/src/patentiq_etl/gold/build_gold.py:849-853`
2. `etl/src/patentiq_etl/gold/build_gold.py:2213-2275`

### 5. Market intelligence Gold marts

PatentIQ creates market-facing marts rather than only family and owner marts. These include:

1. `gold_market_intelligence_overview`
2. `gold_market_intelligence_segments`
3. `gold_market_intelligence_timeseries`
4. `gold_market_citation_trend_pit`
5. `gold_market_citation_pressure_by_jurisdiction_pit`
6. `gold_market_attacker_leaderboard_pit`

One clear example of a ranking metric is the market attacker pressure index:

`attacker_pressure_index = percent_rank within (year, wipo_field) ordered by citation_lethality_sum_raw * 100`

This turns the enriched citation network into competitive-attacker views at market level.

Implementation references:

1. `etl/src/patentiq_etl/gold/build_gold.py:2545-2591`

### 6. Semantic context mart

`gold_semantic_match_context` prepares family-level semantic metadata for later retrieval, compare, and explainability use. It joins:

1. representative text provenance,
2. semantic eligibility,
3. owner metadata,
4. covered WIPO fields,
5. blocking score,
6. OECD quality percentile.

This design shows that semantic search is not isolated from the rest of the analytics stack. Semantic retrieval is anchored back to family identity, legal/business strength, and field context.

Implementation references:

1. `etl/src/patentiq_etl/gold/build_gold.py:2594-2619`

## Serving Snapshots: Backend-Ready Delivery Layer

After Gold marts are built, ETL packages runtime artifacts into three serving DuckDB databases:

1. `core_serving.duckdb`
2. `semantic_serving.duckdb`
3. `market_serving.duckdb`

It also writes:

1. `serving_snapshot_manifest.json`
2. `serving_snapshot_audit.json`

The serving layer exists so the backend can consume stable, certified snapshots rather than reconstructing analytics logic at request time.

The snapshot builder explicitly packages:

1. family summary and blocking marts,
2. portfolio summary and forecast marts,
3. semantic match context,
4. market intelligence marts,
5. derived serving tables such as `family_compare_current_serving` and `publication_evidence_serving`.

Implementation references:

1. `etl/src/patentiq_etl/serving/run.py:696-852`
2. `backend_v2/README.md:54-83`

## Why Bronze, Silver, And Gold Are Necessary In This Project

For this project, the layered model is not optional.

### Bronze is necessary because the source systems are heterogeneous

PATSTAT, Register, EPAB, and external reference files have different semantics, schemas, and granularity. The project needs a recoverable source-preserving layer before any business interpretation happens.

### Silver is necessary because the business logic is cross-source

The key analytics in PatentIQ are not stored in any one source system:

1. family status requires publications plus legal events plus jurisdiction replay,
2. blocking power requires legal enforceability plus market weighting plus citation heritage,
3. portfolio intelligence requires owner harmonization plus family-level scores,
4. market intelligence requires field, geography, and citation aggregation,
5. ML features require stable analytical contracts, not raw source tables.

### Gold is necessary because the product is page-shaped

The backend and frontend need:

1. family overview payloads,
2. portfolio overview payloads,
3. market overview payloads,
4. compare-ready and PIT-safe slices,
5. runtime-friendly query surfaces.

Gold precomputes these so request latency, consistency, and traceability remain manageable.

### Serving is necessary because runtime and build responsibilities must stay separate

The ETL owns data shaping and certification. The backend owns request handling. This separation is critical for auditability and reproducibility.

## Key Takeaways

1. PatentIQ is built on a bounded but deeply structured patent intelligence warehouse, not on ad hoc dashboard queries.
2. The data lineage is explicit from source mode configuration through Bronze, Silver, Gold, and serving outputs.
3. The most important product metrics are formula-driven and code-cited, especially market weighting, citation influence, legal status, enforceability, quality, and blocking power.
4. The backend and UI are downstream consumers of these contracts, not the place where the core analytical logic is invented.
5. Because the data analytics layer is formalized this way, every chart, card, table, and API response can be traced back to a specific parquet contract and, when needed, to the underlying computation code.

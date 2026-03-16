# PatentIQ V2 Stage Stats And Data Consistency Audit Contract

## Purpose

Define the ETL-side record mechanism that captures stage-by-stage proof metrics so the team can:

1. verify that the raw bounded universe looks correct before downstream builds,
2. detect where data inconsistency appears when a later stage fails,
3. compare counts and coverage across releases,
4. support Data Room transparency and internal debugging.

## Core Rule

Every meaningful ETL stage should emit:

1. a structured stage manifest,
2. a human-readable journal entry,
3. a stage stats snapshot.

The stage stats snapshot is the machine-readable proof artifact for:

1. counts,
2. coverage,
3. bridge health,
4. output artifact profiles.

## Output Location

Stage stats snapshots should be written under:

`etl/manifests/stats/`

Recommended naming:

1. `source-certification.json`
2. `bronze.json`
3. `scope.json`
4. `silver-core.json`
5. `silver-enrichment.json`
6. `silver-semantic.json`
7. `gold.json`
8. `ml.json`
9. `semantic.json`
10. `release-certification.json`
11. `publish.json`

## Minimum Stats Payload

Each stage stats JSON should contain:

1. `stage`
2. `status`
3. `summary`
4. `started_at`
5. `finished_at`
6. `metrics`
7. `warnings`
8. `downstream_impacts`
9. `output_profiles`

Each `output_profile` should contain:

1. `path`
2. `exists`
3. `size_bytes`
4. `sha256`
5. `row_count` where parquet
6. `column_count` where parquet

## Metrics That Matter By Stage

## Stage 1: Source Certification

Must record:

1. total input file count
2. file count by source family
3. required-column availability warnings
4. selected WIPO field representability
5. field-level application counts for the 10 selected fields

These metrics prove that the bounded mega-cluster can actually be built before Bronze begins.

## Stage 2: Bronze

Must record:

1. row count for every Bronze parquet table
2. total Bronze row count
3. total parsed row count for USPTO Bronze
4. total parsed row count for EPAB Bronze
5. for USPTO local ODP extraction, per-file counts for:
   - weekly ZIPs discovered
   - weekly ZIPs downloaded
   - publication documents seen
   - publication documents matched
   - publication documents discarded
   - bytes downloaded and bytes deleted after cleanup

These metrics prove that the bounded raw landing completed and that the text-provider side is not silently empty.

## Stage 3: Scope Seed

Must record:

1. total in-scope application count
2. total in-scope family count
3. total in-scope publication count
4. total in-scope owner count
5. application count per selected WIPO field
6. family count per selected WIPO field
7. publication count per selected WIPO field

These metrics prove that every selected field survived the bounded-scope cut and that the universe is not collapsing unexpectedly.

## Stage 4: Silver Citation / Market / Enrichment

Must record:

1. citation edge count
2. unique source publication count
3. unique cited publication count
4. unique source family count
5. unique cited family count
6. row counts for citation, trend, coverage, enforceability, OECD, and Market Intelligence Silver tables

These metrics prove that citation logic is wired and that family-level graph support exists for blocking power and OECD-style overlays.

## Stage 5: Silver Semantic

Must record:

1. representative family text row count
2. semantic eligibility row count
3. abstract fallback incidence if available

These metrics prove that semantic payload generation can proceed and that the claim/abstract fallback hierarchy is working.

## Stage 6: Gold

Must record:

1. family summary row count
2. blocking power row count
3. portfolio summary row count
4. Market Intelligence overview and segment row counts
5. semantic context row count

These metrics prove that page-facing marts are aligned to the bounded family universe and ready for the application layer.

## Recommended Consistency Checks

The ETL should make it easy to compare these invariants across stage stats snapshots:

1. `scope_family_count` should align with `gold_family_summary_rows`
2. `scope_owner_count` should not collapse unexpectedly before `gold_portfolio_summary_rows`
3. selected-field family counts should remain non-zero through Market Intelligence outputs
4. `citation_unique_source_family_count` should be materially compatible with `scope_family_count`
5. `silver_family_text_representative_rows` should not exceed `silver_semantic_sampling_eligibility_rows`

## Failure Localization

When a downstream stage fails, the stats snapshots should make it clear whether the issue began in:

1. raw source absence,
2. bounded scope seeding,
3. family/publication bridging,
4. citation edge retention,
5. EP Register overlay extraction,
6. semantic payload generation,
7. Gold aggregation.

## Relationship To The Journal

The markdown ETL journal should remain the narrative audit trail.

The JSON stage stats files should remain the machine-readable proof layer.

The journal may link to the stats snapshot path for each stage, but the stats payload must remain independently useful for diagnostics and release validation.

## Done Criteria

The audit contract is considered implemented when:

1. every major ETL stage writes a stats snapshot,
2. the snapshot includes both stage metrics and output artifact profiles,
3. key bounded-universe counts are present at source certification, Bronze, scope, and Silver enrichment,
4. failures can be localized by comparing stage stats rather than re-reading all raw data manually.

# PatentIQ V2 TIP Chunked Full-Scope Execution Plan

## Purpose

Define how PatentIQ should execute the full 10-field mega-cluster extraction when the EPO Technology Intelligence Platform (`TIP`) is the source runtime and the environment is constrained to approximately:

1. `4 CPU cores`
2. `32 GB RAM`
3. `30 GB local storage`

This document exists because the full bounded raw universe is too large to materialize and hold locally inside TIP in one monolithic `prebronze` run.

## Core Decision

TIP must be treated as:

`a bounded extraction worker with immediate Blob offload`

Not as:

`the place where the full bounded raw layer or full Bronze/Silver/Gold warehouse is stored`

## Why The Current Monolithic Shape Does Not Fit TIP

The current ETL shape is appropriate for a stronger local machine, but not for the constrained TIP environment because:

1. the 10-field PATSTAT seed is very large,
2. citation retention with ghost-node support is the main storage and memory driver,
3. EPAB and Register overlays add additional bounded raw material,
4. the full `raw-bounded` layer can exceed both available local disk and safe in-memory DataFrame handling.

## TIP Operating Model

The correct TIP execution model is:

1. use TIP clients to build the bounded mega-cluster seed,
2. split the full extraction into many deterministic chunks,
3. write one chunk locally,
4. validate row counts and chunk metadata,
5. upload the chunk immediately to Azure Blob / ADLS,
6. delete local chunk files,
7. keep only small manifests and logs on TIP.

The current ETL runtime implements this conservatively:

1. global main-horizon chunk parallelism defaults to `2`,
2. heritage chunk parallelism defaults to `1`,
3. family-level concurrency follows the configured worker caps,
4. Azure uploads stay file-by-file but use bounded multipart tuning and small upload concurrency,
5. live execution emits both human-readable logs and JSONL event streams while chunks are still running.

That means the true intermediate store is:

`Azure Blob / ADLS`

Not:

`TIP local disk`

## Full-Scope Execution Architecture

### Phase 1: Global Seed Build

Run once in TIP:

1. build `seed_appln_ids`
2. build `seed_family_ids`
3. build `seed_publn_ids`
4. build `seed_person_ids`
5. build `seed_ep_appln_ids`
6. build `seed_ep_publication_numbers`
7. build `seed_us_publication_numbers`
8. write seed stats and field counts
9. upload seeds to Blob

These seed artifacts are comparatively small and should remain available both:

1. locally in TIP during the run
2. in Blob as the authoritative scope reference

### Phase 2: Chunked Bounded Raw Export

Run chunk families iteratively from TIP and upload them immediately.

For the two-horizon model:

1. run the main operating-window export first,
2. run the separate `heritage` chunk plan for the `1996-2006` backfill horizon,
3. keep the heritage export lighter by default, focused on `core`, `publications`, and `citations`.

### Phase 3: Consolidation Outside TIP

After chunk export completes, a stronger environment should:

1. merge or read chunked bounded raw artifacts from Blob
2. run Bronze normalization and certification
3. run Silver
4. run Gold
5. package ML and semantic artifacts

TIP is therefore:

`source extraction infrastructure`

while the stronger machine is:

`warehouse consolidation infrastructure`

## Chunk Key Design

Each extraction job should be defined by:

1. `field`
2. `year bucket`
3. `table family`

Example chunk ids:

1. `computer-technology__2018_2020__core`
2. `computer-technology__2018_2020__publications`
3. `computer-technology__2018_2020__citations`
4. `semiconductors__2021_2023__register`

## Recommended Year Buckets

Use `2-year` or `3-year` buckets.

Recommended default:

1. `2007-2009`
2. `2010-2012`
3. `2013-2015`
4. `2016-2018`
5. `2019-2021`
6. `2022-2024`
7. `2025-2026`

These buckets are small enough to:

1. reduce memory pressure,
2. reduce local parquet staging size,
3. make retries cheap,
4. expose where extraction instability happens.

## Table Families

### 1. `seed`

Run once globally.

Artifacts:

1. `seed_appln_ids`
2. `seed_family_ids`
3. `seed_publn_ids`
4. `seed_person_ids`
5. `seed_ep_appln_ids`
6. `seed_ep_publication_numbers`
7. `seed_us_publication_numbers`
8. `seed_family_field_counts`

### 2. `core`

Export together:

1. `tls201_appln`
2. `tls202_appln_title`
3. `tls203_appln_abstr`
4. `tls204_appln_prior`
5. `tls206_person`
6. `tls207_pers_appln`
7. `tls209_appln_ipc`
8. `tls216_appln_contn`
9. `tls224_appln_cpc`
10. `tls230_appln_techn_field`

### 3. `publications`

Export:

1. `tls211_pat_publn`
2. USPTO bulk XML reduced to only the publication-level documents whose `publication_number_full` belongs to the same field/year chunk

### 4. `legal`

Export:

1. `tls231_inpadoc_legal_event`
2. `tls803_legal_event_code`

### 5. `register`

EP-only bounded export:

1. `reg101_appln`
2. `reg403_appln_status`
3. `reg107_parties`
4. `reg111_licensee`
5. `reg125_appeal`
6. `reg130_opponent`
7. `reg201_proc_step`
8. `reg202_proc_step_text`
9. `reg203_proc_step_date`
10. `reg301_event_data`
11. `reg402_event_text`
12. `reg701_appln`
13. `reg731_event_data`
14. `reg741_appln_status`
15. `reg742_event_text`

### 6. `epab`

EP-only bounded export:

1. publication
2. application
3. abstract
4. claims
5. pct
6. designated states
7. priority links
8. parent links
9. divisional links
10. applicants
11. inventors
12. representative

### 7. `citations`

Keep separate because this is the size driver.

Export:

1. `tls212_citation`
2. `tls214_npl_publn`
3. `tls228_docdb_fam_citn`

## Blob Layout

Use a deterministic chunk-aware layout:

```text
blob://patentiq-data/
  raw-bounded/
    seeds/
      seed_appln_ids.parquet
      seed_family_ids.parquet
      seed_publn_ids.parquet
      seed_person_ids.parquet
      seed_ep_appln_ids.parquet
      seed_ep_publication_numbers.parquet
      seed_us_publication_numbers.parquet
      seed_family_field_counts.parquet
      manifest.json

    refs/
      bronze_ref_techn_field_ipc.parquet
      bronze_ext_iso_country_map.parquet
      ...

    patstat/
      field=computer-technology/year=2018-2020/family=core/
      field=computer-technology/year=2018-2020/family=publications/
      field=computer-technology/year=2018-2020/family=legal/
      field=computer-technology/year=2018-2020/family=citations/

    uspto/
      field=computer-technology/year=2018-2020/family=publications/
      field=semiconductors/year=2021-2023/family=publications/

    register/
      field=computer-technology/year=2018-2020/
      field=semiconductors/year=2021-2023/

    epab/
      field=computer-technology/year=2018-2020/
      field=semiconductors/year=2021-2023/
```

## Chunk Manifest Contract

Every chunk must emit one manifest JSON.

Required fields:

1. `chunk_id`
2. `field`
3. `year_start`
4. `year_end`
5. `table_family`
6. `status`
7. `row_counts`
8. `seed_counts`
9. `uploaded_blobs`
10. `warnings`
11. `started_at`
12. `finished_at`

Example:

```json
{
  "chunk_id": "computer-technology__2018_2020__core",
  "field": "Computer technology",
  "year_start": 2018,
  "year_end": 2020,
  "table_family": "core",
  "status": "success",
  "row_counts": {
    "tls201_appln": 123456,
    "tls202_appln_title": 120111
  },
  "seed_counts": {
    "appln_ids": 123456,
    "family_ids": 84500
  },
  "uploaded_blobs": [
    "raw-bounded/patstat/field=computer-technology/year=2018-2020/family=core/tls201_appln.parquet"
  ],
  "warnings": [],
  "started_at": "2026-03-16T10:00:00Z",
  "finished_at": "2026-03-16T10:18:00Z"
}
```

## Resume And Retry Rules

Chunk processing must be idempotent.

Rules:

1. one chunk writes one manifest,
2. `success` chunks are skipped on rerun,
3. `failed` chunks are rerun independently,
4. uploaded blob paths are deterministic,
5. local output cleanup runs only after upload verification completes.
6. USPTO chunk extraction must filter publication documents inside each bulk XML file rather than copying whole bulk files when only part of the file is in scope.

Supported statuses:

1. `pending`
2. `running`
3. `success`
4. `failed`
5. `degraded`

## Resource-Aware Scheduler For TIP

TIP provides approximately:

1. `4 CPU cores`
2. `32 GB RAM`
3. `30 GB local disk`

This means the scheduler must be:

`CPU-aware but memory-conservative`

### Safe Default Concurrency

Recommended defaults:

1. `2 workers` for `core`
2. `2 workers` for `publications`
3. `1 worker` for `legal`
4. `1 worker` for `register`
5. `1 worker` for `epab`
6. `1 worker` for `citations`

Do not run 4 heavy extraction jobs in parallel by default.

The implemented runtime currently applies:

1. `tip_max_parallel_chunks = 2`
2. `heritage_max_parallel_chunks = 1`
3. per-family caps from the configured `max_workers` map
4. upload tuning through:
   - `upload_max_concurrency`
   - `upload_max_block_size_mb`
   - `upload_max_single_put_size_mb`
5. live runtime files:
   - `etl/manifests/stages/pre-bronze-chunked-export.log`
   - `etl/manifests/stages/pre-bronze-chunked-export.events.jsonl`

### Why

The bottleneck is not CPU. The bottlenecks are:

1. DataFrame memory,
2. local parquet staging size,
3. citation fan-out,
4. upload buffers.

### Local Safety Limits

Recommended operational limits:

1. target `<= 4 GB` output per chunk before upload
2. target `<= 4-6 GB` in-memory DataFrame footprint per worker
3. keep `<= 20 GB` total local temporary usage across active jobs
4. upload and delete immediately after each chunk

## Execution Order

### Pass 1

Run once:

1. `refs`
2. `seed`

### Pass 2

For each field and year bucket:

1. `core`
2. `publications`
3. the `publications` chunk emits both PATSTAT publication rows and any matching USPTO publication documents for the same chunk

### Pass 3

For each field and year bucket:

1. `legal`
2. `register`
3. `epab`

### Pass 4

For each field and year bucket:

1. `citations`

Run citations last because they are the heaviest and easiest to isolate if they fail.

## Local Cleanup Rule

For each chunk:

1. write local parquet or filtered XML,
2. validate row counts,
3. upload to Blob,
4. write manifest,
5. delete local chunk outputs,
6. keep only logs and manifests.

TIP local disk should never be treated as a durable artifact store.

## First Production Rollout

Do not begin with the full mega-cluster simultaneously.

Recommended rollout:

1. `Computer technology / 2018-2020 / core`
2. `Computer technology / 2018-2020 / publications`
3. `Computer technology / 2018-2020 / register`
4. `Computer technology / 2018-2020 / epab`
5. `Computer technology / 2018-2020 / citations`

After that succeeds:

1. expand to more year buckets,
2. then expand to more fields,
3. keep citations as the final scaling stage.

## ETL Changes Required

The current ETL should gain a dedicated `TIP batch export mode` with:

1. chunk planner by field and year bucket,
2. table-family runners,
3. upload-after-write behavior,
4. chunk manifests,
5. resume support,
6. local cleanup-after-upload,
7. per-family concurrency settings.

## Final Rule

For the full PatentIQ mega-cluster scope:

`TIP performs extraction and bounded offload; Azure Blob stores the intermediate bounded raw universe; a stronger environment performs heavy consolidation and downstream warehouse generation.`

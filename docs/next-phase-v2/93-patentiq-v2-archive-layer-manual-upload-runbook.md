# PatentIQ V2 Archive Layer Manual Upload Runbook

## Purpose

This runbook covers the archive-only migration of the local ETL layers:

- `bronze/`
- `silver/`
- `gold/`

These are rebuild/archive layers, not runtime layers. They should upload to immutable top-level archive prefixes, not into `releases/<release_id>/...`.

## Current Local State

As of April 27, 2026, the local archive layers are approximately:

- `bronze`: `25 GiB`, `42` files
- `silver`: `24 GiB`, `220` files
- `gold`: `33 GiB`, `965` files

Total archive payload:

- about `82 GiB`
- about `1227` files

## Blob Naming Contract

Archive layers should upload under stable top-level prefixes:

```text
bronze/<archive_id>/...
silver/<archive_id>/...
gold/<archive_id>/...
```

This keeps archive/rebuild material separate from:

- runtime releases: `releases/<release_id>/...`
- bounded pre-bronze intermediates: `raw-bounded/...`

## Generator

Generate the archive plan with:

```bash
python etl/scripts/prepare_archive_upload_plan.py --etl-root etl --archive-id <archive_id>
```

Outputs:

```text
etl/manifests/archives/<archive_id>/
  archive-upload-plan.json
  archive-summary.json
```

The generated plan includes:

- per-layer blob prefixes
- per-layer file counts and bytes
- per-file blob paths and byte sizes for later verification

## Upload Script

Use the repo script:

```bash
PATENTIQ_AZCOPY_BIN="/opt/homebrew/bin/azcopy" \
AZURE_STORAGE_CONNECTION_STRING="<secret>" \
PATENTIQ_ETL_PYTHON="/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/.venv-seed-backfill/bin/python" \
etl/scripts/upload_archive_layers_with_azcopy.sh \
  --archive-id <archive_id>
```

Resume from a later layer if needed:

```bash
etl/scripts/upload_archive_layers_with_azcopy.sh \
  --archive-id <archive_id> \
  --start-at silver
```

Supported resume points:

- `bronze`
- `silver`
- `gold`

## Recommended Transfer Tuning

For the currently improved uplink, the default archive tuning is:

- `PATENTIQ_AZCOPY_DIR_BLOCK_SIZE_MB=32`
- `PATENTIQ_AZCOPY_DIR_CONCURRENCY=32`
- `PATENTIQ_AZCOPY_PUT_BLOB_SIZE_MB=128`
- `PATENTIQ_AZCOPY_BUFFER_GB=8`

These defaults are intended for recursive directory upload with a mix of many medium files and several large parquet files.

## Verification

After upload, verify by:

1. exact blob path count
2. exact total bytes
3. per-file size comparison for all planned files

The generated `archive-upload-plan.json` contains the per-file `blob_path`, `source_path`, and `bytes` values needed for that comparison.

## Important Runtime Note

Archive upload can happen independently of the active runtime release.

However, a Blob-backed local runtime bootstrap is **not currently safe on this machine** because local free space is too low. The current repo volume has only a few GiB free, while a Blob-backed runtime hydration would need roughly another `110 GiB` for Docker volumes on the same disk.

So the correct order is:

1. archive upload plan and archive migration
2. optionally delete/archive local non-runtime layers only after verification
3. only attempt a local Blob-backed runtime bootstrap after enough disk headroom exists

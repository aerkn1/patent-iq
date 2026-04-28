# PatentIQ V2 Runtime Release Manual Upload Runbook

## Purpose

This runbook covers the pragmatic path for the current repo state:

- generate a runtime-only release manifest without staging a full local release,
- upload the current runtime artifacts to Blob under one immutable `releases/<release_id>/...` prefix,
- update `manifests/active_release.json` only after the runtime payload is complete,
- keep `publication_serving/` as the current directory artifact.

This path is intended for the current transition where:

- `serving/`, `vectors/`, and `ml/` are the runtime layers,
- `bronze/`, `silver/`, and `gold/` are archive/rebuild layers,
- local and Azure both bootstrap from the same runtime release contract.

## Generator

Generate the runtime manifest, active pointer payload, and upload plan with:

```bash
etl/.venv/bin/python etl/scripts/prepare_runtime_release.py --etl-root etl --release-id <release_id>
```

Outputs are written to:

```text
etl/manifests/releases/<release_id>/
  release-manifest.json
  active_release.json
  runtime-upload-plan.json
```

Use `--activate-local-pointer` only if you also want to switch the local Docker bootstrap to the generated release immediately.

## What Gets Uploaded

The runtime release uploads to:

```text
releases/<release_id>/
  release-manifest.json
  serving/
  vectors/
  models/
```

The current runtime contract intentionally keeps:

- `serving/publication_serving/` as a directory artifact
- `models/` as the current full `etl/data/ml` directory

The active pointer uploads separately to:

```text
manifests/active_release.json
```

## Upload Order

1. Upload the runtime payload under `releases/<release_id>/...`
2. Verify counts and bytes against `runtime-upload-plan.json`
3. Upload `manifests/active_release.json` last
4. Only after runtime boot works should archive layers be uploaded:
   - `bronze/`
   - `silver/`
   - `gold/`

## Recommended Verification

Before activation:

- `release-manifest.json` exists in Blob
- all planned `serving/` files exist
- all planned `vectors/` files exist
- all planned `models/` files exist

After activation:

- local `docker compose` with `PATENTIQ_BOOTSTRAP_SOURCE_MODE=azure_blob` resolves the same release
- Azure Container Apps init container hydrates `/artifacts/current`
- backend logs show `/artifacts/current/serving`
- frontend logs show the intended API URL

## AzCopy Upload Script

Use the repo script:

```bash
PATENTIQ_BLOB_ACCOUNT_URL="https://patentiq.blob.core.windows.net" \
PATENTIQ_BLOB_CONTAINER="patentiq-data" \
PATENTIQ_BLOB_SAS="?<container-sas>" \
etl/scripts/upload_runtime_release_with_azcopy.sh \
  --release-id <release_id>
```

Activate only after verification:

```bash
PATENTIQ_BLOB_ACCOUNT_URL="https://patentiq.blob.core.windows.net" \
PATENTIQ_BLOB_CONTAINER="patentiq-data" \
PATENTIQ_BLOB_SAS="?<container-sas>" \
etl/scripts/upload_runtime_release_with_azcopy.sh \
  --release-id <release_id> \
  --activate
```

The script uploads in this order:

1. serving manifests
2. `market_serving.duckdb`
3. `semantic_serving.duckdb`
4. `core_serving.duckdb`
5. `publication_serving/`
6. runtime vectors + `ann/`
7. `models/`
8. `analytics_serving.duckdb`
9. `release-manifest.json`
10. `active_release.json` only when `--activate` is used

## Recommended Transfer Tuning

These defaults are tuned for the current device/network profile and are an operational recommendation, not a protocol guarantee:

- large single-file uploads:
  - `PATENTIQ_AZCOPY_LARGE_BLOCK_SIZE_MB=32`
  - `PATENTIQ_AZCOPY_LARGE_CONCURRENCY=8`
- recursive directory uploads:
  - `PATENTIQ_AZCOPY_DIR_BLOCK_SIZE_MB=16`
  - `PATENTIQ_AZCOPY_DIR_CONCURRENCY=16`
- single-put threshold:
  - `PATENTIQ_AZCOPY_PUT_BLOB_SIZE_MB=32`

Why:

- the uplink is roughly `8.8 Mbps`, so very large block sizes would make retries too expensive on the largest blobs
- `32 MiB` blocks are a practical balance for `analytics_serving.duckdb` and `core_serving.duckdb`
- `publication_serving/` contains many smaller shard files, so lower block size plus higher directory concurrency is a better fit
- `--overwrite=false` and AzCopy plan/log files reduce restart risk on long uploads

The script persists AzCopy state under:

```text
etl/manifests/releases/<release_id>/azcopy/
  logs/
  plans/
```

## Current Caveat

The current runtime manifest preserves the existing `models/` directory contract. That means the runtime upload plan may still include non-runtime ML leftovers present under `etl/data/ml`. This is deliberate for now to avoid accidentally omitting artifacts during bring-up.

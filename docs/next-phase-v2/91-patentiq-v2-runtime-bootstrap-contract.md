# PatentIQ V2 Runtime Bootstrap Contract

## Purpose

This note captures the runtime contract that must hold for both local Docker Compose usage and Azure Container Apps deployment:

- the same backend and frontend images should run in both environments,
- the same release-manifest contract should drive artifact resolution,
- the backend should read a stable mounted runtime layout,
- artifact hydration should be visible in logs and non-destructive by default.

## Runtime Artifact Layout

Both local and Azure should present the backend with the same on-disk shape:

```text
/artifacts/
  current -> /artifacts/releases/<release_id>
  releases/
    <release_id>/
      release-manifest.json
      .bootstrap-state.json
      serving/
      vectors/
      ml/
  logs/
    artifact-init.log
```

The backend runtime should use:

- `PATENTIQ_V2_ETL_DATA_ROOT=/artifacts/current`
- `PATENTIQ_V2_LOCAL_ARTIFACT_ROOT=/artifacts/current/serving`
- `PATENTIQ_V2_SERVING_MANIFEST_PATH=/artifacts/current/serving/serving_snapshot_manifest.json`
- `HF_HOME=/hf-home`

## Local Docker Compose Contract

`compose.yaml` now defines three services:

1. `artifact-init`
   - hydrates the active release into the persistent `patentiq-artifacts` volume,
   - optionally prefetches Hugging Face model snapshots into `patentiq-hf-cache`,
   - logs every copy/download/promote step,
   - refuses overwrite unless explicitly enabled.
2. `backend`
   - waits for `artifact-init`,
   - reads artifacts only from mounted local paths,
   - logs resolved runtime paths before starting `uvicorn`.
3. `frontend`
   - waits for backend startup,
   - writes `public/runtime-config.js` at container start,
   - logs the runtime API base URL before serving.

Default local source mode is `local_release` and reads:

- `/workspace/etl/manifests/releases/active_release.json`
- `/workspace/etl/data/releases/<release_id>/release-manifest.json`

Developers can switch to Blob-backed hydration by setting:

- `PATENTIQ_BOOTSTRAP_SOURCE_MODE=azure_blob`
- `PATENTIQ_AZURE_STORAGE_ACCOUNT_URL`
- `PATENTIQ_AZURE_STORAGE_CONTAINER`
- `PATENTIQ_AZURE_ACTIVE_RELEASE_BLOB=manifests/active_release.json`

## Azure Container Apps Contract

The same `artifact-init` bootstrap logic should be reused as an init container or deployment-time sync step.

Target Azure shape:

1. Blob remains the canonical release store.
2. Active runtime release is materialized onto an Azure Files share or other persistent mounted storage.
3. The backend app mounts that storage at `/artifacts`.
4. A shared Hugging Face cache is mounted at `/hf-home`.
5. Backend starts with the same env vars and mount paths used locally.

For the current full artifact footprint, Azure Container Apps should not rely on replica-local startup hydration for the full release.

For semantic model readiness, the intended Azure behavior is:

1. `artifact-init` downloads the active runtime release into `/artifacts`,
2. `artifact-init` prefetches the declared Hugging Face model snapshots into `/hf-home`,
3. the backend starts only after that bootstrap succeeds,
4. the backend then runs with offline cache settings:
   - `HF_HOME=/hf-home`
   - `HF_HUB_OFFLINE=1`
   - `TRANSFORMERS_OFFLINE=1`

This keeps runtime inference independent from live Hugging Face availability after startup. As long as the `/hf-home` share is persistent, later restarts should reuse the warmed cache instead of downloading again.

## Logging Contract

Visibility is required at each stage:

- publish writes `publish.log` and `publish.events.jsonl`,
- runtime bootstrap writes `artifact-init.log`,
- `artifact-init` prints the promoted release, current runtime tree, and cached release sizes,
- backend prints resolved runtime paths and mounted artifact tree,
- frontend prints the effective runtime API base URL and generated runtime config file.

## Safety Rules

- Release publish must not overwrite an existing local release directory unless `release_overwrite_enabled=true`.
- Azure publish must not overwrite an existing release prefix unless `azure_release_overwrite_enabled=true`.
- Runtime bootstrap must not replace an existing materialized runtime release unless `PATENTIQ_BOOTSTRAP_OVERWRITE=true`.
- Promotion to `/artifacts/current` must remain atomic via symlink swap after staging completes successfully.

## Current Caveat

The release manifest now declares semantic Hugging Face dependencies, but the vector manifest still does not pin exact Hugging Face revisions. Until that upstream contract is tightened, bootstrap prefetch needs `PATENTIQ_BOOTSTRAP_ALLOW_UNPINNED_HF_MODELS=true` for normal developer startup.

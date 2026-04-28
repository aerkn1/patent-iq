# PatentIQ V2 Backend VM Deployment Plan

## Purpose

This note defines the practical migration path for moving the PatentIQ backend from Azure Container Apps to a single Azure VM while keeping:

1. Azure Blob as the canonical runtime artifact source,
2. the current backend container image,
3. the current frontend deployment shape,
4. the current runtime release contract.

The reason for this plan is simple:

1. the backend health route is fine on ACA,
2. light and medium serving endpoints are fine on ACA,
3. analytics-heavy routes are not fine on ACA because `analytics_serving.duckdb` is about `72 GB` and is being queried from Azure Files,
4. DuckDB on a large SMB-mounted file is the wrong storage shape for low-latency request serving.

This plan preserves the product and release model, but changes the backend storage/runtime substrate to something DuckDB can use efficiently.

---

## Recommendation

Use:

1. one Linux VM for the backend,
2. one attached managed disk for runtime artifacts and HF cache,
3. Blob-to-local-disk artifact sync on boot or deployment,
4. the existing backend container image or the same backend code running directly on the VM,
5. the frontend can remain on Azure Container Apps.

Recommended target shape:

1. VM SKU:
   - `Standard_D4s_v5`
2. data disk:
   - `Premium SSD v2`
   - `256 GiB`
3. region:
   - `germanywestcentral`

Actual live fallback shape after the first bring-up and later in-place resize on `2026-04-28`:

1. initial bring-up SKU:
   - `Standard_D2s_v3`
2. current live SKU:
   - `Standard_D4s_v3`
3. data disk:
   - `Premium SSD` `P15`
   - `256 GiB`
4. region:
   - `switzerlandnorth`

Reason for the fallback:

1. the student subscription had `0` quota for `DSv5`, `DASv5`, and `EASv5` families in the tested allowed regions,
2. `germanywestcentral` was also showing widespread VM SKU capacity restrictions,
3. `Premium SSD v2` requires a zonal VM, while the successful fallback VM had to be provisioned regionally to get capacity.

Fallback if more memory headroom is needed:

1. VM SKU:
   - `Standard_E4s_v5`
2. same disk plan

Do **not** use:

1. Azure Files as the request-time home of `analytics_serving.duckdb`
2. ACA ephemeral storage as the full analytics copy target

Reason:

1. ACA ephemeral storage is far too small for the full analytics DB,
2. Azure Files is acceptable for bootstrap persistence, but not for this class of DuckDB query workload.

---

## Why This Helps

Current ACA path:

1. request hits backend,
2. backend opens `analytics_serving.duckdb`,
3. file is read from Azure Files SMB,
4. analytics-heavy routes stall or timeout.

VM path:

1. artifact sync copies runtime files from Blob to a VM-attached managed disk,
2. backend reads the same DuckDB from local block storage,
3. DuckDB gets low-latency local reads instead of SMB-backed remote reads.

The most important change is not "VM versus containers".

It is:

1. remote file share reads
2. becoming
3. local block storage reads

That is the expected speed win.

Observed execution outcome on the fallback host line:

1. the VM-backed local-disk path removed the ACA-style hard timeout / no-response failure mode,
2. semantic and lightweight runtime routes were fast,
3. `pending-grants` returned successfully instead of hanging,
4. but on `Standard_D2s_v3` it still remained slow enough to be uncomfortable for UI use,
5. the in-place resize to `Standard_D4s_v3` improved some routes materially,
6. but the worst analytics-heavy route still remained slow enough that query-path work or a larger memory-heavy SKU remains reasonable.

Practical implication:

1. moving off Azure Files was necessary,
2. but the fallback host line is still a compromise,
3. the next clear scaling step is either:
   - move back toward `D4s_v5` once quota exists,
   - or move to an `E4` shape if memory/cache headroom is the better lever.

---

## Cost Shape

Observed retail rates for the original `germanywestcentral` target on `2026-04-28`:

1. `Standard_D4s_v5` Linux:
   - `€0.1996/hour`
   - about `€145.71/month` at `730h`
2. `Standard_E4s_v5` Linux:
   - `€0.2639/hour`
   - about `€192.65/month`
3. `Premium SSD P15` `256 GiB`:
   - about `€36.29/month`
4. `Premium SSD P20` `512 GiB`:
   - about `€69.91/month`
5. `Premium SSD v2` capacity meter was materially lower than the classic fixed-size Premium SSD tiers.

Practical planning numbers:

1. `D4s_v5` + `Premium SSD v2 256 GiB`
   - roughly `€165-170/month` plus OS disk / egress / small extras
2. `E4s_v5` + `Premium SSD v2 256 GiB`
   - roughly `€210-215/month` plus OS disk / egress / small extras
3. current live fallback shape in `switzerlandnorth`:
   - `D4s_v3` + `P15 256 GiB`
   - roughly `€207/month` plus OS disk / egress / small extras
4. earlier bring-up fallback:
   - `D2s_v3` + `P15 256 GiB`
   - materially cheaper, but with less compute headroom than the current live state

Observed `switzerlandnorth` retail rates used during the live resize decision on `2026-04-28`:

1. `D4s_v3` Linux:
   - `€0.2292/hour`
   - about `€167.32/month`
2. `D4s_v5` Linux:
   - `€0.2196/hour`
   - about `€160.31/month`
   - but blocked by `standardDSv5Family` quota `0`
3. `E4s_v5` Linux:
   - `€0.2899/hour`
   - about `€211.63/month`
4. `E4ds_v5` Linux:
   - `€0.3298/hour`
   - about `€240.75/month`
5. `P15` `256 GiB`:
   - about `€39.92/month`

Sizing note:

1. the current `full` runtime release is about `113 GiB` before HF cache, temp files, logs, and future growth,
2. `256 GiB` is enough for one active runtime copy,
3. but it is a tighter operational fit than `512 GiB` for keeping a previous release around or staging the next release in parallel.

This is the expected useful backend cost band if the goal is "make analytics DuckDB routes actually usable".

---

## Target Resource Layout

Keep:

1. resource group:
   - `patent-data`
2. storage account:
   - `patentiq`
3. blob container:
   - `patentiq-data`
4. ACR:
   - `patentiqacr`
5. frontend ACA app:
   - `patentiq-frontend-v2`

Add:

1. backend VM
2. managed data disk for artifacts
3. optional static public IP if the VM will be directly exposed

Execution note:

1. the current live VM attempt uses `switzerlandnorth` because Azure policy blocked `westeurope` and quota/capacity blocked the preferred `germanywestcentral` host shape.

Suggested VM filesystem layout:

1. OS disk:
   - system packages, Docker, app bootstrap unit files
2. mounted data disk:
   - `/srv/patentiq/artifacts`
   - `/srv/patentiq/hf-home`
   - `/srv/patentiq/logs`

Expected artifact layout on disk:

1. `/srv/patentiq/artifacts/releases/2026-04-25-runtime-current/...`
2. optional symlink:
   - `/srv/patentiq/artifacts/current -> /srv/patentiq/artifacts/releases/2026-04-25-runtime-current`

---

## Runtime Modes

There are two good backend runtime modes on the VM.

## Option A: Keep Container Runtime

Run:

1. `patentiqacr.azurecr.io/patentiq-backend-v2:<tag>`

Mount into the container:

1. `/srv/patentiq/artifacts` -> `/artifacts`
2. `/srv/patentiq/hf-home` -> `/hf-home`

Set env:

1. `PATENTIQ_V2_ARTIFACT_MODE=local_fs`
2. `PATENTIQ_V2_ETL_DATA_ROOT=/artifacts/releases/2026-04-25-runtime-current`
3. `PATENTIQ_V2_LOCAL_ARTIFACT_ROOT=/artifacts/releases/2026-04-25-runtime-current/serving`
4. `PATENTIQ_V2_SERVING_MANIFEST_PATH=/artifacts/releases/2026-04-25-runtime-current/serving/serving_snapshot_manifest.json`
5. `PATENTIQ_V2_DUCKDB_PATH=/tmp/patentiq_v2.duckdb`
6. `PATENTIQ_V2_CACHE_DIR=/tmp/backend-cache`
7. `PATENTIQ_V2_PENDING_GRANT_CACHE_DIR=/tmp/pending-grant-cache`
8. `HF_HOME=/hf-home`
9. `HF_HUB_CACHE=/hf-home/hub`
10. `HF_HUB_OFFLINE=1`
11. `TRANSFORMERS_OFFLINE=1`

This option keeps the deployment closest to the current ACA runtime.

## Option B: Run Backend Directly On VM

Install:

1. Python runtime
2. backend dependencies
3. backend startup unit

Point it at the same local artifact paths on the mounted disk.

This is simpler at runtime but diverges a little more from the current image-based deployment.

Recommendation:

1. use **Option A**
2. keep the backend image
3. only change the substrate and mounted storage path

---

## Artifact Sync Model

Blob remains canonical.

The VM does not regenerate artifacts. It only syncs them.

Required sync behavior:

1. resolve active release:
   - `manifests/active_release.json`
2. if active release is already local and complete, reuse it
3. if missing, download release to the local data disk
4. prefetch HF model dependencies locally
5. start backend only after local runtime is ready

This can reuse the current bootstrap script logic, but the target root becomes local VM disk, not Azure Files.

Recommended local target root:

1. `/srv/patentiq/artifacts`

Recommended bootstrap execution:

1. as a one-shot systemd unit before the backend service,
2. or as part of a deployment/update script.

Important:

1. sync from Blob to local disk,
2. do not query the DB directly over a mounted share.

---

## Deployment Sequence

## Phase 1: Provision

1. create Linux VM in `germanywestcentral`
2. attach `Premium SSD v2` data disk
3. open only required inbound ports:
   - `22` for admin
   - `80/443` only if directly exposing the VM
4. install:
   - Docker
   - AzCopy or Azure CLI
   - systemd service/unit files

## Phase 2: Runtime Bootstrap

1. mount data disk
2. create:
   - `/srv/patentiq/artifacts`
   - `/srv/patentiq/hf-home`
   - `/srv/patentiq/logs`
3. authenticate to Blob
4. sync active runtime release from Blob to the data disk
5. prefetch HF models locally

## Phase 3: Backend Start

1. run backend container with mounted local paths
2. verify:
   - `/health`
   - semantic suggestions
   - semantic family search
   - `pending-grants`
   - one market-intelligence analytics route

## Phase 4: Cutover

1. point `api.patentiq.app` to the VM backend
2. leave frontend on ACA
3. update frontend API base URL if needed
4. keep ACA backend available until VM backend is confirmed stable

---

## Domain and Networking Options

## Simplest

1. frontend stays on ACA
2. backend VM gets public IP
3. Cloudflare `api.patentiq.app` points to VM

## Better

1. frontend stays on ACA
2. backend VM sits behind a reverse proxy
3. TLS terminates on:
   - Nginx/Caddy on the VM,
   - or another Azure ingress layer

Recommended practical first cut:

1. VM public IP
2. Caddy or Nginx on the VM
3. backend container only on localhost / internal port
4. reverse proxy publishes `443`

---

## Why Not Continue With ACA For This Artifact

Continuing with ACA would still leave one of these requirements:

1. split analytics into a much smaller serving artifact,
2. redesign analytics-heavy endpoints around smaller local caches,
3. move to a different backend substrate anyway.

Those may still be worth doing later, but they are product/data refactors.

The VM move is the shortest operational path that keeps:

1. current backend code,
2. current release model,
3. current Blob artifact source,
4. current frontend deployment,
5. and replaces only the weakest layer: backend storage execution substrate.

---

## Immediate Recommendation

Do this first:

1. provision `Standard_D4s_v5`
2. attach `Premium SSD v2 256 GiB`
3. sync current active release to local disk
4. run existing backend container on the VM
5. validate `pending-grants` and a few market routes

If memory pressure remains:

1. move to `Standard_E4s_v5`

Do **not** spend more time trying to make the full `72 GB` analytics DuckDB work well over Azure Files in ACA. That is the wrong storage/runtime match for this workload.

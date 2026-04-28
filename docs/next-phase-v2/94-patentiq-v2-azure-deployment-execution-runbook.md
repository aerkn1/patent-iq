# PatentIQ V2 Azure Deployment Execution Runbook

## Purpose

This note records the actual Azure deployment work completed for PatentIQ V2 and the concrete execution path used to move from:

1. Blob-hosted runtime release artifacts,
2. local image builds,
3. Azure base infrastructure creation,
4. Azure Container Apps deployment,
5. first-time remote runtime hydration.

Unlike the earlier blueprint notes, this document is not a target-state design. It is the operational record of what was actually provisioned, what failed, what was fixed, and what remains after the first live rollout.

Execution date: `2026-04-28`

Related notes:

1. [36-patentiq-v2-azure-deployment-and-release-blueprint.md](./36-patentiq-v2-azure-deployment-and-release-blueprint.md)
2. [90-patentiq-v2-azure-deployment-prep-starting-point.md](./90-patentiq-v2-azure-deployment-prep-starting-point.md)
3. [91-patentiq-v2-runtime-bootstrap-contract.md](./91-patentiq-v2-runtime-bootstrap-contract.md)
4. [92-patentiq-v2-runtime-release-manual-upload-runbook.md](./92-patentiq-v2-runtime-release-manual-upload-runbook.md)
5. [93-patentiq-v2-archive-layer-manual-upload-runbook.md](./93-patentiq-v2-archive-layer-manual-upload-runbook.md)

---

## Final Deployment Direction Locked

The final live deployment was settled on this shape:

1. existing storage account stays canonical:
   - resource group: `patent-data`
   - storage account: `patentiq`
   - region: `germanywestcentral`
2. Azure Container Apps is the public runtime for:
   - frontend only
3. backend serving runs on:
   - one Azure VM
   - one attached local managed disk
4. Azure Blob remains the canonical runtime artifact source:
   - blob container: `patentiq-data`
5. the backend continues to run in:
   - `local_fs` artifact mode
6. Cloudflare fronts the public domains:
   - `https://www.patentiq.app`
   - `https://api.patentiq.app`
   - `https://patentiq.app` -> redirect to `https://www.patentiq.app`
7. Azure Files remains in the storage account as a preserved bootstrap/cache layer from the ACA phase, but it is no longer the live request-time backend substrate

---

## Preconditions Already Completed Before Azure Rollout

The Azure app deployment was not the first step. These prerequisites were already finished:

1. runtime release uploaded to Blob:
   - release id: `2026-04-25-runtime-current`
2. runtime release verified against local by exact blob path and byte size
3. bad nested `publication_serving/publication_serving/...` prefix cleaned from Blob
4. active release pointer uploaded:
   - `manifests/active_release.json`
5. archive layers uploaded:
   - `2026-04-25-archive-current`

This matters because the Azure backend rollout assumes Blob already contains a complete active release.

---

## Azure Resources Provisioned

The following resources were created or confirmed during the rollout.

## Existing Resource Reused

1. resource group:
   - `patent-data`
2. storage account:
   - `patentiq`
3. blob container:
   - `patentiq-data`

## Newly Created

1. Azure Container Registry:
   - `patentiqacr`
   - login server: `patentiqacr.azurecr.io`
2. Log Analytics workspace:
   - `patentiq-logs`
3. Azure Container Apps environment:
   - `patentiq-env`
4. Azure Files shares:
   - `patentiq-artifacts`
   - `patentiq-hf-cache`
5. ACA environment storage links:
   - `patentiq-artifacts`
   - `patentiq-hf-cache`

## Resulting ACA Environment Info

1. environment default domain:
   - `greenbush-c9aa3b9e.germanywestcentral.azurecontainerapps.io`
2. environment static IP:
   - `20.170.75.185`

---

## Host Azure CLI Bring-Up

The deployment was executed with the host Azure CLI, not with Azure MCP.

Reason:

1. Docker MCP Azure tooling became available only after Docker Desktop storage expansion,
2. but Docker Azure MCP did not inherit host `az login` state in this setup,
3. so authenticated deployment work proceeded via host `az`.

Host setup that was completed:

1. Azure CLI installed via Homebrew
2. device-code login completed
3. active subscription:
   - `Azure for Students`
   - subscription id: `a12b6d27-11d3-4400-a4e7-4baba2e389be`
4. tenant:
   - `TUM`

---

## Azure Provider Registration

The subscription was initially not usable for Container Apps.

Observed issue:

1. `Microsoft.App` was not registered
2. `az containerapp env list` failed until provider registration completed

Providers that were explicitly registered:

1. `Microsoft.App`
2. `Microsoft.OperationalInsights`
3. `Microsoft.ContainerRegistry`

This became a required first real step in the host-CLI rollout.

---

## Base Infrastructure Creation Sequence

The Azure base layer was created in this order:

1. create ACR:
   - `patentiqacr`
2. create Log Analytics workspace:
   - `patentiq-logs`
3. create Azure Files share:
   - `patentiq-artifacts`
4. create Azure Files share:
   - `patentiq-hf-cache`
5. create ACA managed environment:
   - `patentiq-env`
6. attach storage link:
   - `patentiq-artifacts`
7. attach storage link:
   - `patentiq-hf-cache`

This matches the contract expected by:

1. [azure/backend.app.yaml](/Users/ardaerkan/Documents/MIGRATE/patent-iq/azure/backend.app.yaml)
2. [azure/frontend.app.yaml](/Users/ardaerkan/Documents/MIGRATE/patent-iq/azure/frontend.app.yaml)

---

## Image Strategy

Three images were required:

1. backend:
   - `patentiq-backend-v2`
2. frontend:
   - `patentiq-frontend-v2`
3. bootstrap init image:
   - `patentiq-bootstrap`

## Initial Image Tag

First tag used:

1. `2026-04-28-aca1`

This tag was built and pushed successfully, but it was not deployable to ACA.

## Problem Found

The initial image build/push path produced a Mac-native manifest set that did not expose the required ACA platform:

1. ACA needs `linux/amd64`
2. the first pushed backend image did not include a valid `linux/amd64` child manifest
3. backend deploy failed with:
   - `no child with platform linux/amd64`

## Corrected Image Tag

Second tag used:

1. `2026-04-28-aca2`

Fix:

1. rebuild all three images with:
   - `docker buildx build --platform linux/amd64 --push`

Final published images:

1. `patentiqacr.azurecr.io/patentiq-backend-v2:2026-04-28-aca2`
2. `patentiqacr.azurecr.io/patentiq-frontend-v2:2026-04-28-aca2`
3. `patentiqacr.azurecr.io/patentiq-bootstrap:2026-04-28-aca2`

The backend image was explicitly verified to expose `linux/amd64`.

---

## Repo Manifest Changes Applied

The Azure manifest files were updated to reflect the real rollout state.

## Backend Manifest

[azure/backend.app.yaml](/Users/ardaerkan/Documents/MIGRATE/patent-iq/azure/backend.app.yaml)

Changes:

1. location set to `germanywestcentral`
2. `managedEnvironmentId` set to real environment:
   - `patentiq-env`
3. image tags updated to:
   - backend `2026-04-28-aca2`
   - bootstrap `2026-04-28-aca2`
4. ACR registry configuration added:
   - `patentiqacr.azurecr.io`
5. ACR secret placeholder added:
   - `acr-password`
6. empty `hf-token` secret removed

Why the HF secret was removed:

1. ACA rejects secrets with empty values
2. the current semantic Hugging Face models are public
3. the deployment therefore does not currently need an `HF_TOKEN`

## Frontend Manifest

[azure/frontend.app.yaml](/Users/ardaerkan/Documents/MIGRATE/patent-iq/azure/frontend.app.yaml)

Changes:

1. location set to `germanywestcentral`
2. `managedEnvironmentId` set to real environment:
   - `patentiq-env`
3. image tag updated to:
   - frontend `2026-04-28-aca2`
4. ACR registry configuration added:
   - `patentiqacr.azurecr.io`
5. ACR secret placeholder added:
   - `acr-password`

---

## Secret Handling Rule Used During Deployment

Secrets were not written back into repo YAML.

Instead:

1. ACR credentials were fetched live from Azure
2. storage connection string was fetched live from Azure
3. temporary deployment YAMLs were generated under `/tmp`
4. those temporary files were used with:
   - `az containerapp create --yaml`
   - `az containerapp update --yaml`

This kept:

1. repo manifests reusable,
2. secrets out of versioned files,
3. deployment-specific values injectable at execution time.

---

## Backend Deployment Path

## First Backend Attempt

The backend app resource was created first with the `aca1` image set.

Two real problems surfaced:

1. empty `hf-token` secret was invalid
2. backend image was not deployable on ACA because it did not include `linux/amd64`

Both were fixed as described above.

## Final Backend App State

App name:

1. `patentiq-backend-v2`

Public FQDN:

1. `https://patentiq-backend-v2.greenbush-c9aa3b9e.germanywestcentral.azurecontainerapps.io`

Final image set:

1. backend:
   - `patentiqacr.azurecr.io/patentiq-backend-v2:2026-04-28-aca2`
2. init:
   - `patentiqacr.azurecr.io/patentiq-bootstrap:2026-04-28-aca2`

Runtime settings kept:

1. `PATENTIQ_V2_ARTIFACT_MODE=local_fs`
2. `PATENTIQ_V2_ETL_DATA_ROOT=/artifacts/current`
3. `PATENTIQ_V2_LOCAL_ARTIFACT_ROOT=/artifacts/current/serving`
4. `PATENTIQ_V2_RAW_PARQUET_FALLBACK_ENABLED=false`
5. `PATENTIQ_BOOTSTRAP_PROFILE=full`
6. `PATENTIQ_BOOTSTRAP_PREFETCH_HF_MODELS=true`
7. `PATENTIQ_BOOTSTRAP_ALLOW_UNPINNED_HF_MODELS=true`

Mounted Azure Files paths:

1. `/artifacts`
2. `/hf-home`

---

## Frontend Deployment Path

The frontend was deployed after the corrected backend app revision existed.

App name:

1. `patentiq-frontend-v2`

Public FQDN:

1. `https://patentiq-frontend-v2.greenbush-c9aa3b9e.germanywestcentral.azurecontainerapps.io`

Final image:

1. `patentiqacr.azurecr.io/patentiq-frontend-v2:2026-04-28-aca2`

Runtime API URL injected at deployment time:

1. `https://patentiq-backend-v2.greenbush-c9aa3b9e.germanywestcentral.azurecontainerapps.io`

Observed result:

1. frontend root returned `HTTP 200`

---

## Runtime Bootstrap Behavior Observed In Azure

The backend app does not become immediately healthy on first deploy, because:

1. the init container must materialize the active runtime release into Azure Files,
2. the init container must prewarm Hugging Face cache into Azure Files,
3. only after that can the backend process start and pass `/health`.

## Current Active Release Resolved In Azure

From the live init log:

1. active pointer blob:
   - `manifests/active_release.json`
2. resolved release manifest:
   - `releases/2026-04-25-runtime-current/release-manifest.json`
3. resolved release id:
   - `2026-04-25-runtime-current`
4. profile:
   - `full`

## Current Bootstrap Progress Observed

Observed phases:

1. backend init started successfully
2. `core_serving.duckdb` download started and progressed correctly
3. bootstrap advanced into:
   - `serving/publication_serving/...`
4. Azure Files log showed continuous shard downloads under:
   - `application_evidence_by_appln/appln_bucket=*`

So the backend deployment is currently blocked only by first-time runtime hydration time, not by a new manifest or image error.

---

## How Progress Was Verified

The most reliable live bootstrap signal was not the public `/health` route.

Instead, progress was verified from:

1. ACA revision state:
   - revision existed
   - running state `Activating`
2. ACA system logs:
   - confirmed image pull and replica scheduling
3. Azure Files mounted log file:
   - `patentiq-artifacts/logs/artifact-init.log`

This log file became the authoritative progress source for:

1. release resolution
2. current serving file in flight
3. publication shard progress

---

## Current Live State At Time Of Writing

## Working

1. ACR is provisioned and usable
2. ACA environment is provisioned and usable
3. both Azure Files mounts are connected to the environment
4. frontend is deployed and responding publicly
5. backend app object and revision are provisioned correctly
6. backend init container is actively hydrating the full runtime release

## Not Yet Complete

1. backend public `/health` was still not returning at the time this note was written
2. reason:
   - first full runtime hydration had not finished yet
3. endpoint smoke tests had therefore not been run yet against the ACA backend

---

## Remaining Steps After This Runbook Snapshot

To finish Azure deployment end-to-end:

1. wait for backend `artifact-init` to finish
2. verify backend health:
   - `/health`
3. run backend smoke checks:
   - family endpoint
   - portfolio endpoint
   - publication endpoint
   - semantic family-anchor search
4. optionally confirm free-text semantic warm-up behavior
5. only then wire custom domains from Cloudflare

Suggested domain plan:

1. backend:
   - `api.patentiq.app`
2. frontend:
   - `patentiq.app` or `www.patentiq.app`
3. initial Cloudflare mode:
   - DNS only during ACA managed certificate issuance

---

## Key Lessons From The Actual Rollout

1. `Microsoft.App` provider registration must be treated as an explicit first step on a fresh subscription.
2. `linux/amd64` image builds must be forced from a Mac host for ACA compatibility.
3. ACA manifest secrets cannot be left as empty placeholders if the secret field is present.
4. the first Azure backend startup should be expected to take a long time because `full` bootstrap is large.
5. the mounted Azure Files bootstrap log is the most useful truth source when health is not yet live.
6. frontend can be deployed in parallel while backend hydration is still running, as long as the frontend points to the intended backend FQDN.

---

## Operational Rule Preserved

This deployment did not change the core runtime contract:

1. Blob is still canonical
2. backend still serves from mounted local paths
3. `publication_serving/` remains a directory artifact
4. semantic still relies on vector/model artifacts outside the serving DuckDBs
5. local and Azure continue to share the same mount-path expectations

That continuity is important because it keeps the Azure rollout aligned with the same release and bootstrap model already proven locally.

---

## Post-Snapshot Recovery Work

After the original snapshot above, additional rollout work was required to move the backend from "hydrating" to "serving".

## Problem 1: ACA Activation Deadline During First `full` Bootstrap

The first live ACA backend revision did not fail because of authentication or image issues. It failed because:

1. first-time `full` artifact hydration took longer than ACA's activation window,
2. the revision ended in:
   - `Deployment Progress Deadline Exceeded. 0/1 replicas ready.`

Operational conclusion:

1. the backend could not rely on "first serving revision hydrates everything itself" for the initial rollout,
2. Azure Files had to be pre-seeded out of band first.

## Recovery 1: One-Off ACI Bootstrap Seeder

A one-off Azure Container Instance runner was introduced:

1. container group:
   - `patentiq-bootstrap-seed`
2. it mounted the same Azure Files shares:
   - `patentiq-artifacts`
   - `patentiq-hf-cache`
3. it reused the same bootstrap image contract as `artifact-init`

Purpose:

1. hydrate the full runtime release into Azure Files,
2. prewarm Hugging Face model assets,
3. finish all slow first-run work outside ACA revision activation.

## Problem 2: Azure Files Does Not Support Runtime Symlinks

The bootstrapper originally promoted the current release using:

1. `/artifacts/current -> /artifacts/releases/<release_id>`

On Azure Files, that failed with filesystem support errors.

Fix applied in code:

1. [etl/scripts/bootstrap_runtime_artifacts.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/scripts/bootstrap_runtime_artifacts.py)
2. `_promote_current_symlink(...)` was changed to:
   - tolerate unsupported symlink filesystems,
   - write `/artifacts/.current-release.json` as a release marker instead.

Deployment implication:

1. backend ACA config stopped depending on `/artifacts/current`,
2. it was switched to the fixed release path:
   - `/artifacts/releases/2026-04-25-runtime-current`

## Problem 3: Hugging Face Cache Symlink Behavior On Azure Files

The first ACI seeding retry then failed during HF prewarm:

1. `huggingface_hub` attempted snapshot layout behavior incompatible with Azure Files SMB symlink limitations,
2. the first failure was on:
   - `BAAI/bge-m3`

Fix applied in code:

1. [etl/scripts/bootstrap_runtime_artifacts.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/scripts/bootstrap_runtime_artifacts.py)
2. HF prewarm was changed to:
   - keep the hub cache under `/hf-home/hub`
   - download actual model payloads into symlink-free local paths under:
     - `/hf-home/models/<repo-slug>`
3. [backend_v2/infrastructure/semantic_query_encoder.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/semantic_query_encoder.py)
4. the backend encoder was updated to prefer those prefetched local model directories.

Result:

1. ACI seeding on image tag `2026-04-28-aca4` completed successfully,
2. both models were prewarmed:
   - `BAAI/bge-m3`
   - `AI-Growth-Lab/PatentSBERTa`

## Updated Image Set After Recovery Fixes

Recovery fixes required additional image generations beyond `aca2`.

Intermediate tag:

1. `2026-04-28-aca3`

Final corrected tag used for the working recovery path:

1. `2026-04-28-aca4`

Relevant images:

1. `patentiqacr.azurecr.io/patentiq-backend-v2:2026-04-28-aca4`
2. `patentiqacr.azurecr.io/patentiq-bootstrap:2026-04-28-aca4`

## Backend ACA Revision Recovery

After the ACI preseed completed:

1. backend ACA was updated to use the fixed release path config,
2. backend ACA was updated to use the `aca4` backend/bootstrap images,
3. a healthy serving revision was reached.

Confirmed working after this recovery:

1. backend `/health`
2. semantic family suggestions
3. semantic family search

So at that point:

1. artifact hydration was no longer the blocker,
2. HF prewarm was no longer the blocker,
3. base backend serving was live.

## Problem 4: `analytics_serving.duckdb` Read Failure

Once the backend was healthy, a narrower runtime defect remained:

1. `pending-grants` returned `500`
2. backend logs showed:
   - `_duckdb.IOException`
   - `Invalid argument`
   - path:
     `/artifacts/releases/2026-04-25-runtime-current/serving/analytics_serving.duckdb`

One mitigation was applied first:

1. writable backend cache and local DuckDB paths were moved off Azure Files and onto `/tmp`
2. this removed one class of SMB-write risk

But the endpoint still failed after that change.

## Root Cause Confirmed

The actual issue was that the Azure Files copy of `analytics_serving.duckdb` was corrupted.

Verified sizes:

1. canonical Blob object size:
   - `72,023,027,712`
2. Azure Files mounted copy size:
   - `72,457,138,176`

Because the backend runtime reads the Azure Files copy, not Blob directly, analytics-backed endpoints continued to fail.

## Repair Path Chosen

The repair path was narrowed to a single file:

1. delete the corrupted Azure Files copy:
   - `releases/2026-04-25-runtime-current/serving/analytics_serving.duckdb`
2. replace it from the known-good Blob source at the exact same path
3. re-run backend analytics smoke checks once the copy completes

The direct repair was intentionally scoped to one file instead of rehydrating the whole release again.

## Bootstrap Hardening Added After Diagnosis

To prevent the same silent corruption from being promoted again in later hydrations:

1. [etl/scripts/bootstrap_runtime_artifacts.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/scripts/bootstrap_runtime_artifacts.py)
2. blob downloads now:
   - stream into `.<filename>.partial`
   - validate on-disk size against the Blob size after download
   - refuse promotion if the actual file size mismatches
   - only rename into the final target path after validation
3. [etl/tests/test_bootstrap_runtime_artifacts.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/tests/test_bootstrap_runtime_artifacts.py)
4. a regression test was added for oversized chunk promotion rejection

At the time of this updated note:

1. ACA backend and frontend deployment infrastructure is in place,
2. core backend serving is healthy,
3. the remaining repair is the in-place replacement of the corrupted Azure Files `analytics_serving.duckdb` copy,
4. once that replacement finishes, `pending-grants` is the primary endpoint to revalidate.

---

## Final Live State After Public Cutover

The final public topology after the ACA backend recovery work and the later VM cutover is:

1. frontend:
   - Azure Container App `patentiq-frontend-v2`
   - public URL: `https://www.patentiq.app`
2. backend:
   - VM `patentiq-backend-vm`
   - public URL: `https://api.patentiq.app`
3. apex:
   - `https://patentiq.app`
   - Cloudflare redirect to `https://www.patentiq.app`

## Final Frontend State

1. ACA custom domain:
   - `www.patentiq.app`
2. ACA managed certificate:
   - `www.patentiq.app-patentiq-260428162442`
3. frontend runtime API URL after the final repoint:
   - `NEXT_PUBLIC_API_BASE_URL=https://api.patentiq.app`

## Final Backend VM State

1. region:
   - `switzerlandnorth`
2. public IP:
   - `172.161.2.87`
3. current live SKU:
   - `Standard_D4s_v3`
4. attached data disk:
   - `patentiq-backend-data-p15`
   - `Premium_LRS`
   - `256 GiB`
5. public HTTPS path:
   - Cloudflare Origin CA certificate on the VM
   - Nginx on `:443`
   - backend container behind Nginx
6. final NSG exposure:
   - `22`
   - `80`
   - `443`
   - public `8000` removed

## Final Cloudflare State

1. `www`
   - `CNAME`
   - ACA frontend hostname
   - `DNS only`
2. `asuid.www`
   - `TXT`
   - ACA validation token
3. `api`
   - `A`
   - `172.161.2.87`
   - `Proxied`
4. `@`
   - proxied apex host for the redirect rule
5. SSL mode:
   - `Full (strict)`

## Cleanup Completed After Cutover

Removed:

1. ACA backend app:
   - `patentiq-backend-v2`
2. one-off bootstrap container group:
   - `patentiq-bootstrap-seed`
3. unused public IP:
   - `patentiq-backend-ip`
4. unattached disk:
   - `patentiq-backend-data`

Retained intentionally:

1. storage account:
   - `patentiq`
2. Azure file shares:
   - `patentiq-artifacts`
   - `patentiq-hf-cache`
3. ACA environment:
   - `patentiq-env`
4. frontend ACA app:
   - `patentiq-frontend-v2`

## Final Outcome

1. the public application now serves through:
   - ACA frontend
   - VM backend
   - Cloudflare DNS/TLS
2. Blob remains canonical for runtime artifacts,
3. the remaining platform question is endpoint latency on the live VM shape, not deployment correctness.

# PatentIQ V2 Azure Deployment And Release Blueprint

## Purpose

Define the intended remote deployment shape for PatentIQ V2 so that:

1. the product is remotely accessible and credible for jury / stakeholder demos,
2. frontend, backend, ETL, models, and semantic artifacts are versioned cleanly,
3. deployments are automated from GitHub tags and releases,
4. Azure Blob remains the canonical artifact store,
5. cost stays controlled for a mostly on-demand demo deployment.

This note is for the ultimate deployable shape, not only the immediate MVP run on local infrastructure.

---

## 1. Deployment Principles

PatentIQ should be deployed as an `artifact-driven`, `container-first`, `Azure-native` system.

Core principles:

1. application code and heavy data artifacts must be versioned separately,
2. frontend and backend containers should stay lightweight,
3. Gold, ML, semantic, and ANN artifacts must live outside app containers,
4. Git tags and GitHub Releases should define promotion boundaries,
5. Azure services should be used consistently because:
   - Azure credit already exists,
   - Azure Blob is already in use,
   - the demo deployment does not require constant availability.

---

## 2. Public Product Shape

Public domains:

1. `https://patentiq.app`
   - frontend application
2. `https://api.patentiq.app`
   - backend API

Optional:

1. `https://www.patentiq.app`
   - redirect to `https://patentiq.app`

High-level request flow:

1. user opens `patentiq.app`,
2. frontend is served from Azure frontend hosting,
3. frontend calls `api.patentiq.app`,
4. backend reads current release configuration,
5. backend serves data from:
   - Gold-backed repositories,
   - model registry artifacts,
   - semantic/vector/ANN artifacts,
   - Azure Blob-hosted release manifests.

---

## 3. Recommended Azure Service Mapping

## 3.1 Frontend

Primary recommendation:

1. `Azure Container Apps`

Why:

1. the frontend is expected to be a moderately large Next.js application,
2. containerizing it keeps runtime behavior closer to local development,
3. env-var driven configuration is clearer,
4. frontend and backend can share the same deployment and scale-to-zero model,
5. it avoids overfitting the product to Static Web Apps constraints.

Alternative:

1. `Azure App Service`

Default decision:

1. `patentiq.app` -> `Azure Container Apps`

## 3.2 Backend

Primary recommendation:

1. `Azure Container Apps`

Why:

1. container-native,
2. easy GitHub Actions deployment,
3. good fit for FastAPI,
4. can scale down aggressively for demo periods,
5. simpler than Kubernetes.

Default decision:

1. `api.patentiq.app` -> `Azure Container Apps`

## 3.3 Artifact Store

Primary recommendation:

1. `Azure Blob Storage`

Blob remains the canonical store for:

1. Silver/Gold release manifests,
2. ML model artifacts,
3. calibration artifacts,
4. semantic vector phase artifacts,
5. merged semantic corpora,
6. ANN snapshots,
7. release manifests that pin active artifact versions.

## 3.4 Batch / ETL / ML Execution

For the ultimate shape:

1. local generation remains valid for development,
2. batch jobs can later run from a dedicated ETL runner container,
3. batch execution does not need to be always-on in Azure for the demo product.

For the near term:

1. continue building heavy ETL/ML/semantic artifacts locally,
2. upload the finished artifacts to Azure Blob,
3. deploy only the serving stack in Azure.

---

## 4. Containerization Strategy

PatentIQ should be split into three deployable container categories.

## 4.1 Frontend Image

Contains:

1. Next.js application,
2. runtime config,
3. no large parquet/model/vector payloads.

Recommended runtime env vars:

1. `NEXT_PUBLIC_API_BASE_URL=https://api.patentiq.app`
2. `NEXT_PUBLIC_APP_ENV=local|prod`
3. `NEXT_PUBLIC_SEMANTIC_ENABLED=true|false`
4. `NEXT_PUBLIC_REPORTS_ENABLED=true|false`
5. other environment-specific values should be injected at container runtime where possible.

Suggested image tag:

1. `ghcr.io/<org>/patentiq-frontend:vX.Y.Z`

## 4.2 Backend Image

Contains:

1. FastAPI application,
2. repository/service/router code,
3. no large semantic corpus or Gold payloads baked in,
4. logic to resolve active artifact versions from Blob-hosted manifests.

Suggested image tag:

1. `ghcr.io/<org>/patentiq-backend:vX.Y.Z`

## 4.3 ETL Runner Image

Contains:

1. Silver/Gold/ML/Semantic execution environment,
2. build dependencies,
3. optional batch-only runtime entrypoints.

Suggested image tag:

1. `ghcr.io/<org>/patentiq-etl-runner:vX.Y.Z`

This image is not required to be deployed continuously for jury demos.

---

## 5. Artifact Strategy

Do not bake heavy artifacts into app containers.

Store these in Azure Blob:

1. Gold outputs and manifests,
2. ML split registries and training manifests,
3. forecast model artifacts and calibration files,
4. serving DuckDB snapshots,
5. semantic phase artifacts,
6. merged vector corpora,
7. ANN index snapshots,
8. release metadata.

Recommended logical containers or path prefixes:

1. `gold/`
2. `ml/`
3. `semantic/`
4. `ann/`
5. `releases/`

Example structure:

```text
releases/
  v2.0.0/
    release-manifest.json
gold/
  2026-04-06-gold/
    gold_family_summary.parquet
    ...
serving/
  2026-04-06-serving/
    core_serving.duckdb
    semantic_serving.duckdb
    market_serving.duckdb
ml/
  family_future_citation_forecast_v2_2026-04-06/
    model_3y.bin
    model_5y.bin
    calibration.json
semantic/
  phase01_mvp_2026-04-06/
    vec_family_embeddings_abstracts_phase_00_of_10_mvp_demo.parquet
    vec_family_embeddings_claims_phase_00_of_03.parquet
ann/
  semantic_release_2026-04-06/
    abstracts_hnsw.index
    claims_hnsw.index
    ann_manifest.json
```

---

## 6. Release Manifest Contract

Each deployable release should have a top-level release manifest.

Suggested file:

1. `releases/vX.Y.Z/release-manifest.json`

It should pin:

1. frontend image tag,
2. backend image tag,
3. active Gold release id,
4. active forecast model release ids,
5. active semantic release id,
6. active ANN snapshot id,
7. schema/contract version,
8. deployment date.

Example shape:

```json
{
  "release_version": "v2.0.0-demo1",
  "frontend_image": "ghcr.io/org/patentiq-frontend:v2.0.0-demo1",
  "backend_image": "ghcr.io/org/patentiq-backend:v2.0.0-demo1",
  "gold_release": "2026-04-06-gold",
  "forecast_release": "family_future_citation_forecast_v2_2026-04-06",
  "semantic_release": "phase01_mvp_2026-04-06",
  "ann_release": "semantic_release_2026-04-06",
  "contract_version": "v2",
  "deployed_at": "2026-04-06"
}
```

The backend should resolve all active artifacts from this manifest rather than hard-coding asset paths.

Serving-note:

1. the backend should prefer split serving DuckDB snapshots such as:
   - `core_serving.duckdb`
   - `semantic_serving.duckdb`
   - `market_serving.duckdb`
2. these files should be downloaded from Azure Blob into Azure Container Apps local ephemeral storage at startup or first use,
3. they should not be treated as fully resident in RAM by default,
4. this keeps cold starts and container sizing more reasonable than one monolithic all-domain database file.

---

## 7. GitHub Release And Tag Strategy

## 7.1 Git Tags

Use Git tags as promotion boundaries:

1. `v2.0.0-demo1`
2. `v2.0.0-demo2`
3. `v2.0.0`

## 7.2 GitHub Releases

Each tag should create a GitHub Release that includes:

1. release notes,
2. image tags,
3. release manifest location,
4. active artifact ids,
5. rollout notes and caveats.

Heavy data artifacts should not be uploaded directly to GitHub Releases if they are large.

Instead:

1. upload them to Azure Blob,
2. reference them from the GitHub Release body and release manifest.

---

## 8. CI/CD Pattern

## 8.1 Build And Test

Use GitHub Actions for:

1. backend tests,
2. frontend tests/lint/build,
3. image builds,
4. release creation,
5. Azure deployment.

Recommended workflow split:

1. `ci.yml`
   - lint
   - tests
   - build validation
2. `publish-images.yml`
   - build and push container images to GHCR
3. `release.yml`
   - on tag
   - generate GitHub Release
   - publish release manifest
4. `deploy-azure.yml`
   - deploy frontend and backend to Azure
   - update environment settings

## 8.2 Container Registry

Use:

1. `GitHub Container Registry (GHCR)`

Why:

1. native to GitHub Actions,
2. simple release tagging,
3. clean promotion flow from source control.

## 8.3 Deployment Trigger

Recommended flow:

1. merge to `dev` -> run CI only,
2. tag approved release -> publish images + release manifest,
3. deploy workflow updates Azure services to use those tagged images.

---

## 9. DNS And Custom Domain Pattern

Recommended DNS provider:

1. `Cloudflare`

Why:

1. easy UI,
2. free DNS is sufficient,
3. fully compatible with Azure custom domains,
4. good long-term flexibility.

Recommended records:

1. `patentiq.app`
   - points to frontend Azure host
2. `www.patentiq.app`
   - optional redirect or alias to `patentiq.app`
3. `api.patentiq.app`
   - `CNAME` to backend Azure host

Important rollout rule:

1. keep DNS records as `DNS only` initially during Azure domain verification,
2. only enable Cloudflare proxy/CDN features later if needed.

Azure flow:

1. deploy frontend and backend first,
2. obtain Azure-assigned default hostnames,
3. bind custom domains in Azure,
4. create DNS records in Cloudflare,
5. wait for validation and TLS issuance.

---

## 10. Runtime Configuration

## 10.1 Frontend Environment

Frontend should know:

1. `NEXT_PUBLIC_API_BASE_URL=https://api.patentiq.app`
2. optional release metadata endpoint
3. optional feature flags for semantic / forecast / compare availability

## 10.2 Backend Environment

Backend should know:

1. Azure Blob account/container credentials or managed identity,
2. active release manifest location,
3. current environment name,
4. cache configuration,
5. optional allowed CORS origins,
6. model/semantic feature flags.

Recommended backend env vars:

1. `AZURE_STORAGE_ACCOUNT_URL`
2. `AZURE_STORAGE_CONTAINER_RELEASES`
3. `PATENTIQ_ACTIVE_RELEASE_MANIFEST`
4. `PATENTIQ_ENV`
5. `PATENTIQ_CORS_ORIGINS`

---

## 11. Cost Pattern

For a jury-demo deployment, optimize for low fixed cost and low idle compute.

Recommended deployment cost shape:

1. frontend always reachable,
2. backend scales down aggressively when unused,
3. Blob artifacts remain continuously stored,
4. heavy ETL/ML jobs are not continuously running in Azure.

Implication:

1. the main fixed monthly floor is frontend hosting + Blob storage,
2. backend compute cost should remain low if demo traffic is light,
3. the deployment is cheap enough for demo use while still looking production-real.

The exact amount will vary by:

1. artifact footprint in Blob,
2. backend CPU/memory profile,
3. demo traffic and cold starts,
4. monitoring/logging retention.

---

## 12. Availability Model

The target deployment does not require strict always-on availability.

That means:

1. frontend may remain continuously reachable,
2. backend may scale down or sleep when idle,
3. cold starts are acceptable for demo scenarios,
4. batch jobs do not need to be permanently provisioned.

This is an intentional product-demo operating mode, not a defect.

---

## 13. Security And Access

Recommended baseline:

1. HTTPS on both domains,
2. no direct public exposure of Blob paths in the frontend,
3. backend accesses private artifacts using Azure credentials,
4. CORS restricted to `patentiq.app`,
5. release manifests should not contain secrets.

Optional later additions:

1. Azure Key Vault,
2. private Blob access via managed identity,
3. Cloudflare WAF / rate limiting,
4. auth layer for non-public demo environments.

---

## 14. Rollback Pattern

Rollback should be artifact-driven, not manual file surgery.

Rollback unit:

1. Git tag / GitHub Release
2. corresponding release manifest

Rollback procedure:

1. choose prior release tag,
2. re-point frontend/backend deployment to prior image tags,
3. re-point active release manifest to prior artifact versions,
4. redeploy Azure services.

This is why release manifests must pin:

1. app images,
2. Gold version,
3. forecast version,
4. semantic/vector version,
5. ANN version.

---

## 15. Suggested Phased Rollout

## Phase 1: Demo Deployment

Deploy:

1. frontend,
2. backend,
3. Azure Blob-backed artifacts,
4. custom domains,
5. release manifest loading.

Use:

1. current Gold release,
2. MVP semantic artifacts,
3. currently promoted model outputs.

## Phase 2: Containerized Batch Capability

Add:

1. ETL runner image,
2. optional Azure-executed batch jobs for refreshes,
3. automated artifact publishing to Blob.

## Phase 3: Fully Automated Promotion

Add:

1. GitHub tag -> image publish,
2. release manifest generation,
3. Azure deploy workflow,
4. rollback-by-tag discipline.

## Phase 4: Optional GitOps

If deployment complexity grows:

1. add infra/deploy repo,
2. move environment definitions there,
3. optionally add GitOps controller later.

This is not required for the first jury-demo deployment.

---

## 16. Recommended Immediate Decisions

1. Use `patentiq.app` for frontend.
2. Use `api.patentiq.app` for backend.
3. Use `Cloudflare` for DNS.
4. Use `Azure Container Apps` for frontend.
5. Use `Azure Container Apps` for backend.
6. Keep heavy artifacts in `Azure Blob`.
7. Build/publish images with `GitHub Actions`.
8. Use `GitHub tags + Releases + release manifests` as the promotion contract.

---

## 17. What Not To Do

Avoid:

1. baking Gold/model/vector artifacts into app images,
2. using GitHub Releases as the primary runtime store for huge artifacts,
3. introducing Kubernetes before the deployment shape is stable,
4. relying on Azure default URLs in the final jury-facing product,
5. coupling release promotion to manual file edits on running services.

---

## 18. Final Recommendation

The cleanest PatentIQ V2 deployment shape is:

1. `patentiq.app` on Azure Container Apps,
2. `api.patentiq.app` on Azure Container Apps,
3. Azure Blob as the canonical artifact layer,
4. Cloudflare DNS for simple domain management,
5. GitHub Actions + Git tags + GitHub Releases as the release automation path.

This gives:

1. a real deployed product shape,
2. low demo-month cost,
3. clean rollout/rollback discipline,
4. no unnecessary infra complexity,
5. a path to later production hardening without throwing away the architecture.

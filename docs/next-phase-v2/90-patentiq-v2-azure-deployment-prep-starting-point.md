# PatentIQ V2 Azure Deployment Prep Starting Point

## Purpose

This note captures the audited starting point before deployment-preparation implementation begins for PatentIQ V2.

It records:

1. the current repo and artifact baseline,
2. the confirmed deployment gaps,
3. the required serving-data migration direction,
4. the initial execution order for local and Azure deployment readiness.

Audit date: `2026-04-17`

Related notes:

1. [21-patentiq-v2-azure-runtime-and-storage-architecture.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/21-patentiq-v2-azure-runtime-and-storage-architecture.md)
2. [36-patentiq-v2-azure-deployment-and-release-blueprint.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/36-patentiq-v2-azure-deployment-and-release-blueprint.md)
3. [40-patentiq-v2-backend-serving-runtime-config-and-cloud-local-parity.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/40-patentiq-v2-backend-serving-runtime-config-and-cloud-local-parity.md)
4. [41-patentiq-v2-etl-serving-snapshots-packaging-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/41-patentiq-v2-etl-serving-snapshots-packaging-contract.md)
5. [63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/63-patentiq-v2-ui-serving-silver-gold-boundary-audit.md)
6. [70-patentiq-v2-current-serving-rebuild-audit.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/70-patentiq-v2-current-serving-rebuild-audit.md)
7. [semantic-similarity-and-vector-layer-requirements.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-similarity-and-vector-layer-requirements.md)
8. [bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/new-feature-ideas/semantic-and-model-development/bge-m3-and-patentsberta-local-installation-storage-and-runtime-guide.md)

---

## Starting Point Summary

The repo already contains the right architectural direction in the docs:

1. Azure Blob or ADLS remains the canonical artifact store.
2. ETL is expected to produce serving DuckDB snapshots.
3. the backend should consume released serving artifacts rather than query remote parquet directly at request time,
4. local and Azure runtime paths should share the same artifact-resolution contract,
5. frontend and backend should be deployed as lightweight containers with heavy artifacts kept outside images.

However, the codebase is only partially aligned with that target.

The deployment-preparation work therefore starts from a transitional state, not a sealed deployment-ready state.

---

## Confirmed Repo Target

For deployment work, the active V2 code targets are:

1. [frontend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2)
2. [backend_v2](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2)

The preserved legacy/reference paths remain:

1. [frontend_v1](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v1)
2. [backend](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend)

This matters because the deployment-prep implementation should not be applied to `backend/` or `frontend_v1`.

---

## Confirmed Serving Artifact Baseline

Current local serving artifacts already exist under [etl/data/serving](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/data/serving):

1. `core_serving.duckdb` at about `10G`
2. `semantic_serving.duckdb` at about `881M`
3. `market_serving.duckdb` at about `780K`
4. `serving_snapshot_manifest.json`
5. `serving_snapshot_audit.json`

Current manifest/audit observations:

1. `built_at` is `2026-04-10T10:11:20+00:00`
2. `serving_release` is still `2026-03-15-serving`
3. the build timestamp and release identifier are therefore out of sync
4. this metadata drift must be corrected before formal release promotion and rollback can be trusted

Current serving-domain coverage:

1. `core_serving.duckdb` includes current family, portfolio, compare, publication-evidence, forecast, and threat-serving tables
2. `semantic_serving.duckdb` currently exposes `semantic_match_context`
3. `market_serving.duckdb` currently exposes `market_intelligence_overview`, `market_intelligence_segments`, and `market_intelligence_timeseries`

---

## Current Code Reality

### 1. Backend runtime configuration is already partially prepared

The current V2 backend settings already expose a serving-artifact contract:

1. `artifact_mode` defaults to `local_fs`
2. `local_artifact_root` defaults to `etl/data/serving`
3. `serving_manifest_path` points to the local serving manifest
4. `serving_manifest_url` and `serving_base_url` already exist for remote resolution
5. `raw_parquet_fallback_enabled` is still `True`

This means the runtime shape exists, but the backend is still in compatibility-bridge mode rather than strict serving-only mode.

### 2. Artifact resolution is not yet Azure-ready

[backend_v2/infrastructure/artifacts/locator.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/infrastructure/artifacts/locator.py) already supports:

1. `local_fs`
2. `azure_blob_cached`

But the remote path is not production-ready yet:

1. it uses `urllib.request.urlopen` rather than the Azure Blob SDK,
2. it does not use Microsoft Entra or managed identity,
3. it resolves `core` and `semantic` serving snapshots but not `market`,
4. it is therefore not yet the secure remote-serving path that Azure Container Apps should rely on.

### 3. Repository serving migration is incomplete

Serving-first status by repository:

1. `PublicationRepository` is the closest to the target state and can read from `core_db.publication_evidence_serving`, but still retains fallback behavior.
2. `FamilyRepository` attaches `core_serving.duckdb` for some paths, but still performs many `read_parquet(...)` queries.
3. `PortfolioRepository` also mixes serving tables with many direct parquet reads.
4. `MarketIntelligenceRepository` is still parquet-only even though `market_serving.duckdb` already exists.
5. `SemanticRepository` uses `semantic_serving.duckdb` for context, while vector parquet remains separate for semantic search.

Important serving rule at this starting point:

1. family, portfolio, publication, compare, and market data-access layers should be migrated toward released serving DuckDB paths,
2. raw vector and ANN assets do not need to be forced into the serving DuckDB files if the semantic runtime continues to use released vector artifacts separately.

### 4. ETL can build serving snapshots but does not yet publish them as full release artifacts

The ETL stack already contains the serving stage group under [etl/src/patentiq_etl/serving](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/serving).

But the publish path is still incomplete:

1. [etl/src/patentiq_etl/publish/run.py](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/src/patentiq_etl/publish/run.py) writes a release manifest and can upload a prepared release directory,
2. the current publish step does not explicitly package the `serving/` release payload as part of the released artifact set,
3. `azure_publish_enabled` is currently `false` in [etl/conf/build.yaml](/Users/ardaerkan/Documents/MIGRATE/patent-iq/etl/conf/build.yaml),
4. there is not yet a sealed release manifest contract that pins container image tags together with the serving release identifiers.

### 5. Local one-command boot is not ready yet

Local dev scripts exist:

1. [scripts/dev_v2_local.sh](/Users/ardaerkan/Documents/MIGRATE/patent-iq/scripts/dev_v2_local.sh)
2. [backend_v2/scripts/serve_local.sh](/Users/ardaerkan/Documents/MIGRATE/patent-iq/backend_v2/scripts/serve_local.sh)

The frontend config is also container-aware:

1. [frontend_v2/lib/config.ts](/Users/ardaerkan/Documents/MIGRATE/patent-iq/frontend_v2/lib/config.ts) defaults to local backend usage
2. it already contains `host.docker.internal` handling for browser-side local Docker scenarios

But the repo is still missing the actual packaging layer:

1. no backend Dockerfile,
2. no frontend Dockerfile,
3. no root `compose.yaml` or `docker-compose.yml`,
4. no clone-and-run local path that guarantees both services boot cleanly with the required serving data.

---

## Confirmed Deployment Blockers

At the start of this deployment-prep work, the critical blockers are:

1. the backend still has direct parquet reads across family, portfolio, and market-serving paths,
2. `market_serving.duckdb` exists but is not yet wired into the backend repository layer,
3. `raw_parquet_fallback_enabled=True` means the serving contract is still transitional,
4. ETL publish does not yet promote serving DuckDB snapshots as first-class release artifacts,
5. the remote artifact locator is not yet secure Azure Blob access via managed identity,
6. there is no Docker Compose boot path for repo-clone local startup,
7. release metadata is not yet cleanly versioned across build date, serving release, and deployable images,
8. the domain plan in the docs still assumes `patentiq.app` while the intended target discussed for this planning pass is `patentiq.apps`

---

## Initial Execution Order

The starting recommendation is:

1. lock the deployment target on `backend_v2` and `frontend_v2`,
2. finish the serving migration for backend data-access layers, with market first, then family, then portfolio, then remaining publication fallback cleanup,
3. extend ETL publish so the release contract includes `bronze`, `silver`, `gold`, `ml`, `semantic`, and `serving`,
4. replace ad hoc remote fetching with Azure Blob SDK plus managed-identity-compatible authentication,
5. add backend and frontend Dockerfiles plus a root `compose.yaml`,
6. make local compose support both local serving-volume usage and remote serving-download hydration,
7. deploy backend and frontend as separate Azure Container Apps backed by ACR and private Blob storage,
8. finalize domain wiring and CORS on `patentiq.apps` and `api.patentiq.apps` if `.apps` is the real production domain

This order keeps the data contract ahead of the container and domain work.

That is the right order because image packaging and ACA rollout should not be finalized while the backend still depends on unstable parquet-serving paths.

---

## Decisions That Must Be Locked Early

Before implementation goes too far, the following decisions need to be explicit:

1. whether the production domain is truly `patentiq.apps` rather than `patentiq.app`
2. whether local-first compose should default to mounting local serving artifacts when they already exist, or downloading the active serving release from Blob on first boot
3. whether Azure Blob access for the backend will be managed identity plus private container access, which is the recommended target, or SAS or connection-string based fallback only for transitional local ops
4. whether the release manifest should pin the backend image tag, frontend image tag, serving release, semantic/vector release, and active release metadata path

---

## External Azure References Used For This Starting Point

These official references were used to align the deployment assumptions with current Azure behavior:

1. Azure Container Apps custom domains and free managed certificates: https://learn.microsoft.com/en-us/azure/container-apps/custom-domains-managed-certificates
2. Azure Container Apps managed identities: https://learn.microsoft.com/en-us/azure/container-apps/managed-identity
3. Azure Storage Blob CLI quickstart with `--auth-mode login`: https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-cli
4. Azure Storage Blob download with Python and `DefaultAzureCredential`: https://learn.microsoft.com/en-us/azure/storage/blobs/storage-blob-download-python

---

## Small Validation Note

As a narrow smoke check of the existing artifact-resolution baseline, the current V2 artifact-locator tests pass:

1. `backend_v2/tests/test_artifact_locator.py`
2. result: `3 passed`

This does not prove deployment readiness.

It only confirms that the current local artifact-locator test slice is green before the deployment-preparation changes start.

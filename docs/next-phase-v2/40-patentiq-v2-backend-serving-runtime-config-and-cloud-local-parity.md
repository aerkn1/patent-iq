# PatentIQ V2 Backend Serving Runtime Config And Cloud-Local Parity

## Purpose

Define the backend V2 serving plan so that:

1. semantic serving works from the same code path locally and in Azure,
2. forecast and later model-serving flows also follow the same runtime contract,
3. environment differences are expressed through configuration rather than forked code,
4. heavy artifacts remain outside the backend image,
5. local development, jury demo deployment, and later production hardening all share one deployable architecture.

This note is the backend-specific implementation companion to:

1. [36-patentiq-v2-azure-deployment-and-release-blueprint.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/36-patentiq-v2-azure-deployment-and-release-blueprint.md)
2. [16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/16-patentiq-v2-semantic-search-and-comparison-flow-and-guardrails.md)
3. [09-forecast-v2-mvp-use-cases-and-feature-semantics.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/09-forecast-v2-mvp-use-cases-and-feature-semantics.md)
4. [39-patentiq-v2-azure-openai-gpt-4o-mini-llm-augmentation-contract.md](/Users/ardaerkan/Documents/MIGRATE/patent-iq/docs/next-phase-v2/39-patentiq-v2-azure-openai-gpt-4o-mini-llm-augmentation-contract.md)

---

## 1. Current Problem

The current backend is not ready for V2 serving parity across local and cloud.

Current limitations:

1. startup assumes one hardcoded DuckDB path and one startup sequence,
2. data access assumes Hugging Face parquet URLs and local cache download at startup,
3. model serving assumes one Hugging Face-hosted citation model registry,
4. semantic serving does not yet exist in backend runtime form,
5. there is no release-manifest-driven artifact resolution layer,
6. appln-first V1 services and family-first V2 services are not yet separated cleanly,
7. environment behavior is mostly implicit instead of governed by settings.

So the V2 backend should not be built by extending the existing V1 assumptions directly.

---

## 2. Core Runtime Principle

The backend must behave as a `single configurable serving application`.

That means:

1. local and Azure use the same services, repositories, and routes,
2. only settings differ,
3. artifact locations differ by manifest and environment,
4. startup chooses the right providers from config,
5. frontend should not know whether the backend is running locally or in Azure.

The backend must never depend on:

1. hardcoded local absolute paths,
2. hardcoded Hugging Face-only artifact URLs,
3. container-baked semantic corpora,
4. separate local-vs-cloud service implementations for the same endpoint behavior.

---

## 3. Recommended Backend V2 Folder Shape

Create a dedicated V2 boundary under `backend/v2/`.

Suggested structure:

```text
backend/
  v2/
    api/
      routes/
        families.py
        portfolios.py
        semantic.py
        forecast.py
        market.py
        reports.py
        health.py
    application/
      services/
        family_summary_service.py
        family_forecast_service.py
        portfolio_forecast_service.py
        semantic_search_service.py
        semantic_compare_service.py
        artifact_release_service.py
        llm_summary_service.py
    domain/
      schemas/
      errors.py
    infrastructure/
      config/
        settings.py
      artifacts/
        release_manifest_resolver.py
        artifact_locator.py
        blob_client.py
        local_fs_client.py
      duckdb/
        connection.py
        registry_builder.py
      ml/
        forecast_model_registry.py
      semantic/
        ann_index_registry.py
        embedding_query_encoder.py
      repositories/
        family_summary_repo.py
        family_history_repo.py
        family_forecast_feature_repo.py
        portfolio_summary_repo.py
        semantic_family_repo.py
        semantic_context_repo.py
```

Key rule:

1. V1 remains under current `backend/...`,
2. V2 routes are mounted at `/api/v2/...`,
3. all new serving logic goes under `backend/v2/...`,
4. shared low-level helpers can be reused later if they are truly environment-neutral.

---

## 4. Runtime Profiles

The same backend should support only two runtime profiles:

1. `local`
2. `prod`

This is sufficient for PatentIQ V2.

Reason:

1. fewer profiles reduce accidental config drift,
2. local should already be able to exercise cloud-facing integrations when credentials are present,
3. the Azure jury deployment is operationally a `prod` profile with smaller scale settings, not a different application mode.

## 4.1 Local

Purpose:

1. local API development,
2. semantic search debugging,
3. model-serving validation,
4. integration tests against real or sampled local artifacts.

Expected storage shape:

1. artifacts available from local filesystem,
2. optional local cache hydrated from Azure Blob or Hugging Face,
3. `.env.local` or equivalent config file points to local manifest and local artifact roots.

## 4.2 Prod

Purpose:

1. Azure-hosted jury demo deployment,
2. later remote production deployment,
3. same features as local runtime, with cloud artifact resolution and stronger readiness guarantees.

Expected storage shape:

1. release manifest in Azure Blob,
2. Gold/model/semantic/ANN artifacts in Azure Blob,
3. backend local ephemeral cache inside Azure Container Apps filesystem,
4. backend warms only the artifacts required by the active routes.

The core architecture should not change between the two profiles.

---

## 5. Config-First Runtime Contract

All environment differences should be expressed through settings.

Recommended settings object:

`backend/v2/infrastructure/config/settings.py`

It should define typed settings for:

1. app identity,
2. route behavior,
3. artifact resolution,
4. DuckDB runtime,
5. semantic runtime,
6. model runtime,
7. caching,
8. Azure/OpenAI usage,
9. CORS and external URLs.

Recommended environment variables:

```text
PATENTIQ_ENV=local|prod
PATENTIQ_API_VERSION=v2
PATENTIQ_CORS_ORIGINS=http://localhost:3000,https://patentiq.app

PATENTIQ_RELEASE_MANIFEST_SOURCE=local|azure_blob
PATENTIQ_RELEASE_MANIFEST_PATH=/abs/path/to/release-manifest.json
PATENTIQ_RELEASE_MANIFEST_BLOB_URL=https://.../releases/v2.0.0-demo1/release-manifest.json

PATENTIQ_ARTIFACT_MODE=local_fs|azure_blob_cached
PATENTIQ_LOCAL_ARTIFACT_ROOT=/abs/path/to/local/artifacts
PATENTIQ_CACHE_DIR=/tmp/patentiq-cache

PATENTIQ_AZURE_STORAGE_ACCOUNT_URL=https://<account>.blob.core.windows.net
PATENTIQ_AZURE_STORAGE_CONTAINER_RELEASES=releases
PATENTIQ_AZURE_STORAGE_CONTAINER_GOLD=gold
PATENTIQ_AZURE_STORAGE_CONTAINER_ML=ml
PATENTIQ_AZURE_STORAGE_CONTAINER_SEMANTIC=semantic
PATENTIQ_AZURE_STORAGE_CONTAINER_ANN=ann

PATENTIQ_DUCKDB_PATH=/tmp/patentiq-v2.duckdb
PATENTIQ_DUCKDB_THREADS=4
PATENTIQ_DUCKDB_MEMORY_LIMIT=8GB

PATENTIQ_SEMANTIC_DEFAULT_MODE=ann
PATENTIQ_SEMANTIC_ALLOW_EXACT_DEBUG=true
PATENTIQ_SEMANTIC_QUERY_TOP_K_DEFAULT=10
PATENTIQ_SEMANTIC_QUERY_TOP_K_MAX=50

PATENTIQ_FORECAST_ARTIFACT_SOURCE=local_fs|azure_blob_cached
PATENTIQ_FORECAST_MODEL_RELEASE=family_future_citation_forecast_v2_2026-04-06

PATENTIQ_AZURE_OPENAI_ENABLED=true
PATENTIQ_AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com
PATENTIQ_AZURE_OPENAI_API_KEY=...
PATENTIQ_AZURE_OPENAI_API_VERSION=2024-10-21
PATENTIQ_AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini

PATENTIQ_LOG_LEVEL=INFO
```

Rules:

1. all routes must resolve behavior through settings,
2. no route or service should inspect Azure/local details directly,
3. settings choose provider implementations at startup,
4. the same route code must work in both local and Azure.

Important rule:

1. local profile must be able to call Azure OpenAI too,
2. Azure-only integrations should not be artificially disabled in local,
3. the difference is only whether credentials and endpoints are configured.

---

## 6. Artifact Resolution Strategy

The backend should not know artifact URLs directly.

Instead, it should resolve artifacts in two stages:

1. resolve active `release manifest`,
2. resolve concrete artifact locations from that manifest.

## 6.1 Release Manifest

The active release manifest should pin:

1. Gold release id,
2. forecast model release id,
3. semantic release id,
4. ANN release id,
5. semantic scope caveats,
6. optional LLM deployment id,
7. contract version.

Recommended shape:

```json
{
  "release_version": "v2.0.0-demo1",
  "artifact_contract_version": "1",
  "gold_release": "2026-04-06-gold",
  "forecast_release": "family_future_citation_forecast_v2_2026-04-06",
  "semantic_release": "semantic-mvp-2026-04-06",
  "ann_release": "semantic-mvp-2026-04-06",
  "semantic_scope": {
    "abstract_scope": "partial_mvp_phase_00_of_10",
    "claim_scope": "full_claim_backed_current_universe"
  }
}
```

## 6.2 Artifact Locator

V2 should provide an `ArtifactLocator` abstraction.

Responsibilities:

1. given a release manifest, resolve all required file URIs,
2. support `local_fs` and `azure_blob_cached` modes,
3. materialize remote files into a local cache when needed,
4. return local file paths for downstream DuckDB, HNSW, and model loaders.

Important rule:

All serving components should consume local file paths after resolution.

This keeps:

1. DuckDB usage simple,
2. HNSW loading simple,
3. model loading simple,
4. runtime behavior stable across environments.

---

## 7. Cache Strategy

The backend should use a `read-through cache`, but not start with Redis as a hard dependency.

Recommended cache layers:

1. `in-process memory cache`
   - for parsed manifests, loaded model metadata, loaded ANN registries, short-lived query memoization,
2. `local filesystem artifact cache`
   - for parquet, model, ANN, and manifest files resolved from Azure Blob,
3. optional `Redis` later
   - only if multi-replica coordination or shared hot-response caching becomes necessary.

So the default V2 design should be:

1. memory cache for runtime objects,
2. local disk cache for fetched artifacts,
3. no Redis requirement for the first local/Azure deployment.

## 7.1 Local

1. local files may already exist in repo or a local artifact directory,
2. if configured, local runtime may still hydrate missing artifacts from Azure Blob,
3. cache location should be configurable and safe to delete.

## 7.2 Prod

1. backend starts with an empty or partial ephemeral cache,
2. on startup, only critical manifests and minimum serving artifacts are fetched,
3. large assets are fetched lazily or warmed selectively,
4. repeated requests hit the local cache for the lifetime of the container replica.

## 7.3 Warming Policy

Startup should warm:

1. release manifest,
2. semantic manifest,
3. forecast model metadata,
4. minimum payloads needed for health endpoints.

Optional eager warm:

1. claim ANN snapshot,
2. abstract ANN snapshot,
3. forecast model binaries.

For prod runtime:

1. warm claim ANN and forecast models eagerly,
2. warm abstract ANN eagerly if semantic workspace is part of the demo,
3. do not warm every Gold parquet unless a route needs it immediately.

---

## 8. DuckDB Strategy

DuckDB should remain the serving query engine for Gold and supporting marts, but V2 must remove current hardcoded assumptions.

Current issues in V1:

1. one hardcoded `analytics.duckdb` path,
2. one hardcoded parquet registry,
3. startup assumes Hugging Face-hosted parquet downloads.

V2 strategy:

1. build the parquet registry dynamically from resolved artifact files,
2. use a V2 connection manager under `backend/v2/infrastructure/duckdb/`,
3. keep DB path configurable,
4. keep threads and memory configurable,
5. register only the views required by active V2 repositories.

Recommended V2 registry behavior:

1. manifest points to Gold parquet files,
2. `registry_builder.py` maps those files to DuckDB view names,
3. repositories query stable V2 view names,
4. local and cloud differ only in how the files were resolved.

Important performance decision:

1. do not treat remote Azure Blob parquet reads as the default serving path,
2. use Azure Blob as the canonical store,
3. resolve required files into the local filesystem cache first,
4. let DuckDB query local cached files during request handling.

Why:

1. remote parquet reads over object storage incur extra latency and range-request overhead,
2. repeated interactive serving over remote parquet is avoidable,
3. Azure Container Apps plus local ephemeral cache is a better fit for jury-demo and moderate production traffic.

So the expected answer is:

1. same-region Azure Blob access is workable,
2. but direct remote DuckDB reads are still slower and less predictable than local cached reads,
3. therefore serving should be `Blob as source of truth, local cache as query substrate`.

## 8.1 Serving Snapshot Strategy

The preferred V2 serving pattern is not:

1. one giant remote parquet registry,
2. or one giant monolithic `analytics_v2.duckdb` by default.

The preferred pattern is:

1. build domain-oriented serving DuckDB snapshots during ETL/release packaging,
2. store them in Azure Blob as versioned artifacts,
3. download only the required snapshots into Azure Container Apps local ephemeral storage,
4. open DuckDB against those local files.

Recommended first split:

1. `core_serving.duckdb`
   - family summary
   - portfolio summary
   - forecast summary
   - family/owner bridge
   - core legal and history views needed across many routes
2. `semantic_serving.duckdb`
   - semantic match context
   - semantic family metadata needed after ANN retrieval
   - semantic compare support tables
3. `market_serving.duckdb`
   - market overview
   - market segments
   - market timeseries

Why this is preferred:

1. smaller bootstrap downloads,
2. better scale-to-zero wakeups,
3. lower risk of overprovisioning container memory,
4. cleaner domain ownership,
5. routes usually need only one domain snapshot.

## 8.2 RAM And Storage Behavior

These `.duckdb` snapshots should live primarily on local ephemeral disk, not be treated as fully resident in RAM.

Important rule:

1. downloading an `8GB` DuckDB file does not mean `8GB` of RAM is immediately consumed,
2. DuckDB reads from the local file,
3. RAM usage is driven mainly by:
   - query working set,
   - buffers,
   - result materialization,
   - configured DuckDB memory limit.

So the main risks of oversized snapshots are:

1. longer cold starts,
2. larger local disk usage,
3. greater chance that hot queries need more RAM,
4. indirect pressure to choose a larger container SKU.

That is why split serving snapshots are preferred over one very large snapshot for PatentIQ V2.

## 8.3 First-Pass Serving Snapshot Allocation

The first V2 release should define explicit inclusion boundaries for each serving snapshot.

Important rule:

1. serving snapshots should prefer already-aggregated Gold marts,
2. large raw Silver ledgers should not be copied blindly into serving DBs,
3. when a route needs heavy history detail, prefer derived serving tables over raw event tables,
4. vector payloads and ANN indexes remain separate artifacts and should not be stored inside DuckDB snapshots.

### `core_serving.duckdb`

Purpose:

1. family page core payloads,
2. portfolio page core payloads,
3. family-first forecast serving,
4. publication-to-family resolution,
5. report metadata used across most routes.

Include directly from current Gold:

1. `gold_family_summary`
2. `gold_family_blocking_power`
3. `gold_family_heritage_summary`
4. `gold_portfolio_summary`
5. `gold_portfolio_forecast_summary`
6. `gold_portfolio_heritage_summary`
7. `gold_portfolio_threat_matrix`

Include directly from current Silver where they are already compact and serving-relevant:

1. `silver_family_status_pt`
2. `silver_family_owner_bridge`
3. `silver_assignee_harmonized`
4. `silver_family_wipo_fields`
5. `silver_family_citation_metrics`
6. `silver_family_coverage_metrics`
7. `silver_family_member_publications`
8. `silver_family_oecd_quality`

Prefer derived serving tables rather than copying the raw heavy sources directly:

1. `family_status_history_serving`
   - source: `silver_family_status_history`
   - should keep only page/report-safe historical fields and time slices
2. `branch_status_summary_serving`
   - source: `silver_branch_status_history_dense`
   - should summarize branch legal states instead of carrying the full dense ledger
3. `publication_evidence_serving`
   - source: `silver_family_member_publications` plus selected publication fields
   - should support the publication page without needing every raw text/legal ledger
4. `family_forecast_features_serving`
   - source: Phase 03 feature mart once finalized
   - keeps forecast serving isolated from raw training-time joins

Do not include in first-pass `core_serving.duckdb`:

1. `silver_legal_status_event_ledger`
2. `silver_branch_status_history_dense` as raw full table
3. `silver_family_text_representative`
4. raw semantic vectors or ANN payloads

### `semantic_serving.duckdb`

Purpose:

1. enrich ANN hits with family context,
2. support semantic compare context,
3. support semantic result tables without duplicating the full family page contract.

Include directly:

1. `gold_semantic_match_context`

Optional compact supporting tables:

1. `semantic_family_resolution_serving`
   - family id to representative publication / provenance metadata
2. `semantic_compare_context_serving`
   - only if compare routes need additional compact overlays not already present in `gold_semantic_match_context`

Keep outside `semantic_serving.duckdb`:

1. abstract embedding parquet
2. claim embedding parquet
3. ANN `.bin` files
4. ANN family-id arrays

Reason:

1. semantic retrieval should use ANN artifacts directly,
2. DuckDB should only provide post-retrieval context joins.

### `market_serving.duckdb`

Purpose:

1. market intelligence overview,
2. market segment detail,
3. market and field trend panels,
4. compare/report market overlays.

Include directly from Gold:

1. `gold_market_intelligence_overview`
2. `gold_market_intelligence_segments`
3. `gold_market_intelligence_timeseries`
4. `gold_portfolio_field_timeseries`
5. `gold_family_field_contributions`
6. `gold_family_field_contributions_timeseries`
7. `gold_family_blocking_power_timeseries`

Optional compact Silver support:

1. `silver_market_intelligence_segments`
2. `silver_market_intelligence_timeseries`
3. derived field/jurisdiction slices if a route needs pre-Gold debug visibility

Do not include in first-pass `market_serving.duckdb`:

1. `silver_global_tech_trends_timeseries` raw if Gold covers the serving need
2. `silver_local_tech_trends_timeseries` raw if Gold covers the serving need
3. very large intermediate field-contribution staging tables

## 8.4 Route-To-Snapshot Mapping

The first V2 routes should map to snapshots like this.

Use `core_serving.duckdb` only:

1. family summary
2. publication evidence
3. family forecast
4. portfolio summary
5. portfolio forecast
6. report metadata that is not semantic or market-heavy

Use `semantic_serving.duckdb` plus ANN artifacts:

1. text-to-family semantic search
2. family neighbors
3. family semantic compare
4. semantic evidence sections in reports

Use `market_serving.duckdb`:

1. market overview
2. market segments
3. market timeseries
4. hotspot/cooling overlays

Use more than one snapshot only when needed:

1. portfolio report with market overlays: `core + market`
2. semantic compare report with family summary: `core + semantic`
3. large executive report: orchestrate at service level rather than forcing one huge cross-database SQL path

## 8.5 Initial Size Expectations

Rough planning ranges for the first release:

1. `core_serving.duckdb`
   - likely the largest
   - target roughly `2GB` to `4GB`
2. `semantic_serving.duckdb`
   - moderate
   - target roughly `<1GB` to `1.5GB`
3. `market_serving.duckdb`
   - comparatively smaller
   - target roughly `<1GB` to `2GB`

These are planning ranges, not hard guarantees.

The important goal is:

1. avoid one `6GB` to `8GB+` monolith if the same serving behavior can be achieved with domain splits,
2. keep the heaviest hot-serving snapshot focused on actual V2 route needs,
3. keep semantic vectors and ANN files out of the DuckDB snapshots.

---

## 9. Semantic Serving Plan

Semantic serving is now artifact-ready and should become the first major V2 serving module.

## 9.1 Inputs

Canonical local paths after artifact resolution:

1. abstract payload parquet,
2. claim payload parquet,
3. abstract HNSW snapshot,
4. abstract family id array,
5. claim HNSW snapshot,
6. claim family id array,
7. semantic manifests and audit JSONs.

## 9.2 Semantic Runtime Components

Recommended components:

1. `AnnIndexRegistry`
   - loads HNSW indexes and aligned family-id arrays,
2. `EmbeddingQueryEncoder`
   - embeds user query text using the same released models,
   - local mode may use locally available models,
   - cloud demo mode may use a CPU-loaded sentence-transformers runtime or a pre-approved embedding service later,
3. `SemanticFamilyRepository`
   - fetches family metadata and representative text snippets for result ids,
4. `SemanticSearchService`
   - orchestrates text-to-family and family-to-family retrieval,
5. `SemanticCompareService`
   - compares two families or two family result sets.

## 9.3 Serving Modes

Supported modes:

1. `ann`
   - default for all user-facing search,
2. `exact_debug`
   - internal/debug-only validation mode,
3. `hybrid_ann_plus_exact_check`
   - optional diagnostic mode for limited requests.

## 9.4 Query Spaces

Keep separate:

1. `vector_abstract`
2. `vector_claims`

Rules:

1. abstract query text must hit abstract embeddings,
2. claim query text must hit claim embeddings,
3. family neighbor routes may expose both spaces separately,
4. UI must display coverage caveats returned by the backend.

## 9.5 Semantic Response Contract

Each response should include:

1. `vector_space`,
2. `search_mode`,
3. `semantic_release`,
4. `ann_release`,
5. `scope_status`,
6. `coverage_caveat`,
7. `result_count`,
8. result items with:
   - `docdb_family_id`
   - `score`
   - `queryable_text_preview`
   - `primary_wipo_field`
   - `family_composite_status`
   - `oecd_quality_percentile`
   - `family_ui_blocking_power_score`
   - `family_earliest_priority_date`

For current MVP:

1. abstract responses must state partial coverage,
2. claim responses may state full claim-backed coverage.

---

## 10. Forecast And Other Model-Serving Plan

Forecast and later model-serving must follow the same artifact-driven contract as semantic serving.

## 10.1 Model Types In Scope

Near-term:

1. family future citation forecast `3y`,
2. family future citation forecast `5y`.

Later:

1. family lapse risk,
2. family friction risk,
3. jurisdiction-field trend forecasts,
4. portfolio-derived prediction layer.

## 10.2 Model Registry Contract

V2 should introduce a dedicated model registry under:

`backend/v2/infrastructure/ml/forecast_model_registry.py`

Responsibilities:

1. resolve the active model release from the release manifest,
2. fetch model binaries and metadata from local FS or Azure Blob cache,
3. load model objects into memory,
4. expose feature contract version and metadata,
5. fail fast when the release contract mismatches repository features.

## 10.3 Feature Repositories

Feature repos must also be local/cloud-neutral.

That means:

1. they query V2 DuckDB views,
2. they do not care where the source parquet came from,
3. they work from manifest-resolved local file paths only.

Recommended family-first repos:

1. `family_forecast_feature_repo.py`
2. `family_summary_repo.py`
3. `family_history_repo.py`
4. `portfolio_summary_repo.py`

## 10.4 Forecast Response Contract

Each forecast response should include:

1. `entity_grain`,
2. `model_release`,
3. `feature_contract_version`,
4. `forecast_horizon`,
5. `prediction`,
6. `percentile`,
7. `interval`,
8. `top_drivers`,
9. `coverage_status`,
10. `caveats`.

The route should not care whether models came from:

1. local artifact directory,
2. Azure Blob cache.

---

## 11. Query Encoding Strategy For Semantic Routes

One important runtime decision is how semantic query text is embedded in local and cloud environments.

Recommended V2 policy:

## 11.1 Local

Use the released local embedding models directly.

Why:

1. easiest for debugging,
2. consistent with ETL-generated embeddings,
3. no network dependency.

## 11.2 Azure Demo

Use the same local-model runtime inside the backend container if performance is acceptable for demo traffic.

Reason:

1. traffic is light,
2. container scale is modest,
3. using the exact same released embedding models avoids embedding drift.

If later needed:

1. move query encoding into a separate embedding service,
2. keep the `EmbeddingQueryEncoder` interface unchanged.

The first V2 semantic serving version should not depend on an external embedding API for search.

---

## 12. LLM Serving Compatibility

LLM augmentation is optional and must remain isolated from core serving truth.

Recommended backend contract:

1. deterministic services compute data and scores first,
2. optional `llm_summary_service.py` takes structured payloads,
3. a centralized Azure OpenAI client/provider is configured through settings,
4. if LLM config is absent, routes still work and return deterministic payloads without narrative text.

Recommended central components:

1. `backend/v2/infrastructure/llm/azure_openai_client.py`
2. `backend/v2/application/services/llm_summary_service.py`

The Azure OpenAI client should:

1. read endpoint, key, deployment, and API version from env,
2. work in both `local` and `prod`,
3. expose reusable methods for:
   - report summaries,
   - compare summaries,
   - forecast explanations,
   - semantic explanations,
4. remain swappable later if another provider is added.

This ensures:

1. local backend can run with LLM disabled,
2. Azure demo can run with LLM enabled,
3. no endpoint becomes non-functional if the LLM layer is unavailable.

---

## 13. Health, Readiness, And Fallback

V2 should expose explicit runtime health endpoints.

Recommended health views:

1. `/api/v2/health/live`
   - process alive
2. `/api/v2/health/ready`
   - release manifest loaded,
   - DuckDB ready,
   - semantic registry ready if enabled,
   - forecast model registry ready if enabled
3. `/api/v2/health/artifacts`
   - active artifact versions,
   - cache status,
   - semantic scope flags,
   - forecast model release

Fallback rules:

1. if semantic ANN is unavailable:
   - semantic routes return service-unavailable with explicit artifact error,
2. if LLM is unavailable:
   - narrative fields omitted, deterministic payload still returned,
3. if one model release is unavailable:
   - only dependent endpoints fail,
4. startup should not crash because an unrelated optional subsystem is unavailable unless the configured runtime mode requires it.

---

## 14. Local And Azure Startup Profiles

Use explicit startup profiles instead of one monolithic eager boot.

## 14.1 Local Profile

Startup sequence:

1. load settings,
2. load release manifest,
3. resolve artifacts from local paths or local cache,
4. initialize DuckDB,
5. optionally initialize forecast registry,
6. optionally initialize semantic ANN registry,
7. leave optional LLM service disabled unless configured.

## 14.2 Azure Demo Profile

Startup sequence:

1. load settings,
2. fetch release manifest from Azure Blob,
3. warm required artifacts into local cache,
4. initialize DuckDB with resolved Gold files,
5. initialize forecast registry,
6. initialize semantic ANN registry,
7. initialize LLM client if enabled,
8. publish readiness only after required serving layers are ready.

The only difference should be settings and artifact source.

### 2026-04-10 backend-v2 implementation note

The current `backend_v2` codebase now includes the first concrete local/cloud-parity serving-artifact path for compare serving:

1. `PATENTIQ_V2_ARTIFACT_MODE=local_fs|azure_blob_cached`
2. `PATENTIQ_V2_SERVING_MANIFEST_PATH` for local runs
3. `PATENTIQ_V2_SERVING_MANIFEST_URL` plus `PATENTIQ_V2_CACHE_DIR` for Azure-like cached runs
4. a manifest-driven `ArtifactLocator` that always returns a local file path to downstream repositories
5. family compare now prefers `core_serving.duckdb` table `family_compare_current_serving`
6. raw parquet fallback remains enabled as a temporary compatibility bridge until the ETL serving snapshot stage materializes that table in released artifacts

Important limitation:

1. this parity path is implemented first for the family compare serving slice,
2. the rest of `backend_v2` still needs the same route-by-route migration from direct parquet paths to serving snapshots.

---

## 15. Recommended Route Rollout Order

Implement V2 incrementally.

## 15.1 First Wave

1. `GET /api/v2/health/live`
2. `GET /api/v2/health/ready`
3. `GET /api/v2/health/artifacts`
4. `POST /api/v2/semantic/search`
5. `GET /api/v2/semantic/families/{docdb_family_id}/neighbors`

Why:

1. semantic artifacts are already ready,
2. they prove the artifact-resolution pattern,
3. they test local/cloud parity with real released assets.

## 15.2 Second Wave

1. `GET /api/v2/families/{docdb_family_id}`
2. `GET /api/v2/families/{docdb_family_id}/forecast`
3. `GET /api/v2/portfolios/{portfolio_id}`
4. `GET /api/v2/portfolios/{portfolio_id}/forecast`

## 15.3 Third Wave

1. compare endpoints,
2. report generation endpoints,
3. market intelligence endpoints,
4. LLM narrative augmentation on top.

---

## 16. Test Matrix

V2 backend parity should be proven by tests, not assumed.

The implementation approach should be `TDD-first`.

That means:

1. define route and service behavior in tests before filling implementation,
2. lock schema, caveat, and artifact-resolution rules through tests,
3. make local/prod parity part of the test suite rather than a later manual check.

Required test classes:

## 16.1 Unit Tests

1. settings parsing,
2. release manifest resolution,
3. local artifact locator,
4. Azure Blob artifact locator with mocked downloads,
5. semantic registry load,
6. forecast model registry load.

## 16.2 Integration Tests

1. local semantic search against current MVP ANN artifacts,
2. local forecast serving against released model artifacts,
3. release manifest swap changes active artifacts without route code changes,
4. local mode works with LLM disabled,
5. Azure-like mode works with blob-backed artifact resolution mocked.

## 16.3 Contract Tests

1. semantic response contains scope caveats,
2. forecast response contains model metadata,
3. health endpoint exposes active release info,
4. local and cloud config profiles return the same schema.

---

## 17. Security And Secrets

Only secrets should vary by environment.

Examples:

1. Azure Blob credentials,
2. Azure OpenAI API key,
3. optional Hugging Face token for older artifact access.

Non-secret runtime behavior should be configurable through plain env vars.

Do not:

1. hardcode storage account names in services,
2. hardcode model releases in route handlers,
3. bake secrets into images,
4. require local developers to have Azure credentials if they already have the artifacts locally.

---

## 18. Recommended Immediate Implementation Order

1. write tests for settings parsing, artifact resolution, health payloads, and semantic route contracts,
2. add `backend/v2/infrastructure/config/settings.py`,
3. add `backend/v2/infrastructure/artifacts/` resolver layer,
4. add `backend/v2/infrastructure/semantic/ann_index_registry.py`,
5. add `backend/v2/infrastructure/duckdb/` local/cloud-neutral connection manager,
6. add V2 health routes,
7. write route/service tests for semantic search and neighbor flows,
8. add V2 semantic search routes,
9. write route/service tests for family-first forecast serving,
10. add V2 family-first forecast registry and feature repo,
11. add V2 forecast routes,
12. add centralized Azure OpenAI client and LLM summary service.

This sequence proves the runtime architecture before larger UI or report serving work begins.

---

## 19. Final Recommendation

PatentIQ V2 backend should be built as a `config-first, artifact-driven, backend/v2 application` where:

1. local and Azure use the same code paths,
2. release manifests choose active Gold/model/semantic/ANN assets,
3. all heavy artifacts are resolved into a local cache before use,
4. semantic and forecast serving both depend on the same artifact-resolution contract,
5. Azure OpenAI stays centrally pluggable and works in both local and prod,
6. environment differences are expressed only through settings and credentials.

The design goal is simple:

`same routes, same services, same artifacts, different config`

That is the cleanest path to make semantic serving and future model-serving reliable both on the local machine and in Azure demo deployment.

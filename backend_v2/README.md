# PatentIQ Backend V2

`backend_v2` is the clean PatentIQ V2 API target.

Principles:

1. page-shaped contracts first
2. thin FastAPI routers
3. orchestration in application services
4. parquet and DuckDB access behind repositories
5. explicit caveat and support metadata in every strategic response

Initial workspace groups:

1. `portfolios`
2. `families`
3. `publications`
4. `market_intelligence`
5. `compare`
6. `data_room`
7. `stats`

Run locally after installing dependencies:

```bash
poetry install
poetry run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

For containerized browser audits through `host.docker.internal`, run the backend on a non-loopback bind:

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Notes:

1. `backend_v2/config/settings.py` already includes `http://host.docker.internal:3000` and `http://host.docker.internal:3001` in CORS.
2. The remaining requirement is that the backend process itself must be reachable from the container path, which typically means using `--host 0.0.0.0` during MCP / Playwright audits.
3. Local browser usage can still stay on `127.0.0.1`.

Shortcut scripts:

```bash
cd backend_v2
bash scripts/serve_local.sh
```

and:

```bash
cd backend_v2
bash scripts/serve_mcp.sh
```

The first is for normal local-browser work. The second is for MCP / containerized browser access.

From the repository root you can also launch both frontend and backend together:

```bash
bash scripts/dev_v2_local.sh
```

or:

```bash
bash scripts/dev_v2_mcp.sh
```

## Serving Artifact Modes

`backend_v2` now supports the same core serving-artifact resolution pattern in both local and Azure-oriented runtimes.

Supported modes:

1. `local_fs`
   - reads `serving_snapshot_manifest.json` from local disk
   - resolves `core_serving.duckdb` from local artifact paths
2. `azure_blob_cached`
   - reads the serving manifest from a URL
   - hydrates `core_serving.duckdb` into local cache
   - queries the local cached file, not the remote blob path

Current implementation status:

1. family compare prefers `core_serving.duckdb` with table `family_compare_current_serving`
2. if that table or snapshot is not present, backend falls back to raw local parquet reads
3. this fallback is transitional and should be removed route-by-route as serving snapshots are packaged by ETL

Local example:

```bash
export PATENTIQ_V2_ARTIFACT_MODE=local_fs
export PATENTIQ_V2_LOCAL_ARTIFACT_ROOT=/abs/path/to/serving
export PATENTIQ_V2_SERVING_MANIFEST_PATH=/abs/path/to/serving/serving_snapshot_manifest.json
poetry run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Azure-like cached example:

```bash
export PATENTIQ_V2_ARTIFACT_MODE=azure_blob_cached
export PATENTIQ_V2_SERVING_MANIFEST_URL=https://.../serving_snapshot_manifest.json
export PATENTIQ_V2_CACHE_DIR=/tmp/patentiq-v2-artifacts
poetry run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

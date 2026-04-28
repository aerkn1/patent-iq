#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
export HF_HOME="${HF_HOME:-/hf-home}"
export HF_HUB_CACHE="${HF_HUB_CACHE:-${HF_HOME%/}/hub}"
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export PATENTIQ_V2_RUNTIME_PROFILE="${PATENTIQ_V2_RUNTIME_PROFILE:-container}"
export PATENTIQ_V2_REPO_ROOT="${PATENTIQ_V2_REPO_ROOT:-/app}"
export PATENTIQ_V2_ETL_DATA_ROOT="${PATENTIQ_V2_ETL_DATA_ROOT:-/artifacts/current}"
export PATENTIQ_V2_LOCAL_ARTIFACT_ROOT="${PATENTIQ_V2_LOCAL_ARTIFACT_ROOT:-/artifacts/current/serving}"
export PATENTIQ_V2_SERVING_MANIFEST_PATH="${PATENTIQ_V2_SERVING_MANIFEST_PATH:-/artifacts/current/serving/serving_snapshot_manifest.json}"
export PATENTIQ_V2_DUCKDB_PATH="${PATENTIQ_V2_DUCKDB_PATH:-/artifacts/backend-cache/patentiq_v2.duckdb}"
export PATENTIQ_V2_CACHE_DIR="${PATENTIQ_V2_CACHE_DIR:-/artifacts/backend-cache}"
export PATENTIQ_V2_PENDING_GRANT_CACHE_DIR="${PATENTIQ_V2_PENDING_GRANT_CACHE_DIR:-/artifacts/pending-grant-cache}"

echo "[backend-start] booting PatentIQ backend v2"
echo "[backend-start] workdir=${BACKEND_DIR}"
echo "[backend-start] runtime_profile=${PATENTIQ_V2_RUNTIME_PROFILE}"
echo "[backend-start] artifact_mode=${PATENTIQ_V2_ARTIFACT_MODE:-<unset>}"
echo "[backend-start] repo_root=${PATENTIQ_V2_REPO_ROOT}"
echo "[backend-start] etl_data_root=${PATENTIQ_V2_ETL_DATA_ROOT:-<unset>}"
echo "[backend-start] local_artifact_root=${PATENTIQ_V2_LOCAL_ARTIFACT_ROOT:-<unset>}"
echo "[backend-start] serving_manifest_path=${PATENTIQ_V2_SERVING_MANIFEST_PATH:-<unset>}"
echo "[backend-start] hf_home=${HF_HOME}"
echo "[backend-start] hf_hub_cache=${HF_HUB_CACHE}"

mkdir -p "${PATENTIQ_V2_CACHE_DIR}" "${PATENTIQ_V2_PENDING_GRANT_CACHE_DIR}"
if [[ -d "${PATENTIQ_V2_ETL_DATA_ROOT}" ]]; then
  echo "[backend-start] artifact tree:"
  find "${PATENTIQ_V2_ETL_DATA_ROOT}" -maxdepth 2 | sort
fi

cd "${BACKEND_DIR}"
python - <<'PY'
import json
import os

from config.settings import get_settings
from infrastructure.artifacts.locator import ArtifactLocator

settings = get_settings()
locator = ArtifactLocator(settings)
description = locator.describe_runtime(resolve_paths=False)
description["duckdb_path"] = str(settings.duckdb_path)
description["cache_dir"] = str(settings.cache_dir)
description["pending_grant_cache_dir"] = str(settings.pending_grant_cache_dir)
description["hf_home"] = os.environ.get("HF_HOME")
description["hf_hub_cache"] = os.environ.get("HF_HUB_CACHE")
print("[backend-start] resolved runtime:")
print(json.dumps(description, indent=2, sort_keys=True))
PY

exec uvicorn main:app --host 0.0.0.0 --port "${PATENTIQ_BACKEND_PORT:-8000}"

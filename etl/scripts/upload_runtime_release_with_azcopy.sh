#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

RELEASE_ID="${PATENTIQ_RUNTIME_RELEASE_ID:-}"
ACTIVATE="false"
START_AT="${PATENTIQ_RUNTIME_UPLOAD_START_AT:-metadata}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --release-id)
      RELEASE_ID="${2:-}"
      shift 2
      ;;
    --start-at)
      START_AT="${2:-}"
      shift 2
      ;;
    --activate)
      ACTIVATE="true"
      shift
      ;;
    *)
      echo "Unsupported argument: $1"
      echo "Usage: $0 --release-id <release_id> [--start-at <metadata|market|semantic|core|publication|vectors|models|analytics|manifest|activate>] [--activate]"
      exit 1
      ;;
  esac
done

if [[ -z "${RELEASE_ID}" ]]; then
  echo "Missing release id. Provide --release-id or PATENTIQ_RUNTIME_RELEASE_ID."
  exit 1
fi

AZCOPY_BIN="${PATENTIQ_AZCOPY_BIN:-azcopy}"
ACCOUNT_URL="${PATENTIQ_BLOB_ACCOUNT_URL:-https://patentiq.blob.core.windows.net}"
CONTAINER="${PATENTIQ_BLOB_CONTAINER:-patentiq-data}"
SAS_TOKEN="${PATENTIQ_BLOB_SAS:-}"
CONNECTION_STRING="${AZURE_STORAGE_CONNECTION_STRING:-}"
ETL_PYTHON="${PATENTIQ_ETL_PYTHON:-${REPO_ROOT}/etl/.venv/bin/python}"
SAS_EXPIRY_HOURS="${PATENTIQ_BLOB_SAS_EXPIRY_HOURS:-168}"

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required for ${0}"
  exit 1
fi

if ! command -v "${AZCOPY_BIN}" >/dev/null 2>&1; then
  echo "AzCopy binary was not found: ${AZCOPY_BIN}"
  exit 1
fi

if [[ -z "${SAS_TOKEN}" && -n "${CONNECTION_STRING}" ]]; then
  if [[ ! -x "${ETL_PYTHON}" ]]; then
    echo "ETL Python interpreter not found for SAS generation: ${ETL_PYTHON}"
    exit 1
  fi
  SAS_TOKEN="$(PATENTIQ_BLOB_CONTAINER="${CONTAINER}" PATENTIQ_BLOB_SAS_EXPIRY_HOURS="${SAS_EXPIRY_HOURS}" "${ETL_PYTHON}" - <<'PY'
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os

from azure.storage.blob import BlobServiceClient, ContainerSasPermissions, generate_container_sas

connection_string = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
container = os.environ["PATENTIQ_BLOB_CONTAINER"]
expiry_hours = int(os.environ.get("PATENTIQ_BLOB_SAS_EXPIRY_HOURS", "168"))

parts = {}
for fragment in connection_string.split(";"):
    if "=" not in fragment:
        continue
    key, value = fragment.split("=", 1)
    parts[key] = value

account_name = parts.get("AccountName")
account_key = parts.get("AccountKey")
if not account_name or not account_key:
    raise SystemExit("Connection string is missing AccountName or AccountKey.")

service = BlobServiceClient.from_connection_string(connection_string)
account_url = service.url.rstrip("/")

sas = generate_container_sas(
    account_name=account_name,
    container_name=container,
    account_key=account_key,
    permission=ContainerSasPermissions(read=True, write=True, create=True, add=True, delete=True, list=True),
    expiry=datetime.now(timezone.utc) + timedelta(hours=expiry_hours),
    protocol="https",
)
print(account_url)
print("?" + sas)
PY
)"
  ACCOUNT_URL="$(printf '%s\n' "${SAS_TOKEN}" | sed -n '1p')"
  SAS_TOKEN="$(printf '%s\n' "${SAS_TOKEN}" | sed -n '2p')"
fi

if [[ -z "${SAS_TOKEN}" ]]; then
  echo "Provide PATENTIQ_BLOB_SAS or AZURE_STORAGE_CONNECTION_STRING."
  exit 1
fi

LARGE_BLOCK_SIZE_MB="${PATENTIQ_AZCOPY_LARGE_BLOCK_SIZE_MB:-32}"
LARGE_CONCURRENCY="${PATENTIQ_AZCOPY_LARGE_CONCURRENCY:-8}"
DIR_BLOCK_SIZE_MB="${PATENTIQ_AZCOPY_DIR_BLOCK_SIZE_MB:-16}"
DIR_CONCURRENCY="${PATENTIQ_AZCOPY_DIR_CONCURRENCY:-16}"
PUT_BLOB_SIZE_MB="${PATENTIQ_AZCOPY_PUT_BLOB_SIZE_MB:-32}"
LOG_LEVEL="${PATENTIQ_AZCOPY_LOG_LEVEL:-ERROR}"
OVERWRITE="${PATENTIQ_AZCOPY_OVERWRITE:-false}"
CHECK_LENGTH="${PATENTIQ_AZCOPY_CHECK_LENGTH:-true}"
BUFFER_GB="${PATENTIQ_AZCOPY_BUFFER_GB:-1}"

GENERATED_DIR="${REPO_ROOT}/etl/manifests/releases/${RELEASE_ID}"
RELEASE_MANIFEST_PATH="${GENERATED_DIR}/release-manifest.json"
ACTIVE_RELEASE_PATH="${GENERATED_DIR}/active_release.json"
UPLOAD_PLAN_PATH="${GENERATED_DIR}/runtime-upload-plan.json"

if [[ ! -f "${RELEASE_MANIFEST_PATH}" || ! -f "${ACTIVE_RELEASE_PATH}" || ! -f "${UPLOAD_PLAN_PATH}" ]]; then
  echo "Generated release files are missing under ${GENERATED_DIR}"
  echo "Run: etl/.venv/bin/python etl/scripts/prepare_runtime_release.py --etl-root etl --release-id ${RELEASE_ID}"
  exit 1
fi

RELEASE_ROOT_PREFIX="$(jq -r '.artifact_root' "${RELEASE_MANIFEST_PATH}")"
if [[ -z "${RELEASE_ROOT_PREFIX}" || "${RELEASE_ROOT_PREFIX}" == "null" ]]; then
  echo "Could not resolve artifact_root from ${RELEASE_MANIFEST_PATH}"
  exit 1
fi

SERVING_DIR="${PATENTIQ_RUNTIME_SERVING_DIR:-${REPO_ROOT}/etl/data/serving}"
VECTORS_DIR="${PATENTIQ_RUNTIME_VECTORS_DIR:-${REPO_ROOT}/etl/data/vectors}"
MODELS_DIR="${PATENTIQ_RUNTIME_MODELS_DIR:-${REPO_ROOT}/etl/data/ml}"
PUBLICATION_DIR="${PATENTIQ_PUBLICATION_SOURCE_DIR:-${SERVING_DIR}/publication_serving}"

AZCOPY_STATE_DIR="${GENERATED_DIR}/azcopy"
mkdir -p "${AZCOPY_STATE_DIR}/logs" "${AZCOPY_STATE_DIR}/plans"

export AZCOPY_LOG_LOCATION="${PATENTIQ_AZCOPY_LOG_LOCATION:-${AZCOPY_STATE_DIR}/logs}"
export AZCOPY_JOB_PLAN_LOCATION="${PATENTIQ_AZCOPY_JOB_PLAN_LOCATION:-${AZCOPY_STATE_DIR}/plans}"
export AZCOPY_LOG_LEVEL="${LOG_LEVEL}"
export AZCOPY_BUFFER_GB="${BUFFER_GB}"

step_rank() {
  case "$1" in
    metadata) echo 0 ;;
    market) echo 10 ;;
    semantic) echo 20 ;;
    core) echo 30 ;;
    publication) echo 40 ;;
    vectors) echo 50 ;;
    models) echo 60 ;;
    analytics) echo 70 ;;
    manifest) echo 80 ;;
    activate) echo 90 ;;
    *)
      echo "Unsupported start step: $1" >&2
      exit 1
      ;;
  esac
}

START_AT_RANK="$(step_rank "${START_AT}")"

should_run_step() {
  local step="$1"
  local step_value
  step_value="$(step_rank "${step}")"
  [[ "${step_value}" -ge "${START_AT_RANK}" ]]
}

dest_url() {
  local blob_path="$1"
  if [[ -n "${SAS_TOKEN}" ]]; then
    printf "%s/%s/%s%s" "${ACCOUNT_URL}" "${CONTAINER}" "${blob_path}" "${SAS_TOKEN}"
  else
    printf "%s/%s/%s" "${ACCOUNT_URL}" "${CONTAINER}" "${blob_path}"
  fi
}

run_azcopy() {
  local concurrency="$1"
  shift
  echo "[runtime-upload] AZCOPY_CONCURRENCY_VALUE=${concurrency} ${AZCOPY_BIN} $*"
  AZCOPY_CONCURRENCY_VALUE="${concurrency}" "${AZCOPY_BIN}" "$@"
}

upload_large_file() {
  local source_path="$1"
  local blob_path="$2"
  echo "[runtime-upload] uploading large file source=${source_path} blob=${blob_path}"
  run_azcopy "${LARGE_CONCURRENCY}" cp \
    "${source_path}" \
    "$(dest_url "${blob_path}")" \
    --block-size-mb "${LARGE_BLOCK_SIZE_MB}" \
    --put-blob-size-mb "${PUT_BLOB_SIZE_MB}" \
    --check-length="${CHECK_LENGTH}" \
    --overwrite="${OVERWRITE}" \
    --log-level "${LOG_LEVEL}"
}

upload_directory() {
  local source_path="$1"
  local blob_path="$2"
  echo "[runtime-upload] uploading directory source=${source_path} blob_prefix=${blob_path}"
  run_azcopy "${DIR_CONCURRENCY}" cp \
    "${source_path}" \
    "$(dest_url "${blob_path}")" \
    --recursive \
    --as-subdir=false \
    --exclude-pattern ".DS_Store" \
    --block-size-mb "${DIR_BLOCK_SIZE_MB}" \
    --put-blob-size-mb "${PUT_BLOB_SIZE_MB}" \
    --check-length="${CHECK_LENGTH}" \
    --overwrite="${OVERWRITE}" \
    --log-level "${LOG_LEVEL}"
}

upload_standard_file() {
  local source_path="$1"
  local blob_path="$2"
  echo "[runtime-upload] uploading file source=${source_path} blob=${blob_path}"
  run_azcopy "${DIR_CONCURRENCY}" cp \
    "${source_path}" \
    "$(dest_url "${blob_path}")" \
    --block-size-mb "${DIR_BLOCK_SIZE_MB}" \
    --put-blob-size-mb "${PUT_BLOB_SIZE_MB}" \
    --check-length="${CHECK_LENGTH}" \
    --overwrite="${OVERWRITE}" \
    --log-level "${LOG_LEVEL}"
}

echo "[runtime-upload] release_id=${RELEASE_ID}"
echo "[runtime-upload] release_root_prefix=${RELEASE_ROOT_PREFIX}"
echo "[runtime-upload] container=${CONTAINER}"
echo "[runtime-upload] account_url=${ACCOUNT_URL}"
echo "[runtime-upload] activate=${ACTIVATE}"
echo "[runtime-upload] start_at=${START_AT}"
echo "[runtime-upload] azcopy_log_location=${AZCOPY_LOG_LOCATION}"
echo "[runtime-upload] azcopy_plan_location=${AZCOPY_JOB_PLAN_LOCATION}"
echo "[runtime-upload] large_block_size_mb=${LARGE_BLOCK_SIZE_MB}"
echo "[runtime-upload] large_concurrency=${LARGE_CONCURRENCY}"
echo "[runtime-upload] dir_block_size_mb=${DIR_BLOCK_SIZE_MB}"
echo "[runtime-upload] dir_concurrency=${DIR_CONCURRENCY}"
echo "[runtime-upload] put_blob_size_mb=${PUT_BLOB_SIZE_MB}"
echo "[runtime-upload] overwrite=${OVERWRITE}"
echo "[runtime-upload] check_length=${CHECK_LENGTH}"

if should_run_step metadata; then
  upload_standard_file "${SERVING_DIR}/serving_snapshot_manifest.json" "${RELEASE_ROOT_PREFIX}/serving/serving_snapshot_manifest.json"
  upload_standard_file "${SERVING_DIR}/serving_snapshot_audit.json" "${RELEASE_ROOT_PREFIX}/serving/serving_snapshot_audit.json"
fi

if should_run_step market; then
  upload_standard_file "${SERVING_DIR}/market_serving.duckdb" "${RELEASE_ROOT_PREFIX}/serving/market_serving.duckdb"
fi

if should_run_step semantic; then
  upload_large_file "${SERVING_DIR}/semantic_serving.duckdb" "${RELEASE_ROOT_PREFIX}/serving/semantic_serving.duckdb"
fi

if should_run_step core; then
  upload_large_file "${SERVING_DIR}/core_serving.duckdb" "${RELEASE_ROOT_PREFIX}/serving/core_serving.duckdb"
fi

if should_run_step publication; then
  upload_directory "${PUBLICATION_DIR}" "${RELEASE_ROOT_PREFIX}/serving/publication_serving"
fi

if should_run_step vectors; then
  upload_standard_file "${VECTORS_DIR}/vec_embedding_manifest.json" "${RELEASE_ROOT_PREFIX}/vectors/vec_embedding_manifest.json"
  upload_large_file "${VECTORS_DIR}/vec_family_embeddings_abstracts.parquet" "${RELEASE_ROOT_PREFIX}/vectors/vec_family_embeddings_abstracts.parquet"
  upload_large_file "${VECTORS_DIR}/vec_family_embeddings_claims.parquet" "${RELEASE_ROOT_PREFIX}/vectors/vec_family_embeddings_claims.parquet"
  upload_standard_file "${VECTORS_DIR}/vec_query_registry.parquet" "${RELEASE_ROOT_PREFIX}/vectors/vec_query_registry.parquet"
  upload_standard_file "${VECTORS_DIR}/vec_ann_index_manifest.json" "${RELEASE_ROOT_PREFIX}/vectors/vec_ann_index_manifest.json"
  upload_standard_file "${VECTORS_DIR}/vec_ann_exact_vs_ann_audit.json" "${RELEASE_ROOT_PREFIX}/vectors/vec_ann_exact_vs_ann_audit.json"
  upload_directory "${VECTORS_DIR}/ann" "${RELEASE_ROOT_PREFIX}/vectors/ann"
fi

if should_run_step models; then
  upload_directory "${MODELS_DIR}" "${RELEASE_ROOT_PREFIX}/models"
fi

if should_run_step analytics; then
  upload_large_file "${SERVING_DIR}/analytics_serving.duckdb" "${RELEASE_ROOT_PREFIX}/serving/analytics_serving.duckdb"
fi

if should_run_step manifest; then
  upload_standard_file "${RELEASE_MANIFEST_PATH}" "${RELEASE_ROOT_PREFIX}/release-manifest.json"
fi

if [[ "${ACTIVATE}" == "true" ]]; then
  if should_run_step activate; then
    upload_standard_file "${ACTIVE_RELEASE_PATH}" "manifests/active_release.json"
    echo "[runtime-upload] active release pointer uploaded"
  else
    echo "[runtime-upload] activate=true but start_at=${START_AT} is after activate; skipping pointer upload"
  fi
else
  echo "[runtime-upload] activation skipped; upload ${ACTIVE_RELEASE_PATH} to manifests/active_release.json when ready"
fi

echo "[runtime-upload] completed release_id=${RELEASE_ID}"

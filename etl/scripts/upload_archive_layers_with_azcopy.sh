#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

ARCHIVE_ID="${PATENTIQ_ARCHIVE_ID:-}"
START_AT="${PATENTIQ_ARCHIVE_START_AT:-bronze}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive-id)
      ARCHIVE_ID="${2:-}"
      shift 2
      ;;
    --start-at)
      START_AT="${2:-}"
      shift 2
      ;;
    *)
      echo "Unsupported argument: $1"
      echo "Usage: $0 --archive-id <archive_id> [--start-at <bronze|silver|gold>]"
      exit 1
      ;;
  esac
done

if [[ -z "${ARCHIVE_ID}" ]]; then
  echo "Missing archive id. Provide --archive-id or PATENTIQ_ARCHIVE_ID."
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

DIR_BLOCK_SIZE_MB="${PATENTIQ_AZCOPY_DIR_BLOCK_SIZE_MB:-32}"
DIR_CONCURRENCY="${PATENTIQ_AZCOPY_DIR_CONCURRENCY:-32}"
PUT_BLOB_SIZE_MB="${PATENTIQ_AZCOPY_PUT_BLOB_SIZE_MB:-128}"
LOG_LEVEL="${PATENTIQ_AZCOPY_LOG_LEVEL:-ERROR}"
OVERWRITE="${PATENTIQ_AZCOPY_OVERWRITE:-false}"
CHECK_LENGTH="${PATENTIQ_AZCOPY_CHECK_LENGTH:-true}"
BUFFER_GB="${PATENTIQ_AZCOPY_BUFFER_GB:-8}"

PLAN_DIR="${REPO_ROOT}/etl/manifests/archives/${ARCHIVE_ID}"
PLAN_PATH="${PLAN_DIR}/archive-upload-plan.json"

if [[ ! -f "${PLAN_PATH}" ]]; then
  echo "Archive upload plan is missing under ${PLAN_DIR}"
  echo "Run: python etl/scripts/prepare_archive_upload_plan.py --etl-root etl --archive-id ${ARCHIVE_ID}"
  exit 1
fi

AZCOPY_STATE_DIR="${PLAN_DIR}/azcopy"
mkdir -p "${AZCOPY_STATE_DIR}/logs" "${AZCOPY_STATE_DIR}/plans"

export AZCOPY_LOG_LOCATION="${PATENTIQ_AZCOPY_LOG_LOCATION:-${AZCOPY_STATE_DIR}/logs}"
export AZCOPY_JOB_PLAN_LOCATION="${PATENTIQ_AZCOPY_JOB_PLAN_LOCATION:-${AZCOPY_STATE_DIR}/plans}"
export AZCOPY_LOG_LEVEL="${LOG_LEVEL}"
export AZCOPY_BUFFER_GB="${BUFFER_GB}"

step_rank() {
  case "$1" in
    bronze) echo 0 ;;
    silver) echo 10 ;;
    gold) echo 20 ;;
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
  printf "%s/%s/%s%s" "${ACCOUNT_URL}" "${CONTAINER}" "${blob_path}" "${SAS_TOKEN}"
}

run_azcopy() {
  local concurrency="$1"
  shift
  echo "[archive-upload] AZCOPY_CONCURRENCY_VALUE=${concurrency} ${AZCOPY_BIN} $*"
  AZCOPY_CONCURRENCY_VALUE="${concurrency}" "${AZCOPY_BIN}" "$@"
}

upload_directory() {
  local source_path="$1"
  local blob_prefix="$2"
  echo "[archive-upload] uploading directory source=${source_path} blob_prefix=${blob_prefix}"
  run_azcopy "${DIR_CONCURRENCY}" cp \
    "${source_path}" \
    "$(dest_url "${blob_prefix}")" \
    --recursive \
    --as-subdir=false \
    --exclude-pattern ".DS_Store" \
    --block-size-mb "${DIR_BLOCK_SIZE_MB}" \
    --put-blob-size-mb "${PUT_BLOB_SIZE_MB}" \
    --check-length="${CHECK_LENGTH}" \
    --overwrite="${OVERWRITE}" \
    --log-level "${LOG_LEVEL}"
}

layer_local_path() {
  local layer="$1"
  jq -r --arg layer "${layer}" '.layers[$layer].local_path' "${PLAN_PATH}"
}

layer_blob_prefix() {
  local layer="$1"
  jq -r --arg layer "${layer}" '.layers[$layer].blob_prefix' "${PLAN_PATH}"
}

echo "[archive-upload] archive_id=${ARCHIVE_ID}"
echo "[archive-upload] container=${CONTAINER}"
echo "[archive-upload] account_url=${ACCOUNT_URL}"
echo "[archive-upload] start_at=${START_AT}"
echo "[archive-upload] azcopy_log_location=${AZCOPY_LOG_LOCATION}"
echo "[archive-upload] azcopy_plan_location=${AZCOPY_JOB_PLAN_LOCATION}"
echo "[archive-upload] dir_block_size_mb=${DIR_BLOCK_SIZE_MB}"
echo "[archive-upload] dir_concurrency=${DIR_CONCURRENCY}"
echo "[archive-upload] put_blob_size_mb=${PUT_BLOB_SIZE_MB}"
echo "[archive-upload] overwrite=${OVERWRITE}"
echo "[archive-upload] check_length=${CHECK_LENGTH}"

for layer in bronze silver gold; do
  if should_run_step "${layer}"; then
    upload_directory "$(layer_local_path "${layer}")" "$(layer_blob_prefix "${layer}")"
  fi
done

echo "[archive-upload] completed archive_id=${ARCHIVE_ID}"

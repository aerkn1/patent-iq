#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SOURCE_MODE="${PATENTIQ_BOOTSTRAP_SOURCE_MODE:-local_release}"
PROFILE="${PATENTIQ_BOOTSTRAP_PROFILE:-default}"
TARGET_ROOT="${PATENTIQ_BOOTSTRAP_TARGET_ROOT:-/artifacts}"
LOG_PATH="${PATENTIQ_BOOTSTRAP_LOG_PATH:-${TARGET_ROOT%/}/logs/artifact-init.log}"
HF_HOME="${PATENTIQ_BOOTSTRAP_HF_HOME:-/hf-home}"
PREFETCH_HF_MODELS="${PATENTIQ_BOOTSTRAP_PREFETCH_HF_MODELS:-true}"
ALLOW_UNPINNED_HF_MODELS="${PATENTIQ_BOOTSTRAP_ALLOW_UNPINNED_HF_MODELS:-false}"
OVERWRITE="${PATENTIQ_BOOTSTRAP_OVERWRITE:-false}"

echo "[artifact-init] starting PatentIQ artifact bootstrap"
echo "[artifact-init] source_mode=${SOURCE_MODE}"
echo "[artifact-init] profile=${PROFILE}"
echo "[artifact-init] target_root=${TARGET_ROOT}"
echo "[artifact-init] log_path=${LOG_PATH}"
echo "[artifact-init] hf_home=${HF_HOME}"
echo "[artifact-init] prefetch_hf_models=${PREFETCH_HF_MODELS}"
echo "[artifact-init] allow_unpinned_hf_models=${ALLOW_UNPINNED_HF_MODELS}"
echo "[artifact-init] overwrite=${OVERWRITE}"

mkdir -p "${TARGET_ROOT}" "${HF_HOME}" "$(dirname "${LOG_PATH}")"

ARGS=(
  "--source-mode" "${SOURCE_MODE}"
  "--target-root" "${TARGET_ROOT}"
  "--profile" "${PROFILE}"
  "--log-path" "${LOG_PATH}"
  "--hf-home" "${HF_HOME}"
  "--hf-token-env" "${PATENTIQ_BOOTSTRAP_HF_TOKEN_ENV:-HF_TOKEN}"
)

if [[ "${OVERWRITE}" == "true" ]]; then
  ARGS+=("--overwrite")
fi

if [[ "${PREFETCH_HF_MODELS}" == "true" ]]; then
  ARGS+=("--prefetch-hf-models")
fi

if [[ "${ALLOW_UNPINNED_HF_MODELS}" == "true" ]]; then
  ARGS+=("--allow-unpinned-hf-models")
fi

if [[ "${SOURCE_MODE}" == "local_release" ]]; then
  if [[ -n "${PATENTIQ_RELEASE_MANIFEST_PATH:-}" ]]; then
    ARGS+=("--release-manifest-path" "${PATENTIQ_RELEASE_MANIFEST_PATH}")
  elif [[ -n "${PATENTIQ_ACTIVE_RELEASE_PATH:-}" ]]; then
    ARGS+=("--active-release-path" "${PATENTIQ_ACTIVE_RELEASE_PATH}")
  else
    echo "[artifact-init] missing PATENTIQ_RELEASE_MANIFEST_PATH or PATENTIQ_ACTIVE_RELEASE_PATH for local_release"
    exit 1
  fi
elif [[ "${SOURCE_MODE}" == "azure_blob" ]]; then
  if [[ -z "${PATENTIQ_AZURE_STORAGE_CONTAINER:-}" ]]; then
    echo "[artifact-init] missing PATENTIQ_AZURE_STORAGE_CONTAINER for azure_blob"
    exit 1
  fi
  ARGS+=("--container" "${PATENTIQ_AZURE_STORAGE_CONTAINER}")
  if [[ -n "${PATENTIQ_AZURE_STORAGE_ACCOUNT_URL:-}" ]]; then
    ARGS+=("--account-url" "${PATENTIQ_AZURE_STORAGE_ACCOUNT_URL}")
  fi
  if [[ -n "${PATENTIQ_AZURE_ACTIVE_RELEASE_BLOB:-}" ]]; then
    ARGS+=("--active-release-blob" "${PATENTIQ_AZURE_ACTIVE_RELEASE_BLOB}")
  fi
  if [[ -n "${PATENTIQ_AZURE_RELEASE_MANIFEST_BLOB:-}" ]]; then
    ARGS+=("--release-manifest-blob" "${PATENTIQ_AZURE_RELEASE_MANIFEST_BLOB}")
  fi
  ARGS+=("--connection-string-env" "${PATENTIQ_AZURE_CONNECTION_STRING_ENV:-AZURE_STORAGE_CONNECTION_STRING}")
else
  echo "[artifact-init] unsupported source mode ${SOURCE_MODE}"
  exit 1
fi

python "${SCRIPT_DIR}/bootstrap_runtime_artifacts.py" "${ARGS[@]}"

echo "[artifact-init] bootstrap completed"
if [[ -L "${TARGET_ROOT}/current" ]]; then
  echo "[artifact-init] current -> $(readlink "${TARGET_ROOT}/current")"
fi
if [[ -d "${TARGET_ROOT}/current" ]]; then
  echo "[artifact-init] current runtime tree:"
  find "${TARGET_ROOT}/current" -maxdepth 2 | sort
fi
if [[ -d "${TARGET_ROOT}/releases" ]]; then
  echo "[artifact-init] cached release sizes:"
  du -sh "${TARGET_ROOT}/releases"/*
fi

python - <<'PY'
import json
from pathlib import Path

target_root = Path(__import__("os").environ.get("PATENTIQ_BOOTSTRAP_TARGET_ROOT", "/artifacts"))
state_path = target_root / "current" / ".bootstrap-state.json"
if state_path.exists():
    payload = json.loads(state_path.read_text(encoding="utf-8"))
    print("[artifact-init] bootstrap state:")
    print(json.dumps(payload, indent=2, sort_keys=True))
else:
    print(f"[artifact-init] bootstrap state file missing at {state_path}")
PY

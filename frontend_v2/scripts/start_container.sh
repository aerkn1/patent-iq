#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/app}"
RUNTIME_CONFIG_PATH="${APP_DIR}/public/runtime-config.js"
API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-}"

echo "[frontend-start] booting PatentIQ frontend v2"
echo "[frontend-start] app_dir=${APP_DIR}"
echo "[frontend-start] next_public_api_base_url=${API_BASE_URL:-<empty>}"
echo "[frontend-start] runtime_config_path=${RUNTIME_CONFIG_PATH}"

APP_DIR="${APP_DIR}" node - <<'NODE'
const fs = require("fs");
const path = require("path");

const appDir = process.env.APP_DIR || "/app";
const runtimeConfigPath = path.join(appDir, "public", "runtime-config.js");
const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();
const payload = `window.__PATENTIQ_RUNTIME_CONFIG__ = Object.assign({}, window.__PATENTIQ_RUNTIME_CONFIG__ || {}, ${JSON.stringify({ apiBaseUrl })});\n`;

fs.mkdirSync(path.dirname(runtimeConfigPath), { recursive: true });
fs.writeFileSync(runtimeConfigPath, payload, "utf8");
console.log(`[frontend-start] wrote runtime config ${runtimeConfigPath}`);
console.log(`[frontend-start] runtime api base url ${apiBaseUrl || "<empty>"}`);
NODE

echo "[frontend-start] runtime-config.js contents:"
cat "${RUNTIME_CONFIG_PATH}"

cd "${APP_DIR}"
exec node server.js

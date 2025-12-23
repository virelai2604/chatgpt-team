#!/usr/bin/env bash
set -euo pipefail

RELAY_BASE_URL="${RELAY_BASE_URL:-${RELAY_BASE:-http://localhost:8000}}"
RELAY_TOKEN="${RELAY_TOKEN:-dummy}"

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

check_json_error () {
  local url="$1"
  local name="$2"
  echo "== ${name}: GET ${url} =="
  curl -sS -D "${TMP_DIR}/${name}.h" -o "${TMP_DIR}/${name}.b" -w "\nHTTP=%{http_code}\n" \
    -L "${url}" \
    -H "Authorization: Bearer ${RELAY_TOKEN}"

  local status_line
  status_line="$(head -n 1 "${TMP_DIR}/${name}.h" || true)"
  echo "Status: ${status_line}"

  if echo "${status_line}" | grep -q " 500 "; then
    echo "ERROR: ${name} returned 500 (should be upstream 4xx JSON error)" >&2
    exit 40
  fi

  if ! grep -qi '^content-type:.*application/json' "${TMP_DIR}/${name}.h"; then
    echo "ERROR: ${name} expected application/json for invalid-id case" >&2
    exit 41
  fi

  if ! jq -e '.error.message' < "${TMP_DIR}/${name}.b" >/dev/null 2>&1; then
    echo "ERROR: ${name} expected JSON body with .error.message" >&2
    cat "${TMP_DIR}/${name}.b" >&2 || true
    exit 42
  fi

  echo "OK: ${name} returned structured JSON error (expected for invalid IDs)"
}

check_json_error "${RELAY_BASE_URL}/v1/containers/cont_invalid/files/file_invalid/content" "containers_content"
check_json_error "${RELAY_BASE_URL}/v1/videos/video_invalid/content" "videos_content"

echo "== Content endpoints smoke: PASS =="

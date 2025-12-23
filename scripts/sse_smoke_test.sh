#!/usr/bin/env bash
set -euo pipefail

# SSE smoke test for /v1/responses:stream
#
# Pass criteria:
# - HTTP 200
# - content-type includes text/event-stream
# - body contains at least one "data:" line

RELAY_BASE_URL="${RELAY_BASE_URL:-${RELAY_BASE:-http://localhost:8000}}"
RELAY_TOKEN="${RELAY_TOKEN:-dummy}"
DEFAULT_MODEL="${DEFAULT_MODEL:-gpt-5.1}"
MAX_TIME="${SSE_MAX_TIME_SECONDS:-15}"

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

payload="$(jq -cn --arg m "${DEFAULT_MODEL}" --arg i "Write exactly 20 characters: 12345678901234567890" '{model:$m,input:$i}')"

echo "== SSE request =="
curl -sS -N --max-time "${MAX_TIME}" \
  -D "${TMP_DIR}/sse.h" \
  -o "${TMP_DIR}/sse.b" \
  -X POST "${RELAY_BASE_URL}/v1/responses:stream" \
  -H "Authorization: Bearer ${RELAY_TOKEN}" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d "${payload}" || true

status_line="$(head -n 1 "${TMP_DIR}/sse.h" || true)"
ctype="$(grep -i '^content-type:' "${TMP_DIR}/sse.h" | head -n 1 | tr -d '\r' || true)"

echo "Status: ${status_line}"
echo "Content-Type: ${ctype}"

if ! echo "${status_line}" | grep -q " 200 "; then
  echo "ERROR: expected 200" >&2
  echo "Body (first 400 bytes):" >&2
  head -c 400 "${TMP_DIR}/sse.b" >&2 || true
  exit 30
fi

if ! echo "${ctype}" | grep -qi "text/event-stream"; then
  echo "ERROR: expected text/event-stream content-type" >&2
  exit 31
fi

if ! grep -q "data:" "${TMP_DIR}/sse.b"; then
  echo "ERROR: expected at least one SSE data: line" >&2
  echo "Body (first 800 bytes):" >&2
  head -c 800 "${TMP_DIR}/sse.b" >&2 || true
  exit 32
fi

echo "== SSE smoke: PASS =="

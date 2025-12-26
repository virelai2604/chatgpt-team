#!/usr/bin/env bash
set -euo pipefail

# Smoke test for /v1/images/variations using multipart/form-data.
#
# Pass criteria:
# - HTTP status is < 500 (wired, no relay crash)
# Optional "functional" criteria:
# - HTTP 200 if you use a valid IMAGE_MODEL and your upstream key has access.

RELAY_BASE_URL="${RELAY_BASE_URL:-http://localhost:8000}"
RELAY_TOKEN="${RELAY_TOKEN:-${RELAY_KEY:-dummy}}"

IMAGE_PATH="${IMAGE_PATH:-input.png}"
IMAGE_SIZE="${IMAGE_SIZE:-256}"
IMAGE_MODEL="${IMAGE_MODEL:-dall-e-2}"     # set to "__invalid__" for a cheap 400 wiring-only test
IMAGE_N="${IMAGE_N:-1}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing required command: $1" >&2; exit 10; }; }
need curl
need jq
need python3

# Generate the PNG if missing
if [[ ! -f "${IMAGE_PATH}" ]]; then
  python3 scripts/make_sample_png.py --out "${IMAGE_PATH}" --size "${IMAGE_SIZE}" --force
fi

echo "== Calling images variations =="
echo "BASE:  ${RELAY_BASE_URL}"
echo "FILE:  ${IMAGE_PATH}"
echo "MODEL: ${IMAGE_MODEL}"
echo "SIZE:  ${IMAGE_SIZE}x${IMAGE_SIZE}"

TMP_BODY="$(mktemp)"
TMP_HDRS="$(mktemp)"
cleanup() { rm -f "${TMP_BODY}" "${TMP_HDRS}"; }
trap cleanup EXIT

# Capture status separately
HTTP_CODE="$(
  curl -sS -X POST "${RELAY_BASE_URL%/}/v1/images/variations" \
    -H "Authorization: Bearer ${RELAY_TOKEN}" \
    -F "image=@${IMAGE_PATH};type=image/png" \
    -F "model=${IMAGE_MODEL}" \
    -F "n=${IMAGE_N}" \
    -F "size=${IMAGE_SIZE}x${IMAGE_SIZE}" \
    -D "${TMP_HDRS}" \
    -o "${TMP_BODY}" \
    -w "%{http_code}"
)"

echo "HTTP: ${HTTP_CODE}"
if [[ "${HTTP_CODE}" -ge 500 ]]; then
  echo "ERROR: relay returned 5xx (should never happen)" >&2
  echo "---- headers ----" >&2
  cat "${TMP_HDRS}" >&2 || true
  echo "---- body (first 1200 bytes) ----" >&2
  head -c 1200 "${TMP_BODY}" >&2 || true
  exit 50
fi

# Try to pretty print JSON if possible (errors are typically JSON)
if jq -e . >/dev/null 2>&1 < "${TMP_BODY}"; then
  cat "${TMP_BODY}" | jq .
else
  echo "Non-JSON body (first 1200 bytes):"
  head -c 1200 "${TMP_BODY}" || true
fi

echo "== images variations smoke: PASS (status < 500) =="

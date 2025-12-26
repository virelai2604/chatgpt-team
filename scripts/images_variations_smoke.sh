#!/usr/bin/env bash
set -euo pipefail

RELAY_BASE_URL="${RELAY_BASE_URL:-http://localhost:8000}"
RELAY_BASE_URL="${RELAY_BASE_URL%/}"

RELAY_TOKEN="${RELAY_TOKEN:-${RELAY_KEY:-}}"
if [[ -z "${RELAY_TOKEN}" ]]; then
  echo "ERROR: Set RELAY_TOKEN (or RELAY_KEY) for relay auth." >&2
  exit 2
fi

tmp_png="$(mktemp --suffix=.png)"
cleanup() { rm -f "${tmp_png}"; }
trap cleanup EXIT

python3 scripts/make_test_png.py --out "${tmp_png}" --force >/dev/null

# Use an invalid model to avoid billable work; the goal is wiring + non-5xx.
if command -v jq >/dev/null 2>&1; then
  curl -sS -X POST "${RELAY_BASE_URL}/v1/images/variations" \
    -H "Authorization: Bearer ${RELAY_TOKEN}" \
    -F "image=@${tmp_png}" \
    -F "model=__invalid_model__" \
    -F "n=1" \
    -F "size=256x256" | jq
else
  curl -sS -X POST "${RELAY_BASE_URL}/v1/images/variations" \
    -H "Authorization: Bearer ${RELAY_TOKEN}" \
    -F "image=@${tmp_png}" \
    -F "model=__invalid_model__" \
    -F "n=1" \
    -F "size=256x256"
  echo
fi

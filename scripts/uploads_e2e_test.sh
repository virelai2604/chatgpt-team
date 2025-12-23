#!/usr/bin/env bash
set -euo pipefail

# Uploads API E2E (happy path + cancel path)
#
# Config via env:
#   RELAY_BASE_URL (default: http://localhost:8000)
#   RELAY_TOKEN    (default: dummy)
#   UPLOAD_PURPOSE (default: batch)
#
# If your account/environment disallows downloading for your chosen purpose,
# rerun with e.g.: UPLOAD_PURPOSE=assistants

RELAY_BASE_URL="${RELAY_BASE_URL:-${RELAY_BASE:-http://localhost:8000}}"
RELAY_TOKEN="${RELAY_TOKEN:-dummy}"
UPLOAD_PURPOSE="${UPLOAD_PURPOSE:-batch}"

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo -n "ping" > "${TMP_DIR}/ping.txt"
BYTES="$(wc -c < "${TMP_DIR}/ping.txt" | tr -d ' ')"

echo "== Create upload (happy path) =="
curl -sS -X POST "${RELAY_BASE_URL}/v1/uploads" \
  -H "Authorization: Bearer ${RELAY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"purpose\":\"${UPLOAD_PURPOSE}\",\"filename\":\"upload_ping.txt\",\"bytes\":${BYTES},\"mime_type\":\"text/plain\"}" \
  | tee "${TMP_DIR}/upload.json" | jq .

UPLOAD_ID="$(jq -r '.id' < "${TMP_DIR}/upload.json")"
if [ -z "${UPLOAD_ID}" ] || [ "${UPLOAD_ID}" = "null" ]; then
  echo "ERROR: missing upload id" >&2
  exit 10
fi

echo "== Add part =="
curl -sS -X POST "${RELAY_BASE_URL}/v1/uploads/${UPLOAD_ID}/parts" \
  -H "Authorization: Bearer ${RELAY_TOKEN}" \
  -F "data=@${TMP_DIR}/ping.txt;type=application/octet-stream" \
  | tee "${TMP_DIR}/part.json" | jq .

PART_ID="$(jq -r '.id' < "${TMP_DIR}/part.json")"
if [ -z "${PART_ID}" ] || [ "${PART_ID}" = "null" ]; then
  echo "ERROR: missing part id" >&2
  exit 11
fi

echo "== Complete upload =="
curl -sS -X POST "${RELAY_BASE_URL}/v1/uploads/${UPLOAD_ID}/complete" \
  -H "Authorization: Bearer ${RELAY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"part_ids\":[\"${PART_ID}\"]}" \
  | tee "${TMP_DIR}/complete.json" | jq .

FILE_ID="$(jq -r '.file.id // .file_id // .file // empty' < "${TMP_DIR}/complete.json")"
if [ -z "${FILE_ID}" ] || [ "${FILE_ID}" = "null" ]; then
  echo "ERROR: could not locate file id in completion response" >&2
  cat "${TMP_DIR}/complete.json" >&2
  exit 12
fi
echo "FILE_ID=${FILE_ID}"

echo "== Download file content (expect 200 for purpose=${UPLOAD_PURPOSE}) =="
curl -sS -D "${TMP_DIR}/content.h" -o "${TMP_DIR}/content.bin" \
  -L "${RELAY_BASE_URL}/v1/files/${FILE_ID}/content" \
  -H "Authorization: Bearer ${RELAY_TOKEN}"

status_line="$(head -n 1 "${TMP_DIR}/content.h")"
echo "Status: ${status_line}"

if ! echo "${status_line}" | grep -q " 200 "; then
  echo "ERROR: expected 200 download; got ${status_line}" >&2
  echo "Body:" >&2
  cat "${TMP_DIR}/content.bin" >&2 || true
  exit 14
fi

if ! cmp -s "${TMP_DIR}/content.bin" "${TMP_DIR}/ping.txt"; then
  echo "ERROR: content downloaded but does not match expected bytes" >&2
  exit 13
fi

echo "== Create upload (cancel path) =="
curl -sS -X POST "${RELAY_BASE_URL}/v1/uploads" \
  -H "Authorization: Bearer ${RELAY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"purpose\":\"${UPLOAD_PURPOSE}\",\"filename\":\"cancel_me.txt\",\"bytes\":${BYTES},\"mime_type\":\"text/plain\"}" \
  | tee "${TMP_DIR}/upload_cancel.json" | jq .

UPLOAD_CANCEL_ID="$(jq -r '.id' < "${TMP_DIR}/upload_cancel.json")"
if [ -z "${UPLOAD_CANCEL_ID}" ] || [ "${UPLOAD_CANCEL_ID}" = "null" ]; then
  echo "ERROR: missing upload id for cancel path" >&2
  exit 20
fi

echo "== Cancel upload =="
curl -sS -X POST "${RELAY_BASE_URL}/v1/uploads/${UPLOAD_CANCEL_ID}/cancel" \
  -H "Authorization: Bearer ${RELAY_TOKEN}" \
  | tee "${TMP_DIR}/cancel.json" | jq .

status="$(jq -r '.status' < "${TMP_DIR}/cancel.json")"
if [ "${status}" != "cancelled" ]; then
  echo "ERROR: expected status=cancelled, got status=${status}" >&2
  exit 21
fi

echo "== Uploads E2E: PASS =="

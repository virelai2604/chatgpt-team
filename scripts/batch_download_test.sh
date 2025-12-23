#!/usr/bin/env bash
set -euo pipefail

# Batch download E2E (create -> poll -> download output)
#
# Config via env:
#   RELAY_BASE_URL (default: http://localhost:8000)
#   RELAY_TOKEN    (default: dummy)
#   DEFAULT_MODEL  (default: gpt-5.1)
#   BATCH_MAX_WAIT_SECONDS (default: 900)
#   BATCH_POLL_INTERVAL_SECONDS (default: 3)
#
# Notes:
# - Batches are asynchronous and can queue; short caps often fail spuriously.
# - This script exits non-zero if the batch does not reach a terminal state within the max wait.

RELAY_BASE_URL="${RELAY_BASE_URL:-${RELAY_BASE:-http://localhost:8000}}"
RELAY_TOKEN="${RELAY_TOKEN:-dummy}"
DEFAULT_MODEL="${DEFAULT_MODEL:-gpt-5.1}"

MAX_WAIT="${BATCH_MAX_WAIT_SECONDS:-900}"
POLL="${BATCH_POLL_INTERVAL_SECONDS:-3}"

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "== Creating batch input JSONL =="
cat > "${TMP_DIR}/batch_input.jsonl" <<JSONL
{"custom_id":"ping-1","method":"POST","url":"/v1/responses","body":{"model":"${DEFAULT_MODEL}","input":"Return exactly: pong"}}
JSONL

echo "== Uploading batch input file (purpose=batch) =="
curl -sS -X POST "${RELAY_BASE_URL}/v1/files" \
  -H "Authorization: Bearer ${RELAY_TOKEN}" \
  -F "purpose=batch" \
  -F "file=@${TMP_DIR}/batch_input.jsonl;type=application/jsonl" \
  | tee "${TMP_DIR}/batch_file.json" | jq .

BATCH_INPUT_FILE_ID="$(jq -r '.id' <"${TMP_DIR}/batch_file.json")"
echo "BATCH_INPUT_FILE_ID=${BATCH_INPUT_FILE_ID}"

echo "== Creating batch =="
curl -sS -X POST "${RELAY_BASE_URL}/v1/batches" \
  -H "Authorization: Bearer ${RELAY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"input_file_id\":\"${BATCH_INPUT_FILE_ID}\",\"endpoint\":\"/v1/responses\",\"completion_window\":\"24h\"}" \
  | tee "${TMP_DIR}/batch.json" | jq .

BATCH_ID="$(jq -r '.id' <"${TMP_DIR}/batch.json")"
echo "BATCH_ID=${BATCH_ID}"

echo "== Polling batch status until terminal state (max_wait=${MAX_WAIT}s, poll=${POLL}s) =="
deadline=$(( $(date +%s) + MAX_WAIT ))

terminal="false"
last_status=""
last_output_id=""
last_error_id=""
last_resp=""

while [ "$(date +%s)" -lt "${deadline}" ]; do
  last_resp="$(curl -sS "${RELAY_BASE_URL}/v1/batches/${BATCH_ID}" -H "Authorization: Bearer ${RELAY_TOKEN}")"
  status="$(echo "$last_resp" | jq -r '.status')"
  out_id="$(echo "$last_resp" | jq -r '.output_file_id')"
  err_id="$(echo "$last_resp" | jq -r '.error_file_id')"

  last_status="$status"
  last_output_id="$out_id"
  last_error_id="$err_id"

  echo "status=${status} output_file_id=${out_id} error_file_id=${err_id}"

  case "$status" in
    completed|failed|expired|cancelled)
      terminal="true"
      break
      ;;
  esac

  sleep "${POLL}"
done

if [ "${terminal}" != "true" ]; then
  echo "ERROR: Batch did not reach terminal state in time." >&2
  echo "  BATCH_ID=${BATCH_ID}" >&2
  echo "  last_status=${last_status}" >&2
  echo "  last_output_file_id=${last_output_id}" >&2
  echo "  last_error_file_id=${last_error_id}" >&2
  echo "" >&2
  echo "Tip: try a longer wait, e.g. BATCH_MAX_WAIT_SECONDS=1800" >&2
  exit 2
fi

if [ "${last_status}" != "completed" ]; then
  echo "ERROR: Batch ended in status=${last_status}" >&2
  echo "  error_file_id=${last_error_id}" >&2
  echo "  full_response:" >&2
  echo "$last_resp" | jq . >&2 || true
  exit 3
fi

OUT_FILE_ID="${last_output_id}"
if [ -z "${OUT_FILE_ID}" ] || [ "${OUT_FILE_ID}" = "null" ]; then
  echo "ERROR: Batch completed but output_file_id is null" >&2
  echo "$last_resp" | jq . >&2 || true
  exit 4
fi

echo "== Downloading batch output file content =="
curl -sS -L "${RELAY_BASE_URL}/v1/files/${OUT_FILE_ID}/content" \
  -H "Authorization: Bearer ${RELAY_TOKEN}" \
  -o "${TMP_DIR}/batch_output.jsonl"

echo "Saved: ${TMP_DIR}/batch_output.jsonl"
echo "== First 5 lines =="
head -n 5 "${TMP_DIR}/batch_output.jsonl"

echo "== Done =="

#!/usr/bin/env bash
set -euo pipefail

RELAY_BASE="${RELAY_BASE:-http://localhost:8000}"
AUTH_HEADER="${AUTH_HEADER:-Authorization: Bearer dummy}"
MODEL="${MODEL:-gpt-5.1}"

require() {
  command -v "$1" >/dev/null 2>&1 || { echo "Missing dependency: $1" >&2; exit 1; }
}

require curl
require jq

tmpdir="$(mktemp -d)"
cleanup() { rm -rf "$tmpdir"; }
trap cleanup EXIT

echo "== Creating batch input JSONL =="
cat > "$tmpdir/batch_input.jsonl" <<JSONL
{"custom_id":"ping-1","method":"POST","url":"/v1/responses","body":{"model":"${MODEL}","input":"Return exactly: pong"}}
JSONL

echo "== Uploading batch input file (purpose=batch) =="
curl -sS -X POST "${RELAY_BASE}/v1/files" \
  -H "${AUTH_HEADER}" \
  -F "purpose=batch" \
  -F "file=@${tmpdir}/batch_input.jsonl;type=application/jsonl" \
  | tee "$tmpdir/batch_file.json" | jq .

BATCH_INPUT_FILE_ID="$(jq -r '.id' < "$tmpdir/batch_file.json")"
if [[ -z "${BATCH_INPUT_FILE_ID}" || "${BATCH_INPUT_FILE_ID}" == "null" ]]; then
  echo "Failed to upload batch input file (no id returned)" >&2
  exit 1
fi
echo "BATCH_INPUT_FILE_ID=${BATCH_INPUT_FILE_ID}"

echo "== Creating batch =="
curl -sS -X POST "${RELAY_BASE}/v1/batches" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d "{\"input_file_id\":\"${BATCH_INPUT_FILE_ID}\",\"endpoint\":\"/v1/responses\",\"completion_window\":\"24h\"}" \
  | tee "$tmpdir/batch.json" | jq .

BATCH_ID="$(jq -r '.id' < "$tmpdir/batch.json")"
if [[ -z "${BATCH_ID}" || "${BATCH_ID}" == "null" ]]; then
  echo "Failed to create batch (no id returned)" >&2
  exit 1
fi
echo "BATCH_ID=${BATCH_ID}"

echo "== Polling batch status until terminal state =="
# No time estimates; this loop simply polls and exits on terminal states.
while true; do
  curl -sS "${RELAY_BASE}/v1/batches/${BATCH_ID}" -H "${AUTH_HEADER}" \
    | tee "$tmpdir/batch_status.json" >/dev/null

  status="$(jq -r '.status' < "$tmpdir/batch_status.json")"
  out_id="$(jq -r '.output_file_id' < "$tmpdir/batch_status.json")"
  err_id="$(jq -r '.error_file_id' < "$tmpdir/batch_status.json")"

  echo "status=${status} output_file_id=${out_id} error_file_id=${err_id}"

  case "${status}" in
    completed)
      if [[ -z "${out_id}" || "${out_id}" == "null" ]]; then
        echo "Batch is completed but output_file_id is null. Dumping batch object:" >&2
        cat "$tmpdir/batch_status.json" | jq .
        exit 1
      fi

      echo "== Downloading batch output file content =="
      curl -sS -L "${RELAY_BASE}/v1/files/${out_id}/content" \
        -H "${AUTH_HEADER}" \
        --output "$tmpdir/batch_output.jsonl"

      echo "Saved: $tmpdir/batch_output.jsonl"
      echo "== First 5 lines =="
      head -n 5 "$tmpdir/batch_output.jsonl" || true
      echo "== Done =="
      exit 0
      ;;
    failed|expired|cancelled|canceled)
      echo "Batch terminal failure state: ${status}" >&2
      echo "Batch object:" >&2
      cat "$tmpdir/batch_status.json" | jq .

      if [[ -n "${err_id}" && "${err_id}" != "null" ]]; then
        echo "== Downloading error_file_id content =="
        curl -sS -L "${RELAY_BASE}/v1/files/${err_id}/content" \
          -H "${AUTH_HEADER}" \
          --output "$tmpdir/batch_error.jsonl" || true
        echo "Saved: $tmpdir/batch_error.jsonl"
        head -n 20 "$tmpdir/batch_error.jsonl" || true
      fi
      exit 2
      ;;
    validating|in_progress|finalizing)
      # continue polling
      sleep 2
      ;;
    *)
      echo "Unknown batch status: ${status}" >&2
      cat "$tmpdir/batch_status.json" | jq .
      exit 3
      ;;
  esac
done

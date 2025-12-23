#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
RELAY_TOKEN="${2:-dummy}"
MODEL="${3:-gpt-5.1}"

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

need curl
need jq
need mktemp

TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

echo "== Creating batch input JSONL =="
cat > "$TMP_DIR/batch_input.jsonl" <<JSONL
{"custom_id":"ping-1","method":"POST","url":"/v1/responses","body":{"model":"$MODEL","input":"Return exactly: pong"}}
JSONL

echo "== Uploading batch input file (purpose=batch) =="
curl -sS -X POST "$BASE_URL/v1/files" \
  -H "Authorization: Bearer $RELAY_TOKEN" \
  -F "purpose=batch" \
  -F "file=@$TMP_DIR/batch_input.jsonl;type=application/jsonl" \
  | tee "$TMP_DIR/batch_file.json" | jq .

BATCH_INPUT_FILE_ID="$(jq -r '.id' <"$TMP_DIR/batch_file.json")"
echo "BATCH_INPUT_FILE_ID=$BATCH_INPUT_FILE_ID"

echo "== Creating batch =="
curl -sS -X POST "$BASE_URL/v1/batches" \
  -H "Authorization: Bearer $RELAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"input_file_id\":\"${BATCH_INPUT_FILE_ID}\",\"endpoint\":\"/v1/responses\",\"completion_window\":\"24h\"}" \
  | tee "$TMP_DIR/batch.json" | jq .

BATCH_ID="$(jq -r '.id' <"$TMP_DIR/batch.json")"
echo "BATCH_ID=$BATCH_ID"

echo "== Polling batch status until terminal state =="
terminal=0
OUT_FILE_ID="null"
ERR_FILE_ID="null"

for i in $(seq 1 120); do
  status_json="$(curl -sS "$BASE_URL/v1/batches/${BATCH_ID}" -H "Authorization: Bearer $RELAY_TOKEN")"
  status="$(echo "$status_json" | jq -r '.status')"
  OUT_FILE_ID="$(echo "$status_json" | jq -r '.output_file_id')"
  ERR_FILE_ID="$(echo "$status_json" | jq -r '.error_file_id')"
  echo "status=$status output_file_id=$OUT_FILE_ID error_file_id=$ERR_FILE_ID"

  case "$status" in
    completed|failed|expired|cancelled)
      terminal=1
      break
      ;;
  esac

  sleep 2
done

if [[ "$terminal" != "1" ]]; then
  echo "Batch did not reach terminal state in time." >&2
  exit 1
fi

if [[ "$status" != "completed" ]]; then
  echo "Batch did not complete successfully (status=$status)." >&2
  echo "$status_json" | jq . >&2 || true
  exit 1
fi

if [[ "$OUT_FILE_ID" == "null" || -z "$OUT_FILE_ID" ]]; then
  echo "Batch completed but output_file_id is null." >&2
  echo "$status_json" | jq . >&2 || true
  exit 1
fi

echo "== Downloading batch output file content =="
curl -sS -L "$BASE_URL/v1/files/${OUT_FILE_ID}/content" \
  -H "Authorization: Bearer $RELAY_TOKEN" \
  -o "$TMP_DIR/batch_output.jsonl"

echo "Saved: $TMP_DIR/batch_output.jsonl"
echo "== First 5 lines =="
head -n 5 "$TMP_DIR/batch_output.jsonl" || true

echo "== Done =="

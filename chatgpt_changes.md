# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 3aaad5ad4a816423a18d6e9a35eee443cbecd3d1
Dirs: app tests static schemas
Root files: project-tree.md pyproject.toml
Mode: changes
Generated: 2025-12-23T10:54:17+07:00

## CHANGE SUMMARY (since 3aaad5ad4a816423a18d6e9a35eee443cbecd3d1, includes worktree)

```
M	tests/test_relay_auth_guard.py
```

## PATCH (since 3aaad5ad4a816423a18d6e9a35eee443cbecd3d1, includes worktree)

```diff
diff --git a/tests/test_relay_auth_guard.py b/tests/test_relay_auth_guard.py
index bb95dfd..3594b52 100644
--- a/tests/test_relay_auth_guard.py
+++ b/tests/test_relay_auth_guard.py
@@ -1,38 +1,96 @@
-# tests/test_relay_auth_guard.py
-from __future__ import annotations
-
-import os
-
-import httpx
-import pytest
-
-from app.main import app
-
-# All tests here are async
-pytestmark = pytest.mark.asyncio
-
-
-@pytest.mark.integration
-@pytest.mark.skipif(
-    os.getenv("RELAY_AUTH_ENABLED", "false").lower() != "true",
-    reason="Set RELAY_AUTH_ENABLED=true to run auth guard test",
-)
-async def test_responses_requires_valid_relay_key() -> None:
-    """
-    When RELAY_AUTH_ENABLED=true and no relay key is provided, the relay
-    must reject the request with 401/403 rather than silently forwarding.
-    """
-    transport = httpx.ASGITransport(app=app)
-
-    async with httpx.AsyncClient(
-        transport=transport,
-        base_url="http://testserver",
-        timeout=30.0,
-    ) as client:
-        # No Authorization, no X-Relay-Key
-        resp = await client.post(
-            "/v1/responses",
-            json={"model": "gpt-5.1", "input": "Should not succeed"},
-        )
-
-    assert resp.status_code in (401, 403)
+#!/usr/bin/env bash
+set -euo pipefail
+
+BASE_URL="${1:-http://localhost:8000}"
+RELAY_TOKEN="${2:-dummy}"
+MODEL="${3:-gpt-5.1}"
+
+need() {
+  command -v "$1" >/dev/null 2>&1 || {
+    echo "Missing required command: $1" >&2
+    exit 1
+  }
+}
+
+need curl
+need jq
+need mktemp
+
+TMP_DIR="$(mktemp -d)"
+cleanup() { rm -rf "$TMP_DIR"; }
+trap cleanup EXIT
+
+echo "== Creating batch input JSONL =="
+cat > "$TMP_DIR/batch_input.jsonl" <<JSONL
+{"custom_id":"ping-1","method":"POST","url":"/v1/responses","body":{"model":"$MODEL","input":"Return exactly: pong"}}
+JSONL
+
+echo "== Uploading batch input file (purpose=batch) =="
+curl -sS -X POST "$BASE_URL/v1/files" \
+  -H "Authorization: Bearer $RELAY_TOKEN" \
+  -F "purpose=batch" \
+  -F "file=@$TMP_DIR/batch_input.jsonl;type=application/jsonl" \
+  | tee "$TMP_DIR/batch_file.json" | jq .
+
+BATCH_INPUT_FILE_ID="$(jq -r '.id' <"$TMP_DIR/batch_file.json")"
+echo "BATCH_INPUT_FILE_ID=$BATCH_INPUT_FILE_ID"
+
+echo "== Creating batch =="
+curl -sS -X POST "$BASE_URL/v1/batches" \
+  -H "Authorization: Bearer $RELAY_TOKEN" \
+  -H "Content-Type: application/json" \
+  -d "{\"input_file_id\":\"${BATCH_INPUT_FILE_ID}\",\"endpoint\":\"/v1/responses\",\"completion_window\":\"24h\"}" \
+  | tee "$TMP_DIR/batch.json" | jq .
+
+BATCH_ID="$(jq -r '.id' <"$TMP_DIR/batch.json")"
+echo "BATCH_ID=$BATCH_ID"
+
+echo "== Polling batch status until terminal state =="
+terminal=0
+OUT_FILE_ID="null"
+ERR_FILE_ID="null"
+
+for i in $(seq 1 120); do
+  status_json="$(curl -sS "$BASE_URL/v1/batches/${BATCH_ID}" -H "Authorization: Bearer $RELAY_TOKEN")"
+  status="$(echo "$status_json" | jq -r '.status')"
+  OUT_FILE_ID="$(echo "$status_json" | jq -r '.output_file_id')"
+  ERR_FILE_ID="$(echo "$status_json" | jq -r '.error_file_id')"
+  echo "status=$status output_file_id=$OUT_FILE_ID error_file_id=$ERR_FILE_ID"
+
+  case "$status" in
+    completed|failed|expired|cancelled)
+      terminal=1
+      break
+      ;;
+  esac
+
+  sleep 2
+done
+
+if [[ "$terminal" != "1" ]]; then
+  echo "Batch did not reach terminal state in time." >&2
+  exit 1
+fi
+
+if [[ "$status" != "completed" ]]; then
+  echo "Batch did not complete successfully (status=$status)." >&2
+  echo "$status_json" | jq . >&2 || true
+  exit 1
+fi
+
+if [[ "$OUT_FILE_ID" == "null" || -z "$OUT_FILE_ID" ]]; then
+  echo "Batch completed but output_file_id is null." >&2
+  echo "$status_json" | jq . >&2 || true
+  exit 1
+fi
+
+echo "== Downloading batch output file content =="
+curl -sS -L "$BASE_URL/v1/files/${OUT_FILE_ID}/content" \
+  -H "Authorization: Bearer $RELAY_TOKEN" \
+  -o "$TMP_DIR/batch_output.jsonl"
+
+echo "Saved: $TMP_DIR/batch_output.jsonl"
+echo "== First 5 lines =="
+head -n 5 "$TMP_DIR/batch_output.jsonl" || true
+
+echo "== Done =="
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: tests/test_relay_auth_guard.py @ WORKTREE
```
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
```


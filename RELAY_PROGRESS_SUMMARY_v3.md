# Relay Progress Summary (v3)

Generated: 2025-12-23

## What is confirmed working

### Files API (`/v1/files`)
- Upload works via relay for `purpose=batch`, `purpose=assistants`, `purpose=user_data`.
- File metadata retrieval (`GET /v1/files/{file_id}`) works.
- Content download policy is enforced by upstream:
  - `purpose=user_data`: download is forbidden (`400 Not allowed to download files of purpose: user_data`).
  - `purpose=batch`: download works (`GET /v1/files/{file_id}/content` returns the JSONL).

Evidence
- `tests/test_files_and_batches_integration.py` all PASS (3/3).
- Manual curls in session logs match expected upstream behavior.

### Batches API (`/v1/batches`)
- Create batch, poll to terminal state, and download output file all work end-to-end through relay.
- A longer poll window may be required during upstream load (set `BATCH_MAX_WAIT_SECONDS`).

Evidence
- `scripts/batch_download_test.sh` produces `pong` in output JSONL.

### Responses streaming (SSE)
- SSE smoke test passes: correct `text/event-stream` behavior and incremental chunk reads.

Evidence
- `tests/test_success_gates_integration.py::test_gate_b_sse_smoke_streaming_content_type_and_incremental_reads` PASS.

### OpenAPI operationId sanity
- No duplicate `operationId` warnings.

Evidence
- `tests/test_success_gates_integration.py::test_gate_c_openapi_has_no_duplicate_operation_ids` PASS.

## What is still failing

### Uploads cancel path (Gate A)
Symptom
- `POST /v1/uploads/{upload_id}/cancel` returns `415 Unsupported Media Type` when sent without `Content-Type` and with an empty body.

Root cause
- Relay `ValidationMiddleware` currently enforces `Content-Type` for all POST/PUT/PATCH requests, even when the request body is empty.

Fix
- Update middleware to allow empty-body POST/PUT/PATCH with no `Content-Type` (based on headers: `Content-Length: 0` and no `Transfer-Encoding`).

### Containers/Videos content endpoints (Gate D)
Symptom
- `GET /v1/containers/cntr_dummy/files/file_dummy/content` returns relay `500`.

Root cause
- Route implementation uses older helper signatures in `app.api.forward_openai` (e.g., `build_outbound_headers(...)`), producing runtime exceptions after refactors.

Fix
- Add backward-compatible helper signatures in `app.api.forward_openai`.

## Next execution

After applying fixes, rerun:

```bash
INTEGRATION_OPENAI_API_KEY=1 pytest -m integration -vv tests/test_success_gates_integration.py
```

Optional bash harness:

```bash
RELAY_BASE_URL=http://localhost:8000 RELAY_TOKEN=dummy INTEGRATION_OPENAI_API_KEY=1 ./scripts/run_success_gates.sh
```

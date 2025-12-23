# Relay Checklist (v7)

Generated: 2025-12-23

This checklist tracks relay readiness across the current success gates.

## Gate A — Uploads E2E (happy path + cancel path)
Status: **FAIL**

- Happy path (create upload → add part → complete): PASS
- Cancel path (`POST /v1/uploads/{upload_id}/cancel` with empty body/no `Content-Type`): FAIL
  - Current relay response: `415 Unsupported Media Type` with `{"detail":"Unsupported Media Type: ''"}`
  - Root cause: relay `ValidationMiddleware` requires `Content-Type` for all POST/PUT/PATCH requests, even when the body is empty.

Fix required
- Allow empty-body POST/PUT/PATCH requests with no `Content-Type` header (based on `Content-Length: 0` and no `Transfer-Encoding`).

## Gate B — SSE smoke (streaming content-type + incremental reads)
Status: **PASS**

- `tests/test_success_gates_integration.py::test_gate_b_sse_smoke_streaming_content_type_and_incremental_reads` passed.

## Gate C — OpenAPI has no duplicate operationId warnings
Status: **PASS**

- `tests/test_success_gates_integration.py::test_gate_c_openapi_has_no_duplicate_operation_ids` passed.

## Gate D — containers/videos `/content` endpoints validated
Status: **FAIL**

- `tests/test_success_gates_integration.py::test_gate_d_containers_and_videos_content_endpoints_no_relay_5xx` failed
  - `GET /v1/containers/cntr_dummy/files/file_dummy/content` returned `500` from relay.
  - Root cause: route code uses legacy helper function signatures (e.g., `build_outbound_headers(...)`) that no longer match `app.api.forward_openai` after refactors, causing runtime exceptions.

Fix required
- Add backward-compatible signatures to `app.api.forward_openai` helpers (at minimum `build_outbound_headers`), and make `forward_openai_method_path` support the legacy `(method, path, request)` call pattern.

## Local command

Run all gates:

```bash
INTEGRATION_OPENAI_API_KEY=1 \
pytest -m integration -vv tests/test_success_gates_integration.py
```

Optionally, run the bash harness:

```bash
RELAY_BASE_URL=http://localhost:8000 RELAY_TOKEN=dummy INTEGRATION_OPENAI_API_KEY=1 \
./scripts/run_success_gates.sh
```

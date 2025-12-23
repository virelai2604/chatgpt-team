# Relay Checklist (v10)

## Status snapshot (as of 2025-12-23)

### Success gates
- Gate A (Uploads E2E: happy + cancel): **PARTIAL**
  - Happy path: create upload → add part → complete: **PASS**
  - Cancel path: **FAIL** (relay returns **415 Unsupported Media Type** when POST has no `Content-Type` and no body)
- Gate B (SSE smoke): **PASS**
- Gate C (OpenAPI operationId duplicates): **PASS**
- Gate D (containers/videos `/content` endpoints): **FAIL**
  - `/v1/containers/{container_id}/files/{file_id}/content` returns **500** for dummy IDs; should forward upstream and return <500 (typically 404/400)
  - `/v1/videos/{video_id}/content` was not reached in the failing run (test aborted at first failure)

## What we have implemented and verified

### Files & batches
- `/v1/files` upload (multipart) works end-to-end.
- `/v1/batches` create + poll + retrieve + download output file works end-to-end.
- Batch output file (`/v1/files/{id}/content`) is downloadable (policy-aligned for batch outputs).
- User data file download remains blocked (policy-aligned).

### Proxy & SSE
- SSE streaming path works for `POST /v1/responses:stream` (content-type, incremental reads).

### OpenAPI
- OpenAPI spec generation runs without duplicate `operationId` warnings (gate C passed).

## Known defects / root causes

### A1 — Upload cancel returns 415 (no Content-Type)
- Root cause: request validation middleware enforces `Content-Type` for POST/PUT/PATCH even when `Content-Length: 0` and the request body is empty.
- Fix: update middleware to allow empty-body requests (Content-Length 0 or no body) without requiring `Content-Type`.

### D1 — Containers content endpoint returns 500 for upstream 4xx
- Root cause: container content route streams via httpx and calls `raise_for_status()`, which turns upstream 4xx (expected for dummy IDs) into an exception → relay 500.
- Fix: never `raise_for_status()` for content proxying; propagate upstream status + body. Stream only on 2xx.

## Next actions (ordered)
1. Patch `app/middleware/validation.py` to allow empty-body POST/PUT/PATCH without Content-Type.
2. Patch `app/routes/containers.py` to propagate upstream 4xx/5xx (no raise_for_status) and only stream 2xx.
3. Ensure `app/api/forward_openai.py` exports the legacy helpers used across route modules (e.g., `forward_embeddings_create`, legacy `build_upstream_url` call style).
4. Rerun: `pytest -m integration -vv tests/test_success_gates_integration.py`.
5. If Gate D still fails, validate `/v1/videos/{id}/content` similarly.

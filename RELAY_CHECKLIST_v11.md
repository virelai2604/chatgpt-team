# Relay Checklist (v11)

## Status snapshot (as of 2025-12-23)

### Success gates (tests/test_success_gates_integration.py)
- Gate A (Uploads E2E: happy + cancel): **PASS**
  - Happy path: create upload → add part (multipart field `data`) → complete: PASS
  - Cancel path: POST `/v1/uploads/{upload_id}/cancel` with empty body: PASS
- Gate B (SSE smoke): **PASS**
  - POST `/v1/responses:stream` returns `text/event-stream` and supports incremental reads
- Gate C (OpenAPI): **PASS**
  - `GET /openapi.json` has **no duplicate** `operationId` values
- Gate D (containers/videos `/content` endpoints): **PASS**
  - Containers content endpoint exists and does **not** return relay 5xx for dummy IDs (upstream 4xx is OK)
  - Videos content endpoint exists and does **not** return relay 5xx for dummy IDs (upstream 4xx is OK)

## Required environment for local runs
- Ensure integration tests target the local relay:
  - `unset RELAY_BASE_URL` (or set `RELAY_BASE_URL=http://localhost:8000`)
- Minimal env for tests:
  - `export RELAY_TOKEN=dummy`
  - `export INTEGRATION_OPENAI_API_KEY=1` (enables integration tests; see test header comment)
- Server:
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Tests:
  - `pytest -m integration -vv tests/test_success_gates_integration.py`

## What we have implemented and verified (scope: success gates)

### Uploads
- `POST /v1/uploads` → returns an upload object with id like `upload_...`
- `POST /v1/uploads/{upload_id}/parts` → multipart upload (field name **MUST** be `data`) returns part id `part_...`
- `POST /v1/uploads/{upload_id}/complete` → returns status `completed` and file object id like `file-...`
- `POST /v1/uploads/{upload_id}/cancel` → returns status `cancelled` even when request has:
  - no body
  - no `Content-Type` header

### Responses (SSE smoke)
- `POST /v1/responses:stream` → relays an SSE stream with:
  - `Content-Type: text/event-stream`
  - incremental event reads (no buffered “all-at-once” response)

### OpenAPI
- `GET /openapi.json` → passes operationId uniqueness validation

### Containers / Videos content endpoints
- `GET /v1/containers/{container_id}/files/{file_id}/content`
- `GET /v1/videos/{video_id}/content`

Expected behavior for dummy IDs:
- upstream returns 400/404
- relay propagates the upstream status/body and does **not** convert it to 5xx

### Proxy header hygiene (client compatibility)
- JSON endpoints avoid sending misleading `Content-Encoding` when the body is already decoded by the upstream client.
- Relay avoids forwarding `Accept-Encoding` upstream for JSON requests to reduce compression-related surprises.

## Resolved defects / root causes (from v10)

### A1 — Upload cancel returned 415 (no Content-Type)
- Fix: validation middleware permits empty-body POST/PUT/PATCH without requiring `Content-Type`.

### D1 — Containers content endpoint returned 500 for upstream 4xx
- Fix: content proxying does **not** `raise_for_status()` for non-2xx. Relay returns upstream status + body; streaming is only used for 2xx.

### E1 — JSONDecodeError when RELAY_BASE_URL points to deployed relay
- Symptom: `requests.Response.json()` fails; response shows `Content-Encoding: gzip` but body bytes are not JSON.
- Fix: strip `Content-Encoding` from proxied responses and avoid forwarding `Accept-Encoding` upstream (requires redeploy for onrender).

## Next actions (ordered)
1. Deploy the latest code to Render and validate parity:
   - `export RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com`
   - `export RELAY_TOKEN=<render-relay-token>`
   - `pytest -m integration -vv tests/test_success_gates_integration.py`
2. Add a one-liner smoke check to confirm JSON parsing works against remote:
   - The create-upload response should have **no** `Content-Encoding`, and the first byte should be `{`.
3. Optional hardening:
   - Add a CI job to run integration gates against localhost.
   - Add a “remote smoke” job (nightly) that runs against onrender with a dedicated token/key.

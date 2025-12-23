# Relay Checklist (v10)

## Status snapshot (as of 2025-12-23) — UPDATED

### Success gates (integration)
- Gate A (Uploads E2E: happy + cancel): **PASS (local)**
  - Happy path: create upload → add part → complete: **PASS**
  - Cancel path: **PASS**
- Gate B (SSE smoke): **PASS**
- Gate C (OpenAPI operationId duplicates): **PASS**
- Gate D (containers/videos `/content` endpoints): **PASS**
  - `/v1/containers/{container_id}/files/{file_id}/content`: **PASS** (returns <500 for dummy ids; forwards upstream 4xx/5xx)
  - `/v1/videos/{video_id}/content`: **PASS** (returns <500 for dummy ids; forwards upstream 4xx/5xx)

### Deployment parity check (still required)
- Deployed relay base (example): `https://chatgpt-team-relay.onrender.com` — **NEEDS RE-VERIFY**
  - Previously observed symptom when targeting deployed base with Python `requests`:
    - Response had `Content-Encoding: gzip`
    - `requests.Response.json()` failed with JSONDecodeError (payload not decodable as JSON)
  - Local relay base: `http://localhost:8000` — **VERIFIED PASS**

## What we have implemented and verified

### Uploads API (Gate A)
- `/v1/uploads` create works.
- `/v1/uploads/{upload_id}/parts` (multipart field name: `data`) works.
- `/v1/uploads/{upload_id}/complete` works.
- `/v1/uploads/{upload_id}/cancel` works (empty-body POST allowed).

### Files & batches
- `/v1/files` upload (multipart) works end-to-end.
- `/v1/batches` create + poll + retrieve + download output file works end-to-end.
- Batch output file (`/v1/files/{id}/content`) is downloadable (policy-aligned for batch outputs).
- User data file download remains blocked (policy-aligned).

### Proxy & SSE (Gate B)
- SSE streaming path works for `POST /v1/responses:stream` (content-type, incremental reads).

### OpenAPI (Gate C)
- OpenAPI spec generation runs without duplicate `operationId` warnings.

### Containers/videos content endpoints (Gate D)
- Content endpoints exist and are wired.
- For dummy IDs, relay returns <500 (typically 404/400 from upstream); does not raise relay 5xx.

## Environment / test runner notes

### RELAY_BASE_URL behavior
- Integration tests use `RELAY_BASE_URL` when set.
  - If unset, tests default to `http://localhost:8000`.

Recommended:
- Local run:
  - `unset RELAY_BASE_URL`
  - or `export RELAY_BASE_URL=http://localhost:8000`
- Deployed run:
  - `export RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com`
  - Ensure deployed instance is up-to-date and returns client-decodable JSON.

## Known defects / root causes
- None blocking success gates on localhost.
- Potential deployment issue:
  - Response compression / encoding mismatch for some Python clients when using deployed base URL (re-verify after redeploy).

## Next actions (ordered)
1. Redeploy latest `main` to Render/Onrender.
2. Re-run success gates against deployed base:
   - `RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com pytest -m integration -vv tests/test_success_gates_integration.py`
3. If deployed run still fails with JSON decode:
   - Confirm relay is stripping problematic response headers (e.g., `Content-Encoding`) when returning decoded bytes
   - Consider forcing identity encoding for upstream and/or disabling edge compression transforms for `/v1/*`
4. Commit this updated checklist snapshot (or bump to v11 if you want immutable versioning).

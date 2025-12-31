# Relay Checklist (v19)

_Last updated: 2025-12-31_

## 0) Baseline integrity (must stay green)

- [x] `GET /openapi.json` returns **200**
- [x] `GET /openapi.actions.json` returns **200**
- [x] Both OpenAPI endpoints are stable across repeated uvicorn restarts
- [x] No transient 500s observed during smoke/integration runs

Verification:
```bash
curl -fsS http://127.0.0.1:8000/openapi.actions.json | jq .info
```

---

## 1) Actions OpenAPI correctness

### 1.1 Operation ID uniqueness
- [x] No duplicate `operationId` in `openapi.actions.json` (Local)

Verification:
```bash
curl -fsS http://127.0.0.1:8000/openapi.actions.json \
  | jq -r '.. | objects | .operationId? // empty' \
  | sort | uniq -d
# Expected: empty output
```

### 1.2 Actions schema is intentionally curated
- [x] Only intended routes are present
- [x] No WebSocket endpoints in Actions schema
- [x] No binary `/content` download endpoints in Actions schema

---

## 2) Router registration & ordering (avoid FastAPI duplication pitfalls)

- [x] Each router is registered exactly once
- [x] Core routers mounted before proxy
- [x] `/v1/proxy` mounted last (explicit routes win)

Confirmed in:
- `app/routes/register_routes.py`

---

## 3) Upload lifecycle (core + Actions)

### 3.1 Core uploads (resumable)
- [x] `POST /v1/uploads`
- [x] `POST /v1/uploads/{upload_id}/parts`
- [x] `POST /v1/uploads/{upload_id}/complete`
- [x] `POST /v1/uploads/{upload_id}/cancel`

### 3.2 Actions wrappers (JSON → multipart)
- [x] `POST /v1/actions/uploads`
- [x] `POST /v1/actions/uploads/{upload_id}/parts`
- [x] `POST /v1/actions/uploads/{upload_id}/complete`
- [x] `POST /v1/actions/uploads/{upload_id}/cancel`

### 3.3 Constraints enforced
- [x] base64 validation
- [x] empty payload rejection
- [x] maximum part size limits (policy-driven)

---

## 4) Files (multipart risk isolated)

- [x] Core `POST /v1/files` exists, but is **not** reachable via `/v1/proxy` (multipart blocked by policy)
- [x] Actions wrapper is available:
  - [x] `POST /v1/actions/files/upload` (JSON → multipart)

---

## 5) Responses streaming (SSE wrapper)

- [x] Non-Actions stream helper:
  - [x] `POST /v1/responses:stream` (SSE)
- [x] Actions wrapper:
  - [x] `POST /v1/actions/responses/stream`
- [x] Streaming is explicitly excluded from proxy (colon-path policy + streaming risk)

---

## 6) Realtime

### 6.1 Actions-supported surface
- [x] `POST /v1/realtime/sessions` (in Actions schema)

### 6.2 Non-Actions surfaces
- [x] `WS /v1/realtime/ws` implemented (non-Actions)

### 6.3 Local-only helpers
- [x] `GET /v1/realtime/sessions/introspect` (local helper)
- [x] `POST /v1/realtime/sessions/validate` (local helper)

Policy expectation:
- These **local-only** endpoints must be explicitly bucketed as **EXCLUDE_REALTIME_LOCAL** in coverage mapping.

---

## 7) Videos (core + Actions)

### 7.1 Core surface
- [x] `POST /v1/videos` (JSON or multipart)
- [x] `POST /v1/videos/{video_id}/remix`
- [x] `GET /v1/videos` / `GET /v1/videos/{video_id}`
- [x] `DELETE /v1/videos/{video_id}`

### 7.2 Actions wrappers
- [x] `POST /v1/actions/videos`
- [x] `POST /v1/actions/videos/{video_id}/remix`
- [x] `POST /v1/actions/videos/generations` (JSON → multipart helper)

Policy expectation:
- Video multipart endpoints remain **blocked via proxy** and are accessed via wrappers or direct routes.

---

## 8) Proxy allowlist hygiene (security posture)

- [x] Explicit allowlist only (deny-by-default)
- [x] No wildcard leakage
- [x] Binary `/content` paths blocked
- [x] Multipart endpoints blocked via proxy
- [x] Legacy and meta routes excluded

---

## 9) Coverage guardrail (must remain authoritative)

- [x] Local: `./scripts/coverage_report.sh` produces **no UNKNOWN**
- [ ] Render: `./scripts/coverage_report.sh` currently reports **1 UNKNOWN**
  - `GET /actions/system/info` (implemented in `app/routes/actions.py`)

Required action:
- [ ] Assign `GET /actions/system/info` to an explicit bucket:
  - Preferred: **EXCLUDE_LEGACY** (non-`/v1` surface), or a new explicit exclusion bucket such as **EXCLUDE_META_NONV1**.
  - Alternative: remove/disable that endpoint if it is not required.

Acceptance criteria:
```bash
RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com ./scripts/coverage_report.sh
# Expected: ERROR: UNKNOWN endpoints detected (0)
```

---

## 10) Integration tests (release gate)

- [x] `pytest -q -m integration` against local uvicorn is **PASS**

Verification:
```bash
export RELAY_BASE_URL=http://127.0.0.1:8000
pytest -q -m integration
```

---

## 11) Incremental feature additions (no refactor risk)

Implement in small, isolated increments that do **not** disturb proxy policy.

### Next features (recommended order)
1. **Coverage fix for `/actions/system/info`** (doc + bucket)
2. **Realtime smoke tests**
   - HTTP: `POST /v1/realtime/sessions`
   - WS: basic connect/echo wiring under `/v1/realtime/ws` (non-Actions)
3. **Video generations validation + tests**
   - Ensure `/v1/actions/videos/generations` handles:
     - missing input video
     - invalid base64
     - max-bytes, max-frames, max-duration
4. **SSE streaming regression tests**
   - Verify relay returns `text/event-stream` and forwards chunking safely
5. **Optional**: explicit exclusions for any future local-only helpers

---

## Status

- **Local**: green
- **Render**: one coverage guardrail item remaining (`/actions/system/info`)

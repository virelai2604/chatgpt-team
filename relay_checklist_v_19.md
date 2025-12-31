# Relay Checklist (v19)

## 0) Baseline Integrity

- [x] `openapi.json` loads successfully
- [x] `openapi.actions.json` loads successfully
- [x] Stable across repeated uvicorn restarts
- [x] No transient 500 errors observed

Verification:
```bash
curl -fsS http://127.0.0.1:8000/openapi.actions.json | jq .info
```

---

## 1) Actions OpenAPI Correctness

- [x] No duplicate `operationId`
- [x] All schemas resolve (Pydantic v2 rebuilds applied)
- [x] Actions-safe endpoints only

Verification:
```bash
curl -fsS http://127.0.0.1:8000/openapi.actions.json \
  | jq -r '.. | objects | .operationId? // empty' \
  | sort | uniq -d
```
Expected: empty output

---

## 2) Router Registration & Ordering

- [x] Each router registered exactly once
- [x] `uploads.actions_router` registered once
- [x] `videos.actions_router` registered once
- [x] Core routers mounted before proxy
- [x] `/v1/proxy` mounted last

Confirmed in `app/routes/register_routes.py`.

---

## 3) Upload Lifecycle (Core + Actions)

### Core Uploads
- [x] `POST /v1/uploads`
- [x] `POST /v1/uploads/{upload_id}/parts`
- [x] `POST /v1/uploads/{upload_id}/complete`
- [x] `POST /v1/uploads/{upload_id}/cancel`

### Actions Wrappers
- [x] `POST /v1/actions/uploads`
- [x] `POST /v1/actions/uploads/{upload_id}/parts`
- [x] `POST /v1/actions/uploads/{upload_id}/complete`
- [x] `POST /v1/actions/uploads/{upload_id}/cancel`

Constraints enforced:
- base64 validation
- max part size
- empty payload rejection

---

## 4) Streaming & Special Paths

- [x] `/v1/responses:stream` reachable directly
- [x] Encoded `:` paths handled
- [x] Streaming explicitly excluded from proxy

---

## 5) Proxy Allowlist Hygiene

- [x] Explicit allowlist only
- [x] No wildcard leakage
- [x] Binary `/content` paths blocked
- [x] Legacy and meta routes excluded

Bucket posture:
- `PROXY_HARNESS`: stable
- `WRAPPER_*`: explicit only
- `EXCLUDE_*`: enforced

---

## 6) Integration Test Suite (Authoritative)

Execution:
```bash
export RELAY_BASE_URL=http://127.0.0.1:8000
pytest -q -m integration
```

Result:
- **100% PASS**
- Executed against live uvicorn (not TestClient)

Coverage:
- uploads
- files
- batches
- images
- proxy guard
- SSE

---

## Status Summary

- OpenAPI generation stable
- Actions schema contract-safe
- Uploads and videos normalized
- Proxy boundaries enforced
- Integration tests green

**Status:** COMPLETE

---

## Bottom-Line Policy (Canonical)

**Proxy = control plane**
- JSON-only
- Allowlisted
- Deterministic

**Wrappers = data plane**
- Multipart, uploads, images, videos handled explicitly

**Actions surface stays small**
- Stable, synchronous HTTP only

**Binary and streaming are opt-in**
- Never exposed implicitly through proxy

**Passing tests > theoretical completeness**

---

## Analogy

The relay behaves like a kernel and drivers:
- Proxy = kernel (minimal, safe, opinionated)
- Wrappers = drivers (explicit adapters for complex I/O)

Nothing crosses that boundary accidentally.


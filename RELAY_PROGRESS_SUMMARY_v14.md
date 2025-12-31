# Relay Progress Summary v14 (as of 2025-12-31)

## Current posture (BIFL)

The relay remains intentionally **hybrid**:
- **Proxy**: minimal, explicit allowlist, JSON-safe, deny-by-default.
- **Wrappers**: used for high-risk operations (multipart, resumable uploads, streaming, video multipart).
- **Actions OpenAPI**: curated subset that exposes only intentional REST capabilities.
- **Guardrails**: coverage must classify every route; integration tests must remain green on Local + Render.

---

## Current state (Green with one guardrail item)

### Test status
- ✅ Local integration (live uvicorn): `pytest -q -m integration` — **PASS**
- ✅ Local/Render script suites remain green per prior baseline (v13)

### Actions OpenAPI
- ✅ `/openapi.actions.json` loads and is stable
- ✅ No duplicate `operationId` detected in Actions schema
- ✅ Actions surface includes:
  - `health`, `models`
  - `responses` + `responses/compact`
  - `embeddings`
  - `images` + Actions JSON wrappers
  - `uploads` Actions wrappers
  - `files` Actions upload wrapper
  - `videos` Actions wrappers
  - `realtime/sessions`

### Functional surfaces verified (by integration suite)
- ✅ Resumable uploads: create/parts/complete/cancel
- ✅ Files: multipart upload via Actions wrapper; metadata via proxy/direct
- ✅ Batches: create + poll
- ✅ Proxy policy: deny multipart/binary/streaming/wildcard; allowlist intact
- ✅ SSE wrapper present and does not expand proxy surface

---

## What changed since v13

1. **Streaming wrapper added**
   - `POST /v1/responses:stream` (SSE)
   - `POST /v1/actions/responses/stream` (Actions wrapper)

2. **Realtime capabilities added**
   - `POST /v1/realtime/sessions` (Actions-visible)
   - `WS /v1/realtime/ws` (non-Actions)
   - Local-only helpers (`/validate`, `/introspect`) introduced for debugging

3. **Videos surfaced cleanly**
   - Canonical `/v1/videos` routes present
   - Actions wrappers added, including a JSON→multipart helper for generations

---

## Known issue (must resolve)

### Coverage guardrail: one UNKNOWN on Render
- `GET /actions/system/info` is surfaced in `openapi.json` but is not bucketed.
- This breaks the “no UNKNOWN endpoints” invariant.

Recommended resolution (lowest risk):
- Classify it as an explicit exclusion bucket (treat it as **legacy/non-v1 meta**).

Acceptance criteria:
- `./scripts/coverage_report.sh` returns **0 UNKNOWN** for:
  - Local uvicorn
  - Render deployment

---

## Next plan (incremental, low-refactor)

### Phase 1 — Restore guardrail invariants
1. Bucket `/actions/system/info` explicitly (EXCLUDE_LEGACY or new EXCLUDE_META_NONV1)
2. Re-run coverage report against Render and local
3. Add/adjust a minimal test that asserts this endpoint is excluded (if desired)

### Phase 2 — Realtime stabilization
1. Add a small integration smoke for `POST /v1/realtime/sessions`
2. Add a non-Actions WS smoke test for `/v1/realtime/ws` (optional; can be skipped in CI if env lacks WS reachability)
3. Ensure local-only helper endpoints remain excluded from proxy and Actions schema

### Phase 3 — Video generations hardening
1. Add focused tests for `/v1/actions/videos/generations`:
   - invalid base64
   - empty bytes
   - >max bytes
   - frames/duration exceeding limits
2. Confirm header filtering is correct (no hop-by-hop headers)

### Phase 4 — SSE regression coverage
1. Basic stream-open test ensuring `text/event-stream` and chunk pass-through
2. Confirm proxy continues to deny colon paths

---

## Quick commands

```bash
# local live integration
export RELAY_BASE_URL=http://127.0.0.1:8000
pytest -q -m integration

# local coverage
./scripts/coverage_report.sh

# render coverage
RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com ./scripts/coverage_report.sh
```

# Relay Progress Summary v13 (as of 2025-12-31)

## Bottom-line policy (BIFL)

**Hybrid model is the long-term stable posture:**
- **Proxy** remains minimal and audited (explicit allowlist; JSON-safe; deny by default).
- **Wrappers** implement high-risk/complex operations (multipart, resumable uploads, streaming, binary retrieval).
- **Actions schema** exposes only intentional capabilities (no accidental surface expansion).
- **Guardrails**: coverage must classify every endpoint (no `UNKNOWN`), and tests must remain green on Local + Render.

---

## Current State (Green)

### Test status
- ✅ Local test runner: `scripts/test_local.sh` — **16/16 passed**
- ✅ Render test runner: `scripts/test_render.sh` — **16/16 passed**
- ✅ Live-server verification: `pytest -q -m integration` against local uvicorn — **PASS**

### Coverage mapping
- ✅ `scripts/coverage_report.sh` produces **no UNKNOWN** buckets on both:
  - Local uvicorn (`http://127.0.0.1:8000`)
  - Render (`https://chatgpt-team-relay.onrender.com`)

### Proxy correctness
- ✅ Runtime verified via `/v1/proxy`:
  - `GET /v1/files/{file_id}` works for file metadata
  - `DELETE /v1/files/{file_id}` works
- ✅ Proxy allowlist hygiene:
  - deduplicated file allowlist entries (GET/DELETE file-id regex)
- ✅ Static coverage correctness:
  - OpenAPI templated paths (`{file_id}` etc.) are instantiated for allowlist evaluation, eliminating false positives.

---

## What changed since v12

1) **Coverage-report correctness and durability**
   - Eliminated templated-path vs regex mismatch (static false negatives).
   - Added explicit classification for newly surfaced `/v1/actions/uploads*` and `/v1/actions/videos` endpoints so the guardrail remains stable (no UNKNOWN).

2) **Proxy allowlist hygiene**
   - Removed duplicated allowlist entries for `/v1/files/[A-Za-z0-9_-]+` (GET/DELETE).

3) **Live-server confidence**
   - Ran integration tests against a live uvicorn instance using `RELAY_BASE_URL=http://127.0.0.1:8000`.

---

## Remaining Risks (operational, not test failures)

1) **Environment mismatch**
   - Mixing Local/Render base URL or token across shells can still cause 401/403 confusion.

2) **Upstream API drift**
   - OpenAI route behavior and schemas may change; periodic contract checks help.

3) **Batch latency variance**
   - Batch completion time is non-deterministic; polling and timeouts should remain configurable.

4) **OpenAPI hygiene**
   - Ensure `operationId` uniqueness end-to-end; FastAPI can warn on duplicate operation IDs if routes are registered twice.

---

## Next agenda (recommended order)

1) **CI enforcement**
   - Add GitHub Actions workflow running local integration suite on PRs.
   - Keep Render checks as a manual “release gate” using secrets.

2) **Documentation consolidation**
   - One authoritative “How to test” section in README mirroring `scripts/test_local.sh` and `scripts/test_render.sh`.
   - Document pitfalls: base URL, token, upstream gating flag.

3) **Contract + regression hardening**
   - Validate:
     - OpenAPI operation ID uniqueness
     - Key response shapes for `/v1/models`, `/v1/responses`, `/v1/uploads`, `/v1/files`, `/v1/batches`
   - Fail fast on unexpected compression/encoding headers for JSON endpoints.

4) **Production observability**
   - Structured logs for request ID propagation and upstream latency buckets.
   - Basic metrics (2xx/4xx/5xx by route family).

---

## Quick commands
- Local: `scripts/test_local.sh`
- Render: `scripts/test_render.sh`
- Coverage: `./scripts/coverage_report.sh`

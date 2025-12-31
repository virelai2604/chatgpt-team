# Relay Checklist v17 (as of 2025-12-31)

This checklist tracks **functional gates**, **route-family smoke tests**, and **exposure policy** for the ChatGPT Team Relay, across:
- **Local**: `http://localhost:8000` (uvicorn)
- **Render**: `https://chatgpt-team-relay.onrender.com`

Primary one-command runners:
- Local: `scripts/test_local.sh`
- Render: `scripts/test_render.sh`

---

## Bottom-line policy (BIFL)

**Hybrid, minimal surface area:**
1) **Proxy** stays **small and audited** (JSON-safe endpoints only; explicit allowlist; deny by default).
2) **Wrappers** handle **high-risk or complex** capabilities:
   - multipart uploads (files, videos)
   - resumable uploads (`/v1/uploads*`)
   - streaming (SSE)
   - binary content (`/content`) only if explicitly required and hardened
3) **Actions schema (`openapi.actions.json`) exposes only intentional capabilities.**
4) **No drift allowed:** coverage must classify every endpoint (no `UNKNOWN`), and tests must remain green locally and on Render.

---

## 0) Environment sanity

### Local (uvicorn)
- [ ] Start the relay: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- [ ] Ensure `RELAY_BASE_URL` is **unset** (tests default to `http://localhost:8000`) or set explicitly:
  - [ ] `export RELAY_BASE_URL=http://127.0.0.1:8000`
- [ ] Export auth values that match your local relay config:
  - [ ] `export RELAY_TOKEN=<local_relay_token>`
  - [ ] `export RELAY_KEY=<local_relay_token>`
- [ ] Enable upstream-dependent smokes (only a gate flag for tests):
  - [ ] `export INTEGRATION_OPENAI_API_KEY=1`

### Render
- [ ] `export RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com`
- [ ] Export the Render relay key/token (must match server configuration):
  - [ ] `export RELAY_TOKEN=<render_relay_token>`
  - [ ] `export RELAY_KEY=<render_relay_token>`
- [ ] Enable upstream-dependent smokes (only a gate flag for tests):
  - [ ] `export INTEGRATION_OPENAI_API_KEY=1`

### Quick smoke probes
- [ ] `GET /v1/actions/ping` returns **200**
- [ ] `POST /v1/proxy` with `{"method":"GET","path":"/v1/evals"}` returns **403 or 404** (blocked; must not be 5xx)

---

## 1) Gate suite: `tests/test_success_gates_integration.py`

Expected gates:
- Gate A: Uploads E2E (create, part upload, complete, cancel)
- Gate B: SSE smoke (`/v1/responses:stream`)
- Gate C: OpenAPI has no duplicate operation IDs
- Gate D: Containers/Videos content endpoints do not 5xx

Status:
- Local: ✅ PASS
- Render: ✅ PASS

**Operational note (hard requirement):**
- [ ] Verify **no OpenAPI duplicate `operationId` warnings** when running the app (FastAPI may warn at startup).

---

## 2) Extended route families: `tests/test_extended_routes_smoke_integration.py`

Coverage (smoke-level; “no 5xx” and basic wiring):
- OpenAPI route families present
- `/v1/actions/ping`, `/v1/actions/relay_info`
- `/v1/proxy` blocklist + allowlist (`/v1/models` allowlisted)
- `/v1/images/generations` wiring
- `/v1/vector_stores` list wiring
- `/v1/conversations` list wiring
- `/v1/realtime/sessions` create wiring

Status:
- Local: ✅ PASS
- Render: ✅ PASS

---

## 3) Remaining route families smoke: `tests/test_remaining_routes_smoke_integration.py`

Coverage:
- Consolidated smoke across remaining route families (expects non-5xx and reasonable 4xx where applicable)

Status:
- Local: ✅ PASS
- Render: ✅ PASS

---

## 4) Files + batches integration: `tests/test_files_and_batches_integration.py`

Goals:
- Proxy blocks `/v1/evals` and fine-tuning endpoints (blocked; expected 4xx/404)
- `purpose=user_data` file **download is blocked** (privacy guardrail; expected 4xx)
- Batch output file download succeeds once batch completes

Status:
- Local: ✅ PASS
- Render: ✅ PASS

---

## 5) Coverage mapping guardrail: `scripts/coverage_report.sh`

Hard requirement:
- [ ] `./scripts/coverage_report.sh` must print **no UNKNOWN buckets** (exit code 0)
- [ ] Any new endpoint must be explicitly classified:
  - ACTIONS_DIRECT (in `openapi.actions.json`)
  - PROXY_HARNESS (allowlisted by proxy)
  - WRAPPER_* (explicit wrapper policy)
  - EXCLUDE_* (explicit exclusion policy)

Status:
- Local: ✅ PASS (no UNKNOWN)
- Render: ✅ PASS (no UNKNOWN)

---

## 6) Running pytest against uvicorn (live server)

- [ ] Terminal A: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`
- [ ] Terminal B:
  - [ ] `export RELAY_BASE_URL=http://127.0.0.1:8000`
  - [ ] `pytest -q -m integration`
  - [ ] `pytest -q tests/test_local_e2e.py`

Status:
- Local (uvicorn): ✅ PASS

---

## 7) Post-green hardening (recommended next steps)
- [ ] Add CI: run the **local** integration suite in GitHub Actions (Render tests as a manual job using secrets)
- [ ] Add a “preflight” in both scripts that prints effective `RELAY_BASE_URL` and whether a token is present (without printing secrets)
- [ ] Add a lightweight “contract drift” check: validate OpenAPI operation IDs and key route schemas on every merge
- [ ] Document: one canonical “Local vs Render” workflow in README (including common failure modes)

# Relay Checklist v15 (as of 2025-12-24)

This checklist tracks **functional gates** and **route-family smoke tests** for the ChatGPT Team Relay, across:
- **Local**: `http://localhost:8000` (uvicorn)
- **Render**: `https://chatgpt-team-relay.onrender.com`

## 0) Environment sanity

### Local (uvicorn)
- [ ] `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- [ ] `unset RELAY_BASE_URL` (tests default to `http://localhost:8000`)
- [ ] `export RELAY_KEY=dummy` and `export RELAY_TOKEN=dummy` (must match local relay config)
- [ ] `export INTEGRATION_OPENAI_API_KEY=1` (enables upstream-proxy smoke tests)

### Render
- [ ] `export RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com`
- [ ] `export RELAY_KEY=<render_relay_key>` and `export RELAY_TOKEN=<render_relay_key>`
- [ ] `export INTEGRATION_OPENAI_API_KEY=1`

**Quick ping checks**
- [ ] `GET /v1/actions/ping` returns 200
- [ ] `POST /v1/proxy` with `{"method":"GET","path":"/v1/evals"}` returns 403/404 (blocked locally, not 5xx)

## 1) Gate suite: `tests/test_success_gates_integration.py` (4 tests)

Expected gates:
- Gate A: Uploads E2E (create, part upload, complete, cancel)
- Gate B: SSE smoke (`/v1/responses:stream`)
- Gate C: OpenAPI has no duplicate operation IDs
- Gate D: Containers/Videos content endpoints do not 5xx

Status:
- Local: ✅ PASS (4/4) — confirmed in prior run logs.
- Render: ✅ PASS (4/4) — confirmed in prior run logs (requires valid relay key).

## 2) Extended route families: `tests/test_extended_routes_smoke_integration.py` (8 tests)

Coverage:
- `/openapi.json` route families present
- `/v1/actions/ping`, `/v1/actions/relay_info`
- `/v1/proxy` blocklist + allowlist
- `/v1/images/generations` wiring (no 5xx)
- `/v1/vector_stores` list (no 5xx)
- `/v1/conversations` list (no 5xx)
- `/v1/realtime/sessions` create (no 5xx)

Status:
- Local: ✅ PASS (8/8)
- Render: ✅ PASS (8/8) **when `RELAY_TOKEN/RELAY_KEY` matches Render’s configured relay key** (otherwise 401 “Invalid relay key”).

## 3) Remaining route families smoke: `tests/test_remaining_routes_smoke_integration.py` (8 tests)

Coverage (no-5xx wiring checks, primarily):
- Assistants, Threads, Runs
- Audio, Moderations
- Responses (non-stream)
- Fine-tuning (expected blocked/404/4xx, but no 5xx)
- Tools manifest

Status:
- Local: ✅ PASS (8/8)
- Render: ⏳ TODO (run the same test file against Render after confirming key)

## 4) Files + batches integration: `tests/test_files_and_batches_integration.py` (3 tests)

Goal:
- Proxy blocks `/v1/evals` and fine-tune endpoints
- User-data file download is forbidden
- Batch output file (once batch completes) is downloadable

Status:
- Local: ❌ FAILING due to **pytest-asyncio STRICT async fixture misconfiguration** (“async_generator has no attribute request”).
- Render: ❌ same root cause if test file/fixture is unchanged.

Fix checklist:
- [ ] Ensure the `client` async fixture uses `@pytest_asyncio.fixture` (not `@pytest.fixture`) under `asyncio_mode=strict`
- [ ] Re-run `pytest -m integration -vv tests/test_files_and_batches_integration.py`

## 5) Full integration suite (`pytest -m integration -vv`)

Target state:
- ✅ All integration tests pass locally
- ✅ All integration tests pass against Render

Current blockers:
- [ ] Fix `tests/test_files_and_batches_integration.py` async fixture handling (Section 4)

## 6) Optional hardening (post-green)
- [ ] Add a `make test:local` and `make test:render` wrapper to prevent RELAY_BASE_URL/key mixups
- [ ] Add a startup log that prints effective `RELAY_AUTH_HEADER` and whether auth is enabled (without printing secret)
- [ ] Document “local vs render” testing steps in README


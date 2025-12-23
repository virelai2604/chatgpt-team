# ChatGPT Team Relay — Checklist v14 (2025-12-23)

This checklist is the “single pane of glass” for validating the relay locally and in the deployed Render environment.

---

## Status snapshot (as of 2025-12-23)

### Environments validated

- **Local dev** (default `http://localhost:8000`):
  - ✅ PASS — `pytest -m integration -vv tests/test_success_gates_integration.py`
  - ✅ PASS — `pytest -m integration -vv tests/test_extended_routes_smoke_integration.py`
- **Deployed relay** (`https://chatgpt-team-relay.onrender.com`):
  - ✅ PASS — `pytest -m integration -vv tests/test_success_gates_integration.py` (requires valid Render relay token)
  - ⚠️ PARTIAL — `pytest -m integration -vv tests/test_extended_routes_smoke_integration.py`
    - Public routes pass (OpenAPI, actions ping/info, etc.)
    - `/v1/proxy` tests will return **401** if `RELAY_TOKEN` is not the real Render relay token

### Success gates (tests/test_success_gates_integration.py)

- Gate A — Uploads API happy path + cancel path: ✅ PASS (local + Render)
- Gate B — SSE `/v1/responses:stream` smoke: ✅ PASS (local + Render)
- Gate C — OpenAPI has no duplicate operation IDs: ✅ PASS (local + Render)
- Gate D — containers/videos content endpoints do not produce relay 5xx: ✅ PASS (local + Render)

### Extended smokes (tests/test_extended_routes_smoke_integration.py)

- OpenAPI includes route families: ✅ PASS (local + Render)
- Actions ping + relay-info: ✅ PASS (local + Render)
- Images generations wiring (no 5xx): ✅ PASS (local + Render)
- Vector stores list (no 5xx): ✅ PASS (local + Render)
- Conversations list (no 5xx): ✅ PASS (local + Render)
- Realtime sessions create (no 5xx): ✅ PASS (local + Render)
- Proxy blocklist + allowlist:
  - ✅ PASS locally
  - ⚠️ Requires correct `RELAY_TOKEN` on Render; otherwise expected 401 “Invalid relay key”

### Next validation tranche (pending)

- ✅ Fix `tests/test_relay_auth_guard.py` so pytest collection does not error (file must be valid Python).
- ▶️ Add & run “remaining routes” smoke tests:
  - `tests/test_remaining_routes_smoke_integration.py` (files, batches, embeddings, non-stream responses, containers/videos roots)

---

## Runbook (local vs deployed)

### Footgun guard: always print target base URL before running tests

```bash
python -c "import os; print(os.environ.get('RELAY_BASE_URL','http://localhost:8000'))"

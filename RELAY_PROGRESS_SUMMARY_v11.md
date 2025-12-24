# Relay Progress Summary v11 (as of 2025-12-24)

## Completed
- ✅ **Remaining routes smoke suite**: `tests/test_remaining_routes_smoke_integration.py` runs clean locally (8/8).
- ✅ **Render sanity**: `/v1/actions/ping` and local proxy blocklist behavior validated (403 for `/v1/evals` via `/v1/proxy`).

## Current State
- Most route families are wired and return non-5xx responses for smoke checks.
- Gate + extended suites are stable provided **RELAY_BASE_URL and relay key are set consistently**.

## Open Issues / Next Work
1) **Fix `tests/test_files_and_batches_integration.py` async fixture issue (STRICT mode)**
   - Symptoms: `AttributeError: 'async_generator' object has no attribute 'request'`
   - Expected outcome: 3/3 tests pass.

2) **Run the remaining routes smoke suite against Render**
   - Command: `pytest -m integration -vv tests/test_remaining_routes_smoke_integration.py` with `RELAY_BASE_URL` pointing at Render.

3) **Run full integration suite in both modes**
   - Local: `unset RELAY_BASE_URL` then `pytest -m integration -vv`
   - Render: `export RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com` then `pytest -m integration -vv`

## Known Pitfalls (do these checks first)
- 401 “Invalid relay key” means **the token/key doesn’t match the server** (especially common when switching between Local and Render shells).
- Connection errors to `localhost:8000` usually mean either:
  - uvicorn isn’t running, or
  - `RELAY_BASE_URL` wasn’t exported in the shell that invoked pytest.

"""
Smokes for core route families not covered by the success-gates and extended-route tests.

Design goals
- Fast (< ~5s typically)
- No expensive object creation (no batches/threads/etc.)
- Validate that endpoints are wired and never crash the relay (no 5xx)

These tests are safe to run against:
- Local relay (default http://localhost:8000)
- Deployed relay (set RELAY_BASE_URL)

Auth
- Sends both Authorization: Bearer <token> and X-Relay-Key: <token> for compatibility.

Upstream opt-in
- Any tests that might touch upstream endpoints are gated behind INTEGRATION_OPENAI_API_KEY.
  Set it to any non-empty value (e.g. 1) to enable.
"""

from __future__ import annotations

import os

import pytest
import requests


RELAY_BASE_URL = (os.environ.get("RELAY_BASE_URL") or "http://localhost:8000").rstrip("/")
DEFAULT_TIMEOUT_S = float(os.environ.get("DEFAULT_TIMEOUT_S", "30"))
INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"


def _relay_token() -> str:
    # Accept either name; many shells/export patterns vary.
    return os.environ.get("RELAY_TOKEN") or os.environ.get("RELAY_KEY") or "dummy"


def _auth_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    token = _relay_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Relay-Key": token,
    }
    if extra:
        headers.update(extra)
    return headers


def _skip_if_no_upstream_opt_in() -> None:
    if not (os.environ.get(INTEGRATION_ENV_VAR) or "").strip():
        pytest.skip(f"{INTEGRATION_ENV_VAR} not set; skipping upstream-touching smoke checks.")


def _assert_not_5xx(r: requests.Response, *, label: str) -> None:
    assert r.status_code < 500, f"{label} returned {r.status_code} (expected <500). Body: {r.text[:800]}"


@pytest.mark.integration
def test_health_endpoints_smoke() -> None:
    """
    Health endpoints are local and should always be 200 + JSON.
    """
    for path in ("/health", "/v1/health"):
        r = requests.get(f"{RELAY_BASE_URL}{path}", headers=_auth_headers(), timeout=DEFAULT_TIMEOUT_S)
        assert r.status_code == 200, f"{path} returned {r.status_code}. Body: {r.text[:400]}"
        assert "application/json" in (r.headers.get("Content-Type") or "")
        body = r.json()
        assert isinstance(body, dict)
        assert body.get("status") == "ok"


@pytest.mark.integration
def test_manifest_endpoints_smoke() -> None:
    """
    Manifest endpoints are local and should always be 200 + JSON.

    We validate that the returned schema includes the endpoints used by tooling.
    """
    for path in ("/manifest", "/v1/manifest"):
        r = requests.get(f"{RELAY_BASE_URL}{path}", headers=_auth_headers(), timeout=DEFAULT_TIMEOUT_S)
        assert r.status_code == 200, f"{path} returned {r.status_code}. Body: {r.text[:400]}"
        assert "application/json" in (r.headers.get("Content-Type") or "")
        body = r.json()
        assert isinstance(body, dict)
        endpoints = body.get("endpoints")
        assert isinstance(endpoints, dict), f"{path} missing endpoints map"
        assert "responses" in endpoints, f"{path} missing endpoints.responses"
        assert "responses_compact" in endpoints, f"{path} missing endpoints.responses_compact"


@pytest.mark.integration
def test_models_list_and_retrieve_smoke() -> None:
    """
    /v1/models is implemented locally by the relay (and should not be 5xx).
    """
    r = requests.get(f"{RELAY_BASE_URL}/v1/models", headers=_auth_headers(), timeout=DEFAULT_TIMEOUT_S)
    assert r.status_code == 200, f"/v1/models returned {r.status_code}. Body: {r.text[:400]}"
    assert "application/json" in (r.headers.get("Content-Type") or "")
    body = r.json()
    assert isinstance(body, dict)
    assert body.get("object") == "list"

    data = body.get("data")
    assert isinstance(data, list)
    if not data:
        pytest.skip("No models returned by relay; skipping retrieve smoke.")
    model_id = data[0].get("id")
    assert isinstance(model_id, str) and model_id

    r2 = requests.get(f"{RELAY_BASE_URL}/v1/models/{model_id}", headers=_auth_headers(), timeout=DEFAULT_TIMEOUT_S)
    assert r2.status_code == 200, f"/v1/models/{model_id} returned {r2.status_code}. Body: {r2.text[:400]}"
    assert "application/json" in (r2.headers.get("Content-Type") or "")
    body2 = r2.json()
    assert isinstance(body2, dict)
    assert body2.get("id") == model_id


@pytest.mark.integration
def test_files_list_no_5xx() -> None:
    """
    /v1/files is upstream-facing. We only require it does not crash the relay.

    We do not create files here (that’s covered by deeper integration tests).
    """
    _skip_if_no_upstream_opt_in()
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/files?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _assert_not_5xx(r, label="files list")
    if "application/json" in (r.headers.get("Content-Type") or ""):
        body = r.json()
        assert isinstance(body, dict)


@pytest.mark.integration
def test_batches_list_no_5xx() -> None:
    """
    /v1/batches is upstream-facing. We only require it does not crash the relay.

    We do not create batches here (that’s covered by deeper integration tests).
    """
    _skip_if_no_upstream_opt_in()
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/batches?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _assert_not_5xx(r, label="batches list")
    if "application/json" in (r.headers.get("Content-Type") or ""):
        body = r.json()
        assert isinstance(body, dict)


@pytest.mark.integration
def test_files_content_dummy_id_no_5xx() -> None:
    """
    Dummy-id content download smoke:
    - Validates the route exists and does not 5xx.
    - Also exercises the relay’s content handling behavior (binary-safe).
    """
    _skip_if_no_upstream_opt_in()
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/files/file_dummy/content",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _assert_not_5xx(r, label="files content dummy")


@pytest.mark.integration
def test_batches_cancel_dummy_id_no_5xx() -> None:
    """
    Dummy-id cancel smoke:
    - Ensures endpoint is routed and handled cleanly (likely 404/400 from upstream).
    """
    _skip_if_no_upstream_opt_in()
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/batches/batch_dummy/cancel",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _assert_not_5xx(r, label="batches cancel dummy")


@pytest.mark.integration
def test_unknown_v1_path_no_5xx() -> None:
    """
    Unknown /v1 path should not crash the relay (should be 404, 400, etc.; never 5xx).
    """
    r = requests.get(
        f"{RELAY_BASE_URL}/v1/this_route_should_not_exist",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    _assert_not_5xx(r, label="unknown v1 path")

"""Extended route smoke tests (integration).

These tests intentionally focus on *wiring* and *non-5xx* behavior for
route families that are not covered by the success gates.

They are safe to run against:
  - Local relay: http://localhost:8000 (default)
  - Remote relay: set RELAY_BASE_URL=https://chatgpt-team-relay.onrender.com

Many routes proxy to OpenAI. To avoid false failures on machines where the
relay is not configured with an upstream key, tests that may call OpenAI are
skipped unless INTEGRATION_OPENAI_API_KEY=1.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable

import pytest
import requests


RELAY_BASE_URL = os.getenv("RELAY_BASE_URL", "http://localhost:8000").rstrip("/")

# NOTE: The server uses RELAY_KEY, but existing integration tests sometimes use RELAY_TOKEN.
# We accept either to reduce operator friction.
RELAY_TOKEN = (
    os.getenv("RELAY_TOKEN")
    or os.getenv("RELAY_KEY")
    or os.getenv("RELAY_AUTH_TOKEN")
    or "dummy"
)

DEFAULT_TIMEOUT_S = float(os.getenv("RELAY_TEST_TIMEOUT_S", "30"))
INTEGRATION_ENV_VAR = "INTEGRATION_OPENAI_API_KEY"


def _auth_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    headers = {"Authorization": f"Bearer {RELAY_TOKEN}"}
    if extra:
        headers.update(extra)
    return headers


def _skip_if_no_real_key() -> None:
    """Skip tests that may call upstream OpenAI unless explicitly enabled."""

    if os.getenv(INTEGRATION_ENV_VAR, "").strip() != "1":
        pytest.skip(f"Set {INTEGRATION_ENV_VAR}=1 to run upstream-proxy smoke tests")


def _get_openapi() -> Dict[str, Any]:
    r = requests.get(
        f"{RELAY_BASE_URL}/openapi.json",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code == 200, f"openapi.json returned {r.status_code}: {r.text[:400]}"
    return r.json()


def _path_exists(openapi: Dict[str, Any], path: str) -> bool:
    return path in (openapi.get("paths") or {})


def _pick_first_existing(openapi: Dict[str, Any], candidates: Iterable[str]) -> str:
    for p in candidates:
        if _path_exists(openapi, p):
            return p
    raise AssertionError(f"None of the candidate paths exist in openapi: {list(candidates)}")


@pytest.mark.integration
def test_openapi_includes_extended_route_families() -> None:
    """Validate route registration (schema), independent of upstream."""

    spec = _get_openapi()
    paths = spec.get("paths") or {}
    assert isinstance(paths, dict) and paths, "openapi.json has no paths"

    # Actions
    assert (
        "/v1/actions/ping" in paths or "/actions/ping" in paths
    ), "Missing actions ping route"
    assert (
        "/v1/actions/relay_info" in paths or "/actions/relay_info" in paths
    ), "Missing actions relay_info route"

    # Proxy
    assert "/v1/proxy" in paths, "Missing /v1/proxy route"

    # Images
    assert "/v1/images/generations" in paths, "Missing /v1/images/generations route"

    # Vector stores
    assert "/v1/vector_stores" in paths, "Missing /v1/vector_stores route"

    # Conversations
    assert "/v1/conversations" in paths, "Missing /v1/conversations route"

    # Realtime sessions (REST). WebSocket path may not appear in schema.
    assert "/v1/realtime/sessions" in paths, "Missing /v1/realtime/sessions route"


@pytest.mark.integration
def test_actions_ping_and_relay_info_smoke() -> None:
    """Actions endpoints should be purely local and return JSON."""

    spec = _get_openapi()

    ping_path = _pick_first_existing(spec, ["/v1/actions/ping", "/actions/ping"])
    r = requests.get(
        f"{RELAY_BASE_URL}{ping_path}",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code == 200, f"{ping_path} returned {r.status_code}: {r.text[:400]}"
    assert "application/json" in (r.headers.get("Content-Type") or "")
    body = r.json()
    assert isinstance(body, dict)

    info_path = _pick_first_existing(spec, ["/v1/actions/relay_info", "/actions/relay_info"])
    r = requests.get(
        f"{RELAY_BASE_URL}{info_path}",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code == 200, f"{info_path} returned {r.status_code}: {r.text[:400]}"
    assert "application/json" in (r.headers.get("Content-Type") or "")
    body = r.json()
    assert isinstance(body, dict)


@pytest.mark.integration
def test_proxy_blocklist_smoke() -> None:
    """Proxy should block high-risk endpoints locally (no upstream required)."""

    payload = {"method": "GET", "path": "/v1/evals"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    # Either 403 from relay (preferred) or 404 if upstream ever changes; must not be 5xx.
    assert r.status_code < 500, f"proxy blocklist returned {r.status_code}: {r.text[:400]}"
    assert r.status_code in (403, 404), f"Unexpected proxy blocklist status: {r.status_code}"


@pytest.mark.integration
def test_proxy_allowlist_models_smoke() -> None:
    """Proxy allowlist should permit /v1/models and return JSON from upstream."""

    _skip_if_no_real_key()

    payload = {"method": "GET", "path": "/v1/models"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/proxy",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"proxy /v1/models returned {r.status_code}: {r.text[:400]}"
    # Upstream should return JSON list.
    assert "application/json" in (r.headers.get("Content-Type") or "")
    body = r.json()
    assert isinstance(body, dict)
    assert body.get("object") == "list", f"Unexpected /v1/models object: {body.get('object')}"


@pytest.mark.integration
def test_images_generations_wiring_no_5xx() -> None:
    """Images generations endpoint should never produce a relay 5xx due to wiring."""

    _skip_if_no_real_key()

    # Use an intentionally invalid model to avoid any billable work; wiring is the goal.
    payload = {"model": "__invalid_model__", "prompt": "ping"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/images/generations",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"images generations returned {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
def test_vector_stores_list_no_5xx() -> None:
    """Vector stores list should route and never 5xx due to relay wiring."""

    _skip_if_no_real_key()

    r = requests.get(
        f"{RELAY_BASE_URL}/v1/vector_stores?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"vector_stores list returned {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
def test_conversations_list_no_5xx() -> None:
    """Conversations list should route and never 5xx due to relay wiring."""

    _skip_if_no_real_key()

    r = requests.get(
        f"{RELAY_BASE_URL}/v1/conversations?limit=1",
        headers=_auth_headers(),
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"conversations list returned {r.status_code}: {r.text[:400]}"


@pytest.mark.integration
def test_realtime_sessions_create_no_5xx() -> None:
    """Realtime sessions should route; we only gate on non-5xx."""

    _skip_if_no_real_key()

    payload = {"model": "gpt-4.1-mini"}
    r = requests.post(
        f"{RELAY_BASE_URL}/v1/realtime/sessions",
        headers=_auth_headers({"Content-Type": "application/json"}),
        json=payload,
        timeout=DEFAULT_TIMEOUT_S,
    )
    assert r.status_code < 500, f"realtime sessions returned {r.status_code}: {r.text[:400]}"

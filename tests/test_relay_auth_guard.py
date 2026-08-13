# tests/test_relay_auth_guard.py
"""Relay auth middleware guardrails.

Why this exists
---------------
We must ensure that when RELAY_AUTH_ENABLED is turned on:

- public endpoints remain reachable without a relay key (e.g. /health)
- /v1/* endpoints require a valid relay key
- both supported auth mechanisms work:
    - Authorization: Bearer <key>
    - X-Relay-Key: <key>

This is intentionally an in-process (FastAPI TestClient) unit test so it:
- runs fast
- does not require an OpenAI API key (we test a local endpoint: /v1/models)
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

pytestmark = pytest.mark.unit


def test_relay_auth_allows_health_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    # Enable relay auth for this test only.
    monkeypatch.setattr(settings, "RELAY_AUTH_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "RELAY_KEY", "secret-relay-key", raising=False)

    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)

        # Health contract in this repo is {"status":"ok", ...}
        assert body.get("status") == "ok"
        assert "timestamp" in body


def test_relay_auth_requires_valid_key_for_v1_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "RELAY_AUTH_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "RELAY_KEY", "secret-relay-key", raising=False)

    with TestClient(app) as client:
        # No Authorization and no X-Relay-Key => 401
        r = client.get("/v1/models")
        assert r.status_code == 401
        assert r.json().get("detail") == "Missing relay key"

        # Authorization present but not Bearer => 401
        r = client.get("/v1/models", headers={"Authorization": "Token secret-relay-key"})
        assert r.status_code == 401
        assert "Bearer" in (r.json().get("detail") or "")

        # Wrong relay key => 401
        r = client.get("/v1/models", headers={"Authorization": "Bearer wrong-key"})
        assert r.status_code == 401
        assert r.json().get("detail") == "Invalid relay key"

        # Correct relay key via Authorization => 200
        r = client.get("/v1/models", headers={"Authorization": "Bearer secret-relay-key"})
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)
        assert body.get("object") == "list"
        assert isinstance(body.get("data"), list)

        # Correct relay key via X-Relay-Key => 200
        r = client.get("/v1/models", headers={"X-Relay-Key": "secret-relay-key"})
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body, dict)
        assert body.get("object") == "list"


def test_relay_auth_uses_constant_time_comparison() -> None:
    """The key check must not short-circuit on the first differing byte.

    A plain `!=` leaks the key one character at a time to a timing attack. This
    asserts the implementation, not the timing — timing tests are flaky in CI.
    """
    import inspect

    from app.middleware import relay_auth

    src = inspect.getsource(relay_auth.RelayAuthMiddleware.dispatch)
    assert "compare_digest" in src, "relay key comparison must use hmac.compare_digest"


def test_relay_auth_misconfiguration_is_a_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Auth on with no key configured is a server fault, not a client one.

    Returning 401 here would tell every caller their key is wrong when in fact
    the deployment is broken.
    """
    monkeypatch.setattr(settings, "RELAY_AUTH_ENABLED", True, raising=False)
    monkeypatch.setattr(settings, "RELAY_KEY", "", raising=False)

    with TestClient(app) as client:
        r = client.get("/v1/models", headers={"X-Relay-Key": "anything"})
        assert r.status_code == 500
        assert "misconfigured" in (r.json().get("detail") or "").lower()

        # Public paths stay reachable even when auth is misconfigured.
        assert client.get("/health").status_code == 200

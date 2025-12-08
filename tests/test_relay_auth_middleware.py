from __future__ import annotations

from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core import config
from app import main


def build_app(monkeypatch, *, relay_enabled: bool, relay_key: str = "test-key"):
    # Toggle relay auth explicitly for this app instance.
    monkeypatch.setattr(config.settings, "RELAY_AUTH_ENABLED", relay_enabled)
    monkeypatch.setattr(config.settings, "RELAY_KEY", relay_key)
    app = main.create_app()

    @app.get("/v1/protected")
    async def protected():
        return {"status": "protected"}

    return app


def build_client(app: FastAPI | None = None):
    # For these tests we want to see the raw HTTP status/JSON, so we disable
    # server-exception re-raising.
    return TestClient(app or main.create_app(), raise_server_exceptions=False)


def _assert_relay_error(resp, *, code: str, message_substring: str) -> None:
    data = resp.json()
    assert "error" in data
    err = data["error"]
    assert err["code"] == code
    assert err["type"] == "relay_auth_error"
    assert message_substring in err["message"]


def test_health_endpoint_remains_open(monkeypatch):
    app = build_app(monkeypatch, relay_enabled=True)
    client = build_client(app)

    response = client.get("/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_endpoint_trailing_slash_is_public(monkeypatch):
    app = build_app(monkeypatch, relay_enabled=True)
    client = build_client(app)

    response = client.get("/v1/health/")

    # We want /v1/health/ to behave the same as /v1/health.
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_route_requires_auth_when_enabled(monkeypatch):
    app = build_app(monkeypatch, relay_enabled=True)
    client = build_client(app)

    response = client.get("/v1/protected")

    assert response.status_code == 401
    _assert_relay_error(
        response,
        code="missing_relay_key",
        message_substring="Missing Authorization header",
    )
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_route_accepts_valid_key(monkeypatch):
    app = build_app(monkeypatch, relay_enabled=True, relay_key="relay-key")
    client = build_client(app)

    response = client.get(
        "/v1/protected",
        headers={"Authorization": "Bearer relay-key"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "protected"


def test_non_v1_route_requires_auth_when_enabled(monkeypatch):
    """
    With relay auth enabled, the root route `/` is protected by middleware.
    This matches the current implementation which protects all routes
    except a small set of health/docs endpoints.
    """
    app = build_app(monkeypatch, relay_enabled=True, relay_key="relay-key")
    client = build_client(app)

    response = client.get("/")

    assert response.status_code == 401
    _assert_relay_error(
        response,
        code="missing_relay_key",
        message_substring="Missing Authorization header",
    )


def test_protected_route_rejects_invalid_key(monkeypatch):
    app = build_app(monkeypatch, relay_enabled=True, relay_key="relay-key")
    client = build_client(app)

    response = client.get(
        "/v1/protected",
        headers={"Authorization": "Bearer wrong"},
    )

    assert response.status_code == 401
    _assert_relay_error(
        response,
        code="invalid_relay_key",
        message_substring="Invalid relay key",
    )
    assert response.headers["www-authenticate"] == "Bearer"


def test_middleware_opt_out_when_disabled(monkeypatch):
    app = build_app(monkeypatch, relay_enabled=False)
    client = build_client(app)

    response = client.get("/v1/protected")

    # When auth is disabled, the middleware must not block the route.
    assert response.status_code == 200
    assert response.json()["status"] == "protected"

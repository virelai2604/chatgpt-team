# tests/test_relay_auth_middleware.py
import os

from fastapi.testclient import TestClient

from app.core import config
from app.main import app as fastapi_app


def build_app_with_auth(*, relay_enabled: bool, relay_key: str = "test-key"):
    """
    Build an app instance with RELAY_AUTH_ENABLED / RELAY_KEY patched via
    app.core.config.settings so we exercise the real middleware.
    """
    # Make sure settings see these values; settings is loaded once at import.
    config.settings.RELAY_AUTH_ENABLED = relay_enabled
    config.settings.RELAY_KEY = relay_key

    return fastapi_app


def build_client(relay_enabled: bool, relay_key: str = "test-key") -> TestClient:
    app = build_app_with_auth(relay_enabled=relay_enabled, relay_key=relay_key)
    client = TestClient(app)

    # Attach Authorization header only if caller wants it
    if relay_enabled and relay_key:
        client.headers.update({"Authorization": f"Bearer {relay_key}"})

    return client


def test_health_endpoints_remain_open_with_auth_enabled():
    """
    /health and /v1/health should stay public even when relay auth is enabled.

    This matches the documented behavior where health checks are not
    protected by the shared-secret header.
    """
    client = build_client(relay_enabled=True, relay_key="test-key")

    # Drop the Authorization header for this test to exercise the bypass
    client.headers.pop("Authorization", None)

    resp_root = client.get("/health")
    resp_v1 = client.get("/v1/health")

    assert resp_root.status_code == 200
    assert resp_v1.status_code == 200


def test_protected_route_requires_auth_when_enabled():
    """
    When RELAY_AUTH_ENABLED is true, hitting a /v1 route with no Authorization
    header should fail with a relay_auth_error and code=missing_relay_key.
    """
    client = build_client(relay_enabled=True, relay_key="test-key")

    # Remove auth header that build_client added
    client.headers.pop("Authorization", None)

    resp = client.get("/v1/models")
    assert resp.status_code == 401

    payload = resp.json()
    error = payload.get("error") or payload.get("detail", {}).get("error")

    assert error is not None
    assert error.get("code") == "missing_relay_key"
    assert error.get("type") == "relay_auth_error"


def test_protected_route_rejects_invalid_key():
    """
    Invalid bearer token should return code=invalid_relay_key.
    """
    client = build_client(relay_enabled=True, relay_key="test-key")

    # Overwrite Authorization header with a wrong token
    client.headers["Authorization"] = "Bearer totally-wrong"

    resp = client.get("/v1/models")
    assert resp.status_code == 401

    payload = resp.json()
    error = payload.get("error") or payload.get("detail", {}).get("error")

    assert error is not None
    assert error.get("code") == "invalid_relay_key"
    assert error.get("type") == "relay_auth_error"

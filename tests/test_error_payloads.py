# tests/test_error_payloads.py
"""Relay error payload contract.

Why this exists
---------------
`register_exception_handlers()` sat unwired for a long time, so the relay quietly
served FastAPI's default error bodies instead of its own `relay_error` shape. These
tests pin the shape down so it cannot silently regress to the defaults again.

In-process (FastAPI TestClient), so it runs fast and needs no OpenAI API key.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.core.config import settings
from app.main import app, create_app

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _auth_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Pin relay auth off for this module.

    Whether auth is on depends on ambient config — app/core/config.py enables it by
    default whenever a relay key happens to be present in the environment. These tests
    are about error *shape*, so they must not depend on that: with auth on, every
    non-public path returns the middleware's own 401 before the handlers are reached.
    """
    monkeypatch.setattr(settings, "RELAY_AUTH_ENABLED", False, raising=False)


# Defined at module scope on purpose. This module uses `from __future__ import
# annotations`, so FastAPI resolves a route's annotations against module globals; a
# model declared inside a test function is invisible there and the parameter silently
# degrades into a query param, which makes the 422 assertions test the wrong thing.
class _Body(BaseModel):
    name: str
    count: int


class _Secretish(BaseModel):
    api_key: str
    count: int


def _assert_relay_error(body: object, status: int) -> dict:
    """Every relay error is {"error": {message,type,param,code}, "status": N}."""
    assert isinstance(body, dict), f"expected a JSON object, got {type(body).__name__}"
    assert body.get("status") == status
    err = body.get("error")
    assert isinstance(err, dict), "error must be an object, not a bare string"
    assert err.get("type") == "relay_error"
    assert isinstance(err.get("message"), str) and err["message"]
    assert "param" in err and "code" in err
    return err


def test_unknown_path_uses_relay_error_shape() -> None:
    with TestClient(app) as client:
        r = client.get("/__definitely_not_a_route")
        assert r.status_code == 404
        _assert_relay_error(r.json(), 404)


def test_method_not_allowed_uses_relay_error_shape() -> None:
    with TestClient(app) as client:
        r = client.post("/health")
        assert r.status_code == 405
        _assert_relay_error(r.json(), 405)


def test_unhandled_exception_returns_json_object_not_bare_string() -> None:
    """Regression guard: the default 500 body was the JSON string "Internal Server Error",
    so callers doing response.json()["error"] hit a TypeError."""
    test_app = create_app()

    @test_app.get("/__boom")
    def _boom():  # pragma: no cover - invoked through the client
        raise RuntimeError("boom")

    with TestClient(test_app, raise_server_exceptions=False) as client:
        r = client.get("/__boom")
        assert r.status_code == 500
        err = _assert_relay_error(r.json(), 500)
        # The exception text must not leak to the caller.
        assert "boom" not in err["message"]


def test_validation_error_reports_offending_fields() -> None:
    """422 must name what was wrong; a bare "Validation error" is not actionable."""
    test_app = create_app()

    @test_app.post("/__validate")
    def _validate(body: _Body):  # pragma: no cover - invoked through the client
        return {"ok": True}

    with TestClient(test_app) as client:
        r = client.post("/__validate", json={"name": 123})
        assert r.status_code == 422
        err = _assert_relay_error(r.json(), 422)

        details = err.get("details")
        assert isinstance(details, list) and len(details) == 2

        locations = {d["loc"] for d in details}
        assert locations == {"body.name", "body.count"}

        # `param` names the first offending field.
        assert err["param"] in locations

        for d in details:
            assert d["msg"] and d["type"]
            # Submitted values are never echoed back — see _validation_details().
            assert "input" not in d


def test_validation_error_does_not_echo_submitted_values() -> None:
    """A relay forwards credential-bearing bodies; they must not come back in errors."""
    test_app = create_app()

    @test_app.post("/__secret")
    def _secret(body: _Secretish):  # pragma: no cover - invoked through the client
        return {"ok": True}

    with TestClient(test_app) as client:
        r = client.post("/__secret", json={"api_key": "sk-super-secret-value"})
        assert r.status_code == 422
        assert "sk-super-secret-value" not in r.text

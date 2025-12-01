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
    monkeypatch.setattr(config.settings, "RELAY_AUTH_ENABLED", relay_enabled)
    monkeypatch.setattr(config.settings, "RELAY_KEY", relay_key)
    app = main.create_app()

    @app.get("/v1/protected")
    async def protected():
        return {"status": "protected"}

    return app


def build_client(app: FastAPI | None = None):
    return TestClient(app or main.create_app(), raise_server_exceptions=False)


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

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_protected_route_requires_auth_when_enabled(monkeypatch):
    app = build_app(monkeypatch, relay_enabled=True)
    client = build_client(app)

    response = client.get("/v1/protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing Authorization header"}
    assert response.headers["www-authenticate"] == "Bearer"


def test_protected_route_accepts_valid_key(monkeypatch):
    app = build_app(monkeypatch, relay_enabled=True, relay_key="relay-key")
    client = build_client(app)

    response = client.get("/v1/protected", headers={"Authorization": "Bearer relay-key"})

    assert response.status_code == 200


def test_non_v1_route_remains_public(monkeypatch):
    app = build_app(monkeypatch, relay_enabled=True, relay_key="relay-key")
    client = build_client(app)

    response = client.get("/")

    assert response.status_code == 200

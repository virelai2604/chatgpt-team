from __future__ import annotations

from typing import Dict

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.core import config
from app.main import create_app


@pytest.fixture()
def client() -> TestClient:
    settings = config.get_settings()
    original: Dict[str, object] = {
        "RELAY_REALTIME_WS_ENABLED": settings.RELAY_REALTIME_WS_ENABLED,
        "RELAY_AUTH_ENABLED": settings.RELAY_AUTH_ENABLED,
        "RELAY_KEY": settings.RELAY_KEY,
    }

    try:
        settings.RELAY_REALTIME_WS_ENABLED = False
        settings.RELAY_AUTH_ENABLED = False
        settings.RELAY_KEY = None
        app = create_app()
        with TestClient(app) as test_client:
            yield test_client
    finally:
        settings.RELAY_REALTIME_WS_ENABLED = original["RELAY_REALTIME_WS_ENABLED"]
        settings.RELAY_AUTH_ENABLED = original["RELAY_AUTH_ENABLED"]
        settings.RELAY_KEY = original["RELAY_KEY"]


def test_realtime_session_rejects_invalid_model(client: TestClient) -> None:
    response = client.post("/v1/realtime/sessions", json={"model": "not-a-real-model"})
    assert response.status_code == 400
    body = response.json()
    assert body.get("error", {}).get("code") == "unsupported_model"


def test_realtime_local_helpers_ok(client: TestClient) -> None:
    response = client.post("/v1/realtime/sessions/validate", json={"session_id": "sess_dummy"})
    assert response.status_code == 200
    assert response.json().get("status") == "ok"

    response = client.get("/v1/realtime/sessions/introspect")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


def test_realtime_ws_disabled_closes(client: TestClient) -> None:
    with client.websocket_connect("/v1/realtime/ws?model=gpt-realtime") as websocket:
        with pytest.raises(WebSocketDisconnect) as exc:
            websocket.receive_text()
    assert exc.value.code == 1008

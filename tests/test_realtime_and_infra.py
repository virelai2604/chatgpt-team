import json
from typing import Any, Dict

from fastapi.testclient import TestClient


def _assert_json(resp, status_code: int = 200) -> Dict[str, Any]:
    assert resp.status_code == status_code
    assert resp.headers["content-type"].startswith("application/json")
    return resp.json()


def test_models_forwarded(client: TestClient, forward_spy: Dict[str, Any]) -> None:
    """
    Basic check that /v1/models is forwarded through the relay and that
    our openai_forward stub is being used.
    """
    resp = client.get("/v1/models")
    data = _assert_json(resp, 200)

    # Check that our stub is in effect
    assert data["object"] == "test_proxy"
    assert data["echo_path"] == "/v1/models"
    assert data["echo_method"] == "GET"

    # Check forward_spy was populated by FakeAsyncClient
    assert forward_spy.get("method") == "GET"
    assert forward_spy.get("url_path") == "/v1/models"


def test_realtime_sessions_forwarded(client: TestClient, forward_spy: Dict[str, Any]) -> None:
    """
    Check that /v1/realtime/sessions is forwarded via the same openai_forward
    stub and that we can see the path/method in forward_spy.
    """
    payload = {
        "model": "gpt-realtime",
        "metadata": {"source": "test"},
    }
    resp = client.post("/v1/realtime/sessions", json=payload)
    data = _assert_json(resp, 200)

    # Our openai_forward stub should echo back the JSON we sent
    assert data["object"] == "test_proxy"
    assert data["echo_path"] == "/v1/realtime/sessions"
    assert data["echo_method"] == "POST"

    # The stubbed upstream request body should match our payload
    assert json.loads(data["echo_json"]) == payload

    # Check that forward_spy also saw it
    assert forward_spy.get("method") == "POST"
    assert forward_spy.get("url_path") == "/v1/realtime/sessions"
    assert json.loads(forward_spy["json"]) == payload

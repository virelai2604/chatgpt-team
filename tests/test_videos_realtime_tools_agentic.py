import json
from typing import Any, Dict

from fastapi.testclient import TestClient
from pytest_mock import MockerFixture


def _assert_json(resp, status_code: int = 200) -> Dict[str, Any]:
    assert resp.status_code == status_code
    assert resp.headers["content-type"].startswith("application/json")
    return resp.json()


def test_videos_create_and_retrieve(client: TestClient, forward_spy: Dict[str, Any]) -> None:
    """
    Check that /v1/videos is wired through the relay and our openai_forward stub.
    """
    payload = {
        "model": "sora-2.0-pro",
        "prompt": "A motorcycle riding through Jakarta at sunset.",
    }
    resp = client.post("/v1/videos", json=payload)
    data = _assert_json(resp, 200)

    assert data["object"] == "test_proxy"
    assert data["echo_path"] == "/v1/videos"
    assert data["echo_method"] == "POST"

    echoed = json.loads(data["echo_json"])
    assert echoed["model"] == "sora-2.0-pro"
    assert "Jakarta" in echoed["prompt"]

    # Simulate retrieving video content through a sub-route (subpath test)
    forward_spy.clear()
    resp_get = client.get("/v1/videos/video_123")
    data_get = _assert_json(resp_get, 200)
    assert data_get["object"] == "test_proxy"
    assert data_get["echo_path"] == "/v1/videos/video_123"

    # The forward_spy should have captured a subpath for content route
    forward_spy.clear()
    resp_content = client.get("/v1/videos/video_123/content")
    data_content = _assert_json(resp_content, 200)
    assert data_content["object"] == "test_proxy"
    assert data_content["echo_path"] == "/v1/videos/video_123/content"
    # The FakeAsyncClient populates "subpath" in forward_spy for nested URLs
    assert forward_spy.get("subpath") == "/content"


def test_videos_delete_routes(client: TestClient, forward_spy: Dict[str, Any]) -> None:
    """
    Exercise DELETE routes for videos.
    """
    forward_spy.clear()
    resp = client.delete("/v1/videos/video_404")
    data = _assert_json(resp, 200)
    assert data["object"] == "test_proxy"
    assert data["echo_path"] == "/v1/videos/video_404"
    assert data["echo_method"] == "DELETE"


def test_realtime_sessions_helper(mocker: MockerFixture, client: TestClient) -> None:
    """
    Example of testing a higher-level helper that wraps /v1/realtime/sessions.
    In the real app, this might be used by an agentic tool or orchestration layer.
    """
    from app.routes import realtime

    # Fake a stable upstream response for a realtime session
    fake_upstream = {
        "object": "realtime.session",
        "id": "rsess_123",
        "session": {
            "id": "rsess_123",
            "model": "gpt-realtime",
            "ws_url": "wss://example.com/realtime/rsess_123",
        },
    }

    mocker.patch.object(
        realtime,
        "forward_openai_request",
        return_value=fake_upstream,
    )

    resp = client.post("/v1/realtime/sessions", json={"model": "gpt-realtime"})
    data = _assert_json(resp, 200)

    assert data["id"] == "rsess_123"
    assert data["session"]["model"] == "gpt-realtime"
    assert data["session"]["ws_url"].startswith("wss://")


def test_tools_include_video_generation(client: TestClient) -> None:
    """
    If the tools manifest includes a video generation tool, it should be
    visible in /v1/tools and /v1/tools/{id}.
    """
    resp = client.get("/v1/tools")
    if resp.status_code != 200:
        # If tools are not configured in this environment, we skip.
        return

    data = _assert_json(resp, 200)
    tools = data.get("data") or []
    assert isinstance(tools, list)

    video_tool_id = None
    for t in tools:
        if "video" in t.get("id", "") or "video" in t.get("name", "").lower():
            video_tool_id = t["id"]
            break

    if not video_tool_id:
        # No video tool configured; nothing more to assert.
        return

    resp2 = client.get(f"/v1/tools/{video_tool_id}")
    data2 = _assert_json(resp2, 200)
    assert data2["id"] == video_tool_id
    assert "video" in data2.get("name", "").lower() or "video" in data2.get("description", "").lower()

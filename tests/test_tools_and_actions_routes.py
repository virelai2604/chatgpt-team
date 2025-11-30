import os
from typing import Any, Dict

from fastapi.testclient import TestClient


def _assert_json(resp, status_code: int = 200) -> Dict[str, Any]:
    assert resp.status_code == status_code
    assert resp.headers["content-type"].startswith("application/json")
    return resp.json()


def test_actions_ping(client: TestClient) -> None:
    resp = client.get("/actions/ping")
    data = _assert_json(resp, 200)
    assert data["status"] == "ok"


def test_actions_relay_info(client: TestClient) -> None:
    resp = client.get("/actions/relay_info")
    data = _assert_json(resp, 200)

    assert "relay_name" in data
    assert "environment" in data
    assert "app_mode" in data
    assert "base_openai_api" in data


def test_tools_routes_when_manifest_present(client: TestClient) -> None:
    """
    If TOOLS_MANIFEST or TOOLS_MANIFEST_PATH is configured, /v1/tools and
    /v1/tools/{id} should be available. Otherwise, this test is skipped.
    """
    tools_manifest = os.getenv("TOOLS_MANIFEST")
    tools_manifest_path = os.getenv("TOOLS_MANIFEST_PATH")
    if not tools_manifest and not tools_manifest_path:
        # If neither is configured, we skip this test.
        return

    # List tools
    resp = client.get("/v1/tools")
    data = _assert_json(resp, 200)
    tools = data.get("data") or []
    assert isinstance(tools, list)
    assert tools, "Expected at least one tool when manifest is configured"

    first_id = tools[0]["id"]

    # Get tool details
    resp2 = client.get(f"/v1/tools/{first_id}")
    data2 = _assert_json(resp2, 200)
    assert data2["id"] == first_id
    assert "name" in data2
    assert "description" in data2

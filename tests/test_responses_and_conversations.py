import json
from typing import Any, Dict, List

from fastapi.testclient import TestClient


def _assert_json(resp, status_code: int = 200) -> Dict[str, Any]:
    assert resp.status_code == status_code
    assert resp.headers["content-type"].startswith("application/json")
    return resp.json()


def _extract_text_from_responses_output(data: Dict[str, Any]) -> str:
    # New /v1/responses style
    output = data.get("output")
    if isinstance(output, list):
        buf: List[str] = []
        for item in output:
            if not isinstance(item, Dict):
                continue
            for part in item.get("content", []):
                if not isinstance(part, Dict):
                    continue
                if part.get("type") in ("output_text", "output_text_delta"):
                    buf.append(part.get("text") or part.get("delta") or "")
        return "".join(buf)

    # Fallback to /v1/chat/completions style if relayed that way
    if "choices" in data:
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            return ""
    return ""


def test_responses_basic(client: TestClient) -> None:
    """
    Basic /v1/responses check through the relay – using the openai_forward stub.
    """
    payload = {
        "model": "gpt-4.1-mini",
        "input": "Say exactly: relay-responses-basic-ok",
        "max_output_tokens": 64,
    }
    resp = client.post("/v1/responses", json=payload)
    data = _assert_json(resp, 200)

    # The stub should echo the request
    assert data["object"] == "test_proxy"
    assert data["echo_path"] == "/v1/responses"
    assert data["echo_method"] == "POST"

    echoed = json.loads(data["echo_json"])
    assert echoed["model"] == payload["model"]
    assert echoed["input"] == payload["input"]

    text = _extract_text_from_responses_output(data)
    # Since we are using a stub, we do not assert exact content,
    # but we ensure it is a string.
    assert isinstance(text, str)


def test_conversations_basic(client: TestClient) -> None:
    """
    /v1/conversations is not fully implemented in the relay yet, but we exercise
    the route wiring and basic shape via the stub.
    """
    # Create a conversation
    create_payload = {
        "title": "Test Conversation",
        "metadata": {"test": "true"},
    }
    resp = client.post("/v1/conversations", json=create_payload)
    data = _assert_json(resp, 200)

    # The stub is used for now, returning "test_proxy"
    assert data["object"] == "test_proxy"
    assert data["echo_path"] == "/v1/conversations"
    assert data["echo_method"] == "POST"

    echoed = json.loads(data["echo_json"])
    assert echoed["title"] == "Test Conversation"

    # Simulate listing conversations
    resp_list = client.get("/v1/conversations")
    data_list = _assert_json(resp_list, 200)
    assert data_list["object"] == "test_proxy"
    assert data_list["echo_path"] == "/v1/conversations"
    assert data_list["echo_method"] == "GET"


def test_conversations_items_basic(client: TestClient) -> None:
    """
    Exercise the /v1/conversations/{id}/items routes for basic wiring.
    Currently still stubbed through openai_forward.
    """
    conversation_id = "conv_123"

    # List items
    resp_list = client.get(f"/v1/conversations/{conversation_id}/items")
    data_list = _assert_json(resp_list, 200)
    assert data_list["object"] == "test_proxy"
    assert data_list["echo_path"] == f"/v1/conversations/{conversation_id}/items"
    assert data_list["echo_method"] == "GET"

    # Create item
    item_payload = {
        "type": "message",
        "role": "user",
        "content": [
            {"type": "input_text", "text": "Hello from conversation item"},
        ],
    }
    resp_create = client.post(
        f"/v1/conversations/{conversation_id}/items", json=item_payload
    )
    data_create = _assert_json(resp_create, 200)
    assert data_create["object"] == "test_proxy"
    assert data_create["echo_path"] == f"/v1/conversations/{conversation_id}/items"
    assert data_create["echo_method"] == "POST"

    echoed = json.loads(data_create["echo_json"])
    assert echoed["role"] == "user"
    assert echoed["content"][0]["text"].startswith("Hello from conversation item")

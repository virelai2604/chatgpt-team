import json
from typing import Any, Dict

import httpx
import pytest
from fastapi.testclient import TestClient


def _assert_single_upstream_request(httpx_mock) -> httpx.Request:
    calls = httpx_mock.get_requests()
    assert len(calls) == 1
    return calls[0]


def _request_json(req: httpx.Request) -> Dict[str, Any]:
    """
    Extract JSON payload from an httpx.Request recorded by pytest-httpx,
    handling the different shapes in httpx 0.27+.
    """
    body = req.content
    if not body:
        return {}
    if isinstance(body, bytes):
        try:
            return json.loads(body.decode("utf-8"))
        except Exception:
            return {}
    if isinstance(body, str):
        try:
            return json.loads(body)
        except Exception:
            return {}
    return {}


def test_models_forwarding_smoke(client: TestClient, httpx_mock) -> None:
    """
    Smoke test that /v1/models is forwarded to OPENAI_API_BASE/v1/models
    and that the relay returns whatever upstream returns (here stubbed via httpx_mock).
    """
    httpx_mock.add_response(
        method="GET",
        url="https://api.openai.com/v1/models",
        json={"object": "list", "data": [{"id": "gpt-4.1-mini"}]},
        status_code=200,
    )

    resp = client.get("/v1/models")
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    assert data["data"][0]["id"] == "gpt-4.1-mini"

    req = _assert_single_upstream_request(httpx_mock)
    assert req.method == "GET"
    assert req.url.path == "/v1/models"


def test_embeddings_forwarding_smoke(client: TestClient, httpx_mock) -> None:
    """
    Smoke test that /v1/embeddings is forwarded as a POST to  /v1/embeddings.
    """
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/embeddings",
        json={
            "object": "list",
            "data": [
                {"embedding": [0.1, 0.2, 0.3]},
            ],
        },
        status_code=200,
    )

    payload = {
        "model": "text-embedding-3-small",
        "input": "test-embeddings-forwarding",
    }

    resp = client.post("/v1/embeddings", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "list"
    assert len(data["data"][0]["embedding"]) == 3

    req = _assert_single_upstream_request(httpx_mock)
    assert req.method == "POST"
    assert req.url.path == "/v1/embeddings"

    sent_json = _request_json(req)
    assert sent_json["model"] == payload["model"]
    assert sent_json["input"] == payload["input"]


def test_responses_forwarding_smoke(client: TestClient, httpx_mock) -> None:
    """
    Smoke test that /v1/responses is forwarded as POST to upstream /v1/responses.
    """
    upstream_json = {
        "object": "response",
        "id": "resp_123",
        "output": [
            {
                "role": "assistant",
                "content": [
                    {"type": "output_text", "text": "Hello from upstream"},
                ],
            }
        ],
    }
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/responses",
        json=upstream_json,
        status_code=200,
    )

    payload = {
        "model": "gpt-4.1-mini",
        "input": "Say hello",
    }

    resp = client.post("/v1/responses", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["object"] == "response"
    assert data["id"] == "resp_123"

    req = _assert_single_upstream_request(httpx_mock)
    assert req.method == "POST"
    assert req.url.path == "/v1/responses"

    sent_json = _request_json(req)
    assert sent_json["model"] == payload["model"]
    assert sent_json["input"] == payload["input"]


@pytest.mark.skip(reason="Conversations forwarding not enabled in this deployment")
def test_conversations_forwarding_smoke(client: TestClient, httpx_mock) -> None:
    """
    Example of how conversations forwarding would be tested once the relay
    fully supports OpenAI /v1/conversations endpoints (create/list/etc.).
    """
    httpx_mock.add_response(
        method="POST",
        url="https://api.openai.com/v1/conversations",
        json={"id": "conv_123", "object": "conversation"},
        status_code=200,
    )

    payload = {"title": "Forwarded Conversation"}
    resp = client.post("/v1/conversations", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "conv_123"
    assert data["object"] == "conversation"

    req = _assert_single_upstream_request(httpx_mock)
    assert req.method == "POST"
    assert req.url.path == "/v1/conversations"
    sent_json = _request_json(req)
    assert sent_json["title"] == "Forwarded Conversation"

# tests/test_local_e2e.py

import json

import pytest
from starlette.testclient import TestClient


@pytest.mark.integration
def test_health_endpoints_ok(client: TestClient) -> None:
    # Root health (public)
    r_root = client.get("/")
    assert r_root.status_code == 200

    # /health and /v1/health should share the same base payload shape
    r_plain = client.get("/health")
    r_v1 = client.get("/v1/health")

    assert r_plain.status_code == 200
    assert r_v1.status_code == 200

    body_plain = r_plain.json()
    body_v1 = r_v1.json()

    # Based on your existing health route and API docs
    assert body_plain.get("status") == "ok"
    assert body_v1.get("status") == "ok"

    # Basic shape checks – loosened enough to be future-proof
    for body in (body_plain, body_v1):
        assert "timestamp" in body
        assert "relay" in body
        assert "openai" in body


@pytest.mark.integration
def test_responses_non_streaming_basic(client: TestClient) -> None:
    payload = {
        "model": "gpt-5.1",
        "input": "Say hello from the local relay.",
    }

    resp = client.post("/v1/responses", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    # Shape aligned with the ChatGPT Responses API
    assert data.get("object") == "response"
    assert "id" in data

    # Look for the response text somewhere in the nested structure
    serialized = json.dumps(data).lower()
    assert "hello" in serialized and "local relay" in serialized


def _collect_sse_buffer(client: TestClient, payload: dict) -> str:
    """POST /v1/responses with stream=True and collect raw SSE text."""
    buffer = ""
    # TestClient.stream() gives you an httpx streaming Response
    with client.stream("POST", "/v1/responses", json=payload) as resp:
        assert resp.status_code == 200
        for chunk in resp.iter_text():
            if not chunk:
                continue
            buffer += chunk
    return buffer


@pytest.mark.integration
def test_responses_streaming_sse_basic(client: TestClient) -> None:
    payload = {
        "model": "gpt-5.1",
        "input": "Stream a short message.",
        "stream": True,
    }

    raw = _collect_sse_buffer(client, payload)

    # Extract "data: ..." lines and JSON-decode each payload
    events = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or not line.startswith("data:"):
            continue
        json_str = line[len("data:"):].strip()
        try:
            events.append(json.loads(json_str))
        except json.JSONDecodeError:
            # Ignore keepalive or malformed chunks
            continue

    assert events, "No SSE data events parsed from streamed response"

    # We expect at least one output_text.delta and a final response.completed
    event_types = {e.get("type") for e in events if isinstance(e, dict)}

    assert "response.created" in event_types
    assert "response.output_text.delta" in event_types
    assert "response.completed" in event_types

    # Collect all text deltas into a single string
    deltas = [
        e.get("delta", "")
        for e in events
        if isinstance(e, dict) and e.get("type") == "response.output_text.delta"
    ]
    combined = " ".join(deltas).strip()
    assert combined, "No text deltas found in SSE stream"

    # We only check for a key word to stay robust across model changes
    assert "message" in combined.lower()


@pytest.mark.integration
def test_embeddings_basic(client: TestClient) -> None:
    payload = {
        "model": "text-embedding-3-small",
        "input": "Hello from the embedding test.",
    }

    resp = client.post("/v1/embeddings", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert data.get("object") == "list"
    assert "data" in data
    assert data["data"], "Embeddings data array is unexpectedly empty"

    first = data["data"][0]
    assert first.get("object") == "embedding"
    assert isinstance(first.get("embedding"), list)
    assert len(first["embedding"]) > 10

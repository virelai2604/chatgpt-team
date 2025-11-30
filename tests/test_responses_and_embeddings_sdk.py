import json
import os
from typing import Any, Dict

from fastapi.testclient import TestClient
from openai import OpenAI


def _assert_proxy(data: Dict[str, Any], path: str, method: str) -> None:
    assert data["object"] == "test_proxy"
    assert data["echo_path"] == path
    assert data["echo_method"] == method


def _make_client() -> OpenAI:
    """
    Construct an OpenAI SDK client that points to the relay instead of
    https://api.openai.com, using environment variables configured in pytest.ini.

    Priority:
      - base_url: OPENAI_BASE_URL (e.g. http://127.0.0.1:8000/v1)
      - api_key: OPENAI_API_KEY (dummy is fine for tests)
    """
    api_key = os.environ.get("OPENAI_API_KEY", "test-sdk-key")
    base_url = (
        os.environ.get("OPENAI_BASE_URL")
        or os.environ.get("OPENAI_API_BASE")
        or "https://api.openai.com/v1"
    )
    return OpenAI(api_key=api_key, base_url=base_url)


def test_responses_via_sdk(client: TestClient) -> None:
    """
    Use the OpenAI Python SDK (configured to talk to the relay) to call /v1/responses.
    We rely on environment variables (OPENAI_BASE_URL, OPENAI_API_KEY) that pytest
    and conftest have set up for us.
    """
    # For tests, we still open the client with default config, which should
    # be reading env vars: OPENAI_BASE_URL, OPENAI_API_KEY, etc.
    client_sdk = _make_client()

    resp = client_sdk.responses.create(
        model="gpt-4.1-mini",
        input="Say exactly: relay-sdk-responses-ok",
        max_output_tokens=32,
    )

    # We know that openai_forward returns a dict that is the JSON body
    # from the upstream response. In tests, the stub returns a "test_proxy" shape.
    assert isinstance(resp, dict)
    _assert_proxy(resp, "/v1/responses", "POST")

    echoed = json.loads(resp["echo_json"])
    assert echoed["model"] == "gpt-4.1-mini"
    assert echoed["input"] == "Say exactly: relay-sdk-responses-ok"


def test_embeddings_via_sdk(client: TestClient) -> None:
    """
    Use the OpenAI Python SDK (configured to talk to the relay) to call /v1/embeddings.
    The relay's openai_forward stub should echo the JSON we send.
    """
    client_sdk = _make_client()

    resp = client_sdk.embeddings.create(
        model="text-embedding-3-small",
        input="relay-sdk-embeddings-ok",
    )

    assert isinstance(resp, dict)
    _assert_proxy(resp, "/v1/embeddings", "POST")

    echoed = json.loads(resp["echo_json"])
    assert echoed["model"] == "text-embedding-3-small"
    assert echoed["input"] == "relay-sdk-embeddings-ok"

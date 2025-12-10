# tests/integration/test_render_relay_basic.py

import os
import pytest
import requests


def _get_base_url() -> str:
    """
    Resolve the Render relay base URL from env.

    Example:
      export RENDER_RELAY_URL="https://chatgpt-team-relay.onrender.com"
    """
    base = os.environ.get("RENDER_RELAY_URL")
    if not base:
        pytest.skip("RENDER_RELAY_URL is not set; skipping Render integration tests.")
    return base.rstrip("/")


def _get_relay_headers() -> dict:
    """
    Build the auth headers for the relay.

    Your app’s relay middleware expects an 'x-relay-auth' header
    whose value matches the RELAY_AUTH_TOKEN (or equivalent) env var
    configured on the server.

    For integration tests we read a local env var RENDER_RELAY_KEY so
    you never hard-code secrets in the repo.
    """
    key = os.environ.get("RENDER_RELAY_KEY")
    if not key:
        pytest.skip("RENDER_RELAY_KEY is not set; skipping Render integration tests.")
    return {"x-relay-auth": key}


@pytest.mark.integration
def test_health_on_render() -> None:
    """
    Smoke test the Render /v1/health endpoint.

    This checks both:
      - The service is actually up.
      - The relay auth header is accepted in production mode.
    """
    base = _get_base_url()
    headers = _get_relay_headers()

    resp = requests.get(f"{base}/v1/health", headers=headers, timeout=10)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    # Shape is kept intentionally loose; adjust if your real health payload differs.
    assert data.get("object") == "health"
    assert "relay" in data
    assert data["relay"].get("app_mode") in {"production", "staging", "development"}


@pytest.mark.integration
def test_responses_endpoint_on_render() -> None:
    """
    Exercise /v1/responses through the Render relay.

    This hits the Ground Truth API via your relay, so it will
    consume tokens on your real OpenAI API key configured in Render.
    Keep prompts small.
    """
    base = _get_base_url()
    headers = _get_relay_headers()

    payload = {
        "model": "gpt-4.1-mini",  # or your DEFAULT_MODEL from Render
        "input": "Say exactly: render-relay-responses-ok",
        "max_output_tokens": 32,
    }

    resp = requests.post(
        f"{base}/v1/responses",
        json=payload,
        headers=headers,
        timeout=60,
    )
    assert resp.status_code == 200, resp.text

    data = resp.json()
    # Very loose structure check to avoid coupling to internal format:
    assert data.get("object") in {"response", "responses.response"}
    output = data.get("output") or {}
    # You can tighten this up once you're happy with the schema:
    # - check output["choices"][0]["message"]["content"]
    # - or whatever your relay returns.
    assert output != {}


@pytest.mark.integration
def test_embeddings_endpoint_on_render() -> None:
    """
    Exercise /v1/embeddings through the Render relay.

    This ensures the HTTP proxying for embeddings is wired correctly.
    """
    base = _get_base_url()
    headers = _get_relay_headers()

    payload = {
        "model": "text-embedding-3-small",
        "input": "render-relay-embeddings-ok",
    }

    resp = requests.post(
        f"{base}/v1/embeddings",
        json=payload,
        headers=headers,
        timeout=60,
    )
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data.get("object") in {"list", "embedding"}
    assert data.get("data"), data


@pytest.mark.integration
def test_files_list_on_render() -> None:
    """
    Optional: exercise /v1/files list.

    This is a cheap way to ensure your relay can talk to the upstream
    files API with the configured OpenAI key on Render.
    """
    base = _get_base_url()
    headers = _get_relay_headers()

    resp = requests.get(f"{base}/v1/files", headers=headers, timeout=30)

    # Depending on whether you've actually uploaded files, you might
    # get an empty list, but status 200 should still hold.
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("object") == "list"
    assert "data" in data

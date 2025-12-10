"""
Integration tests that hit the real Render deployment of the ChatGPT Team Relay.

These tests are intentionally tiny and only check:
  - /v1/health
  - /v1/responses
  - /v1/embeddings
  - /v1/files

They assume:
  - The relay is deployed at RENDER_RELAY_BASE_URL
  - Relay auth is enforced and uses the x-relay-auth header
  - The same RELAY_KEY value is configured in Render and in your local env

Run with:
    pytest tests/integration/test_render_relay.py -m integration
"""

from __future__ import annotations

import os
from typing import Any, Dict

import httpx
import pytest

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.getenv("RENDER_RELAY_BASE_URL") or ""
RELAY_KEY = (
    os.getenv("RELAY_KEY")
    or os.getenv("RENDER_RELAY_KEY")
    or os.getenv("RELAY_AUTH_TOKEN")
)

if not BASE_URL or not RELAY_KEY:
    pytest.skip(
        "Set RENDER_RELAY_BASE_URL and RELAY_KEY (or RENDER_RELAY_KEY / RELAY_AUTH_TOKEN) "
        "to run Render integration tests.",
        allow_module_level=True,
    )

# Mark the whole module as "integration" so you can filter with -m integration
pytestmark = pytest.mark.integration


def _base_url() -> str:
    """
    Normalise the base URL (no trailing slash).
    Example: https://chatgpt-team-relay.onrender.com
    """
    return BASE_URL.rstrip("/")


def _headers() -> Dict[str, str]:
    """
    Headers to talk to the relay in APP_MODE=production.

    Adjust the auth header name if you ever change relay_auth.py; by default the
    middleware expects an `x-relay-auth` header whose value matches your
    relay auth secret.
    """
    return {
        "x-relay-auth": RELAY_KEY,
        "accept": "application/json",
        # FastAPI is happy without Content-Type on GET; POSTs include JSON below.
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_health_ok() -> None:
    """
    Basic sanity check that the Render relay is up and reporting metadata.

    - /v1/health should return 200
    - object == "health"
    - relay.app_mode should be "production"
    """
    url = f"{_base_url()}/v1/health"
    resp = httpx.get(url, headers=_headers(), timeout=30.0)

    assert resp.status_code == 200, f"Health check failed: {resp.status_code} {resp.text}"

    data = resp.json()
    assert data.get("object") == "health"
    relay_meta = data.get("relay") or {}
    assert relay_meta.get("app_mode") == "production"
    # Just make sure meta block exists and has at least one field
    meta = data.get("meta") or {}
    assert "python_version" in meta or "timestamp" in meta


def test_responses_round_trip() -> None:
    """
    Tiny /v1/responses smoke test.

    We send a deterministic instruction and confirm the returned JSON looks like
    a Response object and contains our magic string somewhere in the payload.
    """
    url = f"{_base_url()}/v1/responses"

    model = os.getenv("INTEGRATION_RESPONSE_MODEL", "gpt-4.1-mini")
    payload: Dict[str, Any] = {
        "model": model,
        "input": "Say exactly: render-relay-ok",  # keep this super short
        "max_output_tokens": 16,
    }

    resp = httpx.post(
        url,
        headers={**_headers(), "content-type": "application/json"},
        json=payload,
        timeout=60.0,
    )

    assert resp.status_code == 200, f"/v1/responses failed: {resp.status_code} {resp.text}"

    data = resp.json()
    # Very loose, future-proof checks – we don't depend on full schema here
    assert data.get("object") == "response"
    assert "id" in data

    # To avoid depending on exact Responses API nesting, just search the JSON repr
    serialized = repr(data).lower()
    assert "render-relay-ok" in serialized, f"magic phrase not found in response: {serialized}"


def test_embeddings_round_trip() -> None:
    """
    Tiny /v1/embeddings smoke test.

    We embed a single short string and verify that:
      - status is 200
      - response has 'data' and at least one item with an 'embedding' field.
    """
    url = f"{_base_url()}/v1/embeddings"

    model = os.getenv("INTEGRATION_EMBEDDING_MODEL", "text-embedding-3-small")
    payload: Dict[str, Any] = {
        "model": model,
        "input": "hello from render integration test",
    }

    resp = httpx.post(
        url,
        headers={**_headers(), "content-type": "application/json"},
        json=payload,
        timeout=60.0,
    )

    assert resp.status_code == 200, f"/v1/embeddings failed: {resp.status_code} {resp.text}"

    data = resp.json()
    # Upstream embeddings API returns an object with "object": "list" and "data" array. :contentReference[oaicite:2]{index=2}
    assert data.get("data") is not None, f"Unexpected embeddings payload: {data}"

    items = data.get("data") or []
    assert len(items) >= 1, f"No embedding items returned: {data}"

    first = items[0]
    assert isinstance(first, dict), f"First embedding item is not an object: {first}"
    assert "embedding" in first, f"No 'embedding' field on first item: {first}"
    assert isinstance(first["embedding"], list), "Embedding should be a list of floats"


def test_files_list_auth_only() -> None:
    """
    Very small /v1/files check.

    We do NOT upload anything here (to keep this cheap and side-effect-free).
    We just verify:
      - auth works against the relay
      - the relay can talk to OpenAI's Files list endpoint. :contentReference[oaicite:3]{index=3}
    """
    url = f"{_base_url()}/v1/files"

    resp = httpx.get(
        url,
        headers=_headers(),
        timeout=30.0,
    )

    # If your OpenAI API key is valid, this should be 200.
    # If the key is missing/invalid, you'll likely see a 4xx; in that case you
    # can loosen this assertion or skip this test.
    assert resp.status_code == 200, f"/v1/files failed: {resp.status_code} {resp.text}"

    data = resp.json()
    assert data.get("object") == "list"
    # Data can be empty; we only assert that the field exists.
    assert "data" in data

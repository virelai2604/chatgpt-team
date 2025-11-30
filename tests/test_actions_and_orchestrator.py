# tests/test_actions_and_orchestrator.py

from __future__ import annotations

from typing import Dict, Any

import pytest


@pytest.mark.anyio
async def test_actions_ping(client) -> None:
    """
    Verify /v1/actions/ping returns a simple JSON status payload and
    does NOT hit upstream OpenAI.

    This is a purely local health-style endpoint.
    """
    resp = client.get("/v1/actions/ping")
    assert resp.status_code == 200

    data = resp.json()
    # Shape as defined in app/routes/actions.py
    assert data.get("source") == "chatgpt-team-relay"
    assert data.get("status") == "ok"
    # These fields should be non-empty strings
    assert isinstance(data.get("app_mode"), str) and data["app_mode"]
    assert isinstance(data.get("environment"), str) and data["environment"]


@pytest.mark.anyio
async def test_actions_relay_info(client) -> None:
    """
    Verify /v1/actions/relay_info returns a structured description of
    the relay environment.

    This is used by Actions / toolchains to auto-discover the relay.
    """
    resp = client.get("/v1/actions/relay_info")
    assert resp.status_code == 200

    info = resp.json()
    # Core structural expectations from actions.relay_info
    assert info.get("type") == "relay.info"

    # Nested "relay" section
    relay = info.get("relay") or {}
    assert isinstance(relay, dict)
    assert isinstance(relay.get("name"), str) and relay["name"]
    assert isinstance(relay.get("app_mode"), str) and relay["app_mode"]
    assert isinstance(relay.get("environment"), str) and relay["environment"]

    # Upstream defaults
    upstream = info.get("upstream") or {}
    assert isinstance(upstream, dict)
    assert isinstance(upstream.get("base_url"), str) and upstream["base_url"]
    assert isinstance(upstream.get("default_model"), str) and upstream["default_model"]


@pytest.mark.anyio
async def test_video_generations_forward_has_correct_path_and_method(
    client,
    forward_spy,
) -> None:
    """
    Ensure POST /v1/videos/generations is forwarded correctly through
    the videos router and orchestrator to the upstream stub.

    We assert on:
      - HTTP 200 from the stub
      - Correct HTTP method and URL
      - Forwarded JSON body
    """
    payload = {
        "model": "gpt-video-test",
        "input": "test clip via relay",
    }

    resp = client.post("/v1/videos/generations", json=payload)
    assert resp.status_code == 200

    # Inspect what the FakeAsyncClient saw.
    assert forward_spy["method"] == "POST"
    assert forward_spy["url"].endswith("/v1/videos/generations")

    forwarded_json = forward_spy.get("json") or {}
    # Should include at least our model and input as-is
    assert forwarded_json.get("model") == payload["model"]
    assert forwarded_json.get("input") == payload["input"]


@pytest.mark.anyio
async def test_orchestrator_forwards_unknown_v1_paths(
    client,
    forward_spy,
) -> None:
    """
    Hit a /v1/* path that is NOT handled by a dedicated router and
    verify that the P4 orchestrator forwards it to OpenAI via the
    forward_openai_request machinery.

    We do not depend on a 200 here; the stub may legitimately return 404.
    The key is that the upstream URL/method/body are correct.
    """
    payload = {"text": "hello from orchestrator test"}

    # /v1/audio/speech is a good example of a path that will be handled
    # by the generic orchestrator when not implemented locally.
    resp = client.post("/v1/audio/speech", json=payload)

    # Status may be 200 or 404 depending on the stub; both are acceptable.
    assert resp.status_code in (200, 404)

    assert forward_spy["method"] == "POST"
    assert forward_spy["url"].endswith("/v1/audio/speech")

    forwarded_json =_

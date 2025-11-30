# tests/test_images_and_videos_routes_extra.py

import json
from typing import Any, Dict

import pytest

from tests.client import client

# NOTE:
# These tests run in APP_MODE=test and rely on requests-mock to intercept
# outgoing HTTP calls to the real OpenAI API. They do *not* hit the real
# network, but they exercise your FastAPI routes and forwarding layer.


def _json(obj: Dict[str, Any]) -> str:
    """Small helper to pretty-print for debugging if needed."""
    return json.dumps(obj, indent=2, sort_keys=True)


@pytest.mark.anyio
def test_image_edits_forward(requests_mock) -> None:
    """
    Ensure /v1/images/edits forwards correctly via forward_openai_request.

    We mock the upstream OpenAI endpoint and verify that:
      - The relay calls the correct URL.
      - The response body is passed through unchanged.
    """
    upstream_url = "https://api.openai.com/v1/images/edits"
    mocked_response = {
        "created": 1234567890,
        "data": [
            {
                "url": "https://example.test/generated-image.png",
            }
        ],
    }

    # Mock the upstream OpenAI call
    requests_mock.post(upstream_url, json=mocked_response, status_code=200)

    # Minimal body; we do not validate schema here, only forwarding
    body = {
        "model": "gpt-image-1",
        "prompt": "A minimal test edit prompt",
        # In the real API you'd send an image file or URL; for the
        # purposes of this relay test we keep it simple and JSON-only.
    }

    resp = client.post("/v1/images/edits", json=body)

    assert resp.status_code == 200, _json(resp.json())
    assert resp.json() == mocked_response


@pytest.mark.anyio
def test_video_metadata_forward(requests_mock) -> None:
    """
    Exercise GET /v1/videos/{video_id} (metadata lookup).

    We mock the upstream /v1/videos/video_123 endpoint and verify that
    the relay passes through status code and JSON.
    """
    video_id = "video_123"
    upstream_url = f"https://api.openai.com/v1/videos/{video_id}"
    mocked_response = {
        "id": video_id,
        "object": "video",
        "status": "completed",
        "duration": 8,
        "model": "sora-1",
    }

    requests_mock.get(upstream_url, json=mocked_response, status_code=200)

    resp = client.get(f"/v1/videos/{video_id}")

    assert resp.status_code == 200, _json(resp.json())
    body = resp.json()
    assert body["id"] == video_id
    assert body["status"] == "completed"


@pytest.mark.anyio
def test_video_content_forward(requests_mock) -> None:
    """
    Exercise GET /v1/videos/{video_id}/content (binary content download).

    We mock binary content coming from OpenAI and ensure the relay
    propagates status, headers, and body bytes.
    """
    video_id = "video_123"
    upstream_url = f"https://api.openai.com/v1/videos/{video_id}/content"

    # Simulate a tiny MP4 payload
    video_bytes = b"\x00\x00\x00\x14ftypmp42"  # not a real MP4, but good enough for a smoke test

    requests_mock.get(
        upstream_url,
        content=video_bytes,
        headers={"Content-Type": "video/mp4"},
        status_code=200,
    )

    resp = client.get(f"/v1/videos/{video_id}/content")

    assert resp.status_code == 200
    # content-type should be preserved by the proxy
    assert resp.headers.get("content-type") == "video/mp4"
    assert resp.content == video_bytes


@pytest.mark.anyio
def test_video_delete_forward_error_passthrough(requests_mock) -> None:
    """
    Confirm that upstream 4xx errors for video deletion are passed through.

    This ensures that your relay does not swallow errors and that the
    client can see a 'not found' error coming from OpenAI.
    """
    video_id = "video_404"
    upstream_url = f"https://api.openai.com/v1/videos/{video_id}"
    mocked_response = {
        "error": {
            "message": f"Video '{video_id}' not found",
            "type": "invalid_request_error",
        }
    }

    requests_mock.delete(upstream_url, json=mocked_response, status_code=404)

    resp = client.delete(f"/v1/videos/{video_id}")

    assert resp.status_code == 404
    assert resp.json() == mocked_response


@pytest.mark.anyio
def test_models_delete_error_passthrough(requests_mock) -> None:
    """
    Optional: confirm that /v1/models/{id} also passes through upstream errors
    (e.g. deleting a non-existent model).

    Even if you do not expose model deletion in your UI, this test proves
    that the proxy behaves transparently.
    """
    model_id = "bad-model"
    upstream_url = f"https://api.openai.com/v1/models/{model_id}"
    mocked_response = {
        "error": {
            "message": f"Model '{model_id}' does not exist",
            "type": "invalid_request_error",
        }
    }

    requests_mock.delete(upstream_url, json=mocked_response, status_code=404)

    resp = client.delete(f"/v1/models/{model_id}")

    assert resp.status_code == 404
    assert resp.json() == mocked_response

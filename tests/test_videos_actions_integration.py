from __future__ import annotations

import base64
import os
from typing import Any, Dict

import httpx
import pytest

from app.routes.videos import (
    _ALLOWED_VIDEO_MODELS,
    _ALLOWED_VIDEO_SECONDS,
    _ALLOWED_VIDEO_SIZES,
    _MAX_DURATION_SECONDS,
    _MAX_FRAMES,
    _MAX_VIDEO_BYTES,
)


pytestmark = pytest.mark.integration


def _is_openai_error(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    error = payload.get("error")
    if not isinstance(error, dict):
        return False
    message = error.get("message")
    err_type = error.get("type")
    return isinstance(message, str) and isinstance(err_type, str)


def _assert_4xx_openai_error(response: httpx.Response) -> None:
    assert 400 <= response.status_code < 500, f"expected 4xx, got {response.status_code}: {response.text[:200]}"
    try:
        payload = response.json()
    except Exception:
        pytest.fail(f"expected JSON error payload, got: {response.text[:200]}")
    assert _is_openai_error(payload), f"expected OpenAI-shaped error, got: {payload}"


def _payload_over_max_bytes() -> str:
    raw = b"x" * (_MAX_VIDEO_BYTES + 1)
    return base64.b64encode(raw).decode("utf-8")


@pytest.mark.asyncio
async def test_actions_videos_generations_rejects_invalid_inputs(client: httpx.AsyncClient) -> None:
    url = "/v1/actions/videos/generations"
    base_payload = {"prompt": "A test prompt"}

    invalid_base64 = {**base_payload, "data_base64": "not-base64!!"}
    r = await client.post(url, json=invalid_base64)
    _assert_4xx_openai_error(r)

    empty_bytes = {**base_payload, "data_base64": ""}
    r = await client.post(url, json=empty_bytes)
    _assert_4xx_openai_error(r)

    oversized = {**base_payload, "data_base64": _payload_over_max_bytes()}
    r = await client.post(url, json=oversized)
    _assert_4xx_openai_error(r)

    too_many_frames = {**base_payload, "frames": _MAX_FRAMES + 1}
    r = await client.post(url, json=too_many_frames)
    _assert_4xx_openai_error(r)

    too_long_duration = {**base_payload, "duration_seconds": _MAX_DURATION_SECONDS + 1}
    r = await client.post(url, json=too_long_duration)
    _assert_4xx_openai_error(r)

    invalid_model = {**base_payload, "model": "invalid-model"}
    r = await client.post(url, json=invalid_model)
    _assert_4xx_openai_error(r)

    invalid_seconds = {**base_payload, "seconds": max(_ALLOWED_VIDEO_SECONDS) + 1}
    r = await client.post(url, json=invalid_seconds)
    _assert_4xx_openai_error(r)

    invalid_size = {**base_payload, "size": "999x999"}
    r = await client.post(url, json=invalid_size)
    _assert_4xx_openai_error(r)

from __future__ import annotations

import asyncio
import os

import httpx
import pytest


pytestmark = pytest.mark.integration


def _require_integration() -> None:
    if os.environ.get("INTEGRATION_OPENAI_API_KEY") not in {"1", "true", "TRUE", "yes", "YES"}:
        pytest.skip("Integration tests disabled (set INTEGRATION_OPENAI_API_KEY=1)")


def _default_model() -> str:
    return os.environ.get("DEFAULT_MODEL") or "gpt-5.1"


@pytest.mark.asyncio
async def test_actions_responses_stream_sse_multiple_frames(client: httpx.AsyncClient) -> None:
    _require_integration()

    payload = {"model": _default_model(), "input": "Reply with exactly: OK"}
    max_seconds = float(os.environ.get("SSE_MAX_TIME_SECONDS") or "15")

    async with client.stream("POST", "/v1/actions/responses/stream", json=payload) as response:
        if response.status_code != 200:
            body = await response.aread()
            pytest.fail(f"expected 200, got {response.status_code}: {body[:200]!r}")

        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type.lower(), f"unexpected content-type: {content_type}"

        lines = response.aiter_lines()
        data_frames = 0
        start = asyncio.get_running_loop().time()

        while asyncio.get_running_loop().time() - start < max_seconds and data_frames < 2:
            remaining = max_seconds - (asyncio.get_running_loop().time() - start)
            try:
                line = await asyncio.wait_for(lines.__anext__(), timeout=remaining)
            except StopAsyncIteration:
                break
            except asyncio.TimeoutError:
                break

            if line.startswith("data:"):
                data_frames += 1

        assert data_frames >= 2, f"expected multiple SSE frames, got {data_frames}"

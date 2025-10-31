# ==========================================================
# app/api/forward_openai.py — Ground Truth Forwarder (v2025.11 Final)
# ==========================================================
"""
Forwards /v1 requests to OpenAI-compatible APIs or a local mock.

Supports:
  • Non-streaming JSON responses (POST /v1/responses)
  • Streaming event responses (text/event-stream)
  • Offline safe mock mode when OPENAI_API_KEY is unset
"""

import os
import httpx
import logging
from typing import Any, AsyncGenerator, Dict, Union, Callable, Awaitable

# ----------------------------------------------------------
# Environment and Config
# ----------------------------------------------------------
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "180.0"))

logger = logging.getLogger("forward_openai")

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json",
}


# ----------------------------------------------------------
# Internal streaming handler
# ----------------------------------------------------------
async def _stream_from_openai(url: str, json_body: Dict[str, Any]) -> AsyncGenerator[str, None]:
    """Yield streaming chunks from the upstream OpenAI API."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        async with client.stream("POST", url, headers=HEADERS, json=json_body) as resp:
            if resp.status_code != 200:
                body = await resp.aread()
                raise RuntimeError(f"OpenAI stream error {resp.status_code}: {body.decode()}")
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    yield line[6:]
    yield "[DONE]"


# ----------------------------------------------------------
# Non-streaming forwarder
# ----------------------------------------------------------
async def _forward_once(url: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
    """Perform a single POST to OpenAI and return JSON."""
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(url, headers=HEADERS, json=json_body)
        if resp.status_code != 200:
            try:
                text = resp.text
            except Exception:
                text = (await resp.aread()).decode()
            raise RuntimeError(f"OpenAI request failed {resp.status_code}: {text}")
        return resp.json()


# ----------------------------------------------------------
# Local mock fallback (offline)
# ----------------------------------------------------------
async def _mock_response(endpoint: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
    """Offline-safe mock response for local testing."""
    model = json_body.get("model", "gpt-4o-mini")
    text = json_body.get("input", "Hello from local Ground Truth mock mode.")
    logger.warning(f"⚠️ Running offline for {endpoint}")
    return {
        "id": "mock-response-001",
        "object": "response",
        "model": model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": f"[MOCK] {text}"}}
        ],
    }


async def _mock_stream(endpoint: str) -> AsyncGenerator[str, None]:
    """Offline streaming mock."""
    yield f"data: [MOCK STREAM for {endpoint}]\n\n"
    yield "data: [DONE]\n\n"


# ----------------------------------------------------------
# Unified public interface
# ----------------------------------------------------------
async def forward_openai_request(
    endpoint: str,
    json_body: Dict[str, Any],
    stream: bool = False,
) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
    """
    Forward a request to OpenAI (or mock) depending on config.

    Returns:
        • dict for normal responses
        • async generator for streamed responses
    Example:
        result = await forward_openai_request("/v1/responses", body)
        async for chunk in await forward_openai_request("/v1/responses", body, stream=True):
            ...
    """
    url = f"{OPENAI_BASE}{endpoint}"

    # Offline mock mode
    if not OPENAI_API_KEY:
        if stream:
            logger.info(f"🧩 Using offline mock stream for {endpoint}")
            return _mock_stream(endpoint)
        logger.info(f"🧩 Using offline mock response for {endpoint}")
        return await _mock_response(endpoint, json_body)

    # Live request
    if stream:
        logger.info(f"🌊 Streaming request → {url}")
        return _stream_from_openai(url, json_body)
    else:
        logger.info(f"➡️ Forwarding request → {url}")
        return await _forward_once(url, json_body)

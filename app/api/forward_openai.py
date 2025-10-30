# ==========================================================
# app/api/forward_openai.py — Core Forwarding Engine (Ground Truth Compliant)
# ==========================================================
import os
import httpx
import logging
from typing import Any, Dict, AsyncGenerator

logger = logging.getLogger("forwarder")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

# Timeout per OpenAI spec: 60s connect/read, total optional
client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))

async def forward_openai_request(
    endpoint: str,
    method: str = "POST",
    json_data: Dict[str, Any] = None,
    stream: bool = False,
) -> Any:
    """
    Unified OpenAI request forwarder with async streaming support.
    Mirrors OpenAI 2025.10 Ground Truth streaming semantics:
      - Graceful handling of StreamClosed (no crash)
      - Logs early disconnects silently
    """
    url = f"{OPENAI_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    logger.debug(f"[Relay] Forwarding {method} {url}")
    if json_data:
        import json
        logger.debug("[Relay] Payload:\n%s", json.dumps(json_data, indent=2))

    try:
        if stream:
            async with client.stream(method, url, headers=headers, json=json_data) as r:

                async def event_stream() -> AsyncGenerator[str, None]:
                    try:
                        async for chunk in r.aiter_text():
                            yield chunk
                    except httpx.StreamClosed:
                        logger.warning("[Relay] Stream closed early — client or upstream disconnected.")
                    except Exception as e:
                        logger.error(f"[Relay] Unexpected stream error: {e}")
                    finally:
                        # End-of-stream marker (Ground Truth requires graceful termination)
                        yield ""

                return event_stream()

        # --- Non-streaming (blocking JSON) ---
        response = await client.request(method, url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"[Relay] OpenAI API Error: {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"[Relay] Unexpected Forwarding Error: {e}")
        raise

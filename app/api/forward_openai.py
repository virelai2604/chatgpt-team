# ==========================================================
# app/api/forward_openai.py — Core Forwarding Engine
# ==========================================================
import os
import httpx
from typing import Any, Dict, AsyncGenerator

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

client = httpx.AsyncClient(timeout=60.0)

async def forward_openai_request(
    endpoint: str,
    method: str = "POST",
    json_data: Dict[str, Any] = None,
    stream: bool = False,
) -> Any:
    """
    Unified OpenAI request forwarder with async streaming support.
    """
    url = f"{OPENAI_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"[DEBUG] Forwarding {method} {url}")
    if json_data:
        import json
        print("[DEBUG] JSON Payload:")
        print(json.dumps(json_data, indent=2))

    try:
        if stream:
            async with client.stream(method, url, headers=headers, json=json_data) as r:
                async def event_stream() -> AsyncGenerator[str, None]:
                    async for chunk in r.aiter_text():
                        yield chunk
                return event_stream()
        else:
            response = await client.request(method, url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"[DEBUG] OpenAI API Error: {e.response.text}")
        raise
    except Exception as e:
        print(f"[DEBUG] Unexpected Forwarding Error: {e}")
        raise
# ==========================================================
# app/api/forward_openai.py — Core Forwarding Engine
# ==========================================================
import os
import httpx
from typing import Any, Dict, AsyncGenerator

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")

client = httpx.AsyncClient(timeout=60.0)

async def forward_openai_request(
    endpoint: str,
    method: str = "POST",
    json_data: Dict[str, Any] = None,
    stream: bool = False,
) -> Any:
    """
    Unified OpenAI request forwarder with async streaming support.
    """
    url = f"{OPENAI_BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    print(f"[DEBUG] Forwarding {method} {url}")
    if json_data:
        import json
        print("[DEBUG] JSON Payload:")
        print(json.dumps(json_data, indent=2))

    try:
        if stream:
            async with client.stream(method, url, headers=headers, json=json_data) as r:
                async def event_stream() -> AsyncGenerator[str, None]:
                    async for chunk in r.aiter_text():
                        yield chunk
                return event_stream()
        else:
            response = await client.request(method, url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as e:
        print(f"[DEBUG] OpenAI API Error: {e.response.text}")
        raise
    except Exception as e:
        print(f"[DEBUG] Unexpected Forwarding Error: {e}")
        raise

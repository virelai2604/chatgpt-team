"""
forward_openai.py
-----------------
Transparent proxy between ChatGPT Team Relay and the upstream OpenAI API.

Handles:
- POST /v1/chat/completions
- GET /v1/models
- Any other /v1/* endpoints supported by OpenAI

Adds resilience against:
- Content-Length / streaming mismatches
- Large response payloads (ResponseTooLargeError)
- Automatic relay authentication
- Proper JSON decoding across PowerShell, cURL, or ChatGPT Actions
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import os
import json
import asyncio
import pprint

router = APIRouter()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com"

# Limit relay response size for ChatGPT Actions (bytes)
MAX_RELAY_RESPONSE_BYTES = 4_000_000  # ~4 MB safe for ChatGPT Actions

# Shared async HTTP client
client = httpx.AsyncClient(
    timeout=httpx.Timeout(120.0, connect=10.0),
    follow_redirects=True,
    http2=True
)


async def _stream_openai_response(upstream_response: httpx.Response) -> StreamingResponse:
    """Stream bytes from OpenAI to the relay client."""
    headers = dict(upstream_response.headers)
    headers.pop("content-length", None)
    headers.pop("transfer-encoding", None)

    async def byte_generator():
        async for chunk in upstream_response.aiter_bytes():
            yield chunk

    return StreamingResponse(
        byte_generator(),
        status_code=upstream_response.status_code,
        headers=headers,
        media_type=headers.get("content-type", "application/json")
    )


async def _buffered_openai_response(upstream_response: httpx.Response) -> Response:
    """Read full upstream response, enforce size limit, and return safe JSON."""
    content = await upstream_response.aread()

    if len(content) > MAX_RELAY_RESPONSE_BYTES:
        return JSONResponse(
            status_code=502,
            content={"error": "ResponseTooLargeError", "hint": "Try smaller output or set max_tokens."}
        )

    try:
        data = json.loads(content)
        return JSONResponse(status_code=upstream_response.status_code, content=data)
    except Exception:
        return Response(
            content=content,
            status_code=upstream_response.status_code,
            media_type=upstream_response.headers.get("content-type", "application/octet-stream")
        )


@router.api_route("/v1/{path:path}", methods=["GET", "POST", "DELETE", "PATCH"])
async def forward_openai(request: Request, path: str):
    """
    Forwards any /v1/* request to OpenAI's API.
    Automatically injects Authorization header and handles streaming.
    """
    method = request.method
    url = f"{OPENAI_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = dict(request.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    # Remove hop-by-hop headers that break proxying
    for key in ["host", "content-length", "transfer-encoding"]:
        headers.pop(key, None)

    # Parse request body safely across platforms
    try:
        json_data = await request.json()
    except Exception:
        body_bytes = await request.body()
        try:
            json_data = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            json_data = {}

    # Debugging output to verify payloads during testing
    print(f"\n>>> [Relay Debug] Forwarding {method} {url}")
    pprint.pprint(json_data)
    print(">>> Headers:", {k.lower(): v for k, v in headers.items() if k.lower() in ['content-type', 'authorization']})

    # Default fields for /v1/chat/completions
    if "chat/completions" in path:
        if not json_data.get("model"):
            json_data["model"] = "gpt-4o-mini"
        if "messages" not in json_data or not isinstance(json_data["messages"], list):
            json_data["messages"] = [{"role": "user", "content": "Hello from relay"}]

    # Add sensible token cap if none specified
    if method == "POST" and json_data and "max_tokens" not in json_data:
        json_data["max_tokens"] = 256

    try:
        # Decide streaming vs buffered mode
        if path.startswith("chat/completions") and json_data.get("stream", False):
            async with client.stream("POST", url, headers=headers, json=json_data) as r:
                return await _stream_openai_response(r)
        elif method == "POST":
            r = await client.post(url, headers=headers, json=json_data)
        elif method == "GET":
            r = await client.get(url, headers=headers)
        elif method == "DELETE":
            r = await client.delete(url, headers=headers)
        elif method == "PATCH":
            r = await client.patch(url, headers=headers, json=json_data)
        else:
            return JSONResponse(status_code=405, content={"error": "method_not_allowed"})

        # Log upstream result and extract error bodies if any
        print(f"[Relay → OpenAI] {r.status_code} {url}")
        if r.status_code >= 400:
            try:
                err_preview = (await r.aread()).decode("utf-8", errors="ignore")[:800]
                print("[Upstream Error Body]", err_preview)
                return JSONResponse(status_code=r.status_code, content={"error": "upstream_error", "body": err_preview})
            except Exception:
                pass

        return await _buffered_openai_response(r)

    except httpx.RequestError as e:
        return JSONResponse(status_code=502, content={"error": "upstream_unreachable", "detail": str(e)})
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error": "timeout", "detail": "OpenAI upstream timeout"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "relay_internal_error", "detail": str(e)})


@router.on_event("shutdown")
async def close_client():
    """Gracefully close shared HTTP client."""
    await client.aclose()

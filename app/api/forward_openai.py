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
"""

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import os
import json
import asyncio

router = APIRouter()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = "https://api.openai.com"

# Limit relay response size for ChatGPT Actions (bytes)
MAX_RELAY_RESPONSE_BYTES = 4_000_000  # ~4 MB safe for ChatGPT Actions

# Shared async client
client = httpx.AsyncClient(
    timeout=httpx.Timeout(120.0, connect=10.0),
    follow_redirects=True,
    http2=True
)

async def _stream_openai_response(upstream_response: httpx.Response) -> StreamingResponse:
    """
    Streams bytes from upstream OpenAI API to the relay client.
    Strips Content-Length headers to prevent uvicorn mismatches.
    """
    headers = dict(upstream_response.headers)
    headers.pop("content-length", None)  # Avoid runtime mismatch
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
    """
    Reads response fully, enforces a size limit, and returns a JSONResponse.
    Protects ChatGPT Actions from ResponseTooLargeError.
    """
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
        # Non-JSON, return raw
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
    url = f"{OPENAI_BASE_URL}/v1/{path}"
    headers = dict(request.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    # Remove hop-by-hop headers
    for key in ["host", "content-length", "transfer-encoding"]:
        headers.pop(key, None)

    # Gather body
    body_bytes = await request.body()
    json_data = None
    if body_bytes:
        try:
            json_data = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            json_data = None

    # Automatically add default max_tokens to prevent overloads
    if method == "POST" and json_data and "max_tokens" not in json_data:
        json_data["max_tokens"] = 256

    try:
        # Stream completions, buffer everything else
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

        # Handle large or JSON responses safely
        return await _buffered_openai_response(r)

    except httpx.RequestError as e:
        return JSONResponse(status_code=502, content={"error": "upstream_unreachable", "detail": str(e)})
    except asyncio.TimeoutError:
        return JSONResponse(status_code=504, content={"error": "timeout", "detail": "OpenAI upstream timeout"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": "relay_internal_error", "detail": str(e)})


# Close httpx client when shutting down
@router.on_event("shutdown")
async def close_client():
    await client.aclose()

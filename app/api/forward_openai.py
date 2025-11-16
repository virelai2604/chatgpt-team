import httpx
import logging
import json
import asyncio
import os
from fastapi import Request, Response
from starlette.responses import StreamingResponse

logger = logging.getLogger("uvicorn")

# Default OpenAI REST API endpoint; can be overridden via env or app.state
DEFAULT_OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")


async def _stream_upstream_response(upstream_response: httpx.Response) -> StreamingResponse:
    """
    Relay a streamed response (text/event-stream) from OpenAI to the client.
    """

    async def event_generator():
        async for line in upstream_response.aiter_lines():
            if line:
                # Pass lines through as-is
                yield f"{line}\n"
                await asyncio.sleep(0)  # yield control to event loop

    return StreamingResponse(
        event_generator(),
        status_code=upstream_response.status_code,
        headers={"content-type": "text/event-stream"},
    )


async def forward_openai_request(request: Request) -> Response:
    """
    Universal relay function that forwards /v1/* requests to OpenAI’s API.

    - Preserves Authorization, or injects OPENAI_API_KEY if missing.
    - Supports JSON and multipart/form-data (files).
    - Handles both streaming (SSE) and non-streaming responses.
    - Preserves query parameters on the URL.
    """
    method = request.method.upper()
    # Normalize to avoid leading slashes ambiguity
    path = request.url.path.lstrip("/")
    query = request.url.query

    # Allow app-level override (e.g., Azure-compatible or self-hosted base URLs)
    api_base = getattr(request.app.state, "OPENAI_API_BASE", DEFAULT_OPENAI_API_BASE)

    base_url = f"{api_base.rstrip('/')}/{path}"
    target_url = f"{base_url}?{query}" if query else base_url

    headers = dict(request.headers)

    # Determine upstream Authorization
    auth_header = headers.get("authorization")
    if not auth_header:
        # Prefer app.state if set, otherwise fallback to env var
        state_key = getattr(request.app.state, "OPENAI_API_KEY", None)
        key = state_key or DEFAULT_OPENAI_API_KEY
        if key:
            auth_header = f"Bearer {key}"
    if auth_header:
        headers["authorization"] = auth_header

    # Avoid issues with compressed responses
    headers["accept-encoding"] = "identity"

    # Handle multipart form data (for file uploads)
    if "multipart/form-data" in headers.get("content-type", ""):
        form = await request.form()
        files = []
        for key, value in form.multi_items():
            if hasattr(value, "filename"):
                files.append(
                    (key, (value.filename, await value.read(), value.content_type))
                )
            else:
                files.append((key, str(value)))
        data = None
        content = None
    else:
        data = await request.body()
        files = None
        content = data

    logger.info(f"🔁 Forwarding {method} → {target_url}")

    timeout = httpx.Timeout(60.0, read=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        upstream_response = await client.request(
            method=method,
            url=target_url,
            headers=headers,
            data=data if files is None else None,
            files=files,
            content=content if files is None else None,
        )

    # Handle streaming response (Responses API, etc.)
    if upstream_response.headers.get("content-type", "").startswith("text/event-stream"):
        logger.info("📡 Streaming OpenAI response back to client")
        return await _stream_upstream_response(upstream_response)

    # Handle JSON or binary payloads
    try:
        content_type = upstream_response.headers.get("content-type", "application/json")
        if "application/json" in content_type:
            parsed = upstream_response.json()
            body = json.dumps(parsed)
        else:
            body = upstream_response.content
    except Exception as e:
        logger.warning(f"⚠️ Error reading upstream response: {e}")
        body = upstream_response.text

    return Response(
        content=body,
        status_code=upstream_response.status_code,
        headers={
            "content-type": upstream_response.headers.get(
                "content-type", "application/json"
            )
        },
    )


async def forward_json(method: str, path: str, payload: dict, api_key: str) -> dict:
    """
    Direct JSON-only forwarder (utility for testing).
    """
    url = f"{DEFAULT_OPENAI_API_BASE.rstrip('/')}/{path.lstrip('/')}"
    headers = {
        "authorization": f"Bearer {api_key}",
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.request(method, url, json=payload, headers=headers)
        try:
            return r.json()
        except Exception:
            return {"status_code": r.status_code, "body": r.text}

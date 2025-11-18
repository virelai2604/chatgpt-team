import asyncio
import json
import logging
import os
from typing import Dict, Iterable, Optional, Tuple

import httpx
from fastapi import Request, Response
from starlette.responses import StreamingResponse

logger = logging.getLogger("relay")

# Default OpenAI REST API endpoint; can be overridden via env or app.state.
# IMPORTANT: Prefer setting OPENAI_API_BASE to "https://api.openai.com"
# (without /v1). The code below defensively handles both with/without /v1.
DEFAULT_OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")

DEFAULT_PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", "60.0"))


def _normalize_base_and_path(api_base: str, full_path: str) -> Tuple[str, str]:
    """
    Ensure we don't end up with /v1/v1 in the path.

    - api_base: e.g. https://api.openai.com or https://api.openai.com/v1
    - full_path: e.g. /v1/responses or /responses (depending on router)
    """
    normalized_base = api_base.rstrip("/")
    path = full_path.lstrip("/")

    # If base ends with "/v1" AND path starts with "v1/", strip the leading "v1/".
    if normalized_base.endswith("/v1") and path.startswith("v1/"):
        path = path[len("v1/") :]

    return normalized_base, path


def _filter_response_headers(headers: httpx.Headers) -> Dict[str, str]:
    """
    Drop hop-by-hop headers, keep everything else (rate limits, IDs, etc.).
    """
    blocked = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
               "te", "trailer", "transfer-encoding", "upgrade", "content-encoding"}
    return {k: v for k, v in headers.items() if k.lower() not in blocked}


async def _stream_upstream_response(upstream_response: httpx.Response) -> StreamingResponse:
    """
    Relay a streamed response (text/event-stream) from OpenAI to the client.
    """

    async def event_generator() -> Iterable[bytes]:
        async for line in upstream_response.aiter_lines():
            if line:
                # Pass lines through as-is, with newline, as SSE expects
                yield (line + "\n").encode("utf-8")
                await asyncio.sleep(0)

    headers = _filter_response_headers(upstream_response.headers)
    headers.setdefault("content-type", "text/event-stream")

    return StreamingResponse(
        event_generator(),
        status_code=upstream_response.status_code,
        headers=headers,
    )


async def forward_openai_request(request: Request) -> Response:
    """
    Universal relay function that forwards /v1/* requests to OpenAI’s API.

    - Preserves Authorization, or injects OPENAI_API_KEY if missing.
    - Optionally injects OpenAI-Organization from app.state / env if missing.
    - Supports JSON and multipart/form-data (files).
    - Handles both streaming (SSE) and non-streaming responses.
    - Preserves query parameters on the URL.
    """
    method = request.method.upper()
    full_path = request.url.path  # e.g. "/v1/embeddings"
    query = request.url.query

    # Base URL from app.state or environment
    api_base = getattr(request.app.state, "OPENAI_API_BASE", DEFAULT_OPENAI_API_BASE)
    normalized_base, normalized_path = _normalize_base_and_path(api_base, full_path)

    base_url = f"{normalized_base}/{normalized_path}"
    target_url = f"{base_url}?{query}" if query else base_url

    headers = dict(request.headers)

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------
    auth_header = headers.get("authorization")
    if not auth_header:
        state_key = getattr(request.app.state, "OPENAI_API_KEY", None)
        key = state_key or DEFAULT_OPENAI_API_KEY
        if key:
            auth_header = f"Bearer {key}"
    if auth_header:
        headers["authorization"] = auth_header

    # ------------------------------------------------------------------
    # Organization header (optional)
    # ------------------------------------------------------------------
    org_header = (
        headers.get("OpenAI-Organization")
        or headers.get("openai-organization")
        or None
    )
    if not org_header:
        state_org = getattr(request.app.state, "OPENAI_ORG_ID", None)
        org = state_org or DEFAULT_OPENAI_ORG_ID
        if org:
            headers["OpenAI-Organization"] = org

    # Disable compression so we can stream / inspect bodies cleanly
    headers["accept-encoding"] = "identity"

    # ------------------------------------------------------------------
    # Body handling: multipart vs JSON/bytes
    # ------------------------------------------------------------------
    content_type = headers.get("content-type", "")
    files = None
    data: Optional[bytes] = None
    content: Optional[bytes] = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        files = []
        for key, value in form.multi_items():
            if hasattr(value, "filename"):
                files.append(
                    (key, (value.filename, await value.read(), value.content_type))
                )
            else:
                files.append((key, str(value)))
    else:
        data = await request.body()
        content = data

    logger.info(
        "Forwarding request to OpenAI",
        extra={"path": target_url, "method": method},
    )

    timeout = httpx.Timeout(DEFAULT_PROXY_TIMEOUT, read=DEFAULT_PROXY_TIMEOUT)
    async with httpx.AsyncClient(timeout=timeout) as client:
        upstream_response = await client.request(
            method=method,
            url=target_url,
            headers=headers,
            data=data if files is None else None,
            files=files,
            content=content if files is None else None,
        )

    # Streaming responses (e.g., /v1/responses with stream: true)
    upstream_ct = upstream_response.headers.get("content-type", "")
    if upstream_ct.startswith("text/event-stream"):
        logger.info(
            "Streaming OpenAI response back to client",
            extra={"path": target_url},
        )
        return await _stream_upstream_response(upstream_response)

    # Non-streaming responses
    try:
        if "application/json" in upstream_ct:
            parsed = upstream_response.json()
            body: bytes = json.dumps(parsed).encode("utf-8")
        else:
            body = upstream_response.content
    except Exception as e:
        logger.warning(
            "Error reading upstream response",
            extra={"path": target_url, "exception": str(e)},
        )
        body = upstream_response.content

    resp_headers = _filter_response_headers(upstream_response.headers)
    resp_headers.setdefault("content-type", upstream_ct or "application/json")

    return Response(
        content=body,
        status_code=upstream_response.status_code,
        headers=resp_headers,
    )

"""
OpenAI upstream forwarder for the ChatGPT Team Relay.

This module exposes a single entrypoint:

    forward_openai_request(request: fastapi.Request) -> fastapi.Response

It is used by all local `/v1/*` routes (responses, files, embeddings, etc.)
to transparently proxy requests to the real OpenAI API while:

- Re-using the original HTTP method, path, query string, and body.
- Rebuilding headers safely (no hop-by-hop headers, fixed Authorization).
- Supporting both JSON and multipart/form-data bodies.
- Optionally streaming responses (SSE/chunked) when `stream` is requested.

The implementation is intentionally generic and does NOT depend on any
application-specific settings object so that it can be dropped into a
minimal FastAPI environment.
"""

from __future__ import annotations

import json
import os
from typing import AsyncIterator, Dict, Iterable, Tuple

import httpx
from fastapi import HTTPException, Request
from fastapi.responses import Response, StreamingResponse

# ---------------------------------------------------------------------------
# Basic environment configuration
# ---------------------------------------------------------------------------


def _get_upstream_base() -> str:
    """
    Return the upstream base URL (without trailing slash).

    OPENAI_API_BASE is expected to be something like:
        https://api.openai.com

    We intentionally do NOT append `/v1` here because the incoming path
    already includes `/v1/...`.
    """
    base = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
    return base.rstrip("/")


def _get_upstream_key() -> str:
    """
    Return the OpenAI API key that will be sent to the upstream service.

    - We NEVER forward the caller's Authorization header.
    - Instead, we always inject OPENAI_API_KEY from the environment.
    """
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured in the environment.")
    return key


def _get_timeout_seconds() -> float:
    """Return the timeout used for upstream HTTP requests."""
    # Use RELAY_TIMEOUT if set; fall back to PROXY_TIMEOUT, then a sane default.
    for env_name in ("RELAY_TIMEOUT", "PROXY_TIMEOUT"):
        val = os.getenv(env_name)
        if val:
            try:
                return float(val)
            except ValueError:
                pass
    return 120.0


# A single shared AsyncClient is sufficient and avoids connection churn.
_UPSTREAM_CLIENT: httpx.AsyncClient | None = None


def _get_httpx_client() -> httpx.AsyncClient:
    global _UPSTREAM_CLIENT
    if _UPSTREAM_CLIENT is None or _UPSTREAM_CLIENT.is_closed:
        _UPSTREAM_CLIENT = httpx.AsyncClient(timeout=_get_timeout_seconds())
    return _UPSTREAM_CLIENT


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


_HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
}


def _clean_request_headers(incoming: Iterable[Tuple[str, str]]) -> Dict[str, str]:
    """
    Take the incoming ASGI headers and return a sanitized dict suitable
    for sending to httpx / the upstream OpenAI API.
    """
    headers: Dict[str, str] = {}
    for name, value in incoming:
        lname = name.lower()
        if lname in _HOP_BY_HOP_HEADERS:
            continue
        # For most headers we simply keep the last value.
        headers[name] = value

    # Inject upstream Authorization, regardless of what the caller sent.
    upstream_key = _get_upstream_key()
    headers["Authorization"] = f"Bearer {upstream_key}"

    # If the user configured organization / project, pass them through.
    org = os.getenv("OPENAI_ORG_ID") or os.getenv("OPENAI_ORGANIZATION")
    if org:
        headers.setdefault("OpenAI-Organization", org)

    project = os.getenv("OPENAI_PROJECT")
    if project:
        headers.setdefault("OpenAI-Project", project)

    return headers


def _should_stream(headers: Dict[str, str], body: bytes) -> bool:
    """
    Decide whether the upstream request is asking for a streaming response.

    For the /v1/responses and similar endpoints, OpenAI uses a JSON field
    named `stream`. It may be:
        - true / false
        - an object with a `mode` field (e.g. { "mode": "updates" })

    Any truthy `stream` value means "use SSE / streaming".
    """
    if not body:
        return False

    content_type = headers.get("Content-Type") or headers.get("content-type") or ""
    if "application/json" not in content_type.lower():
        return False

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return False

    if isinstance(payload, dict) and payload.get("stream"):
        return True

    return False


def _clean_response_headers(upstream_headers: httpx.Headers) -> Dict[str, str]:
    """
    Strip hop-by-hop headers from the upstream response and return a plain dict.
    """
    cleaned: Dict[str, str] = {}
    for name, value in upstream_headers.items():
        lname = name.lower()
        if lname in _HOP_BY_HOP_HEADERS:
            continue
        cleaned[name] = value
    return cleaned


# ---------------------------------------------------------------------------
# Main proxy entrypoint
# ---------------------------------------------------------------------------


async def forward_openai_request(request: Request) -> Response:
    """
    Generic forwarder: take the incoming FastAPI request and proxy it
    to the real OpenAI API with minimal transformation.

    This function is suitable for wiring directly into routes such as:
        - POST   /v1/responses
        - POST   /v1/embeddings
        - POST   /v1/files
        - GET    /v1/files
        - DELETE /v1/files/{file_id}
        - etc.
    """
    client = _get_httpx_client()
    upstream_base = _get_upstream_base()

    # Path and querystring are forwarded 1:1.
    path = request.url.path
    query = request.url.query
    upstream_url = f"{upstream_base}{path}"
    if query:
        upstream_url = f"{upstream_url}?{query}"

    method = request.method.upper()

    # Read the full body ONCE from the ASGI request.
    try:
        body = await request.body()
    except Exception as exc:  # pragma: no cover - extremely rare
        raise HTTPException(status_code=400, detail=f"Failed to read request body: {exc}") from exc

    # Build sanitized headers + injected Authorization.
    headers = _clean_request_headers(request.headers.raw)

    # Decide whether to use a streaming response.
    stream_mode = _should_stream(headers, body)

    try:
        if stream_mode:
            # Streaming / SSE branch – do not buffer the upstream response.
            async with client.stream(
                method,
                upstream_url,
                headers=headers,
                content=body,
            ) as upstream_resp:
                resp_headers = _clean_response_headers(upstream_resp.headers)
                status_code = upstream_resp.status_code

                async def _iter_stream() -> AsyncIterator[bytes]:
                    async for chunk in upstream_resp.aiter_raw():
                        if chunk:
                            yield chunk

                return StreamingResponse(
                    _iter_stream(),
                    status_code=status_code,
                    headers=resp_headers,
                )

        # Non-streaming: simple request/response with full buffering.
        upstream_resp = await client.request(
            method,
            upstream_url,
            headers=headers,
            content=body if body else None,
        )
    except httpx.HTTPError as exc:
        # Network-level / protocol issues talking to OpenAI.
        raise HTTPException(
            status_code=502,
            detail=f"Upstream OpenAI request failed: {exc}",
        ) from exc

    resp_headers = _clean_response_headers(upstream_resp.headers)
    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
        media_type=resp_headers.get("content-type"),
    )

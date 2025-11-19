# app/api/forward_openai.py
"""
forward_openai.py — upstream forwarder for the ChatGPT Team Relay.

Responsibilities:
  - Take the incoming FastAPI Request.
  - Build the outbound HTTP request to the OpenAI API:
      • Preserve path and query string.
      • Override auth headers using env vars (OPENAI_API_KEY / OPENAI_ORG_ID).
      • Forward JSON bodies as JSON.
      • Forward multipart/form-data bodies (e.g. /v1/files) as raw bytes.
  - Return a FastAPI Response mirroring upstream status, headers, and body.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import Request, Response


OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "120"))


async def forward_openai_request(
    request: Request,
    method: Optional[str] = None,
    json: Optional[Dict[str, Any]] = None,
    raw_body: Optional[bytes] = None,
    content_type: Optional[str] = None,
) -> Response:
    """
    Generic forwarder used by all /v1/* routers.

    Args:
        request: Incoming FastAPI Request.
        method:  Optional override for HTTP method (defaults to request.method).
        json:    JSON payload to send upstream.
        raw_body:Raw bytes to send upstream (e.g. multipart/form-data).
        content_type: Explicit Content-Type (e.g. multipart/form-data;boundary=...).

    Behavior:
        - Upstream URL: OPENAI_API_BASE + request.url.path + (query string).
        - Auth: Uses OPENAI_API_KEY / OPENAI_ORG_ID, ignoring caller's Authorization.
        - Body:
            • If raw_body is not None → HTTP body = raw bytes.
            • Else if json is not None → HTTP body = JSON.
            • Else → No body.
        - Returns: FastAPI Response with upstream status_code, headers, and body.
    """
    if not OPENAI_API_KEY:
        # Hard fail if relay has no key configured
        return Response(
            content=b'{"error": "Relay missing OPENAI_API_KEY"}',
            media_type="application/json",
            status_code=500,
        )

    # -----------------------------------------------------------------------
    # Resolve method and upstream URL
    # -----------------------------------------------------------------------
    upstream_method = (method or request.method).upper()

    path = request.url.path  # e.g. "/v1/responses", "/v1/files"
    query = request.url.query
    if query:
        upstream_url = f"{OPENAI_API_BASE}{path}?{query}"
    else:
        upstream_url = f"{OPENAI_API_BASE}{path}"

    # -----------------------------------------------------------------------
    # Build headers (override auth, drop hop-by-hop)
    # -----------------------------------------------------------------------
    incoming_headers = dict(request.headers)

    upstream_headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    if OPENAI_ORG_ID:
        upstream_headers["OpenAI-Organization"] = OPENAI_ORG_ID

    hop_by_hop = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }

    for k, v in incoming_headers.items():
        lk = k.lower()
        if lk in hop_by_hop:
            continue
        if lk in {"authorization", "openai-organization"}:
            # Always use relay's credentials, not caller's
            continue
        if lk == "content-type":
            # We'll set Content-Type based on body below
            continue
        upstream_headers.setdefault(k, v)

    # Content-Type
    if content_type:
        upstream_headers["Content-Type"] = content_type
    elif json is not None:
        upstream_headers.setdefault("Content-Type", "application/json")

    # -----------------------------------------------------------------------
    # Outbound request via httpx
    # -----------------------------------------------------------------------
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        if raw_body is not None:
            upstream_resp = await client.request(
                method=upstream_method,
                url=upstream_url,
                headers=upstream_headers,
                content=raw_body,
            )
        elif json is not None:
            upstream_resp = await client.request(
                method=upstream_method,
                url=upstream_url,
                headers=upstream_headers,
                json=json,
            )
        else:
            upstream_resp = await client.request(
                method=upstream_method,
                url=upstream_url,
                headers=upstream_headers,
            )

    # -----------------------------------------------------------------------
    # Build FastAPI Response with upstream data
    # -----------------------------------------------------------------------
    resp_headers: Dict[str, str] = {}
    for k, v in upstream_resp.headers.items():
        if k.lower() in hop_by_hop:
            continue
        # Let FastAPI manage Content-Length if omitted
        resp_headers[k] = v

    return Response(
        content=upstream_resp.content,
        status_code=upstream_resp.status_code,
        headers=resp_headers,
    )

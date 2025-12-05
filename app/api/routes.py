"""
Fallback routing for OpenAI-style endpoints.

This module defines a catch-all router that proxies any ``/v1/*`` path not
explicitly handled by more specific routers. It reconstructs the upstream
path, preserves method, query parameters, and body, and then forwards the
request to the OpenAI API via :func:`forward_openai_from_parts`.

The previous implementation incorrectly passed a ``request`` argument to
``forward_openai_from_parts`` which is not part of its signature. This
version removes that argument so the call matches the helper in
``app/api/forward_openai.py``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_from_parts

# Use the same logger namespace as the rest of the relay
logger = logging.getLogger("relay")

# Define the router without a prefix; paths are explicit
router = APIRouter(tags=["openai-fallback"])


@router.get("/v1/ping")
async def v1_ping() -> Dict[str, Any]:
    """
    Simple health/ping endpoint under ``/v1`` for quick checks.

    This does **not** call the upstream OpenAI API and simply returns a
    lightweight JSON indicating that the relay is responsive.
    """
    logger.info("v1_ping called")
    return {"ok": True, "message": "relay /v1 ping"}


@router.api_route(
    "/v1/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def openai_fallback_proxy(full_path: str, request: Request) -> Response:
    """
    Catch-all proxy for any ``/v1/*`` path that is not handled by more specific
    routers.

    The relay reconstructs the upstream path, extracts query parameters,
    headers, and request body, then delegates to :func:`forward_openai_from_parts`.
    ``forward_openai_from_parts`` adds the relay's OpenAI credentials and
    performs the actual HTTP request.
    """
    # Construct the upstream path exactly as the client requested.
    # The router path is "/v1/{full_path:path}", so we rebuild the leading `/v1`.
    upstream_path = "/v1"
    if full_path:
        upstream_path += f"/{full_path}"

    # Extract query parameters and headers as plain dicts
    query: Dict[str, Any] = dict(request.query_params)
    headers: Dict[str, str] = {k: v for k, v in request.headers.items()}

    # Read the body once. If it parses as JSON we pass a dict/list;
    # otherwise we pass raw bytes. If there is no body we pass ``None``.
    raw_body: bytes = await request.body()
    json_body: Optional[Any] = None
    if raw_body:
        try:
            json_body = await request.json()
        except Exception:
            # Not JSON; keep as raw bytes
            json_body = None

    if json_body is not None:
        body: Any = json_body
    elif raw_body:
        body = raw_body
    else:
        body = None

    logger.info(
        "openai_fallback_proxy: method=%s path=%s query=%s",
        request.method,
        upstream_path,
        query,
    )

    # Delegate to the core forwarder without passing extraneous arguments
    return await forward_openai_from_parts(
        method=request.method,
        path=upstream_path,
        query=query,
        body=body,
        headers=headers,
    )

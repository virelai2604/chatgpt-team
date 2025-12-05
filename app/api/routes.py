# app/api/routes.py

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_from_parts

logger = logging.getLogger("relay")

router = APIRouter(tags=["openai-fallback"])


@router.get("/v1/ping")
async def v1_ping() -> Dict[str, Any]:
    """
    Simple health/ping endpoint under /v1 for quick checks.
    Does NOT hit OpenAI; purely local.
    """
    logger.info("v1_ping called")
    return {"ok": True, "message": "relay /v1 ping"}


@router.api_route(
    "/v1/{full_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def openai_fallback_proxy(full_path: str, request: Request) -> Response:
    """
    Generic fallback proxy for any /v1/* path that is not handled by
    more specific routers.

    It delegates to the core OpenAI forwarder so we get:
    - centralised auth (relay injects OPENAI_API_KEY)
    - consistent header filtering
    - streaming support (for stream=true + SSE Accept headers)
    """

    # Construct the upstream path exactly as the client requested.
    # router path is /v1/{full_path:path}, so we rebuild the leading /v1.
    upstream_path = "/v1"
    if full_path:
        upstream_path += f"/{full_path}"

    # Extract query params and headers
    query: Dict[str, Any] = dict(request.query_params)
    headers: Dict[str, str] = {k: v for k, v in request.headers.items()}

    # Read body once; if JSON, we pass dict; otherwise we pass bytes
    raw_body: bytes = await request.body()
    json_body: Optional[Any] = None

    if raw_body:
        try:
            json_body = await request.json()
        except Exception:
            # Not JSON; keep as raw bytes
            json_body = None

    body: Any
    if json_body is not None:
        body = json_body
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

    # Delegate to the core forwarder
    return await forward_openai_from_parts(
        method=request.method,
        path=upstream_path,
        query=query,
        body=body,
        headers=headers,
        request=request,
    )

# app/api/routes.py
from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response, StreamingResponse

from app.core.http_client import create_async_client, build_openai_headers
from app.api import sse as sse_utils


router = APIRouter()


# --- Health endpoints -------------------------------------------------------


@router.get("/health")
async def health_root() -> Dict[str, str]:
    """
    Simple liveness probe for the relay itself.
    """
    return {"status": "ok"}


@router.get("/v1/health")
async def health_v1() -> Dict[str, str]:
    """
    Namespaced health endpoint (mirrors other /v1/* paths).
    """
    return {"status": "ok"}


# --- Model list (GET /v1/models) -------------------------------------------


@router.get("/v1/models")
async def list_models() -> Response:
    """
    Transparent proxy for the OpenAI /v1/models endpoint.

    - Requires valid OPENAI_API_KEY in env.
    - RelayAuthMiddleware should already have validated the relay key
      before this handler runs.
    """
    async with create_async_client() as client:
        upstream = await client.get("/v1/models", headers=build_openai_headers())

    # Pass through status + body + content-type; avoid re-parsing JSON.
    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )


# --- Responses (POST /v1/responses) ----------------------------------------


@router.post("/v1/responses")
async def create_response(request: Request) -> Response:
    """
    Transparent proxy for OpenAI /v1/responses.

    Behavior:
      - Reads the raw JSON payload from the client.
      - If 'stream' is truthy, opens an upstream streaming request and
        proxies SSE bytes verbatim.
      - Otherwise performs a normal JSON POST and returns the body.

    Notes:
      - We attach OpenAI-Beta: responses=v1 so that the upstream API
        knows we're using the Responses endpoint.
    """
    payload: Dict[str, Any] = await request.json()
    stream_flag = bool(payload.get("stream"))

    headers = build_openai_headers(beta="responses=v1")

    # Non-streaming path: simple passthrough
    if not stream_flag:
        async with create_async_client() as client:
            upstream = await client.post(
                "/v1/responses",
                json=payload,
                headers=headers,
            )

        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            media_type=upstream.headers.get("content-type", "application/json"),
        )

    # Streaming path: SSE
    async def event_stream():
        try:
            async with create_async_client() as client:
                async with client.stream(
                    "POST",
                    "/v1/responses",
                    json=payload,
                    headers=headers,
                ) as upstream:
                    # Proxy upstream SSE bytes as-is.
                    async for chunk in upstream.aiter_raw():
                        if not chunk:
                            continue
                        yield chunk

        except httpx.HTTPError as exc:
            # Graceful SSE-compatible error frame in case upstream drops.
            yield sse_utils.format_sse_event(
                "error",
                {
                    "message": "Upstream SSE error while proxying /v1/responses.",
                    "type": exc.__class__.__name__,
                },
            )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )

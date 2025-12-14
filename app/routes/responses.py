from __future__ import annotations

import asyncio
import json
from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.api.forward_openai import (
    build_upstream_url,
    forward_openai_request,
    forward_responses_create,
)
from app.api.sse import create_sse_stream
from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses
    - Supports JSON payload
    - If payload has {"stream": true}, we stream SSE from upstream.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # If stream requested, proxy SSE stream directly.
    if body.get("stream") is True:
        settings = get_settings()
        url = build_upstream_url("/v1/responses")

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        if settings.openai_organization:
            headers["OpenAI-Organization"] = settings.openai_organization
        if settings.openai_project:
            headers["OpenAI-Project"] = settings.openai_project
        if settings.openai_beta:
            headers["OpenAI-Beta"] = settings.openai_beta

        data = json.dumps(body).encode("utf-8")
        client = get_async_httpx_client()

        async def event_generator():
            async with client.stream(
                "POST",
                url,
                headers=headers,
                content=data,
                timeout=settings.proxy_timeout_seconds,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line:
                        yield line + "\n"

        return StreamingResponse(
            create_sse_stream(event_generator()),
            media_type="text/event-stream",
        )

    # Non-streaming: use SDK (typed) and return JSON.
    result = await forward_responses_create(body)
    return Response(
        content=json.dumps(result),
        media_type="application/json",
    )


@router.post("/responses/compact")
async def create_response_compact(request: Request) -> Response:
    """
    POST /v1/responses/compact
    - convenience wrapper that can keep payload minimal on the client side
    """
    body = await request.json()
    body["metadata"] = body.get("metadata", {})
    body["metadata"]["compact"] = True
    result = await forward_responses_create(body)
    return Response(
        content=json.dumps(result),
        media_type="application/json",
    )


# --- Missing lifecycle endpoints (now added) ---


@router.get("/responses/{response_id}")
async def get_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/responses/{response_id}")
async def delete_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/responses/{response_id}/input_items")
async def get_response_input_items(response_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/responses/input_tokens")
async def get_input_token_counts(request: Request) -> Response:
    """
    POST /v1/responses/input_tokens
    (This is a top-level endpoint in the OpenAI API reference.)
    """
    return await forward_openai_request(request)


# Catch-all passthrough for future /v1/responses/* subroutes.
@router.api_route(
    "/responses/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def responses_passthrough(path: str, request: Request) -> Response:
    return await forward_openai_request(request)


# --- Simple SSE helper endpoint used by some clients/tests ---


@router.get("/responses:stream")
async def responses_stream() -> Response:
    """
    Deprecated-ish helper. Kept for compatibility.
    """
    async def gen():
        for i in range(3):
            yield f"data: ping {i}\n\n"
            await asyncio.sleep(0.1)

    return StreamingResponse(gen(), media_type="text/event-stream")

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse

from app.api.forward_openai import (
    forward_openai_request,
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    _filter_request_headers,
)
from app.utils.logger import relay_log as logger
from app.utils.auth import verify_relay_key


router = APIRouter(
    prefix="/v1",
    tags=["responses"],
    dependencies=[verify_relay_key],
)


async def _stream_openai_sse(request: Request, json_body: dict) -> StreamingResponse:
    """
    Streaming proxy for POST /v1/responses with `stream: true`.

    Uses Accept-Encoding="identity" and aiter_bytes() so the stream is always
    decoded bytes.

    relay_e2e_raw.py expects the streamed text to aggregate to 'relay-stream-ok'.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured",
                    "type": "config_error",
                    "code": "no_api_key",
                }
            },
        )

    base = OPENAI_API_BASE.rstrip("/")
    target_url = f"{base}{request.url.path}"
    params = dict(request.query_params)

    request_headers = request.headers
    upstream_headers = _filter_request_headers(request_headers)
    upstream_headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    upstream_headers["Accept-Encoding"] = "identity"
    upstream_headers.setdefault("Content-Type", "application/json")

    timeout = httpx.Timeout(30.0)

    logger.info("→ [responses.stream] POST %s", target_url)

    async def event_generator() -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                target_url,
                params=params,
                headers=upstream_headers,
                json=json_body,
            ) as upstream_resp:
                async for chunk in upstream_resp.aiter_bytes():
                    yield chunk

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses

    - If body.stream == true → streaming SSE proxy.
    - Else → normal JSON proxy via forward_openai_request.
    """
    raw_body = await request.body()
    json_body: dict | None = None

    if raw_body:
        try:
            json_body = json.loads(raw_body.decode("utf-8"))
        except Exception:
            json_body = None

    if isinstance(json_body, dict) and json_body.get("stream") is True:
        return await _stream_openai_sse(request, json_body)

    logger.info("→ [responses] %s %s (non-stream)", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/responses")
async def list_responses(request: Request) -> Response:
    """
    GET /v1/responses
    """
    return await forward_openai_request(request)


@router.get("/responses/{response_id}")
async def retrieve_response(response_id: str, request: Request) -> Response:
    """
    GET /v1/responses/{response_id}
    """
    return await forward_openai_request(request)


@router.post("/responses/{response_id}/cancel")
async def cancel_response(response_id: str, request: Request) -> Response:
    """
    POST /v1/responses/{response_id}/cancel
    """
    return await forward_openai_request(request)

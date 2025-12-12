# app/routes/responses.py
from __future__ import annotations

import json
import os
from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response as FastAPIResponse, StreamingResponse
from starlette.requests import ClientDisconnect

from app.api.forward_openai import forward_openai_request, forward_responses_create
from app.core.config import settings
from app.core.http_client import get_async_httpx_client
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


_HOP_BY_HOP = {
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


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _join_openai_url(base: str, path: str, query: str | None = None) -> str:
    """
    Same joining logic as forward_openai.py; duplicated here to keep this file standalone.
    """
    base = (base or "").rstrip("/")
    path = "/" + (path or "").lstrip("/")

    if base.endswith("/v1") and path.startswith("/v1/"):
        path = path[3:]  # remove extra '/v1'

    url = f"{base}{path}"
    if query:
        url = f"{url}?{query.lstrip('?')}"
    return url


def _proxy_headers(request: Request, *, accept_sse: bool = False) -> dict[str, str]:
    headers: dict[str, str] = {}
    for k, v in request.headers.items():
        if k.lower() in _HOP_BY_HOP:
            continue
        headers[k] = v

    headers["Authorization"] = f"Bearer {settings.openai_api_key}"
    headers.setdefault("Content-Type", "application/json")
    if accept_sse:
        headers.setdefault("Accept", "text/event-stream")
    return headers


@router.post("/v1/responses")
async def create_response(request: Request) -> Any:
    try:
        body: Dict[str, Any] = await request.json()
    except ClientDisconnect:
        return FastAPIResponse(status_code=499)

    stream = bool(body.get("stream"))

    if not stream:
        logger.info("Handling /v1/responses as non-streaming JSON request")
        resp = await forward_responses_create(body)
        # resp is an OpenAI Response model here
        return JSONResponse(content=resp.model_dump())

    # True SSE proxy
    if not _bool_env("ENABLE_STREAM", default=True):
        # Optional: if you ever disable streaming, fail loudly instead of returning empty
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "Streaming disabled (ENABLE_STREAM=false)"}},
        )

    logger.info("Handling /v1/responses as streaming SSE request (true upstream pass-through)")

    client = get_async_httpx_client()
    upstream_url = _join_openai_url(settings.openai_base_url, "/v1/responses")

    headers = _proxy_headers(request, accept_sse=True)

    upstream_req = client.build_request(
        "POST",
        upstream_url,
        headers=headers,
        content=json.dumps(body).encode("utf-8"),
    )
    upstream_resp = await client.send(upstream_req, stream=True)

    # If upstream errored, return an actual error response (NOT a 200 + empty body)
    if upstream_resp.status_code >= 400:
        err_bytes = await upstream_resp.aread()
        await upstream_resp.aclose()

        # Prefer JSON errors when possible
        try:
            return JSONResponse(status_code=upstream_resp.status_code, content=json.loads(err_bytes.decode("utf-8")))
        except Exception:
            return FastAPIResponse(
                status_code=upstream_resp.status_code,
                content=err_bytes,
                media_type=upstream_resp.headers.get("content-type", "text/plain"),
            )

    async def event_stream() -> AsyncGenerator[bytes, None]:
        try:
            async for chunk in upstream_resp.aiter_raw():
                if chunk:
                    yield chunk
        finally:
            await upstream_resp.aclose()

    # SSE-friendly headers (helps nginx/proxies; harmless in tests)
    out_headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(
        event_stream(),
        status_code=upstream_resp.status_code,
        media_type="text/event-stream",
        headers=out_headers,
    )


@router.post("/v1/responses/compact")
async def compact_response(request: Request) -> Any:
    """
    OpenAI supports POST /v1/responses/compact. 
    """
    logger.info("Incoming /v1/responses/compact request")
    return await forward_openai_request(request)

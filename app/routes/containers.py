from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response, StreamingResponse
from starlette.background import BackgroundTask

from app.api.forward_openai import (
    _get_timeout_seconds,
    build_outbound_headers,
    build_upstream_url,
    filter_upstream_headers,
    forward_openai_request,
)
from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client

router = APIRouter(prefix="/v1", tags=["containers"])


@router.get("/containers")
async def containers_list(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/containers")
async def containers_create(request: Request) -> Response:
    return await forward_openai_request(request)


@router.head("/containers", include_in_schema=False)
async def containers_head(request: Request) -> Response:
    return await forward_openai_request(request)


@router.options("/containers", include_in_schema=False)
async def containers_options(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/containers/{container_id}/files/{file_id}/content")
async def containers_file_content(request: Request, container_id: str, file_id: str) -> Response:
    """
    Stream container file content.

    Critical behavior for Success Gate D:
      - Do NOT raise on upstream non-2xx.
      - If upstream returns 4xx/5xx, read the body and return it with upstream status
        (avoids relay 500 masking upstream errors).
      - Stream only on 2xx.
    """
    upstream_path = f"/v1/containers/{container_id}/files/{file_id}/content"

    s = get_settings()
    base_url = getattr(s, "openai_base_url", None) or "https://api.openai.com"

    upstream_url = build_upstream_url(upstream_path, request=request, base_url=base_url)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    timeout_s = _get_timeout_seconds(s)
    client = get_async_httpx_client(timeout=timeout_s)

    # Sent manually rather than via `async with client.stream(...)`. That context
    # manager closes the upstream response when this function returns — which is
    # *before* Starlette iterates a StreamingResponse — so the 2xx branch used to
    # answer 200 with an empty body while upstream had sent the file. Closing is
    # deferred to a BackgroundTask that runs after the body has been written.
    req = client.build_request("GET", upstream_url, headers=headers)
    try:
        upstream = await client.send(req, stream=True)
    except httpx.HTTPError as exc:
        # A transport failure (DNS, refused connection, timeout, a proxy rejecting
        # CONNECT) raises before any status code exists to propagate. Uncaught it
        # escaped as a bare relay 500 — the very thing this handler exists to
        # prevent. 424 is what forward_openai_request returns for the same class of
        # failure, so every route now degrades identically.
        raise HTTPException(
            status_code=424,
            detail=f"Upstream request failed: {type(exc).__name__}: {exc}",
        ) from exc

    status = upstream.status_code
    resp_headers = filter_upstream_headers(upstream.headers)
    media_type = upstream.headers.get("content-type")

    # IMPORTANT: never raise_for_status(); propagate upstream responses.
    if status >= 400:
        try:
            content = await upstream.aread()
        finally:
            await upstream.aclose()
        return Response(
            content=content,
            status_code=status,
            headers=resp_headers,
            media_type=media_type,
        )

    return StreamingResponse(
        upstream.aiter_bytes(),
        status_code=status,
        headers=resp_headers,
        media_type=media_type,
        background=BackgroundTask(upstream.aclose),
    )


@router.head("/containers/{container_id}/files/{file_id}/content", include_in_schema=False)
async def containers_file_content_head(request: Request, container_id: str, file_id: str) -> Response:
    return await forward_openai_request(request)

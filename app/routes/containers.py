from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.api.forward_openai import (
    _get_timeout_seconds,
    build_outbound_headers,
    build_upstream_url,
    filter_upstream_headers,
    forward_openai_request,
)
from app.core.http_client import get_async_httpx_client
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["containers"])


async def _forward(request: Request) -> Response:
    logger.info("→ [containers] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# ---- /v1/containers ----
@router.get("/containers")
async def containers_root_get(request: Request) -> Response:
    return await _forward(request)


@router.post("/containers")
async def containers_root_post(request: Request) -> Response:
    return await _forward(request)


@router.head("/containers", include_in_schema=False)
async def containers_root_head(request: Request) -> Response:
    return await _forward(request)


@router.options("/containers", include_in_schema=False)
async def containers_root_options(request: Request) -> Response:
    return await _forward(request)


async def _container_file_content_head(container_id: str, file_id: str, request: Request) -> Response:
    upstream_path = f"/v1/containers/{container_id}/files/{file_id}/content"
    upstream_url = build_upstream_url(upstream_path)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    # Forward Range if provided; otherwise minimal range for headers
    range_hdr: Optional[str] = request.headers.get("range")
    if range_hdr:
        headers["Range"] = range_hdr
    else:
        headers["Range"] = "bytes=0-0"

    client = get_async_httpx_client()
    timeout = _get_timeout_seconds()

    upstream_req = client.build_request(
        method="GET",
        url=upstream_url,
        params=request.query_params,
        headers=headers,
    )

    try:
        upstream_resp = await client.send(upstream_req, stream=True, timeout=timeout, follow_redirects=True)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail=f"Upstream timeout: {type(exc).__name__}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {type(exc).__name__}") from exc

    await upstream_resp.aclose()

    return Response(
        content=b"",
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
    )


async def _container_file_content_get(container_id: str, file_id: str, request: Request) -> Response:
    upstream_path = f"/v1/containers/{container_id}/files/{file_id}/content"
    upstream_url = build_upstream_url(upstream_path)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    # Forward Range if provided (best-effort)
    range_hdr: Optional[str] = request.headers.get("range")
    if range_hdr:
        headers["Range"] = range_hdr

    client = get_async_httpx_client()
    timeout = _get_timeout_seconds()

    upstream_req = client.build_request(
        method="GET",
        url=upstream_url,
        params=request.query_params,
        headers=headers,
    )

    try:
        upstream_resp = await client.send(upstream_req, stream=True, timeout=timeout, follow_redirects=True)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail=f"Upstream timeout: {type(exc).__name__}") from exc
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {type(exc).__name__}") from exc

    if upstream_resp.status_code >= 400:
        error_body = await upstream_resp.aread()
        await upstream_resp.aclose()
        return Response(
            content=error_body,
            status_code=upstream_resp.status_code,
            headers=filter_upstream_headers(upstream_resp.headers),
            media_type=upstream_resp.headers.get("content-type"),
        )

    return StreamingResponse(
        upstream_resp.aiter_bytes(),
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
        background=BackgroundTask(upstream_resp.aclose),
    )


@router.get("/containers/{container_id}/files/{file_id}/content")
async def container_file_content_get(container_id: str, file_id: str, request: Request) -> Response:
    return await _container_file_content_get(container_id=container_id, file_id=file_id, request=request)


@router.head("/containers/{container_id}/files/{file_id}/content")
async def container_file_content_head(container_id: str, file_id: str, request: Request) -> Response:
    return await _container_file_content_head(container_id=container_id, file_id=file_id, request=request)


@router.api_route(
    "/containers/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def containers_subpaths(path: str, request: Request) -> Response:
    logger.info("→ [containers/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

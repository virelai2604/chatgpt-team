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

router = APIRouter(
    prefix="/v1",
    tags=["containers"],
)


@router.api_route("/containers", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def containers_root(request: Request) -> Response:
    """
    - POST /v1/containers → create container
    - GET  /v1/containers → list containers
    """
    logger.info("→ [containers] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/containers/{container_id}/files/{file_id}/content",
    methods=["GET", "HEAD"],
)
async def container_file_content(container_id: str, file_id: str, request: Request) -> Response:
    """
    Retrieve binary bytes for a file stored inside a container.

    Upstream canonical:
      GET /v1/containers/{container_id}/files/{file_id}/content

    Behaviour:
      - GET streams bytes (no buffering)
      - HEAD returns headers using a minimal GET (Range: bytes=0-0) because upstream
        may not implement HEAD for binary endpoints.
    """
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

    if request.method.upper() == "HEAD":
        if "Range" not in headers:
            headers["Range"] = "bytes=0-0"

        upstream_req = client.build_request(
            method="GET",
            url=upstream_url,
            params=request.query_params,
            headers=headers,
        )

        try:
            upstream_resp = await client.send(
                upstream_req,
                stream=True,
                timeout=timeout,
                follow_redirects=True,
            )
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=504,
                detail=f"Upstream timeout: {type(exc).__name__}",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Upstream request failed: {type(exc).__name__}",
            ) from exc

        await upstream_resp.aclose()

        return Response(
            content=b"",
            status_code=upstream_resp.status_code,
            headers=filter_upstream_headers(upstream_resp.headers),
            media_type=upstream_resp.headers.get("content-type"),
        )

    upstream_req = client.build_request(
        method="GET",
        url=upstream_url,
        params=request.query_params,
        headers=headers,
    )

    try:
        upstream_resp = await client.send(
            upstream_req,
            stream=True,
            timeout=timeout,
            follow_redirects=True,
        )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail=f"Upstream timeout: {type(exc).__name__}",
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream request failed: {type(exc).__name__}",
        ) from exc

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


@router.api_route(
    "/containers/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def containers_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for /v1/containers/*, including:

      - /v1/containers/{container_id}
      - /v1/containers/{container_id}/files
      - /v1/containers/{container_id}/files/{file_id}/content

    NOTE: the explicit /content route above will match first for GET/HEAD and
    stream the bytes; everything else falls through here.
    """
    logger.info("→ [containers/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

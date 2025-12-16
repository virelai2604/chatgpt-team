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
    tags=["videos"],
)


@router.post("/videos/generations")
async def create_video_generation(request: Request) -> Response:
    """
    Handle POST /v1/videos/generations

    This is the main route used by tests like:
      - test_video_generations_forward
      - test_video_generations_forward_has_correct_path_and_method

    We don't inspect or validate the JSON body here — everything is
    forwarded as‑is via `forward_openai_request`.
    """
    logger.info("→ [videos] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route("/videos/{video_id}/content", methods=["GET", "HEAD"])
async def video_content(video_id: str, request: Request) -> Response:
    """
    Retrieve binary bytes for a generated video.

    Upstream canonical:
      GET /v1/videos/{video_id}/content

    Why this explicit route exists:
      - curl -I sends HEAD. Upstream may return 405 for HEAD on binary endpoints.
        We translate HEAD -> a minimal ranged GET (Range: bytes=0-0) so clients can
        inspect headers without downloading the full file.
      - GET is streamed to avoid buffering large video files in memory.
    """
    upstream_path = f"/v1/videos/{video_id}/content"
    upstream_url = build_upstream_url(upstream_path)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,     # don't force JSON for binary
        forward_accept=True,   # keep client Accept if present
        path_hint=upstream_path,
    )

    # Forward Range if provided (best-effort)
    range_hdr: Optional[str] = request.headers.get("range")
    if range_hdr:
        headers["Range"] = range_hdr

    client = get_async_httpx_client()
    timeout = _get_timeout_seconds()

    # HEAD: fetch headers via a tiny ranged GET and close immediately.
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

        # Do not read the body; just close the stream.
        await upstream_resp.aclose()

        return Response(
            content=b"",
            status_code=upstream_resp.status_code,
            headers=filter_upstream_headers(upstream_resp.headers),
            media_type=upstream_resp.headers.get("content-type"),
        )

    # GET: stream bytes to client
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
        # Read the error body fully so we can close upstream before returning.
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


@router.api_route("/videos", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_videos_root(request: Request) -> Response:
    """
    Root videos endpoint.

    Covers:
      - GET  /v1/videos   (list videos – smoke test allows 200 or 404)
      - POST /v1/videos   (future‑proofing)
    """
    logger.info("→ [videos] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def proxy_videos_subpaths(path: str, request: Request) -> Response:
    """
    Catch‑all for video subresources.

    Examples:
      - GET    /v1/videos/{video_id}
      - DELETE /v1/videos/{video_id}
      - future /v1/videos/* additions
    """
    logger.info("→ [videos/*] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)

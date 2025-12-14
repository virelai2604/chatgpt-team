from __future__ import annotations

from typing import Any, Dict

import httpx
from fastapi import APIRouter, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.api.forward_openai import (
    build_outbound_headers,
    build_upstream_url,
    filter_upstream_headers,
    forward_openai_request,
)
from app.core.config import get_settings
from app.core.http_client import get_async_httpx_client, get_async_openai_client

router = APIRouter(prefix="/v1", tags=["files"])


@router.get("/files")
async def list_files() -> Dict[str, Any]:
    client = get_async_openai_client()
    result = await client.files.list()
    return result.model_dump()


@router.post("/files")
async def create_file(
    purpose: str,
    file: UploadFile = File(...),
) -> Dict[str, Any]:
    """
    Upload a file to OpenAI. (multipart/form-data)
    Note: This reads the file into memory. For very large files, prefer OpenAI Uploads API.
    """
    client = get_async_openai_client()
    content = await file.read()
    result = await client.files.create(
        file=(file.filename, content, file.content_type),
        purpose=purpose,
    )
    return result.model_dump()


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str) -> Dict[str, Any]:
    client = get_async_openai_client()
    result = await client.files.retrieve(file_id)
    return result.model_dump()


@router.get("/files/{file_id}/content")
async def retrieve_file_content(file_id: str, request: Request) -> StreamingResponse:
    """
    Retrieve raw file bytes from OpenAI:
      GET /v1/files/{file_id}/content
    """
    settings = get_settings()

    upstream_url = build_upstream_url(f"/v1/files/{file_id}/content")

    # For binary GETs, do NOT force Content-Type.
    headers = build_outbound_headers(
        request.headers,
        content_type=None,
        default_json=False,
        forward_accept=True,
    )

    # Forward Range if provided (best-effort)
    range_hdr = request.headers.get("range")
    if range_hdr:
        headers["Range"] = range_hdr

    client = get_async_httpx_client()
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
            timeout=settings.proxy_timeout_seconds,
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream request failed: {e.__class__.__name__}",
        ) from e

    return StreamingResponse(
        upstream_resp.aiter_bytes(),
        status_code=upstream_resp.status_code,
        headers=filter_upstream_headers(upstream_resp.headers),
        media_type=upstream_resp.headers.get("content-type"),
        background=BackgroundTask(upstream_resp.aclose),
    )


@router.delete("/files/{file_id}")
async def delete_file(file_id: str) -> Dict[str, Any]:
    client = get_async_openai_client()
    result = await client.files.delete(file_id)
    return result.model_dump()


# Catch-all passthrough for any other /v1/files/* routes (future-proofing).
@router.api_route(
    "/files/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def files_passthrough(path: str, request: Request) -> Response:
    return await forward_openai_request(request)

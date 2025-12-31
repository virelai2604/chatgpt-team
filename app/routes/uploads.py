from __future__ import annotations

import base64
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.forward_openai import build_outbound_hears, build_upstream_url, forward_openai_method_path, forward_openai_request
from app.core.http_client import get_async_httpx_client

router = APIRouter(prefix="/v1", tags=["uploads"])
actions_router = APIRouter(prefix="/v1/actions/uploads", tags=["uploads_actions"])


@router.post("/uploads")
async def create_upload(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/parts")
async def create_upload_part(upload_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/complete")
async def complete_upload(upload_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/uploads/{upload_id}/cancel")
async def cancel_upload(upload_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.api_route(
    "/uploads/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=False,
)
async def uploads_passthrough(path: str, request: Request) -> Response:
    upstream_path = f"/v1/uploads/{path}".rstrip("/")
    return await forward_openai_request(request, upstream_path=upstream_path)


class ActionsUploadCreateRequest(BaseModel):
    """Actions-friendly JSON wrapper for /v1/uploads."""

    model_config = ConfigDict(extra="forbid")

    purpose: str = Field(..., description="Upload purpose (e.g. batch)")
    filename: str = Field(..., description="Original filename")
    bytes: int = Field(..., description="Total size in bytes")
    mime_type: str = Field(..., description="MIME type, e.g. text/plain")
    expires_after: Optional[dict] = Field(default=None, description="Optional expiration settings")

class ActionsUploadPartRequest(BaseModel):
    """Actions-friendly JSON wrapper for /v1/uploads/{id}/parts."""

    model_config = ConfigDict(extra="forbid")

    data_base64: str = Field(..., description="Base64-encoded part bytes (no data: prefix)")
    filename: Optional[str] = Field(default="part.bin", description="Original filename")
    mime_type: Optional[str] = Field(default="application/octet-stream", description="Part MIME type")


class ActionsUploadCompleteRequest(BaseModel):
    """Actions-friendly JSON wrapper for /v1/uploads/{id}/complete."""

    model_config = ConfigDict(extra="forbid")

    part_ids: list[str] = Field(..., description="List of upload part IDs to complete")


def _filter_response_headers(headers: httpx.Headers) -> Dict[str, str]:
    strip = {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "content-length",
        "content-encoding",
    }
    out: Dict[str, str] = {}
    for k, v in headers.items():
        if k.lower() in strip:
            continue
        out[k] = v
    return out


@actions_router.post("", summary="Actions wrapper for /v1/uploads (create upload)")
async def actions_create_upload(payload: ActionsUploadCreateRequest, request: Request) -> Response:
    upstream = await forward_openai_method_path(
        "POST",
        "/v1/uploads",
        json_body=payload.model_dump(),
        inbound_headers=request.headers,
        request=request,
    )
    return upstream


@actions_router.post("/{upload_id}/parts", summary="Actions wrapper for /v1/uploads/{id}/parts")
async def actions_create_upload_part(upload_id: str, payload: ActionsUploadPartRequest, request: Request) -> Response:
    max_bytes = 20 * 1024 * 1024  # 20 MiB decoded
    try:
        raw = base64.b64decode(payload.data_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 in data_base64")

    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="Empty upload part is not allowed")
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Upload part too large (>{max_bytes} bytes)")

    upstream_path = f"/v1/uploads/{upload_id}/parts"
    upstream_url = build_upstream_url(upstream_path, request=request)

    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    client = get_async_httpx_client(timeout=60.0)
    files = {
        "data": (payload.filename or "part.bin", raw, payload.mime_type or "application/octet-stream"),
    }

    try:
        resp = await client.post(upstream_url, headers=headers, files=files)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout while uploading part")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error while uploading part: {exc!r}") from exc

    return StarletteResponse(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        headers=_filter_response_headers(resp.headers),
    )


@actions_router.post("/{upload_id}/complete", summary="Actions wrapper for /v1/uploads/{id}/complete")
async def actions_complete_upload(upload_id: str, payload: ActionsUploadCompleteRequest, request: Request) -> Response:
    upstream = await forward_openai_method_path(
        "POST",
        f"/v1/uploads/{upload_id}/complete",
        json_body=payload.model_dump(),
        inbound_headers=request.headers,
        request=request,
    )
    return upstream


@actions_router.post("/{upload_id}/cancel", summary="Actions wrapper for /v1/uploads/{id}/cancel")
async def actions_cancel_upload(upload_id: str, request: Request) -> Response:
    upstream = await forward_openai_method_path(
        "POST",
        f"/v1/uploads/{upload_id}/cancel",
        json_body=None,
        inbound_headers=request.headers,
        request=request,
    )
    return upstream
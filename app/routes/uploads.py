from __future__ import annotations

import base64
from typing import Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.forward_openai import build_outbound_headers, build_upstream_url, forward_openai_method_path, forward_openai_request
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
    model_config = ConfigDict(extra="forbid")

    purpose: str = Field(..., description="Upstream upload purpose")
    filename: str = Field(..., description="Original filename")
    bytes: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    expires_after: Optional[dict] = Field(default=None, description="Optional expiration settings")


class ActionsUploadPartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    filename: str = Field(..., description="Original filename")
    mime_type: str = Field(..., description="MIME type")
    data_base64: str = Field(..., description="Base64-encoded bytes for part data")


class ActionsUploadCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_ids: List[str] = Field(..., description="Ordered list of part IDs")


def _filter_response_headers(headers: httpx.Headers) -> dict:
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
    out: dict = {}
    for k, v in headers.items():
        if k.lower() in strip:
            continue
        out[k] = v
    return out


@actions_router.post(
    "",
    operation_id="actionsUploadsCreateV1Actions",
    summary="Actions upload create (JSON)",
)
async def actions_create_upload(payload: ActionsUploadCreateRequest, request: Request) -> Response:
    return await forward_openai_method_path(
        "POST",
        "/v1/uploads",
        json_body=payload.model_dump(exclude_none=True),
        inbound_headers=request.headers,
    )


@actions_router.post(
    "/{upload_id}/parts",
    operation_id="actionsUploadsAddPartV1Actions",
    summary="Actions upload part (base64 -> multipart)",
)
async def actions_create_upload_part(upload_id: str, payload: ActionsUploadPartRequest, request: Request) -> Response:
    max_bytes = 10 * 1024 * 1024
    try:
        raw = base64.b64decode(payload.data_base64, validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid data_base64: {exc}") from exc

    if not raw:
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

    client = get_async_httpx_client()
    files = {"data": (payload.filename, raw, payload.mime_type)}

    try:
        resp = await client.post(upstream_url, headers=headers, files=files)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout while uploading part")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error while uploading part: {exc!r}") from exc

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        headers=_filter_response_headers(resp.headers),
    )


@actions_router.post(
    "/{upload_id}/complete",
    operation_id="actionsUploadsCompleteV1Actions",
    summary="Actions upload complete (JSON)",
)
async def actions_complete_upload(
    upload_id: str, payload: ActionsUploadCompleteRequest, request: Request
) -> Response:
    return await forward_openai_method_path(
        "POST",
        f"/v1/uploads/{upload_id}/complete",
        json_body=payload.model_dump(exclude_none=True),
        inbound_headers=request.headers,
    )


@actions_router.post(
    "/{upload_id}/cancel",
    operation_id="actionsUploadsCancelV1Actions",
    summary="Actions upload cancel (JSON)",
)
async def actions_cancel_upload(upload_id: str, request: Request) -> Response:
    return await forward_openai_method_path(
        "POST",
        f"/v1/uploads/{upload_id}/cancel",
        json_body={},
        inbound_headers=request.headers,
    )


ActionsUploadCreateRequest.model_rebuild()
ActionsUploadPartRequest.model_rebuild()
ActionsUploadCompleteRequest.model_rebuild()
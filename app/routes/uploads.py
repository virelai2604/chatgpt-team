from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Request, UploadFile
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_method_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["uploads"])


class UploadCreateRequest(BaseModel):
    filename: str = Field(...)
    purpose: str = Field(...)
    mime_type: str = Field(...)
    bytes: int = Field(...)


@router.post("/uploads")
async def create_upload(payload: UploadCreateRequest, request: Request):
    return await forward_openai_method_path(
        "POST",
        "/v1/uploads",
        json_body=payload.model_dump(),
        inbound_headers=request.headers,
        request=request,
    )


@router.post("/uploads/{upload_id}/parts")
async def add_upload_part(upload_id: str, file: UploadFile, request: Request):
    contents = await file.read()
    files = {"data": (file.filename or "part", contents, file.content_type or "application/octet-stream")}
    return await forward_openai_method_path(
        "POST",
        f"/v1/uploads/{upload_id}/parts",
        files=files,
        inbound_headers=request.headers,
        request=request,
    )


class UploadCompleteRequest(BaseModel):
    parts: list[str] = Field(...)


@router.post("/uploads/{upload_id}/complete")
async def complete_upload(upload_id: str, payload: UploadCompleteRequest, request: Request):
    return await forward_openai_method_path(
        "POST",
        f"/v1/uploads/{upload_id}/complete",
        json_body=payload.model_dump(),
        inbound_headers=request.headers,
        request=request,
    )


@router.post("/uploads/{upload_id}/cancel")
async def cancel_upload(upload_id: str, request: Request):
    return await forward_openai_method_path(
        "POST",
        f"/v1/uploads/{upload_id}/cancel",
        inbound_headers=request.headers,
        request=request,
    )


# Catch-all passthrough for future endpoints - keep OUT of OpenAPI schema
@router.api_route("/uploads/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
async def uploads_passthrough(path: str, request: Request):
    upstream_path = f"/v1/uploads/{path}"
    body = await request.body()
    content_type: Optional[str] = request.headers.get("content-type")
    return await forward_openai_method_path(
        request.method,
        upstream_path,
        data=body if body else None,
        content_type=content_type,
        inbound_headers=request.headers,
        request=request,
    )

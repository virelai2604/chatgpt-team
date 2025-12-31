from __future__ import annotations

import base64
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response

from app.api.forward_openai import build_outbound_headers, build_upstream_url, forward_openai_method_path, forward_openai_request
from app.core.http_client import get_async_httpx_client
from app.core.settings import get_settings

router = APIRouter(prefix="/v1", tags=["files"])


def _filter_response_headers(headers: httpx.Headers) -> Dict[str, str]:
    """
    Strip hop-by-hop / conflicting headers to avoid Starlette issues.
    Keep this local to avoid relying on internal helpers.
    """
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


async def _is_user_data_file(file_id: str, request: Request) -> bool:
    """
    Best-effort guardrail:
    - If we can confirm purpose == 'user_data', block content download.
    - If we cannot confirm (metadata fetch fails), do not introduce new 5xx.
    """
    try:
        meta = await forward_openai_method_path(
            "GET",
            f"/v1/files/{file_id}",
            inbound_headers=request.headers,
        )
    except HTTPException:
        return False
    except Exception:
        return False

    return isinstance(meta, dict) and str(meta.get("purpose", "")).strip().lower() == "user_data"


@router.get("/files")
async def list_files(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/files")
async def create_file(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/files/{file_id}/content")
async def retrieve_file_content(file_id: str, request: Request) -> Response:
    if await _is_user_data_file(file_id, request):
        return JSONResponse(
            status_code=403,
            content={"detail": "Not allowed to download files with purpose 'user_data' via this relay."},
        )
    return await forward_openai_request(request)


class ActionsFileUploadRequest(BaseModel):
    """
    Actions-friendly file upload wrapper.

    Accept JSON + base64 to avoid multipart from Actions.
    """
    model_config = ConfigDict(extra="forbid")

    purpose: str = Field(..., description="Upstream file purpose (e.g. assistants)")
    filename: str = Field(..., description="Original filename (e.g. doc.pdf)")
    mime_type: str = Field(..., description="MIME type (e.g. application/pdf)")
    data_base64: str = Field(..., description="Base64-encoded file bytes (no data: prefix)")


@router.post(
    "/actions/files/upload",
    summary="Actions-friendly JSON->multipart wrapper for /v1/files",
    operation_id="actionsFilesUploadV1",
)
async def actions_files_upload(payload: ActionsFileUploadRequest, request: Request) -> Response:
    """
    Wrapper for multipart POST /v1/files:
      - Input: JSON with base64 bytes
      - Output: upstream JSON response (file object) or upstream error
    """
    # Size guard (base64 expands ~4/3). Keep conservative to reduce memory pressure.
    # You can raise this later if needed.
    max_bytes = 10 * 1024 * 1024  # 10 MiB decoded
    try:
        raw = base64.b64decode(payload.data_base64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 in data_base64")

    if len(raw) == 0:
        raise HTTPException(status_code=400, detail="Empty file upload is not allowed")
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large for Actions wrapper (>{max_bytes} bytes)")

    upstream_path = "/v1/files"
    upstream_url = build_upstream_url(upstream_path, request=request)

    # Build auth + org/project headers; do NOT set Content-Type (httpx will set multipart boundary)
    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    settings = get_settings()
    timeout_s = float(getattr(settings, "timeout_seconds", 60.0) or 60.0)
    client = get_async_httpx_client(timeout=timeout_s)

    files = {
        "file": (payload.filename, raw, payload.mime_type),
    }
    data = {
        "purpose": payload.purpose,
    }

    try:
        resp = await client.post(upstream_url, headers=headers, data=data, files=files)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout while uploading file")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error while uploading file: {e!r}")

    # Return upstream response as-is (JSON error bodies included)
    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        headers=_filter_response_headers(resp.headers),
    )

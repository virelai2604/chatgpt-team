from __future__ import annotations

import base64
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from starlette.responses import Response as StarletteResponse

from app.api.forward_openai import build_outbound_headers, build_upstream_url, forward_openai_method_path, forward_openai_request
from app.core.http_client import get_async_httpx_client
from app.utils.logger import info

router = APIRouter(prefix="/v1", tags=["videos"])
actions_router = APIRouter(prefix="/v1/actions/videos", tags=["videos_actions"])


# --- Canonical Videos API (per OpenAI API reference) ---
#
# POST   /v1/videos                       -> create a video generation job (may be multipart)
# POST   /v1/videos/{video_id}/remix       -> remix an existing video
# GET    /v1/videos                       -> list videos
# GET    /v1/videos/{video_id}            -> retrieve a video job
# DELETE /v1/videos/{video_id}            -> delete a video job
# GET    /v1/videos/{video_id}/content    -> download generated content (binary)
#
# We implement the main paths explicitly (for clean OpenAPI + clarity), and keep a
# hidden catch-all for forward-compat endpoints that may appear later.


@router.post("/videos")
async def create_video(request: Request):
    """Create a new video generation job (JSON or multipart/form-data)."""
    info("→ [videos.create] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/videos/generations", deprecated=True)
async def create_video_legacy_generations(request: Request):
    """Legacy alias: historically `/v1/videos/generations` in older relays.

    The current OpenAI API uses `POST /v1/videos`. We forward this endpoint to
    the canonical path for compatibility.
    """
    info("→ [videos.legacy_generations] %s %s", request.method, request.url.path)
    return await forward_openai_method_path("POST", "/v1/videos", request)


@router.post("/videos/{video_id}/remix")
async def remix_video(video_id: str, request: Request):
    """Create a remix of an existing video job."""
    info("→ [videos.remix] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos")
async def list_videos(request: Request):
    """List video jobs."""
    info("→ [videos.list] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}")
async def retrieve_video(video_id: str, request: Request):
    """Retrieve a single video job."""
    info("→ [videos.retrieve] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str, request: Request):
    """Delete a single video job."""
    info("→ [videos.delete] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}/content")
async def download_video_content(video_id: str, request: Request):
    """Download generated content (binary) for a video job."""
    info("→ [videos.content] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# Forward-compat / extra endpoints (hidden from OpenAPI schema)
@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "PUT", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def videos_passthrough(path: str, request: Request):
    info("→ [videos/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


class ActionsVideoCreateRequest(BaseModel):
    """Actions-friendly multipart wrapper for /v1/videos."""

    model_config = ConfigDict(extra="forbid")

    prompt: Optional[str] = Field(default=None, description="Prompt for video generation")
    model: Optional[str] = Field(default=None, description="Model ID")
    data_base64: Optional[str] = Field(default=None, description="Base64-encoded input image/video bytes")
    filename: Optional[str] = Field(default="input.bin", description="Input filename")
    mime_type: Optional[str] = Field(default="application/octet-stream", description="Input MIME type")
    file_field: Optional[str] = Field(default="image", description="Multipart field name for the file")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Additional form fields to pass through")


def _as_str_form_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    return str(value)


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


@actions_router.post("", summary="Actions wrapper for /v1/videos (multipart)")
async def actions_create_video(payload: ActionsVideoCreateRequest, request: Request) -> Response:
    form: Dict[str, str] = {}
    if payload.model:
        form["model"] = _as_str_form_value(payload.model)
    if payload.prompt:
        form["prompt"] = _as_str_form_value(payload.prompt)
    if payload.params:
        for k, v in payload.params.items():
            if v is None:
                continue
            form[str(k)] = _as_str_form_value(v)

    file_bytes: Optional[bytes] = None
    if payload.data_base64:
        try:
            file_bytes = base64.b64decode(payload.data_base64, validate=True)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 in data_base64")

    if not form and file_bytes is None:
        raise HTTPException(status_code=400, detail="At least one of prompt, params, or data_base64 is required")

    upstream_path = "/v1/videos"
    upstream_url = build_upstream_url(upstream_path, request=request)
    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    files = None
    if file_bytes is not None:
        if len(file_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty data_base64 is not allowed")
        files = {
            payload.file_field or "image": (
                payload.filename or "input.bin",
                file_bytes,
                payload.mime_type or "application/octet-stream",
            )
        }

    client = get_async_httpx_client(timeout=90.0)
    try:
        resp = await client.post(upstream_url, headers=headers, data=form, files=files)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout while creating video")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error while creating video: {exc!r}") from exc

    return StarletteResponse(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        headers=_filter_response_headers(resp.headers),
    )
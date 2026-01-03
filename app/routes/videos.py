from __future__ import annotations

import base64
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.api.forward_openai import (
    build_outbound_headers,
    build_upstream_url,
    forward_openai_method_path,
    forward_openai_request,
)
from app.core.http_client import get_async_httpx_client
from app.models.error import ErrorResponse
from app.utils.logger import info

router = APIRouter(prefix="/v1", tags=["videos"])
actions_router = APIRouter(prefix="/v1/actions/videos", tags=["videos_actions"])

_MAX_VIDEO_BYTES = 25 * 1024 * 1024
_MAX_DURATION_SECONDS = 30
_MAX_FRAMES = 300
_ALLOWED_VIDEO_MODELS = {"sora-2", "sora-2-pro"}
_ALLOWED_VIDEO_SECONDS = {4, 8, 12}
_ALLOWED_VIDEO_SIZES = {"720x1280", "1280x720", "1024x1792", "1792x1024"}


# Canonical Videos API (per OpenAI API reference)
# - POST /v1/videos -> create a video generation job (may be multipart)
# - POST /v1/videos/{video_id}/remix -> remix an existing video
# - GET /v1/videos -> list videos
# - GET /v1/videos/{video_id} -> retrieve a video job
# - DELETE /v1/videos/{video_id} -> delete a video job
# - GET /v1/videos/{video_id}/content -> download generated content (binary)
#
# We implement main paths explicitly (clean OpenAPI + clarity),
# and keep a hidden catch-all for forward-compat endpoints.


@router.post("/videos")
async def create_video(request: Request) -> Response:
    """Create a new video generation job (JSON or multipart/form-data)."""
    info("→ [videos.create] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/videos/generations", deprecated=True)
async def create_video_legacy_generations(request: Request) -> Response:
    """
    Legacy alias: historically /v1/videos/generations in older relays.

    The current OpenAI API uses POST /v1/videos. We forward this endpoint to
    the canonical path for compatibility.
    """
    info("→ [videos.legacy_generations] %s %s", request.method, request.url.path)
    return await forward_openai_method_path(
        "POST",
        "/v1/videos",
        inbound_headers=request.headers,
        request=request,
    )


@router.post("/videos/{video_id}/remix")
async def remix_video(video_id: str, request: Request) -> Response:
    """Create a remix of an existing video job."""
    info("→ [videos.remix] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos")
async def list_videos(request: Request) -> Response:
    """List video jobs."""
    info("→ [videos.list] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}")
async def retrieve_video(video_id: str, request: Request) -> Response:
    """Retrieve a single video job."""
    info("→ [videos.retrieve] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.delete("/videos/{video_id}")
async def delete_video(video_id: str, request: Request) -> Response:
    """Delete a single video job."""
    info("→ [videos.delete] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/videos/{video_id}/content")
async def download_video_content(video_id: str, request: Request) -> Response:
    """Download generated content (binary) for a video job."""
    info("→ [videos.content] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "PUT", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def videos_passthrough(path: str, request: Request) -> Response:
    """Forward-compat / extra endpoints (hidden from OpenAPI schema)."""
    info("→ [videos/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


class ActionsVideoGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: Optional[str] = Field(default=None, description="Text prompt for video generation")
    model: Optional[str] = Field(default=None, description="Model name")
    size: Optional[str] = Field(default=None, description="Output size (e.g., 720x1280)")
    seconds: Optional[int] = Field(default=None, description="Clip duration in seconds")
    duration_seconds: Optional[int] = Field(default=None, description="Duration in seconds (legacy)")
    frames: Optional[int] = Field(default=None, description="Frame count (legacy)")
    data_base64: Optional[str] = Field(default=None, description="Optional base64-encoded input video")
    input_reference_base64: Optional[str] = Field(
        default=None,
        description="Optional base64-encoded input reference (alias for data_base64)",
    )
    filename: Optional[str] = Field(default="input.mp4", description="Input filename")
    mime_type: Optional[str] = Field(default="video/mp4", description="Input MIME type")


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


def _error_response(
    message: str,
    *,
    status_code: int = 400,
    param: Optional[str] = None,
    code: Optional[str] = None,
) -> Response:
    return ErrorResponse.from_message(
        message,
        param=param,
        code=code,
    ).to_response(status_code=status_code)


@actions_router.post(
    "",
    operation_id="actionsVideosCreateV1Actions",
    summary="Actions wrapper for /v1/videos",
)
async def actions_create_video(request: Request) -> Response:
    info("→ [actions.videos.create] %s %s", request.method, request.url.path)
    return await forward_openai_request(request, upstream_path="/v1/videos")


@actions_router.post(
    "/{video_id}/remix",
    operation_id="actionsVideosRemixV1Actions",
    summary="Actions wrapper for /v1/videos/{video_id}/remix",
)
async def actions_remix_video(video_id: str, request: Request) -> Response:
    info("→ [actions.videos.remix] %s %s", request.method, request.url.path)
    return await forward_openai_request(request, upstream_path=f"/v1/videos/{video_id}/remix")


@actions_router.post(
    "/generations",
    operation_id="actionsVideosGenerationsV1Actions",
    summary="Actions wrapper for /v1/videos/generations (multipart)",
)
async def actions_generate_video(payload: ActionsVideoGenerationRequest, request: Request) -> Response:
    if not payload.prompt:
        return _error_response(
            "prompt is required",
            param="prompt",
        )

    if payload.model is not None and payload.model not in _ALLOWED_VIDEO_MODELS:
        return _error_response(
            f"model must be one of: {', '.join(sorted(_ALLOWED_VIDEO_MODELS))}",
            param="model",
        )

    if payload.size is not None and payload.size not in _ALLOWED_VIDEO_SIZES:
        return _error_response(
            f"size must be one of: {', '.join(sorted(_ALLOWED_VIDEO_SIZES))}",
            param="size",
        )

    seconds_value = payload.seconds if payload.seconds is not None else payload.duration_seconds
    if seconds_value is not None and seconds_value not in _ALLOWED_VIDEO_SECONDS:
        return _error_response(
            f"seconds must be one of: {', '.join(str(s) for s in sorted(_ALLOWED_VIDEO_SECONDS))}",
            param="seconds",
        )

    if payload.duration_seconds is not None and payload.duration_seconds > _MAX_DURATION_SECONDS:
        return _error_response(
            f"duration_seconds exceeds {_MAX_DURATION_SECONDS}",
            param="duration_seconds",
        )
    if payload.frames is not None and payload.frames > _MAX_FRAMES:
        return _error_response(
            f"frames exceeds {_MAX_FRAMES}",
            param="frames",
        )

    raw: bytes | None = None
    base64_source = payload.data_base64 if payload.data_base64 is not None else payload.input_reference_base64
    if base64_source is not None:
        try:
            raw = base64.b64decode(base64_source, validate=True)
        except Exception as exc:
            return _error_response(
                f"Invalid data_base64: {exc}",
                param="data_base64",
            )

    if raw is not None:
        if len(raw) == 0:
            return _error_response(
                "Empty input video is not allowed",
                param="data_base64",
            )
        if len(raw) > _MAX_VIDEO_BYTES:
            return _error_response(
                f"Input video too large (>{_MAX_VIDEO_BYTES} bytes)",
                status_code=413,
                param="data_base64",
                code="input_too_large",
            )

    upstream_path = "/v1/videos/generations"
    upstream_url = build_upstream_url(upstream_path, request=request)
    headers = build_outbound_headers(
        inbound_headers=request.headers,
        content_type=None,
        forward_accept=True,
        path_hint=upstream_path,
    )

    data: dict[str, str] = {}
    if payload.prompt:
        data["prompt"] = payload.prompt
    if payload.model:
        data["model"] = payload.model
    if payload.size:
        data["size"] = payload.size
    if payload.duration_seconds is not None:
        data["duration_seconds"] = str(payload.duration_seconds)
    if payload.seconds is not None:
        data["seconds"] = str(payload.seconds)
    if payload.frames is not None:
        data["frames"] = str(payload.frames)

    files = None
    if raw is not None:
        files = {
            "file": (payload.filename or "input.mp4", raw, payload.mime_type or "video/mp4"),
        }

    client = get_async_httpx_client()
    try:
        resp = await client.post(upstream_url, headers=headers, data=data, files=files)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream timeout while generating video")
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error while generating video: {exc!r}") from exc

    return Response(
        content=resp.content,
        status_code=resp.status_code,
        media_type=resp.headers.get("content-type"),
        headers=_filter_response_headers(resp.headers),
    )


ActionsVideoGenerationRequest.model_rebuild()

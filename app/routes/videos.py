from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_method_path, forward_openai_request
from app.utils.logger import info

router = APIRouter(prefix="/v1", tags=["videos"])
actions_router = APIRouter(prefix="/v1/actions/videos", tags=["videos_actions"])

# -----------------------------------------------------------------------------
# Canonical Videos API (per OpenAI API reference)
#
# POST   /v1/videos                 -> create a video generation job (may be multipart)
# POST   /v1/videos/{video_id}/remix -> remix an existing video
# GET    /v1/videos                 -> list videos
# GET    /v1/videos/{video_id}      -> retrieve a video job
# DELETE /v1/videos/{video_id}      -> delete a video job
# GET    /v1/videos/{video_id}/content -> download generated content (binary)
#
# We implement the main paths explicitly (for clean OpenAPI + clarity), and keep a
# hidden catch-all for forward-compat endpoints that may appear later.
# -----------------------------------------------------------------------------


@router.post("/videos")
async def create_video(request: Request):
    """Create a new video generation job (JSON or multipart/form-data)."""
    info("→ [videos.create] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/videos/generations", deprecated=True)
async def create_video_legacy_generations(request: Request):
    """Legacy alias: historically /v1/videos/generations in older relays.

    The current OpenAI API uses `POST /v1/videos`. We forward this endpoint to
    the canonical path for compatibility.
    """
    info("→ [videos.legacy_generations] %s %s", request.method, request.url.path)
    # forward_openai_method_path expects (method, path, request)
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


# -----------------------------------------------------------------------------
# Forward-compat / extra endpoints (hidden from OpenAPI schema)
# -----------------------------------------------------------------------------
@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "PUT", "HEAD", "OPTIONS"],
    include_in_schema=False,
)
async def videos_passthrough(path: str, request: Request):
    info("→ [videos/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# -----------------------------------------------------------------------------
# Actions wrappers: stable JSON-friendly surface for Actions clients
# -----------------------------------------------------------------------------
@actions_router.post(
    "",
    operation_id="actionsVideosCreate",
    summary="Actions wrapper for /v1/videos",
)
async def actions_create_video(request: Request):
    info("→ [actions.videos.create] %s %s", request.method, request.url.path)
    return await forward_openai_request(request, upstream_path="/v1/videos")


@actions_router.post(
    "/{video_id}/remix",
    operation_id="actionsVideosRemix",
    summary="Actions wrapper for /v1/videos/{video_id}/remix",
)
async def actions_remix_video(video_id: str, request: Request):
    info("→ [actions.videos.remix] %s %s", request.method, request.url.path)
    return await forward_openai_request(request, upstream_path=f"/v1/videos/{video_id}/remix")

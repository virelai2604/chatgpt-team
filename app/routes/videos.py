# app/routes/videos.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
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


@router.api_route("/videos", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_videos_root(request: Request) -> Response:
    """
    Root videos endpoint.

    Covers:
      - GET  /v1/videos   (list videos – smoke test allows 200 or 404)
      - POST /v1/videos   (future‑proofing)

    The forwarding helper will build the upstream URL from the path,
    so for GET it becomes:

      GET {OPENAI_BASE_URL}/videos
    """
    logger.info("→ [videos] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/videos/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_videos_subpaths(path: str, request: Request) -> Response:
    """
    Catch‑all for video subresources.

    This is what drives the "extra" tests in:

      - test_video_metadata_forward        (GET /v1/videos/{video_id})
      - test_video_content_forward         (GET /v1/videos/{video_id}/content)
      - test_video_delete_forward_error_passthrough (DELETE /v1/videos/{video_id})
      - test_video_retrieve_forward        (smoke / metadata)
      - test_videos_list_forward           (via root + subpaths)

    Behaviour required by tests:
      * Status code from upstream is preserved (200, 404, etc.)
      * JSON bodies are passed through unchanged for metadata / errors
      * Binary bodies & headers are preserved for /content downloads

    All of this is handled centrally by `forward_openai_request`.
    """
    logger.info("→ [videos/*] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)

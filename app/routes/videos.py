"""
videos.py — /v1/videos proxy
─────────────────────────────
Thin, OpenAI-compatible proxy for video generation and retrieval
(Sora-style Video API).

Typical upstream operations:

  • POST   /v1/videos                 → create video job
  • GET    /v1/videos                 → list videos
  • GET    /v1/videos/{video_id}      → get job status / metadata
  • GET    /v1/videos/{video_id}/content
                                     → download video bytes (e.g. MP4)
  • DELETE /v1/videos/{video_id}      → delete a stored video (when supported)

We do not interpret or transform the payloads here. All behavior is
delegated to `forward_openai_request` so your relay stays aligned
with the official OpenAI Video API and the openai-python SDK.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["videos"],
)


@router.api_route("/videos", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_videos_root(request: Request):
    """
    /v1/videos

    GET:
      List video jobs associated with the authenticated project/org.

    POST:
      Create a new video generation job (e.g. Sora model), with a body
      similar to:

          {
            "model": "sora-2",
            "prompt": "...",
            "seconds": 8,
            "size": "720x1280",
            ...
          }

    We forward the request directly to the upstream OpenAI /v1/videos
    endpoint via `forward_openai_request`.
    """
    logger.info("→ [videos] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route("/videos/{path:path}", methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"])
async def proxy_videos_subpaths(path: str, request: Request):
    """
    /v1/videos/{...} — catch-all for video sub-resources.

    This route covers subpaths such as:

      • GET    /v1/videos/{video_id}
           → Retrieve job status / metadata.

      • GET    /v1/videos/{video_id}/content
           → Download the completed video file.

      • DELETE /v1/videos/{video_id}
           → Delete a video (subject to upstream support).

      • Any future control or remix endpoints under /v1/videos/*.

    The relay makes no assumptions about the semantics; it simply
    forwards the full request to OpenAI via `forward_openai_request`.
    """
    logger.info(
        "→ [videos] %s %s (subpath=%s)",
        request.method,
        request.url.path,
        path,
    )
    return await forward_openai_request(request)

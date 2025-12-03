from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["chatkit"],
)


@router.api_route("/chatkit", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def proxy_chatkit_root(request: Request) -> Response:
    """
    Generic proxy for /v1/chatkit.

    This keeps the relay forward-compatible with new ChatKit endpoints
    without needing to hard-code each subresource.
    """
    logger.info("→ [chatkit] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/chatkit/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_chatkit_subpaths(path: str, request: Request) -> Response:
    """
    Generic proxy for any /v1/chatkit/* sub-path.
    """
    logger.info("→ [chatkit/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

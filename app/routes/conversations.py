# app/routes/conversations.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["conversations"],
)


@router.api_route(
    "/conversations",
    methods=["GET", "POST", "HEAD", "OPTIONS"],
)
async def conversations_root(request: Request) -> Response:
    """
    - GET /v1/conversations      → list conversations
    - POST /v1/conversations     → create conversation
    """
    logger.info("→ [conversations] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/conversations/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "PUT", "HEAD", "OPTIONS"],
)
async def conversations_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for /v1/conversations/*, e.g.:

      - /v1/conversations/{conversation_id}
      - /v1/conversations/{conversation_id}/items
      - /v1/conversations/{conversation_id}/items/{item_id}
    """
    logger.info("→ [conversations/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

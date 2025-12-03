# app/routes/conversations.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["conversations"],
)


@router.api_route("/conversations", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_conversations_root(request: Request) -> Response:
    """
    Conversations root.

    Covers:
      - GET  /v1/conversations  (list)
      - POST /v1/conversations  (create)
    """
    logger.info("→ [conversations] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/conversations/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_conversations_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for Conversations subresources.

    Examples:
      - GET    /v1/conversations/{conversation_id}
      - POST   /v1/conversations/{conversation_id}              (update)
      - DELETE /v1/conversations/{conversation_id}              (delete)
      - GET    /v1/conversations/{conversation_id}/items        (list items)
      - POST   /v1/conversations/{conversation_id}/items        (create item)
      - GET    /v1/conversations/{conversation_id}/items/{id}   (retrieve item)
      - DELETE /v1/conversations/{conversation_id}/items/{id}   (delete item)
      - future /v1/conversations/* additions
    """
    logger.info("→ [conversations/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

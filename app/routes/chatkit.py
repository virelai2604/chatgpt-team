# app/routes/chatkit.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1/chatkit",
    tags=["chatkit"],
)


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_chatkit(path: str, request: Request) -> Response:
    """
    Catch-all proxy for the OpenAI ChatKit REST API.

    Examples forwarded upstream as-is:
      - GET  /v1/chatkit/threads
      - GET  /v1/chatkit/threads/{thread_id}
      - GET  /v1/chatkit/threads/{thread_id}/items
      - POST /v1/chatkit/sessions
      - POST /v1/chatkit/sessions/{session_id}/cancel
      - (Any future /v1/chatkit/* endpoints)

    The OpenAI-Beta: chatkit_beta=v1 header is preserved by forward_openai_request.
    """
    logger.info("[chatkit] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

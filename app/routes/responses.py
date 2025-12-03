# app/routes/responses.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["responses"])


@router.post("/responses")
async def create_response(request: Request) -> Response:
    """
    POST /v1/responses – main chat/agent entrypoint.
    Streaming is handled via Accept: text/event-stream by forward_openai_request.
    """
    logger.info("→ [responses] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/responses/{path:path}",
    methods=["GET", "POST", "DELETE", "HEAD", "OPTIONS"],
)
async def proxy_responses_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for /v1/responses/*, e.g.:

      - /v1/responses/{id}
      - /v1/responses/{id}/cancel
      - /v1/responses/{id}/input_token_counts
      - /v1/responses/{id}/output_items
    """
    logger.info("→ [responses/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

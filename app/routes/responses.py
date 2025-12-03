# app/routes/responses.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["responses"],
)


@router.api_route("/responses", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def proxy_responses_root(request: Request) -> Response:
    """
    Generic proxy for the Responses API root.

    Covers:
      - POST /v1/responses        (create response; JSON or SSE stream)
      - GET  /v1/responses        (future-safe)
    """
    logger.info("→ [responses] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/responses/{path:path}",
    methods=["GET", "POST", "DELETE", "PATCH", "HEAD", "OPTIONS"],
)
async def proxy_responses_subpaths(path: str, request: Request) -> Response:
    """
    Catch-all for all other Responses subpaths.

    Examples:
      - GET    /v1/responses/{response_id}
      - DELETE /v1/responses/{response_id}
      - POST   /v1/responses/{response_id}/cancel
      - GET    /v1/responses/{response_id}/input_token_counts
      - any future /v1/responses/* additions
    """
    logger.info("→ [responses/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

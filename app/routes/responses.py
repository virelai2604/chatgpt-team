from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["responses"],
)


@router.api_route("/responses", methods=["GET", "POST"])
async def proxy_responses_root(request: Request):
    """
    Thin relay over the OpenAI /v1/responses root.

    This endpoint intentionally does NOT implement any custom business logic.
    It simply forwards the request to the upstream OpenAI API via
    `forward_openai_request`, which handles:

    - Authorization and organization headers
    - Optional OpenAI-Beta headers
    - JSON vs SSE streaming responses
    - Error normalization into OpenAI-style error objects
    """
    logger.info("→ [responses] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route("/responses/{path:path}", methods=["GET", "POST", "DELETE", "PATCH"])
async def proxy_responses_subpaths(path: str, request: Request):
    """
    Catch-all proxy for any sub-resource under /v1/responses/*.

    This ensures we automatically support new Responses API endpoints
    (e.g., /v1/responses/{id}/cancel, /v1/responses/{id}/input_items, etc.)
    without needing to constantly update the relay as the API evolves.
    """
    logger.info("→ [responses] %s %s (subpath=%s)", request.method, request.url.path, path)
    return await forward_openai_request(request)

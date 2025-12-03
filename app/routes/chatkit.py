# app/routes/chatkit.py
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger  # type: ignore

router = APIRouter(
    prefix="/v1",
    tags=["chatkit"],
)


@router.api_route(
    "/chatkit",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def chatkit_root_proxy(request: Request) -> Response:
    """
    Generic proxy for /v1/chatkit.

    ChatKit is primarily a client framework, but the OpenAI docs expose
    ChatKit-related API surfaces under /v1/chatkit*. This relay forwards
    them 1:1 to the upstream OpenAI API.
    """
    logger.info("[chatkit] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/chatkit/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def chatkit_proxy(path: str, request: Request) -> Response:
    """
    Catch-all proxy for any nested /v1/chatkit/* path.
    """
    logger.info("[chatkit] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

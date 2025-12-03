# app/routes/containers.py
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger  # type: ignore

router = APIRouter(
    prefix="/v1",
    tags=["containers"],
)


@router.api_route(
    "/containers",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def containers_root_proxy(request: Request) -> Response:
    """
    Generic proxy for /v1/containers.

    Covers list/create operations for containers as defined in the
    OpenAI Containers API reference.
    """
    logger.info("[containers] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/containers/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
)
async def containers_proxy(path: str, request: Request) -> Response:
    """
    Catch-all proxy for any nested /v1/containers/* path, including
    endpoints like /v1/containers/{id}, /v1/containers/file, etc.
    """
    logger.info("[containers] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

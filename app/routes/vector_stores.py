from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["vector_stores"])

_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@router.api_route("/v1/vector_stores", methods=_METHODS)
async def vector_stores_root(request: Request) -> Response:
    return await forward_openai_request(request)


@router.api_route("/v1/vector_stores/{path:path}", methods=_METHODS)
async def vector_stores_subpaths(path: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.api_route("/vector_stores", methods=_METHODS, include_in_schema=False)
async def vector_stores_root_alias(request: Request) -> Response:
    return await forward_openai_request(request)


@router.api_route("/vector_stores/{path:path}", methods=_METHODS, include_in_schema=False)
async def vector_stores_subpaths_alias(path: str, request: Request) -> Response:
    return await forward_openai_request(request)

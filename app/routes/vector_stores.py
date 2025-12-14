from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["vector_stores"])

# OpenAI API (canonical): /v1/vector_stores ...
# Backwards-compatible alias maintained at /vector_stores ... (not in schema).
_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@router.api_route("/v1/vector_stores", methods=_METHODS)
async def vector_stores_root(request: Request) -> Response:
    """Forward /v1/vector_stores to upstream OpenAI."""
    return await forward_openai_request(request)


@router.api_route("/v1/vector_stores/{path:path}", methods=_METHODS)
async def vector_stores_subpaths(path: str, request: Request) -> Response:
    """Forward /v1/vector_stores/* subroutes to upstream OpenAI."""
    return await forward_openai_request(request)


@router.api_route("/vector_stores", methods=_METHODS, include_in_schema=False)
async def vector_stores_root_alias(request: Request) -> Response:
    """Legacy alias (pre-/v1): /vector_stores -> upstream /v1/vector_stores."""
    return await forward_openai_request(request)


@router.api_route("/vector_stores/{path:path}", methods=_METHODS, include_in_schema=False)
async def vector_stores_subpaths_alias(path: str, request: Request) -> Response:
    """Legacy alias (pre-/v1): /vector_stores/* -> upstream /v1/vector_stores/*."""
    return await forward_openai_request(request)

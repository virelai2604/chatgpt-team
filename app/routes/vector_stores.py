from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["vector_stores"])


async def _forward(request: Request) -> Response:
    return await forward_openai_request(request)


# ---- /v1/vector_stores (split methods to avoid duplicate operationId) ----
@router.get("/v1/vector_stores")
async def vector_stores_root_get(request: Request) -> Response:
    return await _forward(request)


@router.post("/v1/vector_stores")
async def vector_stores_root_post(request: Request) -> Response:
    return await _forward(request)


@router.put("/v1/vector_stores")
async def vector_stores_root_put(request: Request) -> Response:
    return await _forward(request)


@router.patch("/v1/vector_stores")
async def vector_stores_root_patch(request: Request) -> Response:
    return await _forward(request)


@router.delete("/v1/vector_stores")
async def vector_stores_root_delete(request: Request) -> Response:
    return await _forward(request)


# ---- /v1/vector_stores/{path:path} (split methods to avoid duplicate operationId) ----
@router.get("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_get(path: str, request: Request) -> Response:
    return await _forward(request)


@router.post("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_post(path: str, request: Request) -> Response:
    return await _forward(request)


@router.put("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_put(path: str, request: Request) -> Response:
    return await _forward(request)


@router.patch("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_patch(path: str, request: Request) -> Response:
    return await _forward(request)


@router.delete("/v1/vector_stores/{path:path}")
async def vector_stores_subpaths_delete(path: str, request: Request) -> Response:
    return await _forward(request)


# ---- Alias paths (kept hidden from OpenAPI) ----
_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@router.api_route("/vector_stores", methods=_METHODS, include_in_schema=False)
async def vector_stores_root_alias(request: Request) -> Response:
    return await _forward(request)


@router.api_route("/vector_stores/{path:path}", methods=_METHODS, include_in_schema=False)
async def vector_stores_subpaths_alias(path: str, request: Request) -> Response:
    return await _forward(request)

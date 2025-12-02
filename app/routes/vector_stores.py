# app/routes/vector_stores.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["vector_stores"],
)


# ---------------------------------------------------------------------------
# Vector Stores – https://platform.openai.com/docs/api-reference/vector-stores
# ---------------------------------------------------------------------------


@router.get("/vector_stores")
async def list_vector_stores(request: Request) -> Response:
    logger.info("[vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/vector_stores")
async def create_vector_store(request: Request) -> Response:
    logger.info("[vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/vector_stores/{vector_store_id}")
async def retrieve_vector_store(vector_store_id: str, request: Request) -> Response:
    logger.info("[vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/vector_stores/{vector_store_id}")
async def update_vector_store(vector_store_id: str, request: Request) -> Response:
    """
    POST /v1/vector_stores/{vector_store_id}

    Update a vector store (e.g. metadata).
    """
    logger.info("[vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.delete("/vector_stores/{vector_store_id}")
async def delete_vector_store(vector_store_id: str, request: Request) -> Response:
    """
    DELETE /v1/vector_stores/{vector_store_id}

    Delete a vector store.
    """
    logger.info("[vector_stores] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# ---------------------------------------------------------------------------
# Vector Store Files – https://platform.openai.com/docs/api-reference/vector-stores-files
# ---------------------------------------------------------------------------


@router.get("/vector_stores/{vector_store_id}/files")
async def list_vector_store_files(
    vector_store_id: str,
    request: Request,
) -> Response:
    logger.info("[vector_store_files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/vector_stores/{vector_store_id}/files")
async def create_vector_store_file(
    vector_store_id: str,
    request: Request,
) -> Response:
    logger.info("[vector_store_files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/vector_stores/{vector_store_id}/files/{file_id}")
async def retrieve_vector_store_file(
    vector_store_id: str,
    file_id: str,
    request: Request,
) -> Response:
    logger.info("[vector_store_files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.delete("/vector_stores/{vector_store_id}/files/{file_id}")
async def delete_vector_store_file(
    vector_store_id: str,
    file_id: str,
    request: Request,
) -> Response:
    logger.info("[vector_store_files] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# ---------------------------------------------------------------------------
# Vector Store File Batches – https://platform.openai.com/docs/api-reference/vector-stores-file-batches
# ---------------------------------------------------------------------------


@router.post("/vector_stores/{vector_store_id}/file_batches")
async def create_vector_store_file_batch(
    vector_store_id: str,
    request: Request,
) -> Response:
    logger.info("[vector_store_file_batches] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/vector_stores/{vector_store_id}/file_batches/{batch_id}")
async def retrieve_vector_store_file_batch(
    vector_store_id: str,
    batch_id: str,
    request: Request,
) -> Response:
    logger.info("[vector_store_file_batches] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

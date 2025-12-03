from __future__ import annotations

import logging

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["vector_stores"],
)


# --- Core vector store operations -------------------------------------------------


@router.post("/vector_stores")
async def create_vector_store(request: Request) -> Response:
    """
    POST /v1/vector_stores

    Create a vector store.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores/create
    """
    logger.debug("Proxying POST /v1/vector_stores to OpenAI")
    return await forward_openai_request(request)


@router.get("/vector_stores")
async def list_vector_stores(request: Request) -> Response:
    """
    GET /v1/vector_stores

    List vector stores.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores/list
    """
    logger.debug("Proxying GET /v1/vector_stores to OpenAI")
    return await forward_openai_request(request)


@router.get("/vector_stores/{vector_store_id}")
async def retrieve_vector_store(
    vector_store_id: str,
    request: Request,
) -> Response:
    """
    GET /v1/vector_stores/{vector_store_id}

    Retrieve a vector store.
    """
    logger.debug(
        "Proxying GET /v1/vector_stores/%s to OpenAI",
        vector_store_id,
    )
    return await forward_openai_request(request)


@router.post("/vector_stores/{vector_store_id}")
async def update_vector_store(
    vector_store_id: str,
    request: Request,
) -> Response:
    """
    POST /v1/vector_stores/{vector_store_id}

    Update a vector store (metadata / expiration).
    """
    logger.debug(
        "Proxying POST /v1/vector_stores/%s to OpenAI",
        vector_store_id,
    )
    return await forward_openai_request(request)


@router.delete("/vector_stores/{vector_store_id}")
async def delete_vector_store(
    vector_store_id: str,
    request: Request,
) -> Response:
    """
    DELETE /v1/vector_stores/{vector_store_id}

    Delete a vector store.
    """
    logger.debug(
        "Proxying DELETE /v1/vector_stores/%s to OpenAI",
        vector_store_id,
    )
    return await forward_openai_request(request)


@router.post("/vector_stores/{vector_store_id}/search")
async def search_vector_store(
    vector_store_id: str,
    request: Request,
) -> Response:
    """
    POST /v1/vector_stores/{vector_store_id}/search

    Search within a vector store.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores/search
    """
    logger.debug(
        "Proxying POST /v1/vector_stores/%s/search to OpenAI",
        vector_store_id,
    )
    return await forward_openai_request(request)


# --- Vector store files -----------------------------------------------------------


@router.get("/vector_stores/{vector_store_id}/files")
async def list_vector_store_files(
    vector_store_id: str,
    request: Request,
) -> Response:
    """
    GET /v1/vector_stores/{vector_store_id}/files

    List files attached to a vector store.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores-files/list
    """
    logger.debug(
        "Proxying GET /v1/vector_stores/%s/files to OpenAI",
        vector_store_id,
    )
    return await forward_openai_request(request)


@router.post("/vector_stores/{vector_store_id}/files")
async def create_vector_store_file(
    vector_store_id: str,
    request: Request,
) -> Response:
    """
    POST /v1/vector_stores/{vector_store_id}/files

    Attach a file to a vector store.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores-files/create
    """
    logger.debug(
        "Proxying POST /v1/vector_stores/%s/files to OpenAI",
        vector_store_id,
    )
    return await forward_openai_request(request)


@router.get("/vector_stores/{vector_store_id}/files/{file_id}")
async def retrieve_vector_store_file(
    vector_store_id: str,
    file_id: str,
    request: Request,
) -> Response:
    """
    GET /v1/vector_stores/{vector_store_id}/files/{file_id}

    Retrieve metadata for a vector store file.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores-files/retrieve
    """
    logger.debug(
        "Proxying GET /v1/vector_stores/%s/files/%s to OpenAI",
        vector_store_id,
        file_id,
    )
    return await forward_openai_request(request)


@router.delete("/vector_stores/{vector_store_id}/files/{file_id}")
async def delete_vector_store_file(
    vector_store_id: str,
    file_id: str,
    request: Request,
) -> Response:
    """
    DELETE /v1/vector_stores/{vector_store_id}/files/{file_id}

    Remove a file from a vector store.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores-files/delete
    """
    logger.debug(
        "Proxying DELETE /v1/vector_stores/%s/files/%s to OpenAI",
        vector_store_id,
        file_id,
    )
    return await forward_openai_request(request)


# --- Vector store file batches ----------------------------------------------------


@router.get("/vector_stores/{vector_store_id}/file_batches")
async def list_vector_store_file_batches(
    vector_store_id: str,
    request: Request,
) -> Response:
    """
    GET /v1/vector_stores/{vector_store_id}/file_batches

    List file batches for a vector store.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores-file-batches/list
    """
    logger.debug(
        "Proxying GET /v1/vector_stores/%s/file_batches to OpenAI",
        vector_store_id,
    )
    return await forward_openai_request(request)


@router.post("/vector_stores/{vector_store_id}/file_batches")
async def create_vector_store_file_batch(
    vector_store_id: str,
    request: Request,
) -> Response:
    """
    POST /v1/vector_stores/{vector_store_id}/file_batches

    Create a batch of files to add to a vector store.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores-file-batches/create
    """
    logger.debug(
        "Proxying POST /v1/vector_stores/%s/file_batches to OpenAI",
        vector_store_id,
    )
    return await forward_openai_request(request)


@router.get("/vector_stores/{vector_store_id}/file_batches/{batch_id}")
async def retrieve_vector_store_file_batch(
    vector_store_id: str,
    batch_id: str,
    request: Request,
) -> Response:
    """
    GET /v1/vector_stores/{vector_store_id}/file_batches/{batch_id}

    Retrieve details of a file batch.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores-file-batches/retrieve
    """
    logger.debug(
        "Proxying GET /v1/vector_stores/%s/file_batches/%s to OpenAI",
        vector_store_id,
        batch_id,
    )
    return await forward_openai_request(request)


@router.post("/vector_stores/{vector_store_id}/file_batches/{batch_id}/cancel")
async def cancel_vector_store_file_batch(
    vector_store_id: str,
    batch_id: str,
    request: Request,
) -> Response:
    """
    POST /v1/vector_stores/{vector_store_id}/file_batches/{batch_id}/cancel

    Cancel a file batch.
    Mirrors:
    https://platform.openai.com/docs/api-reference/vector-stores-file-batches/cancel
    """
    logger.debug(
        "Proxying POST /v1/vector_stores/%s/file_batches/%s/cancel to OpenAI",
        vector_store_id,
        batch_id,
    )
    return await forward_openai_request(request)


# --- Catch-all safeguard for any future nested routes ----------------------------


@router.api_route("/vector_stores/{path:path}", methods=["GET", "POST", "DELETE"])
async def proxy_vector_store_catch_all(path: str, request: Request) -> Response:
    """
    Catch-all proxy for any future vector store sub-routes not explicitly mapped above.
    This keeps the relay resilient to minor API surface expansions.
    """
    logger.debug(
        "Proxying %s /v1/vector_stores/%s (catch-all) to OpenAI",
        request.method,
        path,
    )
    return await forward_openai_request(request)

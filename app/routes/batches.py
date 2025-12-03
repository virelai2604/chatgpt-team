from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["batches"],
)


@router.post("/batches")
async def create_batch(request: Request) -> Response:
    """
    Create a new batch job.
    Mirrors POST /v1/batches.
    """
    logger.info("→ [batches] POST %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/batches")
async def list_batches(request: Request) -> Response:
    """
    List batch jobs.
    Mirrors GET /v1/batches.
    """
    logger.info("→ [batches] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.get("/batches/{batch_id}")
async def retrieve_batch(batch_id: str, request: Request) -> Response:
    """
    Retrieve a single batch.
    Mirrors GET /v1/batches/{batch_id}.
    """
    logger.info("→ [batches] GET %s", request.url.path)
    return await forward_openai_request(request)


@router.delete("/batches/{batch_id}")
async def cancel_batch(batch_id: str, request: Request) -> Response:
    """
    Cancel a batch job.
    Mirrors DELETE /v1/batches/{batch_id}.
    """
    logger.info("→ [batches] DELETE %s", request.url.path)
    return await forward_openai_request(request)

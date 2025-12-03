# app/routes/batches.py
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger  # type: ignore

router = APIRouter(
    prefix="/v1",
    tags=["batches"],
)


@router.get("/batches")
async def list_batches(request: Request) -> Response:
    """
    GET /v1/batches
    List all batch jobs.
    """
    logger.info("[batches] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/batches")
async def create_batch(request: Request) -> Response:
    """
    POST /v1/batches
    Create a new batch job.
    """
    logger.info("[batches] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/batches/{batch_id}")
async def retrieve_batch(batch_id: str, request: Request) -> Response:
    """
    GET /v1/batches/{batch_id}
    Retrieve a specific batch job.
    """
    logger.info("[batches] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.post("/batches/{batch_id}/cancel")
async def cancel_batch(batch_id: str, request: Request) -> Response:
    """
    POST /v1/batches/{batch_id}/cancel
    Cancel a batch job.
    """
    logger.info("[batches] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

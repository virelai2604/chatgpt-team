from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/v1/batches")
async def create_batch(request: Request) -> Response:
    logger.info("Incoming /v1/batches create request")
    return await forward_openai_request(request)


@router.get("/v1/batches/{batch_id}")
async def retrieve_batch(batch_id: str, request: Request) -> Response:
    logger.info(f"Incoming /v1/batches retrieve request for batch_id={batch_id}")
    return await forward_openai_request(request)


@router.get("/v1/batches")
async def list_batches(request: Request) -> Response:
    logger.info("Incoming /v1/batches list request")
    return await forward_openai_request(request)


@router.post("/v1/batches/{batch_id}/cancel")
async def cancel_batch(batch_id: str, request: Request) -> Response:
    logger.info(f"Incoming /v1/batches cancel request for batch_id={batch_id}")
    return await forward_openai_request(request)

# app/routes/batches.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["batches"])


@router.post("/batches")
async def create_batch(request: Request) -> Response:
    """
    Thin proxy for OpenAI Batch API:
    POST https://api.openai.com/v1/batches
    """
    logger.info(
        "Relay: create batch",
        extra={"path": "/v1/batches", "method": "POST"},
    )
    return await forward_openai_request(request)


@router.get("/batches")
async def list_batches(request: Request) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/batches
    """
    logger.info(
        "Relay: list batches",
        extra={"path": "/v1/batches", "method": "GET"},
    )
    return await forward_openai_request(request)


@router.get("/batches/{batch_id}")
async def retrieve_batch(batch_id: str, request: Request) -> Response:
    """
    Thin proxy:
    GET https://api.openai.com/v1/batches/{batch_id}
    """
    logger.info(
        "Relay: retrieve batch",
        extra={"path": f"/v1/batches/{batch_id}", "method": "GET"},
    )
    return await forward_openai_request(request)


@router.post("/batches/{batch_id}/cancel")
async def cancel_batch(batch_id: str, request: Request) -> Response:
    """
    Thin proxy:
    POST https://api.openai.com/v1/batches/{batch_id}/cancel
    """
    logger.info(
        "Relay: cancel batch",
        extra={"path": f"/v1/batches/{batch_id}/cancel", "method": "POST"},
    )
    return await forward_openai_request(request)

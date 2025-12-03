# app/routes/batches.py

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request

router = APIRouter(tags=["batches"])


@router.post("/v1/batches")
async def create_batch(request: Request):
    """
    Proxy for: POST https://api.openai.com/v1/batches
    """
    return await forward_openai_request(request)


@router.get("/v1/batches")
async def list_batches(request: Request):
    """
    Proxy for: GET https://api.openai.com/v1/batches
    """
    return await forward_openai_request(request)


@router.get("/v1/batches/{batch_id}")
async def retrieve_batch(request: Request, batch_id: str):
    """
    Proxy for: GET https://api.openai.com/v1/batches/{batch_id}
    """
    return await forward_openai_request(request)


@router.post("/v1/batches/{batch_id}/cancel")
async def cancel_batch(request: Request, batch_id: str):
    """
    Proxy for: POST https://api.openai.com/v1/batches/{batch_id}/cancel
    """
    return await forward_openai_request(request)

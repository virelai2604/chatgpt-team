# app/routes/responses.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body

from app.api.forward_openai import forward_responses_create
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["responses"],
)


@router.post("/responses")
async def create_response(
    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload"),
) -> Any:
    """
    Proxy for OpenAI Responses API.

    Expects the same JSON body that you would send directly to:
        POST https://api.openai.com/v1/responses
    """
    logger.info("Incoming /v1/responses request")
    return await forward_responses_create(body)

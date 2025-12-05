# app/routes/responses.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Body

from app.api.forward_openai import forward_responses_create
from app.utils.logger import get_logger

router = APIRouter(
    prefix="/v1",
    tags=["responses"],
)

logger = get_logger(__name__)


@router.post("/responses")
async def create_response(
    body: Dict[str, Any] = Body(..., description="OpenAI Responses.create payload"),
) -> Any:
    """
    Proxy for the OpenAI Responses API (primary text/multimodal entry point).

    Expects the same JSON body that you would send directly to:
        POST https://api.openai.com/v1/responses
    """
    logger.info("Incoming /v1/responses request")
    return await forward_responses_create(body)

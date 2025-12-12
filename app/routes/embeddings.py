# app/routes/embeddings.py

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.api.forward_openai import forward_embeddings_create

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/embeddings")
async def create_embeddings(request: Request) -> JSONResponse:
    """
    Proxy /v1/embeddings to the OpenAI Embeddings API via AsyncOpenAI.

    We intentionally return the raw JSON from OpenAI so that:
      - body["object"] == "list"
      - body["data"][0]["embedding"] is a list[float]
    which is exactly what tests/test_local_e2e.py::test_embeddings_basic expects.
    """
    logger.info("Incoming /v1/embeddings request")
    body: Dict[str, Any] = await request.json()

    result = await forward_embeddings_create(body)
    return JSONResponse(content=result)

# ================================================================
# models.py — Model Metadata Routes (with upstream passthrough)
# ================================================================
# Provides mock implementations of the OpenAI /v1/models endpoints.
# Falls back to real OpenAI API when an API key is provided.
# ================================================================

import os
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_to_openai

router = APIRouter(tags=["models"])

MODELS = [
    {"id": "gpt-5", "object": "model"},
    {"id": "gpt-4o", "object": "model"},
    {"id": "gpt-4o-mini", "object": "model"},
]


@router.get("/v1/models")
async def list_models(request: Request):
    """
    Returns available model metadata.
    Falls back to real OpenAI API if API key is configured.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            resp = await forward_to_openai(request, "/v1/models")
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            pass  # fallback to local mock if network fails

    return JSONResponse({
        "object": "list",
        "data": MODELS
    })


@router.get("/models")
async def list_models_alias(request: Request):
    """Legacy alias for /v1/models."""
    return await list_models(request)

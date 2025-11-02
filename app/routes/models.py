# ================================================================
# models.py — Model Metadata Routes (Upstream-Aware)
# ================================================================
# Returns local models when offline, or real OpenAI model list when
# OPENAI_API_KEY is configured.
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
    """Return available models — tries upstream, falls back local."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            resp = await forward_to_openai(request, "/v1/models")
            # forward_to_openai already returns JSONResponse
            return resp
        except Exception:
            pass  # fallback if network error

    return JSONResponse({"object": "list", "data": MODELS})


@router.get("/models")
async def list_models_alias(request: Request):
    """Legacy alias for /v1/models."""
    return await list_models(request)

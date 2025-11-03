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

router = APIRouter(prefix="/v1/models", tags=["models"])

# Local fallback model list for offline/relay-only operation
LOCAL_MODELS = [
    {"id": "gpt-5", "object": "model", "owned_by": "system"},
    {"id": "gpt-4o", "object": "model", "owned_by": "system"},
    {"id": "gpt-4o-mini", "object": "model", "owned_by": "system"},
]

@router.get("")
async def list_models(request: Request):
    """List available models — uses upstream if API key present, otherwise fallback."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            resp = await forward_to_openai(request, "/v1/models")
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            pass  # fallback to local list if OpenAI unavailable
    return JSONResponse({"object": "list", "data": LOCAL_MODELS})

@router.get("/{model_id}")
async def get_model(model_id: str, request: Request):
    """Retrieve metadata for a single model."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            resp = await forward_to_openai(request, f"/v1/models/{model_id}")
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            pass
    model = next((m for m in LOCAL_MODELS if m["id"] == model_id), None)
    return JSONResponse(model or {"error": f"Model '{model_id}' not found"})

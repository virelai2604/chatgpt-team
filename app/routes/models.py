# ==========================================================
# app/routes/models.py — Relay v2025-10 Ground Truth Mirror
# ==========================================================
# OpenAI-compatible /v1/models endpoint.
# Lists available models and retrieves metadata for a specific model.
# Fully async, DB-logged, and proxy-forwarded via forward_openai().
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai


router = APIRouter(prefix="/v1", tags=["Models"])

# ----------------------------------------------------------
# 📋  List Models
# ----------------------------------------------------------
@router.get("/models")
async def list_models(request: Request):
    """
    Mirrors GET /v1/models
    Returns all model IDs, owners, and categories available
    through the relay.
    """
    endpoint = "/v1/models"
    response = await forward_openai(request, endpoint)
    try:
        await log_event(endpoint, response.status_code, "list models")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🔍  Retrieve Specific Model
# ----------------------------------------------------------
@router.get("/models/{model}")
async def get_model(request: Request, model: str):
    """
    Mirrors GET /v1/models/{model}
    Returns metadata about a single model, including ownership,
    release date, and capability flags.
    """
    endpoint = f"/v1/models/{model}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event(endpoint, response.status_code, f"model {model}")
    except Exception:
        pass
    return response

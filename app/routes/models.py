# ==========================================================
# app/routes/models.py — BIFL v2.3.4-fp
# ==========================================================
# Unified model management proxy.
# Supports listing, retrieving, and future GPT-5 beta headers.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from app.utils.db_logger import log_event

router = APIRouter(prefix="/v1/models", tags=["Models"])

# ----------------------------------------------------------
# 🧩  List Models
# ----------------------------------------------------------
@router.get("")
async def list_models(request: Request):
    """
    Retrieve the full list of available models.
    Auto-adds `OpenAI-Beta` headers for GPT-5 and Sora compatibility.
    """
    response = await forward_openai(request, "/v1/models")
    try:
        await log_event("/v1/models/list", response.status_code, "list models")
    except Exception:
        pass
    return response


# ----------------------------------------------------------
# 🔍  Retrieve Model Details
# ----------------------------------------------------------
@router.get("/{model_id}")
async def get_model(request: Request, model_id: str):
    """
    Retrieve details about a specific model ID.
    Example:
        GET /v1/models/gpt-5-pro
    """
    endpoint = f"/v1/models/{model_id}"
    response = await forward_openai(request, endpoint)
    try:
        await log_event("/v1/models/get", response.status_code, f"model {model_id}")
    except Exception:
        pass
    return response

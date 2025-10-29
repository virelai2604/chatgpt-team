# ==========================================================
# app/routes/models.py — Ground Truth OpenAI-Compatible Mirror
# ==========================================================
from fastapi import APIRouter
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/models", tags=["Models"])

@router.get("")
async def list_models():
    """
    Mirrors OpenAI GET /v1/models
    Returns all available models and their metadata.
    """
    return await forward_openai_request("v1/models", method="GET")

@router.get("/{model_id}")
async def get_model(model_id: str):
    """
    Mirrors OpenAI GET /v1/models/{model_id}
    Retrieves metadata for a specific model.
    """
    return await forward_openai_request(f"v1/models/{model_id}", method="GET")

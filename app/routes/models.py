# ================================================================
# models.py — Model Metadata Routes
# ================================================================
# Provides mock implementations of the OpenAI /v1/models endpoints.
# The `/models` endpoint is used in ground truth tests.
# ================================================================

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["models"])

MODELS = [
    {"id": "gpt-5", "object": "model"},
    {"id": "gpt-4o", "object": "model"},
    {"id": "gpt-4o-mini", "object": "model"},
]

@router.get("/models")
@router.get("/v1/models")
async def list_models():
    """
    Returns available model metadata.
    """
    return JSONResponse({
        "object": "list",
        "data": MODELS
    })

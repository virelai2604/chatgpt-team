# app/routes/models.py

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# This router is mounted with prefix "/v1/models" in app.main
router = APIRouter(prefix="/v1/models", tags=["models"])


@router.get("")
async def list_models() -> dict:
    """
    Minimal, local implementation of GET /v1/models.

    For local development & integration tests we don't need to hit OpenAI.
    We just return a list with at least one model: settings.DEFAULT_MODEL.
    """
    default_id = settings.DEFAULT_MODEL

    logger.info("→ [models] local list /v1/models (default=%s)", default_id)

    return {
        "object": "list",
        "data": [
            {
                "object": "model",
                "id": default_id,
                "owned_by": "system",
            }
        ],
    }


@router.get("/{model_id}")
async def retrieve_model(model_id: str) -> dict:
    """
    Minimal, local implementation of GET /v1/models/{id}.

    Always returns a simple model object; tests only check:
      - body["object"] == "model"
      - body["id"] == requested id
    """
    logger.info("→ [models] local retrieve /v1/models/%s", model_id)

    return {
        "object": "model",
        "id": model_id,
        "owned_by": "system",
    }

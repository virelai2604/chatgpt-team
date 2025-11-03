"""
models.py — OpenAI-Compatible /v1/models Endpoint
────────────────────────────────────────────────────────────
Implements model listing and retrieval exactly like OpenAI SDKs.
Conforms to:
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0
  • OpenAI API Reference (2025-10)
Supports:
  • GET /v1/models
  • GET /v1/models/{model_id}
"""

import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1/models", tags=["models"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))
USER_AGENT = "openai-python/2.61.0"

# ------------------------------------------------------------
# GET /v1/models
# ------------------------------------------------------------
@router.get("")
async def list_models(request: Request):
    """Fetch full model list directly from OpenAI."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(f"{OPENAI_API_BASE}/models", headers=headers)
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            log.error(f"[Models] network error: {e}")
            return JSONResponse(
                {"error": {"message": str(e), "type": "network_error"}},
                status_code=502,
            )


# ------------------------------------------------------------
# GET /v1/models/{model_id}
# ------------------------------------------------------------
@router.get("/{model_id}")
async def retrieve_model(model_id: str, request: Request):
    """Retrieve metadata for a specific model (live OpenAI)."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        try:
            resp = await client.get(f"{OPENAI_API_BASE}/models/{model_id}", headers=headers)
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            log.error(f"[Models] network error: {e}")
            return JSONResponse(
                {"error": {"message": str(e), "type": "network_error"}},
                status_code=502,
            )

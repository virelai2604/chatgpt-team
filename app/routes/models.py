"""
models.py — /v1/models
───────────────────────
Implements OpenAI model listing and retrieval.
"""

import os
import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1/models", tags=["models"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


@router.get("")
async def list_models():
    """
    Thin proxy for GET /v1/models.

    NOTE:
      • In your main relay flow, /v1/models is typically handled by
        P4OrchestratorMiddleware + forward_openai_request.
    """
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{OPENAI_API_BASE.rstrip('/')}/v1/models",
                headers=headers,
            )
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            log.error(f"[Models] {e}")
            return JSONResponse({"error": str(e)}, status_code=502)

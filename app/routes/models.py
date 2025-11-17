"""
models.py — /v1/models
───────────────────────
Implements OpenAI model listing and retrieval (optional local proxy).

Matches the official Models API:
  • GET /v1/models
  • GET /v1/models/{model}
"""

import os

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.utils.logger import relay_log as log

router = APIRouter(prefix="/v1/models", tags=["models"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "30"))


def _headers() -> dict:
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    return headers


def _models_url() -> str:
    return f"{OPENAI_API_BASE.rstrip('/')}/v1/models"


@router.get("")
async def list_models():
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(_models_url(), headers=_headers())
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            log.error(f"[Models] list error: {e}")
            return JSONResponse({"error": str(e)}, status_code=502)


@router.get("/{model_id}")
async def retrieve_model(model_id: str):
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.get(f"{_models_url()}/{model_id}", headers=_headers())
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except httpx.RequestError as e:
            log.error(f"[Models] retrieve error: {e}")
            return JSONResponse({"error": str(e)}, status_code=502)

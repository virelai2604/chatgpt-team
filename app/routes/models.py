from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import httpx
import os

router = APIRouter(prefix="/v1/models", tags=["Models"])

OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
API_KEY = os.getenv("OPENAI_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


@router.get("")
async def list_models():
    """List available models (mirrors OpenAI API)."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{OPENAI_BASE}/v1/models", headers=HEADERS)
    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return JSONResponse(r.json())


@router.get("/{model_id}")
async def get_model(model_id: str):
    """Retrieve metadata for a specific model."""
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{OPENAI_BASE}/v1/models/{model_id}", headers=HEADERS)
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="Model not found")
    return JSONResponse(r.json(), status_code=r.status_code)

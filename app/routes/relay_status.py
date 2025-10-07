from fastapi import APIRouter
from fastapi.responses import JSONResponse
import httpx
import os

router = APIRouter()

@router.get("/v1/relay-status")
async def relay_status():
    """Returns relay health, upstream OpenAI health, and available models."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    headers = {"Authorization": f"Bearer {api_key}"}
    health = {"relay": "ok", "upstream": "unknown", "models": []}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://api.openai.com/v1/models", headers=headers)
            if resp.status_code == 200:
                health["upstream"] = "ok"
                health["models"] = [m["id"] for m in resp.json().get("data", [])]
            else:
                health["upstream"] = f"error: {resp.status_code} - {resp.text}"
    except Exception as e:
        health["upstream"] = f"error: {str(e)}"
    return JSONResponse(content=health)

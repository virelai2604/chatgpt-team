from fastapi import APIRouter, HTTPException
from app.client import OpenAIClient
import os

router = APIRouter()

@router.get("/")
async def list_models():
    api_key = os.getenv("OPENAI_API_KEY", "sk-...")
    client = OpenAIClient(api_key)

    try:
        response = await client.client.get("/models")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""
models.py — /v1/models
Lists available models. Mimics OpenAI /models endpoint.
"""

from fastapi import APIRouter
import time

router = APIRouter()

MODELS = [
    {"id": "gpt-5", "object": "model", "created": int(time.time()), "owned_by": "openai"},
    {"id": "gpt-4o", "object": "model", "created": int(time.time()), "owned_by": "openai"},
]

@router.get("/v1/models")
async def list_models():
    return {"object": "list", "data": MODELS}

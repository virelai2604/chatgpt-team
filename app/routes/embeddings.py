# ================================================================
# embeddings.py — Passthrough for /v1/embeddings
# ================================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_to_openai

router = APIRouter(prefix="/v1/embeddings", tags=["embeddings"])

@router.post("")
async def create_embedding(request: Request):
    """Generate text embeddings via OpenAI API."""
    try:
        resp = await forward_to_openai(request, "/v1/embeddings")
        return JSONResponse(resp.json(), status_code=resp.status_code)
    except Exception as e:
        # Local fallback response if upstream unavailable
        return JSONResponse({
            "object": "embedding",
            "data": [{
                "embedding": [0.1, 0.2, 0.3],
                "index": 0
            }],
            "model": "text-embedding-3-large",
            "usage": {"prompt_tokens": 1, "total_tokens": 1},
            "error": str(e)
        })

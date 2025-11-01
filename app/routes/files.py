# ================================================================
# embeddings.py — Embedding Generation Mock
# ================================================================
# Compatible with OpenAI SDK 2.6.1's /v1/embeddings interface.
# Produces deterministic 128-dim vectors suitable for offline tests.
# ================================================================

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import time, random

router = APIRouter(prefix="/v1/embeddings", tags=["embeddings"])

@router.post("")
async def create_embedding(req: Request):
    """
    Mock endpoint for /v1/embeddings.
    """
    body = await req.json()
    text = str(body.get("input", ""))
    seed = sum(ord(c) for c in text) % 10000
    random.seed(seed)

    # Generate reproducible 128-dim embedding
    embedding = [random.random() for _ in range(128)]

    return JSONResponse({
        "object": "embedding",
        "data": [
            {"embedding": embedding, "index": 0}
        ],
        "model": "mock-embedding",
        "usage": {
            "prompt_tokens": len(text),
            "total_tokens": len(text)
        },
        "created": int(time.time())
    })

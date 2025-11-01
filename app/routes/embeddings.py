"""
embeddings.py — /v1/embeddings
Generates text embeddings. Simplified numerical vector simulation.
"""

from fastapi import APIRouter, Request
import time
import numpy as np
import uuid

router = APIRouter()

@router.post("/v1/embeddings")
async def create_embedding(request: Request):
    body = await request.json()
    text = body.get("input", "")
    model = body.get("model", "text-embedding-3-small")
    # Simple numeric simulation
    vector = np.random.random(128).tolist()
    emb_id = f"emb_{uuid.uuid4().hex[:10]}"
    return {
        "id": emb_id,
        "object": "embedding",
        "model": model,
        "created": int(time.time()),
        "data": [{"object": "embedding", "embedding": vector, "index": 0}],
        "usage": {"prompt_tokens": len(text.split()), "total_tokens": len(text.split())}
    }

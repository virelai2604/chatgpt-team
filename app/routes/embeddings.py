# ==========================================================
# app/routes/embeddings.py — BIFL v2.3.4-fp
# ==========================================================
# OpenAI-compatible embeddings endpoint.
# Supports standard embedding creation and optional
# /similarity extension for cosine distance checks.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward import forward_openai
import numpy as np

router = APIRouter(prefix="/v1/embeddings", tags=["Embeddings"])


# ----------------------------------------------------------
# 🧠  Standard Embedding Creation
# ----------------------------------------------------------
@router.post("")
async def create_embedding(request: Request):
    """
    Forward embedding creation requests to OpenAI.
    Example:
      {
        "model": "text-embedding-3-large",
        "input": ["Hello world", "Goodbye world"],
        "stream": false
      }
    """
    return await forward_openai(request, "/v1/embeddings")


# ----------------------------------------------------------
# 🔍  Optional Local Similarity (Cosine)
# ----------------------------------------------------------
@router.post("/similarity")
async def compute_similarity(request: Request):
    """
    Optional local helper for computing cosine similarity between
    embedding vectors. This is *not* an OpenAI API call — just a
    utility for debugging or offline use.
    Example:
      {
        "vectors": [
          [0.1, 0.2, 0.3],
          [0.1, 0.25, 0.35]
        ]
      }
    """
    body = await request.json()
    vectors = body.get("vectors", [])
    if len(vectors) < 2:
        return {"error": "Need at least two vectors to compute similarity."}

    a, b = np.array(vectors[0]), np.array(vectors[1])
    sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    return {"similarity": sim, "method": "cosine"}

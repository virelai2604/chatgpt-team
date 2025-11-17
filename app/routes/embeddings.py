"""
embeddings.py — Handles /v1/embeddings route
─────────────────────────────────────────────
Creates text embeddings via OpenAI API.

Design:
  • Delegates to the universal forwarder (forward_openai_request) so that
    auth, base URL, and streaming behaviour are consistent with all other
    proxied /v1/* endpoints.
"""

from fastapi import APIRouter, Request
from app.utils.logger import relay_log as logger
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/embeddings", tags=["embeddings"])


@router.post("")
async def create_embedding(request: Request):
    """
    POST /v1/embeddings

    OpenAI-parity endpoint, equivalent to:
      client.embeddings.create({ ... })

    We still log the model for observability, but let the shared
    forward_openai_request handle:
      • Authorization header (from request or OPENAI_API_KEY env)
      • Correct OPENAI_API_BASE (no double /v1)
      • JSON vs multipart bodies
      • Error handling
    """
    # lightweight peek for logging only; don't mutate the body
    try:
        body = await request.json()
        model = body.get("model")
    except Exception:
        model = None

    logger.info(f"[Embeddings] incoming request model={model!r}")
    return await forward_openai_request(request)

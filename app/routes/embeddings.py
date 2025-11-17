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

    We intentionally do NOT read the body here; the shared
    forward_openai_request will handle it so that:
      • The JSON body is preserved
      • Authorization / org headers are injected as needed
      • Base URL and /v1 path handling stay consistent
    """
    logger.info("[Embeddings] proxied embedding request to OpenAI")
    return await forward_openai_request(request)

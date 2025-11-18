"""
embeddings.py — /v1/embeddings proxy
─────────────────────────────────────
Creates vector embeddings via the OpenAI Embeddings API.

Official behavior (per current REST docs and openai-python 2.8.x):

  • POST /v1/embeddings
      Body typically includes:
        - model: e.g. "text-embedding-3-small"
        - input: string or array of strings
        - encoding_format: "float" | "base64" (optional)
        - additional parameters as supported by the API.

This router does not inspect or modify the request body. It simply forwards
the request to the upstream OpenAI API using `forward_openai_request`, so it
automatically stays in sync with the latest embedding parameters and response
shapes provided by the official API.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger

router = APIRouter(
    prefix="/v1",
    tags=["embeddings"],
)


@router.post("/embeddings")
async def create_embeddings(request: Request):
    """
    POST /v1/embeddings

    OpenAI-parity Embeddings endpoint, equivalent to:

        client.embeddings.create({ ... })

    We intentionally avoid touching the body here; the shared
    `forward_openai_request` function handles:

      • Reading and forwarding the JSON body as-is
      • Injecting Authorization / organization headers
      • Respecting OPENAI_API_BASE (with or without /v1 suffix)
      • Normalizing errors into OpenAI-style error objects

    This keeps the relay thin, predictable, and future-proof as the
    Embeddings API evolves.
    """
    logger.info("→ [embeddings] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

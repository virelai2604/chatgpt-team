"""
models.py — /v1/models proxy
────────────────────────────
Thin, future-proof proxy over the OpenAI Models API.

OpenAI Models API surface (as of openai-python 2.8.x and current REST docs):
  • GET    /v1/models            → list models
  • GET    /v1/models/{model}    → retrieve model
  • DELETE /v1/models/{model}    → delete fine-tuned model (if supported)

This router does NOT implement custom business logic. It delegates the
actual HTTP call to `forward_openai_request`, which handles:

  • Authorization and organization headers
  • Optional OpenAI-Beta headers (passed through if present)
  • JSON vs streaming responses
  • Error normalization into OpenAI-style error payloads
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger


router = APIRouter(
    prefix="/v1",
    tags=["models"],
)


@router.get("/models")
async def list_models(request: Request):
    """
    GET /v1/models

    Lists the currently available models and provides basic information
    about each one (owner, availability, etc.), as defined in the OpenAI
    Models API reference.

    This simply forwards the request to the upstream OpenAI API via the
    shared forwarder, so it always stays in sync with the official spec.
    """
    logger.info("→ [models] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.get("/models/{model_id}")
async def retrieve_model(model_id: str, request: Request):
    """
    GET /v1/models/{model_id}

    Retrieves information about a specific model (e.g. gpt-4o-mini,
    text-embedding-3-large, etc.).

    The relay does not interpret the model_id; it simply proxies the
    request to OpenAI and returns the upstream response unchanged.
    """
    logger.info(
        "→ [models] %s %s (model_id=%s)",
        request.method,
        request.url.path,
        model_id,
    )
    return await forward_openai_request(request)


@router.delete("/models/{model_id}")
async def delete_model(model_id: str, request: Request):
    """
    DELETE /v1/models/{model_id}

    Deletes a fine-tuned model that you own, when supported by the
    upstream API. For most base models, deletion is not allowed and
    OpenAI will return an error.

    The relay forwards this operation to OpenAI and returns whatever
    result the upstream API provides.
    """
    logger.info(
        "→ [models] %s %s (model_id=%s)",
        request.method,
        request.url.path,
        model_id,
    )
    return await forward_openai_request(request)

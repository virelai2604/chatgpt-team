# app/routes/actions.py

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_from_parts
from app.utils.logger import relay_log as logger


router = APIRouter(
    prefix="/v1/actions",
    tags=["actions"],
)


class OpenAIForwardPayload(BaseModel):
    """
    Payload for `/v1/actions/openai/forward`.

    Lets a GPT or other client ask the relay to perform an OpenAI API call
    on its behalf (relay injects auth, base URL, and streaming semantics).
    """

    method: str = Field(
        default="POST",
        description="HTTP method, e.g. GET, POST, DELETE",
    )
    path: str = Field(
        ...,
        description="Relative OpenAI API path, e.g. /v1/responses or /v1/models",
    )
    query: Dict[str, Any] = Field(
        default_factory=dict,
        description="Query string parameters to append to the URL",
    )
    headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Extra headers to send upstream (excluding Authorization)",
    )
    body: Optional[Any] = Field(
        default=None,
        description="JSON-serialisable body or raw text/bytes",
    )
    stream: bool = Field(
        default=False,
        description="If true, request streaming from the upstream API when supported",
    )


@router.post(
    "/openai/forward",
    name="actions_openai_forward",
    summary="Forward a single OpenAI API call through the relay",
)
async def actions_openai_forward(payload: OpenAIForwardPayload):
    """
    Generic forwarder for OpenAI endpoints, to be called from ChatGPT Actions.

    Examples:
      - Forward `/v1/responses` with stream=True
      - Forward `/v1/models`
      - Forward `/v1/embeddings`
    """
    try:
        return await forward_openai_from_parts(
            method=payload.method,
            path=payload.path,
            query=payload.query,
            headers=payload.headers,
            body=payload.body,
            stream=payload.stream,
        )
    except HTTPException:
        # Let structured HTTP errors bubble up as‑is
        raise
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("actions_openai_forward failed: %r", exc)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "Unexpected error forwarding OpenAI action",
                    "type": "internal_error",
                }
            },
        )

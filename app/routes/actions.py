# app/routes/actions.py

from __future__ import annotations

import os
import platform
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app.api.forward_openai import forward_openai_from_parts

router = APIRouter(tags=["actions"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _base_env() -> Dict[str, str]:
    """
    Shared environment snapshot used by ping and relay_info.
    """
    return {
        "app_mode": os.getenv("APP_MODE", "development"),
        "environment": os.getenv("ENVIRONMENT", "local"),
        "base_openai_api": os.getenv("OPENAI_API_BASE", "https://api.openai.com"),
        "default_model": os.getenv("DEFAULT_MODEL")
        or os.getenv("DEFAULT_OPENAI_MODEL")
        or "gpt-4.1-mini",
    }


def _flat_relay_info() -> Dict[str, Any]:
    base = _base_env()
    relay_name = os.getenv("RELAY_NAME", "ChatGPT Team Relay")

    return {
        "relay_name": relay_name,
        "environment": base["environment"],
        "app_mode": base["app_mode"],
        "base_openai_api": base["base_openai_api"],
    }


def _structured_relay_info() -> Dict[str, Any]:
    base = _base_env()
    relay_name = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
    build_version = os.getenv("BIFL_VERSION", "dev")

    return {
        "relay": {
            "name": relay_name,
            "version": build_version,
            "environment": base["environment"],
            "app_mode": base["app_mode"],
        },
        "upstream": {
            "api_base": base["base_openai_api"],
            "default_model": base["default_model"],
        },
        "host": {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "python_version": platform.python_version(),
        },
        "timestamp": _now_iso(),
    }


class OpenAIForwardPayload(BaseModel):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    path: str = Field(..., description="OpenAI API path, must start with /v1")
    query: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    body: Optional[Any] = None
    stream: bool = Field(
        default=False,
        description="If true, forward as SSE stream (caller must also set Accept: text/event-stream).",
    )


# -------- Relay info / ping -------------------------------------------------


@router.get("/v1/actions/ping")
@router.get("/relay/actions/ping")
async def actions_ping() -> Dict[str, Any]:
    """
    Simple ping endpoint used by tests and health checks.
    """
    env = _base_env()
    return {
        "status": "ok",
        "now": _now_iso(),
        "environment": env["environment"],
        "app_mode": env["app_mode"],
    }


@router.get("/v1/actions/relay_info")
@router.get("/relay/actions/relay_info")
async def actions_relay_info() -> Dict[str, Any]:
    """
    Structured relay metadata for diagnostics and debugging.
    """
    return _structured_relay_info()


# -------- Generic OpenAI forwarder ------------------------------------------


@router.post("/v1/actions/openai/forward")
async def actions_openai_forward(payload: OpenAIForwardPayload, request: Request) -> Response:
    """
    Generic action entrypoint:

      POST /v1/actions/openai/forward
      {
        "method": "POST",
        "path": "/v1/embeddings",
        "query": { ... },
        "headers": { ... },
        "body": { ... },
        "stream": false
      }

    This is relay-native; it is not an OpenAI public API endpoint.
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
        raise
    except Exception as exc:  # noqa: BLE001
        # Wrap unexpected exceptions in an OpenAI-style error envelope
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "message": f"actions_openai_forward failed: {exc}",
                    "type": "server_error",
                    "code": "actions_forward_error",
                }
            },
        )

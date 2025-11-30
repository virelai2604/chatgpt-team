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
    """
    Return the current UTC time as an ISO-8601 string.
    Used as default for BUILD_DATE in relay_info.
    """
    return datetime.now(timezone.utc).isoformat()


def _base_env() -> Dict[str, str]:
    """
    Shared environment snapshot used by both ping and relay_info.
    """
    return {
        "app_mode": os.getenv("APP_MODE", "test"),
        "environment": os.getenv("ENVIRONMENT", "local"),
        "base_openai_api": os.getenv("OPENAI_API_BASE", "https://api.openai.com"),
        "default_model": os.getenv("DEFAULT_MODEL")
        or os.getenv("DEFAULT_OPENAI_MODEL")
        or "gpt-4.1-mini",
    }


def _flat_relay_info() -> Dict[str, Any]:
    """
    Flat relay info used primarily by test_tools_and_actions_routes.py.
    """
    base = _base_env()
    relay_name = os.getenv("RELAY_NAME", "ChatGPT Team Relay (pytest)")

    return {
        "relay_name": relay_name,
        "environment": base["environment"],
        "app_mode": base["app_mode"],
        "base_openai_api": base["base_openai_api"],
    }


def _structured_relay_info() -> Dict[str, Any]:
    """
    Structured relay info used by /v1/actions/relay_info.
    """
    base = _base_env()

    relay = {
        "name": os.getenv("RELAY_NAME", "ChatGPT Team Relay (pytest)"),
        "app_mode": base["app_mode"],
        "environment": base["environment"],
        "version": os.getenv("RELAY_VERSION", "unknown"),
    }

    upstream = {
        "base_url": base["base_openai_api"],
        "default_model": base["default_model"],
    }

    system = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
    }

    build = {
        "build_channel": os.getenv("BUILD_CHANNEL", "unknown"),
        "version_source": os.getenv("VERSION_SOURCE", "unknown"),
        "git_sha": os.getenv("GIT_SHA", "unknown"),
        "build_date": os.getenv("BUILD_DATE", _now_iso()),
    }

    return {
        "type": "relay.info",
        "relay": relay,
        "upstream": upstream,
        "system": system,
        "build": build,
        "app_mode": base["app_mode"],
        "environment": base["environment"],
        "base_openai_api": base["base_openai_api"],
    }


@router.get("/actions/ping")
@router.get("/v1/actions/ping")
async def actions_ping() -> JSONResponse:
    """
    Simple liveness endpoint used by tests and external monitors.
    """
    base = _base_env()
    payload = {
        "object": "actions.ping",
        "source": "chatgpt-team-relay",
        "status": "ok",
        "app_mode": base["app_mode"],
        "environment": base["environment"],
    }
    return JSONResponse(payload, status_code=200)


@router.get("/actions/relay_info", summary="Flat relay environment info")
async def actions_relay_info_flat() -> Dict[str, Any]:
    """
    GET /actions/relay_info

    Flat relay info used primarily by test_tools_and_actions_routes.py.
    """
    return _flat_relay_info()


@router.get("/v1/actions/relay_info", summary="Structured relay environment info")
async def actions_relay_info_v1() -> Dict[str, Any]:
    """
    GET /v1/actions/relay_info

    Structured info used by Actions / orchestrator tests.
    """
    return _structured_relay_info()


class OpenAIForwardPayload(BaseModel):
    """
    Payload for the generic Forward API endpoint.

    This is designed to be used as a ChatGPT Action / tool:

      {
        "method": "POST",
        "path": "/v1/responses",
        "query": {"stream": true},
        "body": { ... arbitrary OpenAI request body ... }
      }
    """

    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = Field(
        ...,
        description="HTTP method to use for the upstream OpenAI request.",
    )
    path: str = Field(
        ...,
        description="Path to call on the upstream OpenAI API, e.g. '/v1/models'.",
        examples=["/v1/models", "/v1/responses"],
    )
    query: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional query parameters to append to the upstream request.",
    )
    body: Optional[Any] = Field(
        default=None,
        description="Optional JSON body to send to the upstream request.",
    )
    headers: Optional[Dict[str, str]] = Field(
        default=None,
        description=(
            "Optional additional headers to send. "
            "Authorization headers are always ignored; the relay injects its own."
        ),
    )


@router.post(
    "/v1/actions/openai/forward",
    summary="Generic Forward API for OpenAI endpoints",
)
async def actions_openai_forward(
    payload: OpenAIForwardPayload,
    request: Request,
) -> Response:
    """
    Generic Forward API endpoint primarily for ChatGPT Actions / Agents.

    It allows a single tool (`openai_forward`) to reach any upstream OpenAI
    endpoint through this relay without creating a new action for each path.

    Security notes:
      - Client-provided Authorization headers are ignored by the core forwarder.
      - The relay always injects its own OPENAI_API_KEY for upstream calls.
    """
    # Optional guardrail: prevent forwarding *this* endpoint to itself
    if payload.path.startswith("/v1/actions/openai/forward"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "message": "Recursive calls to /v1/actions/openai/forward are not allowed.",
                    "type": "invalid_request_error",
                    "code": "recursive_forward",
                }
            },
        )

    return await forward_openai_from_parts(
        method=payload.method,
        path=payload.path,
        query=payload.query,
        body=payload.body,
        headers=payload.headers,
    )

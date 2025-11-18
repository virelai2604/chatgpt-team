# app/routes/actions.py

"""
actions.py — Custom ChatGPT Actions Endpoints
─────────────────────────────────────────────
Implements any /actions/* endpoints that your OpenAPI schema exposes
to the ChatGPT / Custom GPT client.

These are NOT part of the public OpenAI REST surface; they are specific
to your relay and business logic.

For now we implement two utility endpoints:

  • GET /actions/ping
      Lightweight liveness check usable by ChatGPT Actions.

  • GET /actions/relay_info
      Returns diagnostic metadata about this relay instance:
      name, environment, default model, build version, etc.
"""

from __future__ import annotations

import os
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/actions", tags=["actions"])

RELAY_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

BIFL_VERSION = os.getenv("BIFL_VERSION", "unknown")
BUILD_DATE = os.getenv("BUILD_DATE", "unknown")
BUILD_CHANNEL = os.getenv("BUILD_CHANNEL", "unknown")

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")


@router.get("/ping")
async def ping():
    """
    GET /actions/ping

    Simple liveness probe suitable for ChatGPT Actions or external
    monitoring systems. Returns a stable, cacheable JSON payload.
    """
    return JSONResponse(
        {
            "object": "action.ping",
            "status": "ok",
            "relay_name": RELAY_NAME,
            "environment": ENVIRONMENT,
        },
        status_code=200,
    )


@router.get("/relay_info")
async def relay_info():
    """
    GET /actions/relay_info

    Returns non-sensitive metadata describing this relay instance so
    ChatGPT Actions (or other clients) can introspect capabilities
    and configuration without having to parse environment variables.
    """
    return JSONResponse(
        {
            "object": "relay.info",
            "relay_name": RELAY_NAME,
            "environment": ENVIRONMENT,
            "default_model": DEFAULT_MODEL,
            "bifl_version": BIFL_VERSION,
            "build_date": BUILD_DATE,
            "build_channel": BUILD_CHANNEL,
            "openai_api_base": OPENAI_API_BASE,
        },
        status_code=200,
    )

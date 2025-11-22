from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["actions"])


def _now_iso() -> str:
    # Tests tolerate naive UTC ISO timestamp.
    return datetime.utcnow().isoformat()


def _base_env() -> Dict[str, str]:
    """
    Core environment fields used across ping and relay_info.
    """
    return {
        "relay_name": os.getenv("RELAY_NAME", "chatgpt-team-relay"),
        "environment": os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")),
        "app_mode": os.getenv("APP_MODE", "development"),
        "base_openai_api": os.getenv("OPENAI_API_BASE", "https://api.openai.com"),
        "build_channel": os.getenv("BUILD_CHANNEL", "unknown"),
        "bifl_version": os.getenv("BIFL_VERSION", "unknown"),
    }


def _flat_relay_info() -> Dict[str, Any]:
    """
    Shape expected by tests hitting /actions/relay_info.
    """
    env = _base_env()
    return {
        "relay_name": env["relay_name"],
        "environment": env["environment"],
        "app_mode": env["app_mode"],
        "base_openai_api": env["base_openai_api"],
        "build_channel": env["build_channel"],
        "bifl_version": env["bifl_version"],
    }


def _structured_relay_info() -> Dict[str, Any]:
    """
    Shape expected by /v1/actions/relay_info and used by Actions/toolchains.

    {
      "type": "relay.info",
      "relay": {...},
      "environment": {...},
      "build": {...}
    }
    """
    env = _base_env()
    return {
        "type": "relay.info",
        "relay": {
            "name": env["relay_name"],
            "version": env["bifl_version"],
        },
        "environment": {
            "environment": env["environment"],
            "app_mode": env["app_mode"],
            "base_openai_api": env["base_openai_api"],
        },
        "build": {
            "channel": env["build_channel"],
            "version": env["bifl_version"],
            "date": _now_iso(),
        },
    }


# ---------------------------------------------------------------------------
# /actions/ping  (basic health)
# ---------------------------------------------------------------------------

@router.get("/actions/ping", summary="Simple actions health check")
async def actions_ping_legacy() -> Dict[str, Any]:
    """
    GET /actions/ping

    Simple health-style endpoint used by legacy tests.
    """
    env = _base_env()
    return {
        "object": "actions.ping",
        "source": "chatgpt-team-relay",
        "status": "ok",
        "timestamp": _now_iso(),
        "app_mode": env["app_mode"],
        "environment": env["environment"],
        "base_openai_api": env["base_openai_api"],
    }


@router.get("/v1/actions/ping", summary="Versioned actions health check")
async def actions_ping_v1() -> Dict[str, Any]:
    """
    GET /v1/actions/ping

    Used by orchestrator tests; same shape as legacy plus versioned path.
    """
    # Reuse the legacy shape to keep behavior identical.
    return await actions_ping_legacy()


# ---------------------------------------------------------------------------
# /actions/relay_info (flat) and /v1/actions/relay_info (structured)
# ---------------------------------------------------------------------------

@router.get("/actions/relay_info", summary="Legacy relay environment info")
async def actions_relay_info_legacy() -> Dict[str, Any]:
    """
    GET /actions/relay_info

    Legacy flat shape. Tests in test_tools_and_actions_routes.py check for:
      - relay_name
      - environment
      - app_mode
      - base_openai_api
    """
    return _flat_relay_info()


@router.get("/v1/actions/relay_info", summary="Structured relay environment info")
async def actions_relay_info_v1() -> Dict[str, Any]:
    """
    GET /v1/actions/relay_info

    Structured info used by Actions / orchestrator tests.
    """
    return _structured_relay_info()

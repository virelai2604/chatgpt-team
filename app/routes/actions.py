from __future__ import annotations

import os
import platform
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["actions"])


def relay_info():
        # Tests only require a non-empty ISO string; naive UTC is fine here.
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
    Flat relay info used by /actions/relay_info.

    tests/test_tools_and_actions_routes.py expects the following top-level
    keys to be present:

      - relay_name
      - environment
      - app_mode
      - base_openai_api
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

    tests/test_actions_and_orchestrator.py expects:

      - info["type"] == "relay.info"
      - info["relay"]["name"] is a non-empty str
      - info["relay"]["app_mode"] is a non-empty str
      - info["relay"]["environment"] is a non-empty str
      - info["upstream"]["base_url"] and ["default_model"] are non-empty str
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
        # Extra top-level fields; tests may or may not use these.
        "app_mode": base["app_mode"],
        "environment": base["environment"],
        "base_openai_api": base["base_openai_api"],
    }


# ---------------------------------------------------------------------------
# /actions/ping and /v1/actions/ping
# ---------------------------------------------------------------------------

@router.get("/actions/ping")
@router.get("/v1/actions/ping")
async def actions_ping() -> JSONResponse:
    """
    Lightweight health endpoint used by tests.

    Contract:
      - HTTP 200
      - JSON with:
          source == "chatgpt-team-relay"
          status == "ok"
          app_mode: non-empty str
          environment: non-empty str
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


# ---------------------------------------------------------------------------
# /actions/relay_info (flat) and /v1/actions/relay_info (structured)
# ---------------------------------------------------------------------------

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

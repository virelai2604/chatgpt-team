from __future__ import annotations

import os
import platform
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter()


def _now_iso() -> str:
    # Keep UTC, tests only check it's a non-empty string.
    return datetime.utcnow().isoformat()


def _base_env() -> Dict[str, str]:
    """
    Core environment info that tests assert on.
    """
    return {
        "app_mode": os.getenv("APP_MODE", "dev"),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "base_openai_api": os.getenv("OPENAI_API_BASE", "https://api.openai.com"),
    }


def _relay_name() -> str:
    return os.getenv("RELAY_NAME", "chatgpt-team-relay")


# ---------------------------------------------------------------------------
# Non-versioned Actions endpoints (/actions/...)
# ---------------------------------------------------------------------------


@router.get("/actions/ping")
async def actions_ping() -> Dict[str, Any]:
    """
    Lightweight health endpoint used by tests/test_tools_and_actions_routes.py.
    """
    base = _base_env()
    return {
        "source": "chatgpt-team-relay",
        "status": "ok",
        "timestamp": _now_iso(),
        **base,
    }


@router.get("/actions/relay_info")
async def actions_relay_info_root() -> Dict[str, Any]:
    """
    Simple relay info used by tools-and-actions tests.

    Must include at least:
      - relay_name
      - environment
      - app_mode
      - base_openai_api
    """
    base = _base_env()
    return {
        "relay_name": _relay_name(),
        **base,
    }


# ---------------------------------------------------------------------------
# Versioned Actions endpoints (/v1/actions/...)
# ---------------------------------------------------------------------------


@router.get("/v1/actions/ping")
async def actions_ping_v1() -> Dict[str, Any]:
    """
    /v1/actions/ping – used by tests/test_actions_and_orchestrator.py.

    Expected shape (at minimum):
      {
        "object": "actions.ping",
        "source": "chatgpt-team-relay",
        "status": "ok",
        "app_mode": "...",
        "environment": "...",
        "base_openai_api": "...",
        "timestamp": "..."
      }
    """
    base = _base_env()
    return {
        "object": "actions.ping",
        "source": "chatgpt-team-relay",
        "status": "ok",
        "timestamp": _now_iso(),
        **base,
    }


@router.get("/v1/actions/relay_info")
async def actions_relay_info_v1() -> Dict[str, Any]:
    """
    Structured relay metadata for Actions / toolchains.

    Expected (from tests/test_actions_and_orchestrator.py):
      info["type"] == "relay.info"
      info["relay"]["name"], ["environment"], ["app_mode"], ["base_openai_api"]
      info["system"] is a dict with basic system info
    """
    base = _base_env()

    relay = {
        "name": _relay_name(),
        "environment": base["environment"],
        "app_mode": base["app_mode"],
        "base_openai_api": base["base_openai_api"],
    }

    system = {
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "platform_release": platform.release(),
    }

    build = {
        "bifl_version": os.getenv("BIFL_VERSION", "unknown"),
        "build_channel": os.getenv("BUILD_CHANNEL", "unknown"),
        "version_source": os.getenv("VERSION_SOURCE", "unknown"),
        "git_sha": os.getenv("GIT_SHA", "unknown"),
        "build_date": os.getenv("BUILD_DATE", _now_iso()),
    }

    return {
        "type": "relay.info",
        "relay": relay,
        "system": system,
        "build": build,
        # Extra top-level copies for convenience; tests may or may not use these.
        "app_mode": base["app_mode"],
        "environment": base["environment"],
        "base_openai_api": base["base_openai_api"],
    }

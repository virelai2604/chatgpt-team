from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


def _health_payload() -> Dict[str, Any]:
    """
    Health contract expected by the current tests:
      - object/status
      - environment/default_model/timestamp
      - relay/openai/meta dicts
    """
    ts = datetime.now(timezone.utc).isoformat()

    environment = getattr(settings, "ENVIRONMENT", "unknown")
    app_mode = getattr(settings, "APP_MODE", "unknown")
    default_model = getattr(settings, "DEFAULT_MODEL", None)

    return {
        "object": "health",
        "status": "ok",
        "environment": environment,
        "default_model": default_model,
        "timestamp": ts,
        "relay": {
            "app_mode": app_mode,
            "auth_enabled": bool(getattr(settings, "RELAY_AUTH_ENABLED", False)),
        },
        "openai": {
            "base_url": getattr(settings, "OPENAI_BASE_URL", None),
            "has_api_key": bool(getattr(settings, "OPENAI_API_KEY", "")),
        },
        "meta": {
            "python": sys.version.split()[0],
        },
    }


@router.get("/")
async def root() -> Dict[str, Any]:
    return _health_payload()


@router.get("/health")
async def health() -> Dict[str, Any]:
    return _health_payload()


@router.get("/v1/health")
async def v1_health() -> Dict[str, Any]:
    return _health_payload()

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


def _health_payload() -> Dict[str, Any]:
    """
    Health contract used by:
      - GET /
      - GET /health
      - GET /v1/health

    Tests expect:
      - object == "health"
      - status == "ok"
      - environment, default_model, timestamp keys
      - relay/openai/meta are dicts
    """
    now = datetime.now(timezone.utc).isoformat()

    environment = getattr(settings, "ENVIRONMENT", None) or getattr(settings, "APP_MODE", None) or "unknown"
    default_model = getattr(settings, "DEFAULT_MODEL", None) or "unknown"

    return {
        "object": "health",
        "status": "ok",
        "environment": environment,
        "default_model": default_model,
        "timestamp": now,
        "relay": {
            "app_mode": getattr(settings, "APP_MODE", None),
            "auth_enabled": bool(getattr(settings, "RELAY_AUTH_ENABLED", False)),
            "auth_header": getattr(settings, "RELAY_AUTH_HEADER", None),
            "relay_key_configured": bool(getattr(settings, "RELAY_KEY", None)),
        },
        "openai": {
            "base_url": getattr(settings, "OPENAI_BASE_URL", None),
            "api_key_configured": bool(getattr(settings, "OPENAI_API_KEY", None)),
        },
        "meta": {},
    }


@router.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    return _health_payload()


@router.get("/health")
async def health() -> Dict[str, Any]:
    return _health_payload()


@router.get("/v1/health")
async def v1_health() -> Dict[str, Any]:
    return _health_payload()

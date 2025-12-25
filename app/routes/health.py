from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])

_START_TIME = time.time()


def _health_payload() -> Dict[str, Any]:
    now = datetime.now(timezone.utc)

    return {
        "object": "health",
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "default_model": settings.DEFAULT_MODEL,
        "timestamp": now.isoformat(),
        # Nested structures expected by tests
        "relay": {
            "name": settings.RELAY_NAME,
            "app_mode": settings.APP_MODE,
            "auth_enabled": bool(getattr(settings, "RELAY_AUTH_ENABLED", False)),
        },
        "openai": {
            "base_url": settings.OPENAI_BASE_URL,
        },
        "meta": {
            "uptime_seconds": round(time.time() - _START_TIME, 3),
        },
    }


@router.get("/", summary="Health check")
async def root_ping() -> Dict[str, Any]:
    return _health_payload()


@router.get("/health", summary="Health check")
async def health() -> Dict[str, Any]:
    return _health_payload()


@router.get("/v1/health", summary="Health check")
async def v1_health() -> Dict[str, Any]:
    return _health_payload()

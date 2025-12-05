# app/routes/health.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


def _health_payload() -> Dict[str, Any]:
    settings = get_settings()
    default_model = (
        # Prefer explicit env override, then fall back to a reasonable default.
        # This does not have to be in Settings for now.
        __import__("os").getenv("DEFAULT_MODEL", "gpt-5.1-mini")
    )

    return {
        "object": "health",
        "status": "ok",
        "environment": settings.environment,
        "default_model": default_model,
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project_name": settings.project_name,
        },
    }


@router.get("/health")
async def health_root() -> Dict[str, Any]:
    """
    Simple root health check for the relay.
    """
    return _health_payload()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    """
    Namespaced health check under /v1 for clients that expect that shape.
    """
    return _health_payload()

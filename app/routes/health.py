# app/routes/health.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


def _base_status() -> Dict[str, Any]:
    """
    Base health payload used by both /health and /v1/health.

    Tests expect:
      - top-level "object" == "health"
      - top-level "status" == "ok"
      - top-level "environment" key
      - top-level "default_model" key
      - nested "relay", "upstream", "meta" objects
    """
    return {
        # Top-level fields required by tests
        "object": "health",
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "default_model": settings.DEFAULT_MODEL,

        # Structured detail
        "relay": {
            "name": settings.RELAY_NAME,
            "environment": settings.ENVIRONMENT,
            "app_mode": settings.APP_MODE,
            "default_model": settings.DEFAULT_MODEL,
            "realtime_model": settings.REALTIME_MODEL,
        },
        "upstream": {
            "api_base": str(settings.OPENAI_API_BASE),
            "assistants_beta": settings.OPENAI_ASSISTANTS_BETA,
            "realtime_beta": settings.OPENAI_REALTIME_BETA,
        },
        "meta": {
            "python_version": settings.PYTHON_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/health")
async def health_root() -> Dict[str, Any]:
    """
    Simple non-versioned health endpoint.
    """
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    """
    Versioned health endpoint, matching the /v1 namespace.
    """
    return _base_status()

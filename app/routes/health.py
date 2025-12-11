# app/routes/health.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


def _base_status() -> Dict[str, Any]:
    """
    Base health payload used by '/', '/health', and '/v1/health'.

    Tests expect, at minimum:
      - top-level "object" == "health"
      - top-level "status" == "ok"
      - top-level "environment"
      - top-level "default_model"
      - top-level "timestamp"
      - nested "relay" object
      - nested "openai" object
      - nested "meta" object
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        # Top-level fields required by tests
        "object": "health",
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "default_model": settings.DEFAULT_MODEL,
        # Simple, always-present timestamp for quick checks
        "timestamp": now_iso,

        # Relay information
        "relay": {
            "name": settings.RELAY_NAME,
            "environment": settings.ENVIRONMENT,
            "app_mode": settings.APP_MODE,
            "default_model": settings.DEFAULT_MODEL,
            "realtime_model": settings.REALTIME_MODEL,
        },

        # Upstream OpenAI configuration – tests look for this key name
        "openai": {
            "api_base": str(settings.OPENAI_API_BASE),
            "assistants_beta": settings.OPENAI_ASSISTANTS_BETA,
            "realtime_beta": settings.OPENAI_REALTIME_BETA,
        },

        # Extra diagnostic metadata (can evolve over time)
        "meta": {
            "python_version": settings.PYTHON_VERSION,
            "timestamp": now_iso,
        },
    }


@router.get("/")
async def health_root() -> Dict[str, Any]:
    """
    Root health endpoint – public and used by integration tests as '/'.
    """
    return _base_status()


@router.get("/health")
async def health_plain() -> Dict[str, Any]:
    """
    Simple, non-versioned health endpoint.
    """
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    """
    Versioned health endpoint, matching the /v1 namespace.
    """
    return _base_status()

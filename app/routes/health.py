# app/routes/health.py

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


# Sensible defaults; callers can override via environment if desired.
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-5.1-mini") or "gpt-5.1-mini"
REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4o-realtime-preview") or "gpt-4o-realtime-preview"


def _base_status() -> Dict[str, Any]:
    """
    Base health payload used by both /health and /v1/health.

    Top-level fields are kept simple (matching tests), while nested sections
    provide richer introspection for operators.
    """
    now = datetime.now(timezone.utc).isoformat()

    return {
        # Tests expect these:
        "object": "health",
        "status": "ok",
        "environment": settings.environment,
        "default_model": DEFAULT_MODEL,
        # Additional structured info (not required by tests, but useful in practice)
        "relay": {
            "project_name": settings.project_name,
            "environment": settings.environment,
        },
        "upstream": {
            "base_url": settings.openai_base_url,
            "organization": settings.openai_organization,
            "realtime_model": REALTIME_MODEL,
        },
        "meta": {
            "timestamp": now,
        },
    }


@router.get("/health")
async def health_root() -> Dict[str, Any]:
    """
    Root health endpoint.

    Simple, unauthenticated liveness probe for load balancers and basic checks.
    """
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    """
    Versioned health endpoint.

    Used by tests and by clients that expect a /v1-prefixed path alongside other APIs.
    """
    return _base_status()

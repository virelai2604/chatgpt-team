# app/routes/health.py

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


def _base_status() -> Dict[str, Any]:
    """
    Canonical health payload for the relay and upstream OpenAI API.

    Exposes top-level keys that tests and dashboards expect:
      - object: "health"
      - status: "ok"
      - environment: e.g. "development" / "production"
      - default_model: primary model used by the relay
      - realtime_model: default Realtime model
    """
    default_model = os.getenv("DEFAULT_MODEL", "gpt-5.1-mini")
    realtime_model = os.getenv("REALTIME_MODEL", "gpt-4.1-mini")

    return {
        "object": "health",
        "status": "ok",
        "environment": settings.environment,
        "default_model": default_model,
        "realtime_model": realtime_model,
        "relay": {
            "project_name": settings.project_name,
            "debug": settings.debug,
        },
        "upstream": {
            "api_base": settings.openai_base_url,
            "organization": settings.openai_organization,
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/health")
async def health_root() -> Dict[str, Any]:
    """
    Legacy root health endpoint.
    """
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    """
    Versioned health endpoint under /v1 for clients that expect API-style paths.
    """
    return _base_status()

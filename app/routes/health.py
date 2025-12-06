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
    Canonical health payload for the relay.

    - Matches tests/test_health_and_tools.py expectations:
        object == "health"
        status == "ok"
        "environment" in root
        "default_model" in root
    - Also exposes richer nested diagnostic data for observability.
    """
    # Default model is driven by env for flexibility and "buy-it-for-life" tuning.
    # If unset, fall back to a sensible modern default.
    default_model = os.getenv("DEFAULT_MODEL", "gpt-5.1-codex-max")

    return {
        # Test-facing top-level fields
        "object": "health",
        "status": "ok",
        "environment": settings.environment,
        "default_model": default_model,
        # Relay metadata
        "relay": {
            "project_name": settings.project_name,
            "environment": settings.environment,
        },
        # Upstream OpenAI metadata
        "upstream": {
            "api_base": settings.openai_base_url,
            "organization": settings.openai_organization,
        },
        # Diagnostics
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/health")
async def health_root() -> Dict[str, Any]:
    """
    Legacy root health endpoint.

    Kept for convenience; main tests target /v1/health but some tooling
    may still probe /health.
    """
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    """
    Primary health endpoint expected by tests and external tooling.
    """
    return _base_status()

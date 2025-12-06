# app/routes/health.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import get_settings

settings = get_settings()

router = APIRouter(tags=["health"])


def _base_status() -> Dict[str, Any]:
    """
    Canonical health payload.

    This is shaped to satisfy tests/test_health_and_tools.py:
      - object == "health"
      - status == "ok"
      - environment present
      - default_model present

    It also exposes some extra relay + upstream metadata, which is backward‑compatible.
    """
    # You can tune this default model string; tests only require the field to exist.
    default_model = settings.default_model
    if not default_model:
        # Fallback: a reasonable default aligned with your relay purpose
        # (change if you standardise on a different primary model).
        default_model = "gpt-5.1-codex-max"

    now_utc = datetime.now(timezone.utc).isoformat()

    return {
        "object": "health",
        "status": "ok",
        "environment": settings.environment,
        "default_model": default_model,
        "relay": {
            "project_name": settings.project_name,
            "environment": settings.environment,
        },
        "upstream": {
            "api_base": settings.openai_base_url,
            "organization": settings.openai_organization,
        },
        "meta": {
            "timestamp": now_utc,
        },
    }


@router.get("/health")
async def health_root() -> Dict[str, Any]:
    """
    Simple root health check, convenient for curl and uptime probes.
    """
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    """
    Versioned health endpoint used in the test suite.
    """
    return _base_status()

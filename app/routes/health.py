# app/routes/health.py

from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


def _health_payload() -> Dict[str, Any]:
    """
    Build a compact, test-friendly health payload.

    This matches tests/test_health_and_tools.py expectations:
      - object == "health"
      - status == "ok"
      - environment present
      - default_model present
    """
    environment = getattr(settings, "environment", "development") or "development"
    # Default model can be overridden via env; otherwise use a sensible OpenAI default
    default_model = os.getenv("DEFAULT_MODEL", "gpt-4.1-mini")

    return {
        "object": "health",
        "status": "ok",
        "environment": environment,
        "default_model": default_model,
    }


@router.get("/health")
@router.get("/v1/health")
async def health() -> Dict[str, Any]:
    """
    Health endpoint available under both /health and /v1/health.

    Returns a simple JSON payload summarising relay status and configuration.
    """
    return _health_payload()

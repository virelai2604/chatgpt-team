# app/routes/health.py

from __future__ import annotations

import os
from typing import Any, Dict

from fastapi import APIRouter
from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix="/v1",
    tags=["health"],
)


def _base_status() -> Dict[str, Any]:
    """
    Canonical health payload used by tests and observability.

    Shape is intentionally simple and stable:
      - object: "health"
      - status: "ok" | "degraded" | "error"
      - environment: a short label like "dev", "staging", "prod"
      - default_model: the primary Responses model configured in the relay
    """
    environment = os.getenv("RELAY_ENV", "dev")
    default_model = os.getenv("DEFAULT_MODEL", "gpt-5.1-mini")

    return {
        "object": "health",
        "status": "ok",
        "environment": environment,
        "default_model": default_model,
    }


@router.get("/health")
async def health_v1() -> Dict[str, Any]:
    """
    /v1/health – primary health endpoint used by tests and external monitors.
    """
    payload = _base_status()
    logger.info("Health check: %s", payload)
    return payload

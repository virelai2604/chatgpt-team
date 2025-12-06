# app/routes/health.py

from __future__ import annotations

from datetime import datetime, timezone
import platform
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])

_settings = get_settings()


def _health_payload() -> Dict[str, Any]:
    """
    Minimal, test-aligned health payload with room for richer metadata.

    tests/test_health_and_tools.py asserts:
      - object == "health"
      - status == "ok"
      - "environment" in payload
      - "default_model" in payload
    """
    # Derive defaults from env; customise as needed.
    environment = _settings.environment
    default_model = (
        # If you later add this to Settings, prefer that:
        getattr(_settings, "default_model", None)
        or "gpt-5.1-codex-max"  # safe default for now; adjust to your canonical model
    )

    return {
        "object": "health",
        "status": "ok",
        "environment": environment,
        "default_model": default_model,
        "meta": {
            "project_name": _settings.project_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "python_version": platform.python_version(),
        },
    }


@router.get("/health")
async def health_root() -> Dict[str, Any]:
    """
    Backwards-compatible root health probe.
    """
    return _health_payload()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    """
    OpenAI-style health endpoint used by tests.
    """
    return _health_payload()

# app/routes/health.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


def _base_status() -> Dict[str, Any]:
    """
    Minimal, stable health payload that matches tests and is API‑friendly.
    """
    return {
        "object": "health",
        "status": "ok",
        "environment": settings.environment,
        "default_model": "gpt-5.1-codex-max",
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
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    """
    Versioned health endpoint for clients that expect /v1/* shape.
    """
    return _base_status()

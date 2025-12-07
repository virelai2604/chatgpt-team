# app/routes/health.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


def _base_status() -> Dict[str, Any]:
    return {
        "status": "ok",
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
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    return _base_status()
# app/routes/health.py

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["health"])


def _base_status() -> Dict[str, Any]:
    return {
        "status": "ok",
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
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    return _base_status()

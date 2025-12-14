# app/routes/health.py
from __future__ import annotations

import platform
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter

from app.core.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def _safe_get(settings: Any, *names: str, default: Any = None) -> Any:
    for name in names:
        if hasattr(settings, name):
            val = getattr(settings, name)
            if val is not None:
                return val
    return default


def _base_status() -> Dict[str, Any]:
    s = get_settings()
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": _safe_get(s, "relay_name", "RELAY_NAME", default="chatgpt-team-relay"),
        "environment": _safe_get(s, "environment", "ENVIRONMENT", default="unknown"),
        "version": _safe_get(s, "version", "BIFL_VERSION", default="unknown"),
        "default_model": _safe_get(s, "default_model", "DEFAULT_MODEL", default=None),
        "realtime_model": _safe_get(s, "realtime_model", "REALTIME_MODEL", default=None),
        "openai_base_url": str(
            _safe_get(s, "openai_base_url", "OPENAI_API_BASE", default="https://api.openai.com/v1")
        ),
        # Never hard-crash health on config drift:
        "python_version": _safe_get(s, "PYTHON_VERSION", default=platform.python_version()),
    }


@router.get("/health")
async def health_root() -> Dict[str, Any]:
    return _base_status()


@router.get("/v1/health")
async def health_v1() -> Dict[str, Any]:
    return _base_status()

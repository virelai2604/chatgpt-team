# ==========================================================
# app/routes/relay_status.py — Relay Health & Diagnostics
# ==========================================================
# Provides runtime information about the relay, including
# version, uptime, active tools, and model availability.
# Mirrors the OpenAI system route `/v1/relay/status`.
# ==========================================================

import os
import platform
import time
from fastapi import APIRouter
from app.api.tools_api import TOOL_REGISTRY

START_TIME = time.time()

router = APIRouter(prefix="/v1/relay", tags=["Relay"])

@router.get("/status")
async def relay_status():
    """
    Return current system status and runtime metadata.
    """
    uptime = time.time() - START_TIME
    return {
        "object": "relay.status",
        "status": "ok",
        "uptime_seconds": round(uptime, 2),
        "python_version": platform.python_version(),
        "relay_version": os.getenv("RELAY_VERSION", "2025-10"),
        "available_tools": list(TOOL_REGISTRY.keys()),
        "environment": os.getenv("RELAY_ENV", "production")
    }

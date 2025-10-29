# ==========================================================
# app/routes/relay_status.py — Relay Status Endpoint
# ==========================================================
# Returns relay uptime, version, and diagnostic metadata.
# Mirrors OpenAI relay schema used in ChatGPT Team relays.
# ==========================================================

import os, time, platform
from datetime import datetime
from fastapi import APIRouter
from app.api.tools_api import TOOL_REGISTRY

router = APIRouter(prefix="/v1/relay", tags=["Relay"])

START_TIME = time.time()

@router.get("/status")
async def relay_status():
    """
    Returns a status object describing the relay’s runtime state.
    OpenAI-style structure for diagnostic introspection.
    """
    uptime = round(time.time() - START_TIME, 2)
    return {
        "object": "relay.status",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "uptime_seconds": uptime,
        "version": os.getenv("BIFL_VERSION", "v2.3.4-fp"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "tools_count": len(TOOL_REGISTRY),
        "tools": [t["id"] for t in TOOL_REGISTRY],
        "default_model": os.getenv("DEFAULT_MODEL", "gpt-4o-mini"),
        "mode": os.getenv("APP_MODE", "production"),
        "status": "ok"
    }

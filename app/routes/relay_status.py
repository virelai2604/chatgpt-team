# ==========================================================
# app/routes/relay_status.py — Relay Status Endpoint
# ==========================================================
# Returns relay uptime, version, and diagnostic metadata.
# Mirrors OpenAI relay schema used in ChatGPT Team relays.
# ==========================================================

import sys
import time
import platform
import os
from fastapi import APIRouter
from app.api.tools_api import TOOL_REGISTRY

router = APIRouter(prefix="/v1/relay", tags=["Relay"])

# Record the relay’s boot time for uptime tracking
START_TIME = time.time()

@router.get("/status")
async def relay_status():
    """
    Returns a status object describing the relay’s runtime state.
    Expected fields:
      - bifl_version (str)
      - uptime_seconds (float)
      - available_tools (list)
    Also includes diagnostic metadata for introspection.
    """
    uptime = round(time.time() - START_TIME, 2)

    return {
        "object": "relay.status",
        "environment": os.getenv("ENVIRONMENT", "production"),
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "uptime_seconds": uptime,
        "bifl_version": "v2.3.4-fp",
        "available_tools": list(TOOL_REGISTRY.keys()),
    }

# ==========================================================
# app/routes/register_routes.py — Ground Truth Route Registry (2025.10)
# ==========================================================
"""
Registers all /v1/* routes for the ChatGPT Team Relay.

Implements:
  • Core API routes (responses, conversations, files, realtime, etc.)
  • Tool invocation via /v1/responses/tools/*
  • Forward + passthrough proxy routes
  • Full compliance with the OpenAI API 2025 spec
"""

import logging
from fastapi import FastAPI

# ----------------------------------------------------------
# Import core route definitions
# ----------------------------------------------------------
from app.routes import (
    models,
    files,
    responses,
    conversations,
    realtime,
    vector_stores,
)

# ----------------------------------------------------------
# Import proxy + forwarder APIs
# ----------------------------------------------------------
from app.api import (
    passthrough_proxy,
)

logger = logging.getLogger("register_routes")


# ----------------------------------------------------------
# Route Registration Function
# ----------------------------------------------------------
def register_routes(app: FastAPI):
    """Attach all FastAPI route modules to the main application."""
    logger.info("🔗 Registering /v1 API routes...")

    # ------------------------------------------------------
    # Core OpenAI-Compatible Routes
    # ------------------------------------------------------
    app.include_router(models.router)
    app.include_router(files.router)
    app.include_router(responses.router)
    app.include_router(conversations.router)
    app.include_router(realtime.router)
    app.include_router(vector_stores.router)

    # ------------------------------------------------------
    # Tool Execution (Dynamic)
    # ------------------------------------------------------
    # Tools are not static routers — they’re invoked dynamically
    # by /v1/responses/tools/<tool_name> within responses.py.
    logger.info("🧠 Tool execution handled dynamically via /v1/responses/tools")

    # ------------------------------------------------------
    # Proxy Fallbacks (OpenAI passthrough)
    # ------------------------------------------------------
    app.include_router(passthrough_proxy.router)

    # ------------------------------------------------------
    # Route Summary Log
    # ------------------------------------------------------
    total_routes = len(app.router.routes)
    prefixes = sorted(set(
        r.path.split("/")[1] for r in app.router.routes if r.path != "/"
    ))

    logger.info(f"✅ Registered {total_routes} routes.")
    logger.info("🔗 Active route prefixes:")
    for prefix in prefixes:
        logger.info(f"   • /{prefix}")

    logger.info("✅ All /v1 routes registered successfully.")

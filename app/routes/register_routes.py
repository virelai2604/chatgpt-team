# ==========================================================
# app/routes/register_routes.py — Ground Truth Route Registry (v2025.11)
# ==========================================================
"""
Registers all /v1/* routes for the ChatGPT Team Relay.

Implements:
  • Core API routes (responses, conversations, files, realtime, etc.)
  • Dynamic tool invocation via /v1/responses/tools/*
  • Forward + passthrough proxy routes
  • Fully compliant with OpenAI 2025 Ground Truth API spec
"""

import logging
from fastapi import FastAPI

# ----------------------------------------------------------
# Import routers directly (no circular package imports)
# ----------------------------------------------------------
from app.routes.models import router as models_router
from app.routes.files import router as files_router
from app.routes.responses import router as responses_router
from app.routes.conversations import router as conversations_router
from app.routes.realtime import router as realtime_router
from app.routes.vector_stores import router as vector_stores_router
from app.routes.tools import router as tools_router

# Proxy routes
from app.api.passthrough_proxy import router as passthrough_router

logger = logging.getLogger("register_routes")


def register_routes(app: FastAPI):
    """Attach all FastAPI route modules to the main application."""
    logger.info("🔗 Registering /v1 API routes...")

    # Core API Routers
    app.include_router(models_router)
    app.include_router(files_router)
    app.include_router(responses_router)
    app.include_router(conversations_router)
    app.include_router(realtime_router)
    app.include_router(vector_stores_router)
    app.include_router(tools_router)

    # Tool Execution is dynamic inside /v1/responses/tools/*
    logger.info("🧠 Tool execution handled dynamically via /v1/responses/tools")

    # Passthrough proxy routes (OpenAI passthrough)
    app.include_router(passthrough_router)

    # ------------------------------------------------------
    # Route Summary
    # ------------------------------------------------------
    total_routes = len(app.router.routes)
    prefixes = sorted(set(
        r.path.split("/")[1] for r in app.router.routes if r.path and r.path != "/"
    ))

    logger.info(f"✅ Registered {total_routes} routes.")
    logger.info("🔗 Active route prefixes:")
    for prefix in prefixes:
        logger.info(f"   • /{prefix}")

    logger.info("✅ All /v1 routes registered successfully.")

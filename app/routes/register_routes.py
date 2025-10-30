# ==========================================================
# app/routes/register_routes.py — Ground Truth Edition (2025.10)
# ==========================================================
"""
Registers all API route modules for the ChatGPT Team Relay.

Order matters:
  - Specific routes (models, files, vector stores, responses, realtime)
    are mounted first.
  - Passthrough proxy routes must be registered last to catch all
    unmatched /v1/* calls.
"""

from fastapi import FastAPI
from app.routes import (
    models,
    files,
    vector_stores,
    responses,
    realtime,
    relay_status,
    tools
)
from app.api.passthrough_proxy import router as passthrough_router


# ----------------------------------------------------------
# Route registration function
# ----------------------------------------------------------
def register_routes(app: FastAPI):
    """
    Attaches all endpoint routers to the FastAPI app
    in the correct order for full OpenAI API compatibility.
    """

    # Core OpenAI-compatible endpoints
    app.include_router(models.router)          # /v1/models
    app.include_router(files.router)           # /v1/files
    app.include_router(vector_stores.router)   # /v1/vector_stores
    app.include_router(responses.router)       # /v1/responses (+ tools)
    app.include_router(realtime.router)        # /v1/realtime/*
    app.include_router(tools.router)           # /v1/responses/tools

    # Relay meta/status routes (optional)
    app.include_router(relay_status.router)

    # Passthrough proxy — MUST be last
    app.include_router(passthrough_router)

    # ------------------------------------------------------
    # Root & Health Endpoints
    # ------------------------------------------------------
    @app.get("/", tags=["Meta"])
    async def root():
        """
        Root endpoint reporting relay status, version, and documentation URLs.
        Used by test_gt_all_endpoints.py::test_root_and_health
        """
        return {
            "service": "ChatGPT Team Relay",
            "status": "running",  # ✅ must include this exact field
            "version": "Ground Truth Edition v2025.10",
            "docs": "/docs",
            "openapi_yaml": "/v1/openapi.yaml",
            "health": "/health",
        }

    @app.get("/health", tags=["Health"])
    async def health():
        """
        Lightweight readiness probe for load balancers or CI tests.
        """
        return {"status": "ok", "version": "2025.10"}

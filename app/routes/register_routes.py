# ==========================================================
# register_routes.py — Central Route Registrar
# ==========================================================
"""
Registers all route modules for the ChatGPT Team Relay API.

Order matters:
  - Specific routes (models, files, responses, etc.) must be registered first.
  - The passthrough route must always be last to catch unmatched /v1/* requests.
"""

from fastapi import FastAPI
from app.routes import models, files, vector_stores, responses, realtime, relay_status
from app.api.passthrough_proxy import router as passthrough_router


def register_routes(app: FastAPI):
    """
    Attaches all endpoint routers to the FastAPI app
    in the correct order for Ground Truth compatibility.
    """

    app.include_router(models.router)
    app.include_router(files.router)
    app.include_router(vector_stores.router)
    app.include_router(responses.router)
    app.include_router(realtime.router)
    app.include_router(relay_status.router)

    # Passthrough proxy must be registered last
    app.include_router(passthrough_router)

    # Root and health endpoints
    @app.get("/")
    async def root():
        """
        Root endpoint reporting relay status and API version.
        """
        return {
            "service": "ChatGPT Team Relay",
            "status": "running",  # ✅ added for test expectation
            "version": "Ground Truth Edition v2025.10",
            "docs": "/docs",
            "openapi_yaml": "/v1/openapi.yaml",
        }

    @app.get("/health")
    async def health():
        """Lightweight readiness check."""
        return {"status": "ok"}

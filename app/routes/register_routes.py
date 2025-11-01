# ==========================================================
# app/routes/register_routes.py — Ground Truth Route Registrar (v2025.11)
# ==========================================================
"""
Registers all FastAPI route modules for the ChatGPT Team Relay.
Ensures OpenAI-compatible URL structure, schema consistency,
and passthrough fallback for future endpoints.
"""

from fastapi import FastAPI
from app.routes import (
    conversations,
    files,
    models,
    openapi_yaml,
    realtime,
    responses,
    vector_stores,
)
from app.api import passthrough_proxy

def register_routes(app: FastAPI) -> FastAPI:
    """Attach all /v1 routes to the FastAPI app."""

    print("\n[Relay] 🔗 Registering all /v1 API routes...")

    # -------------------------------
    # Core OpenAI-Compatible Endpoints
    # -------------------------------
    app.include_router(models.router, prefix="/v1", tags=["Models"])
    app.include_router(responses.router, prefix="/v1", tags=["Responses"])
    app.include_router(files.router, prefix="/v1", tags=["Files"])
    app.include_router(vector_stores.router, prefix="/v1", tags=["Vector Stores"])
    app.include_router(conversations.router, prefix="/v1", tags=["Conversations"])
    app.include_router(realtime.router, prefix="/v1", tags=["Realtime"])
    app.include_router(openapi_yaml.router, prefix="/v1", tags=["OpenAPI"])

    # -------------------------------
    # Passthrough Fallback (last)
    # -------------------------------
    app.include_router(passthrough_proxy.router, prefix="", tags=["Passthrough"])

    print(f"[Relay] ✅ Registered {len(app.routes)} routes successfully.\n")
    return app

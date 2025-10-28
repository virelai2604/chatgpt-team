# ==========================================================
# app/routes/register_routes.py — Central Route Registrar
# ==========================================================
# Collects and mounts all API route modules into the FastAPI
# application instance. Ensures proper namespace and prefixes.
# Mirrors the structure of OpenAI’s relay API.
# ==========================================================

from fastapi import FastAPI

# ----------------------------------------------------------
# Import route modules explicitly
# ----------------------------------------------------------
# app/api contains OpenAI-compatible endpoints
# app/routes contains internal meta and relay-specific endpoints
# ----------------------------------------------------------
from app.api import responses, passthrough_proxy
from app.routes.relay_status import router as relay_status_router
from app.routes.openapi_yaml import router as openapi_yaml_router


def register_routes(app: FastAPI):
    """
    Mount all relay and OpenAI-compatible routes to the FastAPI app.
    This is called from main.py during application initialization.
    """

    # ---------------------------------------------------------
    # ⚙️ Meta & relay-specific endpoints FIRST
    # ---------------------------------------------------------
    # These must be mounted before the passthrough proxy to ensure
    # /v1/relay/status and /v1/openapi.yaml are handled locally.
    app.include_router(relay_status_router)  # /v1/relay/status
    app.include_router(openapi_yaml_router)  # /v1/openapi.yaml

    # ---------------------------------------------------------
    # 🧩 Core OpenAI-compatible API mirrors
    # ---------------------------------------------------------
    # Mirrors endpoints such as /v1/responses, /v1/chat/completions, etc.
    app.include_router(responses.router)           # /v1/responses & /v1/responses/tools
    app.include_router(passthrough_proxy.router)   # /v1/chat/completions, /v1/models, etc.

    # ---------------------------------------------------------
    # 🌐 Root diagnostic route
    # ---------------------------------------------------------
    @app.get("/")
    async def root():
        """
        Root health and diagnostic endpoint.
        Mirrors the OpenAI relay’s basic status message.
        """
        return {
            "message": "ChatGPT Team Relay operational",
            "version": "v2.3.4-fp",
            "docs": "/docs",
            "openapi": "/v1/openapi.yaml",
        }

    return app

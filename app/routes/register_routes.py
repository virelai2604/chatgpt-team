# ==========================================================
# app/routes/register_routes.py — Central Route Registrar
# ==========================================================
# Collects and mounts all API route modules into the FastAPI
# application instance. Ensures proper namespace and prefixes.
# Mirrors the structure of OpenAI’s relay API.
# ==========================================================

from fastapi import FastAPI

# ----------------------------------------------------------
# Import API and route modules explicitly
# ----------------------------------------------------------
# app/api → OpenAI-compatible endpoints (/v1/responses, etc.)
# app/routes → internal meta endpoints (/v1/relay/status, /v1/openapi.yaml)
# ----------------------------------------------------------
from app.api import responses
from app.api import forward_openai as passthrough_proxy  # ✅ canonical import
from app.routes.relay_status import router as relay_status_router
from app.routes.openapi_yaml import router as openapi_yaml_router


def register_routes(app: FastAPI) -> FastAPI:
    """
    Mount all relay and OpenAI-compatible routes to the FastAPI app.
    This is invoked from main.py during application initialization.
    """

    # ---------------------------------------------------------
    # ⚙️ Meta & relay-specific endpoints FIRST
    # ---------------------------------------------------------
    # These must be mounted before the passthrough proxy to ensure
    # /v1/relay/status and /v1/openapi.yaml are handled locally.
    app.include_router(relay_status_router, prefix="/v1/relay")
    app.include_router(openapi_yaml_router)  # serves /v1/openapi.yaml

    # ---------------------------------------------------------
    # 🧩 Core OpenAI-compatible API mirrors
    # ---------------------------------------------------------
    # These endpoints mirror OpenAI’s schema to allow seamless
    # plugin registration and API compatibility.
    app.include_router(responses.router)          # /v1/responses & /v1/responses/tools
    app.include_router(passthrough_proxy.router)  # /v1/chat/completions, /v1/models, etc.

    # ---------------------------------------------------------
    # 🌐 Root diagnostic route
    # ---------------------------------------------------------
    @app.get("/", tags=["meta"])
    async def root():
        """
        Root health and diagnostic endpoint.
        Mirrors the OpenAI relay’s basic status message.
        """
        return {
            "message": "ChatGPT Team Relay operational ✅",
            "version": "v2.3.4-fp",
            "health": "/health",
            "docs": "/docs",
            "openapi": "/v1/openapi.yaml",
        }

    return app

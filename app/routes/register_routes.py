# ==========================================================
# app/routes/register_routes.py — Ground Truth Edition (Final)
# ==========================================================
"""
Registers all route modules for the ChatGPT Team Relay.
Covers all OpenAI-compatible endpoints and internal APIs.
"""

from fastapi import FastAPI

# Import public OpenAI-compatible routes
from . import (
    models,         # /v1/models
    files,          # /v1/files and /v1/files/images|videos
    vector_stores,  # /v1/vector_stores
    tools,          # /v1/responses/tools
    realtime,       # /v1/realtime
    responses,      # /v1/responses (core Responses API)
)

# Import internal relay-only APIs
from app.api import (
    tools_api,          # /v1/tools_api
    passthrough_proxy,  # /v1/{path:path} fallback
)


# ==========================================================
# Register All Routes
# ==========================================================
def register_routes(app: FastAPI):
    """
    Attach all API routes to the FastAPI app.
    The order matters — passthrough proxy must come last.
    """

    # ------------------------------
    # Public OpenAI-compatible API
    # ------------------------------

    # Models
    app.include_router(models.router)

    # Files and media endpoints
    app.include_router(files.router)

    # Vector Stores (semantic search / retrieval)
    app.include_router(vector_stores.router)

    # Tools API (part of /v1/responses per OpenAI spec)
    app.include_router(tools.router)

    # Realtime streaming endpoints
    app.include_router(realtime.router)

    # Core Responses API (streaming, chain wait, etc.)
    app.include_router(responses.router)

    # ------------------------------
    # Internal / Relay-Only APIs
    # ------------------------------

    # Local diagnostic API for relay tool registry
    app.include_router(tools_api.router)

    # Passthrough proxy — must be last to avoid intercepting real endpoints
    app.include_router(passthrough_proxy.router)

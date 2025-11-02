# ================================================================
# register_routes.py — Route Registration Hub
# ================================================================
# Collects and mounts all endpoint routers for the ChatGPT Team Relay.
# This file ensures clean route registration, avoiding circular imports.
#
# Compatible with:
#   - openai-python SDK v2.6.1
#   - openai-node SDK v6.7.0
# ================================================================

from fastapi import FastAPI

# Import each route module directly (no self-import)
from app.routes import (
    conversations,
    embeddings,
    files,
    models,
    realtime,
    responses,
    vector_stores
)

# ================================================================
# Route Registration Function
# ================================================================
def register_routes(app: FastAPI):
    """
    Attach all primary API routers to the FastAPI application instance.
    Each router corresponds to an OpenAI-compatible endpoint family.
    """

    # --- Core OpenAI-compatible endpoints ---
    app.include_router(models.router, prefix="", tags=["models"])
    app.include_router(embeddings.router, prefix="", tags=["embeddings"])
    app.include_router(files.router, prefix="", tags=["files"])
    app.include_router(vector_stores.router, prefix="", tags=["vector_stores"])
    app.include_router(realtime.router, prefix="", tags=["realtime"])
    app.include_router(responses.router, prefix="", tags=["responses"])
    app.include_router(conversations.router, prefix="", tags=["conversations"])

    # --- Response aliases (for SDK compatibility) ---
    # These mirror /v1/responses → /responses for legacy clients
    app.include_router(responses.responses_router, prefix="", tags=["responses"])

    # --- Startup confirmation ---
    print("✅ All route modules successfully registered with FastAPI.")

# ================================================================
# Notes
# ================================================================
# 1. This module intentionally avoids importing `register_routes` itself.
#    Doing so would create a circular import between main.py and this file.
#
# 2. Each route module (e.g. models.py, responses.py) defines its own
#    FastAPI APIRouter instance named `router`.
#
# 3. The inclusion order matters only for fallback and universal passthrough
#    behavior, which are handled in main.py after this function is called.
# ================================================================

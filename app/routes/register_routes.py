# ==========================================================
# app/routes/register_routes.py — Relay Route Registration
# ==========================================================
# Imports and mounts all public API routes and orchestration endpoints.
# Defines the callable REST API surface of the relay.
# ==========================================================

from app.routes import (
    core,
    chat,
    models,
    files,
    vector_stores,
    realtime,
    relay_status,
    openapi,
    passthrough_proxy
)
from app.api import responses

def register_routes(app):
    """
    Mount all public and orchestration routes into the FastAPI app.
    """
    # ---- Public API routes ----
    app.include_router(core.router)            # /v1/core/ping
    app.include_router(chat.router)            # /v1/chat/completions
    app.include_router(models.router)          # /v1/models
    app.include_router(files.router)           # /v1/files*
    app.include_router(vector_stores.router)   # /v1/vector_stores*
    app.include_router(realtime.router)        # /v1/realtime/*
    app.include_router(relay_status.router)    # /v1/relay/status
    app.include_router(openapi.router)         # /v1/openapi.yaml

    # ---- Core Orchestrator ----
    app.include_router(responses.router)       # /v1/responses

    # ---- Universal Fallback ----
    app.include_router(passthrough_proxy.router)  # must be last

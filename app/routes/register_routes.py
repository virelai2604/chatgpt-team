"""
register_routes.py — Unified Router Registration
────────────────────────────────────────────────────────────
Automatically registers all /v1/* route modules in the relay.

Aligned with:
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0
  • OpenAI API Reference (2025-10)

Ensures all REST routes from app/routes and app/api are available:
  /v1/responses
  /v1/embeddings
  /v1/models
  /v1/files
  /v1/vector_stores
  /v1/conversations
  /v1/realtime/sessions/events
  /v1/tools/*
"""

from fastapi import FastAPI
from app.routes import (
    responses,
    embeddings,
    models,
    files,
    vector_stores,
    conversations,
    realtime,
)
from app.api import tools_api

# ------------------------------------------------------------
# Register all routers
# ------------------------------------------------------------
def register_all_routes(app: FastAPI):
    """Attach all routers to the FastAPI instance."""
    app.include_router(responses.router)
    app.include_router(embeddings.router)
    app.include_router(models.router)
    app.include_router(files.router)
    app.include_router(vector_stores.router)
    app.include_router(conversations.router)
    app.include_router(realtime.router)
    app.include_router(tools_api.router)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok"}

    # Root redirect (for SDK discovery)
    @app.get("/")
    async def root():
        return {"object": "relay", "version": "2025-10", "status": "online"}

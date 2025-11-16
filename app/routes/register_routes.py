"""
register_routes.py — Unified Router Registration (optional)
────────────────────────────────────────────────────────────
Utility to mount all routers on a FastAPI app.

Currently NOT used by app.main, because main wires routers
explicitly for clarity. Safe to keep as a helper.
"""

from fastapi import FastAPI

from app.api.tools_api import router as tools_router
from app.routes import (
    actions,
    conversations,
    embeddings,
    files,
    images,
    models,
    realtime,
    responses,
    vector_stores,
    videos,
)


def register_all_routes(app: FastAPI) -> None:
    # Meta / tools
    app.include_router(tools_router)

    # Relay-focus surfaces
    app.include_router(responses.router)
    app.include_router(conversations.router)
    app.include_router(files.router)
    app.include_router(vector_stores.router)
    app.include_router(embeddings.router)
    app.include_router(realtime.router)
    app.include_router(models.router)
    app.include_router(images.router)
    app.include_router(videos.router)
    app.include_router(actions.router)

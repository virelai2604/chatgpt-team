# app/routes/register_routes.py

from __future__ import annotations

from fastapi import FastAPI

from app.routes import (
    actions,
    batches,
    containers,
    conversations,
    files,
    health,
    images,
    realtime,
    vector_stores,
    videos,
)


def register_routes(app: FastAPI) -> None:
    """
    Central place to wire all "generic" route families that mostly forward
    to OpenAI via forward_openai_request.

    We deliberately *exclude* the typed /v1 endpoints that are already
    handled via app/api/routes.py (responses, embeddings, models, etc.)
    to avoid duplicate registrations.
    """
    # Health
    app.include_router(health.router)

    # File / vector / container families (generic proxying)
    app.include_router(files.router)
    app.include_router(vector_stores.router)
    app.include_router(containers.router)
    app.include_router(batches.router)

    # Conversation / realtime / actions
    app.include_router(conversations.router)
    app.include_router(realtime.router)
    app.include_router(actions.router)

    # Media extensions that are primarily pass-through
    app.include_router(images.router)
    app.include_router(videos.router)

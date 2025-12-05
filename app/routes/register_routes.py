# app/routes/register_routes.py

from __future__ import annotations

from fastapi import FastAPI

from app.api.tools_api import router as tools_router
from app.api.routes import router as api_fallback_router
from app.routes import (
    actions as actions_routes,
    containers as containers_routes,
    conversations as conversations_routes,
    embeddings as embeddings_routes,
    files as files_routes,
    health as health_routes,
    images as images_routes,
    models as models_routes,
    realtime as realtime_routes,
    responses as responses_routes,
    vector_stores as vector_stores_routes,
    videos as videos_routes,
)


def register_routes(app: FastAPI) -> None:
    """
    Central router wiring for the relay.

    Keeps all FastAPI `.include_router` calls in one place so that
    URL structure stays aligned with the OpenAI platform docs.
    """
    # Health / diagnostics
    app.include_router(health_routes.router)

    # Core OpenAI-style APIs
    app.include_router(responses_routes.router)
    app.include_router(conversations_routes.router)
    app.include_router(embeddings_routes.router)
    app.include_router(files_routes.router)
    app.include_router(models_routes.router)
    app.include_router(images_routes.router)
    app.include_router(videos_routes.router)
    app.include_router(vector_stores_routes.router)
    app.include_router(realtime_routes.router)
    app.include_router(containers_routes.router)

    # Tools + Actions
    app.include_router(tools_router)
    app.include_router(actions_routes.router)
    app.include_router(api_fallback_router)
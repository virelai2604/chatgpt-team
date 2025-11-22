from __future__ import annotations

from fastapi import FastAPI

from app.routes import (
    models as models_routes,
    embeddings as embeddings_routes,
    files as files_routes,
    images as images_routes,
    videos as videos_routes,
    vector_stores as vector_stores_routes,
    responses as responses_routes,
    realtime as realtime_routes,
    conversations as conversations_routes,
    actions as actions_routes,
)
from app.api import tools_api


def register_routes(app: FastAPI) -> None:
    """
    Central place to register all routers on the FastAPI app.
    """
    # OpenAI-compatible API surfaces
    app.include_router(models_routes.router)
    app.include_router(embeddings_routes.router)
    app.include_router(files_routes.router)
    app.include_router(images_routes.router)
    app.include_router(videos_routes.router)
    app.include_router(vector_stores_routes.router)
    app.include_router(responses_routes.router)
    app.include_router(realtime_routes.router)
    app.include_router(conversations_routes.router)

    # Local actions endpoints (/actions/* and /v1/actions/*)
    app.include_router(actions_routes.router)

    # Tools manifest endpoints (/v1/tools, /v1/tools/{id})
    app.include_router(tools_api.router)

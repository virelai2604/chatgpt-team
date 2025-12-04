# app/routes/register_routes.py
from __future__ import annotations

from fastapi import FastAPI

# Health routes
from app.routes.health import router as health_router

# Core OpenAI-compatible endpoints
from app.routes.responses import router as responses_router
from app.routes.embeddings import router as embeddings_router
from app.routes.files import router as files_router
from app.routes.models import router as models_router
from app.routes.images import router as images_router
from app.routes.videos import router as videos_router
from app.routes.vector_stores import router as vector_stores_router
from app.routes.conversations import router as conversations_router
from app.routes.containers import router as containers_router
from app.routes.realtime import router as realtime_router
from app.api.routes import router as api_router


# Tools + relay metadata
from app.api.tools_api import router as tools_router
from app.routes.actions import router as actions_router


def register_routes(app: FastAPI) -> None:
    """
    Register all FastAPI routers on the main application.

    This is the central wiring layer – any new route module should be added here.
    """
    # -------- Health --------
    app.include_router(health_router)

    # -------- OpenAI-compatible endpoints --------
    app.include_router(responses_router)
    app.include_router(embeddings_router)
    app.include_router(files_router)
    app.include_router(models_router)
    app.include_router(images_router)
    app.include_router(videos_router)
    app.include_router(vector_stores_router)
    app.include_router(conversations_router)
    app.include_router(realtime_router)
    app.include_router(containers_router)

    # -------- Tools + relay metadata --------
    app.include_router(tools_router)
    app.include_router(actions_router)
    app.include_router(api_router) 

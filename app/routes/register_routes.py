# app/routes/register_routes.py

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, FastAPI

# Local route families (generic pass‑through + extra capabilities)
from . import (
    actions,
    batches,
    containers,
    conversations,
    embeddings,
    files,
    health,
    images,
    models,
    realtime,
    responses,
    vector_stores,
    videos,
)

# SDK‑driven core OpenAI APIs and tools under /v1
from app.api import routes as api_routes
from app.api import sse as sse_routes
from app.api import tools_api as tools_routes


class _RouterLike(Protocol):
    """
    Minimal protocol for something that can have routers included.

    Both FastAPI and APIRouter satisfy this (they expose include_router()).
    """

    def include_router(self, router: APIRouter, **kwargs) -> None:  # pragma: no cover - protocol
        ...


def register_routes(app: _RouterLike) -> None:
    """
    Register all resource routers on the given FastAPI app or APIRouter.

    This centralises wiring so you can:

        from app.routes import register_routes
        register_routes(app)

    or:

        from fastapi import APIRouter
        from app.routes import register_routes

        router = APIRouter()
        register_routes(router)
    """

    # ------------------------------------------------------------------
    # Health – exposes both /health and /v1/health
    # ------------------------------------------------------------------
    app.include_router(health.router)

    # ------------------------------------------------------------------
    # SDK‑driven core model APIs (Python SDK /v1 layer)
    # ------------------------------------------------------------------
    # /v1/responses, /v1/embeddings, /v1/images, /v1/videos, /v1/models
    app.include_router(api_routes.router)

    # /v1/responses:stream – SSE streaming wrapper for Responses API
    app.include_router(sse_routes.router)

    # /v1/tools – serve tools manifest in OpenAI list format
    app.include_router(tools_routes.router)

    # ------------------------------------------------------------------
    # Core REST resources (generic pass‑through via forward_openai_request)
    # ------------------------------------------------------------------
    app.include_router(files.router)
    app.include_router(conversations.router)
    app.include_router(containers.router)
    app.include_router(batches.router)

    # ------------------------------------------------------------------
    # New capability surfaces
    # ------------------------------------------------------------------
    app.include_router(actions.router)
    app.include_router(vector_stores.router)

    # ------------------------------------------------------------------
    # Legacy / transitional SDK routes
    # (kept for compatibility if you still hit these modules directly)
    # ------------------------------------------------------------------
    app.include_router(responses.router)
    app.include_router(embeddings.router)
    app.include_router(images.router)
    app.include_router(videos.router)
    app.include_router(models.router)

    # ------------------------------------------------------------------
    # Realtime (HTTP + WS proxy)
    # ------------------------------------------------------------------
    app.include_router(realtime.router)

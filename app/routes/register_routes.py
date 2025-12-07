# app/routes/register_routes.py

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter

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

    Example:

        from fastapi import FastAPI
        from app.routes import register_routes

        app = FastAPI()
        register_routes(app)
    """

    # Health exposes both /health and /v1/health
    app.include_router(health.router)

    # Core REST resources (generic pass‑through via forward_openai_request)
    app.include_router(files.router)
    app.include_router(conversations.router)
    app.include_router(containers.router)
    app.include_router(batches.router)

    # New capability surfaces
    app.include_router(actions.router)
    app.include_router(vector_stores.router)

    # SDK‑driven core model APIs
    app.include_router(responses.router)
    app.include_router(embeddings.router)
    app.include_router(images.router)
    app.include_router(videos.router)
    app.include_router(models.router)

    # Realtime (HTTP + WS proxy)
    app.include_router(realtime.router)

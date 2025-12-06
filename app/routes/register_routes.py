# app/routes/register_routes.py

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, FastAPI

from . import (
    actions,
    batches,
    containers,
    conversations,
    files,
    health,
    realtime,
    vector_stores,
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
    Register all *resource* routers on the given FastAPI app or APIRouter.

    This centralises wiring so you can:

        from app.routes import register_routes
        register_routes(app)

    or:

        from fastapi import APIRouter
        from app.routes import register_routes

        router = APIRouter()
        register_routes(router)

    Design:

    - This module is responsible for REST-style relay families and infra:
        * /health, /v1/health
        * /v1/files
        * /v1/conversations
        * /v1/containers
        * /v1/batches
        * /v1/actions
        * /v1/vector_stores
        * /v1/realtime/*
    - The *typed* SDK endpoints (/v1/responses, /v1/embeddings, /v1/images,
      /v1/videos, /v1/models) are owned by app.api.routes and are mounted in
      app.main to keep a clear separation of concerns.
    """

    # Health is special: it exposes both /health and /v1/health
    app.include_router(health.router)

    # Core REST resources (generic pass‑through via forward_openai_request)
    app.include_router(files.router)
    app.include_router(conversations.router)
    app.include_router(containers.router)
    app.include_router(batches.router)

    # New capability surfaces
    app.include_router(actions.router)
    app.include_router(vector_stores.router)

    # Realtime (HTTP + WS proxy)
    app.include_router(realtime.router)

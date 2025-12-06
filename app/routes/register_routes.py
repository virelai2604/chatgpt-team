# app/routes/register_routes.py

from __future__ import annotations

from typing import Protocol

from fastapi import APIRouter, FastAPI

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
    Minimal protocol for FastAPI app / APIRouter objects that support include_router.
    """

    def include_router(self, router: APIRouter, **kwargs) -> None:  # pragma: no cover - structural
        ...


def register_routes(app: _RouterLike) -> None:
    """
    Register all route families defined under app.routes.* on the given app or router.

    This centralises wiring so you can:

        from app.routes import register_routes
        register_routes(app)
    """

    # Health + meta
    app.include_router(health.router)

    # Core OpenAI-ish resources (thin proxies that use forward_openai_request)
    app.include_router(models.router)
    app.include_router(files.router)
    app.include_router(vector_stores.router)
    app.include_router(embeddings.router)
    app.include_router(responses.router)
    app.include_router(images.router)
    app.include_router(videos.router)

    # Higher-level / orchestration routes
    app.include_router(realtime.router)
    app.include_router(conversations.router)
    app.include_router(actions.router)
    app.include_router(batches.router)
    app.include_router(containers.router)

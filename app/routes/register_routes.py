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
    proxy,
    realtime,
    responses,
    uploads,
    vector_stores,
    videos,
)


class _RouterLike(Protocol):
    """Structural protocol for FastAPI / APIRouter (anything with include_router)."""

    def include_router(self, router: APIRouter, **kwargs) -> None:  # pragma: no cover
        ...


def register_routes(app: _RouterLike) -> None:
    """Register all route families on the given FastAPI app or APIRouter.

    Ordering matters: mount specific routers first and the generic `/v1/proxy`
    last so explicit routes always win.
    """

    # Health is special: exposes both `/health` and `/v1/health`
    app.include_router(health.router)

    # Relay diagnostics / metadata for Actions
    app.include_router(actions.router)
    app.include_router(images.actions_router)  # /v1/actions/images/*
    app.include_router(uploads.actions_router)  # /v1/actions/uploads/*
    app.include_router(videos.actions_router)  # /v1/actions/videos/*

    # Core OpenAI resource families
    app.include_router(responses.router)  # /v1/responses
    app.include_router(embeddings.router)  # /v1/embeddings
    app.include_router(images.router)  # /v1/images
    app.include_router(videos.router)  # /v1/videos
    app.include_router(videos.actions_router)  # /v1/actions/videos
    app.include_router(models.router)  # /v1/models (local stub)

    # Files & uploads (multipart, binary content)
    app.include_router(files.router)  # /v1/files
    app.include_router(uploads.router)  # /v1/uploads
    app.include_router(uploads.actions_router)  # /v1/actions/uploads/*
    app.include_router(vector_stores.router)  # /v1/vector_stores (+ /vector_stores)

    # Higher-level surfaces
    app.include_router(conversations.router)  # /v1/conversations
    app.include_router(containers.router)  # /v1/containers
    app.include_router(batches.router)  # /v1/batches
    app.include_router(realtime.router)  # /v1/realtime (HTTP + WS)

    # Generic allowlisted proxy LAST
    app.include_router(proxy.router)  # /v1/proxy


def register_all_routes(app: _RouterLike) -> None:
    """Backwards compatibility alias (older main.py imports)."""
    register_routes(app)

from __future__ import annotations

from fastapi import FastAPI

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
    responses,
    realtime,
    vector_stores,
    videos,
)


def register_routes(app: FastAPI) -> None:
    # Health first
    app.include_router(health.router)

    # Option A proxy (Actions-friendly)
    app.include_router(proxy.router)

    # Actions/meta
    app.include_router(actions.router)

    # Core OpenAI surfaces
    app.include_router(models.router)
    app.include_router(responses.router)
    app.include_router(embeddings.router)

    # Media / files
    app.include_router(images.router)
    app.include_router(videos.router)
    app.include_router(files.router)

    # Bulk + retrieval
    app.include_router(batches.router)
    app.include_router(vector_stores.router)

    # Realtime + newer surfaces
    app.include_router(realtime.router)
    app.include_router(conversations.router)
    app.include_router(containers.router)

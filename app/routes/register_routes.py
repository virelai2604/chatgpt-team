from __future__ import annotations

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
    vector_stores,
    videos,
)


def register_routes(app) -> None:
    # Core
    app.include_router(health.router)
    app.include_router(actions.router)

    # Option A (single Action-friendly entrypoint)
    app.include_router(proxy.router)

    # OpenAI-compatible endpoints
    app.include_router(models.router)
    app.include_router(embeddings.router)
    app.include_router(responses.router)
    app.include_router(files.router)
    app.include_router(batches.router)
    app.include_router(images.router)
    app.include_router(vector_stores.router)
    app.include_router(realtime.router)
    app.include_router(conversations.router)
    app.include_router(containers.router)
    app.include_router(videos.router)

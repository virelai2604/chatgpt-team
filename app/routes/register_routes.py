# app/routes/register_routes.py

from __future__ import annotations

from fastapi import FastAPI

from app.routes import (
    batches,
    containers,
    embeddings,
    files,
    health,
    images,
    models,
    proxy,
    responses,
    uploads,
    vector_stores,
    videos,
)


def register_all_routes(app: FastAPI) -> None:
    app.include_router(health.router)

    app.include_router(proxy.router)

    # Core
    app.include_router(models.router)
    app.include_router(embeddings.router)
    app.include_router(responses.router)

    # Files + large uploads
    app.include_router(files.router)
    app.include_router(uploads.router)

    # Media
    app.include_router(images.router)
    app.include_router(videos.router)

    # Containers + vector stores + batches
    app.include_router(containers.router)
    app.include_router(vector_stores.router)
    app.include_router(batches.router)

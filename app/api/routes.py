# app/api/routes.py

from __future__ import annotations

from fastapi import APIRouter

from app.routes.register_routes import register_routes


# This router becomes the single aggregation point for all /v1/* route families.
#
# Each resource router under app/routes/* already declares its own prefix="/v1"
# and tags=[...]. We simply register them all here so that main.py can:
#
#     from app.api.routes import router as api_router
#     app.include_router(api_router)
#
# This implements the “Option B” architecture:
#   - canonical route families live in app/routes/*
#   - a thin API aggregator in app/api/routes.py
#   - shared forwarding logic in app/api/forward_openai.py
router = APIRouter()

# Wire in all route families (files, conversations, containers, batches,
# actions, vector_stores, responses, embeddings, images, videos, models,
# realtime, health, etc.).
register_routes(router)

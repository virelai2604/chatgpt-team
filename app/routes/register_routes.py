# app/routes/register_routes.py

from fastapi import FastAPI

# Core SDK-based OpenAI routers
from app.api.routes import router as api_router
from app.api.sse import router as sse_router

# Health + infra
from app.routes import health as health_routes
from app.routes import realtime as realtime_routes

# Catch-all route families (each should define `router: APIRouter`)
from app.routes import actions as actions_routes
from app.routes import batches as batches_routes
from app.routes import containers as containers_routes
from app.routes import conversations as conversations_routes
from app.routes import embeddings as embeddings_routes
from app.routes import files as files_routes
from app.routes import images as images_routes
from app.routes import models as models_routes
from app.routes import vector_stores as vector_stores_routes
from app.routes import videos as videos_routes


def register_routes(app: FastAPI) -> None:
    """
    Central registry for all routers.

    Canonical shape:

      - /health                  -> health_routes.router
      - /v1/realtime/...         -> realtime_routes.router
      - /v1/responses, /v1/...   -> api_router
      - /v1/responses:stream     -> sse_router
      - /v1/files/...            -> files_routes.router
      - /v1/models/...           -> models_routes.router
      - /v1/vector_stores/...    -> vector_stores_routes.router
      - /v1/batches/...          -> batches_routes.router
      - /v1/containers/...       -> containers_routes.router
      - /v1/conversations/...    -> conversations_routes.router
      - /v1/actions/...          -> actions_routes.router
      - /v1/embeddings/...       -> embeddings_routes.router
      - /v1/images/...           -> images_routes.router
      - /v1/videos/...           -> videos_routes.router
    """

    # Health / infra (no /v1 prefix)
    app.include_router(health_routes.router)

    # Realtime infra under /v1
    app.include_router(realtime_routes.router, prefix="/v1")

    # Canonical SDK-based OpenAI endpoints (responses, embeddings, images, videos, models)
    app.include_router(api_router, prefix="/v1")

    # Streaming Responses (`/v1/responses:stream`)
    app.include_router(sse_router, prefix="/v1")

    # Route families using generic forwarder (forward_openai_request)
    route_families = [
        actions_routes,
        batches_routes,
        containers_routes,
        conversations_routes,
        embeddings_routes,
        files_routes,
        images_routes,
        models_routes,
        vector_stores_routes,
        videos_routes,
    ]

    for module in route_families:
        app.include_router(module.router, prefix="/v1")

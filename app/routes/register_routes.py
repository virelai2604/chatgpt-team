# ==========================================================
# app/routes/register_routes.py — Ground Truth Route Registrar (v1.7 / 2025.11)
# ==========================================================
"""
Registers all FastAPI route modules for the ChatGPT Team Relay.
Ensures OpenAI SDK 2.6.1–compatible URL structure, schema consistency,
and passthrough fallback for unimplemented endpoints.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import (
    conversations,
    files,
    models,
    realtime,
    responses,
    vector_stores,
    embeddings,
)
from app.api import passthrough_proxy
from app.utils.logger import logger


def register_routes(app: FastAPI) -> FastAPI:
    """Attach all /v1 routes to the FastAPI app (Ground Truth API v1.7)."""

    print("\n[Relay] 🔗 Registering all /v1 API routes (Ground Truth v1.7)...")

    # -------------------------------------------------------
    # Middleware
    # -------------------------------------------------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # -------------------------------------------------------
    # Core OpenAI-Compatible Endpoints
    # -------------------------------------------------------
    app.include_router(models.router, prefix="/v1", tags=["Models"])
    app.include_router(responses.router, prefix="/v1", tags=["Responses"])
    app.include_router(files.router, prefix="/v1", tags=["Files"])
    app.include_router(vector_stores.router, prefix="/v1", tags=["Vector Stores"])
    app.include_router(conversations.router, prefix="/v1", tags=["Conversations"])
    app.include_router(realtime.router, prefix="/v1", tags=["Realtime"])
    app.include_router(embeddings.router, prefix="/v1", tags=["Embeddings"])

    # -------------------------------------------------------
    # Passthrough Fallback (MUST BE LAST)
    # -------------------------------------------------------
    app.include_router(passthrough_proxy.router, prefix="", tags=["Passthrough"])

    # -------------------------------------------------------
    # Log and verify
    # -------------------------------------------------------
    active_routes = [
        "/v1/responses",
        "/v1/conversations",
        "/v1/files",
        "/v1/models",
        "/v1/vector_stores",
        "/v1/realtime",
        "/v1/embeddings",
        "(passthrough fallback)"
    ]

    logger.info("✅ Ground Truth API v1.7 active route families:")
    for route in active_routes:
        logger.info(f"   • {route}")

    print(f"[Relay] ✅ Registered {len(app.routes)} total routes successfully.\n")
    return app


def create_app() -> FastAPI:
    """Factory for FastAPI app (used by uvicorn entrypoint)."""
    app = FastAPI(
        title="ChatGPT Team Relay API",
        version="1.7",
        description="Ground Truth API v1.7 — Unified OpenAI-compatible relay with passthrough proxy.",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    register_routes(app)
    return app


# Example run:
#   uvicorn app.routes.register_routes:create_app --reload --port 8000

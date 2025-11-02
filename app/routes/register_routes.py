# ================================================================
# register_routes.py — Centralized Route Registration
# ================================================================
# Loads and attaches all core route modules to the FastAPI app.
# Supports OpenAI-compatible endpoints across the relay:
#   /v1/models, /v1/embeddings, /v1/files,
#   /v1/vector_stores, /v1/realtime, /v1/responses,
#   /responses (aliases), and /v1/conversations.
# ================================================================

from fastapi import FastAPI
import logging

# Import all route modules
from app.routes import (
    models,
    embeddings,
    files,
    vector_stores,
    realtime,
    responses,
    conversations,
)

logger = logging.getLogger("relay")

def register_routes(app: FastAPI):
    """
    Registers all API route modules to the FastAPI app instance.
    Ensures OpenAI SDK endpoint compatibility.
    """

    try:
        # ------------------------------------------------------------
        # Core OpenAI API Families
        # ------------------------------------------------------------
        app.include_router(models.router)
        app.include_router(embeddings.router)
        app.include_router(files.router)
        app.include_router(vector_stores.router)
        app.include_router(realtime.router)

        # ------------------------------------------------------------
        # Responses API (with aliases)
        # ------------------------------------------------------------
        app.include_router(responses.router)
        if hasattr(responses, "responses_router"):
            app.include_router(responses.responses_router)

        # ------------------------------------------------------------
        # Conversations Mock API
        # ------------------------------------------------------------
        app.include_router(conversations.router)

        # ------------------------------------------------------------
        # Log registration success
        # ------------------------------------------------------------
        logger.info("✅ Route registration complete:")
        logger.info("   → /v1/models")
        logger.info("   → /v1/embeddings")
        logger.info("   → /v1/files")
        logger.info("   → /v1/vector_stores")
        logger.info("   → /v1/realtime")
        logger.info("   → /v1/responses (+ /responses)")
        logger.info("   → /v1/conversations")
        logger.info("--------------------------------------------------------")

    except Exception as e:
        logger.error(f"❌ Route registration failed: {e}")
        raise e

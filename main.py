# ==========================================================
# app/main.py — ChatGPT Team Relay Entry Point (Ground Truth API v1.7)
# ==========================================================
"""
Main application bootstrap for the ChatGPT Team Relay.
Creates the FastAPI app, registers all /v1 routes, configures logging,
and validates environment variables for upstream passthrough.
"""

import os
import time
from fastapi import FastAPI
from app.routes.register_routes import register_routes
from app.utils.logger import logger


# --------------------------------------------------------------------------
# Environment + Metadata
# --------------------------------------------------------------------------

RELAY_VERSION = "1.7"
SDK_TARGET = "openai-python 2.6.1"
START_TIME = time.strftime("%Y-%m-%d %H:%M:%S")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
DISABLE_PASSTHROUGH = os.getenv("DISABLE_PASSTHROUGH", "false").lower() == "true"


# --------------------------------------------------------------------------
# Factory
# --------------------------------------------------------------------------

def create_app() -> FastAPI:
    """
    Build the FastAPI application and register all Ground Truth routes.
    """

    logger.info("🚀 Starting ChatGPT Team Relay")
    logger.info(f"→ Ground Truth API version: {RELAY_VERSION}")
    logger.info(f"→ Target SDK version: {SDK_TARGET}")
    logger.info(f"→ Start time: {START_TIME}")
    logger.info(f"→ OpenAI passthrough: {'disabled' if DISABLE_PASSTHROUGH else 'enabled'}")

    app = FastAPI(
        title="ChatGPT Team Relay",
        version=RELAY_VERSION,
        description=(
            "Unified OpenAI-compatible relay implementing Ground Truth API v1.7. "
            "Compatible with openai-python 2.6.1 SDK."
        ),
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # Register all endpoint families
    register_routes(app)

    # Health check endpoint
    @app.get("/v1/health")
    async def health_check():
        return {
            "object": "health",
            "status": "ok",
            "version": RELAY_VERSION,
            "sdk_target": SDK_TARGET,
            "time": START_TIME,
            "passthrough_enabled": not DISABLE_PASSTHROUGH
        }

    logger.info("✅ Relay initialized successfully.")
    return app


# --------------------------------------------------------------------------
# Local development entry
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("RELAY_HOST", "0.0.0.0")
    port = int(os.getenv("RELAY_PORT", "8000"))

    logger.info(f"Starting local server on {host}:{port}")
    uvicorn.run("app.main:create_app", host=host, port=port, reload=True)

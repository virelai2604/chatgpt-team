# ==========================================================
# app/main.py — ChatGPT Team Relay (Ground Truth API v1.7)
# ==========================================================
"""
Entry point for the ChatGPT Team Relay.
Implements Ground Truth-compliant route registration, structured logging,
and a root-level /health endpoint for service monitoring.

This configuration matches the OpenAI SDK 2.6.1 expectations and API schema.
"""

import os
import time
from fastapi import FastAPI
from app.routes.register_routes import register_routes
from app.utils.logger import logger

# --------------------------------------------------------------------------
# Metadata and Environment
# --------------------------------------------------------------------------

RELAY_VERSION = "1.7"
SDK_TARGET = "openai-python 2.6.1"
START_TIME = time.strftime("%Y-%m-%d %H:%M:%S")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
DISABLE_PASSTHROUGH = os.getenv("DISABLE_PASSTHROUGH", "false").lower() == "true"


# --------------------------------------------------------------------------
# Application Factory
# --------------------------------------------------------------------------

def create_app() -> FastAPI:
    """
    Factory pattern for FastAPI app.
    Aligned with Ground Truth relay configuration.
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
            "Fully aligned with openai-python SDK 2.6.1 and OpenAI API reference."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Register all versioned routes first
    register_routes(app)

    # ----------------------------------------------------------------------
    # Root-Level Health Endpoint (per Ground Truth reference)
    # ----------------------------------------------------------------------
    @app.get("/health")
    async def health_check():
        """
        Non-versioned health endpoint for Render/Kubernetes readiness probes.
        Not part of /v1 per OpenAI API reference.
        """
        return {
            "object": "health",
            "status": "ok",
            "version": RELAY_VERSION,
            "sdk_target": SDK_TARGET,
            "time": START_TIME,
            "passthrough_enabled": not DISABLE_PASSTHROUGH,
        }

    logger.info("✅ Relay initialized successfully.")
    return app


# --------------------------------------------------------------------------
# Local Development Entry
# --------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    host = os.getenv("RELAY_HOST", "0.0.0.0")
    port = int(os.getenv("RELAY_PORT", "8000"))

    logger.info(f"Starting local server on {host}:{port}")
    uvicorn.run("app.main:create_app", host=host, port=port, reload=True, factory=True)

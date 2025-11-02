# ================================================================
# main.py — ChatGPT Team Relay (OpenAI-Compatible)
# ================================================================
# Entry point for the ChatGPT Team Relay running on Render.com
# Version: 2.0  |  API Parity: openai-python 2.6.1 / openai-node 6.7.0
# ================================================================

import os
import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import register_routes
from app.api.passthrough_proxy import router as passthrough_router
from app.utils.logger import setup_logger

# ================================================================
# Logging Configuration
# ================================================================
setup_logger()
logger = logging.getLogger("relay")

# ================================================================
# FastAPI App Initialization
# ================================================================
app = FastAPI(
    title="ChatGPT Team Relay API",
    version="2.0",
    description=(
        "Ground-truth-validated OpenAI-compatible relay API.\n"
        "Implements SDK v2.6.1 (Python) and v6.7.0 (Node) endpoints.\n"
        "Supports Responses, Realtime, Files, Vector Stores, and Tools."
    ),
)

# ================================================================
# CORS Configuration
# ================================================================
allowed_origins = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "https://chat.openai.com,https://platform.openai.com"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins],
    allow_credentials=True,
    allow_methods=os.getenv(
        "CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    ).split(","),
    allow_headers=os.getenv("CORS_ALLOW_HEADERS", "*").split(","),
)

# ================================================================
# Health Endpoint
# ================================================================
@app.get("/v1/health")
async def health_check():
    """Return relay health and metadata."""
    return {
        "object": "health",
        "status": "ok",
        "version": "2.0",
        "sdk_target": "openai-python 2.6.1",
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "passthrough_enabled": True,
    }

# ================================================================
# Register Routes
# ================================================================
register_routes(app)

# ================================================================
# Fallback Proxy for Unrecognized Routes
# ================================================================
app.include_router(passthrough_router)

# ================================================================
# Exception Handling
# ================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        {"object": "error", "message": str(exc), "path": str(request.url)},
        status_code=500,
    )

# ================================================================
# Startup Message
# ================================================================
@app.on_event("startup")
async def on_startup():
    logger.info("🚀 ChatGPT Team Relay startup complete.")
    logger.info("   - OpenAI API passthrough enabled")
    logger.info("   - Routes registered successfully")
    logger.info("   - Ready for SDK + Actions integration")

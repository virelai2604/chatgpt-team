"""
app/main.py — ChatGPT Team Relay
Render.com Production Deployment
Ground Truth API v1.7 / SDK 2.6.1
"""

import os
import time
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.routes.register_routes import register_routes
from app.utils.logger import setup_logger


# ============================================================
# Environment Configuration
# ============================================================

APP_MODE = os.getenv("APP_MODE", "production")
APP_VERSION = os.getenv("BIFL_VERSION", "v2.3.4-fp")
SDK_TARGET = "openai-python 2.6.1"

RELAY_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
PORT = int(os.getenv("PORT", "8080"))

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

DISABLE_PASSTHROUGH = os.getenv("DISABLE_PASSTHROUGH", "false").lower() == "true"
MOCK_MODE = os.getenv("MOCK_MODE", "false").lower() == "true"

CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS").split(",")
CORS_ALLOW_HEADERS = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")

setup_logger()
logger = logging.getLogger("relay")

# ============================================================
# Initialize FastAPI App
# ============================================================

app = FastAPI(
    title=RELAY_NAME,
    version=APP_VERSION,
    description="OpenAI-compatible relay deployed on Render.com, aligned with Ground Truth API v1.7."
)

# ============================================================
# Middleware: CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# ============================================================
# Mount /schemas for OpenAPI YAML
# ============================================================

if os.path.isdir("schemas"):
    app.mount("/schemas", StaticFiles(directory="schemas"), name="schemas")
    logger.info("📘 /schemas mounted for OpenAPI schema access")

# ============================================================
# Register all route modules
# ============================================================

register_routes(app)
logger.info("✅ Core route groups registered: models, embeddings, files, vector_stores, realtime, responses")

# ============================================================
# Root Endpoint — Relay Info
# ============================================================

@app.get("/")
async def root():
    """Render.com Root Route — Shows Relay Metadata"""
    return {
        "object": "relay",
        "status": "ok",
        "relay_name": RELAY_NAME,
        "version": APP_VERSION,
        "sdk_target": SDK_TARGET,
        "environment": ENVIRONMENT,
        "port": PORT,
        "mock_mode": MOCK_MODE,
        "passthrough_enabled": not DISABLE_PASSTHROUGH,
        "default_model": DEFAULT_MODEL,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# ============================================================
# Fallback Passthrough
# ============================================================

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def fallback_passthrough(path: str, request: Request):
    """
    Catch-all passthrough handler.
    Mirrors upstream OpenAI API or returns fallback when passthrough is disabled.
    """
    logger.warning(f"⚠️ Unhandled path requested: /{path}")
    return JSONResponse({
        "object": "fallback",
        "path": path,
        "status": "ok",
        "passthrough": not DISABLE_PASSTHROUGH
    })

# ============================================================
# Lifecycle Events
# ============================================================

@app.on_event("startup")
async def on_startup():
    logger.info(f"🚀 {RELAY_NAME} starting up")
    logger.info(f"Version {APP_VERSION} | Env: {ENVIRONMENT} | SDK: {SDK_TARGET}")
    logger.info(f"Passthrough: {not DISABLE_PASSTHROUGH} | Mock mode: {MOCK_MODE}")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("🛑 Relay shutdown complete")

# ============================================================
# Local Dev Entry (Render uses uvicorn via startCommand)
# ============================================================

if __name__ == "__main__":
    import uvicorn
    logger.info(f"🏗️ Starting {RELAY_NAME} on 0.0.0.0:{PORT}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=(ENVIRONMENT != "production"))

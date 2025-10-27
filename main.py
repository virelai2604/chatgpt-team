# ==========================================================
# main.py — ChatGPT Team Relay (Render Deployment Edition)
# ==========================================================
# Production entrypoint for ChatGPT Relay deployed on Render.
# Mirrors OpenAI’s v1 API surface, including /v1/responses,
# chat completions, realtime, and file/vector endpoints.
# ==========================================================

import os
import sys
import asyncio
import logging
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# ----------------------------------------------------------
# 🌍 Load Environment Variables
# ----------------------------------------------------------
load_dotenv()

# ----------------------------------------------------------
# 🧱 Core Imports
# ----------------------------------------------------------
from app.utils.db_logger import init_db
from app.routes.register_routes import register_routes
from app.api.tools_api import TOOL_REGISTRY
from app.utils.error_handler import register_error_handlers

# ----------------------------------------------------------
# 🧾 Metadata
# ----------------------------------------------------------
APP_NAME = "ChatGPT Team Relay"
BIFL_VERSION = "2.3.4-fp"
RELAY_ENV = os.getenv("RELAY_ENV", "production")

# ----------------------------------------------------------
# 🧠 Logging Configuration
# ----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("ChatGPTRelay")

# ----------------------------------------------------------
# 🌐 Lifespan Context
# ----------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown lifecycle:
    - Initialize DB logger
    - Log environment and tools
    - Graceful teardown
    """
    logger.info(f"[Relay] Starting {APP_NAME} (v{BIFL_VERSION}) in {RELAY_ENV} mode...")
    try:
        if os.getenv("ENABLE_DB_LOGGING", "true").lower() == "true":
            await init_db()
            logger.info("[Relay] Database layer initialized successfully.")
        else:
            logger.info("[Relay] Database logging disabled by environment.")
    except Exception as e:
        logger.error(f"[Relay] Failed to initialize database: {e}")

    # Tool discovery
    logger.info(f"[Relay] Loaded tools: {len(TOOL_REGISTRY)} registered.")
    for tool_id in TOOL_REGISTRY:
        logger.info(f"  └── {tool_id}")

    yield  # ---- Application runs ----

    logger.info("[Relay] Shutting down gracefully...")
    await asyncio.sleep(0.2)
    logger.info("[Relay] Shutdown complete.")

# ----------------------------------------------------------
# 🚀 FastAPI App Initialization
# ----------------------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version=BIFL_VERSION,
    description="OpenAI-compatible relay for ChatGPT Actions and Team Orchestration.",
    lifespan=lifespan,
)

# ----------------------------------------------------------
# 🔒 CORS Middleware (Dynamic from Environment)
# ----------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=os.getenv("CORS_ALLOW_METHODS", "*").split(","),
    allow_headers=os.getenv("CORS_ALLOW_HEADERS", "*").split(","),
)

# ----------------------------------------------------------
# 🧩 Route Registration & Error Handlers
# ----------------------------------------------------------
register_routes(app)
register_error_handlers(app)

# ----------------------------------------------------------
# 💡 Core Health Endpoints
# ----------------------------------------------------------
@app.get("/")
async def root():
    """Landing endpoint for relay root."""
    return {
        "object": "relay.root",
        "status": "ok",
        "version": BIFL_VERSION,
        "environment": RELAY_ENV,
        "service_url": "https://chatgpt-team-relay.onrender.com"
    }

@app.get("/v1/healthz")
async def health_check():
    """Render health check endpoint."""
    return Response(status_code=200, content="ok")

@app.get("/v1/version")
async def version_check():
    """Version endpoint for diagnostics."""
    return {
        "object": "relay.version",
        "version": BIFL_VERSION,
        "env": RELAY_ENV
    }

# ----------------------------------------------------------
# 🧭 Entry Point (Render Startup)
# ----------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    host = os.getenv("RELAY_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("RELAY_PORT", "8000")))
    logger.info(f"[Relay] Listening on {host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=False)

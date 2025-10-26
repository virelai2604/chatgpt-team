# ==========================================================
# main.py — ChatGPT Team Relay Core (BIFL v2.3.4-fp)
# ==========================================================
# Fully aligned with OpenAI Relay Ground Truth (Oct 2025)
# Future-proofed for GPT-6, Sora-3, and new /v1 endpoints
# ==========================================================

import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.utils.db_logger import init_db
from dotenv import load_dotenv
from app.routes.register_routes import register_routes  # 🧩 Auto route loader

# --------------------------------------------------------------------------
# Load environment configuration
# --------------------------------------------------------------------------
load_dotenv()

# --------------------------------------------------------------------------
# Logging and configuration setup
# --------------------------------------------------------------------------
logger = logging.getLogger("BIFL")

BIFL_VERSION = "2.3.4-fp"
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
ENABLE_STREAM = os.getenv("ENABLE_STREAM", "false").lower() == "true"

# --------------------------------------------------------------------------
# FastAPI application lifespan manager
# --------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management for startup/shutdown.
    Initializes databases, logs, and registers all routes
    in strict OpenAI relay-compatible order.
    """
    # Initialize DB / telemetry
    logger.info("[BIFL] Initializing database...")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"[BIFL] Database init failed: {e}")

    logger.info(f"[BIFL] Relay Version: {BIFL_VERSION}")
    logger.info(f"[BIFL] Base URL: {OPENAI_BASE_URL}")
    if OPENAI_ORG_ID:
        logger.info(f"[BIFL] Org ID: {OPENAI_ORG_ID}")
    logger.info(f"[BIFL] Streaming Enabled: {ENABLE_STREAM}")

    # ----------------------------------------------------------------------
    # 🧩 Manual registration for core routers (OpenAI ground-truth order)
    # ----------------------------------------------------------------------
    from app.api import tools_api, responses, passthrough_proxy

    app.include_router(tools_api.router)          # 1️⃣ Tool Reflection
    app.include_router(responses.router)          # 2️⃣ Model Responses
    app.include_router(passthrough_proxy.router)  # 3️⃣ Catch-all Proxy

    # ----------------------------------------------------------------------
    # 🧩 Automatic registration for all other /v1 routes
    # This ensures lifetime compatibility with new OpenAI endpoints
    # ----------------------------------------------------------------------
    register_routes(app)

    logger.info("[BIFL] All routers registered successfully.")
    yield
    logger.info("[BIFL] Shutting down gracefully...")
    await asyncio.sleep(0.1)

# --------------------------------------------------------------------------
# FastAPI application setup
# --------------------------------------------------------------------------
app = FastAPI(
    title="ChatGPT Team Relay",
    version=BIFL_VERSION,
    lifespan=lifespan,
)

# --------------------------------------------------------------------------
# Global middleware (CORS, etc.)
# --------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Base and health routes
# --------------------------------------------------------------------------
@app.get("/v1/healthz")
def health():
    """Simple health check endpoint."""
    return {"status": "ok", "version": BIFL_VERSION}

@app.get("/v1/version")
def version():
    """Return relay version and configuration."""
    return {
        "version": BIFL_VERSION,
        "openai_base_url": OPENAI_BASE_URL,
        "enable_stream": ENABLE_STREAM,
    }

@app.get("/")
def root():
    """
    Root route for browser checks and platform uptime monitoring.
    Mirrors the style of OpenAI edge health responses.
    """
    return {
        "status": "ok",
        "message": "ChatGPT Relay is operational.",
        "version": BIFL_VERSION,
        "openai_base_url": OPENAI_BASE_URL,
        "enable_stream": ENABLE_STREAM,
        "endpoints": {
            "health": "/v1/healthz",
            "version": "/v1/version",
            "models": "/v1/models",
            "responses": "/v1/responses",
            "tools": "/v1/tools",
            "auto_routes": True,  # indicates register_routes() is active
        },
    }

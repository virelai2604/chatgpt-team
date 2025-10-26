import os
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.utils.db_logger import init_db

# --------------------------------------------------------------------------
# Configuration and Logging
# --------------------------------------------------------------------------

logger = logging.getLogger("BIFL")

BIFL_VERSION = "2.3.4-fp"
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
ENABLE_STREAM = os.getenv("ENABLE_STREAM", "false").lower() == "true"


# --------------------------------------------------------------------------
# FastAPI Lifespan Manager
# --------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager (replaces FastAPI startup/shutdown)."""
    logger.info("[BIFL] Initializing database...")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"[BIFL] Database init failed: {e}")

    logger.info(f"[BIFL] Base URL: {OPENAI_BASE_URL}")
    if OPENAI_ORG_ID:
        logger.info(f"[BIFL] Organization: {OPENAI_ORG_ID}")
    logger.info(f"[BIFL] Version: {BIFL_VERSION}")

    # 🧩 Manual router registration in strict order
    from app.api import tools_api, responses_api, passthrough_proxy
    app.include_router(tools_api.router)       # must come first
    app.include_router(responses_api.router)   # model API second
    app.include_router(passthrough_proxy.router)  # wildcard last

    logger.info("[BIFL] Route registration complete.")
    yield
    logger.info("[BIFL] Shutting down gracefully...")
    await asyncio.sleep(0.1)


# --------------------------------------------------------------------------
# FastAPI Application
# --------------------------------------------------------------------------

app = FastAPI(
    title="ChatGPT Relay API",
    version=BIFL_VERSION,
    lifespan=lifespan,
)


# --------------------------------------------------------------------------
# Global Middleware
# --------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Base Routes (Health, Version, Root)
# --------------------------------------------------------------------------

@app.get("/v1/healthz")
def health():
    """Health check endpoint."""
    return {"status": "ok", "version": BIFL_VERSION}


@app.get("/v1/version")
def version():
    """Show current relay version and configuration."""
    return {
        "version": BIFL_VERSION,
        "openai_base_url": OPENAI_BASE_URL,
        "enable_stream": ENABLE_STREAM
    }


@app.get("/")
def root():
    """
    Root route (for browsers and Render health probes).
    Prevents 404 spam on GET / and HEAD /.
    """
    return {
        "status": "ok",
        "message": "ChatGPT Relay is running.",
        "version": BIFL_VERSION,
        "openai_base_url": OPENAI_BASE_URL,
        "endpoints": {
            "health": "/v1/healthz",
            "version": "/v1/version",
            "models": "/v1/models",
            "responses": "/v1/responses"
        }
    }

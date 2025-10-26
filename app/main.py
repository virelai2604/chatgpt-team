# ==========================================================
#  app/main.py — BIFL v2.3.3-p2
# ==========================================================
#  Central FastAPI application for ChatGPT-Team relay.
#  Handles:
#   • Dynamic route registration
#   • SQLite logger initialization
#   • Relay version reporting
#   • Graceful startup/shutdown
# ==========================================================

import os
import logging
from fastapi import FastAPI
from app.routes import register_routes
from app.utils.db_logger import init_db
from app.utils.error_handler import error_response

# ──────────────────────────────────────────────
#  App metadata
# ──────────────────────────────────────────────
APP_VERSION = "2.3.3-p2"
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
ORG_ID = os.getenv("OPENAI_ORG_ID", "")
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

logger = logging.getLogger("bifl.main")
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)

# ──────────────────────────────────────────────
#  FastAPI instance
# ──────────────────────────────────────────────
app = FastAPI(
    title="ChatGPT-Team Relay",
    version=APP_VERSION,
    description="Cloudflare ChatGPT-Team Relay API (BIFL v2.3.3-p2)",
)

# ──────────────────────────────────────────────
#  Global error fallback
# ──────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"[BIFL] Unhandled exception: {exc}")
    return error_response("server_error", str(exc), 500, {})

# ──────────────────────────────────────────────
#  Startup / shutdown
# ──────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    logger.info(f"[BIFL] SQLite database initializing...")
    init_db()
    logger.info(f"[BIFL] Relay initialized successfully.")
    logger.info(f"[BIFL] Base URL: {BASE_URL}")
    if ORG_ID:
        logger.info(f"[BIFL] Organization: {ORG_ID}")
    logger.info(f"[BIFL] Version: {APP_VERSION}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("[BIFL] Relay shutting down gracefully.")

# ──────────────────────────────────────────────
#  Register all route modules
# ──────────────────────────────────────────────
register_routes(app)

# ──────────────────────────────────────────────
#  Health check endpoint
# ──────────────────────────────────────────────
@app.get("/relay/health")
async def relay_health():
    """Basic health check and version verification."""
    return {
        "status": "ok",
        "bifl_version": APP_VERSION,
        "base_url": BASE_URL,
    }

# ==========================================================
#  End of main.py
# ==========================================================

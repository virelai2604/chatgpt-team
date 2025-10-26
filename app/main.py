# ==========================================================
#  app/main.py — BIFL v2.3.4-fp
# ==========================================================
#  Central FastAPI relay entrypoint.
#  • Dynamic route registration
#  • SQLite logger init
#  • Unified /v1/version + /v1/healthz
#  • Lifespan startup/shutdown (FastAPI ≥0.118)
# ==========================================================

import os, logging, contextlib
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.routes import register_routes
from app.utils.db_logger import init_db

APP_VERSION = "2.3.4-fp"
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
ORG_ID = os.getenv("OPENAI_ORG_ID", "")
DEBUG_MODE = os.getenv("DEBUG", "false").lower() == "true"

logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)
logger = logging.getLogger("bifl.main")

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"[BIFL] Initializing database...")
    init_db()
    logger.info(f"[BIFL] Base URL: {BASE_URL}")
    if ORG_ID:
        logger.info(f"[BIFL] Organization: {ORG_ID}")
    logger.info(f"[BIFL] Version: {APP_VERSION}")
    yield
    logger.info("[BIFL] Relay shutting down gracefully.")

app = FastAPI(
    title="ChatGPT-Team Relay",
    version=APP_VERSION,
    description="Render-deployed OpenAI-compatible relay (BIFL v2.3.4-fp)",
    lifespan=lifespan,
)

# Register all routers
register_routes(app)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"[BIFL] Unhandled exception: {exc}")
    return JSONResponse(
        {"error": {"type": "server_error", "message": str(exc)}}, status_code=500
    )

@app.get("/v1/healthz")
async def healthz():
    return {"ok": True, "version": APP_VERSION}

@app.get("/v1/version")
async def version():
    return {
        "relay_name": "ChatGPT Team Relay",
        "bifl_version": APP_VERSION,
        "streaming_enabled": os.getenv("ENABLE_STREAM", "false").lower() == "true",
        "base_url": BASE_URL,
    }

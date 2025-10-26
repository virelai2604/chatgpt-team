# ==========================================================
# app/main.py — ChatGPT Team Relay
# BIFL v2.3.4-fp (Future-Proof, Stream-Enabled)
# ==========================================================
import os
import asyncio
import logging
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import register_routes
from app.utils.db_logger import init_db

# ----------------------------------------------------------
# 🧠 Base Config
# ----------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger("BIFL")

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
RELAY_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
BIFL_VERSION = os.getenv("BIFL_VERSION", "2.3.4-fp")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# ----------------------------------------------------------
# 🌱 Lifespan Context (replaces deprecated startup/shutdown)
# ----------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[BIFL] Initializing database...")
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"[BIFL] Database init failed: {e}")

    logger.info(f"[BIFL] Base URL: {OPENAI_BASE_URL}")
    if OPENAI_ORG_ID:
        logger.info(f"[BIFL] Organization: {OPENAI_ORG_ID}")
    logger.info(f"[BIFL] Version: {BIFL_VERSION}")

    # Load all routes dynamically
    register_routes(app)
    logger.info("[BIFL] Route registration complete.")

    yield  # App runs while context is active

    logger.info("[BIFL] Shutting down gracefully...")
    await asyncio.sleep(0.1)

# ----------------------------------------------------------
# ⚙️ FastAPI App
# ----------------------------------------------------------
app = FastAPI(
    title=RELAY_NAME,
    version=BIFL_VERSION,
    description="OpenAI-compatible relay with GPT-5, Sora, and hybrid tools",
    lifespan=lifespan,
)

# ----------------------------------------------------------
# 🌐 CORS
# ----------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS").split(","),
    allow_headers=os.getenv("CORS_ALLOW_HEADERS", "*").split(","),
)

# ----------------------------------------------------------
# 🧱 Health + Version Endpoints
# ----------------------------------------------------------
@app.get("/v1/healthz")
async def health_check():
    """Lightweight health check for Render and CI/CD."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}


@app.get("/v1/version")
async def version_info():
    """Expose relay version and environment metadata."""
    return {
        "relay_name": RELAY_NAME,
        "version": BIFL_VERSION,
        "base_url": OPENAI_BASE_URL,
        "org_id": OPENAI_ORG_ID,
        "debug": DEBUG,
        "tools_dir": os.getenv("TOOLS_DIR", "app/tools"),
        "streaming_enabled": os.getenv("ENABLE_STREAM", "true"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

# ----------------------------------------------------------
# 🏁 Entrypoint (local dev)
# ----------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        reload=DEBUG,
    )

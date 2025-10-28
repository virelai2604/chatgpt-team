import asyncio
import json
import logging
import os
import platform
import sqlite3
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Import route registrar
from app.routes.register_routes import register_routes

# Middleware
from app.middleware.validation import ResponseValidationMiddleware

# Logger setup
from app.utils.db_logger import setup_logging


# ==========================================================
# Configuration
# ==========================================================
RELAY_VERSION = "v2.3.4-fp"
APP_MODE = os.getenv("APP_MODE", "production")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
SCHEMAS_DIR = BASE_DIR / "schemas"

if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Database path setup
if platform.system() == "Windows":
    DB_PATH = os.getenv("LOCAL_DB_PATH", r"D:\ChatgptDATAB\DB Chatgpt\chatgpt_archive.sqlite")
else:
    default_linux_db = "/data/chatgpt_archive.sqlite"
    if not os.access("/data", os.W_OK):
        default_linux_db = "/tmp/chatgpt_archive.sqlite"
    DB_PATH = os.getenv("BIFL_DB_PATH", default_linux_db)

# Initialize logging
setup_logging()
logger = logging.getLogger("relay")


# ==========================================================
# FastAPI Initialization
# ==========================================================
app = FastAPI(
    title="ChatGPT Team Relay",
    description="OpenAI-compatible relay for ChatGPT Actions, API calls, and Team integration.",
    version=RELAY_VERSION,
)


# ==========================================================
# Middleware Configuration
# ==========================================================
app.add_middleware(ResponseValidationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ALLOW_ORIGINS", "*")],
    allow_methods=os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS").split(","),
    allow_headers=[os.getenv("CORS_ALLOW_HEADERS", "*")],
)


# ==========================================================
# Static Files and Plugin Discovery
# ==========================================================
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/.well-known/ai-plugin.json")
async def serve_plugin_manifest():
    """Serve the ChatGPT Plugin manifest file."""
    return FileResponse(STATIC_DIR / ".well-known" / "ai-plugin.json", media_type="application/json")


@app.get("/v1/openapi.yaml", include_in_schema=False)
async def serve_static_openapi():
    """Serve the ground-truth OpenAPI specification."""
    return FileResponse(SCHEMAS_DIR / "openapi.yaml", media_type="application/x-yaml")


# ==========================================================
# Route Registration
# ==========================================================
register_routes(app)


# ==========================================================
# Application Lifecycle
# ==========================================================
@app.on_event("startup")
async def on_startup():
    logger.info(f"[Relay] Starting ChatGPT Team Relay ({RELAY_VERSION}) in {APP_MODE} mode...")
    logger.info(f"[DBLogger] Using database at: {DB_PATH}")

    try:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT (datetime('now')),
                level TEXT,
                message TEXT
            );
        """)
        conn.commit()
        conn.close()
        logger.info("[Relay] Verified database schema.")
    except Exception as e:
        logger.error(f"[Relay] Failed to verify or create database: {e}")

    logger.info("Application startup complete.")


@app.on_event("shutdown")
async def on_shutdown():
    logger.info("[Relay] Shutting down gracefully...")
    await asyncio.sleep(0.25)
    logger.info("[Relay] Shutdown complete.")


# ==========================================================
# Health + Diagnostics Endpoints
# ==========================================================
@app.get("/health")
async def health_check():
    """Simple uptime and DB health status."""
    exists = os.path.exists(DB_PATH)
    size = os.path.getsize(DB_PATH) if exists else 0
    return {
        "status": "ok",
        "version": RELAY_VERSION,
        "mode": APP_MODE,
        "db_exists": exists,
        "db_path": DB_PATH,
        "db_size_bytes": size,
    }


@app.get("/logs/recent")
async def get_recent_logs(limit: int = 10):
    """Fetch recent application logs."""
    if not os.path.exists(DB_PATH):
        return {"error": "Database not found", "path": DB_PATH}
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, timestamp, level, message FROM logs ORDER BY id DESC LIMIT ?;", (limit,)
    ).fetchall()
    conn.close()
    return {"recent_logs": rows, "count": len(rows)}


# ==========================================================
# Entry Point
# ==========================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8000)), reload=True)

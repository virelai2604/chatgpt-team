import asyncio
import json
import logging
import os
import platform
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Route registrator
from app.routes.register_routes import register_routes

# Middleware
from app.middleware.validation import ResponseValidationMiddleware

# Logging
from app.utils.db_logger import setup_logging

# -----------------------------------------------------
# Relay Metadata
# -----------------------------------------------------
RELAY_VERSION = "v2.3.4-fp"
APP_MODE = os.getenv("APP_MODE", "production")

# -----------------------------------------------------
# Database Path (Cross-platform)
# -----------------------------------------------------
if platform.system() == "Windows":
    DB_PATH = os.getenv("LOCAL_DB_PATH", r"D:\ChatgptDATAB\DB Chatgpt\chatgpt_archive.sqlite")
else:
    default_linux_db = "/data/chatgpt_archive.sqlite"
    if not os.access("/data", os.W_OK):
        default_linux_db = "/tmp/chatgpt_archive.sqlite"
    DB_PATH = os.getenv("BIFL_DB_PATH", default_linux_db)

# -----------------------------------------------------
# Logging Setup
# -----------------------------------------------------
setup_logging()
logger = logging.getLogger("relay")

# -----------------------------------------------------
# FastAPI Initialization
# -----------------------------------------------------
app = FastAPI(
    title="ChatGPT Team Relay",
    description="Unified OpenAI-compatible relay for ChatGPT Actions and API extensions. Fully aligned to OpenAI API ground truth.",
    version=RELAY_VERSION,
)

# -----------------------------------------------------
# Middleware
# -----------------------------------------------------
app.add_middleware(ResponseValidationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ALLOW_ORIGINS", "*")],
    allow_methods=os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS").split(","),
    allow_headers=[os.getenv("CORS_ALLOW_HEADERS", "*")],
)

# -----------------------------------------------------
# Static Files + Plugin Discovery
# -----------------------------------------------------
# Your project-tree shows /static/.well-known/ai-plugin.json at the root,
# not under app/static, so adjust directory accordingly:
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/.well-known/ai-plugin.json")
async def serve_plugin_manifest():
    """Serve the ChatGPT Plugin manifest."""
    return FileResponse("static/.well-known/ai-plugin.json", media_type="application/json")

@app.get("/v1/openapi.yaml", include_in_schema=False)
async def serve_static_openapi():
    """
    Serve the static ground-truth OpenAPI specification stored in /schemas/openapi.yaml.
    This file represents the authoritative API contract, verified against the OpenAI API reference.
    """
    return FileResponse("schemas/openapi.yaml", media_type="application/x-yaml")

# -----------------------------------------------------
# Register All Routes
# -----------------------------------------------------
register_routes(app)

# -----------------------------------------------------
# Startup Event
# -----------------------------------------------------
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

# -----------------------------------------------------
# Shutdown Event
# -----------------------------------------------------
@app.on_event("shutdown")
async def on_shutdown():
    logger.info("[Relay] Shutting down gracefully...")
    await asyncio.sleep(0.2)
    logger.info("[Relay] Shutdown complete.")

# -----------------------------------------------------
# Health Check
# -----------------------------------------------------
@app.get("/health")
async def health_check():
    exists = os.path.exists(DB_PATH)
    size = os.path.getsize(DB_PATH) if exists else 0
    return {
        "status": "ok",
        "version": RELAY_VERSION,
        "mode": APP_MODE,
        "db_exists": exists,
        "db_path": DB_PATH,
        "db_size_bytes": size
    }

# -----------------------------------------------------
# Logs Viewer
# -----------------------------------------------------
@app.get("/logs/recent")
async def get_recent_logs(limit: int = 10):
    if not os.path.exists(DB_PATH):
        return {"error": "Database not found", "path": DB_PATH}
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT id, timestamp, level, message FROM logs ORDER BY id DESC LIMIT ?;", (limit,)
    ).fetchall()
    conn.close()
    return {"recent_logs": rows, "count": len(rows)}

# -----------------------------------------------------
# Entry Point
# -----------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 8080)))

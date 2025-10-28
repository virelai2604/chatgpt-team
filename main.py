import asyncio
import json
import logging
import os
import platform
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.responses import router as responses_router
from app.api.tools_api import router as tools_router, load_manifest
from app.api.forward_openai import router as forward_router   # ✅ Added for OpenAI proxy forwarding
from app.utils.db_logger import setup_logging

# -----------------------------------------------------
# Relay Metadata
# -----------------------------------------------------
RELAY_VERSION = "v2.3.4-fp"
APP_MODE = os.getenv("APP_MODE", "production")

# -----------------------------------------------------
# Database Path (Render-compatible + Local fallback)
# -----------------------------------------------------
if platform.system() == "Windows":
    DB_PATH = os.getenv("LOCAL_DB_PATH", r"D:\ChatgptDATAB\DB Chatgpt\chatgpt_archive.sqlite")
else:
    default_linux_db = "/data/chatgpt_archive.sqlite"
    if not os.access("/data", os.W_OK):  # fallback if /data is not writable
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
# Middleware (CORS)
# -----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("CORS_ALLOW_ORIGINS", "*")],
    allow_methods=os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS").split(","),
    allow_headers=[os.getenv("CORS_ALLOW_HEADERS", "*")],
)

# -----------------------------------------------------
# Routers
# -----------------------------------------------------
app.include_router(responses_router, prefix="/v1")
app.include_router(tools_router)
app.include_router(forward_router)  # ✅ now handles all /v1/* routes (including /v1/responses)

# -----------------------------------------------------
# Startup Event
# -----------------------------------------------------
@app.on_event("startup")
async def on_startup():
    logger.info(f"[Relay] Starting ChatGPT Team Relay ({RELAY_VERSION}) in {APP_MODE} mode...")
    logger.info(f"[DBLogger] Using database at: {DB_PATH}")

    # Ensure database exists and schema is valid
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

    # Load tool manifest definitions
    try:
        tool_manifest = load_manifest()
        if tool_manifest:
            logger.info(f"[Relay] Loaded tools: {len(tool_manifest)} registered from manifest.")
            for tool in tool_manifest:
                logger.info(f"  └── {tool['id']} ({tool.get('description', '')})")
        else:
            logger.warning("[Relay] No tools found in manifest.")
    except Exception as e:
        logger.error(f"[Relay] Failed to load tools manifest: {e}")

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

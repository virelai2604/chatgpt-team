"""
main.py — ChatGPT Team Relay (Production Edition)
-------------------------------------------------
FastAPI app exposing OpenAI-compatible endpoints
for Chat Completions, Responses, Realtime, Files,
Vector Stores, and Tools. Fully Relay-compatible.

This version supports:
  ✅ SQLite logging with persistence (/data mount)
  ✅ OpenAPI 3.1 auto-spec in YAML
  ✅ Validation middleware for /v1/responses
  ✅ Streaming (SSE) and passthrough proxying
  ✅ CORS + environment-safe configuration
  ✅ Plugin discovery via /.well-known/ai-plugin.json
-------------------------------------------------
"""

import os
import platform
import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# ---------------------------------------------------------
# ✅ App imports
# ---------------------------------------------------------
from app.routes.register_routes import register_routes
from app.utils.db_logger import setup_logging, ensure_schema
from app.middleware.validation import ResponseValidationMiddleware

# ---------------------------------------------------------
# 🧭 Basic App Configuration
# ---------------------------------------------------------
APP_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
APP_MODE = os.getenv("APP_MODE", "development")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
ENABLE_STREAM = os.getenv("ENABLE_STREAM", "true").lower() == "true"

# ---------------------------------------------------------
# 🗄 Database Path Resolution (cross-platform safe)
# ---------------------------------------------------------
if platform.system() == "Windows":
    DB_PATH = os.getenv("LOCAL_DB_PATH", r"D:\ChatgptDATAB\DB Chatgpt\chatgpt_archive.sqlite")
else:
    default_linux_db = "/data/chatgpt_archive.sqlite"
    # Fallback to /tmp if no write permission (Render build sandbox)
    if not os.access("/data", os.W_OK):
        default_linux_db = "/tmp/chatgpt_archive.sqlite"
    DB_PATH = os.getenv("BIFL_DB_PATH", default_linux_db)

# ---------------------------------------------------------
# 🧱 Logging + DB Setup
# ---------------------------------------------------------
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
setup_logging(DB_PATH)
ensure_schema(DB_PATH)

logging.info(f"[Relay] Starting {APP_NAME} ({APP_MODE}) mode...")
logging.info(f"[DBLogger] Using database at: {DB_PATH}")

# ---------------------------------------------------------
# 🚀 FastAPI Application
# ---------------------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version="2025-10",
    description="Relay-compatible OpenAI API surface (ChatGPT Team architecture).",
    contact={"name": "ChatGPT Team Relay", "url": "https://chat.openai.com"},
    license_info={"name": "MIT"},
)

# ---------------------------------------------------------
# 🧩 Middleware
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE,OPTIONS").split(","),
    allow_headers=os.getenv("CORS_ALLOW_HEADERS", "*").split(","),
)

# Schema validation middleware for /v1/responses
app.add_middleware(ResponseValidationMiddleware)

# ---------------------------------------------------------
# 🗺 Static + Routes
# ---------------------------------------------------------
# Static files (for /static assets)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ✅ Serve /.well-known/ai-plugin.json from within static/.well-known
well_known_dir = os.path.join(static_dir, ".well-known")
if os.path.isdir(well_known_dir):
    app.mount("/.well-known", StaticFiles(directory=well_known_dir), name="well-known")

# Register API route modules
register_routes(app)

# ---------------------------------------------------------
# 🩺 Health Check
# ---------------------------------------------------------
@app.get("/health")
async def health_check():
    db_exists = os.path.exists(DB_PATH)
    return JSONResponse(
        {
            "status": "ok",
            "version": "v2.3.4-fp",
            "mode": APP_MODE,
            "default_model": DEFAULT_MODEL,
            "db_exists": db_exists,
            "db_path": DB_PATH,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )

# ---------------------------------------------------------
# 🌍 Root route (metadata)
# ---------------------------------------------------------
@app.get("/")
async def root():
    return {
        "object": "relay.root",
        "name": APP_NAME,
        "mode": APP_MODE,
        "streaming_enabled": ENABLE_STREAM,
        "default_model": DEFAULT_MODEL,
        "routes": len(app.routes),
        "docs": "/docs",
        "openapi_yaml": "/v1/openapi.yaml",
        "health": "/health",
    }

# ---------------------------------------------------------
# 🧪 Local Dev Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )

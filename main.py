"""
main.py — ChatGPT Team Relay (Render Production, DB-Free)
---------------------------------------------------------
OpenAI API–compatible relay server exposing endpoints:
  • /v1/responses
  • /v1/chat/completions
  • /v1/models
  • /v1/files
  • /v1/vector_stores
  • /v1/realtime/*
  • /.well-known/ai-plugin.json
---------------------------------------------------------
Environment variables defined in `.env` control all models,
timeouts, and metadata. Designed for Render deployment.
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
from app.middleware.validation import ResponseValidationMiddleware

# ---------------------------------------------------------
# 🧭 Configuration
# ---------------------------------------------------------
APP_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
APP_MODE = os.getenv("APP_MODE", "development")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-4o")
ENABLE_STREAM = os.getenv("ENABLE_STREAM", "true").lower() == "true"

# ---------------------------------------------------------
# 🗄 Database placeholder (for metadata only, not active)
# ---------------------------------------------------------
if platform.system() == "Windows":
    DB_PATH = os.getenv("LOCAL_DB_PATH", r"D:\ChatgptDATAB\DB Chatgpt\chatgpt_archive.sqlite")
else:
    # Render-safe: fallback ensures /data permission errors never occur
    default_linux_db = "/tmp/chatgpt_archive.sqlite"
    DB_PATH = os.getenv("BIFL_DB_PATH", default_linux_db)

# ---------------------------------------------------------
# 🧱 Logging
# ---------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logging.info(f"[Relay] Starting {APP_NAME} ({APP_MODE}) mode...")

# ---------------------------------------------------------
# 🚀 FastAPI App
# ---------------------------------------------------------
app = FastAPI(
    title=APP_NAME,
    version=os.getenv("BIFL_VERSION", "v2.3.4-fp"),
    description="OpenAI-compatible relay API for Responses, Tools, and Realtime endpoints.",
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
# 🗺 Static & Routes
# ---------------------------------------------------------
# Serve /static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve /.well-known/ai-plugin.json
well_known_dir = os.path.join(static_dir, ".well-known")
if os.path.isdir(well_known_dir):
    app.mount("/.well-known", StaticFiles(directory=well_known_dir), name="well-known")

# Register all route modules
register_routes(app)

# ---------------------------------------------------------
# 🩺 Health Endpoint
# ---------------------------------------------------------
@app.get("/health")
async def health_check():
    return JSONResponse(
        {
            "status": "ok",
            "version": os.getenv("BIFL_VERSION", "v2.3.4-fp"),
            "mode": APP_MODE,
            "default_model": DEFAULT_MODEL,
            "build_date": os.getenv("BUILD_DATE"),
            "channel": os.getenv("BUILD_CHANNEL"),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
    )

# ---------------------------------------------------------
# 🌍 Root Metadata
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
# 🧪 Local Entry Point
# ---------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=True,
        log_level="info",
    )

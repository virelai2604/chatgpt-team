# ==========================================================
# main.py — ChatGPT Team Relay (Ground Truth Edition)
# ==========================================================

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# --- Load environment variables (.env for local, Render env vars in prod) ---
load_dotenv()

# ==========================================================
# Basic App Configuration
# ==========================================================
APP_MODE = os.getenv("APP_MODE", "development")
RELAY_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
RELAY_VERSION = os.getenv("RELAY_VERSION", "v2.3.4-fp")
PORT = int(os.getenv("PORT", 8080))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("relay")

logger.info(f"[Relay] Starting {RELAY_NAME} ({APP_MODE}) mode — version {RELAY_VERSION}")

app = FastAPI(
    title=RELAY_NAME,
    version=RELAY_VERSION,
    description="A fully OpenAI-compatible relay with Ground Truth routing and plugin integration.",
)

# ==========================================================
# Static File Mount (for /.well-known/ai-plugin.json & assets)
# ==========================================================
if not os.path.exists("static"):
    os.makedirs("static/.well-known", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def serve_plugin_manifest():
    """Serve ChatGPT plugin manifest."""
    manifest_path = os.path.join("static", ".well-known", "ai-plugin.json")
    if not os.path.exists(manifest_path):
        return {"error": "Plugin manifest not found"}
    return FileResponse(manifest_path, media_type="application/json")

@app.get("/static/logo.png", include_in_schema=False)
async def serve_logo():
    """Serve plugin logo (optional)."""
    logo_path = os.path.join("static", "logo.png")
    if not os.path.exists(logo_path):
        return {"error": "Logo not found"}
    return FileResponse(logo_path, media_type="image/png")

# ==========================================================
# Middleware Configuration
# ==========================================================
from app.middleware.validation import ResponseValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware

# --- CORS ---
allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core middleware stack ---
app.add_middleware(ResponseValidationMiddleware)
app.add_middleware(P4OrchestratorMiddleware)

# ==========================================================
# Register All Routes
# ==========================================================
from app.routes.register_routes import register_routes
app = register_routes(app)

# ==========================================================
# Root Endpoint
# ==========================================================
@app.get("/", tags=["Meta"])
async def root():
    """Public metadata and diagnostics."""
    return {
        "service": RELAY_NAME,
        "status": "running",
        "mode": APP_MODE,
        "version": RELAY_VERSION,
        "docs": "/docs",
        "openapi_spec": "/v1/openapi.yaml",
        "plugin_manifest": "/.well-known/ai-plugin.json",
        "health": "/health",
        "upstream": os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
    }

# ==========================================================
# Application Entrypoint
# ==========================================================
if __name__ == "__main__":
    import uvicorn

    logger.info(f"[Relay] Launching on 0.0.0.0:{PORT}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=(APP_MODE == "development"),
        log_level=LOG_LEVEL.lower(),
    )
# ==========================================================
# main.py — ChatGPT Team Relay (Ground Truth Edition)
# ==========================================================

import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# --- Load environment variables (.env for local, Render env vars in prod) ---
load_dotenv()

# ==========================================================
# Basic App Configuration
# ==========================================================
APP_MODE = os.getenv("APP_MODE", "development")
RELAY_NAME = os.getenv("RELAY_NAME", "ChatGPT Team Relay")
RELAY_VERSION = os.getenv("RELAY_VERSION", "v2.3.4-fp")
PORT = int(os.getenv("PORT", 8080))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger("relay")

logger.info(f"[Relay] Starting {RELAY_NAME} ({APP_MODE}) mode — version {RELAY_VERSION}")

app = FastAPI(
    title=RELAY_NAME,
    version=RELAY_VERSION,
    description="A fully OpenAI-compatible relay with Ground Truth routing and plugin integration.",
)

# ==========================================================
# Static File Mount (for /.well-known/ai-plugin.json & assets)
# ==========================================================
if not os.path.exists("static"):
    os.makedirs("static/.well-known", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/.well-known/ai-plugin.json", include_in_schema=False)
async def serve_plugin_manifest():
    """Serve ChatGPT plugin manifest."""
    manifest_path = os.path.join("static", ".well-known", "ai-plugin.json")
    if not os.path.exists(manifest_path):
        return {"error": "Plugin manifest not found"}
    return FileResponse(manifest_path, media_type="application/json")

@app.get("/static/logo.png", include_in_schema=False)
async def serve_logo():
    """Serve plugin logo (optional)."""
    logo_path = os.path.join("static", "logo.png")
    if not os.path.exists(logo_path):
        return {"error": "Logo not found"}
    return FileResponse(logo_path, media_type="image/png")

# ==========================================================
# Middleware Configuration
# ==========================================================
from app.middleware.validation import ResponseValidationMiddleware
from app.middleware.p4_orchestrator import P4OrchestratorMiddleware

# --- CORS ---
allowed_origins = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core middleware stack ---
app.add_middleware(ResponseValidationMiddleware)
app.add_middleware(P4OrchestratorMiddleware)

# ==========================================================
# Register All Routes
# ==========================================================
from app.routes.register_routes import register_routes
app = register_routes(app)

# ==========================================================
# Root Endpoint
# ==========================================================
@app.get("/", tags=["Meta"])
async def root():
    """Public metadata and diagnostics."""
    return {
        "service": RELAY_NAME,
        "status": "running",
        "mode": APP_MODE,
        "version": RELAY_VERSION,
        "docs": "/docs",
        "openapi_spec": "/v1/openapi.yaml",
        "plugin_manifest": "/.well-known/ai-plugin.json",
        "health": "/health",
        "upstream": os.getenv("OPENAI_BASE_URL", "https://api.openai.com"),
    }

# ==========================================================
# Application Entrypoint
# ==========================================================
if __name__ == "__main__":
    import uvicorn

    logger.info(f"[Relay] Launching on 0.0.0.0:{PORT}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=(APP_MODE == "development"),
        log_level=LOG_LEVEL.lower(),
    )

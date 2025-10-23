# app/main.py
from __future__ import annotations

import os
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Load env early
load_dotenv()

# --- Utilities (project-local) ---
from app.utils.error_handler import error_response
from app.utils.db_logger import init_db

# --- Routers (BIFL surface) ---
# NOTE: these routers define absolute paths (e.g., /v1/responses) or are mounted with a prefix below.
from app.routes import (
    responses,         # /v1/responses  (unified)
    files,             # /v1/files      (mounted with prefix)
    audio,             # /v1/audio      (mounted with prefix)
    images,            # /v1/images     (mounted with prefix)
    vector_stores,     # /v1/vector_stores (mounted with prefix)
    models,            # /v1/models     (mounted with prefix)
    openapi,           # /openapi.yaml and helpers
    relay_status,      # /v1/relay/status or similar
    usage              # organization usage endpoints (mounted under /v1/organization/usage/*)
)

# Catch-all passthrough (must be last)
from app.api import passthrough_proxy  # blocks legacy endpoints & forwards others. :contentReference[oaicite:3]{index=3}

app = FastAPI(title="OpenAI Relay", version="2025.10.23")

# --- CORS (relax in dev; restrict in prod) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Startup: ensure DB tables exist ---
@app.on_event("startup")
def _startup() -> None:
    init_db()

# --- Static mounts for plugin + assets ---
def _mount_static(app: FastAPI) -> None:
    """
    Serve /.well-known/ai-plugin.json and other static assets.
    Supports either 'static' or 'Static' directory names.
    """
    for base in ("static", "Static"):
        well_known_dir = os.path.join(base, ".well-known")
        if os.path.isdir(well_known_dir):
            app.mount("/.well-known", StaticFiles(directory=well_known_dir), name="well_known")
            break

    # Optional general static (logo.png, legal, etc.)
    for base in ("static", "Static"):
        if os.path.isdir(base):
            app.mount("/static", StaticFiles(directory=base), name="static")
            break

_mount_static(app)

# --- Health and Root ---
@app.get("/v1/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "ok", "detail": "ChatGPT Team Relay is running."}

# --- Global error handler (consistent JSON) ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {request.method} {request.url}\n{traceback.format_exc()}")
    return error_response("internal_server_error", str(exc), status_code=500)

# --- First-class routers (specific routes first) ---
# Unified responses
app.include_router(responses.router)  # /v1/responses etc. (non-stream tool loop; stream passthrough) 

# Resource families (mounted with prefixes)
app.include_router(files.router,         prefix="/v1/files")           # list/get/delete/content, uploads, etc.
app.include_router(audio.router,         prefix="/v1/audio")           # transcriptions/translations/speech
app.include_router(images.router,        prefix="/v1/images")          # generations/edits/variations
app.include_router(vector_stores.router, prefix="/v1/vector_stores")   # vector store + batch/file ops
app.include_router(models.router,        prefix="/v1/models")          # model list

# Organization Usage (enterprise metrics)
# Exposes: /v1/organization/usage/images, /audio_transcriptions, /code_interpreter_sessions :contentReference[oaicite:5]{index=5}
app.include_router(usage.router, prefix="/v1/organization/usage")

# Relay status + OpenAPI surface
app.include_router(relay_status.router)
app.include_router(openapi.router)

# --- Catch-all passthrough (MUST be last) ---
# Deny-lists legacy routes and proxies the rest to OpenAI (SSE/NDJSON safe). :contentReference[oaicite:6]{index=6}
app.include_router(passthrough_proxy.router)

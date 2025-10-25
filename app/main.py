# app/main.py
from __future__ import annotations
import os, traceback
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

load_dotenv()

from app.utils.error_handler import error_response
from app.utils.db_logger import init_db

# Routers
from app.routes import (
    responses, files, audio, images, vector_stores, models,
    openapi, relay_status, usage, conversations, videos
)
from app.routes.services import tools_admin   # ← NEW
from app.api import passthrough_proxy

# ───────────────────────────────────────────────────────────────
#  FastAPI App
# ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="OpenAI Relay (BIFL v2.1)",
    version="2025.10.25",
    description="Unified OpenAI-compatible relay supporting Sora 2 Pro and parallel tools."
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def _startup() -> None:
    init_db()

# Static mounts
def _mount_static(app: FastAPI) -> None:
    for base in ("static", "Static"):
        well_known = os.path.join(base, ".well-known")
        if os.path.isdir(well_known):
            app.mount("/.well-known", StaticFiles(directory=well_known), name="well_known")
            break
    for base in ("static", "Static"):
        if os.path.isdir(base):
            app.mount("/static", StaticFiles(directory=base), name="static")
            break
_mount_static(app)

# ───────────────────────────────────────────────────────────────
#  Health and Root
# ───────────────────────────────────────────────────────────────
@app.get("/v1/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "ok", "detail": "ChatGPT Team Relay (BIFL v2.1) is running."}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[ERROR] {request.method} {request.url}\n{traceback.format_exc()}")
    return error_response("internal_server_error", str(exc), status_code=500)

# ───────────────────────────────────────────────────────────────
#  Routers (Specific → Generic)
# ───────────────────────────────────────────────────────────────
app.include_router(responses.router)
app.include_router(files.router, prefix="/v1/files")
app.include_router(audio.router, prefix="/v1/audio")
app.include_router(images.router, prefix="/v1/images")
app.include_router(vector_stores.router, prefix="/v1/vector_stores")
app.include_router(models.router, prefix="/v1/models")
app.include_router(usage.router, prefix="/v1/organization/usage")
app.include_router(conversations.router, prefix="/v1/conversations")
app.include_router(videos.router, prefix="/v1")
app.include_router(relay_status.router)
app.include_router(openapi.router)
app.include_router(tools_admin.router)  # ← NEW Admin Tool Router
app.include_router(passthrough_proxy.router)  # MUST remain last

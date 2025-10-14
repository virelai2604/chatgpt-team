from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

from app.utils.error_handler import error_response

from app.routes import (
    chat, completions, conversations, files, models, openapi, assistants, tools, attachments, audio, images, embeddings,
    moderations, threads, vector_stores, videos, batch, relay_status, responses, tools
)
from app.api import passthrough_proxy

from app.utils.db_logger import init_db
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OpenAI Relay", version="1.0.0")

# === CORS Middleware for plugin/frontend/browser use ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For dev, allow all. Restrict in prod!
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Ensure all database tables exist before serving requests (BIFL)."""
    init_db()

@app.get("/v1/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "ok", "detail": "ChatGPT relay is running."}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    print(f"[ERROR] {request.method} {request.url}\n{tb}")
    return error_response("internal_server_error", str(exc), status_code=500)

# === Register all routers ===
app.include_router(chat.router, prefix="/v1/chat")
app.include_router(completions.router, prefix="/v1/completions")
app.include_router(models.router, prefix="/v1/models")
app.include_router(files.router, prefix="/v1/files")
app.include_router(assistants.router, prefix="/v1/assistants")
app.include_router(tools.router, prefix="/v1/tools")
app.include_router(audio.router, prefix="/v1/audio")
app.include_router(images.router, prefix="/v1/images")
app.include_router(embeddings.router, prefix="/v1/embeddings")
app.include_router(moderations.router, prefix="/v1/moderations")
app.include_router(threads.router, prefix="/v1/threads")
app.include_router(vector_stores.router, prefix="/v1/vector_stores")
app.include_router(videos.router, prefix="/v1/videos")
app.include_router(batch.router, prefix="/v1/batch")
app.include_router(attachments.router, prefix="/v1/attachments")
app.include_router(conversations.router, prefix="/v1/conversations")
app.include_router(relay_status.router)
app.include_router(responses.router)
app.include_router(openapi.router)

# === Passthrough proxy registered LAST ===
app.include_router(passthrough_proxy.router)  # <- Catches all unmatched /v1/* requests

# Static files (e.g. for .well-known/ai-plugin.json)
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# Load .env before anything else!
load_dotenv()

from app.routes import (
    chat, completions, files, models, openapi, assistants, tools, proxy,
    audio, images, embeddings, moderations, threads, vector_stores, batch
)
import httpx

app = FastAPI(title="OpenAI Relay (FastAPI)", version="1.0.0")

# (Optional) Debug route for checking API key (remove or comment out in prod)
# @app.get("/debug/api_key_raw")
# async def debug_api_key_raw():
#     key = os.environ.get("OPENAI_API_KEY")
#     return {"OPENAI_API_KEY": key}

# Register all routers with their prefixes
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
app.include_router(batch.router, prefix="/v1/batch")
app.include_router(openapi.router)
app.include_router(proxy.router)  # Proxy must be last!

@app.get("/v1/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"status": "ok", "detail": "ChatGPT relay is running."}

app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

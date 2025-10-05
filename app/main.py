from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from app.routes import (
    chat, completions, files, models, openapi, assistants, tools, proxy,
    audio, images, embeddings, moderations
)
import httpx
import os

load_dotenv()
app = FastAPI(title="OpenAI Relay (FastAPI)", version="1.0.0")

# Core OpenAI endpoints
app.include_router(chat.router,        prefix="/v1/chat")
app.include_router(completions.router, prefix="/v1")
app.include_router(models.router,      prefix="/v1/models")
app.include_router(files.router,       prefix="/v1")
app.include_router(assistants.router,  prefix="/v1")
app.include_router(tools.router,       prefix="/v1")
app.include_router(audio.router,       prefix="/v1")
app.include_router(images.router,      prefix="/v1")
app.include_router(embeddings.router,  prefix="/v1")
app.include_router(moderations.router, prefix="/v1")
app.include_router(openapi.router)

# Proxy must be LAST for fallback passthrough!
app.include_router(proxy.router)

# Health check, always returns 200 OK for GET
@app.get("/v1/health")
async def health():
    return {"status": "ok"}

# List models, always GET, never requires body
@app.get("/v1/models")
async def models():
    openai_url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY', '')}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(openai_url, headers=headers)
        return resp.json(), resp.status_code

@app.get("/")
async def root():
    return {"status": "ok", "detail": "ChatGPT relay is running."}

# Static files for /.well-known
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from app.routes import (
    chat, completions, files, models, openapi, assistants, tools, proxy
)

load_dotenv()

app = FastAPI(title="OpenAI Relay (FastAPI)", version="1.0.0")

# Include API routers
app.include_router(chat.router, prefix="/v1/chat")
app.include_router(completions.router, prefix="/v1")
app.include_router(files.router, prefix="/v1/files")
app.include_router(models.router, prefix="/v1/models")
app.include_router(assistants.router, prefix="/v1/assistants")
app.include_router(tools.router, prefix="/v1/tools")
app.include_router(openapi.router)
app.include_router(proxy.router)

# Root health check
@app.get("/")
async def root():
    return {"status": "ok", "detail": "ChatGPT relay is running."}

# /v1/health health check
@app.get("/v1/health")
async def health():
    return {"status": "ok"}

# Static files for /.well-known
app.mount("/.well-known", StaticFiles(directory=".well-known"), name="well-known")

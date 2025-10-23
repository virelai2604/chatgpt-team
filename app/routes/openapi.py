# app/routes/openapi.py
import os
from fastapi import APIRouter, Response, Request

router = APIRouter()

@router.get("/openapi.yaml")
async def serve_openapi_yaml(request: Request):
    path = os.path.abspath(os.path.join(os.getcwd(), "openapi.yaml"))
    if not os.path.isfile(path):
        return Response(status_code=404, content="openapi.yaml not found", media_type="text/plain")
    with open(path, "r", encoding="utf-8") as f:
        return Response(content=f.read(), media_type="application/yaml")

@router.get("/.well-known/ai-plugin.json")
async def serve_ai_plugin(request: Request):
    # Try static/.well-known first, then project root
    candidates = [
        os.path.abspath(os.path.join(os.getcwd(), "static", ".well-known", "ai-plugin.json")),
        os.path.abspath(os.path.join(os.getcwd(), "ai-plugin.json")),
    ]
    for p in candidates:
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                return Response(content=f.read(), media_type="application/json")
    return Response(status_code=404, content="ai-plugin.json not found", media_type="text/plain")

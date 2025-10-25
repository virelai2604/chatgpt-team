# app/routes/openapi.py
"""
BIFL v2.1 – OpenAPI & Plugin Documentation Router
Serves openapi.yaml and .well-known/ai-plugin.json with caching.
"""

import os
from fastapi import APIRouter, Response, Request

router = APIRouter(tags=["documentation"])

# ───────────────────────────────────────────────────────────────
#  Serve openapi.yaml
# ───────────────────────────────────────────────────────────────
@router.get("/openapi.yaml")
async def serve_openapi_yaml(request: Request):
    """
    Serves the OpenAPI specification (application/yaml).
    Search order:
    1. static/openapi.yaml
    2. project root openapi.yaml
    """
    candidates = [
        os.path.join(os.getcwd(), "static", "openapi.yaml"),
        os.path.join(os.getcwd(), "openapi.yaml"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return Response(
                    content=f.read(),
                    media_type="application/yaml",
                    headers={"Cache-Control": "public, max-age=86400"},
                )
    return Response("openapi.yaml not found", status_code=404, media_type="text/plain")

# ───────────────────────────────────────────────────────────────
#  Serve ai-plugin.json
# ───────────────────────────────────────────────────────────────
@router.get("/.well-known/ai-plugin.json")
async def serve_ai_plugin(request: Request):
    """
    Serves ChatGPT plugin manifest (.well-known/ai-plugin.json).
    Search order:
    1. static/.well-known/ai-plugin.json
    2. project root ai-plugin.json
    """
    candidates = [
        os.path.join(os.getcwd(), "static", ".well-known", "ai-plugin.json"),
        os.path.join(os.getcwd(), "ai-plugin.json"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                return Response(
                    content=f.read(),
                    media_type="application/json",
                    headers={"Cache-Control": "public, max-age=86400"},
                )
    return Response("ai-plugin.json not found", status_code=404, media_type="text/plain")

# ───────────────────────────────────────────────────────────────
#  /docs/status (for deployment verification)
# ───────────────────────────────────────────────────────────────
@router.get("/docs/status")
async def docs_status():
    """
    Returns file existence status for docs validation.
    """
    base = os.getcwd()
    openapi_path = os.path.join(base, "openapi.yaml")
    plugin_path = os.path.join(base, "ai-plugin.json")
    return {
        "openapi.yaml": os.path.isfile(openapi_path),
        "ai-plugin.json": os.path.isfile(plugin_path),
        "cwd": base,
    }

# app/routes/openapi.py
# BIFL v2.2 — Unified API Schema Surface for ChatGPT Team Relay (BIFL Surface)
# Auto-generates and serves OpenAPI 3.1 schemas with relay parity.

import os
import json
import time
import inspect
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse
from typing import Dict, Any
from app.routes import (
    responses, files, images, audio, videos,
    models, vector_stores, conversations, embeddings,
    moderations, attachments, usage
)

router = APIRouter(prefix="/v1/openapi", tags=["OpenAPI"])

# === Constants ===
SERVICE_NAME = "ChatGPT Team Relay (BIFL Surface)"
VERSION = os.getenv("BIFL_VERSION", "2025-10-24")
BASE_URL = os.getenv("RELAY_BASE_URL", "https://chatgpt-team-relay.onrender.com")

# === Registry of active modules ===
ROUTE_MODULES = {
    "responses": responses,
    "files": files,
    "images": images,
    "audio": audio,
    "videos": videos,
    "models": models,
    "vector_stores": vector_stores,
    "conversations": conversations,
    "embeddings": embeddings,
    "moderations": moderations,
    "attachments": attachments,
    "usage": usage,
}

# === Helper to extract route metadata from a module ===
def describe_module(module):
    info = []
    for name, obj in inspect.getmembers(module):
        if hasattr(obj, "methods") and hasattr(obj, "path"):
            info.append({
                "path": getattr(obj, "path", "unknown"),
                "methods": list(getattr(obj, "methods", [])),
                "doc": inspect.getdoc(obj) or "",
            })
    return info


def generate_schema() -> Dict[str, Any]:
    """Return the full OpenAPI 3.1 schema as a dict."""
    paths: Dict[str, Any] = {}
    for name, module in ROUTE_MODULES.items():
        routes = describe_module(module)
        for route in routes:
            methods = route.get("methods", ["GET"])
            paths[route["path"]] = {
                m.lower(): {
                    "summary": route["doc"].split("\n")[0] if route["doc"] else f"{name} endpoint",
                    "description": route["doc"],
                    "responses": {"200": {"description": "Success"}},
                }
                for m in methods
            }

    return {
        "openapi": "3.1.0",
        "info": {
            "title": SERVICE_NAME,
            "version": VERSION,
            "license": {"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
            "description": (
                "Unified BIFL Surface (OpenAI-compatible)\n\n"
                "Supports /v1/responses, /v1/files, /v1/images, /v1/audio, /v1/videos, "
                " /v1/models, /v1/vector_stores, /v1/jobs, /v1/realtime and more."
            ),
        },
        "servers": [{"url": BASE_URL}],
        "security": [{"BearerAuth": []}],
        "tags": [{"name": name.title(), "description": f"{name} operations"} for name in ROUTE_MODULES.keys()],
        "paths": paths,
        "components": {
            "securitySchemes": {
                "BearerAuth": {"type": "http", "scheme": "bearer"},
            }
        },
    }


@router.get("/", response_class=JSONResponse)
async def get_openapi_schema(request: Request):
    """Return the BIFL unified OpenAPI 3.1 JSON schema."""
    return JSONResponse(content=generate_schema())


@router.get("/yaml", response_class=PlainTextResponse)
async def get_openapi_yaml(request: Request):
    """Return the OpenAPI schema as YAML (text)."""
    try:
        import yaml
        schema = generate_schema()
        return PlainTextResponse(content=yaml.safe_dump(schema, sort_keys=False))
    except Exception:
        return PlainTextResponse(content="PyYAML not installed", status_code=500)


@router.get("/html", response_class=HTMLResponse)
async def openapi_html():
    """Serve a basic Swagger-UI style viewer."""
    return HTMLResponse(
        f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8" />
          <title>BIFL OpenAPI Schema</title>
          <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.min.js"></script>
          <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.min.css" />
        </head>
        <body>
          <div id="swagger-ui"></div>
          <script>
            window.onload = () => {{
              SwaggerUIBundle({{
                url: "{BASE_URL}/v1/openapi",
                dom_id: '#swagger-ui',
                presets: [SwaggerUIBundle.presets.apis],
                layout: "BaseLayout"
              }});
            }};
          </script>
        </body>
        </html>
        """
    )


@router.get("/summary")
async def summary():
    """Return a lightweight summary of the registered routes."""
    data = []
    for name, module in ROUTE_MODULES.items():
        routes = describe_module(module)
        data.append({"module": name, "routes": len(routes)})
    return JSONResponse(content={"object": "openapi_summary", "data": data, "generated_at": int(time.time())})


@router.get("/ping")
async def ping():
    """Quick ping for relay health."""
    return JSONResponse(content={"status": "ok", "version": VERSION, "time": int(time.time())})

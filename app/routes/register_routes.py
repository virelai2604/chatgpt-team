"""
register_routes.py — Unified Router Registration
────────────────────────────────────────────────
Registers all /v1 API endpoints (OpenAI-compatible) and custom /actions routes
for ChatGPT Actions integration. 100% SDK-aligned as of OpenAI Node 6.9 / Python 2.8.
"""

import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse, PlainTextResponse
from app.utils.logger import relay_log as logger
from app.api.tools_api import load_manifest


def register_all_routes(app: FastAPI):
    """
    Attach every major route group to the FastAPI app.
    """

    # ============================================================
    # 1. Core OpenAI-compatible endpoints
    # ============================================================
    from app.routes import (
        responses,
        embeddings,
        models,
        files,
        vector_stores,
        realtime,
        conversations,
        actions,          # ChatGPT Actions routes
    )

    # Attach all /v1 SDK-parity routes
    app.include_router(responses.router, prefix="/v1")
    app.include_router(embeddings.router, prefix="/v1")
    app.include_router(models.router, prefix="/v1")
    app.include_router(files.router, prefix="/v1")
    app.include_router(vector_stores.router, prefix="/v1")
    app.include_router(realtime.router, prefix="/v1")

    # Optional internal conversation logs
    app.include_router(conversations.router, prefix="/v1")

    # Attach ChatGPT Actions routes (custom APIs)
    app.include_router(actions.router, prefix="")

    logger.info("✅ Registered all OpenAI and ChatGPT Action routes.")

    # ============================================================
    # 2. Health / Root endpoints
    # ============================================================
    @app.get("/health", tags=["system"])
    @app.get("/v1/health", tags=["system"])
    async def health_check():
        """Simple system status endpoint."""
        return {
            "object": "health",
            "status": "ok",
            "service": "ChatGPT Team Relay",
            "uptime": "online",
        }

    @app.get("/", tags=["system"])
    async def root_info():
        """Root information endpoint."""
        return {
            "object": "relay_root",
            "status": "ok",
            "description": "ChatGPT Team Relay — OpenAI-compatible API gateway.",
            "version": "2025.11"
        }

    # ============================================================
    # 3. /v1/tools — Manifest-driven registry
    # ============================================================
    @app.get("/v1/tools", tags=["tools"])
    @app.get("/v1/tools/{tool_id}", tags=["tools"])
    async def list_tools(tool_id: str | None = None):
        """
        Returns all tools declared in tools_manifest.json.
        Compatible with SDK /v1/tools schema.
        """
        manifest = load_manifest()
        if tool_id:
            for tool in manifest.get("tools", []):
                if tool["id"] == tool_id:
                    return JSONResponse(tool, status_code=200)
            return JSONResponse({"error": f"Tool '{tool_id}' not found"}, status_code=404)
        return JSONResponse(manifest, status_code=200)

    logger.info("🧰 Loaded dynamic /v1/tools manifest route.")

    # ============================================================
    # 4. Serve OpenAPI schema for ChatGPT Actions
    # ============================================================
    @app.get("/schemas/openapi.yaml", tags=["schemas"])
    async def serve_schema():
        """
        Serves the OpenAPI YAML schema file required by ChatGPT Actions.
        """
        schema_path = os.path.join(os.getcwd(), "schemas", "openapi.yaml")
        if not os.path.exists(schema_path):
            return JSONResponse({"error": "Schema not found."}, status_code=404)

        with open(schema_path, "r", encoding="utf-8") as f:
            content = f.read()
        return PlainTextResponse(content, media_type="text/yaml", status_code=200)

    # ============================================================
    # 5. Local Realtime session mock (optional diagnostic)
    # ============================================================
    @app.get("/v1/realtime/sessions", tags=["realtime"])
    async def get_realtime_session():
        """
        Lightweight local realtime-session stub.
        """
        return {
            "object": "realtime_session",
            "status": "ok",
            "events": [],
            "message": "Realtime session active (local mock)."
        }

    logger.info("📘 Local meta routes (health, tools, schema, realtime) initialized.")

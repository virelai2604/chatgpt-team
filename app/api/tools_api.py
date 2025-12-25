from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.utils.logger import relay_log as logger

router = APIRouter(tags=["manifest"])


def get_tools_manifest() -> dict[str, Any]:
    """Load the tools manifest JSON shipped with the relay.

    This is intentionally file-backed (not hard-coded) so the manifest can be edited
    without changing Python code.
    """
    manifest_path = Path(__file__).resolve().parent.parent / "manifests" / "tools_manifest.json"
    try:
        with manifest_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to load tools manifest: %s", manifest_path)
        return {}


def _normalize_upstream_base_url(base: str) -> str:
    """Return an upstream base URL suitable for documentation/metadata.

    Ensures the returned string ends with /v1 (without double-slashes).
    """
    base = (base or "").rstrip("/")
    if not base:
        return "https://api.openai.com/v1"
    if base.endswith("/v1"):
        return base
    return f"{base}/v1"


def build_manifest_response() -> dict[str, Any]:
    s = get_settings()
    tools_manifest = get_tools_manifest()

    endpoints: dict[str, list[str]] = {
        # Canonical surface: Responses
        "responses": ["/v1/responses"],
        "responses_compact": ["/v1/responses/compact"],
        # Common aux surfaces
        "models": ["/v1/models"],
        "embeddings": ["/v1/embeddings"],
        "images": ["/v1/images/generations"],
        # Multipart endpoints (NOT Actions-friendly; keep for non-Actions clients)
        "images_edits_multipart": ["/v1/images/edits"],
        "images_variations_multipart": ["/v1/images/variations"],
        # Actions-friendly wrappers (JSON body with URL/base64)
        "images_actions": ["/v1/actions/images/edits", "/v1/actions/images/variations"],
        # Realtime: HTTP session creation only (WS upgrades are intentionally non-Actions)
        "realtime": ["/v1/realtime/sessions"],
        # Escape hatch (server-side allowlist + blocklist). Not exposed in actions schema by default.
        "proxy": ["/v1/proxy"],
    }

    actions_openapi_url = "/openapi.actions.json"
    actions_openapi_groups = [
        "health",
        "models",
        "responses",
        "embeddings",
        "images",
        "images_actions",
    ]

    return {
        "object": "relay.manifest",
        "data": tools_manifest,
        "endpoints": endpoints,
        "meta": {
            "relay_name": "chatgpt-team-relay",
            "environment": getattr(s, "APP_ENVIRONMENT", "local"),
            "auth_required": bool(getattr(s, "RELAY_AUTH_ENABLED", True)),
            "upstream_base_url": _normalize_upstream_base_url(getattr(s, "openai_base_url", "")),
            "actions_openapi_url": actions_openapi_url,
            "actions_openapi_groups": actions_openapi_groups,
        },
    }


@router.get("/manifest", include_in_schema=False)
async def get_manifest() -> dict[str, Any]:
    """Return a relay manifest used by tooling and smoke tests."""
    return build_manifest_response()


@router.get("/v1/manifest", include_in_schema=False)
async def get_manifest_v1() -> dict[str, Any]:
    """Legacy alias for /manifest."""
    return build_manifest_response()


# ---- Actions: curated OpenAPI schema (HTTP-only, JSON-first) ----

_ACTIONS_ALLOWED_PATHS: set[str] = {
    # Health
    "/health",
    "/v1/health",
    # Models
    "/v1/models",
    "/v1/models/{model}",
    # Canonical Responses surface
    "/v1/responses",
    "/v1/responses/compact",
    "/v1/responses/{response_id}",
    "/v1/responses/{response_id}/cancel",
    "/v1/responses/{response_id}/input_items",
    # Embeddings
    "/v1/embeddings",
    # Images (JSON)
    "/v1/images",
    "/v1/images/generations",
    # Images Actions wrappers (JSON)
    "/v1/actions/images/edits",
    "/v1/actions/images/variations",
    # Minimal Actions metadata endpoints (optional)
    "/v1/actions/ping",
    "/v1/actions/relay_info",
}


@router.get("/openapi.actions.json", include_in_schema=False)
async def get_openapi_actions(request: Request) -> JSONResponse:
    """Return an Actions-safe OpenAPI schema.

    Rationale:
      - ChatGPT Actions are HTTP-only (no WebSocket upgrades).
      - Streaming SSE endpoints are excluded.
      - Multipart file-upload endpoints are excluded; use /v1/actions/images/* wrappers instead.
    """
    full_schema = request.app.openapi()
    schema = copy.deepcopy(full_schema)

    paths = schema.get("paths", {})
    schema["paths"] = {p: spec for (p, spec) in paths.items() if p in _ACTIONS_ALLOWED_PATHS}

    # Make the schema standalone and Actions-friendly
    info = schema.get("info", {}) or {}
    info["title"] = info.get("title", "chatgpt-team-relay") + " (Actions)"
    info.setdefault(
        "description",
        "Curated OpenAPI schema for ChatGPT Actions: HTTP-only and JSON-first.",
    )
    schema["info"] = info

    schema["servers"] = [{"url": str(request.base_url).rstrip("/")}]

    return JSONResponse(schema)

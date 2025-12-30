from __future__ import annotations

import copy
from typing import Any, Dict

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings

router = APIRouter()


def _build_manifest() -> Dict[str, Any]:
    s = get_settings()

    endpoints = {
        "health": ["/health", "/v1/health"],
        "models": ["/v1/models", "/v1/models/{model}"],
        "responses": [
            "/v1/responses",
            "/v1/responses/{response_id}",
            "/v1/responses/{response_id}/cancel",
            "/v1/responses/{response_id}/input_items",
        ],
        "responses_stream": ["/v1/responses:stream"],
        "responses_compact": ["/v1/responses/compact"],
        "embeddings": ["/v1/embeddings"],
        "images": ["/v1/images/generations", "/v1/images/edits", "/v1/images/variations"],
        "images_actions": ["/v1/actions/images/edits", "/v1/actions/images/variations"],
        "proxy": ["/v1/proxy"],
        "realtime_http": ["/v1/realtime/sessions"],

        # NEW: Actions-friendly wrapper for multipart file upload
        "files_actions": ["/v1/actions/files/upload"],
        "uploads_actions": [
            "/v1/actions/uploads",
            "/v1/actions/uploads/{upload_id}/parts",
            "/v1/actions/uploads/{upload_id}/complete",
            "/v1/actions/uploads/{upload_id}/cancel",
        ],
        "videos_actions": ["/v1/actions/videos"],
    }

    meta = {
        "relay_name": getattr(s, "RELAY_NAME", "chatgpt-team-relay"),
        "auth_required": bool(getattr(s, "RELAY_AUTH_ENABLED", False)),
        "auth_header": "X-Relay-Key",
        "upstream_base_url": getattr(s, "UPSTREAM_BASE_URL", getattr(s, "OPENAI_API_BASE", "")),
        "actions_openapi_url": "/openapi.actions.json",
        "actions_openapi_groups": [
            "health",
            "models",
            "responses",
            "responses_stream",
            "responses_compact",
            "embeddings",
            "images",
            "images_actions",
            "proxy",
            "realtime_http",

            # include wrapper route in Actions schema
            "files_actions",
            "uploads_actions",
            "videos_actions",
        ],
    }

    return {
        "object": "relay.manifest",
        "data": {"endpoints": endpoints, "meta": meta},
        "endpoints": endpoints,
        "meta": meta,
    }


@router.get("/manifest", include_in_schema=False)
@router.get("/v1/manifest", include_in_schema=False)
async def get_manifest() -> Dict[str, Any]:
    return _build_manifest()


@router.get("/openapi.actions.json", include_in_schema=False)
async def openapi_actions(request: Request) -> JSONResponse:
    """
    Curated OpenAPI subset for ChatGPT Actions (REST; no WebSocket client).
    """
    full = request.app.openapi()
    manifest = _build_manifest()

    groups = (manifest.get("meta") or {}).get("actions_openapi_groups") or []
    endpoints = manifest.get("endpoints") or {}
    allowed_paths: set[str] = set()

    for g in groups:
        allowed_paths.update(endpoints.get(str(g), []) or [])

    allowed_paths.update({"/health", "/v1/health"})

    filtered = copy.deepcopy(full)
    filtered["paths"] = {p: spec for p, spec in (full.get("paths") or {}).items() if p in allowed_paths}

    info = filtered.get("info") or {}
    title = str(info.get("title") or "OpenAPI")
    info["title"] = f"{title} (Actions subset)"
    filtered["info"] = info

    return JSONResponse(filtered)

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.utils.logger import relay_log as logger

router = APIRouter()


def _load_tools_manifest_data() -> list[dict[str, Any]]:
    """
    Load the local tools manifest file (used by dev tooling / documentation).

    The file can be either:
      - {"tools": [...]} (preferred)
      - {"data": [...]}  (legacy)
      - [...]            (bare list)
    """
    settings = get_settings()
    path = Path(settings.TOOLS_MANIFEST)

    try:
        raw = path.read_text(encoding="utf-8")
        loaded = json.loads(raw)
    except Exception:
        return []

    if isinstance(loaded, dict):
        if isinstance(loaded.get("tools"), list):
            return [x for x in loaded["tools"] if isinstance(x, dict)]
        if isinstance(loaded.get("data"), list):
            return [x for x in loaded["data"] if isinstance(x, dict)]
        return []

    if isinstance(loaded, list):
        return [x for x in loaded if isinstance(x, dict)]

    return []


def build_manifest_response() -> dict[str, Any]:
    """
    Lightweight capability manifest (human/dev tooling).

    This is *not* the ChatGPT Actions OpenAPI document. Use /openapi.actions.json for Actions.
    """
    settings = get_settings()
    data = _load_tools_manifest_data()

    endpoints: dict[str, list[str]] = {
        "health": ["/health", "/v1/health"],
        "manifest": ["/manifest", "/v1/manifest"],
        "models": ["/v1/models", "/v1/models/{model}"],
        "responses": [
            "/v1/responses",
            "/v1/responses/compact",
            "/v1/responses/{response_id}",
            "/v1/responses/{response_id}/cancel",
            "/v1/responses/{response_id}/input_items",
        ],
        "embeddings": ["/v1/embeddings"],
        "images": [
            "/v1/images",
            "/v1/images/generations",
            "/v1/images/edits",
            "/v1/images/variations",
        ],
        # JSON-only aliases that are convenient for Actions (optional).
        "images_actions": [
            "/v1/actions/images/edits",
            "/v1/actions/images/variations",
        ],
        "files": ["/v1/files", "/v1/files/{file_id}", "/v1/files/{file_id}/content"],
        "uploads": [
            "/v1/uploads",
            "/v1/uploads/{upload_id}",
            "/v1/uploads/{upload_id}/parts",
            "/v1/uploads/{upload_id}/complete",
            "/v1/uploads/{upload_id}/cancel",
        ],
        "batches": ["/v1/batches", "/v1/batches/{batch_id}"],
        # Actions can call the HTTP session-creation endpoint, but not WS upgrades.
        "realtime": ["/v1/realtime/sessions"],
        # Escape hatch for dev tooling; consider omitting from Actions.
        "proxy": ["/v1/proxy"],
    }

    return {
        "object": "list",
        "data": data,
        "endpoints": endpoints,
        "meta": {
            "relay_name": settings.RELAY_NAME,
            "environment": settings.ENVIRONMENT,
            "app_mode": settings.APP_MODE,
            "auth_required": bool(settings.RELAY_AUTH_ENABLED and (settings.RELAY_KEY or settings.RELAY_AUTH_TOKEN)),
            "auth_header": "X-Relay-Key",
            "upstream_base_url": settings.UPSTREAM_BASE_URL,
            "default_model": settings.DEFAULT_MODEL,
            "actions_openapi_url": "/openapi.actions.json",
            # Which endpoint groups are included in the Actions-safe OpenAPI subset.
            "actions_openapi_groups": [
                "health",
                "models",
                "responses",
                "embeddings",
                "images",
                "realtime",
                # "proxy",  # Optional; include only if you want Actions to reach /v1/proxy.
            ],
        },
    }


# ---- Actions-safe OpenAPI subset ----

def _actions_allowed_paths(manifest: dict[str, Any]) -> set[str]:
    groups = manifest.get("meta", {}).get("actions_openapi_groups") or []
    endpoints = manifest.get("endpoints", {}) or {}

    allowed: set[str] = set()
    for g in groups:
        allowed.update(endpoints.get(str(g), []))

    # Always include core health + manifest discovery.
    allowed.update({"/health", "/v1/health", "/manifest", "/v1/manifest"})

    return allowed


def _strip_multipart_from_actions_schema(openapi: dict[str, Any]) -> dict[str, Any]:
    """
    ChatGPT Actions cannot send multipart/form-data. Remove multipart from requestBody
    definitions in the Actions subset to prevent the model from selecting that content type.
    """
    paths = openapi.get("paths") or {}
    for _path, ops in paths.items():
        if not isinstance(ops, dict):
            continue
        for _method, spec in ops.items():
            if not isinstance(spec, dict):
                continue
            rb = spec.get("requestBody")
            if not isinstance(rb, dict):
                continue
            content = rb.get("content")
            if not isinstance(content, dict):
                continue
            if "multipart/form-data" in content:
                del content["multipart/form-data"]
    return openapi


@router.get("/manifest", include_in_schema=False)
@router.get("/v1/manifest", include_in_schema=False)
async def get_manifest() -> dict[str, Any]:
    return build_manifest_response()


@router.get("/openapi.actions.json", include_in_schema=False)
async def openapi_actions(request: Request) -> JSONResponse:
    """
    Return an Actions-safe OpenAPI schema.

    ChatGPT Actions are REST-style request/response calls (no SSE, no WebSocket client)
    and typically operate on JSON bodies. This endpoint filters the relay's full OpenAPI
    schema down to an allowlist of Action-friendly paths.
    """
    manifest = build_manifest_response()
    allowed_paths = _actions_allowed_paths(manifest)

    full = request.app.openapi()

    filtered = copy.deepcopy(full)
    filtered["paths"] = {
        path: spec
        for path, spec in (full.get("paths") or {}).items()
        if path in allowed_paths
    }

    # Ensure the base URL is present for Actions tooling.
    base_url = str(request.base_url).rstrip("/")
    filtered["servers"] = [{"url": base_url}]

    info = filtered.get("info") or {}
    title = str(info.get("title") or "OpenAPI")
    info["title"] = f"{title} (Actions subset)"
    filtered["info"] = info

    filtered = _strip_multipart_from_actions_schema(filtered)

    logger.info("→ [tools_api] served /openapi.actions.json with %d paths", len(filtered.get("paths") or {}))
    return JSONResponse(filtered)

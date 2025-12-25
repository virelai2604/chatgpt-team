from __future__ import annotations

import copy
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import settings

# This router serves:
#   - /manifest: a lightweight capability manifest for human/dev tooling
#   - /openapi.actions.json: a curated OpenAPI subset suitable for ChatGPT Actions

router = APIRouter()

MANIFEST: dict[str, Any] = {
    "object": "relay.manifest",
    "data": [],
    "endpoints": {
        "health": ["/health", "/v1/health"],
        "models": ["/v1/models", "/v1/models/{model}"],
        "responses": ["/v1/responses", "/v1/responses/compact"],
        "embeddings": ["/v1/embeddings"],
        "images": ["/v1/images/generations"],
        "images_actions": ["/v1/actions/images/variations", "/v1/actions/images/edits"],
        "files": ["/v1/files", "/v1/files/{file_id}", "/v1/files/{file_id}/content"],
        "uploads": [
            "/v1/uploads",
            "/v1/uploads/{upload_id}",
            "/v1/uploads/{upload_id}/parts",
            "/v1/uploads/{upload_id}/complete",
            "/v1/uploads/{upload_id}/cancel",
        ],
        "batches": ["/v1/batches", "/v1/batches/{batch_id}"],
        "proxy": ["/v1/proxy"],
    },
    "meta": {
        "relay_name": "chatgpt-team relay",
        "auth_required": settings.RELAY_AUTH_ENABLED,
        "auth_header": "X-Relay-Key",
        "upstream_base_url": settings.UPSTREAM_BASE_URL,
        "actions_openapi_url": "/openapi.actions.json",
        "actions_openapi_groups": [
            "health",
            "models",
            "responses",
            "embeddings",
            "images",
            "images_actions",
            "proxy",
        ],
    },
}


@router.get("/manifest", include_in_schema=False)
@router.get("/v1/manifest", include_in_schema=False)
async def get_manifest() -> dict[str, Any]:
    return MANIFEST


@router.get("/openapi.actions.json", include_in_schema=False)
async def openapi_actions(request: Request) -> JSONResponse:
    """
    Return an Actions-safe OpenAPI schema.

    ChatGPT Actions are REST-style request/response calls (no WebSocket client) and
    typically operate on JSON bodies. This endpoint filters the relay's full OpenAPI
    schema down to an allowlist of Action-friendly paths (see MANIFEST["meta"]).
    """
    full = request.app.openapi()

    groups = MANIFEST.get("meta", {}).get("actions_openapi_groups") or []
    allowed_paths: set[str] = set()
    for g in groups:
        allowed_paths.update(MANIFEST.get("endpoints", {}).get(str(g), []))

    allowed_paths.update({"/health", "/v1/health"})

    filtered = copy.deepcopy(full)
    filtered["paths"] = {
        path: spec
        for path, spec in (full.get("paths") or {}).items()
        if path in allowed_paths
    }

    info = filtered.get("info") or {}
    title = str(info.get("title") or "OpenAPI")
    info["title"] = f"{title} (Actions subset)"
    filtered["info"] = info

    return JSONResponse(filtered)

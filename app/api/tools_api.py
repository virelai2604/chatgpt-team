from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Set

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings

router = APIRouter()


def _load_tools_manifest() -> List[Dict[str, Any]]:
    """
    Optional helper: if app/manifests/tools_manifest.json exists, include it in /manifest.
    """
    app_dir = Path(__file__).resolve().parents[1]
    candidates = [
        app_dir / "manifests" / "tools_manifest.json",
        app_dir / "manifests" / "tools_manifest.tools.json",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            try:
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            except Exception:
                return []
    return []


def _manifest_endpoints() -> Dict[str, List[str]]:
    """
    Canonical manifest endpoint groups.

    Baseline tests require:
      - data.endpoints.responses includes /v1/responses
      - data.endpoints.responses_compact includes /v1/responses/compact
    """
    return {
        "health": ["/health", "/v1/health"],
        "actions": ["/v1/actions/ping", "/v1/actions/health", "/v1/actions/schema"],
        "models": ["/v1/models", "/v1/models/{model}"],
        "responses": [
            "/v1/responses",
            "/v1/responses/{response_id}",
            "/v1/responses/{response_id}/cancel",
            "/v1/responses/{response_id}/input_items",
        ],
        "responses_compact": ["/v1/responses/compact"],
        "embeddings": ["/v1/embeddings"],
        "images": [
            "/v1/images/generations",
            "/v1/images",
            "/v1/images/edits",
            "/v1/images/variations",
        ],
        "images_actions": [
            "/v1/actions/images/edits",
            "/v1/actions/images/variations",
        ],
        "uploads": [
            "/v1/uploads",
            "/v1/uploads/{upload_id}",
            "/v1/uploads/{upload_id}/parts",
            "/v1/uploads/{upload_id}/complete",
            "/v1/uploads/{upload_id}/cancel",
        ],
        "files": [
            "/v1/files",
            "/v1/files/{file_id}",
            "/v1/files/{file_id}/content",
        ],
        "batches": [
            "/v1/batches",
            "/v1/batches/{batch_id}",
            "/v1/batches/{batch_id}/cancel",
        ],
        "realtime": ["/v1/realtime/sessions"],
        "conversations": ["/v1/conversations", "/v1/conversations/{path}"],
        "vector_stores": ["/v1/vector_stores", "/v1/vector_stores/{path}"],
        "proxy": ["/v1/proxy"],
    }


def build_manifest_response(base_url: str = "") -> Dict[str, Any]:
    settings = get_settings()

    manifest = {
        "name": settings.RELAY_NAME,
        "version": "1.0.0",
        "description": "OpenAI-compatible relay with explicit subroutes and Actions-friendly wrappers.",
        "tools": _load_tools_manifest(),
        "endpoints": _manifest_endpoints(),
        "meta": {
            "app_mode": settings.APP_MODE,
            "environment": settings.ENVIRONMENT,
            "relay_auth_enabled": bool(settings.RELAY_AUTH_ENABLED),
            "relay_auth_header": settings.RELAY_AUTH_HEADER,
            "upstream_base_url": settings.UPSTREAM_BASE_URL,
            "openapi_url": "/openapi.json",
            "actions_openapi_url": "/openapi.actions.json",
        },
    }

    return {
        "object": "relay.manifest",
        "data": manifest,
        "meta": {"base_url": base_url},
    }


@router.get("/manifest", include_in_schema=False)
async def manifest(request: Request) -> JSONResponse:
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse(content=build_manifest_response(base_url=base_url))


@router.get("/v1/manifest", include_in_schema=False)
async def manifest_v1(request: Request) -> JSONResponse:
    base_url = str(request.base_url).rstrip("/")
    return JSONResponse(content=build_manifest_response(base_url=base_url))


def _collect_allowed_paths(manifest: Dict[str, Any]) -> Set[str]:
    allowed: Set[str] = set()
    endpoints = manifest.get("endpoints") or {}
    if isinstance(endpoints, dict):
        for paths in endpoints.values():
            if isinstance(paths, list):
                for p in paths:
                    if not isinstance(p, str):
                        continue
                    # Normalize placeholder used by some wildcard routes
                    allowed.add(p.replace("{path}", "{path:path}"))
    return allowed


def _filtered_openapi_for_actions(request: Request) -> Dict[str, Any]:
    """
    Actions-focused OpenAPI document by filtering app.openapi()
    down to the paths we advertise in /manifest.
    """
    base = request.app.openapi()
    manifest = build_manifest_response(base_url=str(request.base_url).rstrip("/"))["data"]
    allowed = _collect_allowed_paths(manifest)

    base_paths = base.get("paths") or {}
    base["paths"] = {k: v for k, v in base_paths.items() if k in allowed}

    info = base.get("info") or {}
    title = info.get("title") or "OpenAI Relay"
    info["title"] = f"{title} (Actions)"
    base["info"] = info

    return base


@router.get("/openapi.actions.json", include_in_schema=False)
async def openapi_actions_json(request: Request) -> JSONResponse:
    return JSONResponse(content=_filtered_openapi_for_actions(request))


@router.get("/v1/openapi.actions.json", include_in_schema=False)
async def openapi_actions_json_v1(request: Request) -> JSONResponse:
    return JSONResponse(content=_filtered_openapi_for_actions(request))

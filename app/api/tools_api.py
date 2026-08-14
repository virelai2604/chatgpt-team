#app/api/tools_api
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
        "responses_actions": ["/v1/actions/responses/stream"],
        "responses_compact": ["/v1/responses/compact"],
        "embeddings": ["/v1/embeddings"],
        "images": ["/v1/images/generations", "/v1/images/edits", "/v1/images/variations"],
        "images_actions": ["/v1/actions/images/edits", "/v1/actions/images/variations"],
        "files": ["/v1/files", "/v1/files/{file_id}", "/v1/files/{file_id}/content"],
        "files_actions": ["/v1/actions/files/upload"],
        "uploads_actions": [
            "/v1/actions/uploads",
            "/v1/actions/uploads/{upload_id}/parts",
            "/v1/actions/uploads/{upload_id}/complete",
            "/v1/actions/uploads/{upload_id}/cancel",
        ],
        "videos_actions": [
            "/v1/actions/videos",
            "/v1/actions/videos/generations",
            "/v1/actions/videos/{video_id}/remix",
        ],
        "uploads": [
            "/v1/uploads",
            "/v1/uploads/{upload_id}",
            "/v1/uploads/{upload_id}/parts",
            "/v1/uploads/{upload_id}/complete",
            "/v1/uploads/{upload_id}/cancel",
        ],
        "batches": ["/v1/batches", "/v1/batches/{batch_id}", "/v1/batches/{batch_id}/cancel"],
        "proxy": ["/v1/proxy"],
        "realtime_http": ["/v1/realtime/sessions"],
        "realtime_ws": ["/v1/realtime/ws"],
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
            "responses_compact",
            "responses_actions",
            "embeddings",
            "images",
            "images_actions",
            "files_actions",
            "uploads_actions",
            # "videos_actions" is deliberately absent. openai/openai-python@721cb1cd
            # stamps `deprecated: true` on the Sora video paths ahead of a September
            # shutdown, so advertising them to ChatGPT points models at an API with
            # an expiry date. The routes stay served for direct callers until then;
            # they are simply no longer offered as Actions. Re-add this entry only
            # if OpenAI reverses the deprecation.
            "proxy",
            # "realtime_http" is deliberately absent too, for a harder reason than
            # the videos one: POST /v1/realtime/sessions returns 404 from OpenAI.
            # Verified live on 2026-08-14 --
            #   Realtime session upstream error: status=404
            #   url=https://api.openai.com/v1/realtime/sessions
            # -- so advertising it handed ChatGPT a URL that cannot work. The route
            # is still served, and the relay relays the 404 faithfully; it is only
            # no longer offered as an Action.
            #
            # ChatGPT could not have used the realtime surface anyway: Actions are
            # request/response and cannot open a WebSocket, so a session minted
            # through the relay has no consumer inside a Custom GPT.
            #
            # Before re-adding, confirm against OpenAI's spec which endpoint mints
            # ephemeral tokens today -- /realtime/client_secrets exists and is
            # documented for exactly that purpose.
        ],
    }

    # Provide both "old" and "new" shapes for compatibility:
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
    filtered["paths"] = {
        p: spec for p, spec in (full.get("paths") or {}).items() if p in allowed_paths
    }

    info = filtered.get("info") or {}
    title = str(info.get("title") or "OpenAPI")
    info["title"] = f"{title} (Actions subset)"
    filtered["info"] = info

    # FastAPI emits no `servers`, and ChatGPT Actions cannot dispatch a request
    # without one. Derive it from the inbound request so the document is correct
    # on whichever domain served it (ai.lafiel.me or the onrender.com subdomain)
    # rather than hardcoding one and being wrong on the other.
    filtered["servers"] = [{"url": str(request.base_url).rstrip("/")}]

    return JSONResponse(filtered)

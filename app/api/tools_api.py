from __future__ import annotations

from fastapi import APIRouter
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.utils.logger import relay_log as logger

router = APIRouter(tags=["tools"], include_in_schema=False)

settings = get_settings()


def _safe_upstream_base_url() -> str:
    """
    Return the effective upstream base URL used by the relay.

    Some forks used `UPSTREAM_BASE_URL`; the canonical setting in this repo is
    `OPENAI_API_BASE`. Use getattr() to prevent import-time crashes.
    """
    return (
        getattr(settings, "UPSTREAM_BASE_URL", None)
        or getattr(settings, "OPENAI_API_BASE", None)
        or "https://api.openai.com/v1"
    )


tool_manifest = {
    "object": "tools.manifest",
    "data": [
        {
            "name": "chatgpt-team-relay",
            "description": "Local relay that proxies a safe subset of /v1 endpoints to OpenAI.",
            "environment": getattr(settings, "environment", "unknown"),
            "default_model": getattr(settings, "default_model", None),
            "upstream_base_url": _safe_upstream_base_url(),
        }
    ],
    "endpoints": {
        # Local
        "health": ["/", "/health", "/v1/health"],
        "manifest": ["/manifest"],
        # Action-safe (JSON request/response)
        "models": ["/v1/models", "/v1/models/{id}"],
        "responses": ["/v1/responses"],
        "responses_compact": ["/v1/responses/compact"],
        "embeddings": ["/v1/embeddings"],
        # Images: relay supports BOTH multipart (normal clients) and JSON wrapper (Actions) for edits/variations
        "images": [
            "/v1/images",
            "/v1/images/generations",
            "/v1/images/edits",
            "/v1/images/variations",
        ],
        # Generic proxy (relay-only; typically exclude from Actions schema)
        "proxy": ["/v1/proxy/{path:path}"],
    },
    "meta": {
        "openai_api_base": getattr(settings, "OPENAI_API_BASE", None),
        "proxy_allow_prefixes": list(getattr(settings, "proxy_allow_prefixes", [])),
        "proxy_block_prefixes": list(getattr(settings, "proxy_block_prefixes", [])),
        "blocked_v1_prefixes": [
            # Multipart/binary/WS families should not be used from Actions directly.
            "/v1/realtime",
            "/v1/uploads",
            "/v1/files",
            "/v1/audio",
            "/v1/images/edits",
            "/v1/images/variations",
        ],
        "actions_constraints": {
            # Informational (see OpenAI Actions production notes)
            "custom_headers_supported": False,
            "requests_responses_text_only": True,
        },
    },
}


@router.get("/manifest", summary="Relay tools manifest", include_in_schema=False)
async def manifest() -> JSONResponse:
    logger.info("→ [tools] /manifest")
    return JSONResponse(
        {
            "object": tool_manifest["object"],
            "data": tool_manifest["data"],
            "endpoints": tool_manifest["endpoints"],
            "meta": tool_manifest["meta"],
        }
    )

# app/routes/actions.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger  # matches other route families
from app.core.config import get_settings

router = APIRouter(
    prefix="/v1",
    tags=["actions"],
)


def _settings_snapshot() -> Dict[str, Any]:
    """
    Small helper to safely expose a subset of settings for debug endpoints.

    We use getattr(...) with defaults so this stays robust even if your
    Settings class evolves.
    """
    settings = get_settings()
    return {
        "project_name": getattr(settings, "project_name", None),
        "environment": getattr(settings, "environment", None),
        "default_model": getattr(settings, "default_model", None),
        "openai_base_url": getattr(settings, "openai_base_url", None),
        "openai_organization": getattr(settings, "openai_organization", None),
        "relay_version": getattr(settings, "relay_version", None),
    }


# ---------------------------------------------------------------------------
# Local relay debug/info endpoints
# ---------------------------------------------------------------------------


@router.get("/actions/ping")
async def actions_ping() -> Dict[str, Any]:
    """
    Lightweight relay health check, scoped to the Actions subsystem.

    This is **local only** (no upstream OpenAI call) so tests can assert it
    without needing a valid OPENAI_API_KEY.
    """
    snapshot = _settings_snapshot()
    logger.debug("Handling /v1/actions/ping with settings: %s", snapshot)

    return {
        "object": "relay_action_ping",
        "status": "ok",
        "relay": {
            "project_name": snapshot["project_name"],
            "environment": snapshot["environment"],
        },
        "upstream": {
            "base_url": snapshot["openai_base_url"],
            "organization": snapshot["openai_organization"],
        },
    }


@router.get("/actions/relay_info")
async def actions_relay_info() -> Dict[str, Any]:
    """
    Returns a small introspection blob about the relay + upstream config.

    Useful for debugging and for the tests in `tests/test_tools_and_actions_routes.py`.
    """
    snapshot = _settings_snapshot()
    logger.debug("Handling /v1/actions/relay_info with settings: %s", snapshot)

    return {
        "object": "relay_info",
        "relay": {
            "project_name": snapshot["project_name"],
            "environment": snapshot["environment"],
            "version": snapshot["relay_version"],
        },
        "upstream": {
            "base_url": snapshot["openai_base_url"],
            "organization": snapshot["openai_organization"],
            "default_model": snapshot["default_model"],
        },
    }


# ---------------------------------------------------------------------------
# Pass‑through proxy for OpenAI Actions (/v1/actions/*)
# ---------------------------------------------------------------------------


@router.api_route(
    "/actions",
    methods=["GET", "POST", "HEAD", "OPTIONS"],
)
async def actions_root(request: Request) -> Response:
    """
    Generic proxy for the root Actions endpoint: /v1/actions

    This forwards the incoming request to OpenAI using forward_openai_request,
    preserving method, query params, headers, and body.
    """
    logger.info(
        "Proxying %s %s to OpenAI (actions root)",
        request.method,
        request.url.path,
    )
    return await _proxy_actions(request)


@router.api_route(
    "/actions/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def actions_subpaths(path: str, request: Request) -> Response:
    """
    Generic proxy for all subpaths under /v1/actions/*.

    Examples:
      - /v1/actions/some-action
      - /v1/actions/some-action/invoke
      - /v1/actions/whatever/you/add/later
    """
    logger.info(
        "Proxying %s /v1/actions/%s to OpenAI",
        request.method,
        path,
    )
    return await _proxy_actions(request)


async def _proxy_actions(request: Request) -> Response:
    """
    Shared implementation for the two proxy endpoints above.

    We delegate to forward_openai_request which already knows how to:
      * strip the /v1 prefix from the path
      * build the upstream URL using OPENAI_BASE_URL
      * copy headers/query/body
      * add Authorization / org headers
      * return a fastapi.Response with upstream status/body/headers
    """
    try:
        upstream_response = await forward_openai_request(request)
        logger.debug(
            "Upstream OpenAI /actions response: %s %s",
            upstream_response.status_code,
            getattr(upstream_response, "media_type", None),
        )
        return upstream_response
    except HTTPException:
        # Already a well‑shaped FastAPI error; just re‑raise.
        logger.exception("HTTPException while proxying /v1/actions")
        raise
    except Exception as exc:  # pragma: no cover - safety net
        logger.exception("Unexpected error while proxying /v1/actions", exc_info=exc)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "Unexpected error while forwarding /v1/actions request.",
                    "type": "relay_internal_error",
                    "code": "actions_forward_error",
                }
            },
        ) from exc

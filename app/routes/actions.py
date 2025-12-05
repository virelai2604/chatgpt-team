# app/routes/actions.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger  # keep consistent with other route families

router = APIRouter(
    prefix="/v1",
    tags=["actions"],
)


@router.api_route("/actions", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def actions_root(request: Request) -> Response:
    """
    Root for Actions.

    Examples:
      - GET  /v1/actions   (list actions)
      - POST /v1/actions   (create/define an action)
    """
    logger.info("→ [actions] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/actions/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def actions_subpaths(path: str, request: Request) -> Response:
    """
    Catch‑all for /v1/actions/* subresources.

    This is intentionally generic and will forward things like:
      - /v1/actions/{action_id}
      - /v1/actions/{action_id}/runs
      - /v1/actions/{action_id}/versions/{version_id}
    """
    logger.info("→ [actions/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

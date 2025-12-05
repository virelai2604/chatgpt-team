# app/routes/actions.py

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.api.forward_openai import forward_openai_request
from app.utils.logger import relay_log as logger  # type: ignore[attr-defined]

router = APIRouter(
    prefix="/v1",
    tags=["actions"],
)


@router.api_route("/actions", methods=["GET", "POST", "HEAD", "OPTIONS"])
async def actions_root(request: Request) -> Response:
    """
    Root for the Actions API.

    Typical operations (subject to upstream API evolution):

      - GET  /v1/actions       → list actions
      - POST /v1/actions       → create/register an action
    """
    logger.info("→ [actions] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


@router.api_route(
    "/actions/{path:path}",
    methods=["GET", "POST", "PATCH", "DELETE", "HEAD", "OPTIONS"],
)
async def actions_subpaths(path: str, request: Request) -> Response:
    """
    Catch‑all for /v1/actions/*.

    Examples (aligned with ChatGPT‑style Actions concepts):

      - GET    /v1/actions/{action_id}
      - DELETE /v1/actions/{action_id}
      - POST   /v1/actions/{action_id}/run
      - POST   /v1/actions/{action_id}/test
      - Future /v1/actions/* expansions

    We intentionally do no interpretation here and rely on the upstream API.
    """
    logger.info("→ [actions/*] %s %s", request.method, request.url.path)
    return await forward_openai_request(request)

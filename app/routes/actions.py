# app/routes/actions.py

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Body

from app.api.tools_api import _load_tools_manifest  # reuse manifest loader
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/v1",
    tags=["actions"],
)


def _tools_as_actions() -> List[Dict[str, Any]]:
    """
    Interpret tools from the manifest as generic 'actions'.

    For now we simply surface them 1:1 as actions. You can tighten
    this later once the P4 orchestration story is fully fleshed out.
    """
    tools = _load_tools_manifest()
    actions: List[Dict[str, Any]] = []

    for tool in tools:
        # Pass through as-is but mark the 'kind' to make downstream
        # filtering easier for frontends or agents.
        action = dict(tool)
        action.setdefault("kind", "tool")
        actions.append(action)

    return actions


@router.get("/tools/actions")
async def list_actions() -> Dict[str, Any]:
    """
    GET /v1/tools/actions – list all configured actions.

    Currently this is a thin wrapper around the tools manifest, returned
    as an OpenAI-style list object.
    """
    actions = _tools_as_actions()
    logger.info("Listing %d actions from tools manifest", len(actions))
    return {"object": "list", "data": actions}


@router.post("/tools/actions/call")
async def call_action(
    payload: Dict[str, Any] = Body(..., description="Minimal action invocation payload"),
) -> Dict[str, Any]:
    """
    POST /v1/tools/actions/call – minimal echo-style action call.

    This is intentionally conservative: it does not perform any external
    side effects. It's useful for tests, demos, or as a shim that you can
    later swap out for true P4 orchestration.
    """
    action_id = payload.get("id") or payload.get("name")
    logger.info("Received tools/actions.call for action_id=%s", action_id)

    return {
        "object": "action.call",
        "status": "ok",
        "id": action_id,
        "input": payload.get("input"),
        "meta": {
            "message": "Action call handled by relay stub; no external side effects.",
        },
    }

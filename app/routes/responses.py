# app/routes/responses.py
"""
BIFL v2.1 – Unified Responses Endpoint
Now defaults to sora-2-pro model unless overridden in request.
Handles both streaming passthrough and non-stream (tool-loop) logic.
"""

import os, json
import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.api.forward import forward_openai
from app.routes.services.tool_registry import collect_tool_results

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "sora-2-pro")

router = APIRouter(tags=["core"])

OPENAI_BASE = "https://api.openai.com"
MAX_TOOL_ROUNDS = 3  # limit re-entry to avoid loops

# ----------------------------------------------------------------------
# Helper: Authentication headers
# ----------------------------------------------------------------------
def _auth_headers() -> dict:
    h = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENAI_ORG_ID:
        h["OpenAI-Organization"] = OPENAI_ORG_ID
    return h


# ----------------------------------------------------------------------
# /v1/responses → main unified interface
# ----------------------------------------------------------------------
@router.post("/v1/responses")
async def create_response(request: Request):
    """
    Handle response creation:
    - If 'stream' is True → SSE passthrough to OpenAI
    - Else → run local tool-loop for function_call handling
    - Defaults to sora-2-pro if model unspecified
    """
    body = await request.json()

    # Default model fallback
    if "model" not in body or not body["model"]:
        body["model"] = DEFAULT_MODEL

    # Streaming passthrough
    if body.get("stream") is True:
        return await forward_openai(request, "/v1/responses")

    # Non-stream: execute locally with tool-loop
    headers = _auth_headers()
    async with httpx.AsyncClient(timeout=None) as client:
        # Initial request
        r = await client.post(f"{OPENAI_BASE}/v1/responses", headers=headers, json=body)
        try:
            data = r.json()
        except Exception:
            return Response(
                content=r.content,
                status_code=r.status_code,
                media_type=r.headers.get("content-type"),
            )

        rounds = 0
        while rounds < MAX_TOOL_ROUNDS:
            tool_results = await collect_tool_results(data)
            if not tool_results:
                break
            follow_up = {
                "model": body["model"],
                "previous_response_id": data["id"],
                "input": tool_results,
            }
            r2 = await client.post(
                f"{OPENAI_BASE}/v1/responses", headers=headers, json=follow_up
            )
            data = r2.json()
            rounds += 1

        # Final model output
        return JSONResponse(content=data, status_code=r.status_code)


# ----------------------------------------------------------------------
# Secondary Routes (passthrough)
# ----------------------------------------------------------------------
@router.get("/v1/responses/{response_id}")
async def get_response(request: Request, response_id: str):
    """Retrieve a response by ID."""
    return await forward_openai(request, f"/v1/responses/{response_id}")


@router.delete("/v1/responses/{response_id}")
async def delete_response(request: Request, response_id: str):
    """Delete a response."""
    return await forward_openai(request, f"/v1/responses/{response_id}")


@router.post("/v1/responses/{response_id}/cancel")
async def cancel_response(request: Request, response_id: str):
    """Cancel an in-progress response."""
    return await forward_openai(request, f"/v1/responses/{response_id}/cancel")


@router.get("/v1/responses/{response_id}/input_items")
async def list_input_items(request: Request, response_id: str):
    """List all input items linked to a response."""
    return await forward_openai(request, f"/v1/responses/{response_id}/input_items")

# ==========================================================
# app/routes/responses.py — Ground Truth Edition (2025.10)
# ==========================================================
"""
Implements /v1/responses endpoint with full support for:
  - Non-streaming JSON completions
  - Streaming responses (SSE)
  - Chain wait mode (controlled by CHAIN_WAIT_MODE)
Fully compatible with OpenAI’s 2025.10 spec.
"""

import os
import httpx
import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from app.api.forward_openai import OPENAI_API_KEY, OPENAI_BASE_URL

router = APIRouter(tags=["Responses"])

CHAIN_WAIT_MODE = os.getenv("CHAIN_WAIT_MODE", "false").lower() == "true"


# ----------------------------------------------------------
# POST /v1/responses — create response (non-streaming or stream)
# ----------------------------------------------------------
@router.post("/v1/responses")
async def create_response(request: Request):
    """
    Mirrors OpenAI’s /v1/responses endpoint.
    Supports both streaming and standard completions.
    """
    body = await request.json()
    stream = bool(body.get("stream", False))
    url = f"{OPENAI_BASE_URL}/v1/responses"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:

            # STREAMING MODE
            if stream:
                async with client.stream("POST", url, json=body, headers=headers) as upstream:
                    if upstream.status_code != 200:
                        err_body = await upstream.aread()
                        raise HTTPException(
                            status_code=upstream.status_code,
                            detail=err_body.decode()
                        )

                    # Relay upstream SSE stream
                    return StreamingResponse(
                        upstream.aiter_text(),
                        media_type="text/event-stream"
                    )

            # NON-STREAMING MODE
            response = await client.post(url, json=body, headers=headers)
            if response.status_code >= 400:
                raise HTTPException(status_code=response.status_code, detail=response.text)

            result = response.json()

            # Optional chain-wait behavior for synchronous relay
            if CHAIN_WAIT_MODE and isinstance(result, dict) and result.get("id"):
                result["chain_wait_mode"] = True

            return JSONResponse(content=result, status_code=response.status_code)

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Upstream request timed out.")
    except Exception as e:
        logging.exception(f"[Relay] Error forwarding /v1/responses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------
# GET /v1/responses/tools — list relay tools
# ----------------------------------------------------------
@router.get("/v1/responses/tools")
async def list_tools():
    """
    Returns the list of registered relay tools (from tools_api).
    This route allows models to enumerate available built-ins
    for function calling or tool invocation.
    """
    try:
        from app.api.tools_api import list_tools as list_registered_tools
        tools = await list_registered_tools()
        return JSONResponse(content={"object": "list", "data": tools}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ----------------------------------------------------------
# POST /v1/responses/tools/{tool_name} — invoke tool
# ----------------------------------------------------------
@router.post("/v1/responses/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """
    Invokes a registered relay tool (mock or live) via the tools_api.
    """
    body = await request.json()
    try:
        from app.api.tools_api import call_tool
        result = await call_tool(tool_name, body)
        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

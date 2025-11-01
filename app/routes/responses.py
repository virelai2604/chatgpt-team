# ==========================================================
# app/routes/responses.py — Unified Responses API (v2025.11)
# ==========================================================
"""
Implements the unified /v1/responses endpoint.

Behavior:
  • Standard model completion & reasoning
  • Inline tool execution (CHAIN_WAIT_MODE)
  • Vector store chaining
  • Streaming passthrough (SSE)
  • SDK-compatible JSON output
  • Automatic fallback to OpenAI API

Aligned with:
  - Ground Truth API Spec (Nov 2025)
  - openai-python SDK v1.51+
"""

import uuid
import json
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.api.forward_openai import forward_openai_request
from app.api.tools_api import execute_tool
from app.routes.vector_stores import VECTOR_STORE_REGISTRY

router = APIRouter(tags=["Responses"])

# ----------------------------------------------------------
# Helper: Local tool execution (CHAIN_WAIT_MODE)
# ----------------------------------------------------------
async def _run_tool_chain(tools: list, model: str):
    """
    Executes a list of tools sequentially in CHAIN_WAIT_MODE.
    Each tool output is added to results and may register a vector.
    """
    results = []
    for tool in tools:
        t_type = tool.get("type")
        params = tool.get("params", {})

        if not t_type:
            raise HTTPException(status_code=400, detail="Tool missing 'type' field")

        try:
            output = await execute_tool(t_type, params)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Tool '{t_type}' failed: {e}")

        # Vector chaining (if tool returns a vector)
        if isinstance(output, dict) and "vector" in output:
            v_id = f"vec_{uuid.uuid4().hex[:8]}"
            VECTOR_STORE_REGISTRY[v_id] = {
                "id": v_id,
                "object": "vector",
                "model": model,
                "vector": output["vector"],
                "metadata": output.get("metadata", {}),
            }
            output["vector_id"] = v_id

        results.append({
            "tool": t_type,
            "status": "completed",
            "output": output,
        })

    return results


# ----------------------------------------------------------
# Helper: Streaming passthrough
# ----------------------------------------------------------
async def _stream_openai_response(body: dict, headers: dict):
    """
    Streams event data from OpenAI API back to the client.

    Each upstream chunk (SSE 'data:' line) is forwarded verbatim,
    preserving real-time behavior for SDK compatibility.
    """
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=body,
        ) as resp:
            if resp.status_code >= 400:
                text = await resp.aread()
                raise HTTPException(
                    status_code=resp.status_code,
                    detail=text.decode(errors="ignore"),
                )

            async for chunk in resp.aiter_text():
                # Forward SSE events line-by-line (no modification)
                yield chunk


# ----------------------------------------------------------
# Endpoint: POST /v1/responses
# ----------------------------------------------------------
@router.post("/responses", summary="Unified Responses API (Models + Tools + Streaming)")
async def create_response(request: Request):
    """
    Unified entrypoint for model reasoning and tool execution.
    Mirrors OpenAI's /v1/responses endpoint behavior.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    model = body.get("model", "gpt-4.1-mini")
    stream = body.get("stream", False)
    tools = body.get("tools", [])
    chain_wait_mode = body.get("chain_wait_mode", True)
    input_text = body.get("input", "")

    # ------------------------------------------------------
    # 1️⃣ Local inline tool execution (CHAIN_WAIT_MODE)
    # ------------------------------------------------------
    if tools and chain_wait_mode:
        outputs = await _run_tool_chain(tools, model)
        return JSONResponse(
            content={
                "id": f"resp_{uuid.uuid4().hex[:8]}",
                "object": "response",
                "model": model,
                "chain_wait_mode": True,
                "input": input_text,
                "outputs": outputs,
                "metadata": {"relay_mode": "local", "version": "2025.11"},
            },
            status_code=200,
        )

    # ------------------------------------------------------
    # 2️⃣ Streaming passthrough to OpenAI (SSE)
    # ------------------------------------------------------
    if stream:
        headers = {
            "Authorization": request.headers.get("Authorization"),
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        return StreamingResponse(
            _stream_openai_response(body, headers),
            media_type="text/event-stream",
        )

    # ------------------------------------------------------
    # 3️⃣ Standard non-streaming passthrough
    # ------------------------------------------------------
    return await forward_openai_request("/v1/responses", body, stream=False)


# ----------------------------------------------------------
# Endpoint: GET /v1/responses/meta (diagnostics)
# ----------------------------------------------------------
@router.get("/responses/meta", summary="Response API metadata")
async def responses_meta():
    """
    Returns metadata about relay status and supported features.
    """
    return JSONResponse(
        content={
            "relay": "ChatGPT Team Relay",
            "supports_tools": True,
            "supports_streaming": True,
            "chain_wait_mode": True,
            "vector_store_count": len(VECTOR_STORE_REGISTRY),
            "sdk_version_target": "1.51+",
            "version": "2025.11",
        },
        status_code=200,
    )

# ==========================================================
# app/routes/responses.py — Ground Truth Edition (Final)
# ==========================================================
"""
Implements the OpenAI Responses API, including:
- POST /v1/responses (stream + non-stream)
- CHAIN_WAIT_MODE (polls until completion)
- /v1/responses/tools list & invocation
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx
import asyncio
import time
import os
import json

router = APIRouter(prefix="/v1/responses", tags=["Responses"])

OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
API_KEY = os.getenv("OPENAI_API_KEY")
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
CHAIN_WAIT = os.getenv("CHAIN_WAIT_MODE", "false").lower() == "true"

TOOLS_MANIFEST = os.getenv("TOOLS_MANIFEST", "app/manifests/tools_manifest.json")

# ==========================================================
# Helper: Poll for response completion
# ==========================================================
async def _poll_until_complete(response_id: str, timeout: int = 60):
    """Poll /v1/responses/{id} until completed or timeout."""
    async with httpx.AsyncClient(timeout=None) as client:
        start = time.time()
        while time.time() - start < timeout:
            r = await client.get(f"{OPENAI_BASE}/v1/responses/{response_id}", headers=HEADERS)
            try:
                j = r.json()
            except Exception:
                await asyncio.sleep(0.5)
                continue
            if "completed" in r.text or j.get("status") == "completed" or j.get("output"):
                return j
            await asyncio.sleep(0.5)
        return {"id": response_id, "status": "timeout", "message": "Chain wait exceeded"}

# ==========================================================
# POST /v1/responses
# ==========================================================
@router.post("")
async def create_response(request: Request):
    body = await request.json()
    stream_mode = bool(body.get("stream", False))

    # Non-stream mode
    if not stream_mode:
        async with httpx.AsyncClient(timeout=None) as client:
            r = await client.post(f"{OPENAI_BASE}/v1/responses", headers=HEADERS, json=body)
            if not CHAIN_WAIT:
                return JSONResponse(r.json(), status_code=r.status_code)
            j = r.json()
            rid = j.get("id")
            if not rid:
                return JSONResponse(j, status_code=r.status_code)
            result = await _poll_until_complete(rid)
            result["chain_wait"] = True
            return JSONResponse(result, status_code=200)

    # Stream mode
    async def event_stream():
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", f"{OPENAI_BASE}/v1/responses", headers=HEADERS, json=body) as r:
                async for chunk in r.aiter_bytes():
                    yield chunk

    return StreamingResponse(event_stream(), media_type="text/event-stream")

# ==========================================================
# GET /v1/responses/{id}
# ==========================================================
@router.get("/{response_id}")
async def get_response(response_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{OPENAI_BASE}/v1/responses/{response_id}", headers=HEADERS)
    return JSONResponse(r.json(), status_code=r.status_code)

# ==========================================================
# DELETE /v1/responses/{id}
# ==========================================================
@router.delete("/{response_id}")
async def delete_response(response_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{OPENAI_BASE}/v1/responses/{response_id}", headers=HEADERS)
    return JSONResponse(r.json(), status_code=r.status_code)

# ==========================================================
# POST /v1/responses/{id}/cancel
# ==========================================================
@router.post("/{response_id}/cancel")
async def cancel_response(response_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{OPENAI_BASE}/v1/responses/{response_id}/cancel", headers=HEADERS)
    return JSONResponse(r.json(), status_code=r.status_code)

# ==========================================================
# GET /v1/responses/tools
# ==========================================================
@router.get("/tools")
async def list_tools():
    """Return a Ground Truth–formatted list of available tools."""
    tools = []
    if os.path.exists(TOOLS_MANIFEST):
        try:
            with open(TOOLS_MANIFEST, "r") as f:
                manifest = json.load(f)
                for name in manifest.get("registry", []):
                    tools.append({
                        "id": name,
                        "name": name,
                        "type": "function",
                        "description": f"Tool for {name.replace('_', ' ')}."
                    })
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Invalid tools manifest: {e}")

    if not tools:
        tools = [
            {"id": "code_interpreter", "name": "code_interpreter", "type": "function", "description": "Executes Python code."},
            {"id": "file_search", "name": "file_search", "type": "function", "description": "Searches uploaded files."},
        ]

    return JSONResponse({"object": "list", "data": tools})

# ==========================================================
# POST /v1/responses/tools/{tool_name}
# ==========================================================
@router.post("/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """Invoke a specific tool (local simulation or upstream passthrough)."""
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    # Local tool simulation
    if tool_name == "code_interpreter":
        code = payload.get("code", "")
        return {
            "object": "tool_call",
            "id": f"local_tool_{tool_name}",
            "status": "succeeded",
            "output": f"Executed code: {code}"
        }

    if tool_name == "file_search":
        query = payload.get("query", "")
        return {
            "object": "tool_call",
            "id": f"local_tool_{tool_name}",
            "status": "succeeded",
            "output": f"Search results for query: '{query}'"
        }

    # Forward to upstream if not local
    async with httpx.AsyncClient(timeout=None) as client:
        r = await client.post(f"{OPENAI_BASE}/v1/responses/tools/{tool_name}", headers=HEADERS, json=payload)
    if r.status_code == 404:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found upstream")
    return JSONResponse(r.json(), status_code=r.status_code)

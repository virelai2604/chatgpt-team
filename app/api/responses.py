# ==========================================================
# responses.py — Ground-Truth /v1/responses relay endpoint
# Fully aligned with OpenAI Relay schema (as of Oct 2025)
# ==========================================================
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
import httpx, os, json

router = APIRouter()

# ----------------------------------------------------------
# Environment
# ----------------------------------------------------------
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL   = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")

# ----------------------------------------------------------
# Request Models (mirror OpenAI spec)
# ----------------------------------------------------------
class ResponseContent(BaseModel):
    type: str
    text: str

class ResponseMessage(BaseModel):
    role: str
    content: List[ResponseContent]

class ResponseRequest(BaseModel):
    model: str = Field(default=DEFAULT_MODEL)
    input: List[ResponseMessage]
    response: Optional[Dict[str, Any]] = None
    stream: Optional[bool] = False
    tools: Optional[List[Dict[str, Any]]] = None

# ----------------------------------------------------------
# Input normalization — ensures schema fidelity
# ----------------------------------------------------------
def normalize_request(body: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize older/legacy formats to ground-truth /v1/responses."""
    # 1. Legacy `type: text` → `input_text`
    for msg in body.get("input", []):
        for item in msg.get("content", []):
            if item.get("type") == "text":
                item["type"] = "input_text"

    # 2. Legacy `response_format` → `response.format`
    if "response_format" in body:
        fmt = body.pop("response_format")
        body["response"] = {"format": fmt}

    # 3. Normalize tool schema
    if "tools" in body and isinstance(body["tools"], list):
        normalized = []
        for t in body["tools"]:
            if isinstance(t, dict) and "name" in t:
                normalized.append({"type": "function",
                                   "function": {"name": t["name"]}})
        body["tools"] = normalized
    return body

# ----------------------------------------------------------
# POST /v1/responses — JSON + SSE streaming
# ----------------------------------------------------------
@router.post("/v1/responses")
async def create_response(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    body = normalize_request(body)
    if "model" not in body or "input" not in body:
        raise HTTPException(status_code=400,
                            detail="Missing 'model' or 'input'")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"{OPENAI_BASE_URL}/v1/responses"
    stream = body.get("stream", False)

    async with httpx.AsyncClient(timeout=None) as client:
        if stream:
            async def sse_events():
                async with client.stream("POST", url, headers=headers, json=body) as resp:
                    async for line in resp.aiter_lines():
                        if line.strip():
                            yield f"data: {line}\n\n"
            return StreamingResponse(sse_events(), media_type="text/event-stream")

        resp = await client.post(url, headers=headers, json=body)
        return JSONResponse(content=resp.json() if resp.content else {"error": "Empty response"},
                            status_code=resp.status_code)

# ----------------------------------------------------------
# GET /v1/responses/tools — bridge to tool registry
# ----------------------------------------------------------
@router.get("/v1/responses/tools")
async def get_tools():
    from app.api.tools_api import list_tools
    return {"tools": list_tools()}

# ----------------------------------------------------------
# Health and model passthrough
# ----------------------------------------------------------
@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/v1/models")
async def list_models():
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{OPENAI_BASE_URL}/v1/models", headers=headers)
    return JSONResponse(content=resp.json(), status_code=resp.status_code)

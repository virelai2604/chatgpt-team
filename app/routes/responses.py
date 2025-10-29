# ==========================================================
# app/routes/responses.py — Ground Truth OpenAI-Compatible Mirror
# ==========================================================
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.api.forward_openai import forward_openai_request
from app.api.tools_api import list_tools, call_tool
import pprint
import httpx

router = APIRouter(prefix="/v1/responses", tags=["Responses"])

# ==========================================================
# POST /v1/responses  →  Create model response (stream / non-stream)
# ==========================================================
@router.post("")
async def create_response(request: Request):
    """
    Mirrors OpenAI POST /v1/responses
    Generates model output. Supports streaming (SSE) and standard JSON.
    """
    print("\n>>> [DEBUG] Incoming /v1/responses request")

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    pprint.pprint(body)
    is_stream = bool(body.get("stream", False))
    print(f"[DEBUG] Stream mode: {is_stream}")

    try:
        result = await forward_openai_request(
            endpoint="v1/responses",
            method="POST",
            json_data=body,
            stream=is_stream,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    if is_stream:
        print("[DEBUG] Returning streaming response")
        return StreamingResponse(result, media_type="text/event-stream")

    print("[DEBUG] Returning non-stream JSON response")
    return JSONResponse(result)

# ==========================================================
# POST /v1/responses/input_tokens  →  Token counting
# ==========================================================
@router.post("/input_tokens")
async def count_input_tokens(request: Request):
    """
    Mirrors OpenAI POST /v1/responses/input_tokens
    Returns token usage count for a given model + input.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    result = await forward_openai_request(
        "v1/responses/input_tokens",
        method="POST",
        json_data=body,
    )
    return JSONResponse(result)

# ==========================================================
# GET /v1/responses/tools  →  Tool registry
# ==========================================================
@router.get("/tools")
async def get_tools():
    """
    Mirrors OpenAI GET /v1/responses/tools
    Returns all registered relay tools in OpenAI-compatible format.
    """
    tools = await list_tools()
    return JSONResponse({"tools": tools})

# ==========================================================
# POST /v1/responses/tools/{tool_name}  →  Manual tool invocation
# ==========================================================
@router.post("/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """
    Mirrors OpenAI POST /v1/responses/tools/{tool_name}
    Allows manual execution of a registered tool for debugging or testing.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_json")

    result = await call_tool(tool_name, body)
    return JSONResponse({"tool_name": tool_name, "result": result})

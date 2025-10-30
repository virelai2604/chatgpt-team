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
# POST /v1/responses → Create model response (stream / non-stream)
# ==========================================================
@router.post("")
async def create_response(request: Request):
    """
    Mirrors OpenAI POST /v1/responses
    Supports both standard and Server-Sent Event (stream) responses.
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    is_stream = bool(body.get("stream", False))
    pprint.pprint({"stream": is_stream, "body": body})

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
        return StreamingResponse(result, media_type="text/event-stream; charset=utf-8")

    return JSONResponse(result)


# ==========================================================
# POST /v1/responses/input_tokens → Token counting
# ==========================================================
@router.post("/input_tokens")
async def count_input_tokens(request: Request):
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
# GET /v1/responses/tools → Tool registry
# ==========================================================
@router.get("/tools")
async def get_tools():
    tools = await list_tools()
    return JSONResponse({"tools": tools})


# ==========================================================
# POST /v1/responses/tools/{tool_name} → Manual tool invocation
# ==========================================================
@router.post("/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_json")

    result = await call_tool(tool_name, body)
    return JSONResponse({"tool_name": tool_name, "result": result})

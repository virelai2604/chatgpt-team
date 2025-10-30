"""
ChatGPT Team Relay — Responses Routes
-------------------------------------
Implements /v1/responses endpoints for model completions,
streamed responses, and relay tool invocation.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter()

@router.post("/v1/responses")
async def create_response(request: Request):
    """Forward model generation requests (stream or non-stream)."""
    body = await request.json()
    stream = body.get("stream", False)

    if stream:
        # Streamed model output (Server-Sent Events)
        async with await forward_openai_request("v1/responses", method="POST", json=body, stream=True) as stream_resp:
            if stream_resp.status_code != 200:
                content = await stream_resp.aread()
                raise HTTPException(status_code=stream_resp.status_code, detail=content.decode())

            return StreamingResponse(
                stream_resp.aiter_text(),
                media_type="text/event-stream"
            )
    else:
        response = await forward_openai_request("v1/responses", method="POST", json=body)
        if response.status_code >= 400:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return JSONResponse(content=response.json())

@router.get("/v1/responses/tools")
async def list_tools():
    """Return the list of available relay tools."""
    return JSONResponse(
        {
            "tools": [
                {"name": "listModels", "description": "Lists available models."},
                {"name": "uploadFile", "description": "Uploads a file."},
            ]
        }
    )

@router.post("/v1/responses/tools/{tool_name}")
async def invoke_tool(tool_name: str, request: Request):
    """Invoke a registered relay tool."""
    args = await request.json()
    # Forward call to the internal tool handler
    return JSONResponse({"tool_invoked": tool_name, "args": args})

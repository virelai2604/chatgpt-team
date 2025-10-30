# ==========================================================
# app/api/passthrough_proxy.py — Ground Truth Edition (Final)
# ==========================================================
"""
Fallback proxy that captures any unhandled OpenAI-style route
and forwards it using forward_openai.py.
Provides transparent compatibility with new or unknown endpoints.
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from .forward_openai import forward_openai_request

router = APIRouter(prefix="/v1", tags=["Passthrough Proxy"])


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough(request: Request, path: str):
    """
    Forward any unhandled /v1/* request to OpenAI.
    Automatically preserves HTTP method, body, and headers.
    """
    method = request.method
    content_type = request.headers.get("content-type", "")
    body = None
    files = None
    data = None

    try:
        if "multipart/form-data" in content_type:
            form = await request.form()
            files = {
                k: (v.filename, await v.read(), v.content_type)
                for k, v in form.items()
                if hasattr(v, "filename")
            }
            data = {k: v for k, v in form.items() if not hasattr(v, "filename")}
        elif "application/json" in content_type:
            body = await request.json()
        else:
            raw = await request.body()
            body = raw.decode("utf-8") if raw else None
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {e}")

    # Determine if streaming
    is_stream = "text/event-stream" in request.headers.get("accept", "")

    result = await forward_openai_request(
        path=path,
        method=method,
        json=body if isinstance(body,

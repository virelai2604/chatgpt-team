# ==========================================================
# passthrough.py — Universal OpenAI Proxy Passthrough Routes
# ==========================================================
"""
Handles generic passthrough for any OpenAI API path not explicitly
covered by other routes.

Examples:
  GET    /v1/models
  POST   /v1/responses
  PUT    /v1/some/unknown/path
  PATCH  /v1/files/metadata
  DELETE /v1/vector_stores/test
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.api.forward_openai import forward_openai_request
import logging

logger = logging.getLogger("forwarder")

router = APIRouter(prefix="/v1", tags=["Passthrough"])


# ==========================================================
# Core passthrough handler
# ==========================================================

async def _handle_passthrough(request: Request, path: str, method: str):
    """
    Shared passthrough logic for all HTTP verbs.
    Supports both normal and stream-based responses.
    """
    try:
        # Read JSON body if present
        if request.headers.get("content-type", "").startswith("application/json"):
            body = await request.json()
        else:
            body = None

        # Stream mode if explicitly requested
        stream = bool(body and body.get("stream"))

        # Forward to OpenAI
        result = await forward_openai_request(
            f"v1/{path}",
            method=method,
            json_data=body,
            stream=stream,
        )

        # Streamed responses
        if stream and hasattr(result, "__aiter__"):
            return StreamingResponse(result, media_type="text/event-stream")

        # Standard JSON responses
        if isinstance(result, dict) and "status_code" in result and "error" in result:
            # Internal error passthrough
            return JSONResponse(content=result, status_code=result.get("status_code", 500))
        return JSONResponse(content=result)

    except Exception as e:
        logger.exception(f"[Passthrough] Unexpected error handling {method} {path}: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ==========================================================
# REST Method Endpoints
# ==========================================================

@router.get("/{path:path}")
async def passthrough_get(request: Request, path: str):
    return await _handle_passthrough(request, path, "GET")


@router.post("/{path:path}")
async def passthrough_post(request: Request, path: str):
    return await _handle_passthrough(request, path, "POST")


@router.put("/{path:path}")
async def passthrough_put(request: Request, path: str):
    return await _handle_passthrough(request, path, "PUT")


@router.patch("/{path:path}")
async def passthrough_patch(request: Request, path: str):
    return await _handle_passthrough(request, path, "PATCH")


@router.delete("/{path:path}")
async def passthrough_delete(request: Request, path: str):
    return await _handle_passthrough(request, path, "DELETE")

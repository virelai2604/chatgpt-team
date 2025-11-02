# ================================================================
# responses.py — /v1/responses passthrough and local testing stub
# ================================================================
# Implements OpenAI-compatible responses endpoints for use with
# the ChatGPT Team Relay. Supports both passthrough and mock
# response generation for offline/local testing.
#
# This module defines two routers:
#   - router: the main /v1/responses implementation
#   - responses_router: alias for /responses (legacy SDK compatibility)
# ================================================================

import time
import uuid
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.api.forward_openai import forward_to_openai

# ================================================================
# Routers
# ================================================================
router = APIRouter(prefix="/v1/responses", tags=["responses"])
responses_router = APIRouter(prefix="/responses", tags=["responses (legacy)"])

# ================================================================
# Core Endpoint: POST /v1/responses
# ================================================================
@router.post("")
async def create_response(request: Request):
    """
    Forwards response creation requests to OpenAI’s /v1/responses.
    If OpenAI is unreachable, returns a local mock response object.
    """
    try:
        resp = await forward_to_openai(request, "/v1/responses")

        # Streamed responses (SSE)
        content_type = resp.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            async def stream_generator():
                async for chunk in resp.aiter_bytes():
                    yield chunk
            return StreamingResponse(stream_generator(), media_type="text/event-stream")

        # Normal JSON
        return JSONResponse(resp.json(), status_code=resp.status_code)

    except Exception as e:
        # Local fallback for offline testing
        mock_id = f"resp_{uuid.uuid4().hex[:8]}"
        return JSONResponse({
            "id": mock_id,
            "object": "response",
            "created": int(time.time()),
            "model": "gpt-4o-mini",
            "output": [{"type": "message", "content": [{"type": "text", "text": f"[offline mock] {e}"}]}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
        }, status_code=200)

# ================================================================
# GET /v1/responses/{response_id}
# ================================================================
@router.get("/{response_id}")
async def get_response(response_id: str, request: Request):
    """Retrieves a response by ID (proxied to OpenAI)."""
    resp = await forward_to_openai(request, f"/v1/responses/{response_id}")
    return JSONResponse(resp.json(), status_code=resp.status_code)

# ================================================================
# DELETE /v1/responses/{response_id}
# ================================================================
@router.delete("/{response_id}")
async def delete_response(response_id: str, request: Request):
    """Deletes a response by ID (proxied to OpenAI)."""
    resp = await forward_to_openai(request, f"/v1/responses/{response_id}")
    return JSONResponse(resp.json(), status_code=resp.status_code)

# ================================================================
# Legacy Aliases — /responses (SDK backward compatibility)
# ================================================================
@responses_router.post("")
async def create_response_legacy(request: Request):
    """Alias for POST /v1/responses"""
    return await create_response(request)

@responses_router.get("/{response_id}")
async def get_response_legacy(response_id: str, request: Request):
    """Alias for GET /v1/responses/{response_id}"""
    return await get_response(response_id, request)

@responses_router.delete("/{response_id}")
async def delete_response_legacy(response_id: str, request: Request):
    """Alias for DELETE /v1/responses/{response_id}"""
    return await delete_response(response_id, request)

# ================================================================
# No function calls here!
# ================================================================
# ⚠️ DO NOT call register_routes(app) in this file.
# Route registration happens only once, in main.py, through:
#     from app.routes.register_routes import register_routes
#     register_routes(app)
# ================================================================

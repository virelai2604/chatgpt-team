# ==========================================================
# app/api/passthrough_proxy.py — Ground Truth Edition
# ==========================================================
"""
Fallback proxy for any unmatched /v1/* routes.
Passes through arbitrary requests to OpenAI’s upstream API.
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1", tags=["Passthrough"])

# ----------------------------------------------------------
# Internal handler
# ----------------------------------------------------------
async def _handle(request: Request, path: str, method: str):
    try:
        # Parse JSON if possible, otherwise skip
        body = None
        if request.headers.get("content-type", "").startswith("application/json"):
            body = await request.json()
    except Exception:
        body = None

    # Forward the request
    return await forward_openai_request(f"v1/{path}", method=method, json=body)

# ----------------------------------------------------------
# Route definitions (matches OpenAI HTTP verbs)
# ----------------------------------------------------------
@router.get("/{path:path}")
async def passthrough_get(request: Request, path: str):
    """Fallback GET passthrough"""
    return await _handle(request, path, "GET")

@router.post("/{path:path}")
async def passthrough_post(request: Request, path: str):
    """Fallback POST passthrough"""
    return await _handle(request, path, "POST")

@router.put("/{path:path}")
async def passthrough_put(request: Request, path: str):
    """Fallback PUT passthrough"""
    return await _handle(request, path, "PUT")

@router.patch("/{path:path}")
async def passthrough_patch(request: Request, path: str):
    """Fallback PATCH passthrough"""
    return await _handle(request, path, "PATCH")

@router.delete("/{path:path}")
async def passthrough_delete(request: Request, path: str):
    """Fallback DELETE passthrough"""
    return await _handle(request, path, "DELETE")

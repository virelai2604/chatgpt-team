# ================================================================
# passthrough_proxy.py — Universal catch-all proxy to OpenAI
# ================================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_to_openai
import httpx

router = APIRouter(tags=["passthrough"])

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough(path: str, request: Request):
    """Forward any unrecognized /v1/* path directly to OpenAI."""
    resp = await forward_to_openai(request, f"/{path}")

    # --- Handle FastAPI vs HTTPX responses safely ---
    if isinstance(resp, JSONResponse):
        # forward_to_openai() already handled it (e.g., error JSON)
        return resp

    if isinstance(resp, httpx.Response):
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            return JSONResponse({
                "object": "passthrough",
                "status": resp.status_code,
                "body": resp.text[:1000]  # safe truncate
            }, status_code=resp.status_code)

    # Unexpected fallback
    return JSONResponse({
        "object": "error",
        "message": "Unexpected response type from forward_to_openai.",
        "type": str(type(resp))
    }, status_code=500)

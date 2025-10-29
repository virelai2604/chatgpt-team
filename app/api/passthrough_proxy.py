# ==========================================================
# app/api/passthrough_proxy.py — Universal Fallback Proxy
# ==========================================================
# Forwards any unmatched /v1/* request to the official OpenAI API.
# Always registered LAST to avoid intercepting local endpoints.
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai

router = APIRouter(prefix="/v1", tags=["Passthrough"])

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough(request: Request, path: str):
    """Universal fallback proxy that forwards any unmatched /v1/* route."""
    endpoint = f"/v1/{path}"
    return await forward_openai(request, endpoint)

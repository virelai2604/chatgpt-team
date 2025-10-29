# ==========================================================
# app/api/passthrough_proxy.py — Universal Fallback Proxy
# ==========================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1", tags=["Passthrough"])

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough(request: Request, path: str):
    """
    Universal fallback proxy that forwards any unhandled /v1/* route to OpenAI.
    Ensures compatibility with all future endpoints.
    """
    method = request.method
    body = None
    if method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except Exception:
            body = None

    endpoint = f"v1/{path}"
    result = await forward_openai_request(endpoint, method=method, json_data=body)
    return JSONResponse(result)

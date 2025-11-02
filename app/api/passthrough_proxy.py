# ================================================================
# passthrough_proxy.py — Universal /v1/* Proxy
# ================================================================
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_to_openai
import httpx

router = APIRouter(tags=["passthrough"])

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough(path: str, request: Request):
    """Forward any unknown /v1/* endpoint to OpenAI, SDK-aligned."""
    result = await forward_to_openai(request, f"/{path}")

    # FastAPI JSONResponse returned → already ready
    if isinstance(result, JSONResponse):
        return result

    # Raw httpx.Response returned (shouldn’t happen, but guard anyway)
    if isinstance(result, httpx.Response):
        ctype = result.headers.get("content-type", "")
        if ctype.startswith("application/json"):
            try:
                return JSONResponse(result.json(), status_code=result.status_code)
            except Exception:
                pass
        return JSONResponse(
            {
                "object": "passthrough",
                "status": result.status_code,
                "content_type": ctype,
                "body": getattr(result, "text", "")[:1000],
            },
            status_code=result.status_code,
        )

    # Unexpected type
    return JSONResponse(
        {
            "error": {
                "message": f"Unexpected passthrough type: {type(result)}",
                "type": "relay_error",
                "param": None,
                "code": "unexpected_response_type"
            }
        },
        status_code=500,
    )

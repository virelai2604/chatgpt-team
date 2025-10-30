# ==========================================================
# app/api/passthrough_proxy.py — Safe Generic API Passthrough
# ==========================================================
"""
Provides a universal proxy for all unhandled /v1/* routes.

Used to:
  • Mirror unsupported OpenAI endpoints (assistants, threads, etc.)
  • Gracefully deprecate legacy endpoints (return 404/410)
  • Forward all other traffic to OpenAI transparently

Requires forward_openai_request() from forward_openai.py.
"""

import logging
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1", tags=["Passthrough"])
logger = logging.getLogger("passthrough_proxy")

# ----------------------------------------------------------
# Helper: identify deprecated routes
# ----------------------------------------------------------
DEPRECATED_ENDPOINTS = [
    "assistants",
    "threads",
    "messages",
    "runs",
]

def _is_deprecated(path: str) -> bool:
    return any(path.strip("/").startswith(ep) for ep in DEPRECATED_ENDPOINTS)


# ----------------------------------------------------------
# Catch-all passthrough handler
# ----------------------------------------------------------
@router.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough(request: Request, full_path: str):
    """
    Forward any /v1/* endpoint not explicitly defined elsewhere.
    """
    method = request.method.upper()
    logger.info(f"🌐 Passthrough proxy → /v1/{full_path} [{method}]")

    # Handle deprecated endpoints explicitly
    if _is_deprecated(full_path):
        # Return 410 Gone (spec-compliant for deprecated APIs)
        return JSONResponse(
            {
                "error": {
                    "message": f"The endpoint /v1/{full_path} is deprecated. "
                               "Use /v1/responses instead.",
                    "type": "deprecated_endpoint",
                    "code": 410
                }
            },
            status_code=410,
        )

    # Build forward path (strip redundant slashes)
    forward_path = f"v1/{full_path}".lstrip("/")

    # Parse request body
    content_type = request.headers.get("content-type", "")
    body = None
    json_payload = None
    if "application/json" in content_type:
        try:
            json_payload = await request.json()
        except Exception:
            json_payload = {}
    elif "multipart/form-data" in content_type:
        body = await request.form()
    else:
        raw = await request.body()
        body = raw if raw else None

    try:
        resp = await forward_openai_request(
            path=forward_path,
            method=method,
            json=json_payload,
            data=body if not json_payload else None,
            headers=dict(request.headers),
        )
        return resp
    except HTTPException as e:
        logger.error(f"Proxy error: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected passthrough error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

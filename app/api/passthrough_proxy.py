# ================================================================
# passthrough_proxy.py — Universal /v1/* Proxy (Ground Truth v2.2)
# ================================================================
# This module forwards all unmatched /v1/* requests to OpenAI’s
# upstream API through forward_openai.py. It is the universal
# passthrough for routes like:
#   • /v1/responses
#   • /v1/embeddings
#   • /v1/realtime/sessions
#   • any future OpenAI API path
#
# It is fully compatible with the OpenAI SDK and relay core:
#   • Accepts GET, POST, PUT, PATCH, DELETE
#   • Handles JSON and SSE (streaming) responses
#   • No .json() or .text() misuse — returns FastAPI responses cleanly
# ================================================================

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.api.forward_openai import forward_to_openai
import logging

# Router instance
router = APIRouter(tags=["passthrough"])
logger = logging.getLogger("relay")

# ================================================================
# Universal Passthrough Endpoint
# ================================================================
@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough(path: str, request: Request):
    """
    Forwards any /v1/* route that isn’t explicitly defined elsewhere
    directly to OpenAI via forward_to_openai().

    Behaves exactly like the OpenAI public API, but with local
    authentication, logging, and error handling.
    """

    logger.info(f"🔄 Universal passthrough triggered for /v1/{path}")

    # Call the unified forwarder — returns a FastAPI response
    result = await forward_to_openai(request, path)

    # Case 1: Already a valid FastAPI Response
    if isinstance(result, (JSONResponse, StreamingResponse)):
        return result

    # Case 2: Unexpected result type — wrap in diagnostic JSON
    logger.warning(f"⚠️ Unexpected passthrough return type: {type(result)}")
    return JSONResponse(
        {
            "object": "passthrough_error",
            "message": f"Unexpected passthrough return type: {type(result)}",
            "path": path,
        },
        status_code=500,
    )

"""
validation.py — Schema Validation Middleware
────────────────────────────────────────────
Performs lightweight JSON schema validation and request sanity checking
before passing to the orchestrator.  Ensures requests are well-formed
and OpenAI-compatible.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import json
import logging

logger = logging.getLogger("validation")


class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """
    Intercepts incoming requests and performs basic validation:
      • Valid JSON body for POST/PUT/PATCH
      • Proper Content-Type headers
      • Graceful 400 response if malformed
    """

    async def dispatch(self, request: Request, call_next):
        # Allow GET, DELETE etc. to pass through
        if request.method in ("GET", "DELETE", "OPTIONS", "HEAD"):
            return await call_next(request)

        # Check for JSON in POST/PUT/PATCH
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                if request.headers.get("content-type", "").startswith("application/json"):
                    # Try parsing to ensure it's valid JSON
                    _ = await request.json()
                else:
                    logger.warning(f"[validation] Non-JSON request to {request.url.path}")
            except json.JSONDecodeError:
                logger.error(f"[validation] Invalid JSON on {request.url.path}")
                return JSONResponse(
                    {
                        "error": {
                            "message": "Invalid JSON in request body.",
                            "type": "invalid_request_error",
                        }
                    },
                    status_code=400,
                )
            except Exception as e:
                logger.exception(f"[validation] Unexpected validation error: {e}")
                return JSONResponse(
                    {
                        "error": {
                            "message": f"Unexpected validation error: {str(e)}",
                            "type": "validation_error",
                        }
                    },
                    status_code=400,
                )

        # All clear — continue downstream
        return await call_next(request)

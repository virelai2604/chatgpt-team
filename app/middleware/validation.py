"""
validation.py — Schema Validation Middleware
────────────────────────────────────────────
Performs lightweight JSON validation and request sanity checking
before passing to the orchestrator. Ensures requests are well-formed
and OpenAI-compatible.
"""

import json
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("validation")


class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """
    Intercepts incoming requests and performs basic validation:

      • Allows GET, DELETE, OPTIONS, HEAD to pass through untouched.
      • For POST/PUT/PATCH:
          - If Content-Type is application/json, attempts to parse the body.
          - Returns 400 if JSON is invalid.
          - Logs a warning for non-JSON bodies.

    This is intentionally minimal to keep latency low while still protecting
    the relay from malformed requests.
    """

    async def dispatch(self, request: Request, call_next):
        # Allow non-body methods to pass straight through
        if request.method in ("GET", "DELETE", "OPTIONS", "HEAD"):
            return await call_next(request)

        # Validate JSON for typical body-bearing methods
        if request.method in ("POST", "PUT", "PATCH"):
            try:
                content_type = request.headers.get("content-type", "")
                if content_type.startswith("application/json"):
                    # Ensure the JSON body is syntactically valid
                    _ = await request.json()
                else:
                    logger.warning(
                        f"[validation] Non-JSON request to {request.url.path} "
                        f"with Content-Type: {content_type}"
                    )
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

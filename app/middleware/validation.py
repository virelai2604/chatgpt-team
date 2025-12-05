# app/middleware/validation.py

from __future__ import annotations

import json
import logging
from json import JSONDecodeError

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("relay.schema")


class SchemaValidationMiddleware(BaseHTTPMiddleware):
    """
    Lightweight JSON validation middleware.

    - GET/DELETE/HEAD/OPTIONS: pass through.
    - POST/PUT/PATCH:
        * If Content-Type is application/json, attempt to parse JSON.
        * On JSON decode failure → 400 invalid_request_error.
    - Does not mutate the request body; FastAPI will re-use the cached body.
    """

    async def dispatch(self, request: Request, call_next):
        # Skip methods that normally have no body
        if request.method in ("GET", "DELETE", "HEAD", "OPTIONS"):
            return await call_next(request)

        if request.method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "").lower()
            if "application/json" in content_type:
                try:
                    # This populates the internal body cache; subsequent
                    # request.json() / request.body() calls reuse it.
                    await request.json()
                except JSONDecodeError:
                    logger.warning(
                        "Invalid JSON body on %s %s", request.method, request.url.path
                    )
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "message": "Invalid JSON in request body",
                                "type": "invalid_request_error",
                            }
                        },
                    )
                except Exception as exc:
                    logger.warning(
                        "Unexpected error parsing JSON body on %s %s: %r",
                        request.method,
                        request.url.path,
                        exc,
                    )
                    return JSONResponse(
                        status_code=400,
                        content={
                            "error": {
                                "message": "Malformed JSON in request body",
                                "type": "invalid_request_error",
                            }
                        },
                    )

        return await call_next(request)

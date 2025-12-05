# app/middleware/validation.py
from typing import Callable, Awaitable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Lightweight request validation middleware.

    - Enforces JSON or multipart Content-Type for mutating requests.
    """

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method in {"POST", "PUT", "PATCH"}:
            content_type = request.headers.get("content-type", "")
            if (
                "application/json" not in content_type
                and not content_type.startswith("multipart/form-data")
            ):
                return JSONResponse(
                    status_code=415,
                    content={"detail": f"Unsupported Media Type: {content_type!r}"},
                )

        return await call_next(request)

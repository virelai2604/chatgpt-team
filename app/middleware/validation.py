from __future__ import annotations

from typing import Callable, Iterable, Set

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


def _base_content_type(content_type_header: str) -> str:
    # e.g. "application/json; charset=utf-8" -> "application/json"
    return (content_type_header or "").split(";", 1)[0].strip().lower()


def _is_allowed_content_type(base_ct: str, allowed: Set[str]) -> bool:
    if not base_ct:
        return False
    if base_ct in allowed:
        return True
    # Allow any vendor JSON: application/*+json
    if base_ct.endswith("+json"):
        return True
    # Allow multipart with boundary parameter already stripped
    if base_ct == "multipart/form-data":
        return True
    return False


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Enforce Content-Type for body-bearing methods, while allowing empty-body POSTs.

    Why:
      - Some OpenAI endpoints (notably `/v1/uploads/{upload_id}/cancel`) accept POST with no body.
      - Clients often omit Content-Type when body is empty.
      - We still want strict enforcement when a body *is present*.
    """

    def __init__(
        self,
        app,
        *,
        allowed_content_types: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.allowed_content_types: Set[str] = set(
            ct.strip().lower()
            for ct in (allowed_content_types or ("application/json",))
            if ct and ct.strip()
        )
        # Always allow multipart uploads (e.g. /v1/files, /v1/uploads/*/parts)
        self.allowed_content_types.add("multipart/form-data")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        method = request.method.upper()

        # Only validate methods that commonly carry a body.
        if method in {"POST", "PUT", "PATCH"}:
            raw_ct = request.headers.get("content-type") or ""
            base_ct = _base_content_type(raw_ct)

            if not base_ct:
                # No Content-Type provided. Allow only if the body is empty.
                body = await request.body()  # Starlette caches this (safe for downstream).
                if body:
                    return JSONResponse(
                        status_code=415,
                        content={"detail": "Unsupported Media Type: ''"},
                    )
                return await call_next(request)

            if not _is_allowed_content_type(base_ct, self.allowed_content_types):
                return JSONResponse(
                    status_code=415,
                    content={"detail": f"Unsupported Media Type: '{base_ct}'"},
                )

        return await call_next(request)

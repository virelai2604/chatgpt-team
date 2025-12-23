from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_415_UNSUPPORTED_MEDIA_TYPE

from app.core.logging import get_logger
from app.models.error import ErrorResponse

logger = get_logger(__name__)

_JSON_CT_PREFIX = "application/json"
_MULTIPART_CT_PREFIX = "multipart/form-data"


def _parse_content_length(value: str | None) -> int | None:
    """
    Parse Content-Length safely.

    Returns:
      - int (>=0) if parseable or empty-string treated as 0
      - None if not parseable
    """
    if value is None:
        return None

    v = value.strip()
    if v == "":
        # Some clients/proxies may send an empty Content-Length header.
        return 0

    # If multiple values appear (rare), take the first.
    first = v.split(",", 1)[0].strip()
    if first == "":
        return 0

    try:
        n = int(first)
        return max(n, 0)
    except ValueError:
        return None


def _has_body(request: Request) -> bool:
    """
    Determine if the request is expected to have a body without consuming it.

    Rules:
      - Content-Length parses to >0 => has body
      - Content-Length parses to 0 => no body
      - Transfer-Encoding present => has body
      - Otherwise => assume no body

    This is intentionally permissive for empty-body POSTs (e.g. cancel endpoints).
    """
    cl = _parse_content_length(request.headers.get("content-length"))
    if cl is not None:
        return cl > 0

    # Chunked uploads, etc.
    if request.headers.get("transfer-encoding"):
        return True

    return False


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Reject unsupported content-types for methods that typically carry bodies.

    IMPORTANT: allow empty-body requests (e.g., POST cancel endpoints) even if
    Content-Type is missing. Many clients send Content-Length: 0 and no CT.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method.upper()

        if method in {"POST", "PUT", "PATCH"} and _has_body(request):
            content_type = (request.headers.get("content-type") or "").strip()

            if not (
                content_type.startswith(_JSON_CT_PREFIX)
                or content_type.startswith(_MULTIPART_CT_PREFIX)
            ):
                msg = f"Unsupported Media Type: '{content_type}'"
                logger.info(
                    "ValidationMiddleware rejected request: method=%s path=%s content-type=%r content-length=%r",
                    request.method,
                    request.url.path,
                    content_type,
                    request.headers.get("content-length"),
                )
                err = ErrorResponse.from_message(msg)
                return err.to_response(status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        return await call_next(request)

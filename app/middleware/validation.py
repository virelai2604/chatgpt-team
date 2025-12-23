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


def _has_body(request: Request) -> bool:
    """
    Determine if the request is expected to have a body without consuming it.

    - If Content-Length is present and > 0 => has body
    - If Transfer-Encoding is present => has body
    - Otherwise => assume no body
    """
    cl = request.headers.get("content-length")
    if cl is not None:
        try:
            return int(cl) > 0
        except ValueError:
            # If Content-Length is malformed, be conservative.
            return True

    # Chunked uploads, etc.
    if request.headers.get("transfer-encoding"):
        return True

    return False


class ValidationMiddleware(BaseHTTPMiddleware):
    """
    Reject unsupported content-types for methods that typically carry bodies.

    IMPORTANT: allow empty-body requests (e.g., POST cancel endpoints) even if
    Content-Type is missing. Many clients send `Content-Length: 0` and no CT.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method.upper() in {"POST", "PUT", "PATCH"}:
            if _has_body(request):
                content_type = request.headers.get("content-type", "")
                if not (
                    content_type.startswith(_JSON_CT_PREFIX)
                    or content_type.startswith(_MULTIPART_CT_PREFIX)
                ):
                    logger.info(
                        "ValidationMiddleware rejected request: method=%s path=%s content-type=%r",
                        request.method,
                        request.url.path,
                        content_type,
                    )
                    err = ErrorResponse(
                        detail=f"Unsupported Media Type: '{content_type}'",
                    )
                    return err.to_response(status_code=HTTP_415_UNSUPPORTED_MEDIA_TYPE)

        return await call_next(request)

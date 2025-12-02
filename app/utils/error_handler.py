# app/utils/error_handler.py

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("relay")


def _build_openai_error(
    message: str,
    *,
    status_code: int,
    code: Optional[str] = None,
    path: Optional[str] = None,
    exc: Optional[BaseException] = None,
) -> Dict[str, Any]:
    """
    Build an OpenAI-style error envelope.

    Shape:
      {
        "error": {
          "message": "...",
          "type": "invalid_request_error" | "authentication_error" | "server_error",
          "param": null,
          "code": "some_code" | null,
          "path": "http://...",
          "extra": { ... }   # optional
        }
      }
    """
    if status_code in (401, 403):
        error_type = "authentication_error"
    elif status_code == 404 or (400 <= status_code < 500):
        error_type = "invalid_request_error"
    else:
        error_type = "server_error"

    payload: Dict[str, Any] = {
        "error": {
            "message": message,
            "type": error_type,
            "param": None,
            "code": code,
        }
    }

    if path:
        payload["error"]["path"] = path

    if exc is not None:
        payload["error"]["extra"] = {"exception": str(exc)}

    return payload


def register_exception_handlers(app: FastAPI) -> None:
    """
    Register global exception handlers that return OpenAI-style error
    envelopes instead of the default FastAPI error format.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        path = str(request.url)

        # If already OpenAI-style, pass through.
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            logger.warning(
                "HTTPException in relay (passthrough)",
                extra={
                    "path": path,
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                },
            )
            return JSONResponse(status_code=exc.status_code, content=exc.detail)

        if isinstance(exc.detail, str):
            message = exc.detail
        else:
            message = str(exc.detail)

        logger.warning(
            "HTTPException in relay",
            extra={"path": path, "status_code": exc.status_code, "detail": exc.detail},
        )

        payload = _build_openai_error(
            message=message,
            status_code=exc.status_code,
            path=path,
        )
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        path = str(request.url)
        logger.exception(
            "Unhandled exception in relay",
            extra={"path": path},
        )

        payload = _build_openai_error(
            message="Internal server error",
            status_code=500,
            code="internal_server_error",
            path=path,
            exc=exc,
        )
        return JSONResponse(status_code=500, content=payload)

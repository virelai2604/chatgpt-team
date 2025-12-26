from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["sse"])


@router.post("/responses:stream")
async def responses_stream(request: Request) -> Response:
    """
    Convenience wrapper that forces streaming for /v1/responses.

    Expected: JSON in, SSE out (text/event-stream).
    """
    try:
        payload: Any = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": {"message": "Invalid JSON body"}})

    if not isinstance(payload, dict):
        return JSONResponse(status_code=400, content={"error": {"message": "JSON body must be an object"}})

    forced = dict(payload)
    forced["stream"] = True

    return await forward_openai_method_path(
        method="POST",
        path="/v1/responses",
        request=None,
        inbound_headers=request.headers,
        json_body=forced,
        stream=True,
    )
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from app.api.forward_openai import forward_openai_method_path

router = APIRouter(prefix="/v1", tags=["sse"])


@router.post("/responses:stream")
async def responses_stream(request: Request) -> Response:
    """
    Convenience wrapper that forces streaming for /v1/responses.

    Expected: JSON in, SSE out (text/event-stream).
    """
    try:
        payload: Any = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": {"message": "Invalid JSON body"}})

    if not isinstance(payload, dict):
        return JSONResponse(status_code=400, content={"error": {"message": "JSON body must be an object"}})

    forced = dict(payload)
    forced["stream"] = True

    return await forward_openai_method_path(
        method="POST",
        path="/v1/responses",
        request=None,
        inbound_headers=request.headers,
        json_body=forced,
        stream=True,
    )

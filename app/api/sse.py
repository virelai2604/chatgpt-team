from __future__ import annotations

import json
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse, Response, StreamingResponse

from app.core.config import settings
from app.core.http_client import get_async_httpx_client
from app.api.forward_openai import _build_outbound_headers, _filter_response_headers, _join_upstream_url  # type: ignore
from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["sse"])


@router.post("/responses:stream", include_in_schema=False)
async def responses_stream(request: Request) -> Response:
    """
    Compatibility endpoint used by your tests.

    Behavior:
      - Reads JSON body
      - Forces stream=true
      - Proxies to upstream POST /v1/responses
      - Passes upstream SSE through verbatim (no reformatting)
    """
    try:
        payload: Dict[str, Any] = {}
        raw = await request.body()
        if raw:
            payload = json.loads(raw.decode("utf-8"))

        payload["stream"] = True

        upstream_url = _join_upstream_url(settings.OPENAI_API_BASE, "/v1/responses", "")
        headers = _build_outbound_headers(request.headers.items())
        headers["Accept"] = "text/event-stream"
        headers["Content-Type"] = "application/json"

        client = get_async_httpx_client(timeout=float(settings.PROXY_TIMEOUT_SECONDS))
        req = client.build_request("POST", upstream_url, headers=headers, json=payload)
        resp = await client.send(req, stream=True)

        content_type = resp.headers.get("content-type", "text/event-stream")
        filtered_headers = _filter_response_headers(resp.headers)

        if not content_type.lower().startswith("text/event-stream"):
            data = await resp.aread()
            await resp.aclose()
            return Response(
                content=data,
                status_code=resp.status_code,
                headers=filtered_headers,
                media_type=content_type,
            )

        logger.info("↔ upstream SSE POST /v1/responses (via /v1/responses:stream)")

        async def _aiter():
            async for chunk in resp.aiter_bytes():
                yield chunk
            await resp.aclose()

        return StreamingResponse(
            _aiter(),
            status_code=resp.status_code,
            headers=filtered_headers,
            media_type=content_type,
        )

    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return JSONResponse(status_code=400, content={"detail": "Invalid JSON body", "error": str(exc)})
    except httpx.HTTPError as exc:
        return JSONResponse(status_code=424, content={"detail": "Upstream request failed", "error": str(exc)})
    except Exception as exc:
        return JSONResponse(status_code=424, content={"detail": "Relay wiring error", "error": str(exc)})

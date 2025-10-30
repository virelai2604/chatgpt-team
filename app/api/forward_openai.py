# ==========================================================
# app/api/forward_openai.py — OpenAI-Compatible Forward Proxy
# ==========================================================
"""
Generic forwarder for OpenAI API requests.
Used by passthrough_proxy.py, vector store calls, and SDK mirror routes.

Implements full support for:
  • All HTTP verbs (GET, POST, PUT, PATCH, DELETE)
  • JSON and multipart/form-data
  • Streaming (SSE-style)
  • Graceful error forwarding

Compliant with OpenAI Python SDK behavior (as of 2025.10).
"""

import os
import logging
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

OPENAI_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TIMEOUT = float(os.getenv("OPENAI_TIMEOUT", "60"))

logger = logging.getLogger("forward_openai")

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Accept": "application/json",
}


# ----------------------------------------------------------
# Helper: Forward a request to OpenAI
# ----------------------------------------------------------
async def forward_openai_request(
    path: str,
    method: str = "GET",
    json: dict | None = None,
    data: dict | None = None,
    files: dict | None = None,
    headers: dict | None = None,
    stream: bool = False,
) -> JSONResponse | StreamingResponse:
    """
    Forwards an HTTP request to the OpenAI API.
    Supports full SDK compatibility (JSON, multipart, SSE).
    """
    headers = headers or HEADERS
    url = path if path.startswith("http") else f"{OPENAI_BASE.rstrip('/')}/{path.lstrip('/')}"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            logger.info(f"🔁 Forwarding {method.upper()} → {url}")
            resp = await client.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=json,
                data=data,
                files=files,
                stream=stream,
            )
        except Exception as e:
            logger.error(f"Forwarding error to {url}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        # Handle streaming case
        if stream:
            async def _streamer():
                async for chunk in resp.aiter_text():
                    yield chunk
            return StreamingResponse(_streamer(), media_type=resp.headers.get("content-type", "text/event-stream"))

        # Regular JSON or binary
        if "application/json" in resp.headers.get("content-type", ""):
            try:
                return JSONResponse(resp.json(), status_code=resp.status_code)
            except Exception:
                return JSONResponse({"error": "Invalid JSON from upstream"}, status_code=resp.status_code)

        # Pass through binary content
        return StreamingResponse(
            resp.aiter_bytes(),
            media_type=resp.headers.get("content-type", "application/octet-stream"),
            status_code=resp.status_code,
        )


# ----------------------------------------------------------
# Proxy utility — used in passthrough_proxy
# ----------------------------------------------------------
async def forward_from_request(request: Request, subpath: str):
    """
    Generic proxy used by /v1/passthrough_proxy/* and /v1/forward_openai/*.
    Replicates incoming method, headers, and body.
    """
    method = request.method.upper()
    url = f"{OPENAI_BASE.rstrip('/')}/{subpath.lstrip('/')}"
    headers = dict(request.headers)
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"

    content_type = headers.get("content-type", "")
    body = None
    json_payload = None

    if "application/json" in content_type:
        try:
            json_payload = await request.json()
        except Exception:
            json_payload = {}
    elif "multipart/form-data" in content_type:
        body = await request.form()
    else:
        body = await request.body()

    logger.debug(f"Proxy {method} → {url}")

    resp = await forward_openai_request(
        path=url,
        method=method,
        json=json_payload,
        data=body if not json_payload else None,
        headers=headers,
    )

    return resp

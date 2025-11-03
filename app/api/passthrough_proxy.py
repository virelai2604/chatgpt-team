"""
passthrough_proxy.py — Universal Fallback Proxy for OpenAI Endpoints
────────────────────────────────────────────────────────────────────
Handles all /v1/* routes that aren’t explicitly defined in the relay.
Forwards requests directly to OpenAI’s REST API.

Aligned with:
  • openai-python SDK v2.61
  • openai-node SDK v6.7.0
  • OpenAI API Reference (2025-10)
"""

import os
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1", tags=["passthrough"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_AGENT = "openai-python/2.61.0"
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))


# ------------------------------------------------------------
# Universal passthrough handler
# ------------------------------------------------------------
@router.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def universal_passthrough(request: Request, full_path: str):
    """
    Fallback route: forwards any unmatched /v1/* endpoint to OpenAI.
    Supports both JSON and SSE (stream=True).
    """
    method = request.method.lower()
    upstream_url = f"{OPENAI_API_BASE}/{full_path}"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
    }

    # Prepare request content
    content_type = request.headers.get("content-type", "").lower()
    send_kwargs = {}
    if method in {"post", "put", "patch"}:
        if "application/json" in content_type:
            body = await request.body()
            send_kwargs["content"] = body
            headers["Content-Type"] = "application/json"
        elif "multipart/form-data" in content_type:
            form = await request.form()
            files, data = [], {}
            for key, val in form.multi_items():
                if hasattr(val, "filename"):
                    files.append((key, (val.filename, val.file, val.content_type)))
                else:
                    data[key] = val
            send_kwargs = {"data": data, "files": files}
        else:
            send_kwargs["content"] = await request.body()

    async with httpx.AsyncClient(timeout=None) as client:
        try:
            upstream = await client.request(method, upstream_url, headers=headers, **send_kwargs)
        except httpx.RequestError as e:
            log.error(f"[Passthrough] Network error: {e}")
            return JSONResponse(
                {"error": {"message": str(e), "type": "network_error"}},
                status_code=502,
            )

        # SSE stream passthrough
        if "text/event-stream" in upstream.headers.get("content-type", ""):
            async def sse_stream():
                async for chunk in upstream.aiter_bytes():
                    if await request.is_disconnected():
                        log.info("[Passthrough] Client disconnected mid-stream")
                        break
                    yield chunk
            return StreamingResponse(sse_stream(), media_type="text/event-stream")

        # Standard JSON / binary passthrough
        try:
            return JSONResponse(upstream.json(), status_code=upstream.status_code)
        except Exception:
            return JSONResponse(
                {
                    "object": "proxy_response",
                    "status": upstream.status_code,
                    "content_type": upstream.headers.get("content-type"),
                    "raw": upstream.text[:1000],
                },
                status_code=upstream.status_code,
            )

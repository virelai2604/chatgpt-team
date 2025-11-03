"""
passthrough_proxy.py — Universal Fallback Proxy (v2.1)
────────────────────────────────────────────────────────
Handles all /v1/* routes not explicitly defined.
Aligns with OpenAI SDKs and 2025-10 API reference.
"""

import os
import json
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from app.utils.logger import log

router = APIRouter(prefix="/v1", tags=["passthrough"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_AGENT = "openai-python/2.61.0"
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))


@router.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def universal_passthrough(request: Request, full_path: str):
    """Fallback route: forwards any unmatched /v1/* endpoint to OpenAI."""
    method = request.method.lower()
    url = f"{OPENAI_API_BASE.rstrip('/')}/{full_path.lstrip('/')}"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    try:
        body = await request.json()
        if body.get("stream", False):
            headers["Accept"] = "text/event-stream"
    except Exception:
        pass

    send_kwargs = {}
    ctype = request.headers.get("content-type", "").lower()
    if method in {"post", "put", "patch"}:
        if "application/json" in ctype:
            send_kwargs["content"] = await request.body()
            headers["Content-Type"] = "application/json"
        elif "multipart/form-data" in ctype:
            form = await request.form()
            files, data = [], {}
            for k, v in form.multi_items():
                if hasattr(v, "filename"):
                    files.append((k, (v.filename, v.file, v.content_type)))
                else:
                    data[k] = v
            send_kwargs = {"data": data, "files": files}
        else:
            send_kwargs["content"] = await request.body()

    async with httpx.AsyncClient(timeout=httpx.Timeout(RELAY_TIMEOUT)) as client:
        try:
            resp = await client.request(method, url, headers=headers, **send_kwargs)
        except httpx.RequestError as e:
            log.error(f"[Passthrough] Network error: {e}")
            return JSONResponse({"error": {"message": str(e), "type": "network_error"}}, status_code=502)

        # SSE passthrough
        if "text/event-stream" in resp.headers.get("content-type", ""):
            async def sse_stream():
                async for chunk in resp.aiter_bytes():
                    if await request.is_disconnected():
                        log.info("[Passthrough] Client disconnected mid-stream")
                        break
                    yield chunk
            return StreamingResponse(sse_stream(), media_type="text/event-stream")

        # JSON / fallback
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            return JSONResponse(
                {
                    "object": "proxy_response",
                    "status": resp.status_code,
                    "content_type": resp.headers.get("content-type"),
                    "raw": resp.text[:1000],
                },
                status_code=resp.status_code,
            )

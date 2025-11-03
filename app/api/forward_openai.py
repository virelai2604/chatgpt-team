"""
forward_openai.py — Canonical OpenAI Passthrough Transport (v3.1)
─────────────────────────────────────────────────────────────────
Implements the same request pipeline used by openai-python v2.61
and openai-node v6.7.0.
"""

import os
import time
import json
import asyncio
import httpx
import logging
from fastapi import Request
from fastapi.responses import StreamingResponse, JSONResponse

log = logging.getLogger("relay")

# Environment
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", 120))
MAX_RETRIES = 3


# ------------------------------------------------------------
# Header builder (matches openai-python v2.61)
# ------------------------------------------------------------
def build_headers(method: str = "get", stream: bool = False) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": "openai-python/2.61.0",
        "Accept": "text/event-stream" if stream else "application/json",
    }
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID
    if method.lower() in {"post", "put", "patch"}:
        headers["Content-Type"] = "application/json"
    return headers


# ------------------------------------------------------------
# Core request forwarder
# ------------------------------------------------------------
async def forward_to_openai(request: Request, path: str):
    """Forward /v1/* calls to the configured OpenAI API."""
    method = request.method.lower()
    # Detect if request body includes stream=True
    try:
        body = await request.json()
        is_stream = body.get("stream", False)
    except Exception:
        is_stream = False

    headers = build_headers(method, stream=is_stream)
    url = f"{OPENAI_API_BASE.rstrip('/')}/{path.lstrip('/')}"

    send_kwargs = {}
    if method in {"post", "put", "patch"}:
        ctype = request.headers.get("content-type", "").lower()
        if "multipart/form-data" in ctype:
            form = await request.form()
            data, files = {}, []
            for key, val in form.multi_items():
                if getattr(val, "filename", None):
                    files.append((key, (val.filename, val.file, val.content_type)))
                else:
                    data[key] = val
            send_kwargs = {"data": data, "files": files}
        else:
            raw = await request.body()
            if raw:
                send_kwargs["content"] = raw

    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=httpx.Timeout(RELAY_TIMEOUT, connect=10)) as client:
        resp = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await client.request(method, url, headers=headers, **send_kwargs)
                if resp.status_code not in {429, 500, 502, 503, 504}:
                    break
                log.warning(f"[Forward] Retry {attempt} {resp.status_code} → {url}")
                await asyncio.sleep(0.5 * attempt)
            except httpx.RequestError as e:
                if attempt == MAX_RETRIES:
                    return JSONResponse(
                        {"error": {"message": str(e), "type": "network_error", "code": "request_failed"}},
                        status_code=502,
                    )

    elapsed = round((time.perf_counter() - start) * 1000, 2)
    log.info(json.dumps({
        "method": method.upper(),
        "url": url,
        "status": resp.status_code,
        "elapsed_ms": elapsed,
        "request_id": resp.headers.get("x-request-id")
    }))

    # SSE streaming passthrough
    if "text/event-stream" in resp.headers.get("content-type", ""):
        async def stream_events():
            try:
                async for chunk in resp.aiter_bytes():
                    if await request.is_disconnected():
                        log.info("🔌 Client disconnected mid-stream")
                        break
                    yield chunk
            except asyncio.TimeoutError:
                yield b"event: error\ndata: {\"message\": \"stream timeout\"}\n\n"

        return StreamingResponse(stream_events(), media_type="text/event-stream")

    # Standard JSON response
    if "application/json" in resp.headers.get("content-type", ""):
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            try:
                data = json.loads(resp.text)
                return JSONResponse(data, status_code=resp.status_code)
            except Exception:
                pass

    # Fallback
    return JSONResponse(
        {
            "object": "proxy_response",
            "status": resp.status_code,
            "content_type": resp.headers.get("content-type"),
            "body": getattr(resp, "text", "")[:1000],
        },
        status_code=resp.status_code,
    )

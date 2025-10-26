# app/api/forward.py — BIFL v2.3.4-fp (Render-Optimized, Stream-Enabled)

import os, httpx, json
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
from app.utils.error_handler import error_response

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
TIMEOUT = int(os.getenv("RELAY_TIMEOUT", "600"))
ENABLE_STREAM = os.getenv("ENABLE_STREAM", "false").lower() == "true"

# ──────────────────────────────────────────────
def _build_headers(request: Request) -> dict:
    """Construct canonical OpenAI headers for Render compatibility."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "openai-python/2.6.1 (relay-bifl; Render)",
    }
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    beta_header = []
    model = request.query_params.get("model", "")
    if "gpt-5" in request.url.path or "gpt-5" in model:
        beta_header.append("gpt-5-pro=v1")
    if "sora" in request.url.path or "video" in request.url.path:
        beta_header.append("sora-2-pro=v2")
    if beta_header:
        headers["OpenAI-Beta"] = ", ".join(beta_header)

    return headers

# ──────────────────────────────────────────────
async def _stream_response(upstream: httpx.Response) -> StreamingResponse:
    async def _gen():
        async for chunk in upstream.aiter_bytes():
            yield chunk
    return StreamingResponse(
        _gen(),
        status_code=upstream.status_code,
        headers=upstream.headers,
        media_type=upstream.headers.get("content-type", "application/x-ndjson"),
    )

# ──────────────────────────────────────────────
async def forward_openai(request: Request, endpoint: str):
    headers = _build_headers(request)
    method = request.method.upper()
    url = f"{OPENAI_BASE_URL}{endpoint}"

    try:
        body = await request.body()
        stream_flag = (
            str(request.query_params.get("stream", "")).lower() == "true"
            or ENABLE_STREAM
        )

        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            http2=True,
            headers=headers,
            follow_redirects=True,
        ) as client:
            resp = await client.request(method, url, content=body or None)

            # Stream if flagged or if upstream returns SSE/NDJSON
            if stream_flag or resp.headers.get("content-type", "").startswith(
                ("text/event-stream", "application/x-ndjson")
            ):
                return await _stream_response(resp)

            # Otherwise return JSON
            if resp.headers.get("content-type", "").startswith("application/json"):
                return Response(
                    resp.text, media_type="application/json", status_code=resp.status_code
                )

            # Fallback decode
            try:
                data = resp.json()
                return Response(
                    json.dumps(data),
                    media_type="application/json",
                    status_code=resp.status_code,
                )
            except Exception:
                return Response(
                    resp.content,
                    status_code=resp.status_code,
                    media_type=resp.headers.get(
                        "content-type", "application/octet-stream"
                    ),
                )

    except httpx.RequestError as e:
        return error_response("network_error", str(e), 503)
    except Exception as e:
        return error_response("forward_error", str(e), 500)

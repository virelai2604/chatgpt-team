# app/api/forward.py — BIFL v2.3.3 (Render-Optimized Stable)
# Compatible with Render shared egress and OpenAI Cloudflare edge.

import os, httpx, json
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
from app.utils.error_handler import error_response

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
TIMEOUT = int(os.getenv("FORWARD_TIMEOUT", "600"))

# ──────────────────────────────────────────────
# Build trusted OpenAI headers
# ──────────────────────────────────────────────
def _build_headers(request: Request) -> dict:
    """
    Build a canonical OpenAI header set for Render hosting.
    """
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "openai-python/2.6.1 (relay-bifl; Render)",
    }

    # Optional org header
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    # Beta model headers (GPT-5, Sora, etc.)
    beta_header = []
    model_param = request.query_params.get("model", "")
    if "gpt-5" in request.url.path or "gpt-5" in model_param:
        beta_header.append("gpt-5-pro=v1")
    if "sora" in request.url.path or "video" in request.url.path:
        beta_header.append("sora-2-pro=v2")
    if beta_header:
        headers["OpenAI-Beta"] = ", ".join(beta_header)

    return headers

# ──────────────────────────────────────────────
# Stream response helper
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
# Forward any request to OpenAI API
# ──────────────────────────────────────────────
async def forward_openai(request: Request, endpoint: str):
    headers = _build_headers(request)
    method = request.method.upper()
    url = f"{OPENAI_BASE_URL}{endpoint}"

    try:
        body = await request.body()
        stream_flag = str(request.query_params.get("stream", "")).lower() == "true"

        # ─── Render-safe HTTP/2 client ───
        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            http2=True,
            headers=headers,
            follow_redirects=True,
        ) as client:

            # Debug (optional)
            print(f"[DEBUG] → {method} {url}")
            print("[DEBUG] Headers:", json.dumps(headers, indent=2))

            resp = await client.request(method, url, content=body or None)

            # ─── Streamed responses ───
            if stream_flag or resp.headers.get("content-type", "").startswith(
                ("text/event-stream", "application/x-ndjson")
            ):
                return await _stream_response(resp)

            # ─── Standard JSON responses ───
            if resp.headers.get("content-type", "").startswith("application/json"):
                return Response(
                    resp.text,
                    media_type="application/json",
                    status_code=resp.status_code,
                )

            # ─── Fallback decoding ───
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

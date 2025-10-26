import os
import json
import httpx
from fastapi import Request
from fastapi.responses import Response, StreamingResponse
from app.utils.error_handler import error_response
from app.api.tools_api import TOOL_REGISTRY

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
TIMEOUT = int(os.getenv("RELAY_TIMEOUT", "600"))
ENABLE_STREAM = os.getenv("ENABLE_STREAM", "false").lower() == "true"

def _build_headers(request: Request) -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    beta = []
    path = request.url.path.lower()
    if "gpt-5" in path:
        beta.append("gpt-5-pro=v1")
    if "sora" in path or "video" in path:
        beta.append("sora-2-pro=v2")
    if "realtime" in path:
        beta.append("gpt-5-realtime=v1")

    if beta:
        headers["OpenAI-Beta"] = ", ".join(beta)
    return headers

def inject_tools(payload: dict) -> dict:
    """Auto-inject available tools if model supports them."""
    model = payload.get("model", "")
    if not payload.get("tools") and any(k in model for k in ["gpt-5", "gpt-4o", "o-series"]):
        payload["tools"] = [
            {"type": getattr(m, "TOOL_TYPE", "function"), "id": tid}
            for tid, m in TOOL_REGISTRY.items()
        ]
        payload.setdefault("tool_choice", "auto")
    return payload

async def _stream_response(resp: httpx.Response):
    async def event_gen():
        async for chunk in resp.aiter_bytes():
            yield chunk
    return StreamingResponse(event_gen(),
        status_code=resp.status_code,
        headers=resp.headers,
        media_type=resp.headers.get("content-type", "application/x-ndjson")
    )

async def forward_openai(request: Request, endpoint: str | None = None, override_body: dict | None = None):
    headers = _build_headers(request)
    endpoint = endpoint or request.url.path
    url = f"{OPENAI_BASE_URL}{endpoint}"

    try:
        if override_body is not None:
            if endpoint.startswith("/v1/responses"):
                override_body = inject_tools(override_body)
            body = json.dumps(override_body)
        else:
            body = await request.body() or None

        async with httpx.AsyncClient(timeout=TIMEOUT, http2=True, headers=headers) as client:
            resp = await client.request(request.method, url, content=body)

            # ✅ Upstream error passthrough
            if resp.is_error:
                return error_response("upstream_error", resp.text, resp.status_code)

            # ✅ Streaming support
            if ENABLE_STREAM or "text/event-stream" in resp.headers.get("content-type", ""):
                return await _stream_response(resp)

            return Response(
                resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json"),
                headers=resp.headers,
            )

    except httpx.RequestError as e:
        return error_response("network_error", str(e), 503)
    except Exception as e:
        return error_response("forward_error", str(e), 500)

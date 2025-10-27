# ==========================================================
# app/api/forward_openai.py — Relay v2025-10 Ground Truth Mirror
# ==========================================================
# Universal async OpenAI proxy for all /v1 endpoints.
# Handles streaming, realtime, binary content, and tool orchestration.
# ==========================================================

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


# ----------------------------------------------------------
# HEADER BUILDER
# ----------------------------------------------------------
def _build_headers(request: Request) -> dict:
    """Construct upstream OpenAI headers dynamically."""
    auth_header = request.headers.get("Authorization")
    headers = {
        "Authorization": auth_header or f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Accept header negotiation (SSE vs JSON)
    if "stream" in str(request.url.path).lower():
        headers["Accept"] = "text/event-stream"
    else:
        headers["Accept"] = "application/json"

    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    # Auto Beta flags (OpenAI 2025 spec)
    beta = []
    path = request.url.path.lower()
    if "gpt-5" in path:
        beta.append("gpt-5-pro=v1")
    if "gpt-4o" in path:
        beta.append("gpt-4o=v1")
    if "sora" in path or "video" in path:
        beta.append("sora-2-pro=v2")
    if "realtime" in path or "o-series" in path:
        beta.append("gpt-5-realtime=v1")
    if beta:
        headers["OpenAI-Beta"] = ", ".join(beta)

    return headers


# ----------------------------------------------------------
# TOOL INJECTION (for /v1/responses)
# ----------------------------------------------------------
def inject_tools(payload: dict) -> dict:
    """
    Auto-inject registered tools if model supports them
    (GPT-5, GPT-4o, or O-Series models).
    """
    model = payload.get("model", "")
    if not payload.get("tools") and any(k in model for k in ["gpt-5", "gpt-4o", "o-series"]):
        payload["tools"] = [
            {"type": getattr(m, "TOOL_TYPE", "function"), "id": tid}
            for tid, m in TOOL_REGISTRY.items()
        ]
        payload.setdefault("tool_choice", "auto")
    return payload


# ----------------------------------------------------------
# STREAMING HANDLER
# ----------------------------------------------------------
async def _stream_response(resp: httpx.Response):
    async def event_gen():
        try:
            async for chunk in resp.aiter_bytes():
                yield chunk
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n".encode("utf-8")

    return StreamingResponse(
        event_gen(),
        status_code=resp.status_code,
        headers={k: v for k, v in resp.headers.items() if k.lower() != "transfer-encoding"},
        media_type=resp.headers.get("content-type", "text/event-stream"),
    )


# ----------------------------------------------------------
# MAIN FORWARD FUNCTION
# ----------------------------------------------------------
async def forward_openai(
    request: Request,
    endpoint: str | None = None,
    override_body: dict | None = None,
    stream: bool | None = None
):
    """
    Forward any OpenAI-compatible request upstream.
    Supports standard & streaming modes, tool injection,
    binary transfer, and automatic header management.
    """
    headers = _build_headers(request)
    endpoint = endpoint or request.url.path
    url = f"{OPENAI_BASE_URL}{endpoint}"

    try:
        # Serialize body (override or raw)
        if override_body is not None:
            if endpoint.startswith("/v1/responses"):
                override_body = inject_tools(override_body)
            body = json.dumps(override_body)
        else:
            body = await request.body() or None

        # Determine if streaming mode
        if stream is None:
            stream = ENABLE_STREAM
        if override_body and "stream" in override_body:
            stream = override_body.get("stream")

        async with httpx.AsyncClient(timeout=TIMEOUT, http2=True, headers=headers) as client:
            if stream:
                async with client.stream(request.method, url, content=body) as resp:
                    if resp.is_error:
                        raw = await resp.aread()
                        msg = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
                        return error_response("upstream_error", msg, resp.status_code)
                    return await _stream_response(resp)

            # Standard mode
            resp = await client.request(request.method, url, content=body)
            if resp.is_error:
                msg = resp.text
                # Defensive check in case resp.text fails
                if isinstance(msg, (bytes, bytearray)):
                    msg = msg.decode("utf-8", errors="replace")
                return error_response("upstream_error", msg, resp.status_code)

            return Response(
                resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json"),
                headers={k: v for k, v in resp.headers.items() if k.lower() != "transfer-encoding"},
            )

    except httpx.RequestError as e:
        return error_response("network_error", str(e), 503)
    except Exception as e:
        # If e is bytes or contains bytes, decode safely
        msg = str(e)
        if isinstance(e, (bytes, bytearray)):
            try:
                msg = e.decode("utf-8", errors="replace")
            except Exception:
                msg = str(e)
        return error_response("forward_error", msg, 500)

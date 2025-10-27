# ==========================================================
# app/api/forward_openai.py — Relay v2025-10 ChatGPT Action Mode
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
# HEADER BUILDER (ALWAYS USE INTERNAL OPENAI KEY)
# ----------------------------------------------------------
def _build_headers(_: Request) -> dict:
    """Construct upstream OpenAI headers — always use relay's internal key."""
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    # Beta flags for OpenAI 2025 spec
    beta = []
    if "gpt-5" in OPENAI_API_KEY:
        beta.append("gpt-5-pro=v1")
    if "gpt-4o" in OPENAI_API_KEY:
        beta.append("gpt-4o=v1")
    if beta:
        headers["OpenAI-Beta"] = ", ".join(beta)

    return headers


# ----------------------------------------------------------
# TOOL INJECTION (for /v1/responses)
# ----------------------------------------------------------
def inject_tools(payload: dict) -> dict:
    """Auto-inject registered tools if model supports them."""
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
    Always authenticates using the relay's internal OPENAI_API_KEY,
    ignoring any Authorization header sent by clients.
    """
    headers = _build_headers(request)
    endpoint = endpoint or request.url.path
    url = f"{OPENAI_BASE_URL}{endpoint}"

    try:
        # Serialize request body
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

            # Non-streaming mode
            resp = await client.request(request.method, url, content=body)
            if resp.is_error:
                msg = resp.text
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
        msg = str(e)
        if isinstance(e, (bytes, bytearray)):
            try:
                msg = e.decode("utf-8", errors="replace")
            except Exception:
                msg = str(e)
        return error_response("forward_error", msg, 500)

# ==========================================================
# app/routes/responses.py — Unified Responses Endpoint
# BIFL v2.3.4-fp (Future-Proof, Stream-Enabled, Realtime-Ready)
# ==========================================================
import os, json, httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from app.utils.error_handler import error_response
from app.api.tools_api import TOOL_REGISTRY

router = APIRouter(prefix="/v1", tags=["Responses"])

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TIMEOUT = int(os.getenv("FORWARD_TIMEOUT", "600"))
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-5-pro")
ENABLE_STREAM = os.getenv("ENABLE_STREAM", "true").lower() == "true"


# ──────────────────────────────────────────────
async def _stream_response(upstream: httpx.Response) -> StreamingResponse:
    """Pipe the upstream NDJSON/SSE stream to the client."""
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
@router.post("/responses")
async def create_response(request: Request):
    """
    POST /v1/responses — Unified multimodal handler for GPT-5.
    Supports text, image, audio, video (via tools[]).
    """
    try:
        body = await request.json()
        body.setdefault("stream", ENABLE_STREAM)
        model = body.get("model", DEFAULT_MODEL)
        tools = body.get("tools", [])

        # Auto-populate tools if missing
        if not tools:
            body["tools"] = [{"type": t} for t in list_local_tools()]  # ✅ fixed function

        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        # Beta feature headers
        beta = []
        if "gpt-5" in model:
            beta.append("gpt-5-pro=v1")
        if any("sora" in t["type"] for t in body["tools"]):
            beta.append("sora-2-pro=v2")
        if beta:
            headers["OpenAI-Beta"] = ", ".join(beta)

        async with httpx.AsyncClient(timeout=TIMEOUT, http2=True) as client:
            upstream = await client.post(
                f"{OPENAI_BASE_URL}/v1/responses", headers=headers, json=body
            )

            # Stream if upstream supports it
            if upstream.headers.get("content-type", "").startswith(
                ("text/event-stream", "application/x-ndjson")
            ):
                return await _stream_response(upstream)

            # Otherwise normal JSON
            return Response(
                upstream.text, media_type="application/json", status_code=upstream.status_code
            )

    except Exception as e:
        return error_response("response_error", str(e), 500)


# ──────────────────────────────────────────────
@router.post("/responses/stream")
async def create_response_stream(request: Request):
    """
    POST /v1/responses/stream — Stream alias for realtime GPT-5 & Sora.
    Equivalent to /v1/responses with stream=true.
    """
    try:
        body = await request.json()
        body["stream"] = True
        return await create_response(request)
    except Exception as e:
        return error_response("stream_error", str(e), 500)

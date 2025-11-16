"""
responses.py — /v1/responses
─────────────────────────────
Thin but explicit wrapper around OpenAI's Responses API.

This is where you can later add:
  • extra logging,
  • org-level policy,
  • default tools configuration.

For now it forwards to OpenAI with true streaming support.
"""

import os
import json
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.utils.logger import relay_log as logger

router = APIRouter(prefix="/v1", tags=["responses"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "60"))
USER_AGENT = os.getenv("RELAY_USER_AGENT", "chatgpt-team-relay/1.0")


def _headers():
    return {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }


@router.post("/responses")
async def create_response(request: Request):
    """
    POST /v1/responses

    Accepts a standard Responses API body and forwards it to OpenAI.
    Supports both streaming and non-streaming modes.

    Tools are passed via the 'tools' field and are NOT modified here.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"error": {"message": "Invalid JSON body", "type": "invalid_request_error"}},
            status_code=400,
        )

    stream = bool(body.get("stream", False))
    model = body.get("model")
    logger.info(f"[Responses] model={model} stream={stream}")

    url = f"{OPENAI_API_BASE.rstrip('/')}/responses"
    headers = _headers()

    # Non-streaming: simple JSON round-trip
    if not stream:
        async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
            try:
                resp = await client.post(url, headers=headers, json=body)
            except httpx.RequestError as e:
                logger.error(f"[Responses] network error: {e}")
                return JSONResponse(
                    {
                        "error": {
                            "message": str(e),
                            "type": "upstream_error",
                        }
                    },
                    status_code=502,
                )
        try:
            return JSONResponse(resp.json(), status_code=resp.status_code)
        except Exception:
            return JSONResponse(
                {"status_code": resp.status_code, "body": resp.text},
                status_code=resp.status_code,
            )

    # Streaming: true SSE passthrough
    async def sse_stream():
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream("POST", url, headers=headers, json=body) as upstream:
                    async for line in upstream.aiter_lines():
                        if await request.is_disconnected():
                            break
                        if line:
                            yield line + "\n"
            except httpx.RequestError as e:
                logger.error(f"[Responses] stream error: {e}")
                err = {"message": str(e), "type": "upstream_error"}
                yield "event: error\n"
                yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(sse_stream(), media_type="text/event-stream")

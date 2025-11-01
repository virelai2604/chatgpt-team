"""
p4_orchestrator.py — Ground Truth API v1.7
Transforms /v1/p4 requests into /v1/responses payloads for unified reasoning.
"""

import os
import json
import httpx
import asyncio
import time
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from app.utils.logger import logger

router = APIRouter()
RELAY_URL = os.getenv("RELAY_URL", "http://127.0.0.1:8000")


async def _forward_responses(payload: dict, headers: dict) -> httpx.Response:
    """Forward request to /v1/responses with stream or non-stream handling."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        if payload.get("stream"):
            return client.stream(
                "POST", f"{RELAY_URL}/v1/responses", json=payload, headers=headers
            )
        return await client.post(f"{RELAY_URL}/v1/responses", json=payload, headers=headers)


@router.post("/v1/p4")
async def handle_p4_request(request: Request):
    """
    Converts a P4 hybrid reasoning payload into a /v1/responses request.
    SDK-compatible fields are preserved (model, input, tools, stream).
    """
    body = await request.json()
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in {"host", "content-length"}}
    headers["Authorization"] = headers.get("authorization", os.getenv("OPENAI_API_KEY", ""))

    payload = {
        "model": body.get("model", "gpt-5"),
        "input": body.get("prompt") or body.get("input", ""),
        "instructions": body.get("instructions", ""),
        "tools": body.get("tools", []),
        "stream": body.get("stream", False),
    }

    logger.info(f"P4 orchestrator forwarding to /v1/responses (stream={payload['stream']})")

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            if payload["stream"]:
                async with client.stream("POST", f"{RELAY_URL}/v1/responses",
                                         json=payload, headers=headers) as resp:
                    async def sse():
                        async for chunk in resp.aiter_bytes():
                            yield chunk
                    return StreamingResponse(sse(), media_type="text/event-stream")
            else:
                resp = await client.post(f"{RELAY_URL}/v1/responses",
                                         json=payload, headers=headers)
                return JSONResponse(status_code=resp.status_code, content=resp.json())
    except Exception as e:
        logger.error(f"P4 orchestrator failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

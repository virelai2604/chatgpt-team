"""
forward_openai.py — Ground Truth API v1.7
Forwards unmatched requests to upstream OpenAI endpoints.
Supports JSON + streaming.
"""

import os
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse, Response
from app.utils.logger import logger

router = APIRouter()

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TIMEOUT = float(os.getenv("PROXY_TIMEOUT", "180"))


async def _passthrough(method: str, path: str, request: Request):
    target_url = f"{OPENAI_API_BASE}{path}"
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in {"host", "content-length"}}
    headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
    headers["User-Agent"] = "ChatGPT-Team-Relay/2025.11"

    try:
        body = await request.body()
    except Exception:
        body = b""

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            resp = await client.request(method, target_url,
                                        headers=headers, content=body, stream=True)
            # Streamed
            if resp.headers.get("content-type", "").startswith("text/event-stream"):
                async def event_gen():
                    async for chunk in resp.aiter_bytes():
                        yield chunk
                return StreamingResponse(event_gen(),
                                         media_type="text/event-stream",
                                         status_code=resp.status_code)
            # JSON
            try:
                data = resp.json()
                out = JSONResponse(status_code=resp.status_code, content=data)
                # propagate select headers
                for key in ["x-request-id", "openai-processing-ms"]:
                    if key in resp.headers:
                        out.headers[key] = resp.headers[key]
                return out
            except Exception:
                return Response(content=await resp.aread(),
                                status_code=resp.status_code,
                                headers=dict(resp.headers))
        except httpx.RequestError as e:
            logger.error(f"Passthrough error: {e}")
            raise HTTPException(status_code=502, detail=str(e))


@router.api_route("/{path:path}",
                  methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def passthrough_router(request: Request, path: str):
    if os.getenv("DISABLE_PASSTHROUGH", "false").lower() == "true":
        raise HTTPException(status_code=404, detail="Passthrough disabled")
    return await _passthrough(request.method, f"/{path}", request)

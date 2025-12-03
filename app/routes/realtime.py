# app/routes/realtime.py

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

import httpx
import websockets
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from websockets.exceptions import ConnectionClosed

from app.api.forward_openai import forward_openai_from_parts

logger = logging.getLogger("relay.realtime")

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA", "realtime=v1")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", "300"))
DEFAULT_REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4.1-mini")

router = APIRouter(
    prefix="/v1/realtime",
    tags=["realtime"],
)


def _build_openai_beta_header(existing: Optional[str]) -> str:
    """
    Merge existing OpenAI-Beta header with realtime=v1, avoiding duplicates.
    """
    parts = []
    if existing:
        parts.extend(
            [p.strip() for p in existing.split(",") if p.strip() and p.strip() != "realtime=v1"]
        )
    parts.append("realtime=v1")
    return ", ".join(parts)


@router.post("/sessions")
async def create_realtime_session(request: Request) -> JSONResponse:
    """
    REST helper for creating a realtime session descriptor.

    This is a thin proxy to POST https://api.openai.com/v1/realtime/sessions
    and ensures OpenAI-Beta: realtime=v1 plus a default model.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured for realtime.",
                    "type": "server_error",
                    "code": "missing_api_key",
                }
            },
        )

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    if "model" not in payload:
        payload["model"] = DEFAULT_REALTIME_MODEL

    incoming_headers = dict(request.headers)
    beta_existing = incoming_headers.get("OpenAI-Beta") or incoming_headers.get("openai-beta")
    incoming_headers["OpenAI-Beta"] = _build_openai_beta_header(beta_existing)

    # Use the generic forwarder for consistency
    resp = await forward_openai_from_parts(
        method="POST",
        path="/v1/realtime/sessions",
        query=dict(request.query_params),
        body=payload,
        headers=incoming_headers,
    )

    # forward_openai_from_parts returns a generic Response; wrap as JSONResponse
    # for FastAPI to keep type hints clean.
    return JSONResponse(
        status_code=resp.status_code,
        content=json.loads(resp.body.decode("utf-8")) if resp.body else None,
    )


@router.websocket("/ws")
async def realtime_websocket(websocket: WebSocket) -> None:
    """
    WebSocket proxy:

    Client  <—WS—>  /v1/realtime/ws (relay)  <—WS—>  wss://api.openai.com/v1/realtime

    Query params:
      - model: optional, defaults to DEFAULT_REALTIME_MODEL
      - session_id / session_key: optional, forwarded as-is for ephemeral sessions
    """
    await websocket.accept()

    if not OPENAI_API_KEY:
        await websocket.close(code=4401)  # Unauthorized
        return

    query_params = dict(websocket.query_params)
    model = query_params.get("model") or DEFAULT_REALTIME_MODEL

    # Build upstream Realtime WS URL
    base_ws = OPENAI_API_BASE.replace("https://", "wss://").replace("http://", "ws://")
    query_qs = "&".join(
        [f"model={model}"]
        + [f"{k}={v}" for k, v in query_params.items() if k != "model"]
    )
    upstream_url = f"{base_ws}/v1/realtime"
    if query_qs:
        upstream_url = f"{upstream_url}?{query_qs}"

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": OPENAI_REALTIME_BETA,
    }

    logger.info("realtime_ws.connect upstream_url=%s", upstream_url)

    try:
        async with websockets.connect(
            upstream_url,
            extra_headers=headers,
            open_timeout=PROXY_TIMEOUT,
            close_timeout=PROXY_TIMEOUT,
            max_size=None,  # allow large frames
        ) as upstream_ws:

            async def client_to_openai() -> None:
                try:
                    while True:
                        msg = await websocket.receive()
                        if "text" in msg and msg["text"] is not None:
                            await upstream_ws.send(msg["text"])
                        elif "bytes" in msg and msg["bytes"] is not None:
                            await upstream_ws.send(msg["bytes"])
                except WebSocketDisconnect:
                    logger.info("realtime_ws.client_disconnected")
                    await upstream_ws.close()
                except Exception as exc:
                    logger.warning("realtime_ws.client_to_openai_error %s", exc)
                    await upstream_ws.close()

            async def openai_to_client() -> None:
                try:
                    async for message in upstream_ws:
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except ConnectionClosed:
                    logger.info("realtime_ws.upstream_closed")
                    await websocket.close()
                except Exception as exc:
                    logger.warning("realtime_ws.openai_to_client_error %s", exc)
                    await websocket.close()

            await asyncio.gather(client_to_openai(), openai_to_client())

    except Exception as exc:
        logger.exception("realtime_ws.proxy_error %s", exc)
        # 1011: internal error
        await websocket.close(code=1011)

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from websockets import connect as ws_connect  # type: ignore
from websockets.exceptions import ConnectionClosed  # type: ignore

from app.utils.logger import relay_log as logger

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA", "realtime=v1")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
DEFAULT_REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4o-realtime-preview")

router = APIRouter(
    prefix="/v1",
    tags=["realtime"],
)


def _auth_headers(extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": OPENAI_REALTIME_BETA,
    }
    if extra:
        headers.update(extra)
    return headers


@router.post("/realtime/sessions")
async def create_realtime_session(request: Request) -> JSONResponse:
    """
    POST /v1/realtime/sessions

    Thin proxy to OpenAI's Realtime sessions API. Ensures:
      - `model` defaults to REALTIME_MODEL if not provided.
      - `OpenAI-Beta: realtime=v1` header is set.
    """
    try:
        payload = await request.json()
    except Exception:
        payload = {}

    if not isinstance(payload, dict):
        payload = {}

    payload.setdefault("model", DEFAULT_REALTIME_MODEL)

    url = f"{OPENAI_API_BASE}/v1/realtime/sessions"
    logger.info("→ [realtime] POST %s", url)

    async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
        try:
            resp = await client.post(url, headers=_auth_headers(), json=payload)
        except httpx.HTTPError as exc:
            logger.exception("Upstream realtime session error")
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    content: Any
    try:
        content = resp.json()
    except Exception:
        content = {"raw": resp.text}

    return JSONResponse(
        status_code=resp.status_code,
        content=content,
        headers={"x-openai-upstream-status": str(resp.status_code)},
    )


@router.websocket("/realtime/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    """
    WebSocket bridge:

      Client <—WS—> Relay <—WS—> OpenAI Realtime

    Query params:
      - model (optional): defaults to REALTIME_MODEL.
    """
    await websocket.accept()
    params = dict(websocket.query_params)
    model = params.get("model") or DEFAULT_REALTIME_MODEL

    # Map HTTP base → WS base
    ws_base = OPENAI_API_BASE.replace("https://", "wss://").replace("http://", "ws://")
    upstream_url = f"{ws_base}/v1/realtime?model={model}"

    logger.info("↔ [realtime/ws] proxy to %s", upstream_url)

    try:
        async with ws_connect(
            upstream_url,
            extra_headers=_auth_headers(),
            open_timeout=PROXY_TIMEOUT,
            close_timeout=PROXY_TIMEOUT,
            max_size=None,
        ) as upstream:
            async def client_to_upstream() -> None:
                try:
                    while True:
                        message = await websocket.receive_text()
                        await upstream.send(message)
                except WebSocketDisconnect:
                    await upstream.close()
                except Exception:
                    logger.exception("Error relaying client → upstream")
                    await upstream.close()

            async def upstream_to_client() -> None:
                try:
                    while True:
                        message = await upstream.recv()
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except ConnectionClosed:
                    await websocket.close()
                except Exception:
                    logger.exception("Error relaying upstream → client")
                    await websocket.close()

            await asyncio.gather(client_to_upstream(), upstream_to_client())

    except Exception as exc:
        logger.exception("Failed to establish realtime websocket: %s", exc)
        # 1011 = internal error
        await websocket.close(code=1011, reason="Upstream realtime error")

# app/routes/realtime.py

"""
realtime.py — /v1/realtime
──────────────────────────
WebSocket bridge for OpenAI Realtime API.

Client connects to:
  wss://chatgpt-team-relay.onrender.com/v1/realtime/sessions?model=gpt-4o-realtime-preview

Relay opens a WebSocket to:
  wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview

and passes messages both ways, adding Authorization (and optional
OpenAI-Beta: realtime=v1) on the upstream connection only (never
exposing the API key to the client).
"""

import asyncio
import os

import websockets
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from websockets.exceptions import ConnectionClosed

from app.utils.logger import relay_log as log

router = APIRouter(prefix="/v1/realtime", tags=["realtime"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Optional; GA may not require this, but keeping it preserves beta behavior.
# Example value: "realtime=v1"
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA", "realtime=v1")


def _build_upstream_ws_url(model: str) -> str:
    """
    Derive wss://.../v1/realtime?model=... from OPENAI_API_BASE.

    Examples:
      OPENAI_API_BASE = https://api.openai.com
        -> wss://api.openai.com/v1/realtime?model=...
      OPENAI_API_BASE = http://localhost:8080
        -> ws://localhost:8080/v1/realtime?model=...
    """
    base = OPENAI_API_BASE.rstrip("/")
    if base.startswith("https://"):
        host = base[len("https://") :]
        ws_base = f"wss://{host}/v1/realtime"
    elif base.startswith("http://"):
        host = base[len("http://") :]
        ws_base = f"ws://{host}/v1/realtime"
    else:
        # Assume caller set full ws(s) URL; append /v1/realtime if not present
        ws_base = base
        if "/v1/realtime" not in ws_base:
            ws_base = ws_base.rstrip("/") + "/v1/realtime"

    return f"{ws_base}?model={model}"


def _upstream_headers() -> dict:
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    # Keep the beta header for compatibility if configured
    if OPENAI_REALTIME_BETA:
        # Value like "realtime=v1" → OpenAI-Beta: realtime=v1
        headers["OpenAI-Beta"] = OPENAI_REALTIME_BETA
    return headers


@router.get("/sessions/ping")
async def ping_realtime():
    """
    Simple HTTP ping so you can curl /v1/realtime/sessions/ping for monitoring.
    """
    return JSONResponse({"object": "realtime.ping", "status": "ok"}, status_code=200)


@router.websocket("/sessions")
async def realtime_sessions(
    websocket: WebSocket,
    model: str = Query("gpt-4o-realtime-preview"),
):
    """
    WebSocket endpoint that proxies a Realtime session.

    - Client connects here with a model query param.
    - Relay connects upstream to OpenAI Realtime with the same model.
    - Messages (text or binary) are forwarded both ways.
    """
    await websocket.accept()
    upstream_url = _build_upstream_ws_url(model)
    log.info(f"[Realtime] Bridging WebSocket for model={model} → {upstream_url}")

    # If no API key is configured, fail fast.
    if not OPENAI_API_KEY:
        await websocket.send_text(
            '{"type":"error","error":{"message":"Relay missing OPENAI_API_KEY"}}'
        )
        await websocket.close()
        return

    try:
        async with websockets.connect(
            upstream_url,
            extra_headers=_upstream_headers(),
            ping_interval=None,
        ) as upstream:

            async def client_to_openai():
                try:
                    while True:
                        msg = await websocket.receive()
                        if "text" in msg and msg["text"] is not None:
                            await upstream.send(msg["text"])
                        elif "bytes" in msg and msg["bytes"] is not None:
                            await upstream.send(msg["bytes"])
                        elif msg.get("type") == "websocket.disconnect":
                            break
                except WebSocketDisconnect:
                    log.info("[Realtime] Client disconnected.")
                    await upstream.close()
                except Exception as e:
                    log.error(f"[Realtime] client_to_openai error: {e}")
                    try:
                        await upstream.close()
                    except Exception:
                        pass

            async def openai_to_client():
                try:
                    async for msg in upstream:
                        if isinstance(msg, str):
                            await websocket.send_text(msg)
                        else:
                            await websocket.send_bytes(msg)
                except ConnectionClosed:
                    log.info("[Realtime] Upstream connection closed.")
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                except Exception as e:
                    log.error(f"[Realtime] openai_to_client error: {e}")
                    try:
                        await websocket.close()
                    except Exception:
                        pass

            await asyncio.gather(client_to_openai(), openai_to_client())

    except Exception as e:
        log.error(f"[Realtime] Failed to open upstream WS: {e}")
        try:
            await websocket.send_text(
                '{"type":"error","error":{"message":"Failed to connect to Realtime upstream"}}'
            )
        except Exception:
            pass
        await websocket.close()

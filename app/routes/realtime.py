# app/routes/realtime.py
from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from websockets import connect as ws_connect  # type: ignore
from websockets.exceptions import ConnectionClosed  # type: ignore

from app.api.forward_openai import forward_openai_request
from app.core.config import settings
from app.utils.logger import relay_log as logger  # type: ignore

router = APIRouter(
    tags=["realtime"],
)

# ----------------------------------------------------------------------
# Upstream config
# ----------------------------------------------------------------------

# Derive WebSocket base from HTTP base. We assume https → wss.
OPENAI_API_BASE_WS = "wss://api.openai.com"

OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_REALTIME_BETA = settings.OPENAI_REALTIME_BETA
REALTIME_MODEL = settings.REALTIME_MODEL
PROXY_TIMEOUT = settings.PROXY_TIMEOUT


def _build_realtime_ws_url() -> str:
    """
    Build upstream websocket URL for the Realtime API.
    """
    return f"{OPENAI_API_BASE_WS}/v1/realtime?model={REALTIME_MODEL}"


# ----------------------------------------------------------------------
# HTTP: /v1/realtime/sessions
# ----------------------------------------------------------------------


@router.post("/v1/realtime/sessions")
async def create_realtime_session(request: Request) -> Response:
    """
    POST /v1/realtime/sessions

    Thin proxy for Realtime session creation, matching:
      https://platform.openai.com/docs/api-reference/realtime-sessions
    """
    logger.info("[realtime] HTTP %s %s", request.method, request.url.path)
    return await forward_openai_request(request)


# ----------------------------------------------------------------------
# WebSocket: /v1/realtime
# ----------------------------------------------------------------------


async def _pump_client_to_upstream(
    client_ws: WebSocket,
    upstream_ws: Any,
) -> None:
    """
    Forward messages from local client → upstream Realtime API.
    """
    try:
        while True:
            message = await client_ws.receive()

            # FastAPI WebSocket receive() returns a dict.
            if message["type"] == "websocket.disconnect":
                break

            text = message.get("text")
            data = message.get("bytes")

            if text is not None:
                await upstream_ws.send(text)
            elif data is not None:
                await upstream_ws.send(data)
    except WebSocketDisconnect:
        logger.info("[realtime] client WebSocket disconnected")
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("[realtime] client→upstream pump error: %s", exc)


async def _pump_upstream_to_client(
    client_ws: WebSocket,
    upstream_ws: Any,
) -> None:
    """
    Forward messages from upstream Realtime API → local client.
    """
    try:
        async for msg in upstream_ws:
            if isinstance(msg, bytes):
                await client_ws.send_bytes(msg)
            else:
                await client_ws.send_text(msg)
    except ConnectionClosed:
        logger.info("[realtime] upstream WebSocket closed")
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("[realtime] upstream→client pump error: %s", exc)


@router.websocket("/v1/realtime")
async def realtime_websocket(client_ws: WebSocket) -> None:
    """
    WebSocket bridge for the OpenAI Realtime API.

    Local clients connect to:
      ws://<relay-host>/v1/realtime

    The relay connects upstream to:
      wss://api.openai.com/v1/realtime?model=REALTIME_MODEL

    with headers:
      Authorization: Bearer <OPENAI_API_KEY>
      OpenAI-Beta: realtime=v1
    """
    await client_ws.accept()
    logger.info("[realtime] WebSocket accepted from %s", client_ws.client)

    if not OPENAI_API_KEY:
        await client_ws.close(code=1011)
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not configured")

    url = _build_realtime_ws_url()
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": OPENAI_REALTIME_BETA,
    }

    try:
        async with ws_connect(
            url,
            extra_headers=headers,
            open_timeout=PROXY_TIMEOUT,
        ) as upstream_ws:
            logger.info("[realtime] connected upstream to %s", url)

            client_to_upstream = asyncio.create_task(
                _pump_client_to_upstream(client_ws, upstream_ws)
            )
            upstream_to_client = asyncio.create_task(
                _pump_upstream_to_client(client_ws, upstream_ws)
            )

            done, pending = await asyncio.wait(
                {client_to_upstream, upstream_to_client},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()

    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("[realtime] error establishing upstream WebSocket: %s", exc)
        try:
            await client_ws.close(code=1011)
        except Exception:  # ignore double close
            pass

# app/routes/realtime.py
from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from websockets import connect as ws_connect  # type: ignore
from websockets.exceptions import ConnectionClosed  # type: ignore

from app.utils.logger import relay_log as logger

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA", "realtime=v1")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
DEFAULT_REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4.1-mini")

router = APIRouter(
    prefix="/v1",
    tags=["realtime"],
)


def _build_headers(request: Optional[Request] = None) -> Dict[str, str]:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured for Realtime",
                    "type": "config_error",
                    "code": "no_api_key",
                }
            },
        )

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # Allow clients to override OpenAI-Beta header, but fall back to env default
    incoming_beta: Optional[str] = None
    if request is not None:
        incoming_beta = request.headers.get("OpenAI-Beta")
    beta = incoming_beta or OPENAI_REALTIME_BETA
    if beta:
        headers["OpenAI-Beta"] = beta

    return headers


async def _post_realtime_sessions(
    request: Request,
    body: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    POST /v1/realtime/sessions → OpenAI Realtime Sessions API.
    """
    url = f"{OPENAI_API_BASE}/v1/realtime/sessions"
    headers = _build_headers(request)
    logger.info("→ [realtime] POST %s", url)

    async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
        try:
            resp = await client.post(url, headers=headers, json=body)
        except httpx.RequestError as exc:
            logger.error("[realtime] Upstream request error: %s", exc)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Failed to reach OpenAI Realtime Sessions API",
                        "type": "upstream_error",
                        "code": "realtime_upstream_unreachable",
                    }
                },
            ) from exc

    try:
        payload: Dict[str, Any] = resp.json()
    except Exception:
        payload = {
            "error": {
                "message": resp.text,
                "type": "api_error",
                "code": resp.status_code,
            }
        }

    if resp.status_code >= 400:
        logger.warning(
            "[realtime] Upstream error %s: %s",
            resp.status_code,
            payload.get("error", {}).get("message", ""),
        )
        raise HTTPException(status_code=resp.status_code, detail=payload)

    return payload


@router.post("/realtime/sessions", summary="Create a Realtime session (HTTP)")
async def create_realtime_session(request: Request) -> JSONResponse:
    """
    HTTP helper for creating Realtime sessions.

    Mirrors:
      POST https://api.openai.com/v1/realtime/sessions
    """
    try:
        body = await request.json()
    except Exception:
        body = None

    if isinstance(body, dict) and "model" not in body:
        body.setdefault("model", DEFAULT_REALTIME_MODEL)

    payload = await _post_realtime_sessions(request, body)
    return JSONResponse(payload, status_code=200)


@router.websocket("/realtime/ws")
async def realtime_websocket(
    websocket: WebSocket,
    model: Optional[str] = None,
) -> None:
    """
    WebSocket bridge for the Realtime API.

    Clients connect to:
      ws[s]://<relay>/v1/realtime/ws?model=<model>

    The relay then connects to:
      wss://api.openai.com/v1/realtime?model=<model>

    All text/binary frames are proxied bidirectionally.
    """
    await websocket.accept()
    upstream_model = model or DEFAULT_REALTIME_MODEL

    if not OPENAI_API_KEY:
        await websocket.close(code=1011)
        return

    # Convert OPENAI_API_BASE ⇒ WebSocket base
    if OPENAI_API_BASE.startswith("https://"):
        ws_base = "wss://" + OPENAI_API_BASE[len("https://") :]
    elif OPENAI_API_BASE.startswith("http://"):
        ws_base = "ws://" + OPENAI_API_BASE[len("http://") :]
    else:
        ws_base = OPENAI_API_BASE.replace("https://", "wss://").replace(
            "http://", "ws://"
        )

    upstream_url = f"{ws_base}/v1/realtime?model={upstream_model}"

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }
    if OPENAI_REALTIME_BETA:
        headers["OpenAI-Beta"] = OPENAI_REALTIME_BETA

    logger.info(
        "[realtime.ws] Connecting upstream model=%s url=%s",
        upstream_model,
        upstream_url,
    )

    try:
        async with ws_connect(
            upstream_url,
            extra_headers=headers,
            open_timeout=PROXY_TIMEOUT,
        ) as upstream:

            async def client_to_upstream() -> None:
                try:
                    while True:
                        msg = await websocket.receive()
                        if "text" in msg and msg["text"] is not None:
                            await upstream.send(msg["text"])
                        elif "bytes" in msg and msg["bytes"] is not None:
                            await upstream.send(msg["bytes"])
                except WebSocketDisconnect:
                    logger.info("[realtime.ws] client disconnected")
                    try:
                        await upstream.close()
                    except Exception:
                        pass
                except ConnectionClosed:
                    logger.info("[realtime.ws] upstream closed (client_to_upstream)")
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error("[realtime.ws] client_to_upstream error: %s", exc)
                    try:
                        await upstream.close()
                    except Exception:
                        pass

            async def upstream_to_client() -> None:
                try:
                    while True:
                        msg = await upstream.recv()
                        if isinstance(msg, bytes):
                            await websocket.send_bytes(msg)
                        else:
                            await websocket.send_text(msg)
                except ConnectionClosed:
                    logger.info("[realtime.ws] upstream closed (upstream_to_client)")
                    try:
                        await websocket.close()
                    except Exception:
                        pass
                except WebSocketDisconnect:
                    logger.info("[realtime.ws] client disconnected (upstream_to_client)")
                except Exception as exc:  # pragma: no cover - defensive
                    logger.error("[realtime.ws] upstream_to_client error: %s", exc)
                    try:
                        await websocket.close()
                    except Exception:
                        pass

            await asyncio.gather(client_to_upstream(), upstream_to_client())

    except Exception as exc:  # pragma: no cover - defensive
        logger.error("[realtime.ws] failed to establish upstream connection: %s", exc)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass

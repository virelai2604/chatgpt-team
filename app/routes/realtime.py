# app/routes/realtime.py

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from websockets import connect as ws_connect  # type: ignore
from websockets.exceptions import ConnectionClosed  # type: ignore

from app.core.config import get_settings
from app.utils.logger import relay_log as logger

RAW_OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA", "realtime=v1")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
DEFAULT_REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-realtime")
ALLOWED_REALTIME_MODELS = {
    "gpt-realtime-mini-2025-12-15",
    "gpt-realtime",
    "gpt-realtime-2025-08-28",
    "gpt-realtime-mini",
    "gpt-realtime-mini-2025-10-06",
}

router = APIRouter(
    prefix="/v1",
    tags=["realtime"],
)


def _normalize_openai_base(raw_base: str) -> str:
    base = (raw_base or "").strip().rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base or "https://api.openai.com"


def _build_headers(request: Request | None = None) -> Dict[str, str]:
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured for Realtime sessions",
                    "type": "config_error",
                    "code": "no_api_key",
                }
            },
        )

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    incoming_beta = request.headers.get("OpenAI-Beta") if request else None
    beta = incoming_beta or OPENAI_REALTIME_BETA
    if beta:
        headers["OpenAI-Beta"] = beta

    return headers


async def _post_realtime_sessions(
    request: Request,
    body: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """
    Helper for POST {OPENAI_API_BASE}/v1/realtime/sessions
    """
    openai_base = _normalize_openai_base(RAW_OPENAI_API_BASE)
    url = f"{openai_base}/v1/realtime/sessions"
    headers = _build_headers(request)
    timeout = httpx.Timeout(PROXY_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, headers=headers, json=body or {})
        except httpx.RequestError as exc:
            logger.error("Error calling OpenAI Realtime sessions: %r", exc)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Error calling OpenAI Realtime sessions",
                        "type": "server_error",
                        "code": "upstream_request_error",
                        "extra": {"exception": str(exc)},
                    }
                },
            ) from exc

    try:
        data = resp.json()
    except json.JSONDecodeError:
        data = {"raw": resp.text}

    return resp.status_code, data


@router.post("/realtime/sessions")
async def create_realtime_session(request: Request) -> JSONResponse:
    """
    POST /v1/realtime/sessions – create a Realtime session descriptor.

    If the client omits `model`, we default to REALTIME_MODEL.
    """
    try:
        payload: Any = await request.json()
    except Exception:
        payload = {}

    if not isinstance(payload, dict):
        payload = {}

    payload.setdefault("model", DEFAULT_REALTIME_MODEL)
    model = payload.get("model")

    if model not in ALLOWED_REALTIME_MODELS:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "message": "Unsupported realtime model",
                    "type": "invalid_request_error",
                    "code": "unsupported_model",
                    "param": "model",
                    "extra": {
                        "model": model,
                        "allowed": sorted(ALLOWED_REALTIME_MODELS),
                    },
                }
            },
        )

    status_code, data = await _post_realtime_sessions(request, payload)
    return JSONResponse(status_code=status_code, content=data)


class RealtimeSessionValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., description="Realtime session ID to validate")
    expires_at: Optional[float] = Field(
        default=None,
        description="Optional Unix timestamp (seconds) for session expiry",
    )


@router.post("/realtime/sessions/validate")
async def validate_realtime_session(payload: RealtimeSessionValidateRequest) -> JSONResponse:
    """
    Local-only validation helper for realtime session descriptors.

    Stateless; does not call upstream. Validates shape and expiry.
    """
    now = time.time()
    if payload.expires_at is not None and payload.expires_at <= now:
        return JSONResponse(
            status_code=410,
            content={
                "error": {
                    "message": "Realtime session has expired",
                    "type": "session_error",
                    "code": "session_expired",
                    "extra": {"expires_at": payload.expires_at, "now": now},
                }
            },
        )

    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "session_id": payload.session_id,
            "expires_at": payload.expires_at,
            "now": now,
        },
    )


@router.get("/realtime/sessions/introspect")
async def introspect_realtime_sessions() -> JSONResponse:
    """
    Local-only introspection endpoint for realtime settings.
    """
    openai_base = _normalize_openai_base(RAW_OPENAI_API_BASE)
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "realtime_model": DEFAULT_REALTIME_MODEL,
            "openai_api_base": openai_base,
            "openai_realtime_beta": OPENAI_REALTIME_BETA,
            "now": time.time(),
        },
    )


def _build_ws_base() -> str:
    """
    Convert OPENAI_API_BASE (http/https) into ws/wss base for Realtime WS.
    """
    openai_base = _normalize_openai_base(RAW_OPENAI_API_BASE)
    if openai_base.startswith("https://"):
        return "wss://" + openai_base[len("https://") :]
    if openai_base.startswith("http://"):
        return "ws://" + openai_base[len("http://") :]
    return openai_base


@router.websocket("/realtime/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    """
    WebSocket proxy between client and OpenAI Realtime WS.

    Client connects to:
      ws(s)://relay-host/v1/realtime/ws?model=...&session_id=...

    Relay connects to:
      wss://api.openai.com/v1/realtime?model=...&session_id=...
    """
    await websocket.accept(subprotocol="openai-realtime-v1")

    settings = get_settings()
    if not settings.RELAY_REALTIME_WS_ENABLED:
        await websocket.close(code=1008)
        return

    model = (websocket.query_params.get("model") or DEFAULT_REALTIME_MODEL).strip()
    if model not in ALLOWED_REALTIME_MODELS:
        await websocket.close(code=1008)
        return

    session_id = websocket.query_params.get("session_id")

    ws_base = _build_ws_base()
    url = f"{ws_base}/v1/realtime?model={model}"
    if session_id:
        url += f"&session_id={session_id}"

    if not OPENAI_API_KEY:
        await websocket.close(code=1011)
        return

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "OpenAI-Beta": OPENAI_REALTIME_BETA,
    }

    try:
        async with ws_connect(
            url,
            extra_headers=headers,
            subprotocols=["openai-realtime-v1"],
        ) as upstream_ws:

            async def _client_to_openai() -> None:
                try:
                    while True:
                        msg = await websocket.receive()
                        if msg["type"] == "websocket.disconnect":
                            await upstream_ws.close()
                            break

                        if msg.get("text") is not None:
                            await upstream_ws.send(msg["text"])
                        elif msg.get("bytes") is not None:
                            await upstream_ws.send(msg["bytes"])
                except WebSocketDisconnect:
                    await upstream_ws.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Client->OpenAI WS error: %r", exc)
                    await upstream_ws.close()

            async def _openai_to_client() -> None:
                try:
                    async for message in upstream_ws:
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except ConnectionClosed:
                    await websocket.close()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("OpenAI->Client WS error: %r", exc)
                    await websocket.close()

            await asyncio.gather(_client_to_openai(), _openai_to_client())

    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to establish WS to OpenAI: %r", exc)
        await websocket.close()

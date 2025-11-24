from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Dict, Optional, Tuple

import httpx
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from websockets import connect as ws_connect  # type: ignore
from websockets.exceptions import ConnectionClosed  # type: ignore

from app.utils.logger import relay_log as logger

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA", "realtime=v1")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))
DEFAULT_REALTIME_MODEL = os.getenv("REALTIME_MODEL", "gpt-4.1-mini")

router = APIRouter(
    prefix="/v1",
    tags=["realtime"],
)

# ---------------------------------------------------------------------------
# HTTP Realtime Sessions
# ---------------------------------------------------------------------------


def _build_headers(request: Request) -> Dict[str, str]:
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

    incoming_beta = request.headers.get("OpenAI-Beta")
    beta = incoming_beta or OPENAI_REALTIME_BETA
    if beta:
        headers["OpenAI-Beta"] = beta

    return headers


async def _post_realtime_sessions(
    request: Request,
    body: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    base = OPENAI_API_BASE.rstrip("/")
    url = f"{base}/v1/realtime/sessions"

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
    POST /v1/realtime/sessions

    Proxies to OpenAI's /v1/realtime/sessions and returns the JSON descriptor.
    Typically used to obtain a client_secret and ws URL for Realtime.
    """
    try:
        body = await request.json()
    except Exception:
        body = None

    payload = await _post_realtime_sessions(request, body)
    return JSONResponse(payload, status_code=200)


# ---------------------------------------------------------------------------
# WebSocket Relay Endpoint
# ---------------------------------------------------------------------------


async def _create_session_for_ws(
    model: str,
    session_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a Realtime session for the WS relay itself.

    Similar to _post_realtime_sessions, but independent of FastAPI Request.
    Uses OPENAI_REALTIME_BETA from env and injects "model" + session_config.
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured for Realtime WS",
                    "type": "config_error",
                    "code": "no_api_key",
                }
            },
        )

    base = OPENAI_API_BASE.rstrip("/")
    url = f"{base}/v1/realtime/sessions"

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if OPENAI_REALTIME_BETA:
        headers["OpenAI-Beta"] = OPENAI_REALTIME_BETA

    body: Dict[str, Any] = {"model": model}
    if session_config:
        body.update(session_config)

    logger.info("→ [realtime.ws] POST %s model=%s", url, model)

    async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
        try:
            resp = await client.post(url, headers=headers, json=body)
        except httpx.RequestError as exc:
            logger.error("[realtime.ws] Upstream request error: %s", exc)
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Failed to reach OpenAI Realtime Sessions API (WS)",
                        "type": "upstream_error",
                        "code": "realtime_ws_upstream_unreachable",
                    }
                },
            ) from exc

    try:
        payload = resp.json()
    except Exception:
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Non-JSON response from Realtime Sessions API",
                    "type": "upstream_error",
                    "code": "realtime_ws_non_json",
                }
            },
        )

    if resp.status_code >= 400:
        logger.warning(
            "[realtime.ws] Upstream error %s: %s",
            resp.status_code,
            payload.get("error", {}).get("message", ""),
        )
        raise HTTPException(status_code=resp.status_code, detail=payload)

    return payload


def _extract_ws_auth(payload: Dict[str, Any]) -> Tuple[str, Dict[str, str]]:
    """
    Extract the websocket URL and auth headers from a Realtime sessions payload.

    Handles shapes like:
      { "url": "...", "client_secret": {"value": "..."} }
      { "session": { "url": "...", "client_secret": {"value": "..."} } }
    """
    ws_url = payload.get("url") or payload.get("ws_url")

    if not ws_url and isinstance(payload.get("session"), dict):
        session = payload["session"]
        ws_url = session.get("url") or session.get("ws_url")

    if not ws_url:
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Realtime session response missing websocket URL",
                    "type": "upstream_error",
                    "code": "realtime_ws_no_url",
                }
            },
        )

    auth_headers: Dict[str, str] = {}

    # Look for client_secret in various shapes
    cs = payload.get("client_secret")
    if isinstance(cs, dict):
        token = cs.get("value")
        if isinstance(token, str) and token:
            auth_headers["Authorization"] = f"Bearer {token}"
    elif isinstance(cs, str) and cs:
        auth_headers["Authorization"] = f"Bearer {cs}"

    if "Authorization" not in auth_headers:
        session = payload.get("session")
        if isinstance(session, dict):
            cs2 = session.get("client_secret")
            if isinstance(cs2, dict):
                token2 = cs2.get("value")
                if isinstance(token2, str) and token2:
                    auth_headers["Authorization"] = f"Bearer {token2}"
            elif isinstance(cs2, str) and cs2:
                auth_headers["Authorization"] = f"Bearer {cs2}"

    return ws_url, auth_headers


@router.websocket("/realtime/ws")
async def realtime_ws_relay(websocket: WebSocket):
    """
    WebSocket endpoint: /v1/realtime/ws

    Protocol:

      - Client connects to ws://relay/v1/realtime/ws?model=...
      - OPTIONAL: first message is JSON config:
            {
              "model": "gpt-4.1-mini",
              "session_config": { ... optional Realtime session parameters ... }
            }
        If JSON parse fails *or* it has no "model"/"session_config",
        the first message is treated as a normal Realtime event and
        forwarded to upstream.

      - Relay:
          1. Creates a Realtime session via HTTP.
          2. Connects to OpenAI's Realtime websocket URL.
          3. Pipes messages bidirectionally between client and upstream.

    This keeps the client blind to the upstream OpenAI URL and credentials;
    only the relay holds OPENAI_API_KEY / client_secret.
    """
    await websocket.accept()

    # 1) Determine model & optional session_config
    model = websocket.query_params.get("model") or DEFAULT_REALTIME_MODEL
    session_config: Optional[Dict[str, Any]] = None

    initial_to_forward: Optional[str] = None

    # Try to read an optional config message
    try:
        initial_text = await websocket.receive_text()
    except WebSocketDisconnect:
        await websocket.close()
        return
    except Exception:
        initial_text = None

    if initial_text:
        try:
            cfg = json.loads(initial_text)
        except json.JSONDecodeError:
            # Not JSON → treat as first upstream message
            cfg = None

        if isinstance(cfg, dict) and ("model" in cfg or "session_config" in cfg):
            # Treat as configuration
            if isinstance(cfg.get("model"), str):
                model = cfg["model"]
            if isinstance(cfg.get("session_config"), dict):
                session_config = cfg["session_config"]
            # Do not forward this config message
            initial_to_forward = None
        else:
            # No config keys → treat as first upstream message
            initial_to_forward = initial_text

    # 2) Create a Realtime session for this WS
    payload = await _create_session_for_ws(model, session_config)
    ws_url, upstream_headers = _extract_ws_auth(payload)

    logger.info(
        "[realtime.ws] Opening upstream WS url=%s model=%s headers=%s",
        ws_url,
        model,
        bool(upstream_headers),
    )

    # 3) Connect to upstream WebSocket and relay messages
    try:
        async with ws_connect(ws_url, extra_headers=upstream_headers) as upstream:

            async def client_to_upstream():
                """
                Forward messages from client → upstream Realtime WS.
                """
                # If we had a non-config first message, forward it
                if initial_to_forward is not None:
                    await upstream.send(initial_to_forward)

                try:
                    while True:
                        msg = await websocket.receive()
                        if "text" in msg and msg["text"] is not None:
                            await upstream.send(msg["text"])
                        elif "bytes" in msg and msg["bytes"] is not None:
                            await upstream.send(msg["bytes"])
                        else:
                            # ignore ping/close frames here; upstream_to_client will handle closure
                            continue
                except WebSocketDisconnect:
                    await upstream.close()
                except Exception as exc:
                    logger.error("[realtime.ws] client_to_upstream error: %s", exc)
                    try:
                        await upstream.close()
                    except Exception:
                        pass

            async def upstream_to_client():
                """
                Forward messages from upstream Realtime WS → client.
                """
                try:
                    async for msg in upstream:
                        if isinstance(msg, (bytes, bytearray)):
                            await websocket.send_bytes(msg)
                        else:
                            await websocket.send_text(str(msg))
                except ConnectionClosed:
                    await websocket.close()
                except Exception as exc:
                    logger.error("[realtime.ws] upstream_to_client error: %s", exc)
                    try:
                        await websocket.close()
                    except Exception:
                        pass

            await asyncio.gather(client_to_upstream(), upstream_to_client())

    except Exception as exc:
        logger.error("[realtime.ws] Failed to open upstream WS: %s", exc)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass

# ChatGPT Sync
Repo: chatgpt-team
Base: origin/main
Base commit (merge-base): 46737c8de920dc877599c4194c301fa4a0659a0b
Dirs: app tests static schemas src scripts/src
Root files: project-tree.md pyproject.toml chatgpt_sync.sh AGENTS.md __init__.py generate_tree.py
Mode: changes
Generated: 2026-01-01T19:15:01+07:00

## CHANGE SUMMARY (since 46737c8de920dc877599c4194c301fa4a0659a0b, includes worktree)

```
M	app/routes/realtime.py
```

## PATCH (since 46737c8de920dc877599c4194c301fa4a0659a0b, includes worktree)

```diff
diff --git a/app/routes/realtime.py b/app/routes/realtime.py
index 17dd042..ec375fa 100755
--- a/app/routes/realtime.py
+++ b/app/routes/realtime.py
@@ -422,4 +422,4 @@ async def realtime_ws(websocket: WebSocket) -> None:
             "Realtime WS proxy error: %s",
             {"exception": repr(exc), **upstream_context},
         )
-        await websocket.close(code=1011, reason="Realtime websocket proxy error")
+        await websocket.close(code=1011, reason="Realtime websocket proxy error")
\ No newline at end of file
```

## CURRENT CONTENT OF CHANGED FILES (WORKTREE)

## FILE: app/routes/realtime.py @ WORKTREE
```
# app/routes/realtime.py

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from websockets import connect as ws_connect  # type: ignore
from websockets.exceptions import ConnectionClosed  # type: ignore

from app.core.config import get_settings
from app.utils.logger import relay_log as logger


def _normalize_openai_api_base(raw: str) -> str:
    base = raw.rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base


RAW_OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
OPENAI_API_BASE_SOURCE = "env:OPENAI_API_BASE" if RAW_OPENAI_API_BASE else "default:https://api.openai.com"
OPENAI_API_BASE = _normalize_openai_api_base(RAW_OPENAI_API_BASE or "https://api.openai.com")
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


def _realtime_upstream_context() -> Dict[str, Any]:
    return {
        "openai_api_base": OPENAI_API_BASE,
        "openai_api_base_source": OPENAI_API_BASE_SOURCE,
        "realtime_sessions_url": f"{OPENAI_API_BASE}/v1/realtime/sessions",
    }


def _resolve_port(scheme: Optional[str], port: Optional[int]) -> Optional[int]:
    if port is not None:
        return port
    if scheme == "https":
        return 443
    if scheme == "http":
        return 80
    return None


def _validate_realtime_upstream(request: Request) -> None:
    url = f"{OPENAI_API_BASE}/v1/realtime/sessions"
    parsed_base = urlparse(OPENAI_API_BASE)
    context = _realtime_upstream_context()
    settings = get_settings()

    if parsed_base.scheme not in ("http", "https") or not parsed_base.hostname:
        logger.error("Invalid realtime upstream base: %s", context)
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "Invalid OPENAI_API_BASE for realtime sessions",
                    "type": "config_error",
                    "code": "invalid_api_base",
                    "extra": context,
                }
            },
        )

    relay_host = request.url.hostname
    if relay_host and parsed_base.hostname == relay_host:
        relay_port = _resolve_port(request.url.scheme, request.url.port)
        upstream_port = _resolve_port(parsed_base.scheme, parsed_base.port)
        if upstream_port is None or relay_port == upstream_port:
            loop_context = {
                **context,
                "relay_host": relay_host,
                "relay_port": relay_port,
                "upstream_host": parsed_base.hostname,
                "upstream_port": upstream_port,
            }
            logger.error("Realtime upstream base would loop to relay: %s", loop_context)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "message": "OPENAI_API_BASE resolves to the relay host and would cause a proxy loop",
                        "type": "config_error",
                        "code": "realtime_base_loop",
                        "extra": loop_context,
                    }
                },
            )

    if settings.RELAY_HOST and parsed_base.hostname == settings.RELAY_HOST:
        relay_port = _resolve_port(request.url.scheme, settings.RELAY_PORT)
        upstream_port = _resolve_port(parsed_base.scheme, parsed_base.port)
        if upstream_port is None or relay_port == upstream_port:
            loop_context = {
                **context,
                "relay_host": settings.RELAY_HOST,
                "relay_port": relay_port,
                "upstream_host": parsed_base.hostname,
                "upstream_port": upstream_port,
            }
            logger.error("Realtime upstream base matches relay settings: %s", loop_context)
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "message": "OPENAI_API_BASE matches relay host settings and would cause a proxy loop",
                        "type": "config_error",
                        "code": "realtime_base_loop_settings",
                        "extra": loop_context,
                    }
                },
            )


async def _post_realtime_sessions(
    request: Request,
    body: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any]]:
    """
    Helper for POST {OPENAI_API_BASE}/v1/realtime/sessions
    """
    _validate_realtime_upstream(request)
    url = f"{OPENAI_API_BASE}/v1/realtime/sessions"
    
    headers = _build_headers(request)
    timeout = httpx.Timeout(PROXY_TIMEOUT)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.post(url, headers=headers, json=body or {})
        except httpx.RequestError as exc:
            logger.error("Error calling OpenAI Realtime sessions: %r", exc)
            context = _realtime_upstream_context()
            raise HTTPException(
                status_code=502,
                detail={
                    "error": {
                        "message": "Error calling OpenAI Realtime sessions",
                        "type": "server_error",
                        "code": "upstream_request_error",
                        "extra": {"exception": str(exc), **context},
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

    payload.pop("expires_at", None)

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
    if status_code >= 400:
        upstream_url = f"{OPENAI_API_BASE}/v1/realtime/sessions"
        logger.warning(
            "Realtime session upstream error: status=%s base=%s url=%s source=%s",
            status_code,
            OPENAI_API_BASE,
            upstream_url,
            OPENAI_API_BASE_SOURCE,
        )
        if not isinstance(data, dict):
            data = {"error": {"message": "Realtime upstream error", "type": "upstream_error"}}
        error = data.get("error")
        if not isinstance(error, dict):
            error = {"message": "Realtime upstream error", "type": "upstream_error"}
        extra = error.get("extra")
        if not isinstance(extra, dict):
            extra = {}
        extra.update(
            {
                "openai_api_base": OPENAI_API_BASE,
                "openai_api_base_source": OPENAI_API_BASE_SOURCE,
                "realtime_sessions_url": upstream_url,
            }
        )
        error["extra"] = extra
        data["error"] = error
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
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "realtime_model": DEFAULT_REALTIME_MODEL,
            "openai_api_base": OPENAI_API_BASE,
            "openai_realtime_beta": OPENAI_REALTIME_BETA,
            "now": time.time(),
        },
    )


def _build_ws_base() -> str:
    """
    Convert OPENAI_API_BASE (http/https) into ws/wss base for Realtime WS.
    """
    if OPENAI_API_BASE.startswith("https://"):
        return "wss://" + OPENAI_API_BASE[len("https://") :]
    if OPENAI_API_BASE.startswith("http://"):
        return "ws://" + OPENAI_API_BASE[len("http://") :]
    # Fallback: assume already ws/wss
    return OPENAI_API_BASE


@router.websocket("/realtime/ws")
async def realtime_ws(websocket: WebSocket) -> None:
    """
    WebSocket proxy between client and OpenAI Realtime WS.

    Client connects to:
      ws(s)://relay-host/v1/realtime/ws?model=...&session_id=...

    Relay connects to:
      wss://api.openai.com/v1/realtime?model=...&session_id=...
    """
    subprotocols = websocket.headers.get("sec-websocket-protocol")
    if subprotocols and "openai-realtime-v1" in subprotocols:
        await websocket.accept(subprotocol="openai-realtime-v1")
    else:
        await websocket.accept()

    settings = get_settings()
    if not settings.RELAY_REALTIME_WS_ENABLED:
        await websocket.close(code=1008, reason="Realtime WS is disabled on this relay")
        return

    model = (websocket.query_params.get("model") or DEFAULT_REALTIME_MODEL).strip()
    if model not in ALLOWED_REALTIME_MODELS:
        await websocket.close(code=1008, reason="Unsupported realtime model")
        return

    session_id = (websocket.query_params.get("session_id") or "").strip()
    if not session_id:
        await websocket.close(code=1008, reason="Missing session_id")
        return

    client_auth = websocket.headers.get("authorization") or websocket.headers.get("Authorization")
    if not client_auth and not OPENAI_API_KEY:
        await websocket.close(code=1008, reason="Missing Authorization header or OPENAI_API_KEY")
        return
        
    ws_base = _build_ws_base()
    url = f"{ws_base}/v1/realtime?model={model}&session_id={session_id}"

    auth_header = client_auth or f"Bearer {OPENAI_API_KEY}"
    headers = {
        "Authorization": auth_header,
        "OpenAI-Beta": OPENAI_REALTIME_BETA,
    }

    upstream_context = {
        "openai_api_base": OPENAI_API_BASE,
        "upstream_url": url,
        "model": model,
        "session_id": session_id,
    }
    
    try:
        async with ws_connect(
            url,
            extra_headers=headers,
            subprotocols=["openai-realtime-v1"],
        ) as upstream:

            async def client_to_upstream() -> None:
                while True:
                    message = await websocket.receive_text()
                    await upstream.send(message)

            async def upstream_to_client() -> None:
                async for message in upstream:
                    await websocket.send_text(message)

            await asyncio.gather(client_to_upstream(), upstream_to_client())
    except WebSocketDisconnect:
        return
    except ConnectionClosed as exc:
        logger.warning(
            "Realtime WS upstream closed: %s",
            {"exception": repr(exc), **upstream_context},
        )
        await websocket.close(code=1011, reason="Upstream websocket closed")
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Realtime WS proxy error: %s",
            {"exception": repr(exc), **upstream_context},
        )
        await websocket.close(code=1011, reason="Realtime websocket proxy error")```


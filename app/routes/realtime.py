# app/routes/realtime.py

"""
realtime.py — /v1/realtime/sessions
───────────────────────────────────
Secure proxy for the OpenAI Realtime Sessions API.

This endpoint mints ephemeral session tokens for browser / client-side
use with the Realtime WebSocket or WebRTC APIs, as described in the
Realtime Sessions reference:

  • POST https://api.openai.com/v1/realtime/sessions

The upstream returns a session object that includes a `client_secret`
which can be used by clients to connect directly to:

  • wss://api.openai.com/v1/realtime?model=...

Pattern:

  Frontend:
    POST https://chatgpt-team-relay.onrender.com/v1/realtime/sessions
      { model, modalities, voice, ... }

  Relay (this file):
    - Adds Authorization: Bearer <OPENAI_API_KEY>
    - Optionally adds OpenAI-Organization and OpenAI-Beta
    - POSTs to https://api.openai.com/v1/realtime/sessions
    - Returns the session JSON (including client_secret) unchanged.

  Frontend:
    - Uses client_secret as the Bearer token when connecting
      to the Realtime API via WebSocket or WebRTC.

We intentionally do NOT proxy the Realtime WebSocket itself; the client
connects directly to OpenAI using the ephemeral client_secret.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.logger import relay_log as logger

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA")  # e.g. "realtime=v1"
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))

router = APIRouter(
    prefix="/v1",
    tags=["realtime"],
)


def _build_headers(request: Request) -> Dict[str, str]:
    """
    Build headers for POST /v1/realtime/sessions.

    Security:
      - We NEVER forward any client Authorization header.
      - We ALWAYS use the server-side OPENAI_API_KEY.
      - OpenAI-Beta:
          * Prefer client header if present
          * Otherwise, fall back to OPENAI_REALTIME_BETA env if set
    """
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

    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    # Respect any caller-provided beta header; otherwise, use env toggle.
    incoming_beta = request.headers.get("OpenAI-Beta")
    beta = incoming_beta or OPENAI_REALTIME_BETA
    if beta:
        headers["OpenAI-Beta"] = beta

    return headers


async def _post_realtime_sessions(
    request: Request,
    body: Optional[Dict[str, Any]],
) -> Any:
    """
    Call the upstream OpenAI Realtime Sessions endpoint:

        POST {OPENAI_API_BASE}/v1/realtime/sessions

    with the given JSON body and properly constructed headers.
    """
    base = OPENAI_API_BASE.rstrip("/")
    url = f"{base}/v1/realtime/sessions"

    headers = _build_headers(request)

    # Important: do not log body, as the response includes client_secret.
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
            )

    # Try to preserve upstream JSON error payloads when possible.
    try:
        payload = resp.json()
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


@router.post("/realtime/sessions")
async def create_realtime_session(request: Request):
    """
    POST /v1/realtime/sessions

    Create an ephemeral API token for use in client-side applications
    with the Realtime API. Mirrors the official REST endpoint:

        POST https://api.openai.com/v1/realtime/sessions

    The request body usually includes fields like:

      - model
      - modalities
      - instructions
      - voice
      - input_audio_format
      - output_audio_format
      - input_audio_transcription
      - turn_detection
      - tools

    We forward the JSON body as-is to OpenAI and return the upstream
    JSON response unchanged, including the `client_secret`.
    """
    try:
        body = await request.json()
    except Exception:
        # Body may be optional; treat non-JSON as empty object.
        body = None

    payload = await _post_realtime_sessions(request, body)
    # Do NOT log payload (contains client_secret).
    return JSONResponse(payload, status_code=200)

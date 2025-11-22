from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.logger import relay_log as logger

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_REALTIME_BETA = os.getenv("OPENAI_REALTIME_BETA")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", os.getenv("RELAY_TIMEOUT", "120")))

router = APIRouter(
    prefix="/v1",
    tags=["realtime"],
)


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
) -> Any:
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
            )

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
    try:
        body = await request.json()
    except Exception:
        body = None

    payload = await _post_realtime_sessions(request, body)
    return JSONResponse(payload, status_code=200)

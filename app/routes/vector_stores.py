from __future__ import annotations

import json  # <-- IMPORTANT: needed for json.loads
import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from app.utils.logger import relay_log as logger

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

router = APIRouter(
    prefix="/v1",
    tags=["vector_stores"],
)


async def _vs_request(method: str, path: str, request: Request) -> JSONResponse:
    """
    Helper to forward vector store requests to OpenAI.

    - Uses OPENAI_API_BASE + full /v1/vector_stores path.
    - Sends JSON body when available.
    - Returns JSONResponse with upstream's status + body.
    """
    base = OPENAI_API_BASE.rstrip("/")
    url = f"{base}{path}"

    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured for Vector Stores",
                    "type": "config_error",
                    "code": "no_api_key",
                }
            },
        )

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    body = await request.body()
    json_data = None
    if body:
        try:
            json_data = json.loads(body.decode("utf-8"))
        except Exception:
            logger.warning(
                "[vector_stores] Failed to parse JSON body for %s %s; sending raw.",
                method,
                path,
            )
            json_data = None

    timeout = httpx.Timeout(30.0)

    logger.info("[vector_stores] %s %s", method, url)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(
                method,
                url,
                headers=headers,
                json=json_data if json_data is not None else None,
            )
    except httpx.RequestError as exc:
        logger.error("[vector_stores] Upstream request error: %s", exc)
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Error contacting upstream OpenAI Vector Stores API",
                    "type": "upstream_connection_error",
                }
            },
        ) from exc

    try:
        data = resp.json()
    except Exception:
        logger.error("[vector_stores] Invalid JSON from upstream: %s", resp.text)
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "Invalid JSON from upstream vector store",
                    "type": "upstream_error",
                }
            },
        )

    return JSONResponse(status_code=resp.status_code, content=data)


@router.get("/vector_stores")
async def list_vector_stores(request: Request) -> JSONResponse:
    return await _vs_request("GET", "/v1/vector_stores", request)


@router.post("/vector_stores")
async def create_vector_store(request: Request) -> JSONResponse:
    return await _vs_request("POST", "/v1/vector_stores", request)


@router.get("/vector_stores/{vs_id}")
async def retrieve_vector_store(vs_id: str, request: Request) -> JSONResponse:
    return await _vs_request("GET", f"/v1/vector_stores/{vs_id}", request)

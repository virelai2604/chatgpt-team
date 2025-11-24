from __future__ import annotations

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
    base = OPENAI_API_BASE.rstrip("/")
    url = f"{base}{path}"

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
            json_data = None

    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.request(method, url, headers=headers, json=json_data)

    try:
        data = resp.json()
    except Exception:
        raise HTTPException(
            status_code=502,
            detail={"error": {"message": "Invalid JSON from upstream vector store"}},
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

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings

# BIFL retriever bridge — read-only first milestone (health, search, fetch).
# Write/destructive tools (ingest, rebuild, delete, purge) are intentionally
# NOT implemented here yet, per the BIFL governance: read-only first, add
# preview_ingest next, then app-only writes only after audit logging exists.
router = APIRouter(prefix="/v1/bifl", tags=["bifl"])

_settings = get_settings()


def _vector_store_id() -> Optional[str]:
    return os.getenv("BIFL_VECTOR_STORE_ID") or None


def _upstream_base() -> str:
    base = (getattr(_settings, "OPENAI_API_BASE", None) or "https://api.openai.com").rstrip("/")
    if base.endswith("/v1"):
        base = base[: -len("/v1")]
    return base


def _upstream_headers() -> Dict[str, str]:
    key = getattr(_settings, "OPENAI_API_KEY", "") or ""
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


@router.get("/health")
async def bifl_health() -> Dict[str, Any]:
    """Read-only: report BIFL retriever status. Safe, no upstream call."""
    vs = _vector_store_id()
    return {
        "object": "bifl.health",
        "status": "ok",
        "backend": "ai.lafiel.me",
        "vector_store_configured": bool(vs),
        "vector_store_id": vs,
        "openai_key_configured": bool(getattr(_settings, "OPENAI_API_KEY", "")),
    }


class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query over distilled BIFL knowledge.")
    limit: int = Field(default=5, ge=1, le=20)


@router.post("/search")
async def bifl_search(req: SearchRequest):
    """
    Read-only: semantic search over the distilled-knowledge OpenAI Vector Store.

    Requires BIFL_VECTOR_STORE_ID to be set (sync distilled chunks to an OpenAI
    Vector Store first). Degrades gracefully with a clear note if unconfigured.
    """
    vs = _vector_store_id()
    if not vs:
        return JSONResponse(
            {
                "object": "bifl.search",
                "query": req.query,
                "results": [],
                "note": "BIFL_VECTOR_STORE_ID not configured. Sync distilled chunks "
                        "to an OpenAI Vector Store, then set BIFL_VECTOR_STORE_ID.",
            }
        )

    url = f"{_upstream_base()}/v1/vector_stores/{vs}/search"
    payload = {"query": req.query, "max_num_results": req.limit}
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(url, headers=_upstream_headers(), json=payload)
    except httpx.HTTPError as exc:
        return JSONResponse(
            status_code=502,
            content={"object": "bifl.search", "error": f"upstream error: {type(exc).__name__}"},
        )

    try:
        data = r.json()
    except Exception:
        data = {}
    results: List[Dict[str, Any]] = []
    for item in (data.get("data") or []):
        results.append(
            {
                "file_id": item.get("file_id"),
                "filename": item.get("filename"),
                "score": item.get("score"),
                "content": item.get("content"),
            }
        )
    return {"object": "bifl.search", "query": req.query, "results": results}


class FetchRequest(BaseModel):
    file_id: str = Field(..., description="OpenAI file id (or BIFL record id) to fetch.")


@router.post("/fetch")
async def bifl_fetch(req: FetchRequest):
    """Read-only: fetch a record's metadata by file id from the hosted store."""
    url = f"{_upstream_base()}/v1/files/{req.file_id}"
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.get(url, headers=_upstream_headers())
    except httpx.HTTPError as exc:
        return JSONResponse(
            status_code=502,
            content={"object": "bifl.fetch", "error": f"upstream error: {type(exc).__name__}"},
        )
    try:
        record = r.json()
    except Exception:
        record = {"raw": r.text}
    return {"object": "bifl.fetch", "file_id": req.file_id, "record": record}

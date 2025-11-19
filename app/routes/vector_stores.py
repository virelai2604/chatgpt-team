from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException, Request

from app.utils.logger import relay_log as logger

# ---------------------------------------------------------------------------
# OpenAI config for vector stores / assistants API
# ---------------------------------------------------------------------------

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_ASSISTANTS_BETA = os.getenv("OPENAI_ASSISTANTS_BETA", "assistants=v2")
PROXY_TIMEOUT = float(os.getenv("PROXY_TIMEOUT", "120"))

router = APIRouter(
    prefix="/v1/vector_stores",
    tags=["vector_stores"],
)


def _build_headers(request: Request) -> Dict[str, str]:
    """
    Build headers for vector store calls:

    - Authorization and optional organization
    - OpenAI-Beta:
        * Prefer incoming header (from SDK/client)
        * Fallback to OPENAI_ASSISTANTS_BETA env (e.g. 'assistants=v2')
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": "OPENAI_API_KEY is not configured",
                    "type": "config_error",
                    "code": "no_api_key",
                }
            },
        )

    headers: Dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    # Organization – prefer request header, then env
    request_org = request.headers.get("OpenAI-Organization")
    org_id = request_org or OPENAI_ORG_ID
    if org_id:
        headers["OpenAI-Organization"] = org_id

    # Assistants / vector store beta header – prefer incoming, else env
    incoming_beta = request.headers.get("OpenAI-Beta")
    beta_header = incoming_beta or OPENAI_ASSISTANTS_BETA
    if beta_header:
        headers["OpenAI-Beta"] = beta_header

    return headers


async def _request_json(
    request: Request,
    method: str,
    path_suffix: str,
    *,
    json: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Generic JSON proxy to OpenAI's Vector Stores API.

    path_suffix is appended after '/v1/vector_stores'.
    """
    url = f"{OPENAI_API_BASE}/v1/vector_stores{path_suffix}"

    headers = _build_headers(request)

    logger.info("→ [vector_stores] %s %s", method, url)

    async with httpx.AsyncClient(timeout=PROXY_TIMEOUT) as client:
        resp = await client.request(
            method,
            url,
            headers=headers,
            json=json,
            params=params,
        )

    if resp.status_code >= 400:
        # Try to preserve OpenAI error payload as-is
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

        logger.error(
            "✖ [vector_stores] %s %s → %s %s",
            method,
            url,
            resp.status_code,
            resp.text,
        )
        raise HTTPException(status_code=resp.status_code, detail=payload)

    return resp.json()


# ---------------------------------------------------------------------------
# Vector store core operations
# ---------------------------------------------------------------------------


@router.post("")
async def create_vector_store(request: Request):
    """
    Create a vector store.

    Mirrors POST /v1/vector_stores as in the official API reference and
    openai-python 2.8.x client.
    """
    body = await request.json()
    return await _request_json(request, "POST", "", json=body)


@router.get("")
async def list_vector_stores(request: Request):
    """
    List vector stores.

    Mirrors GET /v1/vector_stores.
    """
    params = dict(request.query_params)
    return await _request_json(request, "GET", "", params=params)


@router.get("/{vector_store_id}")
async def retrieve_vector_store(vector_store_id: str, request: Request):
    """
    Retrieve a single vector store.

    Mirrors GET /v1/vector_stores/{id}.
    """
    return await _request_json(request, "GET", f"/{vector_store_id}")


@router.delete("/{vector_store_id}")
async def delete_vector_store(vector_store_id: str, request: Request):
    """
    Delete a vector store.

    Mirrors DELETE /v1/vector_stores/{id}.
    """
    return await _request_json(request, "DELETE", f"/{vector_store_id}")


# ---------------------------------------------------------------------------
# Vector store files
# ---------------------------------------------------------------------------


@router.get("/{vector_store_id}/files")
async def list_vector_store_files(vector_store_id: str, request: Request):
    """
    List files in a vector store.

    Mirrors GET /v1/vector_stores/{vector_store_id}/files.
    """
    params = dict(request.query_params)
    return await _request_json(
        request,
        "GET",
        f"/{vector_store_id}/files",
        params=params,
    )


@router.post("/{vector_store_id}/files")
async def create_vector_store_file(vector_store_id: str, request: Request):
    """
    Add a file to a vector store.

    For this relay and its tests we simply forward JSON.
    """
    body = await request.json()
    return await _request_json(
        request,
        "POST",
        f"/{vector_store_id}/files",
        json=body,
    )


@router.get("/{vector_store_id}/files/{file_id}")
async def retrieve_vector_store_file(
    vector_store_id: str,
    file_id: str,
    request: Request,
):
    """
    Retrieve a file within a vector store.

    Mirrors GET /v1/vector_stores/{vector_store_id}/files/{file_id}.
    """
    return await _request_json(
        request,
        "GET",
        f"/{vector_store_id}/files/{file_id}",
    )


@router.delete("/{vector_store_id}/files/{file_id}")
async def delete_vector_store_file(
    vector_store_id: str,
    file_id: str,
    request: Request,
):
    """
    Delete a file from a vector store.

    Mirrors DELETE /v1/vector_stores/{vector_store_id}/files/{file_id}.
    """
    return await _request_json(
        request,
        "DELETE",
        f"/{vector_store_id}/files/{file_id}",
    )


# ---------------------------------------------------------------------------
# Vector store file batches
# ---------------------------------------------------------------------------


@router.get("/{vector_store_id}/file_batches")
async def list_file_batches(vector_store_id: str, request: Request):
    """
    List file batches for a vector store.

    Mirrors GET /v1/vector_stores/{vector_store_id}/file_batches.
    """
    params = dict(request.query_params)
    return await _request_json(
        request,
        "GET",
        f"/{vector_store_id}/file_batches",
        params=params,
    )


@router.post("/{vector_store_id}/file_batches")
async def create_file_batch(vector_store_id: str, request: Request):
    """
    Create a file batch for a vector store.

    Mirrors POST /v1/vector_stores/{vector_store_id}/file_batches.
    """
    body = await request.json()
    return await _request_json(
        request,
        "POST",
        f"/{vector_store_id}/file_batches",
        json=body,
    )


@router.get("/{vector_store_id}/file_batches/{batch_id}")
async def retrieve_file_batch(
    vector_store_id: str,
    batch_id: str,
    request: Request,
):
    """
    Retrieve a file batch for a vector store.

    Mirrors GET /v1/vector_stores/{vector_store_id}/file_batches/{batch_id}.
    """
    return await _request_json(
        request,
        "GET",
        f"/{vector_store_id}/file_batches/{batch_id}",
    )


@router.delete("/{vector_store_id}/file_batches/{batch_id}")
async def cancel_file_batch(
    vector_store_id: str,
    batch_id: str,
    request: Request,
):
    """
    Cancel a file batch for a vector store.

    Mirrors DELETE /v1/vector_stores/{vector_store_id}/file_batches/{batch_id}.
    """
    return await _request_json(
        request,
        "DELETE",
        f"/{vector_store_id}/file_batches/{batch_id}",
    )

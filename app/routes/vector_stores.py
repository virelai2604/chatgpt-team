import json
import os

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1/vector_stores", tags=["vector_stores"])

OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID", "")
RELAY_TIMEOUT = float(os.getenv("RELAY_TIMEOUT", "120"))

# For vector stores (historically tied to Assistants v2), some stacks require:
#   OpenAI-Beta: assistants=v2
# The official SDKs add this themselves when talking directly to api.openai.com;
# here we allow you to configure it explicitly.
OPENAI_ASSISTANTS_BETA = os.getenv("OPENAI_ASSISTANTS_BETA", "")


def _base_url(path: str) -> str:
    return f"{OPENAI_API_BASE.rstrip('/')}{path}"


def auth_headers(request: Request | None = None) -> dict:
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    headers: dict[str, str] = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    if OPENAI_ORG_ID:
        headers["OpenAI-Organization"] = OPENAI_ORG_ID

    beta = OPENAI_ASSISTANTS_BETA.strip()
    if not beta and request is not None:
        # Fallback: propagate any beta header the client sent (e.g. from SDK)
        beta = request.headers.get("OpenAI-Beta", "").strip()

    if beta:
        headers["OpenAI-Beta"] = beta

    return headers


async def _proxy(
    method: str,
    path: str,
    request: Request | None = None,
    body: dict | None = None,
) -> JSONResponse:
    async with httpx.AsyncClient(timeout=RELAY_TIMEOUT) as client:
        url = _base_url(path)
        kwargs = {
            "headers": auth_headers(request),
        }
        if body is not None:
            kwargs["content"] = json.dumps(body)

        upstream = await client.request(method, url, **kwargs)

    if upstream.is_error:
        raise HTTPException(
            status_code=upstream.status_code,
            detail=upstream.text,
        )

    return JSONResponse(
        status_code=upstream.status_code,
        content=upstream.json(),
    )


@router.get("")
async def list_vector_stores(request: Request) -> JSONResponse:
    """
    GET /v1/vector_stores
    """
    return await _proxy("GET", "/v1/vector_stores", request=request)


@router.post("")
async def create_vector_store(request: Request) -> JSONResponse:
    """
    POST /v1/vector_stores

    Mirrors client.vector_stores.create(...) from the official SDKs. 
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    return await _proxy("POST", "/v1/vector_stores", request=request, body=body)


@router.get("/{vector_store_id}")
async def retrieve_vector_store(vector_store_id: str, request: Request) -> JSONResponse:
    """
    GET /v1/vector_stores/{vector_store_id}
    """
    path = f"/v1/vector_stores/{vector_store_id}"
    return await _proxy("GET", path, request=request)


@router.post("/{vector_store_id}/files")
async def create_vector_store_file(vector_store_id: str, request: Request) -> JSONResponse:
    """
    POST /v1/vector_stores/{vector_store_id}/files

    This attaches a file to an existing vector store. It maps to
    client.vector_stores.files.create(...) in the Python/Node SDKs. 
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    path = f"/v1/vector_stores/{vector_store_id}/files"
    return await _proxy("POST", path, request=request, body=body)


@router.get("/{vector_store_id}/files")
async def list_vector_store_files(vector_store_id: str, request: Request) -> JSONResponse:
    """
    GET /v1/vector_stores/{vector_store_id}/files
    """
    path = f"/v1/vector_stores/{vector_store_id}/files"
    return await _proxy("GET", path, request=request)


@router.post("/{vector_store_id}/file_batches")
async def create_vector_store_file_batch(
    vector_store_id: str, request: Request
) -> JSONResponse:
    """
    POST /v1/vector_stores/{vector_store_id}/file_batches

    Equivalent to client.vector_stores.file_batches.create(...) or
    create_and_poll(...) at the REST level. 
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    path = f"/v1/vector_stores/{vector_store_id}/file_batches"
    return await _proxy("POST", path, request=request, body=body)


@router.get("/{vector_store_id}/file_batches/{batch_id}")
async def retrieve_vector_store_file_batch(
    vector_store_id: str,
    batch_id: str,
    request: Request,
) -> JSONResponse:
    """
    GET /v1/vector_stores/{vector_store_id}/file_batches/{batch_id}
    """
    path = f"/v1/vector_stores/{vector_store_id}/file_batches/{batch_id}"
    return await _proxy("GET", path, request=request)

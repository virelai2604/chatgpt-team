from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.api.forward_openai import forward_openai_method_path, forward_openai_request

router = APIRouter(prefix="/v1", tags=["files"])


async def _is_user_data_file(file_id: str, request: Request) -> bool:
    """
    Best-effort guardrail:
    - If we can confirm purpose == 'user_data', block content download.
    - If we cannot confirm (metadata fetch fails), do not introduce new 5xx.
    """
    try:
        meta = await forward_openai_method_path(
            "GET",
            f"/v1/files/{file_id}",
            inbound_headers=request.headers,
        )
    except HTTPException:
        return False
    except Exception:
        return False

    return isinstance(meta, dict) and str(meta.get("purpose", "")).strip().lower() == "user_data"


@router.get("/files")
async def list_files(request: Request) -> Response:
    return await forward_openai_request(request)


@router.post("/files")
async def create_file(request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.delete("/files/{file_id}")
async def delete_file(file_id: str, request: Request) -> Response:
    return await forward_openai_request(request)


@router.get("/files/{file_id}/content")
async def retrieve_file_content(file_id: str, request: Request) -> Response:
    if await _is_user_data_file(file_id, request):
        # Tests accept 400 or 403, but 403 is semantically correct here.
        return JSONResponse(
            status_code=403,
            content={"detail": "Not allowed to download files with purpose 'user_data' via this relay."},
        )
    return await forward_openai_request(request)

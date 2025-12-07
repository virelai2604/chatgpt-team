# app/routes/files.py

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, HTTPException, UploadFile, File, Query

from app.core.http_client import get_async_openai_client
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["files"])


@router.get("/files")
async def list_files(
    purpose: Optional[str] = Query(None, description="Optional OpenAI file purpose filter"),
) -> Any:
    """
    List files from the OpenAI Files API.

    Equivalent to:
        client.files.list(purpose=purpose)
    """
    client = get_async_openai_client()
    logger.info("Incoming /v1/files list request (purpose=%s)", purpose)
    result = await client.files.list(purpose=purpose)
    # SDK v2 returns a pydantic-like object; FastAPI can usually serialize it directly.
    return result


@router.post("/files")
async def upload_file(
    file: UploadFile = File(...),
    purpose: str = Query("assistants", description="File purpose, e.g. 'assistants', 'fine-tune'"),
) -> Any:
    """
    Upload a file to the OpenAI Files API.

    Equivalent to:
        client.files.create(file=..., purpose=purpose)
    """
    client = get_async_openai_client()
    logger.info("Incoming /v1/files upload request (filename=%s, purpose=%s)", file.filename, purpose)

    try:
        contents = await file.read()
        # Note: the official v2 SDK expects a file-like; using bytes is acceptable with 'file' param.
        result = await client.files.create(
            file=(file.filename, contents),
            purpose=purpose,
        )
        return result
    except Exception as exc:
        logger.exception("Failed to upload file to OpenAI: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to upload file to OpenAI") from exc


@router.get("/files/{file_id}")
async def retrieve_file(file_id: str) -> Any:
    """
    Retrieve file metadata.

    Equivalent to:
        client.files.retrieve(file_id)
    """
    client = get_async_openai_client()
    logger.info("Incoming /v1/files/%s retrieve request", file_id)
    result = await client.files.retrieve(file_id)
    return result


@router.delete("/files/{file_id}")
async def delete_file(file_id: str) -> Any:
    """
    Delete a file.

    Equivalent to:
        client.files.delete(file_id)
    """
    client = get_async_openai_client()
    logger.info("Incoming /v1/files/%s delete request", file_id)
    result = await client.files.delete(file_id)
    return result

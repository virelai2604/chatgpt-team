from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.get("")
async def list_files(request: Request):
    """
    List files – forwards GET /v1/files to OpenAI.

    The forwarder reads request.method (GET) and passes query params + headers on.
    """
    return await forward_openai_request(request=request)


@router.post("")
async def create_file(request: Request):
    """
    Create/upload file – forwards POST /v1/files.

    The forwarder:
    - Reads the raw body bytes.
    - Detects multipart/form-data vs JSON from Content-Type.
    - For multipart/form-data: forwards raw body.
    - For application/json: forwards parsed JSON via json=.
    """
    return await forward_openai_request(request=request)


@router.get("/{file_id}")
async def retrieve_file(request: Request, file_id: str):
    """
    Retrieve a single file's metadata – forwards GET /v1/files/{file_id}.
    """
    return await forward_openai_request(request=request)


@router.delete("/{file_id}")
async def delete_file(request: Request, file_id: str):
    """
    Delete a file – forwards DELETE /v1/files/{file_id}.
    """
    return await forward_openai_request(request=request)

# app/routes/files.py

from fastapi import APIRouter, Request

from app.api.forward_openai import forward_openai_request

router = APIRouter()


@router.get("/v1/files", tags=["files"])
async def list_files(request: Request):
    """
    List files – simple passthrough to OpenAI /v1/files.
    """
    return await forward_openai_request(request)


@router.post("/v1/files", tags=["files"])
async def create_file(request: Request):
    """
    Create/upload a file.

    Important: we do NOT declare UploadFile/Form parameters here.
    That would force FastAPI to validate the multipart body and can
    produce a 422 before we ever hit the relay.

    Instead, we pass the raw multipart/form-data body through to OpenAI.
    """
    return await forward_openai_request(request)


@router.get("/v1/files/{file_id}", tags=["files"])
async def retrieve_file(request: Request, file_id: str):
    """
    Retrieve file metadata.
    """
    return await forward_openai_request(request)


@router.delete("/v1/files/{file_id}", tags=["files"])
async def delete_file(request: Request, file_id: str):
    """
    Delete a file.
    """
    return await forward_openai_request(request)


@router.get("/v1/files/{file_id}/content", tags=["files"])
async def download_file_content(request: Request, file_id: str):
    """
    Download full file content.

    We still use the same generic forwarder; it will proxy the binary
    response body and headers back to the client.
    """
    return await forward_openai_request(request)

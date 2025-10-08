from fastapi import APIRouter, Request, UploadFile, File
from app.api.forward import forward_openai
from app.utils.db_logger import save_file_upload
import os

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def files_collection(request: Request, file: UploadFile = File(None)):
    # Structured log for file upload
    if file is not None:
        try:
            content = await file.read()
            save_file_upload(
                filename=file.filename,
                filetype=os.path.splitext(file.filename)[-1],
                mimetype=file.content_type,
                content=content,
                extra_json="{}"
            )
        except Exception as ex:
            print("BIFL log error (file upload):", ex)
    # Universal raw logging handled in forward_openai
    return await forward_openai(request, "/v1/files")

@router.api_route("/{file_id}", methods=["GET", "DELETE"])
async def file_resource(request: Request, file_id: str):
    return await forward_openai(request, f"/v1/files/{file_id}")

@router.api_route("/{file_id}/content", methods=["GET"])
async def file_content(request: Request, file_id: str):
    return await forward_openai(request, f"/v1/files/{file_id}/content")

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from app.api.forward import forward_openai
from app.utils.db_logger import save_chat_request

router = APIRouter()

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    # Structured logging for file upload
    try:
        save_chat_request(
            role="user",
            content=f"Uploading file: {file.filename}",
            function_call_json="",
            metadata_json="{'filename': '%s'}" % file.filename
        )
    except Exception as ex:
        print("BIFL log error (file upload):", ex)
    return await forward_openai(request, "/v1/files", files={"file": file})

@router.get("/")
async def list_files(request: Request):
    return await forward_openai(request, "/v1/files")

@router.get("/{file_id}")
async def retrieve_file(request: Request, file_id: str):
    return await forward_openai(request, f"/v1/files/{file_id}")

@router.delete("/{file_id}")
async def delete_file(request: Request, file_id: str):
    return await forward_openai(request, f"/v1/files/{file_id}")

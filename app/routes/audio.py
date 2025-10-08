from fastapi import APIRouter, Request, UploadFile, File, Form
from app.api.forward import forward_openai
from app.utils.db_logger import save_file_upload
import os

router = APIRouter()

@router.api_route("/speech", methods=["POST"])
async def audio_speech(request: Request, file: UploadFile = File(None)):
    # Structured file logging (if UploadFile is used directly)
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
            print("BIFL log error (audio speech):", ex)
    # Universal raw logging handled in forward_openai
    return await forward_openai(request, "/v1/audio/speech")

@router.api_route("/transcriptions", methods=["POST"])
async def audio_transcriptions(request: Request, file: UploadFile = File(None)):
    # Structured file logging
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
            print("BIFL log error (audio transcriptions):", ex)
    return await forward_openai(request, "/v1/audio/transcriptions")

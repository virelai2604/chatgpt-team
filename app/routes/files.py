from fastapi import APIRouter, Request, UploadFile, File
from app.api.forward import forward_openai
import os

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def files_collection(request: Request, file: UploadFile = File(None)):
    return await forward_openai(request, "/v1/files")

@router.api_route("/{file_id}", methods=["GET", "DELETE"])
async def file_resource(request: Request, file_id: str):
    return await forward_openai(request, f"/v1/files/{file_id}")

@router.api_route("/{file_id}/content", methods=["GET"])
async def file_content(request: Request, file_id: str):
    return await forward_openai(request, f"/v1/files/{file_id}/content")

from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def files_root(request: Request):
    return await forward_openai(request, "files")

@router.api_route("/{file_id}", methods=["GET", "DELETE"])
async def files_by_id(request: Request, file_id: str):
    return await forward_openai(request, f"files/{file_id}")

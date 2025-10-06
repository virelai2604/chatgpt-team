from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def batch_create(request: Request):
    return await forward_openai(request, "batch")

@router.api_route("/{batch_id}", methods=["GET"])
async def batch_by_id(request: Request, batch_id: str):
    return await forward_openai(request, f"batch/{batch_id}")
    

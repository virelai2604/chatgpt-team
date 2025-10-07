from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def batch_create(request: Request):
    return await forward_openai(request, "/v1/batch")

@router.api_route("/{batch_id}", methods=["GET"])
async def batch_by_id(request: Request, batch_id: str):
    return await forward_openai(request, f"/v1/batch/{batch_id}")

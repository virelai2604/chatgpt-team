from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET"])
async def list_models(request: Request):
    return await forward_openai(request, "models")

@router.api_route("/{model_id}", methods=["GET", "DELETE"])
async def model_by_id(request: Request, model_id: str):
    return await forward_openai(request, f"models/{model_id}")

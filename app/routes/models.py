from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET"])
async def list_models(request: Request):
    return await forward_openai(request, "/v1/models")

@router.api_route("/{model}", methods=["GET"])
async def retrieve_model(request: Request, model: str):
    return await forward_openai(request, f"/v1/models/{model}")


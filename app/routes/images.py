from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/generations", methods=["POST"])
async def image_generations(request: Request):
    return await forward_openai(request, "/v1/images/generations")

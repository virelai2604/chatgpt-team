from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def embeddings(request: Request):
    return await forward_openai(request, "embeddings")

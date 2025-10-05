from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def handle_embeddings(request: Request):
    return await forward_openai(request, "embeddings")

@router.api_route("/{item_id}", methods=["GET", "POST", "PATCH", "DELETE"])
async def handle_embeddings_by_id(request: Request, item_id: str):
    return await forward_openai(request, f"embeddings/{item_id}")

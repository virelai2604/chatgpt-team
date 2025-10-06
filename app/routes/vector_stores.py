from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def vector_stores_root(request: Request):
    return await forward_openai(request, "vector_stores")

@router.api_route("/{vector_store_id}", methods=["GET", "POST", "DELETE", "PATCH"])
async def vector_store_by_id(request: Request, vector_store_id: str):
    return await forward_openai(request, f"vector_stores/{vector_store_id}")

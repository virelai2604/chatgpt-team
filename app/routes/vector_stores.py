from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def vector_stores(request: Request):
    return await forward_openai(request, "/v1/vector_stores")

@router.api_route("/{vector_store_id}", methods=["GET"])
async def vector_store_by_id(request: Request, vector_store_id: str):
    return await forward_openai(request, f"/v1/vector_stores/{vector_store_id}")

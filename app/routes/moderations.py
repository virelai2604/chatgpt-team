from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def handle_moderations(request: Request):
    return await forward_openai(request, "moderations")

@router.api_route("/{item_id}", methods=["GET", "POST", "PATCH", "DELETE"])
async def handle_moderations_by_id(request: Request, item_id: str):
    return await forward_openai(request, f"moderations/{item_id}")

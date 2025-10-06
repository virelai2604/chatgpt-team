from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def assistants_root(request: Request):
    return await forward_openai(request, "assistants")

@router.api_route("/{assistant_id}", methods=["GET", "POST", "DELETE", "PATCH"])
async def assistants_by_id(request: Request, assistant_id: str):
    return await forward_openai(request, f"assistants/{assistant_id}")

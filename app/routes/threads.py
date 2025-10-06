from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def threads_create(request: Request):
    return await forward_openai(request, "threads")

@router.api_route("/{thread_id}", methods=["GET", "POST", "DELETE", "PATCH"])
async def threads_by_id(request: Request, thread_id: str):
    return await forward_openai(request, f"threads/{thread_id}")

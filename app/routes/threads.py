from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def threads(request: Request):
    return await forward_openai(request, "/v1/threads")

@router.api_route("/{thread_id}", methods=["GET", "POST"])
async def thread_by_id(request: Request, thread_id: str):
    return await forward_openai(request, f"/v1/threads/{thread_id}")

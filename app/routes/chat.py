from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/completions", methods=["POST"])
async def chat_completions(request: Request):
    return await forward_openai(request, "chat/completions")

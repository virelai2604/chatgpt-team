from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.post("/completions")
async def create_chat_completion(request: Request):
    return await forward_openai(request, "chat/completions")

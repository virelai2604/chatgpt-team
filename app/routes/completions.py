from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.post("/")
async def legacy_completion(request: Request):
    return await forward_openai(request, "completions")

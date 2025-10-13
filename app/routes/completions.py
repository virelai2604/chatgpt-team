from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter(prefix="/completions")

@router.post("")
async def completions(request: Request):
    return await forward_openai(request, "/v1/completions")

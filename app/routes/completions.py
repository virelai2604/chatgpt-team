from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["POST"])
async def completions(request: Request):
    return await forward_openai(request, "/v1/completions")

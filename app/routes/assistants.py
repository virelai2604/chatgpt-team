from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def assistants(request: Request):
    return await forward_openai(request, "/v1/assistants")

@router.api_route("/{assistant_id}", methods=["GET", "POST", "DELETE"])
async def assistant_by_id(request: Request, assistant_id: str):
    return await forward_openai(request, f"/v1/assistants/{assistant_id}")

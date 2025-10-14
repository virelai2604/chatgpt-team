from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def tools(request: Request):
    """Proxy for /v1/tools endpoint."""
    return await forward_openai(request, "/v1/tools")

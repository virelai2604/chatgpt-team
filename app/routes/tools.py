from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def tools_root(request: Request):
    return await forward_openai(request, "tools")

@router.api_route("/{tool_id}", methods=["GET", "DELETE"])
async def tools_by_id(request: Request, tool_id: str):
    return await forward_openai(request, f"tools/{tool_id}")

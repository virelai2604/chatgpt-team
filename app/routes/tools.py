from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/", methods=["GET", "POST"])
async def handle_tools(request: Request):
    return await forward_openai(request, "tools")

@router.api_route("/{tool_id}", methods=["GET", "POST", "PATCH", "DELETE"])
async def handle_tool_by_id(request: Request, tool_id: str):
    return await forward_openai(request, f"tools/{tool_id}")

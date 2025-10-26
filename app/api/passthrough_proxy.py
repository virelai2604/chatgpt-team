from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai

router = APIRouter(prefix="/v1", tags=["Passthrough"])

@router.api_route("/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def passthrough(request: Request, path: str):
    """
    Universal fallback proxy that forwards any unmatched /v1/* route
    to the official OpenAI API endpoint.
    Must always be registered LAST.
    """
    endpoint = f"/v1/{path}"
    return await forward_openai(request, endpoint)
from fastapi import APIRouter, Request
from app.api.forward_openai import forward_openai

router = APIRouter(prefix="/v1", tags=["Passthrough"])

@router.api_route("/{path:path}", methods=["GET","POST","PUT","PATCH","DELETE"])
async def passthrough(request: Request, path: str):
    """
    Universal fallback proxy that forwards any unmatched /v1/* route
    to the official OpenAI API endpoint.
    Must always be registered LAST.
    """
    endpoint = f"/v1/{path}"
    return await forward_openai(request, endpoint)

from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/v1/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def passthrough(request: Request, full_path: str):
    """
    Forwards all unmatched /v1/* routes to the OpenAI API.
    Preserves ALL headers and body bytes (including custom headers and multipart data).
    """
    endpoint = f"/v1/{full_path}"
    return await forward_openai(request, endpoint)

# app/routes/responses.py

from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/v1/responses", methods=["GET", "POST"])
@router.api_route("/v1/responses/{full_path:path}", methods=["GET", "POST", "PATCH", "DELETE"])
async def responses_passthrough(request: Request, full_path: str = ""):
    """
    Passthrough for all /v1/responses endpoints (BIFL-grade).
    """
    endpoint = "/v1/responses"
    if full_path:
        endpoint += f"/{full_path}"
    return await forward_openai(request, endpoint)

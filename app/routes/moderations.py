# app/routes/moderations.py

from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/v1/moderations", methods=["POST"])
async def moderations_passthrough(request: Request):
    """
    BIFL-grade moderation endpoint passthrough.
    """
    return await forward_openai(request, "/v1/moderations")

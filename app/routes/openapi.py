from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/openapi.json", methods=["GET"])
async def openapi_json(request: Request):
    return await forward_openai(request, "/v1/openapi.json")

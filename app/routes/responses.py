# app/routes/responses.py — BIFL v2.3.4-fp
from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter(prefix="/v1/responses", tags=["Responses"])

@router.post("")
async def responses_post(request: Request):
    return await forward_openai(request, "/v1/responses")

# app/routes/usage.py
from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.get("/images")
async def usage_images(request: Request):
    return await forward_openai(request, "/v1/organization/usage/images")

@router.get("/audio_transcriptions")
async def usage_stt(request: Request):
    return await forward_openai(request, "/v1/organization/usage/audio_transcriptions")

@router.get("/code_interpreter_sessions")
async def usage_ci(request: Request):
    return await forward_openai(request, "/v1/organization/usage/code_interpreter_sessions")

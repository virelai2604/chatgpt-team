from fastapi import APIRouter, Request
from app.utils.forward import forward_openai

router = APIRouter()

@router.api_route("/transcriptions", methods=["POST"])
async def audio_transcriptions(request: Request):
    return await forward_openai(request, "audio/transcriptions")

@router.api_route("/translations", methods=["POST"])
async def audio_translations(request: Request):
    return await forward_openai(request, "audio/translations")

@router.api_route("/speech", methods=["POST"])
async def audio_speech(request: Request):
    return await forward_openai(request, "audio/speech")

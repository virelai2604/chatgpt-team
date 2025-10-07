from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter()

@router.api_route("/speech", methods=["POST"])
async def audio_speech(request: Request):
    return await forward_openai(request, "/v1/audio/speech")

@router.api_route("/transcriptions", methods=["POST"])
async def audio_transcriptions(request: Request):
    return await forward_openai(request, "/v1/audio/transcriptions")

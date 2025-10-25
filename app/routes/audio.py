from fastapi import APIRouter, Request
from app.api.forward import forward_openai
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/audio")

@router.post("/speech")
async def audio_speech(request: Request):
    return await forward_openai(request, "/v1/audio/speech")

@router.post("/transcriptions")
async def audio_transcriptions(request: Request):
    return await forward_openai(request, "/v1/audio/transcriptions")


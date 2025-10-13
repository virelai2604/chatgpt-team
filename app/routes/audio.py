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

# /translation is not supported in OpenAI v2
@router.post("/translation")
async def audio_translation(request: Request):
    return JSONResponse(
        {"error": "audio/translation is not available in OpenAI v2."}, status_code=404
    )

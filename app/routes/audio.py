# ==========================================================
# app/routes/audio.py — BIFL v2.3.4-fp
# ==========================================================
# Unified proxy for all OpenAI audio endpoints:
#   /v1/audio/speech        → text → speech (TTS)
#   /v1/audio/transcriptions → speech → text (STT)
#   /v1/audio/translations  → translation
#   /v1/audio/realtime      → streaming realtime audio
# ==========================================================

from fastapi import APIRouter, Request
from app.api.forward import forward_openai

router = APIRouter(prefix="/v1/audio", tags=["Audio"])

# ----------------------------
# 🔊 Text → Speech (TTS)
# ----------------------------
@router.post("/speech")
async def text_to_speech(request: Request):
    """
    Forwards a text-to-speech (TTS) request to OpenAI.
    Example:
      {
        "model": "gpt-audio-2025-08-28",
        "input": "Hello world",
        "voice": "verse",
        "format": "mp3",
        "stream": true
      }
    """
    return await forward_openai(request, "/v1/audio/speech")

# ----------------------------
# 🎧 Speech → Text (Transcription)
# ----------------------------
@router.post("/transcriptions")
async def audio_transcribe(request: Request):
    """
    Forward a transcription (STT) request.
    Supports multipart/form-data or base64 JSON bodies.
    """
    return await forward_openai(request, "/v1/audio/transcriptions")

# ----------------------------
# 🌐 Speech Translation
# ----------------------------
@router.post("/translations")
async def audio_translate(request: Request):
    """Forward translation requests (audio → translated text)."""
    return await forward_openai(request, "/v1/audio/translations")

# ----------------------------
# 🔴 Realtime Audio (Bidirectional Streaming)
# ----------------------------
@router.api_route("/realtime/{session_id}", methods=["GET", "POST"])
async def realtime_audio_session(request: Request, session_id: str):
    """
    Realtime relay for gpt-audio or gpt-5-pro-realtime models.
    Example:
      GET/POST /v1/audio/realtime/{session_id}
    """
    endpoint = f"/v1/audio/realtime/{session_id}"
    return await forward_openai(request, endpoint)

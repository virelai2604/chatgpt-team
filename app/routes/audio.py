# app/routes/audio.py
# BIFL v2.2 — Unified Audio API
# Supports TTS (speech) + STT (transcription) + relay forwarding.
# Compatible with OpenAI SDK 2.6.1 and GPT-5-Codex / gpt-4o audio models.

import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, Dict, Any
from app.api.forward import forward_openai

router = APIRouter(prefix="/v1/audio", tags=["Audio"])

# === Default Models ===
DEFAULT_TTS_MODEL = os.getenv("DEFAULT_TTS_MODEL", "gpt-4o-mini-tts")
DEFAULT_TRANSCRIBE_MODEL = os.getenv("DEFAULT_TRANSCRIBE_MODEL", "gpt-4o-transcribe-diarize")


def error(msg: str, type_: str = "audio_error", code: int = 400):
    return JSONResponse(status_code=code, content={"error": {"type": type_, "message": msg}})


# === Speech (TTS) ===
@router.post("/speech")
async def create_speech(
    input: str = Form(..., description="Text to convert to speech"),
    model: str = Form(DEFAULT_TTS_MODEL),
    voice: Optional[str] = Form("alloy"),
    stream: bool = Form(False),
):
    """
    Text-to-Speech generation.
    Supports `stream=True` for audio chunk streaming.
    """
    try:
        payload = {"model": model, "input": input, "voice": voice}

        if stream:
            async def audio_stream():
                async for chunk in forward_openai(
                    path="/v1/audio/speech", method="POST", json=payload, stream=True
                ):
                    yield chunk
            return StreamingResponse(audio_stream(), media_type="audio/mpeg")

        resp = await forward_openai(path="/v1/audio/speech", method="POST", json=payload)
        if not resp:
            raise HTTPException(status_code=502, detail="No audio returned")
        return StreamingResponse(iter([resp]), media_type="audio/mpeg", headers={"x-model": model})

    except Exception as e:
        return error(str(e), "tts_failed", 500)


# === Transcription (STT) ===
@router.post("/transcriptions")
async def create_transcription(
    file: UploadFile = File(...),
    model: str = Form(DEFAULT_TRANSCRIBE_MODEL),
    prompt: Optional[str] = Form(None),
    temperature: Optional[float] = Form(0.2),
):
    """Speech-to-Text transcription. Uploads audio file, returns JSON transcription text."""
    try:
        tmp_path = f"/tmp/{file.filename}"
        async with aiofiles.open(tmp_path, "wb") as f:
            await f.write(await file.read())

        resp = await forward_openai(
            path="/v1/audio/transcriptions",
            method="POST",
            files={"file": (file.filename, open(tmp_path, "rb"))},
            data={"model": model, "prompt": prompt or "", "temperature": temperature},
        )
        if not resp:
            raise HTTPException(status_code=502, detail="No transcription response")

        try:
            os.remove(tmp_path)
        except FileNotFoundError:
            pass

        return JSONResponse(status_code=200, content={"object": "transcription", "data": resp})
    except Exception as e:
        return error(str(e), "transcription_failed", 500)


# === Tool entrypoints ===
async def execute_audio_tool(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Internal handler for responses.py to execute audio-related tools."""
    try:
        t_type = tool.get("type")
        params = tool.get("parameters", {})

        if t_type == "audio_speech":
            text = params.get("input", "")
            voice = params.get("voice", "alloy")
            model = params.get("model", DEFAULT_TTS_MODEL)
            resp = await forward_openai(
                path="/v1/audio/speech", method="POST",
                json={"input": text, "model": model, "voice": voice}
            )
            return {"type": "audio_speech", "audio_url": resp.get("url") if isinstance(resp, dict) else None}

        if t_type == "audio_transcribe":
            file_id = params.get("file_id")
            model = params.get("model", DEFAULT_TRANSCRIBE_MODEL)
            if not file_id:
                raise ValueError("Missing file_id for transcription tool")
            resp = await forward_openai(path=f"/v1/files/{file_id}/content", method="GET")
            return {"type": "audio_transcribe", "transcript": resp.get("text") if isinstance(resp, dict) else resp}

        return {"error": f"Unsupported tool type: {t_type}"}
    except Exception as e:
        return {"error": str(e)}

from fastapi import APIRouter, UploadFile, File, Form

router = APIRouter()

@router.post("/audio/transcriptions")
async def audio_transcriptions(
    file: UploadFile = File(...),
    model: str = Form(...)
):
    # For the relay, just reply with dummy
    return {
        "text": "Transcription test: OpenAI relay test"
    }

# ==========================================================
# app/tools/audio_transcribe.py — Speech-to-Text
# ==========================================================
import os, httpx
from app.routes.services.tool_registry import register_tool

@register_tool("audio_transcribe")
async def audio_transcribe(file_path: str):
    """Transcribe audio to text using gpt-audio."""
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=300) as client:
        with open(file_path, "rb") as f:
            files = {"file": f}
            res = await client.post("https://api.openai.com/v1/audio/transcriptions", headers=headers, files=files)
        return res.json()

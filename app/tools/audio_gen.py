from app.routes.services.tool_registry import register_tool
import os, httpx

@register_tool("audio_gen")
async def audio_gen(text: str, voice: str = "alloy"):
    """Convert text to speech using gpt-audio-2025-08-28."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "Missing OPENAI_API_KEY"}
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"model": "gpt-audio-2025-08-28", "input": text, "voice": voice}
    async with httpx.AsyncClient() as client:
        r = await client.post("https://api.openai.com/v1/audio/speech", headers=headers, json=payload)
        return {"status": r.status_code, "content_type": r.headers.get("content-type")}

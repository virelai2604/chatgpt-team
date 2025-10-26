from app.routes.services.tool_registry import register_tool
import os, httpx

@register_tool("video_gen")
async def video_gen(prompt: str, seconds: int = 10, size: str = "1920x1080"):
    """Generate a short video using sora-2-pro."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "Missing OPENAI_API_KEY"}
    headers = {"Authorization": f"Bearer {api_key}", "OpenAI-Beta": "sora-2-pro=v2"}
    payload = {"model": "sora-2-pro", "prompt": prompt, "seconds": seconds, "size": size}
    async with httpx.AsyncClient() as client:
        r = await client.post("https://api.openai.com/v1/videos", headers=headers, json=payload)
        return {"status": r.status_code, "video_job": r.json()}

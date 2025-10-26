# ==========================================================
# app/tools/image_gen.py — BIFL v2.3.5 (Future-Proof)
# Unified Image Generation via /v1/responses
# ==========================================================
import os, httpx, asyncio
from app.routes.services.tool_registry import register_tool

@register_tool("image_gen")
async def image_gen(prompt: str, size: str = "1024x1024", n: int = 1):
    """Generate or edit image using gpt-image-1 through /v1/responses."""
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-5-pro",
        "input": prompt,
        "tools": [
            {
                "type": "image_generation",
                "model": "gpt-image-1",
                "parameters": {"size": size, "n": n}
            }
        ],
        "stream": True
    }

    async with httpx.AsyncClient(timeout=600) as client:
        r = await client.post("https://api.openai.com/v1/responses", headers=headers, json=payload)
        try:
            return r.json()
        except Exception:
            return {"error": r.text}

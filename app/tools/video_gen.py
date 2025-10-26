# ==========================================================
# app/tools/video_gen.py — Sora-2-Pro Integration Tool
# BIFL v2.3.7-fp (Future-Proof)
# ==========================================================
# Compatible with OpenAI /v1/responses (2025+)
# Uses function-based tool schema (video_generate)
# ==========================================================

import os
import httpx
from app.routes.services.tool_registry import register_tool

@register_tool("video_generate")
async def video_generate(prompt: str, seconds: int = 10, size: str = "1920x1080"):
    """Generate a short video using Sora-2-Pro via /v1/responses."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "Missing OPENAI_API_KEY"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "sora-2-pro=v2",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sora-2-pro",
        "input": prompt or f"Generate a {seconds}s {size} video using Sora 2 Pro.",
        "tools": [
            {
                "type": "function",
                "name": "video_generate",
                "function": {
                    "description": "Generate a Sora 2 Pro video with configurable length and size.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "seconds": {"type": "integer", "default": seconds},
                            "size": {"type": "string", "default": size}
                        },
                        "required": ["seconds", "size"]
                    }
                }
            }
        ],
        "stream": True
    }

    async with httpx.AsyncClient(timeout=600, http2=False) as client:
        resp = await client.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload
        )
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}
        return {
            "status": resp.status_code,
            "data": data,
            "tool": "video_generate"
        }

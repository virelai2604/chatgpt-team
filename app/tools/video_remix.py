# ==========================================================
# app/tools/video_remix.py — Sora 2 Pro Remix Tool
# BIFL v2.3.7-fp
# ==========================================================

import os, httpx
from app.routes.services.tool_registry import register_tool

@register_tool("video_remix")
async def video_remix(source_video_id: str, prompt: str = "", strength: float = 0.6):
    """Remix an existing Sora video with a new prompt."""
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
        "input": prompt or f"Remix video {source_video_id} with strength {strength}.",
        "tools": [
            {
                "type": "function",
                "name": "video_remix",
                "function": {
                    "description": "Remix an existing Sora 2 Pro video using a new prompt.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "source_video_id": {"type": "string", "default": source_video_id},
                            "prompt": {"type": "string", "default": prompt},
                            "strength": {"type": "number", "default": strength}
                        },
                        "required": ["source_video_id", "prompt"]
                    }
                }
            }
        ]
    }

    async with httpx.AsyncClient(timeout=600, http2=False) as client:
        resp = await client.post("https://api.openai.com/v1/responses", headers=headers, json=payload)
        try:
            data = resp.json()
        except Exception:
            data = {"raw": resp.text}
        return {"status": resp.status_code, "data": data, "tool": "video_remix"}

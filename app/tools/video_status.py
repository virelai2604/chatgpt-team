# ==========================================================
# app/tools/video_status.py — Sora 2 Pro Video Status Tool
# BIFL v2.3.7-fp
# ==========================================================

import os, httpx
from app.routes.services.tool_registry import register_tool

@register_tool("video_status")
async def video_status(video_id: str):
    """Query the status of a generated or remixed Sora video."""
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
        "input": f"Retrieve status for video ID {video_id}",
        "tools": [
            {
                "type": "function",
                "name": "video_status",
                "function": {
                    "description": "Retrieve the processing status or output of a Sora 2 Pro video job.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "video_id": {"type": "string", "default": video_id}
                        },
                        "required": ["video_id"]
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
        return {"status": resp.status_code, "data": data, "tool": "video_status"}

# ============================================================
# Tool: video_generation — Mock video generator
# ============================================================

import uuid

TOOL_SCHEMA = {
    "name": "video_generation",
    "description": "Create or remix short videos from text prompts.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "seconds": {"type": "integer", "default": 10},
            "remixed_from_video_id": {"type": "string", "nullable": True}
        },
        "required": ["prompt"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "status": {"type": "string"},
            "url": {"type": "string"},
            "duration": {"type": "integer"}
        }
    }
}

async def run(payload: dict) -> dict:
    """Simulates video generation."""
    vid = str(uuid.uuid4())
    prompt = payload.get("prompt", "")
    sec = int(payload.get("seconds", 10))
    return {"id": vid, "status": "completed", "url": f"https://mock.videos/{vid}.mp4", "duration": sec}

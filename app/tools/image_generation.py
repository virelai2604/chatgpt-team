# ============================================================
# Tool: image_generation — Mock image generation
# ============================================================

TOOL_SCHEMA = {
    "name": "image_generation",
    "description": "Generate or edit AI images from a text prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "size": {"type": "string", "default": "1024x1024"},
            "model": {"type": "string", "default": "dall-e-3"}
        },
        "required": ["prompt"]
    },
    "returns": {
        "type": "object",
        "properties": {"object": {"type": "string"}, "url": {"type": "string"}}
    }
}

async def run(payload: dict) -> dict:
    """Returns mock image generation URL."""
    prompt = payload.get("prompt", "")
    size = payload.get("size", "1024x1024")
    return {"object": "image", "url": f"https://mock.images/{hash(prompt)%10000}_{size}.png"}

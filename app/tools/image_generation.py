TOOL_ID = "image_generation"
TOOL_VERSION = "v1"
TOOL_TYPE = "image"
TOOL_SCHEMA = {
    "name": "image_generation",
    "description": "Generate AI images from a text prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "size": {"type": "string", "default": "1024x1024"}
        },
        "required": ["prompt"]
    },
    "returns": {"type": "array", "items": {"type": "string", "description": "Image URLs"}}
}

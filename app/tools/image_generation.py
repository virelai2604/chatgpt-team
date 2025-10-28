TOOL_SCHEMA = {
    "name": "image_generation",
    "description": "Generate or edit AI images from a text prompt.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "size": {
                "type": "string",
                "default": "1024x1024",
                "description": "Output image resolution."
            },
            "model": {
                "type": "string",
                "default": "dall-e-3",
                "description": "Image generation model name."
            }
        },
        "required": ["prompt"]
    },
    "returns": {
        "type": "object",
        "properties": {
            "object": {"type": "string"},
            "url": {"type": "string"}
        }
    }
}

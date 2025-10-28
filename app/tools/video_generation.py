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

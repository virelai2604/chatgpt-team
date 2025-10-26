TOOL_ID = "video_generation"
TOOL_VERSION = "v1"
TOOL_TYPE = "video"
TOOL_SCHEMA = {
    "name": "video_generation",
    "description": "Generate short AI videos using Sora 2 Pro.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string"},
            "seconds": {"type": "integer", "default": 10},
            "resolution": {"type": "string", "default": "1920x1080"}
        },
        "required": ["prompt"]
    },
    "returns": {"type": "object", "properties": {
        "video_id": {"type": "string"},
        "status": {"type": "string"},
        "download_url": {"type": "string"}
    }}
}

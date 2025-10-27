TOOL_ID = "video_generation"
TOOL_VERSION = "v1"
TOOL_TYPE = "video"
TOOL_DESCRIPTION = "Generate or remix videos using Sora models via /v1/responses."

TOOL_SCHEMA = {
    "name": "video_generation",
    "description": "Create or remix videos.",
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Text description of video."},
            "seconds": {"type": "integer", "default": 10},
            "remixed_from_video_id": {"type": "string", "nullable": True}
        },
        "required": ["prompt"]
    },
    "returns": {"type": "object", "properties": {
        "id": {"type": "string"}, "status": {"type": "string"}, "url": {"type": "string"}}}
}

def run(payload):
    prompt = payload.get("prompt", "example video")
    duration = payload.get("seconds", 10)
    remix_id = payload.get("remixed_from_video_id")
    return {
        "id": "vid_mock_001",
        "status": "queued",
        "url": f"https://mock-videos.local/{prompt.replace(' ', '_')}.mp4",
        "duration": duration,
        "remixed_from": remix_id
    }

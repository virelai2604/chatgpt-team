TOOL_ID = "realtime"
TOOL_VERSION = "v1"
TOOL_TYPE = "realtime"
TOOL_SCHEMA = {
    "name": "realtime",
    "description": "Start or manage a realtime session (audio/video).",
    "parameters": {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "enum": ["text", "audio", "video"], "default": "text"},
            "voice": {"type": "string", "default": "verse"}
        }
    },
    "returns": {"type": "object", "properties": {"session_id": {"type": "string"}, "status": {"type": "string"}}}
}
